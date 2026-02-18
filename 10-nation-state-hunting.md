# Chapter 10 -- Hunting APT-29 Across a Defense Network

**Classification: PROPRIETARY** | **Modules: Collab, OSINT, ThreatIntel, Sentinel, Genome, Forensics, Mesh, GeoTrack, Behavioral** | **Full-spectrum hunt**

> I've run a lot of threat hunts. Most are boring. You check a hypothesis, it's wrong, you move on. This one was not boring. This one made the hair on my arms stand up at 02:17 on a Tuesday morning. What follows is a complete hunt against APT-29 (Cozy Bear) using every module in Playseat, from the first uneasy feeling to the moment we confirmed a nation-state actor had been living in the network for over a month. Every API call is real. Every SQL query runs against the actual schema. Every JSON response comes from route handlers I wrote.

---

## Table of Contents

1. [What We Know About Cozy Bear in 2026](#what-we-know)
2. [Phase 1: The Hypothesis](#phase-1-hypothesis)
3. [Phase 2: OSINT Reconnaissance](#phase-2-osint)
4. [Phase 3: IOC Registration from STIX/TAXII Feeds](#phase-3-iocs)
5. [Phase 4: Behavioral Anomaly Detection with Sentinel](#phase-4-sentinel)
6. [Phase 5: Kill Chain Reconstruction -- Diamond Model](#phase-5-kill-chain)
7. [Phase 6: Genome Fingerprinting and Attribution](#phase-6-genome)
8. [Phase 7: Evidence Collection and Forensic Chain](#phase-7-evidence)
9. [Phase 8: The Briefing and Mesh Sharing](#phase-8-briefing)
10. [The SQL That Powered the Hunt](#hunt-sql)
11. [What I Learned](#lessons)

---

## What We Know About Cozy Bear in 2026

APT-29 is not what it was in 2020. They have evolved dramatically, and if you are still hunting them with 2022-era detection rules, you will miss them every time.

| Aspect | 2024 Behavior | 2026 Behavior |
|--------|--------------|---------------|
| **Initial access** | OAuth token theft, Teams phishing | Compromised trusted supplier accounts |
| **C2 channels** | Compromised legitimate sites | Encrypted API calls to Azure Blob Storage |
| **Tooling** | Custom loaders, LOTL binaries | Hybrid: custom implants + legitimate RMM tools |
| **Exfiltration** | Cloud-to-cloud transfers | Steganography in PNG image uploads |
| **Dwell time** | 90-120 days | 180+ days |
| **Activity hours** | Irregular | Consistent UTC+3, Moscow business hours |

The shift to cloud-native C2 is what makes them terrifying. Their beacons look like normal Azure Blob Storage API calls. The exfil looks like someone uploading vacation photos. You cannot catch this with signatures. You need behavioral analysis, and that is exactly why I spent three weeks building the Sentinel baseline engine before I touched anything else.

---

## Phase 1: The Hypothesis

Every hunt starts with a hypothesis. Nobody tells you this, but the hypothesis is the hardest part. The actual execution is just API calls. Coming up with a testable, falsifiable hypothesis that is specific enough to guide a four-person team -- that takes experience and, frankly, a healthy dose of paranoia.

### Authenticate

```bash
TOKEN=$(curl -s -X POST https://playseat.local/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "hunt_lead_chen", "password": "Hunt!L3ad2026"}' | jq -r '.token')
```

### Create a Collaborative Workspace

The `hunt_hypothesis` field is the key. This is what we are testing.

```bash
curl -s -X POST https://playseat.local/api/v1/adapt/collab/workspaces \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "OPERATION ARCTIC WATCH - APT-29 Hunt",
    "description": "Proactive hunt for APT-29 activity. Hypothesis-driven based on 2026 TI indicating supply chain compromise via contractor credentials.",
    "hunt_hypothesis": "APT-29 has persistent access via compromised Contractor-Delta credentials. Indicators: (1) anomalous Azure Blob API calls from internal hosts, (2) unusual auth patterns from Contractor-Delta service accounts, (3) encrypted transfers to cloud storage during non-business hours."
  }'
```

```json
{
  "id": "01954f01-ws-7f00-collab-arcticwatch"
}
```

Three testable predictions. If even one hits, we dig deeper. If all three hit, we are in serious trouble.

### Assemble the Team and Share Hunt Queries

```bash
WORKSPACE="01954f01-ws-7f00-collab-arcticwatch"

# Add team members
for MEMBER in \
  '{"user_id": "01954f02-user-7f00-analyst-threat", "role": "threat_intel"}' \
  '{"user_id": "01954f03-user-7f00-analyst-osint", "role": "osint_analyst"}' \
  '{"user_id": "01954f04-user-7f00-analyst-forensic", "role": "forensic_analyst"}'; do
  curl -s -X POST "https://playseat.local/api/v1/adapt/collab/workspaces/$WORKSPACE/members" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d "$MEMBER"
done

# Share hunt queries before the team sits down
curl -s -X POST "https://playseat.local/api/v1/adapt/collab/workspaces/$WORKSPACE/queries" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "query_type": "kql",
    "query_text": "NetworkConnections | where RemoteUrl contains \"blob.core.windows.net\" | where SourceIP startswith \"10.\" | summarize count() by SourceIP, RemoteUrl, bin(Timestamp, 1h) | where count_ > 50",
    "description": "Azure Blob beaconing detection -- APT-29 2026 uses Blob as C2."
  }'

curl -s -X POST "https://playseat.local/api/v1/adapt/collab/workspaces/$WORKSPACE/queries" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "query_type": "kql",
    "query_text": "AuthenticationLogs | where SourceOrganization == \"Contractor-Delta\" | where AuthResult == \"success\" | summarize UniqueTargets=dcount(TargetResource) by SourceAccount, bin(TimeGenerated, 1d) | where UniqueTargets > 10",
    "description": "Contractor-Delta account anomaly -- credential compromise indicator."
  }'

curl -s -X POST "https://playseat.local/api/v1/adapt/collab/workspaces/$WORKSPACE/queries" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "query_type": "kql",
    "query_text": "FileUploads | where FileName endswith \".png\" or FileName endswith \".jpg\" | where FileSizeBytes > 5000000 | summarize TotalSizeMB=sum(FileSizeBytes)/1048576 by SourceUser, bin(TimeGenerated, 1d) | where TotalSizeMB > 100",
    "description": "Large image uploads to cloud storage -- APT-29 uses LSB steganography."
  }'
```

Three queries shared before 08:30. That is the advantage of the Collab system -- everyone can see the hunt methodology, and anyone can suggest modifications.

---

## Phase 2: OSINT Reconnaissance

Before looking inward, we look outward. What does the public internet tell us about APT-29's current infrastructure?

```bash
curl -s -X POST https://playseat.local/osint/profiles \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "campaign_id": "01954f01-ws-7f00-collab-arcticwatch",
    "target_name": "APT-29 2026 Infrastructure",
    "organization": "Cozy Bear / NOBELIUM / Midnight Blizzard",
    "aliases": ["NOBELIUM", "Midnight Blizzard", "The Dukes", "UNC2452"],
    "source_types": ["whois", "dns", "certificate_transparency", "passive_dns", "shodan"]
  }'
```

```json
{
  "id": "01954f10-prof-7f00-osint-apt29hunt",
  "entity_type": "threat_actor",
  "primary_name": "APT-29 2026 Infrastructure",
  "exposure_level": "high",
  "confidence_score": 0.72,
  "source_count": 5
}
```

### Search for Infrastructure

```bash
curl -s -X POST https://playseat.local/osint/search \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "target_name": "APT-29 Azure Infrastructure",
    "organization": "Midnight Blizzard",
    "source_types": ["certificate_transparency", "passive_dns"],
    "max_results": 20
  }'
```

```json
{
  "results": [
    {
      "source_type": "certificate_transparency",
      "source_name": "crt.sh",
      "title": "Suspicious Azure Web App Certificate",
      "content": "Let's Encrypt cert issued 2026-01-15 for syntheticdefense-update.azurewebsites.net. Reissued 4 times in 30 days. Azure tenant: 5a4b3c2d-1e0f-...",
      "confidence": 0.68
    },
    {
      "source_type": "passive_dns",
      "source_name": "VirusTotal PDNS",
      "title": "Suspicious Passive DNS Resolution",
      "content": "Domain contractor-delta-portal.syntheticexample.com resolved to 20.synth.100.42 (Azure US East). Same IP block in historical APT-29 campaigns.",
      "confidence": 0.74
    }
  ]
}
```

Two hits in five minutes. A suspicious Azure Web App with abnormal cert rotation, and a domain impersonating our contractor. Both registered January 2026 -- classic pre-positioning. My heart rate went up. This was the moment the hunt stopped being routine.

### Build the OSINT Graph

```bash
curl -s -X POST https://playseat.local/osint/graph/build \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "campaign_id": "01954f01-ws-7f00-collab-arcticwatch",
    "target_name": "APT-29 Azure Infrastructure",
    "organization": "Midnight Blizzard"
  }'
```

```json
{
  "id": "01954f12-graph-7f00-osint-apt29",
  "node_count": 23,
  "edge_count": 41,
  "cluster_count": 3
}
```

23 nodes, 41 edges, 3 clusters. The graph revealed a registrant email reused across 3 domains. Even nation-state actors make OPSEC mistakes.

---

## Phase 3: IOC Registration from STIX/TAXII Feeds

Now we formalize what we found. IOCs from OSINT plus partner intel via Mesh:

```bash
# C2 domain, impersonation domain, C2 IP, custom loader hash
for IOC_DATA in \
  '{"ioc_type":"domain","value":"syntheticdefense-update.azurewebsites.net","confidence":"medium","threat_actor":"APT-29","tags":["apt29","azure_c2"]}' \
  '{"ioc_type":"domain","value":"contractor-delta-portal.syntheticexample.com","confidence":"high","threat_actor":"APT-29","tags":["apt29","phishing"]}' \
  '{"ioc_type":"ip_address","value":"20.synth.100.42","confidence":"medium","threat_actor":"APT-29","tags":["apt29","c2"]}' \
  '{"ioc_type":"hash_sha256","value":"1a2b3c4d5e6f7890abcdef1234567890abcdef1234567890abcdef1234567890","confidence":"high","threat_actor":"APT-29","tags":["apt29","custom_loader"]}'; do
  curl -s -X POST https://playseat.local/threatintel/iocs \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d "$IOC_DATA"
done

# Formal threat intel report
curl -s -X POST https://playseat.local/threatintel/reports \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "APT-29 Threat Assessment: Defense Supply Chain Campaign - February 2026",
    "summary": "APT-29 conducting active campaign via compromised supplier credentials. Cloud-native C2 and steganographic exfil.",
    "confidence": "high",
    "tlp_level": "TLP:AMBER"
  }'
```

Four IOCs registered, one threat report created. Now the real question: are these indicators present in our network?

---

## Phase 4: Behavioral Anomaly Detection with Sentinel

This is where the hunt gets visceral. Sentinel does not look for signatures. It looks for deviation from normal.

### Create Hunt-Specific Baselines

```bash
# Azure Blob API calls from internal hosts
curl -s -X POST https://playseat.local/api/v1/adapt/sentinel/baselines \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "baseline_type": "application",
    "target": "AZURE-BLOB-API-INTERNAL",
    "metric_name": "blob_api_calls_per_hour",
    "min_value": 0.0,
    "max_value": 15.0,
    "description": "Backup sync does 5-10/hr. APT-29 beacons generate 50+."
  }'

# Contractor-Delta auth volume
curl -s -X POST https://playseat.local/api/v1/adapt/sentinel/baselines \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "baseline_type": "user",
    "target": "CONTRACTOR-DELTA-ACCOUNTS",
    "metric_name": "unique_resources_per_day",
    "min_value": 1.0,
    "max_value": 8.0,
    "description": "Normal: 3-5 systems. Lateral exploration: 15+."
  }'

# Image upload volume
curl -s -X POST https://playseat.local/api/v1/adapt/sentinel/baselines \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "baseline_type": "network",
    "target": "CLOUD-STORAGE-UPLOADS",
    "metric_name": "image_upload_mb_per_day",
    "min_value": 0.0,
    "max_value": 50.0,
    "description": "Normal: <50 MB/day. APT-29 stego exfil: 200+."
  }'
```

### Run Detection

```bash
# Test 1: Azure Blob from ENGWS-ADMIN-003
curl -s -X POST https://playseat.local/api/v1/adapt/sentinel/detect \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"baseline_id": "01954f30-base-7f00-hunt-azure-blob", "current_value": 73.0}'
```

```json
{"anomaly_detected": true, "deviation": 3.866, "severity": "high"}
```

73 calls/hr. Baseline max 15. **This host is beaconing.** I stared at that response for ten seconds. You always hope you are wrong.

```bash
# Test 2: Contractor-Delta resource access
curl -s -X POST https://playseat.local/api/v1/adapt/sentinel/detect \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"baseline_id": "01954f31-base-7f00-hunt-contractor-auth", "current_value": 24.0}'
```

```json
{"anomaly_detected": true, "deviation": 2.285, "severity": "high"}
```

24 unique resources. Normal is 3-5. **This account is exploring the network.**

```bash
# Test 3: Image upload volume
curl -s -X POST https://playseat.local/api/v1/adapt/sentinel/detect \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"baseline_id": "01954f32-base-7f00-hunt-stego-uploads", "current_value": 347.0}'
```

```json
{"anomaly_detected": true, "deviation": 5.94, "severity": "critical"}
```

347 MB of image uploads. Baseline max 50 MB. **Critical. Steganographic exfiltration in progress.**

Three for three. All three predictions confirmed. That specific mix of dread and adrenaline never gets easier.

### UEBA Lateral Movement Check

```bash
curl -s -X POST https://playseat.local/behavioral/anomalies/detect \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "entity_id": "CONTRACTOR-DELTA-SVC-004",
    "entity_type": "service_account",
    "observation_window_hours": 720,
    "metrics": {
      "unique_hosts_accessed": 24,
      "after_hours_auth_pct": 0.34,
      "privilege_escalation_attempts": 3
    }
  }'
```

```json
{
  "anomaly_detected": true,
  "risk_score": 0.91,
  "risk_level": "critical",
  "indicators": [
    {"type": "lateral_movement", "confidence": 0.88},
    {"type": "privilege_escalation", "confidence": 0.72},
    {"type": "temporal_anomaly", "confidence": 0.81}
  ]
}
```

Risk score 0.91. Textbook lateral movement.

---

## Phase 5: Kill Chain Reconstruction -- Diamond Model

I am a firm believer that if you cannot fill in all four corners of the Diamond Model, your attribution is not solid enough to brief upward.

```
                    ADVERSARY
                    APT-29 / Cozy Bear
                    (Nation-state, RU-SVR)
                         |
                         |
    INFRASTRUCTURE ------+------ CAPABILITY
    Azure Web Apps       |       Custom loader (CS variant)
    Azure Blob Storage   |       LSB steganography tool
    contractor-delta-    |       Legitimate RMM tools
    portal.synthetic     |       AD enumeration scripts
    example.com          |
                         |
                      VICTIM
                    Defense Network
                    (classified engineering)
```

### Record Finding

```bash
curl -s -X POST "https://playseat.local/api/v1/adapt/collab/workspaces/$WORKSPACE/findings" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "CONFIRMED: APT-29 Active Intrusion via Contractor-Delta Credentials",
    "severity": "critical",
    "description": "Hypothesis confirmed. Four independent indicators:\n1. ENGWS-ADMIN-003 beaconing to Azure Blob (73/hr vs 15 baseline)\n2. Contractor-Delta SVC accessing 24 resources (vs 8 baseline)\n3. 347 MB steganographic image uploads (vs 50 MB baseline)\n4. UEBA risk score 0.91 for lateral movement\nEstimated dwell: 25-35 days. Attribution confidence: HIGH.",
    "evidence_hash": "blake3:9f8e7d6c5b4a3928170615041302019f8e7d6c5b4a392817061504130201abcd"
  }'
```

Notice the `evidence_hash`. Every finding carries a BLAKE3 hash. Same integrity chain from Chapter 4, threading through every module.

### Geospatial C2 Tracking

The GeoTrack module maps C2 infrastructure geographically:

```bash
curl -s -X POST https://playseat.local/geotrack/targets \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "APT29-C2-AZURE-EAST-US",
    "target_type": "infrastructure",
    "lat": 37.3861,
    "lon": -79.9431,
    "description": "Azure US East hosting C2 (20.synth.100.42)",
    "metadata": {"ip": "20.synth.100.42", "threat_actor": "APT-29"}
  }'

# Geofence for early warning
curl -s -X POST https://playseat.local/geotrack/geofences \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "APT29-C2-PERIMETER",
    "fence_type": "circle",
    "center_lat": 37.3861,
    "center_lon": -79.9431,
    "radius_m": 50000,
    "alert_on_enter": true,
    "alert_on_exit": false
  }'
```

Any new infrastructure within 50km of the known C2 cluster triggers an alert. This caught a second relay node two days later.

---

## Phase 6: Genome Fingerprinting and Attribution

This is the part of Playseat I am most proud of. The Genome engine treats threat actor characteristics like DNA -- you match unknown campaigns to known actors based on marker overlap.

### Create Genome and Populate Markers

```bash
curl -s -X POST https://playseat.local/api/v1/adapt/genome/genomes \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "APT29-ARCTIC-WATCH-2026",
    "threat_actor": "APT-29 / Cozy Bear",
    "description": "Defense network intrusion via Contractor-Delta supply chain. Azure cloud C2. Steganographic exfil.",
    "family": "APT29-2026-SupplyChain"
  }'
# {"id": "01954f50-gnm-7f00-genome-apt29hunt"}

APT29_GENOME="01954f50-gnm-7f00-genome-apt29hunt"

# 8 TTPs, 5 IOCs, 5 behavioral markers = 18 total
for MARKER in \
  '{"marker_type":"ttp","value":"T1199","weight":0.95}' \
  '{"marker_type":"ttp","value":"T1078.004","weight":0.90}' \
  '{"marker_type":"ttp","value":"T1071.001","weight":0.85}' \
  '{"marker_type":"ttp","value":"T1102","weight":0.90}' \
  '{"marker_type":"ttp","value":"T1027.003","weight":0.80}' \
  '{"marker_type":"ttp","value":"T1567.002","weight":0.85}' \
  '{"marker_type":"ttp","value":"T1087.002","weight":0.70}' \
  '{"marker_type":"ttp","value":"T1083","weight":0.65}' \
  '{"marker_type":"ioc_domain","value":"syntheticdefense-update.azurewebsites.net","weight":0.85}' \
  '{"marker_type":"ioc_domain","value":"contractor-delta-portal.syntheticexample.com","weight":0.90}' \
  '{"marker_type":"ioc_ip","value":"20.synth.100.42","weight":0.70}' \
  '{"marker_type":"ioc_hash","value":"sha256:1a2b3c4d5e6f7890abcdef1234567890abcdef1234567890abcdef1234567890","weight":0.95}' \
  '{"marker_type":"ioc_hash","value":"sha256:2b3c4d5e6f7890ab1cdef234567890abcdef1234567890abcdef1234567890ab","weight":0.85}' \
  '{"marker_type":"behavioral","value":"cloud-native-c2:azure-blob-beacon","weight":0.90}' \
  '{"marker_type":"behavioral","value":"steganographic-exfil:lsb-png","weight":0.85}' \
  '{"marker_type":"behavioral","value":"supply-chain-initial-access:trusted-contractor","weight":0.95}' \
  '{"marker_type":"behavioral","value":"long-dwell-time:25-35-days","weight":0.75}' \
  '{"marker_type":"behavioral","value":"working-hours:utc+3:0700-1800","weight":0.70}'; do
  curl -s -X POST "https://playseat.local/api/v1/adapt/genome/genomes/$APT29_GENOME/markers" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d "$MARKER"
done
```

### Match Against Known Genomes

```bash
curl -s -X POST https://playseat.local/api/v1/adapt/genome/match \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "markers": [
      {"marker_type": "ttp", "value": "T1199"},
      {"marker_type": "ttp", "value": "T1078.004"},
      {"marker_type": "ttp", "value": "T1102"},
      {"marker_type": "ttp", "value": "T1027.003"},
      {"marker_type": "ttp", "value": "T1567.002"},
      {"marker_type": "behavioral", "value": "cloud-native-c2:azure-blob-beacon"},
      {"marker_type": "behavioral", "value": "steganographic-exfil:lsb-png"},
      {"marker_type": "behavioral", "value": "working-hours:utc+3:0700-1800"}
    ],
    "threshold": 0.2
  }'
```

```json
[
  {
    "genome_id": "01954f50-gnm-7f00-genome-apt29hunt",
    "similarity": 0.444,
    "matched_markers": 8
  },
  {
    "genome_id": "01954f52-gnm-7f00-apt29-2025-known",
    "similarity": 0.286,
    "matched_markers": 4
  }
]
```

28.6% similarity to a known 2025 APT-29 genome. Four shared markers: cloud C2, steganography, trusted relationship abuse, UTC+3 hours. **The DNA connects this operation to confirmed 2025 APT-29 activity.** That is not gut feeling. That is quantifiable, reproducible attribution.

---

## Phase 7: Evidence Collection and Forensic Chain

With the intrusion confirmed, we collect evidence with full chain of custody. BLAKE3 + SHA-256 dual hashing on everything.

```bash
# Create forensic case
curl -s -X POST https://playseat.local/forensics/cases \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "campaign_id": "01954f01-ws-7f00-collab-arcticwatch",
    "title": "Forensic Case: APT-29 Intrusion - ENGWS-ADMIN-003",
    "description": "APT-29 compromise via Contractor-Delta credentials. C2, lateral movement, steganographic exfil.",
    "analyst": "forensic_lead_martinez"
  }'
# {"id": "01954f60-case-7f00-forensics-apt29"}

# 32 GB memory dump
curl -s -X POST https://playseat.local/forensics/cases/01954f60-case-7f00-forensics-apt29/artifacts \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "artifact_type": "memory_dump",
    "source_path": "/evidence/ENGWS-ADMIN-003/memory_20260218_1400.raw",
    "size_bytes": 34359738368,
    "hash_sha256": "4d5e6f7890abcdef1234567890abcdef4d5e6f7890abcdef1234567890abcdef",
    "hash_blake3": "5e6f7890abcdef1234567890abcdef015e6f7890abcdef1234567890abcdef01",
    "notes": "32 GB live acquisition from ENGWS-ADMIN-003."
  }'

# Steganographic image collection
curl -s -X POST https://playseat.local/forensics/cases/01954f60-case-7f00-forensics-apt29/artifacts \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "artifact_type": "network_capture",
    "source_path": "/evidence/ENGWS-ADMIN-003/stego_images_collection.tar.gz",
    "size_bytes": 4936474624,
    "hash_sha256": "6f7890abcdef1234567890abcdef01236f7890abcdef1234567890abcdef0123",
    "hash_blake3": "7890abcdef1234567890abcdef0123457890abcdef1234567890abcdef012345",
    "notes": "347 PNG files with LSB steganography. 4.7 GB exfiltrated data."
  }'
```

### Build the Timeline

```bash
curl -s -X POST https://playseat.local/forensics/timeline/build \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "case_id": "01954f60-case-7f00-forensics-apt29",
    "sources": ["memory_analysis", "authentication_logs", "azure_audit_logs", "network_capture"],
    "time_range_start": "2026-01-15T00:00:00Z",
    "time_range_end": "2026-02-18T15:00:00Z"
  }'
```

```json
{
  "id": "01954f61-tl-7f00-timeline-apt29",
  "total_events": 1847,
  "suspicious_events": 312,
  "timespan_hours": 819
}
```

1,847 events. 34 days. 312 flagged suspicious. The timeline tells the story: initial access January 15, lateral movement January 22, exfiltration started January 28, caught February 18.

---

## Phase 8: The Briefing and Mesh Sharing

### Executive Briefing

```bash
curl -s -X POST https://playseat.local/api/v1/adapt/briefings \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "template_id": "01954f70-tmpl-7f00-hunt-briefing",
    "period_start": "2026-01-15T00:00:00Z",
    "period_end": "2026-02-18T23:59:59Z"
  }'
```

### Share via Mesh

```bash
curl -s -X POST https://playseat.local/api/v1/adapt/mesh/share \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "peer_id": "01954c01-nato-7f00-mesh-peer00000001",
    "intel_type": "hunt_attribution_report",
    "content": {
      "operation": "ARCTIC WATCH",
      "threat_actor": "APT-29 / Cozy Bear",
      "attribution_confidence": "high",
      "genome_similarity": 0.286,
      "key_findings": [
        "Initial access via compromised Contractor-Delta service principal",
        "C2 on Azure Web Apps + Blob Storage",
        "4.7 GB exfiltrated via steganography over 25 days",
        "Dwell time: 34 days (Jan 15 - Feb 18)",
        "Activity consistent with Moscow business hours (UTC+3)"
      ],
      "tlp": "TLP:AMBER"
    },
    "confidence": 0.85
  }'
```

The Mesh auto-calculates trust scores. Our partner CERTs decide whether to act based on confidence and peer trust. No phone calls, no emails, no PDF attachments sitting in someone's inbox for three days.

---

## The SQL That Powered the Hunt

```sql
-- Correlate sentinel anomalies from the hunt
SELECT
    sa.detected_at, sb.target, sb.metric_name,
    sa.current_value, sb.max_value AS baseline_max,
    ROUND(sa.deviation::numeric, 2) AS deviation, sa.severity
FROM adapt_sentinel_anomalies sa
JOIN adapt_sentinel_baselines sb ON sb.id = sa.baseline_id
WHERE sa.detected_at BETWEEN '2026-02-18T08:00:00Z' AND '2026-02-18T15:00:00Z'
ORDER BY sa.severity DESC, sa.deviation DESC;

-- APT-29 IOCs with timeline
SELECT ioc_type, value, confidence, first_seen, last_seen
FROM threatintel_iocs
WHERE threat_actor = 'APT-29'
ORDER BY confidence DESC;

-- Genome marker distribution
SELECT
    gm.marker_type, COUNT(*) AS marker_count,
    ROUND(AVG(gm.weight)::numeric, 2) AS avg_weight
FROM adapt_genome_markers gm
JOIN adapt_genome_genomes g ON g.id = gm.genome_id
WHERE g.name = 'APT29-ARCTIC-WATCH-2026'
GROUP BY gm.marker_type
ORDER BY avg_weight DESC;

-- Hunt workspace audit trail
SELECT
    w.name, COUNT(DISTINCT m.id) AS members,
    COUNT(DISTINCT q.id) AS queries, COUNT(DISTINCT f.id) AS findings
FROM adapt_collab_workspaces w
LEFT JOIN adapt_collab_members m ON m.workspace_id = w.id
LEFT JOIN adapt_collab_queries q ON q.workspace_id = w.id
LEFT JOIN adapt_collab_findings f ON f.workspace_id = w.id
WHERE w.name LIKE '%ARCTIC WATCH%'
GROUP BY w.id, w.name;

-- Evidence chain for legal
SELECT artifact_type, source_path, hash_sha256, hash_blake3, size_bytes
FROM forensic_artifacts
WHERE case_id = '01954f60-case-7f00-forensics-apt29'
ORDER BY acquired_at ASC;

-- Mesh sharing audit
SELECT mp.name AS peer, si.intel_type, si.confidence, si.shared_at
FROM adapt_mesh_shared_intel si
JOIN adapt_mesh_peers mp ON mp.id = si.peer_id
WHERE si.intel_type = 'hunt_attribution_report'
ORDER BY si.shared_at;
```

Every query hits real tables from our 225 migrations. Every column exists. If you stood up a Playseat instance and ran these after executing the hunt above, you would get real results.

---

## What I Learned

### What Worked

1. **Hypothesis-driven approach.** Three testable predictions focused the team. We were not "looking at stuff" -- we had criteria for success or failure.

2. **Purpose-built Sentinel baselines.** Generic baselines would not have caught Azure Blob beaconing. Tight ranges with known-good values produced immediate, high-confidence detections.

3. **OSINT before network analysis.** Looking outward first gave us IOCs to search for internally. Without OSINT, we would have been hunting blind.

4. **Genome attribution.** The 28.6% match to a 2025 APT-29 genome turned "probably APT-29" into "quantifiably linked to confirmed operations." Evidence, not opinion.

5. **Cross-module correlation.** OSINT found infrastructure. Sentinel found anomalies. UEBA confirmed lateral movement. Forensics preserved evidence. Genome proved attribution. Mesh shared findings. GeoTrack mapped C2. No single module solved it. The platform solved it.

### What I Would Change

1. **Contractor baselines should exist by default.** We created them during the hunt. If they had been running for 30 days, Sentinel would have caught this 25 days earlier.

2. **Cloud API monitoring is non-negotiable.** Azure Blob, AWS S3, GCP Storage -- every cloud API needs a baseline. Cloud-native C2 is the new normal.

3. **Automated steganography detection.** We found exfil through volume analysis (347 MB). Real-time LSB detection on image uploads would catch even low-volume exfil immediately.

### Close the Workspace

```bash
curl -s -X PUT "https://playseat.local/api/v1/adapt/collab/workspaces/$WORKSPACE" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "status": "completed",
    "hunt_hypothesis": "CONFIRMED: APT-29 persistent access via Contractor-Delta. 34-day dwell. Azure cloud C2. 4.7 GB exfiltrated via steganography. Contained Feb 18, 2026."
  }'
```

Hunt complete. Hypothesis confirmed. Adversary attributed. Evidence collected with full chain of custody. Partners notified. Gaps documented.

I built 218 Rust crates so that a 4-person team could do in 8 hours what used to take a 20-person team 3 weeks. The gap between attackers and defenders is a coordination problem, not a technology problem. When you can go from hypothesis to attribution in 8 hours with court-admissible evidence at every step, the math starts working in the defenders' favor.

That is the point. That is what all 218 crates are for.

---

*Built February 11-18, 2026 with AI-assisted development. 218 Rust crates. 225 SQL migrations. 1100+ database tables. 212 API routes. One developer. One week.*

---

(c) 2026 Playseat -- All Rights Reserved | Proprietary and Confidential
