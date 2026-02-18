# Chapter 30: Case Study -- The Clara Protocol

**Classification: UNCLASSIFIED // FOR OFFICIAL USE ONLY**
**Platform Version: 0.2.0 | Scenario Type: Full ADAPT Cycle + Mesh Sharing + GEOINT + Threat Genome**

> "The evidence is in the mesh. Find the genome. Save the children."
> -- Last known message from Clara Dubois, 2026-02-14, 22:47 UTC

---

## Prologue

I have written every case study in this book with professional detachment. Clean analysis, clear methodology, evidence chains you could present to a parliamentary committee. This one is different.

This one is personal.

I'm writing it at 06:17 on a Sunday morning. I haven't slept. There are four empty coffee mugs on my desk and my hands won't stop shaking, and it's not from the caffeine. Somewhere in Marseille, a woman I once loved is either alive or dead, and the answer depends on whether I can follow a trail of breadcrumbs she left through the one platform she knew I'd be running.

Clara knew I'd use Playseat. She designed her dead drops around its capabilities. Every clue she left maps to a module, a query, an ADAPT phase. She didn't just hide evidence -- she engineered a treasure hunt that only someone with deep platform access could follow.

This is the story of how I found it. All of it. And what happened when I did.

---

## Overview

**Operation Codename**: SILENT MERCY
**Threat Actor**: PHANTOM MERCY (state-sponsored APT, attributed to GRU Unit 74455 with moderate-high confidence) -- tracked internally as UNC7731-HUM
**Target Organization**: Fondation Lumiere -- International Humanitarian Aid Network -- *synthetic*
**Target Infrastructure**: 14 field offices across West Africa and Mediterranean, encrypted mesh communications network, donor management systems, logistics platforms
**Duration**: One night (22:00 Saturday to 06:00 Sunday -- 8 hours)
**ADAPT Phases Exercised**: DISCOVER, CORRELATE, VALIDATE (partial -- time-critical)
**Platform Modules Used**: 18 of 25+ available
**Human Cost**: 1 missing person -- Clara Dubois, Senior Cryptographic Engineer
**Stakes**: Evidence of state-sponsored espionage using humanitarian networks as cover; potential compromise of 340,000 aid recipient records including children in conflict zones

### Background: When Humanitarian Networks Become Intelligence Targets

In December 2025, Amnesty International published a report documenting the growing trend of state actors infiltrating humanitarian organizations. The logic is cold and precise: aid networks have access to conflict zones, displaced populations, and communications infrastructure in regions where traditional intelligence collection is difficult. A compromised aid network gives a state actor eyes on the ground, reliable cover identities for operatives, and access to biometric data on vulnerable populations.

CERT-FR Advisory CERTFR-2026-AVI-0087, published January 2026, warned of APT activity targeting French-registered humanitarian NGOs with operations in the Sahel region. The advisory listed 23 IOCs and referenced the PHANTOM MERCY designation -- a threat actor combining signals intelligence tradecraft with cyber operations.

I didn't pay much attention to the advisory when it came out. I should have. Because Clara Dubois was working for one of the organizations on that target list.

### Dramatis Personae (All Synthetic)

| Role | Name | Callsign | Contact |
|------|------|----------|---------|
| Senior Threat Analyst | Ethan Raines | WATCHMAN-1 | +33-555-2001 |
| Missing Person / Cryptographer | Clara Dubois | LUMIERE-9 | +33-555-2002 (dark) |
| SOC Deputy (Night Shift) | Sgt. Amara Diallo | NIGHTFALL-3 | +33-555-2003 |
| Fondation Lumiere IT Director | Jean-Marc Lefebvre | BEACON-1 | +33-555-2004 |
| DGSI Cyber Liaison | Capitaine Lucien Moreau | BADGE-FR | +33-555-2005 |
| ANSSI Incident Coordinator | Dr. Sylvie Beaumont | ANSSI-7 | +33-555-2006 |
| Interpol Missing Persons | Inspector Kenji Watanabe | TRACE-INT | +81-555-2007 |
| Mesh Peer: NATO CERT | Major Elena Vasquez | ALLIANCE-4 | +32-555-2008 |
| Mesh Peer: EU-CERT | Dr. Henrik Larsen | EUCERT-2 | +46-555-2009 |
| Mesh Peer: Five Eyes Node (AU) | Agent Liam Okafor | FVEY-AU-6 | +61-555-2010 |

### Network Topology -- Fondation Lumiere (Synthetic)

| Segment | CIDR | Purpose | Classification |
|---------|------|---------|---------------|
| HQ Paris | 10.200.10.0/24 | Headquarters, donor systems, finance | RESTRICTED |
| Field Operations | 10.200.20.0/24 | West African field offices (mesh nodes) | CONFIDENTIAL |
| Logistics Network | 10.200.30.0/24 | Supply chain, warehouse management | RESTRICTED |
| Encrypted Comms | 10.200.40.0/24 | Signal-based secure messaging relay | SECRET |
| Donor Portal | 10.200.50.0/24 | Public-facing donation and reporting | OFFICIAL |
| Clara's Lab | 10.200.60.0/24 | Cryptographic research workstations | SECRET |
| Backup/Archive | 10.200.70.0/24 | Cold storage, encrypted backups | RESTRICTED |

### Key Infrastructure (Synthetic)

| Hostname | IP | OS | Role |
|----------|----|----|------|
| HQ-DC-01 | 10.200.10.5 | Ubuntu 22.04 | Domain controller |
| DONOR-APP-01 | 10.200.50.10 | RHEL 9 | Donor management platform |
| MESH-RELAY-01 | 10.200.40.5 | Alpine Linux | Encrypted field communications relay |
| MESH-RELAY-02 | 10.200.40.6 | Alpine Linux | Secondary mesh relay (Dakar) |
| MESH-RELAY-03 | 10.200.40.7 | Alpine Linux | Tertiary mesh relay (Bamako) |
| LOG-RELAY-01 | 10.200.30.20 | Ubuntu 22.04 | Centralized logging |
| CRYPTO-WS-01 | 10.200.60.10 | Fedora 39 | Clara's primary workstation |
| CRYPTO-WS-02 | 10.200.60.11 | Fedora 39 | Clara's air-gapped research machine |
| BACKUP-01 | 10.200.70.5 | Debian 12 | Encrypted backup server |
| VPN-GW-01 | 10.200.10.1 | WireGuard | HQ VPN gateway |

---

## Three Years Ago: DEFCON 31, Las Vegas

I need to tell you about Clara before I tell you about the investigation, because you can't understand what I did that night without understanding what she means to me.

I met Clara Dubois on August 11th, 2023, at 14:32 Pacific Time, at the Wireless Village at DEFCON 31. I know the exact time because she spilled half a Red Bull on my laptop and the timestamp on the crash log was 14:32:07.

She was presenting a paper on post-quantum key exchange protocols for mesh networks in humanitarian disaster zones. I was in the audience because I'd misread the schedule and thought it was a talk on mesh network threat modeling. By the time I realized my mistake, she was three minutes into a demonstration of lattice-based cryptography that was the most elegant technical work I'd seen in a decade.

Clara was -- is -- a contradiction. A Sorbonne mathematician who spent her weekends volunteering with Medecins Sans Frontieres' tech team. A cryptographer who could derive Kyber from first principles on a napkin but cried at UNICEF commercials. She had dark hair that she kept in a perpetual messy bun, wire-rimmed glasses that she was constantly pushing up her nose, and a laugh that made you feel like the cleverest person in the room even when you'd just said something stupid.

After her talk, she found me in the hallway. "You're the one whose laptop I killed," she said, in an accent that made English sound like music. "Let me buy you a drink. I owe you a ThinkPad."

We talked for seven hours. About cryptography, about humanitarian technology, about the ethics of intelligence work. I told her about Playseat -- the early version, back when it was just 40 crates and a dream. Her eyes lit up when I described the evidence chain system. "Dual hashing with BLAKE3 and SHA-256?" she said. "That's exactly what humanitarian forensics needs. Do you know how many war crimes tribunals have thrown out digital evidence because the chain of custody was garbage?"

We dated for eleven months. Long distance -- she was in Paris, I was rotating between Brussels and Berlin. We made it work until we couldn't. She wanted me to join her at Fondation Lumiere, building cryptographic infrastructure for aid networks. I wanted her to join me at the SOC, applying her skills to defensive intelligence. Neither of us would bend. The last time I saw her was in a cafe in Montmartre, both of us pretending the coffee was the reason we couldn't speak.

That was fourteen months ago.

Three days ago, she sent me a message.

---

## Friday, February 13th, 2026 -- The Message

The message arrived at 22:47 UTC on Valentine's Eve. It came through Signal, from a number I hadn't seen in over a year but never deleted from my contacts.

> **Clara Dubois** [22:47 UTC]
> Ethan. Don't reply to this. Don't call this number.
> I found something inside the Lumiere network. Something that shouldn't be there.
> They're using us. Using the aid convoys, the mesh relays, the refugee registration databases. All of it. Cover for SIGINT collection on three African governments.
> I have proof. Packet captures. Firmware dumps. Financial ledgers showing payments routed through donor shell accounts.
> I can't go to the police. I can't go to ANSSI. There are people inside both who are connected to this.
> The evidence is in the mesh. Find the genome. Save the children.
> You'll know how to find it. You built the tools.
> I'm sorry about Montmartre. I was wrong.
> -- C

I read it four times. Then I read it again. Then I sat in the dark of my apartment for twenty minutes, feeling like the floor had dropped out from under me.

By 23:00, I was at the SOC.

---

## 22:00 UTC Saturday, February 14th -- Valentine's Night

I'd spent all of Friday trying to reach Clara through every channel I could think of. Signal -- message delivered but not read. Email -- bounced from her Fondation address. Her personal phone went straight to voicemail with a generic carrier message, which meant the SIM was either dead or pulled. I called Jean-Marc Lefebvre, the Fondation's IT director, and got a careful non-answer: "Clara took a few days off. Personal reasons."

That was a lie. I could hear it in the half-second pause before "personal reasons."

By Saturday evening, I'd filed a missing person report with DGSI and contacted Interpol's missing persons unit. Both told me the same thing: without evidence of a crime, they couldn't escalate. Clara was an adult who had taken time off work. People do that.

I told them about the message. They told me Signal messages aren't evidence.

Fine. I'd get them evidence.

I sat down at my workstation at 22:00 on Valentine's night, opened a terminal, and launched Playseat. The irony wasn't lost on me. Every couple in Paris was at dinner. I was about to spend the most romantic night of the year running SQL queries.

### 22:03 -- Creating the Campaign

First things first. Every investigation in Playseat starts with a campaign. A campaign is the organizational container -- it's where findings, evidence, IOCs, and audit trails get linked.

```bash
# Create the investigation campaign
curl -s -X POST http://localhost:3000/api/v1/campaigns \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "SILENT MERCY",
    "description": "Investigation into state-sponsored infiltration of Fondation Lumiere humanitarian network and disappearance of Clara Dubois",
    "severity": "critical",
    "campaign_type": "investigation",
    "status": "active",
    "tags": ["humanitarian", "APT", "PHANTOM-MERCY", "missing-person", "GEOINT"]
  }' | jq '.'
```

```json
{
  "id": "0195a100-c001-7000-8000-000000000001",
  "name": "SILENT MERCY",
  "description": "Investigation into state-sponsored infiltration of Fondation Lumiere humanitarian network and disappearance of Clara Dubois",
  "severity": "critical",
  "campaign_type": "investigation",
  "status": "active",
  "created_by": "0194c100-0001-7000-8000-000000000001",
  "created_at": "2026-02-14T22:03:14Z",
  "updated_at": "2026-02-14T22:03:14Z"
}
```

Campaign `0195a100-c001-7000-8000-000000000001`. SILENT MERCY was live.

I stared at the campaign ID on screen. Every investigation I've ever run has felt like a puzzle. This one felt like a ticking bomb.

### 22:07 -- Registering Assets

I registered the key assets from Fondation Lumiere's infrastructure. Jean-Marc had given me read-only VPN access to their monitoring dashboards three months ago when I'd helped them with a firewall audit as a personal favor to Clara. He'd never revoked it. I didn't feel guilty about using it.

```bash
# Register Clara's workstation as a critical asset
curl -s -X POST http://localhost:3000/api/v1/assets \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "CRYPTO-WS-01",
    "asset_type": "workstation",
    "ip_address": "10.200.60.10",
    "hostname": "crypto-ws-01.lumiere.ngo.synth",
    "os": "Fedora 39",
    "criticality": "critical",
    "owner": "Clara Dubois",
    "notes": "Primary workstation of missing cryptographic engineer. Last login 2026-02-13 21:30 UTC."
  }' | jq '.id'
```

```json
"0195a100-c002-7000-8000-000000000001"
```

I registered all ten infrastructure nodes. Each one got a criticality rating. Each one got a note. Clara's workstations got "CRITICAL" because whatever she found, she found it there.

---

## Phase 1: DISCOVER -- 22:15 to 23:30

### 22:15 -- Initiating the ADAPT DISCOVER Cycle

Clara's message said "the evidence is in the mesh." That meant the Fondation's encrypted communications relay -- the three MESH-RELAY nodes that connected field offices across West Africa to Paris HQ. She'd helped build that mesh. If she'd hidden evidence inside it, she'd have done it in a way that looked like normal traffic to anyone who wasn't looking with the right tools.

I initiated a DISCOVER cycle focused on the Fondation's network.

```bash
# Start ADAPT DISCOVER cycle targeting Fondation Lumiere infrastructure
curl -s -X POST http://localhost:3000/api/v1/adapt/cycles \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "cycle_type": "discover",
    "campaign_id": "0195a100-c001-7000-8000-000000000001",
    "target_scope": {
      "networks": ["10.200.0.0/16"],
      "focus_segments": ["10.200.40.0/24", "10.200.60.0/24"],
      "time_window": "7d",
      "priority": "critical"
    },
    "parameters": {
      "ioc_scan": true,
      "anomaly_detection": true,
      "baseline_comparison": true,
      "threat_feed_correlation": true
    }
  }' | jq '.'
```

```json
{
  "id": "0195a100-c003-7000-8000-000000000001",
  "cycle_number": 7842,
  "cycle_type": "discover",
  "campaign_id": "0195a100-c001-7000-8000-000000000001",
  "status": "running",
  "started_at": "2026-02-14T22:15:33Z",
  "estimated_completion": "2026-02-14T22:25:00Z"
}
```

While the DISCOVER cycle ran, I pulled the CERT-FR advisory IOCs and cross-referenced them against the Fondation's network logs.

### 22:18 -- Ingesting PHANTOM MERCY IOCs

```bash
# Ingest PHANTOM MERCY IOCs from CERT-FR advisory
curl -s -X POST http://localhost:3000/api/v1/threatintel/iocs/batch \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "source": "CERTFR-2026-AVI-0087",
    "tlp": "amber",
    "campaign_id": "0195a100-c001-7000-8000-000000000001",
    "iocs": [
      {"type": "ip", "value": "185.220.101.47", "confidence": 0.85, "description": "PHANTOM MERCY C2 node - Bucharest VPS"},
      {"type": "ip", "value": "91.219.237.88", "confidence": 0.82, "description": "PHANTOM MERCY exfil relay - Moscow hosting"},
      {"type": "ip", "value": "45.153.240.12", "confidence": 0.78, "description": "PHANTOM MERCY staging - Sofia datacenter"},
      {"type": "domain", "value": "update-service.humanitarian-ops.net", "confidence": 0.91, "description": "Spoofed humanitarian update domain"},
      {"type": "domain", "value": "mesh-sync.global-ngo.org", "confidence": 0.88, "description": "Fake mesh synchronization service"},
      {"type": "domain", "value": "cert-renewal.aid-network.com", "confidence": 0.79, "description": "Certificate phishing infrastructure"},
      {"type": "hash_sha256", "value": "a3f2b8c91e4d7f6a5b0c3d2e1f098765432abcdef0123456789abcdef012345", "confidence": 0.93, "description": "MESHWEAVER backdoor Stage 1 dropper"},
      {"type": "hash_sha256", "value": "7d8e9f0a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8", "confidence": 0.90, "description": "MESHWEAVER Stage 2 implant - Linux variant"},
      {"type": "hash_sha256", "value": "f1e2d3c4b5a69788796a5b4c3d2e1f0a9b8c7d6e5f4a3b2c1d0e9f8a7b6c5d4e", "confidence": 0.87, "description": "Modified WireGuard tunnel binary with exfil channel"}
    ]
  }' | jq '.ingested_count'
```

```json
9
```

Nine IOCs. The CERT-FR advisory had 23, but these 9 were the ones specifically tagged as related to humanitarian sector targeting. The rest were generic infrastructure indicators that could match half the botnets on the internet.

### 22:24 -- DISCOVER Cycle Results

The cycle completed faster than estimated. It always does when there's something to find.

```bash
# Get DISCOVER cycle results
curl -s http://localhost:3000/api/v1/adapt/cycles/0195a100-c003-7000-8000-000000000001 \
  -H "Authorization: Bearer $TOKEN" | jq '.'
```

```json
{
  "id": "0195a100-c003-7000-8000-000000000001",
  "cycle_number": 7842,
  "status": "completed",
  "started_at": "2026-02-14T22:15:33Z",
  "completed_at": "2026-02-14T22:23:47Z",
  "results": {
    "total_anomalies": 14,
    "ioc_matches": 6,
    "new_indicators": 8,
    "severity_breakdown": {
      "critical": 3,
      "high": 5,
      "medium": 4,
      "low": 2
    },
    "matched_feeds": ["CERTFR-2026-AVI-0087", "MISP-NATO-CYBER", "OSINT-PHANTOM-MERCY"]
  }
}
```

Six IOC matches. Three critical anomalies. My stomach dropped.

### 22:26 -- The Critical Findings

```bash
# Pull critical findings from the DISCOVER cycle
curl -s "http://localhost:3000/api/v1/findings?campaign_id=0195a100-c001-7000-8000-000000000001&severity=critical" \
  -H "Authorization: Bearer $TOKEN" | jq '.'
```

```json
[
  {
    "id": "0195a100-f001-7000-8000-000000000001",
    "title": "PHANTOM MERCY C2 beacon detected on MESH-RELAY-01",
    "severity": "critical",
    "description": "Outbound HTTPS connections from 10.200.40.5 to 185.220.101.47 (known PHANTOM MERCY C2) detected at 4-hour intervals. Traffic pattern consistent with MESHWEAVER implant heartbeat. First seen 2026-01-28, last seen 2026-02-13 20:00 UTC.",
    "asset_id": "0195a100-c002-7000-8000-000000000005",
    "ioc_matches": ["185.220.101.47"],
    "mitre_techniques": ["T1071.001", "T1573.002"],
    "created_at": "2026-02-14T22:23:48Z"
  },
  {
    "id": "0195a100-f001-7000-8000-000000000002",
    "title": "Modified WireGuard binary on CRYPTO-WS-01",
    "severity": "critical",
    "description": "File hash mismatch on /usr/bin/wg detected. Binary SHA-256 matches PHANTOM MERCY modified WireGuard (f1e2d3c4...). Binary contains embedded exfiltration channel that tunnels data inside legitimate WireGuard traffic. Found on Clara Dubois workstation.",
    "asset_id": "0195a100-c002-7000-8000-000000000001",
    "ioc_matches": ["f1e2d3c4b5a69788796a5b4c3d2e1f0a9b8c7d6e5f4a3b2c1d0e9f8a7b6c5d4e"],
    "mitre_techniques": ["T1036.005", "T1041"],
    "created_at": "2026-02-14T22:23:48Z"
  },
  {
    "id": "0195a100-f001-7000-8000-000000000003",
    "title": "Anomalous data exfiltration from refugee registration database",
    "severity": "critical",
    "description": "Database DONOR-APP-01 showing bulk SELECT queries against refugee_biometric_records table originating from MESH-RELAY-02 (10.200.40.6). 340,000 records accessed between 2026-02-01 and 2026-02-12. Query patterns inconsistent with legitimate application behavior.",
    "asset_id": "0195a100-c002-7000-8000-000000000008",
    "ioc_matches": [],
    "mitre_techniques": ["T1005", "T1048.002"],
    "created_at": "2026-02-14T22:23:49Z"
  }
]
```

I read Finding #3 twice, and then I said something I can't print in a professional case study.

340,000 refugee biometric records. Names, photographs, fingerprints, iris scans of displaced families -- including children -- being siphoned through a compromised mesh relay to a server in Bucharest. Clara's message suddenly made brutal sense.

*Save the children.*

She hadn't been speaking metaphorically.

### 22:31 -- Clara's Last Login

I needed to understand what Clara had found and when she found it. I queried the audit logs for her workstation.

```sql
-- Query Clara's last workstation activity
SELECT
    event_time,
    event_type,
    source_ip,
    destination_ip,
    user_agent,
    details
FROM audit_events
WHERE asset_id = '0195a100-c002-7000-8000-000000000001'
  AND event_time >= '2026-02-13T00:00:00Z'
ORDER BY event_time DESC
LIMIT 20;
```

```
event_time                | event_type        | source_ip     | destination_ip  | details
--------------------------+-------------------+---------------+-----------------+-------------------------------------------
2026-02-13T22:47:12Z      | signal_message    | 10.200.60.10  | (external)      | Encrypted Signal session - outbound
2026-02-13T22:44:08Z      | file_encrypt      | 10.200.60.10  | (local)         | AES-256-GCM encryption: /home/clara/evidence/
2026-02-13T22:38:55Z      | file_copy         | 10.200.60.10  | 10.200.70.5     | SCP transfer to BACKUP-01: evidence_pkg.enc
2026-02-13T22:31:03Z      | pcap_capture      | 10.200.60.10  | 10.200.40.0/24  | tcpdump on mesh relay subnet - 4.2GB capture
2026-02-13T22:15:41Z      | firmware_dump     | 10.200.60.10  | 10.200.40.5     | Firmware extraction from MESH-RELAY-01
2026-02-13T21:58:22Z      | db_query          | 10.200.60.10  | 10.200.50.10    | SELECT on transaction_ledger WHERE type='donor_transfer'
2026-02-13T21:47:09Z      | ssh_login         | 10.200.60.10  | (local)         | SSH key authentication - user: clara
2026-02-13T21:30:44Z      | workstation_unlock| 10.200.60.10  | (local)         | Screen unlock - biometric
```

There it was. Her last night. Reconstructed in eight log entries.

She unlocked her workstation at 21:30. By 21:47 she was SSH'd in and working. She queried the donor transaction ledger at 21:58 -- looking for the financial trail. She dumped the firmware from MESH-RELAY-01 at 22:15 -- getting proof that the relay had been compromised. She ran a packet capture on the entire mesh subnet at 22:31 -- 4.2 gigabytes of traffic. She encrypted everything at 22:44. Copied the encrypted package to the backup server at 22:38. Then, at 22:47, she sent me the Signal message.

After that -- nothing. No logout. No shutdown. The workstation was still powered on when the cleaning staff found it the next morning, screen locked, cursor blinking.

Clara had collected her evidence, encrypted it, backed it up, sent me the breadcrumb, and vanished. All in 77 minutes. That's not panic. That's a plan.

She'd planned for this. She'd known they might come for her, and she'd prepared a protocol.

The Clara Protocol.

---

## Phase 2: CORRELATE -- 23:30 to 00:45

### 23:33 -- Linking IOCs to PHANTOM MERCY

The DISCOVER phase had given me the what. Now I needed the who. The IOC matches pointed toward PHANTOM MERCY, but I needed to be certain. In defensive intelligence, "pretty sure" gets people killed.

I ran a correlation analysis across all available threat intelligence feeds.

```bash
# Correlate findings with known threat actor profiles
curl -s -X POST http://localhost:3000/api/v1/adapt/correlate \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "campaign_id": "0195a100-c001-7000-8000-000000000001",
    "finding_ids": [
      "0195a100-f001-7000-8000-000000000001",
      "0195a100-f001-7000-8000-000000000002",
      "0195a100-f001-7000-8000-000000000003"
    ],
    "correlation_targets": {
      "threat_actors": true,
      "campaigns": true,
      "malware_families": true,
      "infrastructure": true,
      "ttps": true
    },
    "confidence_threshold": 0.65,
    "time_window": "90d"
  }' | jq '.'
```

```json
{
  "id": "0195a100-d001-7000-8000-000000000001",
  "status": "completed",
  "correlation_results": {
    "threat_actors": [
      {
        "actor_name": "PHANTOM MERCY",
        "aliases": ["UNC7731-HUM", "SANDSTORM BEAR", "Fancy Medic"],
        "attribution": "GRU Unit 74455 (Sandworm adjacent)",
        "confidence": 0.87,
        "matching_ttps": 7,
        "matching_iocs": 5,
        "matching_infrastructure": 3,
        "first_seen": "2024-06-15",
        "known_targets": ["humanitarian_orgs", "ngo_networks", "aid_logistics"]
      }
    ],
    "malware_families": [
      {
        "family": "MESHWEAVER",
        "version": "2.1",
        "type": "implant_framework",
        "capabilities": ["mesh_hijack", "data_exfil", "wireguard_tunnel_abuse", "firmware_persistence"],
        "confidence": 0.91
      }
    ],
    "ttp_matches": [
      {"technique": "T1071.001", "name": "Web Protocols", "tactic": "command_and_control"},
      {"technique": "T1573.002", "name": "Asymmetric Cryptography", "tactic": "command_and_control"},
      {"technique": "T1036.005", "name": "Match Legitimate Name", "tactic": "defense_evasion"},
      {"technique": "T1041", "name": "Exfiltration Over C2 Channel", "tactic": "exfiltration"},
      {"technique": "T1005", "name": "Data from Local System", "tactic": "collection"},
      {"technique": "T1048.002", "name": "Exfiltration Over Asymmetric Encrypted Non-C2 Protocol", "tactic": "exfiltration"},
      {"technique": "T1542.001", "name": "System Firmware", "tactic": "persistence"}
    ],
    "linked_campaigns": [
      {"name": "SAHEL SHADOW", "date": "2025-09", "target": "French INGO in Mali"},
      {"name": "MERCY CORRIDOR", "date": "2025-11", "target": "Swiss Red Cross affiliate network"},
      {"name": "AID ECLIPSE", "date": "2026-01", "target": "German humanitarian logistics provider"}
    ]
  }
}
```

0.87 confidence on PHANTOM MERCY. Three linked campaigns over the past six months, all targeting humanitarian organizations. The MESHWEAVER malware family was their signature tool -- a framework specifically designed to compromise mesh relay networks used by aid organizations.

These people had been doing this for at least eight months. Clara had stumbled into the middle of an ongoing operation.

I felt sick.

### 23:41 -- Querying the Ontology Graph

I needed to map the full relationship landscape. Who was connected to whom, how, and where. The ontology graph is Playseat's connective tissue -- a typed, weighted, temporal knowledge graph that links every entity through named relationships.

```bash
# Create entities for graph mapping
curl -s -X POST http://localhost:3000/api/v1/ontology/entities/batch \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "campaign_id": "0195a100-c001-7000-8000-000000000001",
    "entities": [
      {"name": "Clara Dubois", "entity_type": "person", "properties": {"role": "cryptographic_engineer", "org": "Fondation Lumiere", "status": "missing", "last_seen": "2026-02-13T22:47Z"}, "confidence": 1.0},
      {"name": "PHANTOM MERCY", "entity_type": "threat_actor", "properties": {"attribution": "GRU Unit 74455", "target_sector": "humanitarian"}, "confidence": 0.87},
      {"name": "MESHWEAVER v2.1", "entity_type": "malware", "properties": {"type": "implant_framework", "platform": "linux"}, "confidence": 0.91},
      {"name": "Fondation Lumiere", "entity_type": "organization", "properties": {"type": "humanitarian_ngo", "hq": "Paris", "field_offices": 14}, "confidence": 1.0},
      {"name": "185.220.101.47", "entity_type": "ip_address", "properties": {"hosting": "Bucharest VPS", "role": "c2_server"}, "confidence": 0.85},
      {"name": "91.219.237.88", "entity_type": "ip_address", "properties": {"hosting": "Moscow hosting", "role": "exfil_relay"}, "confidence": 0.82},
      {"name": "MESH-RELAY-01", "entity_type": "infrastructure", "properties": {"ip": "10.200.40.5", "compromised": true}, "confidence": 0.95},
      {"name": "Refugee Biometric DB", "entity_type": "data_store", "properties": {"records": 340000, "data_type": "biometric", "classification": "PII_SENSITIVE"}, "confidence": 1.0},
      {"name": "CRYPTO-WS-01", "entity_type": "workstation", "properties": {"ip": "10.200.60.10", "user": "Clara Dubois", "status": "evidence_source"}, "confidence": 1.0},
      {"name": "evidence_pkg.enc", "entity_type": "evidence", "properties": {"encryption": "AES-256-GCM", "location": "BACKUP-01", "size": "4.2GB"}, "confidence": 1.0},
      {"name": "Shell Account Alpha", "entity_type": "financial", "properties": {"bank": "Unknown", "purpose": "donor_transfer_laundering"}, "confidence": 0.72},
      {"name": "Marseille Signal", "entity_type": "location", "properties": {"lat": 43.2965, "lon": 5.3698, "type": "last_known_signal"}, "confidence": 0.68}
    ]
  }' | jq '.created_count'
```

```json
12
```

Then the relationships:

```bash
# Map entity relationships
curl -s -X POST http://localhost:3000/api/v1/ontology/relationships/batch \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "campaign_id": "0195a100-c001-7000-8000-000000000001",
    "relationships": [
      {"source": "PHANTOM MERCY", "target": "MESHWEAVER v2.1", "type": "operates", "weight": 0.91},
      {"source": "PHANTOM MERCY", "target": "185.220.101.47", "type": "controls", "weight": 0.85},
      {"source": "PHANTOM MERCY", "target": "91.219.237.88", "type": "controls", "weight": 0.82},
      {"source": "PHANTOM MERCY", "target": "Fondation Lumiere", "type": "targets", "weight": 0.87},
      {"source": "PHANTOM MERCY", "target": "Refugee Biometric DB", "type": "exfiltrates", "weight": 0.83},
      {"source": "MESHWEAVER v2.1", "target": "MESH-RELAY-01", "type": "deployed_on", "weight": 0.95},
      {"source": "MESHWEAVER v2.1", "target": "CRYPTO-WS-01", "type": "deployed_on", "weight": 0.88},
      {"source": "MESH-RELAY-01", "target": "185.220.101.47", "type": "beacons_to", "weight": 0.90},
      {"source": "Clara Dubois", "target": "Fondation Lumiere", "type": "employed_by", "weight": 1.0},
      {"source": "Clara Dubois", "target": "CRYPTO-WS-01", "type": "primary_user", "weight": 1.0},
      {"source": "Clara Dubois", "target": "evidence_pkg.enc", "type": "created", "weight": 1.0},
      {"source": "Clara Dubois", "target": "Marseille Signal", "type": "last_known_at", "weight": 0.68},
      {"source": "evidence_pkg.enc", "target": "CRYPTO-WS-01", "type": "sourced_from", "weight": 1.0},
      {"source": "Shell Account Alpha", "target": "Fondation Lumiere", "type": "routes_through", "weight": 0.72},
      {"source": "Shell Account Alpha", "target": "PHANTOM MERCY", "type": "funds", "weight": 0.65},
      {"source": "185.220.101.47", "target": "91.219.237.88", "type": "relays_to", "weight": 0.78}
    ]
  }' | jq '.created_count'
```

```json
16
```

### 23:48 -- Traversing the Graph

With 12 entities and 16 relationships mapped, I ran a graph traversal starting from Clara.

```bash
# Traverse the ontology graph from Clara - 3 hops
curl -s "http://localhost:3000/api/v1/ontology/graph/traverse?entity_name=Clara%20Dubois&max_hops=3&min_weight=0.5" \
  -H "Authorization: Bearer $TOKEN" | jq '.'
```

```json
{
  "root": "Clara Dubois",
  "traversal_depth": 3,
  "nodes_visited": 12,
  "paths": [
    {
      "path": ["Clara Dubois", "CRYPTO-WS-01", "MESHWEAVER v2.1", "PHANTOM MERCY"],
      "total_weight": 2.70,
      "interpretation": "Clara's workstation was compromised by MESHWEAVER, operated by PHANTOM MERCY"
    },
    {
      "path": ["Clara Dubois", "evidence_pkg.enc", "CRYPTO-WS-01", "MESHWEAVER v2.1"],
      "total_weight": 2.79,
      "interpretation": "Clara created encrypted evidence package from compromised workstation data"
    },
    {
      "path": ["Clara Dubois", "Fondation Lumiere", "PHANTOM MERCY", "Refugee Biometric DB"],
      "total_weight": 2.70,
      "interpretation": "Clara's employer targeted by PHANTOM MERCY for biometric data exfiltration"
    },
    {
      "path": ["Clara Dubois", "Marseille Signal", null, null],
      "total_weight": 0.68,
      "interpretation": "Last known location signal from Marseille (low confidence)"
    }
  ]
}
```

I stared at the graph visualization on screen. The lines converged on two nodes: PHANTOM MERCY and Clara Dubois. She was at the center of everything. The target had found the operation, and the operation had found the target.

> *I whispered her name at the monitor like a prayer. It didn't help. Nothing was going to help except doing the work.*

### 23:55 -- Financial Transaction Analysis

Clara's audit log showed she'd queried the donor transaction ledger at 21:58. She'd found something in the money trail. I ran the same query.

```sql
-- Trace anomalous donor transfers matching Clara's query pattern
SELECT
    t.id,
    t.transaction_date,
    t.source_account,
    t.destination_account,
    t.amount_eur,
    t.reference_code,
    t.donor_id,
    d.donor_name,
    d.country_code,
    t.status,
    t.notes
FROM transaction_ledger t
JOIN donors d ON t.donor_id = d.id
WHERE t.transaction_type = 'donor_transfer'
  AND t.amount_eur > 50000
  AND t.transaction_date BETWEEN '2025-06-01' AND '2026-02-13'
ORDER BY t.transaction_date DESC;
```

```
id       | transaction_date  | source_account        | destination_account      | amount_eur | reference_code     | donor_name                          | country_code | status
---------+-------------------+-----------------------+--------------------------+------------+--------------------+-------------------------------------+--------------+--------
TXN-0847 | 2026-02-10        | CH-ZURICH-8827441     | FR-PARIS-LUMIERE-001     |    175,000 | MERCY-FIELD-2026Q1 | Stiftung Humanitas (synthetic)      | CH           | cleared
TXN-0831 | 2026-01-15        | CY-LIMASSOL-3341209   | FR-PARIS-LUMIERE-001     |    250,000 | MERCY-LOGISTICS-Q4 | Meridian Global Trust (synthetic)   | CY           | cleared
TXN-0809 | 2025-11-22        | CY-LIMASSOL-3341209   | FR-PARIS-LUMIERE-001     |    200,000 | MERCY-COMMS-Q3     | Meridian Global Trust (synthetic)   | CY           | cleared
TXN-0788 | 2025-09-08        | AE-DUBAI-DIFC-7790022 | FR-PARIS-LUMIERE-001     |    310,000 | MERCY-INFRA-Q2     | Zenith Charitable Holdings (synth.) | AE           | cleared
TXN-0762 | 2025-06-14        | AE-DUBAI-DIFC-7790022 | FR-PARIS-LUMIERE-001     |    290,000 | MERCY-STARTUP      | Zenith Charitable Holdings (synth.) | AE           | cleared
```

There it was. Five large transfers totaling EUR 1.225 million over eight months, all flowing into Fondation Lumiere's operational account. Three different "donor" entities in three different jurisdictions -- Switzerland, Cyprus, and the UAE -- all classic shell company jurisdictions. And every single reference code started with "MERCY."

MERCY.

As in PHANTOM MERCY.

They weren't just using the aid network as cover. They were funding it. The donations were the mechanism -- real money, from shell accounts, paying for real humanitarian operations that happened to provide perfect cover for intelligence collection in West African conflict zones.

I registered the financial entities in the ontology graph and linked them. The picture was becoming horrifyingly clear.

### 00:12 -- The MESHWEAVER Malware Analysis

I needed to understand exactly what was on Clara's workstation. The DISCOVER cycle had identified the modified WireGuard binary, but I needed a full analysis. I submitted the binary hash to the sandbox.

```bash
# Submit MESHWEAVER sample for sandbox analysis
curl -s -X POST http://localhost:3000/api/v1/sandboxanalysis/submit \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "sample_hash": "f1e2d3c4b5a69788796a5b4c3d2e1f0a9b8c7d6e5f4a3b2c1d0e9f8a7b6c5d4e",
    "sample_name": "wg_modified_meshweaver.bin",
    "campaign_id": "0195a100-c001-7000-8000-000000000001",
    "analysis_type": "full",
    "priority": "critical",
    "tags": ["PHANTOM-MERCY", "MESHWEAVER", "wireguard-trojan"]
  }' | jq '.'
```

```json
{
  "id": "0195a100-e001-7000-8000-000000000001",
  "status": "completed",
  "analysis_duration_seconds": 47,
  "verdict": "malicious",
  "confidence": 0.96,
  "family": "MESHWEAVER",
  "version": "2.1.3",
  "capabilities": [
    "wireguard_tunnel_hijack",
    "steganographic_data_exfil",
    "firmware_persistence_arm64",
    "encrypted_c2_over_dns_txt",
    "biometric_data_harvester",
    "mesh_relay_impersonation"
  ],
  "c2_addresses": [
    "185.220.101.47:443",
    "91.219.237.88:8443"
  ],
  "encryption": {
    "c2_protocol": "AES-256-CBC over TLS 1.3",
    "exfil_protocol": "ChaCha20-Poly1305 inside WireGuard tunnel",
    "key_exchange": "X25519 with hardcoded fallback key"
  },
  "mitre_techniques": [
    "T1071.001", "T1071.004", "T1573.002", "T1036.005",
    "T1041", "T1005", "T1542.001", "T1048.002"
  ],
  "notable": "Sample contains embedded mesh relay certificate that allows impersonation of legitimate MESH-RELAY nodes. Also contains module for harvesting biometric template data (ISO/IEC 19795 format) from connected databases."
}
```

MESHWEAVER 2.1.3. A purpose-built implant with a biometric data harvester built right in. It wasn't a generic RAT -- it was engineered from the ground up to infiltrate humanitarian mesh networks and steal refugee biometric data.

I thought about the 340,000 records. Names. Faces. Fingerprints. Children who'd fled conflict zones, registered with aid organizations because they were told it was safe, told their data would be protected.

My hands were shaking again.

---

## Phase 3: THREAT GENOME -- 00:45 to 01:30

### 00:47 -- Fingerprinting PHANTOM MERCY

Clara's message said "find the genome." In Playseat, a Threat Genome is a deterministic DNA fingerprint computed from an adversary's TTPs, IOCs, and behavioral markers using BLAKE3 hashing. Same inputs, same hash. Every time.

If PHANTOM MERCY had hit other targets -- and the correlation data said they'd hit at least three -- then their genome would match across campaigns. I needed that match to prove this wasn't an isolated incident. Courts and oversight committees don't act on single incidents. They act on patterns.

```bash
# Create a Threat Genome from SILENT MERCY investigation data
curl -s -X POST http://localhost:3000/api/v1/adapt/genome/create \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "campaign_id": "0195a100-c001-7000-8000-000000000001",
    "actor_name": "PHANTOM MERCY",
    "markers": {
      "ttps": [
        "T1071.001", "T1071.004", "T1573.002", "T1036.005",
        "T1041", "T1005", "T1542.001", "T1048.002",
        "T1566.001", "T1059.004", "T1021.004"
      ],
      "iocs": [
        "185.220.101.47", "91.219.237.88", "45.153.240.12",
        "update-service.humanitarian-ops.net",
        "mesh-sync.global-ngo.org",
        "a3f2b8c91e4d7f6a5b0c3d2e1f098765432abcdef0123456789abcdef012345",
        "7d8e9f0a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8",
        "f1e2d3c4b5a69788796a5b4c3d2e1f0a9b8c7d6e5f4a3b2c1d0e9f8a7b6c5d4e"
      ],
      "behavioral": [
        "4h_c2_beacon_interval",
        "wireguard_tunnel_abuse",
        "mesh_relay_impersonation",
        "biometric_harvesting_iso19795",
        "humanitarian_sector_targeting",
        "shell_company_funding_cy_ae_ch",
        "firmware_level_persistence"
      ]
    }
  }' | jq '.'
```

```json
{
  "id": "0195a100-g001-7000-8000-000000000001",
  "actor_name": "PHANTOM MERCY",
  "genome_hash_blake3": "b7e4f2a19c3d8e5f6071829a4b5c6d7e8f9012345678abcdef0123456789abcd",
  "genome_hash_sha256": "2a3b4c5d6e7f8091a2b3c4d5e6f70819a2b3c4d5e6f708192a3b4c5d6e7f8091",
  "marker_count": {
    "ttps": 11,
    "iocs": 8,
    "behavioral": 7
  },
  "total_markers": 26,
  "created_at": "2026-02-15T00:47:22Z"
}
```

### 00:52 -- Genome Matching

Now the critical step. Run the new genome against every genome in the database -- our own investigations and everything shared through the Mesh.

```bash
# Run genome matching against all known threat actor genomes
curl -s -X POST http://localhost:3000/api/v1/adapt/genome/match \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "genome_id": "0195a100-g001-7000-8000-000000000001",
    "match_threshold": 0.60,
    "include_mesh_peers": true
  }' | jq '.'
```

```json
{
  "query_genome": "0195a100-g001-7000-8000-000000000001",
  "matches": [
    {
      "genome_id": "0194e200-g001-7000-8000-000000000003",
      "actor_name": "PHANTOM MERCY (SAHEL SHADOW campaign)",
      "similarity": 0.89,
      "matching_ttps": 9,
      "matching_iocs": 3,
      "matching_behavioral": 6,
      "source": "local",
      "campaign": "SAHEL SHADOW",
      "date": "2025-09"
    },
    {
      "genome_id": "0194e200-g001-7000-8000-000000000004",
      "actor_name": "PHANTOM MERCY (MERCY CORRIDOR campaign)",
      "similarity": 0.84,
      "matching_ttps": 8,
      "matching_iocs": 2,
      "matching_behavioral": 6,
      "source": "mesh_peer_nato_cert",
      "campaign": "MERCY CORRIDOR",
      "date": "2025-11"
    },
    {
      "genome_id": "0194e200-g001-7000-8000-000000000005",
      "actor_name": "PHANTOM MERCY (AID ECLIPSE campaign)",
      "similarity": 0.82,
      "matching_ttps": 8,
      "matching_iocs": 4,
      "matching_behavioral": 5,
      "source": "mesh_peer_eucert",
      "campaign": "AID ECLIPSE",
      "date": "2026-01"
    },
    {
      "genome_id": "0194e200-g001-7000-8000-000000000099",
      "actor_name": "SANDWORM (Industroyer2 campaign)",
      "similarity": 0.63,
      "matching_ttps": 5,
      "matching_iocs": 0,
      "matching_behavioral": 3,
      "source": "local",
      "campaign": "INDUSTROYER2_TRACKING",
      "date": "2022-04"
    }
  ]
}
```

Four matches. The top three were all PHANTOM MERCY -- 89%, 84%, and 82% genome similarity across three separate campaigns. That's not coincidence. That's the same threat actor with the same playbook, evolving slightly between operations but fundamentally the same organism.

The fourth match was interesting. 63% similarity to Sandworm -- the GRU unit responsible for Industroyer2 and NotPetya. The overlap was in TTPs, not IOCs, which meant shared tradecraft, not shared infrastructure. PHANTOM MERCY was likely a sub-unit or spin-off of Sandworm, specializing in humanitarian sector operations.

I exported the genome comparison and added it to the evidence chain.

```bash
# Export genome comparison as evidence artifact
curl -s -X POST http://localhost:3000/api/v1/evidence \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "campaign_id": "0195a100-c001-7000-8000-000000000001",
    "title": "Threat Genome Analysis - PHANTOM MERCY cross-campaign correlation",
    "evidence_type": "analysis",
    "classification": "TLP:AMBER",
    "description": "BLAKE3 genome fingerprint matching confirms SILENT MERCY threat actor matches PHANTOM MERCY across 3 prior campaigns (SAHEL SHADOW, MERCY CORRIDOR, AID ECLIPSE) with 82-89% genome similarity. Partial match to SANDWORM tradecraft (63%) suggests GRU lineage.",
    "metadata": {
      "genome_hash": "b7e4f2a19c3d8e5f6071829a4b5c6d7e8f9012345678abcdef0123456789abcd",
      "match_count": 4,
      "highest_similarity": 0.89
    }
  }' | jq '{ id, blake3_hash, sha256_hash }'
```

```json
{
  "id": "0195a100-h001-7000-8000-000000000001",
  "blake3_hash": "c8d9e0f1a2b3c4d5e6f7081920a1b2c3d4e5f6071829304a5b6c7d8e9f0a1b2",
  "sha256_hash": "3c4d5e6f70819203a4b5c6d7e8f90a1b2c3d4e5f6071829304a5b6c7d8e9f0a1"
}
```

Dual-hashed. BLAKE3 for speed, SHA-256 for legal standing. Every piece of evidence in this investigation would survive court scrutiny. Clara would expect nothing less.

---

## Phase 4: MESH INTELLIGENCE SHARING -- 01:30 to 02:15

### 01:33 -- Reaching Out to the Mesh

I couldn't do this alone. The Mesh is Playseat's federated intelligence sharing network -- peer-to-peer, TLP-controlled, trust-scored. I had active peer relationships with NATO CERT, EU-CERT, and an Australian Five Eyes node. Each of them might have pieces of this puzzle that I was missing.

At 01:33 on a Sunday morning, I sent out a priority intelligence request.

```bash
# Send priority mesh intel request to all active peers
curl -s -X POST http://localhost:3000/api/v1/adapt/mesh/share \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "request_type": "priority_intel_request",
    "campaign_id": "0195a100-c001-7000-8000-000000000001",
    "tlp": "amber",
    "target_peers": ["nato_cert", "eu_cert", "fvey_au"],
    "request": {
      "actor": "PHANTOM MERCY / UNC7731-HUM",
      "malware": "MESHWEAVER",
      "sector": "humanitarian",
      "time_window": "2025-06-01 to present",
      "specific_asks": [
        "Any MESHWEAVER samples or variant analysis",
        "C2 infrastructure sightings beyond known IOCs",
        "HUMINT on PHANTOM MERCY operators or front organizations",
        "Financial intelligence on shell companies: Zenith Charitable Holdings, Meridian Global Trust, Stiftung Humanitas",
        "Missing persons reports connected to humanitarian sector cyber incidents"
      ]
    },
    "sharing_back": {
      "ioc_count": 9,
      "findings_count": 3,
      "genome_included": true,
      "note": "Time-critical: missing person investigation. Any information on Clara Dubois, French national, cryptographic engineer, Fondation Lumiere."
    }
  }' | jq '.'
```

```json
{
  "request_id": "0195a100-m001-7000-8000-000000000001",
  "status": "dispatched",
  "peers_contacted": 3,
  "acknowledgements": [
    {"peer": "nato_cert", "ack_at": "2026-02-15T01:33:47Z", "status": "received"},
    {"peer": "eu_cert", "ack_at": "2026-02-15T01:34:02Z", "status": "received"},
    {"peer": "fvey_au", "ack_at": "2026-02-15T01:34:18Z", "status": "received"}
  ]
}
```

All three peers acknowledged within 35 seconds. Even at 01:30 on a Sunday, the Mesh runs 24/7.

### 01:48 -- NATO CERT Response

Major Elena Vasquez was working the overnight shift at NATO CERT. She responded in fifteen minutes. That woman is a machine.

```bash
# Check mesh peer responses
curl -s "http://localhost:3000/api/v1/adapt/mesh/responses?request_id=0195a100-m001-7000-8000-000000000001" \
  -H "Authorization: Bearer $TOKEN" | jq '.'
```

```json
{
  "request_id": "0195a100-m001-7000-8000-000000000001",
  "responses": [
    {
      "peer": "nato_cert",
      "responded_at": "2026-02-15T01:48:33Z",
      "trust_score": 0.94,
      "intel": {
        "new_iocs": [
          {"type": "ip", "value": "89.208.29.111", "confidence": 0.79, "description": "PHANTOM MERCY staging server - Kyiv datacenter (compromised Ukrainian hosting)"},
          {"type": "domain", "value": "ngo-update-service.org", "confidence": 0.83, "description": "Previously unseen PHANTOM MERCY phishing domain registered 2026-02-01"},
          {"type": "hash_sha256", "value": "e4f5a6b7c8d9e0f1a2b3c4d5e6f708192a3b4c5d6e7f8091a2b3c4d5e6f70819", "confidence": 0.88, "description": "MESHWEAVER v2.1.4 - updated variant with anti-forensics module"}
        ],
        "analysis_note": "NATO CERT tracked PHANTOM MERCY infrastructure pivot in January 2026. Actor migrated primary C2 from Romanian hosting to compromised Ukrainian datacenter. Consistent with GRU operational security practice of using compromised infrastructure in conflict zones. New MESHWEAVER variant (v2.1.4) includes anti-forensics capability that wipes mesh relay logs after exfiltration.",
        "humint_note": "No HUMINT available through NATO channels. Recommend DGSI engagement for French national missing person.",
        "financial_note": "Zenith Charitable Holdings flagged by FinCEN in December 2025 as potential money laundering vehicle. No further detail at this classification level."
      }
    },
    {
      "peer": "eu_cert",
      "responded_at": "2026-02-15T01:52:11Z",
      "trust_score": 0.91,
      "intel": {
        "new_iocs": [
          {"type": "ip", "value": "194.147.142.67", "confidence": 0.76, "description": "Backup C2 node observed in AID ECLIPSE campaign - Chisinau Moldova"},
          {"type": "domain", "value": "secure-mesh-update.com", "confidence": 0.81, "description": "MESHWEAVER dropper distribution site"}
        ],
        "analysis_note": "EU-CERT confirms PHANTOM MERCY is highest-priority threat to European humanitarian sector. Our AID ECLIPSE investigation (January 2026) documented identical TTP to what you are describing. MESHWEAVER was deployed via compromised firmware update mechanism on mesh relay hardware. Recommend checking firmware signing certificates on all MESH-RELAY nodes.",
        "missing_persons": "EU-CERT has no missing persons reports linked to cyber incidents in humanitarian sector. This is concerning if confirmed -- would represent significant escalation in PHANTOM MERCY operational behavior."
      }
    },
    {
      "peer": "fvey_au",
      "responded_at": "2026-02-15T02:03:44Z",
      "trust_score": 0.88,
      "intel": {
        "new_iocs": [
          {"type": "ip", "value": "103.216.220.45", "confidence": 0.71, "description": "PHANTOM MERCY relay node observed in APAC region - Hong Kong hosting"}
        ],
        "analysis_note": "ASD has tracked PHANTOM MERCY activity targeting Australian humanitarian organizations operating in Pacific Islands since October 2025. Same MESHWEAVER family, adapted for satellite-linked mesh relays used in Pacific disaster response. We assess PHANTOM MERCY has global reach beyond European theater.",
        "geoint_note": "ASD SIGINT collection identified device matching Clara Dubois phone IMEI broadcasting from Marseille, France, on 2026-02-14 at 03:22 UTC. Single ping, then dark. Coordinates: 43.2951°N, 5.3810°E. Accuracy radius: ~200m. Forwarding raw SIGINT to your GEOINT module."
      }
    }
  ]
}
```

I stopped breathing when I read the Five Eyes response.

Device matching Clara's phone IMEI. Broadcasting from Marseille. February 14th, 03:22 UTC -- roughly four and a half hours after she sent me the Signal message.

She was alive at 03:22. Or at least her phone was.

I immediately pivoted to GEOINT.

---

## Phase 5: GEOINT -- 02:15 to 03:30

### 02:17 -- Registering the Target

My hands were not steady as I typed these commands. I want that on the record.

```bash
# Register Clara's phone as a GEOINT target
curl -s -X POST http://localhost:3000/api/v1/geoint/targets \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Clara Dubois Mobile Device",
    "target_type": "mobile_device",
    "lat": 43.2951,
    "lon": 5.3810,
    "description": "Personal encrypted phone (IMEI redacted). Last SIGINT ping 2026-02-14 03:22 UTC from Marseille. Single ping then dark.",
    "metadata": {
      "device_type": "encrypted_smartphone",
      "campaign_id": "0195a100-c001-7000-8000-000000000001",
      "owner": "Clara Dubois",
      "status": "missing_person",
      "imei_hash_blake3": "a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2"
    },
    "status": "active"
  }' | jq '.'
```

```json
{
  "id": "0195a100-t001-7000-8000-000000000001",
  "name": "Clara Dubois Mobile Device",
  "target_type": "mobile_device",
  "lat": 43.2951,
  "lon": 5.3810,
  "status": "active",
  "created_at": "2026-02-15T02:17:44Z"
}
```

### 02:21 -- Recording the Position History

I recorded every known position ping from Clara's device. There weren't many.

```bash
# Add known position history
curl -s -X POST http://localhost:3000/api/v1/geoint/positions/batch \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "target_id": "0195a100-t001-7000-8000-000000000001",
    "positions": [
      {
        "lat": 48.8566,
        "lon": 2.3522,
        "timestamp": "2026-02-13T21:30:00Z",
        "source": "workstation_login_geoloc",
        "accuracy_m": 50,
        "notes": "Workstation unlock at Fondation Lumiere HQ, Paris"
      },
      {
        "lat": 48.8602,
        "lon": 2.3508,
        "timestamp": "2026-02-13T22:47:00Z",
        "source": "signal_message_metadata",
        "accuracy_m": 500,
        "notes": "Signal message sent - cell tower triangulation estimate, still Paris area"
      },
      {
        "lat": 48.8448,
        "lon": 2.3735,
        "timestamp": "2026-02-13T23:15:00Z",
        "source": "cctv_facial_recognition",
        "accuracy_m": 10,
        "notes": "DGSI CCTV match at Gare de Lyon train station, Paris"
      },
      {
        "lat": 43.2951,
        "lon": 5.3810,
        "timestamp": "2026-02-14T03:22:00Z",
        "source": "sigint_imei_ping",
        "accuracy_m": 200,
        "notes": "ASD SIGINT - single IMEI ping, Marseille port district, then dark"
      }
    ]
  }' | jq '.recorded_count'
```

```json
4
```

Four data points. Paris HQ at 21:30. Paris at 22:47 when she sent the message. Gare de Lyon at 23:15 -- she'd gone straight to the train station. Marseille at 03:22.

### 02:28 -- Distance and Movement Analysis

```bash
# Calculate movement analysis
curl -s "http://localhost:3000/api/v1/geoint/targets/0195a100-t001-7000-8000-000000000001/movement?time_start=2026-02-13T21:00:00Z&time_end=2026-02-14T04:00:00Z" \
  -H "Authorization: Bearer $TOKEN" | jq '.'
```

```json
{
  "target_id": "0195a100-t001-7000-8000-000000000001",
  "analysis_period": {
    "start": "2026-02-13T21:00:00Z",
    "end": "2026-02-14T04:00:00Z"
  },
  "total_distance_km": 775.4,
  "movement_segments": [
    {
      "from": "Paris HQ",
      "to": "Gare de Lyon",
      "distance_km": 1.8,
      "time_elapsed_min": 28,
      "speed_kmh": 3.9,
      "transport_estimate": "walking"
    },
    {
      "from": "Gare de Lyon",
      "to": "Marseille port district",
      "distance_km": 773.6,
      "time_elapsed_min": 247,
      "speed_kmh": 187.8,
      "transport_estimate": "TGV high-speed rail"
    }
  ],
  "pattern_analysis": {
    "movement_type": "deliberate_transit",
    "direction": "south_southeast",
    "consistent_with": "Paris to Marseille via TGV (scheduled travel time: ~3h20m)",
    "anomaly_score": 0.0,
    "notes": "Movement pattern consistent with planned departure. Walking speed to Gare de Lyon suggests no pursuit or panic. TGV timing matches SNCF schedule for 23:25 departure, arriving Marseille Saint-Charles ~02:50."
  }
}
```

She walked. Not ran. Walked from HQ to Gare de Lyon. That's a 28-minute walk at a normal pace. Then she caught the 23:25 TGV to Marseille -- probably the last direct train of the night. She arrived at Marseille Saint-Charles around 02:50 and her phone pinged once at 03:22, thirty-two minutes after arrival, in the port district.

She wasn't fleeing in panic. She was executing a plan. The Clara Protocol.

### 02:35 -- Geofencing the Last Known Position

```bash
# Create geofence around last known position
curl -s -X POST http://localhost:3000/api/v1/geoint/geofences \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "CLARA-LAST-KNOWN-200M",
    "center_lat": 43.2951,
    "center_lon": 5.3810,
    "radius_m": 200,
    "alert_on": "entry_or_exit",
    "target_ids": ["0195a100-t001-7000-8000-000000000001"],
    "campaign_id": "0195a100-c001-7000-8000-000000000001",
    "description": "200m radius around last SIGINT ping for Clara Dubois phone in Marseille port district. Alert on any future signal activity."
  }' | jq '.id'
```

```json
"0195a100-t002-7000-8000-000000000001"
```

### 02:41 -- Mapping the Area

I pulled up satellite imagery of the Marseille port district around the coordinates. The 200-meter accuracy radius from the SIGINT ping covered a block of old maritime buildings -- converted warehouses, some commercial space, a few residential apartments above ground-floor businesses. One building stood out in the metadata: a co-working space called "Le Port Numerique" that marketed itself as a tech hub for NGO workers and digital nomads.

Clara would have known about it. It's exactly the kind of place she'd gravitate toward.

```sql
-- Query nearby infrastructure within geofence radius
SELECT
    gt.name,
    gt.target_type,
    gt.lat,
    gt.lon,
    gt.metadata,
    (6371 * acos(cos(radians(43.2951)) * cos(radians(gt.lat))
    * cos(radians(gt.lon) - radians(5.3810))
    + sin(radians(43.2951)) * sin(radians(gt.lat)))) AS distance_km
FROM geo_targets gt
WHERE gt.status = 'active'
  AND (6371 * acos(cos(radians(43.2951)) * cos(radians(gt.lat))
    * cos(radians(gt.lon) - radians(5.3810))
    + sin(radians(43.2951)) * sin(radians(gt.lat)))) < 0.2
ORDER BY distance_km;
```

```
name                      | target_type  | lat      | lon     | distance_km | metadata
--------------------------+--------------+----------+---------+-------------+---------------------------
Le Port Numerique         | facility     | 43.2953  | 5.3808  | 0.028       | {"type": "coworking_space", "wifi": true, "24h_access": true}
Entrepot Maritime 7       | building     | 43.2948  | 5.3815  | 0.052       | {"type": "converted_warehouse", "mixed_use": true}
Cafe du Vieux Port        | commercial   | 43.2960  | 5.3795  | 0.137       | {"type": "cafe", "hours": "06:00-02:00"}
```

Le Port Numerique. 28 meters from the center of the ping. Open 24 hours. Wi-Fi enabled.

Clara had gone there. I was sure of it. She'd taken the last TGV to Marseille, walked to this co-working space in the port district, done something -- left something -- and then gone dark.

---

## Phase 6: FINDING THE DEAD DROP -- 03:30 to 05:15

### 03:33 -- The Backup Server

Clara's audit trail showed she'd copied `evidence_pkg.enc` to BACKUP-01 at 22:38. But her message said "the evidence is in the mesh." The backup was a safety copy. The real evidence was somewhere in the mesh relay network.

I went back to the mesh relays.

```bash
# Deep scan MESH-RELAY-01 filesystem for anomalous files
curl -s -X POST http://localhost:3000/api/v1/diskforensics/scan \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "asset_id": "0195a100-c002-7000-8000-000000000005",
    "campaign_id": "0195a100-c001-7000-8000-000000000001",
    "scan_type": "full_filesystem",
    "parameters": {
      "check_hidden_files": true,
      "check_alternate_data_streams": true,
      "check_steganography": true,
      "check_encrypted_volumes": true,
      "file_entropy_threshold": 7.5,
      "modified_since": "2026-02-01T00:00:00Z"
    }
  }' | jq '.'
```

```json
{
  "id": "0195a100-k001-7000-8000-000000000001",
  "status": "completed",
  "scan_duration_seconds": 134,
  "findings": [
    {
      "path": "/var/lib/wireguard/keys/.mesh_config.dat",
      "size_bytes": 4517289984,
      "entropy": 7.98,
      "modified": "2026-02-13T22:36:00Z",
      "type": "encrypted_container",
      "notes": "Hidden file in WireGuard key directory. 4.2GB. Entropy consistent with AES-256 encrypted data. Modified timestamp aligns with Clara Dubois activity window."
    },
    {
      "path": "/opt/mesh-relay/firmware/update_pending.bin",
      "size_bytes": 8847360,
      "entropy": 7.91,
      "modified": "2026-01-28T14:22:00Z",
      "type": "suspected_malware",
      "notes": "Firmware update file. SHA-256 matches MESHWEAVER Stage 2 implant."
    },
    {
      "path": "/tmp/.wg_cache/peers.enc",
      "size_bytes": 2048,
      "entropy": 7.99,
      "modified": "2026-02-13T22:40:00Z",
      "type": "encrypted_file",
      "notes": "Small encrypted file in temporary WireGuard cache. Created during Clara Dubois activity window. May be key material or metadata."
    }
  ]
}
```

There. `/var/lib/wireguard/keys/.mesh_config.dat`. A 4.2-gigabyte encrypted container hidden in the WireGuard key directory, disguised as a mesh configuration file. Modified at 22:36 on February 13th -- two minutes before Clara copied the backup to BACKUP-01. Same size as the packet capture she'd run at 22:31.

She'd captured 4.2GB of mesh traffic, encrypted it, and hidden it inside the mesh relay itself. Hiding in plain sight. Classic Clara.

And there was a second file: `peers.enc`. 2KB. Created at 22:40, four minutes after the big container. A key file. Or instructions.

### 03:44 -- Evidence Collection with Chain of Custody

I needed to collect these files as evidence with proper chain of custody. Every byte, dual-hashed, timestamped, audit-trailed.

```bash
# Collect encrypted container as evidence
curl -s -X POST http://localhost:3000/api/v1/evidence \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "campaign_id": "0195a100-c001-7000-8000-000000000001",
    "title": "Clara Dubois encrypted evidence container from MESH-RELAY-01",
    "evidence_type": "forensic_image",
    "classification": "TLP:RED",
    "source_path": "/var/lib/wireguard/keys/.mesh_config.dat",
    "source_asset": "MESH-RELAY-01",
    "collected_by": "Ethan Raines (WATCHMAN-1)",
    "description": "4.2GB AES-256-GCM encrypted container hidden in WireGuard key directory on compromised mesh relay. Created by Clara Dubois at 22:36 UTC on 2026-02-13, containing packet capture of mesh relay traffic documenting PHANTOM MERCY data exfiltration.",
    "metadata": {
      "original_size": 4517289984,
      "entropy": 7.98,
      "encryption": "AES-256-GCM (presumed)",
      "key_status": "unknown - requires decryption key",
      "chain_of_custody_note": "File collected remotely via read-only VPN access. No modification to source filesystem."
    }
  }' | jq '{ id, blake3_hash, sha256_hash, collected_at }'
```

```json
{
  "id": "0195a100-h002-7000-8000-000000000001",
  "blake3_hash": "d9e0f1a2b3c4d5e6f70819203a4b5c6d7e8f9a0b1c2d3e4f5061728394a5b6c7",
  "sha256_hash": "4e5f6a7b8c9d0e1f2a3b4c5d6e7f80192a3b4c5d6e7f80192a3b4c5d6e7f8019",
  "collected_at": "2026-02-15T03:44:22Z"
}
```

```bash
# Collect the small encrypted key file
curl -s -X POST http://localhost:3000/api/v1/evidence \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "campaign_id": "0195a100-c001-7000-8000-000000000001",
    "title": "Clara Dubois encrypted key/metadata file from MESH-RELAY-01",
    "evidence_type": "key_material",
    "classification": "TLP:RED",
    "source_path": "/tmp/.wg_cache/peers.enc",
    "source_asset": "MESH-RELAY-01",
    "collected_by": "Ethan Raines (WATCHMAN-1)",
    "description": "2KB encrypted file found in temporary WireGuard cache. Created 4 minutes after main evidence container. Likely contains decryption key or instructions for the 4.2GB evidence package.",
    "metadata": {
      "original_size": 2048,
      "entropy": 7.99,
      "encryption": "unknown",
      "chain_of_custody_note": "File collected remotely via read-only VPN access."
    }
  }' | jq '{ id, blake3_hash, sha256_hash }'
```

```json
{
  "id": "0195a100-h002-7000-8000-000000000002",
  "blake3_hash": "e0f1a2b3c4d5e6f708192a3b4c5d6e7f8091a2b3c4d5e6f708192a3b4c5d6e7f",
  "sha256_hash": "5f6a7b8c9d0e1f2a3b4c5d6e7f80192a3b4c5d6e7f80192a3b4c5d6e7f801920"
}
```

### 03:52 -- The peers.enc File

I downloaded the 2KB file and examined it. It wasn't encrypted with AES. It was encrypted with a much simpler scheme -- a passphrase-derived key using Argon2id. Clara had used a different encryption method for this file than for the main container. That was deliberate. The main container was encrypted with a proper key that she'd stored somewhere secure. This small file was encrypted with a passphrase that someone -- specifically, one person -- would know.

The file header, visible in hex:

```
00000000: 4352 4c50 0100 0002 4152 474f 4e32 4944  CRLP....ARGON2ID
00000010: 0000 0020 0000 0004 0000 0000 0100 0000  ... ............
00000020: [encrypted payload begins]
```

`CRLP`. Clara Protocol. Version 1.0. Encryption: Argon2ID. Memory cost: 32MB. Iterations: 4. The parameters of a key derivation function that turns a passphrase into a decryption key.

She'd designed a protocol. Named it after herself. And locked it with a passphrase.

I stared at the hex dump. My heart was hammering.

What passphrase would Clara use? What would she choose that only I would know?

> *"You'll know how to find it. You built the tools."*

She built the protocol. I built Playseat. She designed it so that only someone running Playseat could follow the trail. And she encrypted the key file with a passphrase that only someone who knew her -- who really knew her -- would guess.

### 04:10 -- The Search for the Key

I tried everything. Her birthday. My birthday. Her Sorbonne student number. The title of her DEFCON paper. "Playseat." "mesh." "children." "genome."

None of them worked.

I went to the kitchen, made another coffee, stood at the window looking at the pre-dawn sky over Paris, and thought about what Clara would do.

She was a cryptographer. She understood key management. A good passphrase is something you can remember but an adversary can't guess. It needs to be unique to the relationship between the encryptor and the intended decryptor. Not a birthday -- too guessable. Not a name -- too obvious. Something specific. Something anchored to a shared experience that no one else would know.

> *"The evidence is in the mesh. Find the genome. Save the children."*

Find the genome. That's a Playseat instruction. Save the children. That's the stakes. But "the evidence is in the mesh" -- that's both an instruction and a clue.

The mesh. The DEFCON Wireless Village, where we met. Where she was presenting on mesh networks. Where she spilled Red Bull on my laptop.

The date.

August 11th, 2023.

The date we met.

I went back to my workstation.

### 04:22 -- The Moment

I have never typed eight characters with more fear in my life.

```
20230811
```

I fed it to the Argon2ID key derivation function with the parameters from the file header, and used the derived key to decrypt `peers.enc`.

It worked.

The file decrypted into 1,847 bytes of plaintext. A JSON document. I'll remember every word until I die.

```json
{
  "protocol": "CLARA",
  "version": "1.0",
  "created": "2026-02-13T22:40:00Z",
  "author": "Clara Dubois",
  "recipient": "Ethan Raines",
  "message": "If you're reading this, you found the trail. I knew you would. The main container (.mesh_config.dat) is encrypted with AES-256-GCM. The key is derived from the SHA-256 hash of our first conversation topic at DEFCON. Not the talk title. The thing we actually argued about over drinks at the Flamingo bar. You'll remember. You always remember the arguments.",
  "evidence_manifest": {
    "packet_captures": "4.1GB mesh relay traffic, 2026-01-28 through 2026-02-13, showing MESHWEAVER C2 beacons and biometric data exfiltration",
    "firmware_dumps": "3 mesh relay firmware images with embedded MESHWEAVER implants",
    "financial_records": "Export of donor transaction ledger showing shell company payments totaling EUR 1.225M",
    "access_logs": "Database access logs showing 340,000 refugee biometric records queried from unauthorized source",
    "operator_comms": "12 intercepted C2 messages between MESHWEAVER implant and 185.220.101.47, partially decrypted"
  },
  "instructions": "Take this to ANSSI through official channels. Not through Capitaine Moreau at DGSI -- he is compromised. Use Director Beaumont at ANSSI, she is clean. The evidence package is court-admissible if the chain of custody is maintained. You built Evidence Court for exactly this.",
  "personal": "I am safe. I have a backup of everything on an air-gapped drive. I am in a place they won't look. I will surface when the evidence is public. Don't come looking for me -- they are watching the trains and the airports. When this is over, I owe you a ThinkPad and an honest conversation about Montmartre. -- C"
}
```

I sat there for a long time. The timestamp on my display said 04:22. Dawn was bleeding through the window. My face was wet and I didn't remember starting to cry.

She was safe. She was alive. She had a plan. The Clara Protocol wasn't just about hiding evidence -- it was about ensuring it reached someone who could do something with it. Someone with the tools, the methodology, and the legal framework to turn raw intelligence into admissible proof.

She'd chosen me. Not because of the past. Because of Playseat.

> *"You built Evidence Court for exactly this."*

Yeah. Yeah, I did.

### 04:31 -- Logging the Decryption as Evidence

Even in that moment, even with tears on my face, the analyst in me did what the analyst always does. I logged the decryption event as evidence.

```bash
# Record decryption of Clara Protocol key file
curl -s -X POST http://localhost:3000/api/v1/evidence \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "campaign_id": "0195a100-c001-7000-8000-000000000001",
    "title": "Decrypted Clara Protocol metadata file (peers.enc)",
    "evidence_type": "decrypted_artifact",
    "classification": "TLP:RED",
    "description": "peers.enc decrypted using Argon2ID-derived key from passphrase. Contains evidence manifest and instructions from Clara Dubois. Confirms evidence container contents and identifies safe contact at ANSSI. Passphrase methodology: date of first meeting between analyst and source.",
    "metadata": {
      "decryption_method": "Argon2ID key derivation",
      "decrypted_size": 1847,
      "decrypted_at": "2026-02-15T04:22:33Z",
      "decrypted_by": "Ethan Raines (WATCHMAN-1)",
      "chain_of_custody": "Original encrypted file hash preserved. Decrypted content hashed separately."
    }
  }' | jq '{ id, blake3_hash, sha256_hash }'
```

```json
{
  "id": "0195a100-h003-7000-8000-000000000001",
  "blake3_hash": "f1a2b3c4d5e6f708192a3b4c5d6e7f8091a2b3c4d5e6f708192a3b4c5d6e7f80",
  "sha256_hash": "6a7b8c9d0e1f2a3b4c5d6e7f80192a3b4c5d6e7f80192a3b4c5d6e7f80192a3b"
}
```

Three evidence artifacts. All dual-hashed. All audit-trailed. All court-admissible.

Clara would approve.

---

## 04:45 -- The Second Key

The main container still needed decrypting. Clara's message said the key was derived from "the SHA-256 hash of our first conversation topic at DEFCON." Not the talk title. "The thing we actually argued about over drinks at the Flamingo bar."

I knew exactly what she meant.

After her presentation, after the spilled Red Bull, after we'd moved to the Flamingo bar, we'd gotten into an argument about post-quantum cryptography. Specifically, about whether NIST's choice of CRYSTALS-Kyber as the post-quantum key encapsulation standard was the right one. I argued it was solid. She argued that NTRU was mathematically superior and Kyber was a political choice driven by the NSA's influence on the selection process.

We argued for two hours. Neither of us gave an inch. It was the most fun I'd had at DEFCON in years.

The topic: `CRYSTALS-Kyber vs NTRU`

```bash
# Compute SHA-256 of the conversation topic to derive the AES key
echo -n "CRYSTALS-Kyber vs NTRU" | sha256sum
```

```
8e7d6c5b4a39281706f5e4d3c2b1a0987654321fedcba9876543210fedcba98  -
```

I used that hash as the AES-256-GCM key and pointed it at the 4.2-gigabyte container.

The decryption took 47 seconds. When it finished, the output was a tar archive containing exactly what Clara's manifest described: packet captures, firmware dumps, financial records, access logs, and 12 partially decrypted C2 messages.

The evidence was real. All of it.

### 05:02 -- Hashing the Decrypted Evidence

```bash
# Hash and catalog every file in the decrypted evidence package
curl -s -X POST http://localhost:3000/api/v1/evidence/batch \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "campaign_id": "0195a100-c001-7000-8000-000000000001",
    "artifacts": [
      {
        "title": "Mesh relay packet capture (2026-01-28 to 2026-02-13)",
        "evidence_type": "pcap",
        "classification": "TLP:RED",
        "size_bytes": 4404019200,
        "description": "Raw packet capture from mesh relay subnet showing MESHWEAVER C2 traffic and biometric data exfiltration"
      },
      {
        "title": "MESH-RELAY-01 firmware dump with MESHWEAVER implant",
        "evidence_type": "firmware_image",
        "classification": "TLP:RED",
        "size_bytes": 8847360
      },
      {
        "title": "MESH-RELAY-02 firmware dump with MESHWEAVER implant",
        "evidence_type": "firmware_image",
        "classification": "TLP:RED",
        "size_bytes": 8912000
      },
      {
        "title": "MESH-RELAY-03 firmware dump with MESHWEAVER implant",
        "evidence_type": "firmware_image",
        "classification": "TLP:RED",
        "size_bytes": 8781824
      },
      {
        "title": "Donor transaction ledger export - shell company payments",
        "evidence_type": "financial_record",
        "classification": "TLP:RED",
        "size_bytes": 445622
      },
      {
        "title": "Database access logs - refugee biometric record exfiltration",
        "evidence_type": "access_log",
        "classification": "TLP:RED",
        "size_bytes": 2847103
      },
      {
        "title": "Intercepted MESHWEAVER C2 messages (12 messages, partial decrypt)",
        "evidence_type": "sigint",
        "classification": "TLP:RED",
        "size_bytes": 34816
      }
    ]
  }' | jq '{ total_artifacts, all_hashed }'
```

```json
{
  "total_artifacts": 7,
  "all_hashed": true
}
```

Seven evidence artifacts. Every one dual-hashed with BLAKE3 and SHA-256. Every one logged in the audit trail with full chain of custody. Every one linked to campaign SILENT MERCY.

---

## 05:15 -- The Audit Trail

Before I did anything else, I exported the complete audit trail. If this was going to ANSSI -- and it was -- the chain of custody had to be airtight.

```bash
# Export complete evidence chain for ANSSI submission
curl -s -X POST http://localhost:3000/api/v1/evidence/export \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "campaign_id": "0195a100-c001-7000-8000-000000000001",
    "export_format": "legal_package",
    "include": {
      "evidence_artifacts": true,
      "chain_of_custody": true,
      "audit_trail": true,
      "hash_verification": true,
      "analyst_notes": true,
      "genome_analysis": true,
      "mesh_intel": true,
      "geoint_data": true,
      "ontology_graph": true,
      "timeline": true
    },
    "classification": "TLP:RED",
    "recipient": "ANSSI - Dr. Sylvie Beaumont (ANSSI-7)",
    "legal_standard": "EU_FORENSIC_2024",
    "notes": "Court-admissible evidence package documenting state-sponsored infiltration of Fondation Lumiere humanitarian network by PHANTOM MERCY (GRU Unit 74455). Contains proof of biometric data exfiltration affecting 340,000 refugee records and financial evidence of shell company funding. Package prepared in compliance with EU Digital Evidence Regulation 2024/1689. Contact: ANSSI-7, not DGSI (see Clara Protocol instructions)."
  }' | jq '.'
```

```json
{
  "export_id": "0195a100-x001-7000-8000-000000000001",
  "status": "completed",
  "package_size_bytes": 4893241856,
  "artifact_count": 14,
  "evidence_items": 10,
  "hash_verification": "all_passed",
  "chain_of_custody_entries": 47,
  "audit_trail_entries": 312,
  "legal_compliance": {
    "standard": "EU_FORENSIC_2024",
    "compliant": true,
    "dual_hash_verified": true,
    "timestamp_integrity": true,
    "analyst_attestation": true
  },
  "package_hashes": {
    "blake3": "a2b3c4d5e6f70819203a4b5c6d7e8f9a0b1c2d3e4f5061728394a5b6c7d8e9f0",
    "sha256": "7b8c9d0e1f2a3b4c5d6e7f80192a3b4c5d6e7f80192a3b4c5d6e7f80192a3b4c"
  },
  "created_at": "2026-02-15T05:15:22Z"
}
```

---

## 05:30 -- The Call

I picked up the phone and dialed the number Clara had specified. Dr. Sylvie Beaumont, ANSSI Incident Coordinator.

It rang four times. A woman's voice, alert despite the hour.

> "Beaumont."
>
> "Dr. Beaumont, this is Ethan Raines, callsign WATCHMAN-1. I have a TLP:RED evidence package regarding state-sponsored infiltration of a French humanitarian organization. PHANTOM MERCY, GRU Unit 74455. Biometric data exfiltration affecting 340,000 refugee records. And a missing French national connected to the investigation."
>
> Silence. Two seconds.
>
> "How did you get this number?"
>
> "From the person who is missing. She told me you were clean."
>
> Another pause. "Clara Dubois."
>
> "Yes."
>
> "I've been waiting for this call for three days. I'll have a secure courier at your location within the hour. Do not -- I repeat -- do not contact DGSI. Are we clear?"
>
> "Crystal."
>
> "Good. And Raines? Is she alive?"
>
> "She says she is."
>
> "Then let's make sure she stays that way. Beaumont out."

---

## 05:45 -- Final Campaign Status

```bash
# Update campaign status
curl -s -X PATCH "http://localhost:3000/api/v1/campaigns/0195a100-c001-7000-8000-000000000001" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "status": "evidence_transferred",
    "notes": "Complete evidence package transferred to ANSSI (Dr. Sylvie Beaumont, ANSSI-7) at 05:45 UTC. 14 evidence artifacts, all dual-hashed, full chain of custody maintained. PHANTOM MERCY attribution at 87% confidence. Genome analysis confirms cross-campaign pattern. Mesh intel from 3 partner agencies incorporated. GEOINT tracking active for Clara Dubois device. Investigation ongoing."
  }' | jq '.status'
```

```json
"evidence_transferred"
```

### Campaign SILENT MERCY -- Summary Statistics

| Metric | Value |
|--------|-------|
| Duration | 7 hours 45 minutes (22:00 - 05:45) |
| ADAPT Phases | DISCOVER, CORRELATE, VALIDATE (partial) |
| Findings | 3 critical, 5 high, 4 medium, 2 low |
| IOCs Ingested | 9 initial + 6 from Mesh peers = 15 total |
| Evidence Artifacts | 14 (all dual-hashed BLAKE3 + SHA-256) |
| Ontology Entities | 12 entities, 16 relationships |
| Genome Matches | 4 (89%, 84%, 82%, 63% similarity) |
| Mesh Peers Consulted | 3 (NATO CERT, EU-CERT, FVEY-AU) |
| GEOINT Data Points | 4 positions, 1 geofence |
| Audit Trail Entries | 312 |
| Chain of Custody Entries | 47 |
| Platform Modules Used | 18 |
| Coffee Consumed | 5 cups |
| Hours of Sleep | 0 |

---

## Epilogue: 06:17 UTC

I'm writing this at 06:17. Dawn has broken over Paris. The ANSSI courier left twenty minutes ago with an encrypted hard drive containing the full evidence package.

The investigation isn't over. The FORTIFY and PROVE phases are still ahead -- ANSSI will need to coordinate with Interpol, FinCEN, and probably NATO to take action against PHANTOM MERCY's infrastructure. The shell companies need to be frozen. The compromised mesh relays need to be rebuilt from clean firmware. The 340,000 refugee records need to be assessed for damage and the affected individuals notified through humanitarian channels.

And Clara needs to come home.

I don't know where she is. She told me not to look for her, and the analyst in me understands why -- if PHANTOM MERCY has people inside DGSI, any overt search operation could lead them straight to her. She'll surface when it's safe. When the evidence is public and the operation is blown and there's no point in silencing her anymore.

But the part of me that isn't an analyst -- the part that remembers a spilled Red Bull at DEFCON and an argument about lattice-based cryptography and a laugh that made the Flamingo bar feel like the center of the universe -- that part wants to get on the next TGV to Marseille and knock on every door in the port district until I find her.

I won't. Not yet. The work comes first. It always does. That's what pulled us apart, and ironically, it's what brought us back together.

She built the Clara Protocol knowing I'd follow it. She encrypted her dead drop with the date we met and the topic of our first argument. She used Playseat's features as stepping stones because she knew I'd know exactly how to walk them. Every API call, every evidence hash, every ontology relationship -- they were all breadcrumbs designed for one specific analyst running one specific platform.

In twelve years of defensive intelligence work, I've never seen a more elegant operation. And it was planned and executed by a mathematician with a messy bun and wire-rimmed glasses in 77 minutes flat while a state-sponsored threat actor was closing in on her.

Clara Dubois isn't just the subject of this investigation.

She's the best operational planner I've ever encountered.

And when this is over, I owe her a ThinkPad. And an honest conversation about Montmartre.

---

## Technical Appendix: Playseat Modules Used in SILENT MERCY

| Module | Crate | Purpose in Investigation |
|--------|-------|------------------------|
| Campaigns | `campaign-manager` | Investigation container and tracking |
| Assets | `asset-inventory` | Fondation Lumiere infrastructure registration |
| ADAPT Cycle | `svc-api::routes::adapt` | DISCOVER phase network scanning |
| Threat Intel | `threatintel-*` | PHANTOM MERCY IOC ingestion and correlation |
| Findings | `finding-engine` | Critical finding documentation |
| ADAPT Correlate | `svc-api::routes::adapt` | TTP and threat actor matching |
| Ontology Graph | `ontology-knowledge` | Entity-relationship mapping |
| Sandbox Analysis | `sandbox-analysis` | MESHWEAVER malware analysis |
| Threat Genome | `svc-collaboration::threat_genome` | Cross-campaign fingerprinting |
| Evidence Court | `core-evidence` | Dual-hash chain of custody |
| Mesh Sharing | `svc-api::routes::adapt` | Federated intel exchange with 3 peers |
| GEOINT | `geoint-*` | Target tracking and movement analysis |
| Disk Forensics | `disk-forensics` | Hidden file detection on mesh relays |
| Audit Trail | `core-audit` | Complete operation logging |
| Evidence Export | `core-evidence` | Legal evidence package generation |
| Network Forensics | `network-forensics` | Packet capture analysis |
| Risk Assessment | `risk-assessment` | Refugee data exposure evaluation |
| Attribution Engine | `attribution-engine` | PHANTOM MERCY GRU linkage |

### Evidence Hashing Summary

| Artifact | BLAKE3 Hash (truncated) | SHA-256 Hash (truncated) | Status |
|----------|------------------------|--------------------------|--------|
| Encrypted container (.mesh_config.dat) | `d9e0f1a2b3c4...` | `4e5f6a7b8c9d...` | Collected, decrypted |
| Key file (peers.enc) | `e0f1a2b3c4d5...` | `5f6a7b8c9d0e...` | Collected, decrypted |
| Decrypted Clara Protocol message | `f1a2b3c4d5e6...` | `6a7b8c9d0e1f...` | Verified |
| Packet capture (4.1GB) | `[generated]` | `[generated]` | Transferred to ANSSI |
| Genome analysis report | `c8d9e0f1a2b3...` | `3c4d5e6f7081...` | Verified |
| Full evidence export package | `a2b3c4d5e6f7...` | `7b8c9d0e1f2a...` | Transferred to ANSSI |

### MITRE ATT&CK Mapping

| Technique ID | Name | Tactic | Observed In |
|-------------|------|--------|-------------|
| T1566.001 | Spearphishing Attachment | Initial Access | Mesh relay compromise vector |
| T1059.004 | Unix Shell | Execution | MESHWEAVER post-exploitation |
| T1021.004 | SSH | Lateral Movement | Relay-to-relay propagation |
| T1036.005 | Match Legitimate Name | Defense Evasion | Modified WireGuard binary |
| T1542.001 | System Firmware | Persistence | Mesh relay firmware implant |
| T1071.001 | Web Protocols | Command and Control | HTTPS C2 beacons |
| T1071.004 | DNS | Command and Control | DNS TXT record C2 channel |
| T1573.002 | Asymmetric Cryptography | Command and Control | AES-256-CBC/TLS C2 encryption |
| T1005 | Data from Local System | Collection | Biometric database access |
| T1041 | Exfiltration Over C2 Channel | Exfiltration | Data tunneled through WireGuard |
| T1048.002 | Exfiltration Over Asymmetric Encrypted Non-C2 | Exfiltration | ChaCha20-Poly1305 exfil channel |

---

## Author's Note

This case study is different from the others in this book. The others are exercises in methodology. This one is a reminder of why methodology matters.

We build defensive intelligence platforms because somewhere, someone like Clara Dubois is going to discover something terrible and need a way to prove it. Not with opinions. Not with assessments. With evidence that is cryptographically verifiable, legally admissible, and auditably complete.

The ADAPT cycle is not an abstraction. The evidence chain is not a checkbox. The dual-hash system is not over-engineering. Every feature in Playseat exists because somewhere, someday, it will be the difference between justice and impunity.

Build your tools well. Maintain your chains of custody. Trust your methodology.

And when the message comes in at 22:47 on a Valentine's Eve, be ready to follow the trail wherever it leads.

---

> *This chapter is dedicated to the humanitarian workers -- the real ones -- who operate in conflict zones around the world. The threats described here are fictional but inspired by documented patterns. The courage required to do that work is not.*

---

*Next Chapter: [Chapter 31 -- Quickstart: Zero to Analyst in 30 Minutes](31-quickstart-zero-to-analyst.md)*

---

`© 2026 Playseat -- All Rights Reserved | Defensive Intelligence Through ADAPT`
