# Chapter 9: Ransomware at 3 AM -- A Complete Response Playbook

**Playseat Advanced Field Manual -- Book 2**
**Hour-by-Hour Response Using Every Module in the Platform**

---

> The phone rings at 3:14 AM. It is always 3 AM. Threat actors do not work 9-to-5 in your timezone. The SOC duty officer says four words that ruin your night: "We have been encrypted." Here is what happens next -- every API call, every command, every decision point -- using Playseat to orchestrate the response from first alert to evidence delivery.

---

## 9.1 -- The Call Comes In

**3:14 AM, February 17, 2026.**

The monitoring system detects anomalous file encryption across VLAN-300 (classified engineering workstations). Simultaneously, Sentinel fires a critical alert: egress baseline for VLAN-300 spiked from 0.5 GB/hr to 47 GB/hr. Someone is encrypting files and exfiltrating data at the same time. Double extortion ransomware.

The SOC duty officer calls me. By the time I have my laptop open, I know three things:

1. This is ransomware (file encryption pattern, `.locked3` extension)
2. This is double extortion (simultaneous exfiltration)
3. This is consistent with LockBit 4.0 successor TTPs from January 2026 threat intel

The clock starts now. Everything that follows gets tied to a single incident ID.

---

## 9.2 -- Minute 0-5: Incident Creation and Initial Triage

### Authenticate

```bash
TOKEN=$(curl -s -X POST https://playseat.local/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "ir_commander", "password": "IR!C0mmand3r2026"}' | jq -r '.access_token')
```

### Create the Incident

```bash
curl -s -X POST https://playseat.local/incident/incidents \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "RANSOMWARE - VLAN-300 Classified Engineering - Double Extortion Active",
    "description": "Active ransomware encryption on classified engineering workstations. Simultaneous exfiltration confirmed. Sentinel egress anomaly: 47 GB/hr vs 0.5 GB/hr baseline. File extension .locked3. Consistent with LockBit 4.0 successor variants.",
    "priority": "critical",
    "affected_systems": [
      "ENGWS-001 (10.30.1.11)",
      "ENGWS-002 (10.30.1.12)",
      "ENGWS-003 (10.30.1.13)",
      "ENGWS-004 (10.30.1.14)",
      "ENGWS-005 (10.30.1.15)",
      "FILESRV-ENG-01 (10.30.2.1)",
      "BUILDAGENT-ENG-01 (10.30.3.1)"
    ]
  }'
```

Response:

```json
{
  "id": "01954e01-aaaa-7f00-ir00-ransomware001",
  "title": "RANSOMWARE - VLAN-300 Classified Engineering - Double Extortion Active",
  "phase": "identification",
  "priority": "critical"
}
```

Phase: `identification`. The incident will move through: `identification` -> `containment` -> `eradication` -> `recovery` -> `lessons_learned`.

### First Timeline Event

```bash
curl -s -X POST https://playseat.local/incident/incidents/01954e01-aaaa-7f00-ir00-ransomware001/timeline \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "event_type": "detection",
    "timestamp": "2026-02-17T03:14:00Z",
    "description": "Sentinel critical alert: VLAN-300 egress anomaly. 47 GB/hr vs 0.5 GB/hr baseline. EDR correlated file encryption pattern (.locked3) across 5 engineering workstations.",
    "source": "sentinel_auto"
  }'
```

---

## 9.3 -- Minute 5-15: SOAR Auto-Containment

I do not manually contain. The SOAR playbook does it. This is why we built automation -- so humans make strategic decisions while machines execute tactical steps at machine speed.

### Find the Ransomware Playbook

```bash
curl -s https://playseat.local/soar/playbooks \
  -H "Authorization: Bearer $TOKEN" | jq '.playbooks[] | select(.trigger_type == "ransomware") | {id, name, status}'
```

```json
{
  "id": "01954e10-play-7f00-soar-ransomware01",
  "name": "Ransomware Containment - Critical Infrastructure",
  "status": "active"
}
```

### View the Steps

```bash
curl -s https://playseat.local/soar/playbooks/01954e10-play-7f00-soar-ransomware01/steps \
  -H "Authorization: Bearer $TOKEN" | jq '.steps[] | {step_order, name, action_type, requires_approval}'
```

```json
{"step_order": 1, "name": "Isolate Affected VLAN", "action_type": "network_isolation", "requires_approval": false}
{"step_order": 2, "name": "Kill Malicious Processes", "action_type": "process_termination", "requires_approval": false}
{"step_order": 3, "name": "Disable Compromised Accounts", "action_type": "account_lockout", "requires_approval": false}
{"step_order": 4, "name": "Block C2 Communications", "action_type": "firewall_block", "requires_approval": false}
{"step_order": 5, "name": "Snapshot Affected Systems", "action_type": "forensic_snapshot", "requires_approval": false}
{"step_order": 6, "name": "Notify Incident Commander", "action_type": "notification", "requires_approval": false}
{"step_order": 7, "name": "Begin Evidence Collection", "action_type": "forensic_collection", "requires_approval": true}
```

Steps 1-6 fire automatically. Step 7 waits for human approval because forensic collection requires chain-of-custody procedures.

### Trigger the Playbook

```bash
curl -s -X POST https://playseat.local/soar/playbooks/01954e10-play-7f00-soar-ransomware01/trigger \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "trigger_event": {
      "incident_id": "01954e01-aaaa-7f00-ir00-ransomware001",
      "threat_type": "ransomware_double_extortion",
      "affected_vlan": "VLAN-300",
      "affected_hosts": ["10.30.1.11","10.30.1.12","10.30.1.13","10.30.1.14","10.30.1.15","10.30.2.1","10.30.3.1"],
      "iocs": {"file_extension": ".locked3", "ransom_note": "README_RESTORE.txt", "encryption_process": "svchost_crypt.exe"}
    }
  }'
```

```json
{
  "id": "01954e11-exec-7f00-soar-execution001",
  "status": "playbook_triggered"
}
```

### Monitor Execution

```bash
curl -s https://playseat.local/soar/executions/01954e11-exec-7f00-soar-execution001/steps \
  -H "Authorization: Bearer $TOKEN" | jq '.steps[] | {name: .step_id, status, completed_at}'
```

Six steps completed in 45 seconds. VLAN isolated. Processes killed. Accounts locked. C2 blocked. Snapshots taken. Commander notified. Step 7 waiting for my approval.

**Elapsed time from detection to full containment: 6 minutes.** Without automation, manual containment takes 45-90 minutes. In those extra minutes the attacker encrypts three more VLANs and exfiltrates another 30 GB.

### Advance Incident Phase

```bash
curl -s -X POST https://playseat.local/incident/incidents/01954e01-aaaa-7f00-ir00-ransomware001/advance \
  -H "Authorization: Bearer $TOKEN"
```

Phase advanced to `containment`.

---

## 9.4 -- Minute 15-30: Forensics Collection

I approve the forensics step and begin evidence collection. Volatile evidence first -- memory is the most perishable.

### Approve the SOAR Step

```bash
curl -s -X POST https://playseat.local/soar/executions/01954e11-exec-7f00-soar-execution001/approve \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"approved": true, "comment": "Approved by IR Commander. Chain of custody initiated."}'
```

### Create Forensic Case

```bash
curl -s -X POST https://playseat.local/forensics/cases \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "campaign_id": "01954e01-aaaa-7f00-ir00-ransomware001",
    "title": "Forensic Case: RANSOMWARE-VLAN300-20260217",
    "description": "Full forensic investigation of double-extortion ransomware on VLAN-300. Memory, disk, and network artifacts from 7 affected systems."
  }'
```

```json
{
  "id": "01954e20-case-7f00-forensics-00001",
  "title": "Forensic Case: RANSOMWARE-VLAN300-20260217",
  "status": "open"
}
```

### Memory Analysis

```bash
curl -s -X POST https://playseat.local/forensics/memory/analyze \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "artifact_id": "01954e21-art-7f00-memdump-00001",
    "dump_content": "base64_encoded_memory_image_reference"
  }'
```

```json
{
  "id": "01954e21-mem-7f00-analysis-00001",
  "process_count": 187,
  "suspicious_count": 4,
  "injected_modules": 2,
  "hidden_processes": 1
}
```

Four suspicious processes. Two injected modules. One hidden process. The ransomware left traces.

### Check for Process Injection

```bash
curl -s https://playseat.local/forensics/memory/01954e21-art-7f00-memdump-00001/injection \
  -H "Authorization: Bearer $TOKEN" | jq '.details[]'
```

```json
{
  "target_process": "svchost.exe (PID 4812)",
  "injection_type": "process_hollowing",
  "injected_module": "svchost_crypt.dll",
  "injected_hash": "sha256:b4c5d6e7f8091a2b3c4d5e6f708192a3b4c5d6e7f8091a2b3c4d5e6f708192a3"
}
{
  "target_process": "explorer.exe (PID 2340)",
  "injection_type": "dll_injection",
  "injected_module": "winupdate_helper.dll",
  "injected_hash": "sha256:c5d6e7f8091a2b3c4d5e6f708192a3b4c5d6e7f8091a2b3c4d5e6f708192a3b4"
}
```

Process hollowing in svchost.exe and DLL injection in explorer.exe. Classic ransomware delivery.

### Detect Hidden Process

```bash
curl -s https://playseat.local/forensics/memory/01954e21-art-7f00-memdump-00001/hidden \
  -H "Authorization: Bearer $TOKEN" | jq '.details[0]'
```

```json
{
  "process_name": "csrss_helper.exe",
  "pid": 8844,
  "parent_pid": 4812,
  "hiding_technique": "dkom",
  "hash": "sha256:d6e7f8091a2b3c4d5e6f708192a3b4c5d6e7f8091a2b3c4d5e6f708192a3b4c5"
}
```

DKOM (Direct Kernel Object Manipulation) -- the persistence mechanism that survives the initial process kill.

### Disk Analysis

```bash
curl -s -X POST https://playseat.local/forensics/disk/analyze \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "artifact_id": "01954e22-art-7f00-diskimg-00001",
    "paths": ["/evidence/ENGWS-001/disk_C_20260217.e01"]
  }'
```

```json
{
  "id": "01954e22-disk-7f00-analysis-00001",
  "findings": 59,
  "deleted_files": 47,
  "recovered_files": 31,
  "encrypted_volumes": 0,
  "suspicious_paths": 12
}
```

47 deleted files -- the ransomware cleaning up after itself. 31 recoverable.

### Verify Evidence Integrity

```bash
curl -s -X POST https://playseat.local/forensics/artifacts/01954e21-art-7f00-memdump-00001/verify \
  -H "Authorization: Bearer $TOKEN"
```

```json
{
  "artifact_id": "01954e21-art-7f00-memdump-00001",
  "sha256_verified": true,
  "blake3_verified": true,
  "integrity_status": "intact"
}
```

Both hashes match. Chain of custody intact.

---

## 9.5 -- Minute 30-60: IOC Extraction and Correlation

Extract indicators from forensic evidence and register them in Threat Intel.

### Register IOCs

```bash
# Ransomware binary hash
curl -s -X POST https://playseat.local/threatintel/iocs \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "ioc_type": "hash_sha256",
    "value": "b4c5d6e7f8091a2b3c4d5e6f708192a3b4c5d6e7f8091a2b3c4d5e6f708192a3",
    "confidence": "high",
    "threat_actor": "LockBit-4-Successor",
    "tags": ["ransomware", "double_extortion", "locked3", "2026"]
  }'

# C2 IP
curl -s -X POST https://playseat.local/threatintel/iocs \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "ioc_type": "ip_address",
    "value": "203.0.113.199",
    "confidence": "high",
    "threat_actor": "LockBit-4-Successor",
    "tags": ["ransomware", "c2", "exfil_endpoint"]
  }'

# Persistence registry key
curl -s -X POST https://playseat.local/threatintel/iocs \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "ioc_type": "registry_key",
    "value": "HKLM\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Run\\CsrssHelper",
    "confidence": "high",
    "threat_actor": "LockBit-4-Successor",
    "tags": ["ransomware", "persistence", "dkom"]
  }'
```

### Build Forensic Timeline

```bash
curl -s -X POST https://playseat.local/forensics/timeline/build \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "case_id": "01954e20-case-7f00-forensics-00001",
    "events": [
      {"timestamp": "2026-02-16T22:14:00Z", "event_type": "initial_access", "source": "email_gateway", "description": "Spearphishing attachment to eng_user_47@corp.local. Subject: Q4 Defense Contract Review", "severity": "high"},
      {"timestamp": "2026-02-16T22:16:00Z", "event_type": "execution", "source": "edr_telemetry", "description": "Macro in Contract_Review.docx executed PowerShell download cradle", "severity": "critical"},
      {"timestamp": "2026-02-17T01:30:00Z", "event_type": "lateral_movement", "source": "windows_event_log", "description": "SVC-ENG-BUILD authenticated to FILESRV-ENG-01 via NTLM. No prior history.", "severity": "high"},
      {"timestamp": "2026-02-17T02:45:00Z", "event_type": "exfiltration", "source": "network_capture", "description": "HTTPS POST to 203.0.113.199:443. 47.2 GB transferred over 29 minutes.", "severity": "critical"},
      {"timestamp": "2026-02-17T03:12:00Z", "event_type": "impact", "source": "edr_telemetry", "description": "File encryption initiated. svchost_crypt.exe via process hollowing. .locked3 extension. VSS deleted.", "severity": "critical"}
    ]
  }'
```

```json
{
  "id": "01954e30-tl-7f00-timeline-00001",
  "case_id": "01954e20-case-7f00-forensics-00001",
  "event_count": 5
}
```

The full kill chain: phishing at 22:14 -> execution at 22:16 -> lateral movement at 01:30 -> exfiltration at 02:45 -> encryption at 03:12 -> detection at 03:14.

**Dwell time from initial access to encryption: 4 hours 58 minutes.** Detection was 2 minutes after encryption began. If Sentinel had authentication pattern baselines for service accounts, we could have caught the lateral movement at 01:30 -- 1.5 hours earlier.

---

## 9.6 -- Hour 1-2: Attribution with Threat Genome

With IOCs and TTPs extracted, fingerprint the attacker using Threat Genome.

### Create Genome

```bash
curl -s -X POST https://playseat.local/api/v1/adapt/genome/genomes \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "RANSOMWARE-VLAN300-20260217",
    "threat_actor": "Unknown-Ransomware-2026",
    "description": "Double-extortion ransomware. .locked3 extension. LockBit 4.0 successor TTPs.",
    "family": "LockBit-Successor"
  }'
```

### Add Markers

```bash
GENOME_ID="01954e40-gnm-7f00-genome-ransom001"

# TTP markers
curl -s -X POST "https://playseat.local/api/v1/adapt/genome/genomes/$GENOME_ID/markers" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"marker_type": "ttp", "value": "T1055.012", "weight": 0.95, "confidence": 0.95}'

curl -s -X POST "https://playseat.local/api/v1/adapt/genome/genomes/$GENOME_ID/markers" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"marker_type": "ttp", "value": "T1014", "weight": 0.90, "confidence": 0.90}'

curl -s -X POST "https://playseat.local/api/v1/adapt/genome/genomes/$GENOME_ID/markers" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"marker_type": "ttp", "value": "T1486", "weight": 0.99, "confidence": 0.99}'

curl -s -X POST "https://playseat.local/api/v1/adapt/genome/genomes/$GENOME_ID/markers" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"marker_type": "ttp", "value": "T1490", "weight": 0.95, "confidence": 0.95}'

curl -s -X POST "https://playseat.local/api/v1/adapt/genome/genomes/$GENOME_ID/markers" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"marker_type": "ttp", "value": "T1041", "weight": 0.90, "confidence": 0.90}'

# Behavioral markers
curl -s -X POST "https://playseat.local/api/v1/adapt/genome/genomes/$GENOME_ID/markers" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"marker_type": "behavioral", "value": "double-extortion-encrypt-then-leak", "weight": 0.90, "confidence": 0.90}'

curl -s -X POST "https://playseat.local/api/v1/adapt/genome/genomes/$GENOME_ID/markers" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"marker_type": "behavioral", "value": "aes256ctr-rsa4096-hybrid", "weight": 0.80, "confidence": 0.80}'

# IOC marker
curl -s -X POST "https://playseat.local/api/v1/adapt/genome/genomes/$GENOME_ID/markers" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"marker_type": "ioc_hash", "value": "sha256:b4c5d6e7f8091a2b3c4d5e6f708192a3b4c5d6e7f8091a2b3c4d5e6f708192a3", "weight": 0.99, "confidence": 0.99}'
```

### Run Match

```bash
curl -s -X POST https://playseat.local/api/v1/adapt/genome/match \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "markers": [
      {"marker_type": "ttp", "value": "T1486"},
      {"marker_type": "ttp", "value": "T1490"},
      {"marker_type": "ttp", "value": "T1055.012"},
      {"marker_type": "behavioral", "value": "double-extortion-encrypt-then-leak"},
      {"marker_type": "behavioral", "value": "aes256ctr-rsa4096-hybrid"}
    ],
    "threshold": 0.2
  }'
```

```json
[
  {
    "genome_id": "01954e40-gnm-7f00-genome-ransom001",
    "similarity": 0.625,
    "matched_markers": 5,
    "matched_at": "2026-02-17T04:30:00Z"
  },
  {
    "genome_id": "01954e42-gnm-7f00-lockbit3-known",
    "similarity": 0.333,
    "matched_markers": 4,
    "matched_at": "2026-02-17T04:30:00Z"
  }
]
```

33.3% match against a known LockBit 3.0 genome from previous analysis. Four shared markers: T1486, T1490, volume-shadow-deletion, double-extortion. **Confirmed lineage.** This variant is a LockBit descendant. The new TTPs (process hollowing, DKOM) are evolutionary additions, but the core DNA is LockBit.

---

## 9.7 -- Hour 2-4: Recovery with ADAPT FORTIFY

Containment done, attribution underway. Now we figure out what let them in and make sure it does not happen again.

### Check Coverage Gaps

```bash
for TTP in T1055.012 T1014 T1574.002 T1486 T1490 T1041; do
  echo "=== $TTP ==="
  curl -s "https://playseat.local/api/v1/adapt/coverage/$TTP" \
    -H "Authorization: Bearer $TOKEN" | jq '{technique_id, coverage_status, confidence}'
done
```

```
=== T1055.012 ===
{"technique_id": "T1055.012", "coverage_status": "gap", "confidence": 0.0}
=== T1014 ===
{"technique_id": "T1014", "coverage_status": "gap", "confidence": 0.0}
=== T1574.002 ===
{"technique_id": "T1574.002", "coverage_status": "partial", "confidence": 0.45}
=== T1486 ===
{"technique_id": "T1486", "coverage_status": "covered", "confidence": 0.92}
=== T1490 ===
{"technique_id": "T1490", "coverage_status": "covered", "confidence": 0.88}
=== T1041 ===
{"technique_id": "T1041", "coverage_status": "partial", "confidence": 0.60}
```

Two gaps: T1055.012 (Process Hollowing) and T1014 (DKOM Rootkit). These are the techniques that let the ransomware persist after the initial process kill. We could detect the encryption (T1486) but not the injection that delivered it.

### Approve ADAPT Defense Actions

```bash
# Get pending actions from the current cycle
curl -s https://playseat.local/api/v1/adapt/actions/pending \
  -H "Authorization: Bearer $TOKEN" | jq '.[] | {id, action_type, details}'
```

```bash
# Approve the process hollowing detection rule
curl -s -X POST https://playseat.local/api/v1/adapt/actions/01954e50-act-001/approve \
  -H "Authorization: Bearer $TOKEN"

# Approve the DKOM detection
curl -s -X POST https://playseat.local/api/v1/adapt/actions/01954e50-act-002/approve \
  -H "Authorization: Bearer $TOKEN"
```

---

## 9.8 -- Hour 4-24: Evidence Packaging for Law Enforcement

The legal team wants packages for the FBI (IC3), national CERT, and Europol (the exfil endpoint is EU-hosted).

### Verify Chain of Custody

```bash
curl -s https://playseat.local/forensics/artifacts/01954e21-art-7f00-memdump-00001/custody \
  -H "Authorization: Bearer $TOKEN"
```

```json
{
  "artifact_id": "01954e21-art-7f00-memdump-00001",
  "chain": [
    {"action": "acquired", "handler": "forensic_lead_martinez", "timestamp": "2026-02-17T03:20:00Z", "hash_verified": true},
    {"action": "analyzed", "handler": "forensic_lead_martinez", "timestamp": "2026-02-17T03:25:00Z", "hash_verified": true},
    {"action": "verified", "handler": "ir_commander", "timestamp": "2026-02-17T03:32:00Z", "hash_verified": true}
  ]
}
```

Unbroken chain. Three handlers, three verified checkpoints. SHA-256 and BLAKE3 consistent throughout.

### Generate Executive Briefing

```bash
curl -s -X POST https://playseat.local/api/v1/adapt/briefings \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "template_id": "01954e50-tmpl-7f00-incident-brief",
    "period_start": "2026-02-17T00:00:00Z",
    "period_end": "2026-02-17T23:59:59Z"
  }'
```

### Share IOCs via Mesh

```bash
curl -s -X POST https://playseat.local/api/v1/adapt/mesh/share \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "peer_id": "01954c01-nato-7f00-mesh-peer00000001",
    "intel_type": "ransomware_ioc_package",
    "content": {
      "title": "LockBit 4.0 Successor - Double Extortion IOCs",
      "incident_date": "2026-02-17",
      "iocs": [
        {"type": "hash_sha256", "value": "b4c5d6e7f8091a2b3c4d5e6f708192a3b4c5d6e7f8091a2b3c4d5e6f708192a3"},
        {"type": "ip", "value": "203.0.113.199"},
        {"type": "registry", "value": "HKLM\\\\SOFTWARE\\\\Microsoft\\\\Windows\\\\CurrentVersion\\\\Run\\\\CsrssHelper"}
      ],
      "ttps": ["T1486", "T1490", "T1055.012", "T1014", "T1574.002", "T1041"]
    },
    "confidence": 0.90
  }'
```

---

## 9.9 -- Post-Incident: Lessons Learned and ADAPT PROVE

### Create Lessons Learned

```bash
curl -s -X POST https://playseat.local/incident/incidents/01954e01-aaaa-7f00-ir00-ransomware001/lessons \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "findings": [
      "DETECTION GAP: No baseline for service account auth patterns across VLANs. Lateral movement at 01:30 went undetected for 1.75 hours.",
      "DETECTION GAP: Process hollowing (T1055.012) and DKOM (T1014) not covered by current EDR rules.",
      "SUCCESS: Sentinel egress baseline detected encryption-phase exfiltration within 2 minutes.",
      "SUCCESS: SOAR playbook contained the incident in 6 minutes.",
      "SUCCESS: Forensic evidence maintained chain of custody with dual-hash verification.",
      "IMPROVEMENT: Add service account cross-VLAN authentication baselines to Sentinel.",
      "IMPROVEMENT: Deploy kernel-level integrity monitoring for DKOM detection.",
      "IMPROVEMENT: Reduce backup RPO from 24 hours to 4 hours for classified data."
    ],
    "recommendations": [
      "Deploy 15 new Sentinel baselines for service account authentication",
      "Deploy Sysmon v15 with process hollowing detection",
      "Enable Hypervisor-protected Code Integrity on classified workstations",
      "Implement MFA for service account file server access",
      "Reduce backup RPO to 4 hours for classified engineering data"
    ]
  }'
```

### Advance Through Remaining Phases

```bash
# eradication
curl -s -X POST https://playseat.local/incident/incidents/01954e01-aaaa-7f00-ir00-ransomware001/advance \
  -H "Authorization: Bearer $TOKEN"
# recovery
curl -s -X POST https://playseat.local/incident/incidents/01954e01-aaaa-7f00-ir00-ransomware001/advance \
  -H "Authorization: Bearer $TOKEN"
# lessons_learned
curl -s -X POST https://playseat.local/incident/incidents/01954e01-aaaa-7f00-ir00-ransomware001/advance \
  -H "Authorization: Bearer $TOKEN"
```

### Get Incident Stats

```bash
curl -s https://playseat.local/incident/stats \
  -H "Authorization: Bearer $TOKEN" | jq .
```

---

## 9.10 -- Timeline Summary

| Time | Phase | Action | Elapsed |
|------|-------|--------|---------|
| 03:14 | Detection | Sentinel critical alert on egress anomaly | 0 min |
| 03:15 | Triage | Incident created in Playseat | 1 min |
| 03:19 | Containment | SOAR playbook triggered | 5 min |
| 03:20 | Containment | VLAN isolated, processes killed, accounts locked, C2 blocked | 6 min |
| 03:25 | Forensics | Memory analysis: 4 suspicious, 2 injections, 1 hidden | 11 min |
| 03:30 | Forensics | Disk analysis: 47 deleted files, 12 suspicious paths | 16 min |
| 03:32 | Forensics | Evidence integrity verified (SHA-256 + BLAKE3) | 18 min |
| 03:45 | Correlation | IOCs registered in Threat Intel | 31 min |
| 04:30 | Attribution | Genome: 33.3% match to known LockBit 3.0 | 76 min |
| 05:00 | Fortify | Coverage gaps identified: T1055.012, T1014 | 106 min |
| 06:00 | Recovery | Restoration from backup initiated | 166 min |
| 08:00 | Reporting | Executive briefing generated | 286 min |
| 12:00 | Evidence | Law enforcement packages prepared | 526 min |
| 18:00 | Mesh | IOCs shared with all mesh peers | 886 min |
| 24:00 | Lessons | Post-incident review complete, 5 new baselines deployed | 1246 min |

**Detection to containment: 6 minutes.**
**Detection to attribution: 76 minutes.**
**Detection to full closure: 24 hours.**

---

## 9.11 -- What Went Right and What Did Not

**What worked:**
- SOAR automation cut containment from 45+ minutes to 6. Non-negotiable for double extortion where every minute is exfiltration.
- Sentinel egress baseline caught the anomaly within 2 minutes of encryption start.
- Dual-hash evidence verification survived the full chain of custody review.
- Genome attribution gave us lineage within 76 minutes without external consultation.

**What failed:**
- No Sentinel baseline for service account cross-VLAN authentication. The lateral movement at 01:30 was invisible for 1 hour 44 minutes. That is the gap that let them reach the file server.
- No process hollowing detection. T1055.012 is a known ransomware delivery technique and we had zero coverage.
- Backup RPO of 24 hours meant we lost a full day of engineering work. For classified data, 4-hour RPO should be the floor.

**The uncomfortable truth:** We caught them at the encryption stage, not the initial access stage. The phishing email landed at 22:14. We did not detect anything for 5 hours. A properly baselined Sentinel deployment would have flagged the PowerShell download cradle at 22:16 or the lateral movement at 01:30. We need to be faster.

The 3 AM call is never fun. But with Playseat running the playbook, it is controlled chaos instead of just chaos. Every step documented, every piece of evidence hashed, every action auditable.

---

*Next chapter: hunting APT-29 proactively across a defense network.*

---

(c) 2026 Playseat -- All Rights Reserved | Proprietary and Confidential
