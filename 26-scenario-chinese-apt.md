# Chapter 26: Case Study -- Chinese APT vs European Satellites: Lessons for STARLIGHT

**Classification: UNCLASSIFIED // FOR OFFICIAL USE ONLY**
**Platform Version: 0.2.0 | Scenario Type: Full ADAPT Cycle + Mesh Sharing**

> "I remember this case because Clara was still at her desk when the first IOC hit. She looked at the correlation graph, looked at me, and said: 'They're hiding inside the ground stations the same way someone would hide inside a city. You don't look for the spy. You look for what the spy needs.' Six months later, I'd use that exact insight to find PHANTOM MERCY."

---

## The Flashback Begins

It's 02:47 on a Tuesday in February 2026, and I'm staring at the STARLIGHT countdown clock on my second monitor. T-minus 9 hours. Clara Dubois is being held in an abandoned hospital in Marseille by a trafficking network that calls itself PHANTOM MERCY, and I'm sitting here in a bunker in Brussels trying to figure out how to get her out alive.

But my mind keeps going back to ORBITAL SHADOW.

Six months ago. August 2025. The case that taught me how advanced persistent threats hide inside critical infrastructure. The case Clara helped me crack before she went under cover with the DGSE. Her notes are still in the evidence vault -- I pulled them up an hour ago, looking for the pattern, the blind spot, the thing she saw that I didn't.

Because PHANTOM MERCY has the same blind spot. I'm sure of it. I just can't see it yet.

So let me tell you about ORBITAL SHADOW. Let me tell you how we found Volt Typhoon hiding inside European satellite ground stations. And let me tell you what Clara figured out that I missed.

---

## Overview

**Operation Codename**: ORBITAL SHADOW
**Threat Actor**: Volt Typhoon Evolution (MSS-linked, designated JADE PANDA internally) -- tracked as UNC4841-SAT by Mandiant
**Target Organization**: European Space Operations Consortium (ESOC-PRIME) -- *synthetic*
**Target Infrastructure**: 3 satellite ground stations, 2 telemetry uplink facilities, 1 mission control center
**Duration**: 5 days (Monday through Friday)
**ADAPT Phases Exercised**: All five -- DISCOVER, CORRELATE, VALIDATE, FORTIFY, PROVE
**Platform Modules Used**: 22 of 25+ available
**Estimated Loss Avoided**: EUR 340M (satellite constellation operational continuity)

### Background: The 2025 Satellite Threat Landscape

In January 2025, CISA published Advisory AA25-009A documenting Volt Typhoon's pivot from US critical infrastructure to European satellite operators. The advisory described pre-positioning techniques -- living-off-the-land binaries, compromised SOHO routers as relay points, and exploitation of ground station VPN appliances. By July, CERT-EU confirmed three European satellite operators had experienced reconnaissance activity matching Volt Typhoon TTPs.

I was the lead threat intelligence analyst at ESOC-PRIME when the first alert came in. Clara was my partner on the analysis desk. We'd been working together for eight months by then, and she had this way of reading intelligence that was different from anyone I'd ever worked with. She didn't just look at the data. She looked at what the data was trying to *not* tell you.

This is the complete investigation, told through every API call, SQL query, and decision point. And in the margins, Clara's annotations -- the ones she left in the evidence vault before the DGSE pulled her into Marseille.

### Dramatis Personae (All Synthetic)

| Role | Name | Callsign | Contact |
|------|------|----------|---------|
| Threat Intel Lead (me) | -- | ORBIT-1 | -- |
| Analysis Partner | Clara Dubois | PRISM-6 | +33-555-0808 |
| SOC Lead | Captain Marco Bellini | GROUND-3 | +39-555-0802 |
| Incident Commander | Colonel Pierre Moreau | ZENITH | +33-555-0803 |
| Forensics Lead | Dr. Ayumi Watanabe | EVIDENCE-9 | +49-555-0804 |
| CISO | Director Freya Lindqvist | SHIELD-SAT | +46-555-0805 |
| NATO CERT Liaison | Major David Kowalski | ALLIANCE-7 | +32-555-0806 |

### Network Topology (Synthetic)

| Segment | CIDR | Purpose | Classification |
|---------|------|---------|---------------|
| Ground Station Alpha | 10.100.10.0/24 | Kourou uplink facility | RESTRICTED |
| Ground Station Bravo | 10.100.20.0/24 | Darmstadt control center | SECRET |
| Ground Station Charlie | 10.100.30.0/24 | Svalbard polar station | RESTRICTED |
| Telemetry Network | 10.100.40.0/24 | Satellite telemetry processing | SECRET |
| Corporate LAN | 10.100.50.0/24 | Office workstations, email | OFFICIAL |
| VPN/Remote Access | 10.100.60.0/24 | Contractor and remote staff | RESTRICTED |
| Management/OOB | 10.100.70.0/24 | Infrastructure management | RESTRICTED |

### Key Infrastructure (Synthetic)

| Hostname | IP | OS | Role |
|----------|----|----|------|
| GS-ALPHA-CTRL-01 | 10.100.10.5 | RHEL 9 | Ground station controller |
| GS-BRAVO-CTRL-01 | 10.100.20.5 | RHEL 9 | Mission control primary |
| GS-CHARLIE-CTRL-01 | 10.100.30.5 | RHEL 9 | Polar station controller |
| TLM-PROC-01 | 10.100.40.10 | Ubuntu 22.04 | Telemetry processor |
| DC-ESOC-01 | 10.100.50.5 | Windows Server 2022 | Domain controller |
| VPN-GW-01 | 10.100.60.1 | FortiGate 7.4 | VPN gateway |
| MAIL-01 | 10.100.50.20 | Exchange 2019 | Email gateway |
| JUMP-01 | 10.100.70.10 | Ubuntu 22.04 | Jump server (OOB) |

---

## Day 1 (Monday) -- STIX Feed Ingests New IOCs

### 08:17 UTC -- The First Alert

I arrived at my desk at 08:00. Clara was already there -- she always beat me in by twenty minutes, a habit from her DGSE training that she never talked about. I didn't know she was DGSE then. I just thought she was punctual.

By 08:17 the ADAPT Autopilot cycle had flagged something that made my coffee go cold. Our CERT-EU STIX feed had ingested 47 new IOCs overnight, and 6 of them matched infrastructure connected to our satellite ground stations.

```bash
# Check latest ADAPT cycle status
curl -s http://localhost:3000/api/v1/adapt/cycles \
  -H "Authorization: Bearer $TOKEN" | jq '.[0]'
```

```json
{
  "id": "0194c100-a001-7000-8000-000000000001",
  "cycle_number": 6284,
  "status": "Completed",
  "started_at": "2025-08-11T08:00:00Z",
  "completed_at": "2025-08-11T08:17:03Z",
  "events_discovered": 14,
  "correlations_computed": 6,
  "actions_generated": 3
}
```

Clara saw it the same time I did. She didn't say anything. She just pulled her chair closer to my screen and started reading.

### 08:20 UTC -- Reviewing the STIX Ingestion

The feed aggregator had pulled in a fresh CERT-EU advisory tied to Volt Typhoon activity against satellite operators.

```bash
# List recent feed ingestion events
curl -s http://localhost:3000/api/v1/feedaggregator/ingest \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "feed_id": "0194c100-f001-7000-8000-000000000001",
    "format": "stix2.1",
    "source_url": "https://feeds.cert-eu.synth.gov/volt-typhoon-satellite-2025.json"
  }'
```

```json
{
  "ingestion_id": "0194c100-f100-7000-8000-000000000001",
  "feed_name": "CERT-EU Satellite Advisory",
  "format": "stix2.1",
  "indicators_ingested": 47,
  "indicators_new": 42,
  "indicators_updated": 5,
  "indicators_matched_internal": 6,
  "confidence_avg": 0.87,
  "ingested_at": "2025-08-11T06:30:00Z"
}
```

Six indicators matched our infrastructure. That's not a drill number. I pulled the specific matches.

```bash
# Retrieve IOC matches against our asset inventory
curl -s http://localhost:3000/api/v1/iocmanager?search=volt-typhoon-sat \
  -H "Authorization: Bearer $TOKEN" | jq '.[] | select(.matched == true)'
```

```json
[
  {
    "id": "0194c101-0001-7000-8000-000000000001",
    "ioc_type": "ip_address",
    "value": "103.224.182.47",
    "source": "CERT-EU IR-2025-011",
    "confidence": 0.92,
    "matched": true,
    "matched_asset": "VPN-GW-01 (10.100.60.1)",
    "match_type": "inbound_connection",
    "first_seen": "2025-08-09T03:22:00Z",
    "last_seen": "2025-08-11T01:15:00Z",
    "tags": ["volt-typhoon", "satellite-targeting", "soho-relay"]
  },
  {
    "id": "0194c101-0001-7000-8000-000000000002",
    "ioc_type": "domain",
    "value": "update-service.fortinet-cdn[.]net",
    "source": "CERT-EU IR-2025-011",
    "confidence": 0.89,
    "matched": true,
    "matched_asset": "VPN-GW-01 (10.100.60.1)",
    "match_type": "dns_resolution",
    "first_seen": "2025-08-10T11:42:00Z",
    "last_seen": "2025-08-10T23:58:00Z",
    "tags": ["volt-typhoon", "c2-infrastructure", "typosquat"]
  },
  {
    "id": "0194c101-0001-7000-8000-000000000003",
    "ioc_type": "file_hash",
    "value": "a3f2c891d7e4b0056f8912ab34cd5678ef901234567890abcdef1234567890ab",
    "source": "CISA AA25-009A",
    "confidence": 0.94,
    "matched": true,
    "matched_asset": "JUMP-01 (10.100.70.10)",
    "match_type": "file_present",
    "first_seen": "2025-08-09T14:07:00Z",
    "tags": ["volt-typhoon", "living-off-land", "proxy-tool"]
  }
]
```

Three matching IOCs on the VPN gateway. One file hash on our jump server. Clara picked up her pen and started writing in her notebook -- the leather-bound one she carried everywhere. I'd only later understand that those notes were going to the DGSE.

"The VPN gateway," she said quietly. "That's the front door. But what's interesting is the jump server. That's the back door. They're not coming in through the VPN -- they've already *been* in. The VPN connections are maintenance traffic."

She was right. And that insight would save us two days of investigation.

### 08:35 UTC -- Opening the Incident

```bash
# Create incident
curl -s -X POST http://localhost:3000/api/v1/incident/incidents \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "INC-2025-0089: Potential Volt Typhoon Activity on Satellite Ground Infrastructure",
    "description": "STIX feed ingestion matched 6 IOCs from CERT-EU IR-2025-011 to ESOC-PRIME infrastructure. Matches include inbound connections to VPN-GW-01 from known Volt Typhoon relay (103.224.182.47), DNS resolution of C2 typosquat domain, and suspicious file hash on JUMP-01. Requires immediate investigation.",
    "priority": "critical",
    "affected_systems": ["VPN-GW-01", "JUMP-01", "GS-ALPHA-CTRL-01", "GS-BRAVO-CTRL-01", "GS-CHARLIE-CTRL-01"]
  }' | jq
```

```json
{
  "id": "0194c102-aa01-7000-8000-000000000001",
  "title": "INC-2025-0089: Potential Volt Typhoon Activity on Satellite Ground Infrastructure",
  "priority": "critical",
  "phase": "identification",
  "status": "open",
  "created_at": "2025-08-11T08:35:00Z"
}
```

### 09:00 UTC -- ADAPT CORRELATE Runs

The correlation engine matched our 6 IOC hits against the broader threat landscape.

```bash
# Retrieve correlations for this cycle
curl -s http://localhost:3000/api/v1/adapt/correlations/high-risk \
  -H "Authorization: Bearer $TOKEN" | jq '.'
```

```json
[
  {
    "id": "0194c103-0001-7000-8000-000000000001",
    "cycle_id": "0194c100-a001-7000-8000-000000000001",
    "exposure_event_id": "0194c100-e001-7000-8000-000000000001",
    "threat_type": "Ioc",
    "threat_id": "VOLT-TYPHOON-SAT-2025-001",
    "risk_score": 94.7,
    "exposure_score": 95.0,
    "threat_score": 97.0,
    "exploitability_score": 88.0,
    "criticality_score": 99.0,
    "details": "6 IOCs matched from CERT-EU advisory IR-2025-011. Volt Typhoon pre-positioning against satellite ground stations. VPN gateway shows inbound connections from known SOHO relay network. Criticality: satellite operations support EUR 12B constellation."
  }
]
```

Risk score 94.7. Criticality 99.0 -- because if they get to the ground station controllers, they can disrupt an entire satellite constellation. The risk score breakdown:

```
Risk Score = (95.0 x 0.30) + (97.0 x 0.25) + (88.0 x 0.25) + (99.0 x 0.20)
           = 28.5 + 24.25 + 22.0 + 19.8
           = 94.55 --> 94.7 (with temporal boost for active campaign)
```

Clara looked at the number and said: "Ninety-four-seven. That's not a score. That's a countdown."

I didn't understand what she meant at the time. Now, sitting here at T-minus 9 hours to STARLIGHT, watching a different countdown, I understand perfectly.

### 10:00 UTC -- Genome Matching

I ran the genome comparison to confirm we were dealing with Volt Typhoon and not a copycat.

```bash
# Run genome comparison
curl -s -X POST http://localhost:3000/api/v1/threatintel/genome/compare \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "ioc_set": [
      "103.224.182.47", "103.224.182.48",
      "update-service.fortinet-cdn.net",
      "telemetry.esoc-patch.net",
      "a3f2c891d7e4b0056f8912ab34cd5678ef901234567890abcdef1234567890ab"
    ],
    "compare_against": "Volt Typhoon"
  }'
```

```json
{
  "actor": "Volt Typhoon",
  "aliases": ["BRONZE SILHOUETTE", "Vanguard Panda", "DEV-0391", "Insidious Taurus"],
  "jaccard_similarity": 0.78,
  "matching_iocs": 4,
  "total_iocs_in_genome": 892,
  "confidence": "HIGH",
  "last_campaign": "US Critical Infrastructure (2023-2025), European Satellite Operators (2025)",
  "ttp_overlap": {
    "T1190": "Exploit Public-Facing Application (FortiGate VPN)",
    "T1059.001": "PowerShell (living-off-the-land)",
    "T1071.001": "Web Protocols (HTTPS C2)",
    "T1078": "Valid Accounts (contractor credentials)",
    "T1021.004": "Remote Services: SSH"
  }
}
```

Jaccard similarity 0.78 with 4 direct IOC matches and 5 overlapping TTPs. This was not a coincidence.

### Day 1 SQL -- What Did the VPN Gateway See?

I needed raw connection data. The platform's streaming analytics had been recording everything.

```sql
-- Query VPN gateway connection logs for suspicious source IPs
SELECT
    s.id,
    s.source_ip,
    s.destination_ip,
    s.destination_port,
    s.protocol,
    s.bytes_sent,
    s.bytes_received,
    s.duration_secs,
    s.geo_country,
    s.created_at
FROM stream_events s
WHERE s.destination_ip = '10.100.60.1'
  AND s.source_ip IN ('103.224.182.47', '103.224.182.48')
  AND s.created_at >= NOW() - INTERVAL '7 days'
ORDER BY s.created_at DESC;
```

| source_ip | dest_port | bytes_sent | bytes_received | geo_country | created_at |
|-----------|-----------|-----------|---------------|-------------|------------|
| 103.224.182.47 | 443 | 2,847 | 156,923 | TW | 2025-08-11T01:15:00Z |
| 103.224.182.47 | 443 | 3,102 | 203,445 | TW | 2025-08-10T19:30:00Z |
| 103.224.182.48 | 443 | 1,456 | 89,201 | TW | 2025-08-10T11:42:00Z |
| 103.224.182.47 | 443 | 4,510 | 312,778 | TW | 2025-08-09T22:05:00Z |
| 103.224.182.47 | 443 | 2,201 | 145,660 | TW | 2025-08-09T03:22:00Z |

Five connections over 3 days. Small outbound bytes (commands), large inbound bytes (data exfiltration). Classic C2 pattern. The IPs geolocated to Taiwan but CERT-EU confirmed they were compromised SOHO routers being used as relay points -- a signature Volt Typhoon technique.

Clara circled the bytes_received column in red. "That's telemetry data," she said. "They're pulling satellite orbital parameters. Why would an intelligence service want orbital parameters unless they're planning to interfere with positioning?"

She was building a theory that went beyond espionage into potential sabotage. I logged her analysis into the evidence vault.

---

## Day 2 (Tuesday) -- OSINT Discovers Domain Registration Patterns

### 07:30 UTC -- OSINT Task Creation

I tasked the OSINT module with investigating the C2 infrastructure. Clara had left me a note on my desk -- she'd been running her own queries before dawn.

*"Look at the nameservers. They're shared. Shared nameservers mean lazy tradecraft or deliberate grouping. Either way, it's a thread you can pull."* -- Clara's handwritten note, now in the evidence vault as EV-2025-0089-NOTE-001.

```bash
# Create OSINT collection task for domain investigation
curl -s -X POST http://localhost:3000/api/v1/osint/tasks \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "ORBITAL-SHADOW: C2 Domain Infrastructure Mapping",
    "task_type": "infrastructure_mapping",
    "target": {
      "type": "domain_cluster",
      "identifiers": {
        "known_domains": [
          "update-service.fortinet-cdn.net",
          "telemetry.esoc-patch.net"
        ],
        "registration_patterns": ["*-service.*-cdn.*", "*telemetry.*-patch.*"],
        "ip_ranges": ["103.224.182.0/24"]
      }
    },
    "sources": ["domain_whois", "dns_records", "certificate_transparency", "passive_dns"],
    "priority": "critical",
    "deadline": "2025-08-12T00:00:00Z"
  }' | jq
```

```json
{
  "id": "0194c200-b001-7000-8000-000000000001",
  "name": "ORBITAL-SHADOW: C2 Domain Infrastructure Mapping",
  "status": "running",
  "tasks_queued": 4,
  "estimated_completion": "2025-08-11T09:30:00Z"
}
```

### 09:45 UTC -- OSINT Results Come In

Clara was right about the nameservers. The results painted a disturbing picture. I was looking at coordinated infrastructure registration that pre-dated the first connection by 60 days.

```bash
# Retrieve OSINT task results
curl -s http://localhost:3000/api/v1/osint/tasks/0194c200-b001-7000-8000-000000000001 \
  -H "Authorization: Bearer $TOKEN" | jq '.findings'
```

```json
{
  "findings": [
    {
      "source": "domain_whois",
      "findings_count": 7,
      "details": [
        {
          "domain": "update-service.fortinet-cdn.net",
          "registrar": "GoDaddy (privacy-protected)",
          "registered_date": "2025-06-15",
          "nameservers": ["ns1.hostinger.synth.com", "ns2.hostinger.synth.com"],
          "registrant_email": "privacy@domainsbyproxy.synth.com"
        },
        {
          "domain": "telemetry.esoc-patch.net",
          "registrar": "GoDaddy (privacy-protected)",
          "registered_date": "2025-06-16",
          "nameservers": ["ns1.hostinger.synth.com", "ns2.hostinger.synth.com"],
          "registrant_email": "privacy@domainsbyproxy.synth.com"
        },
        {
          "domain": "patch-service.esa-update.org",
          "registrar": "GoDaddy (privacy-protected)",
          "registered_date": "2025-06-17",
          "nameservers": ["ns1.hostinger.synth.com", "ns2.hostinger.synth.com"],
          "registrant_email": "privacy@domainsbyproxy.synth.com",
          "note": "NEW: Not previously known. Typosquats ESA (European Space Agency)."
        }
      ]
    },
    {
      "source": "certificate_transparency",
      "findings_count": 5,
      "details": [
        {
          "domain": "update-service.fortinet-cdn.net",
          "issuer": "Let's Encrypt",
          "issued_date": "2025-06-20",
          "san_domains": ["update-service.fortinet-cdn.net", "*.fortinet-cdn.net"],
          "note": "Wildcard cert. Could cover additional subdomains."
        },
        {
          "domain": "patch-service.esa-update.org",
          "issuer": "Let's Encrypt",
          "issued_date": "2025-06-22",
          "san_domains": ["patch-service.esa-update.org", "api.esa-update.org", "telemetry.esa-update.org"],
          "note": "NEW: Three SAN entries suggest planned multi-purpose infrastructure."
        }
      ]
    },
    {
      "source": "passive_dns",
      "findings_count": 12,
      "details": [
        {
          "domain": "update-service.fortinet-cdn.net",
          "resolved_ips": ["103.224.182.47", "103.224.182.49"],
          "first_resolution": "2025-06-21",
          "resolution_count": 847,
          "note": "Resolved to two IPs in same /24 block"
        },
        {
          "domain": "patch-service.esa-update.org",
          "resolved_ips": ["103.224.182.50"],
          "first_resolution": "2025-06-23",
          "resolution_count": 234,
          "note": "NEW: Same IP range as known C2"
        }
      ]
    }
  ]
}
```

The pattern was clear. Seven domains registered in a 5-day window in June 2025. Same registrar, same nameservers, same privacy proxy, same IP range. This was operational infrastructure stood up 60 days before first use -- consistent with Volt Typhoon's known patience.

Clara's note had been dead right. The shared nameservers were the thread. Pull one, and the whole tapestry unravels.

I'm thinking about this now because PHANTOM MERCY has the same pattern. Different domain. Different registrar. But the same *behavior* -- infrastructure registered weeks before use, clustered around shared services. Clara spotted it in satellites. I need to spot it in Marseille.

### 10:30 UTC -- Building the Ontology Graph

I needed to visualize the full infrastructure relationship.

```bash
# Build ontology graph from OSINT findings
curl -s -X POST http://localhost:3000/api/v1/ontology/graph \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "root_entity": "103.224.182.47",
    "entity_type": "ip_address",
    "depth": 5,
    "include_types": ["domain", "ip_address", "certificate", "registrar", "nameserver", "actor"]
  }'
```

```json
{
  "nodes": [
    {"id": "103.224.182.47", "type": "ip_address", "label": "C2 Relay 1 (Taiwan)"},
    {"id": "103.224.182.48", "type": "ip_address", "label": "C2 Relay 2 (Taiwan)"},
    {"id": "103.224.182.49", "type": "ip_address", "label": "C2 Relay 3 (Taiwan)"},
    {"id": "103.224.182.50", "type": "ip_address", "label": "C2 Relay 4 (Taiwan)"},
    {"id": "update-service.fortinet-cdn.net", "type": "domain", "label": "C2 Domain 1"},
    {"id": "telemetry.esoc-patch.net", "type": "domain", "label": "C2 Domain 2"},
    {"id": "patch-service.esa-update.org", "type": "domain", "label": "C2 Domain 3 (NEW)"},
    {"id": "ns1.hostinger.synth.com", "type": "nameserver", "label": "Shared NS"},
    {"id": "LE-WILDCARD-2025-06", "type": "certificate", "label": "Let's Encrypt Wildcard"},
    {"id": "Volt Typhoon", "type": "actor", "label": "JADE PANDA"}
  ],
  "edges": [
    {"from": "update-service.fortinet-cdn.net", "to": "103.224.182.47", "relation": "resolves_to"},
    {"from": "update-service.fortinet-cdn.net", "to": "103.224.182.49", "relation": "resolves_to"},
    {"from": "telemetry.esoc-patch.net", "to": "103.224.182.48", "relation": "resolves_to"},
    {"from": "patch-service.esa-update.org", "to": "103.224.182.50", "relation": "resolves_to"},
    {"from": "update-service.fortinet-cdn.net", "to": "ns1.hostinger.synth.com", "relation": "uses_nameserver"},
    {"from": "telemetry.esoc-patch.net", "to": "ns1.hostinger.synth.com", "relation": "uses_nameserver"},
    {"from": "patch-service.esa-update.org", "to": "ns1.hostinger.synth.com", "relation": "uses_nameserver"},
    {"from": "Volt Typhoon", "to": "103.224.182.47", "relation": "operates"},
    {"from": "Volt Typhoon", "to": "update-service.fortinet-cdn.net", "relation": "registered"}
  ],
  "total_nodes": 10,
  "total_edges": 9
}
```

When Clara saw the ontology graph, she leaned back in her chair and said something I didn't fully appreciate until tonight: "The APT that hides inside critical infrastructure always has a blind spot. It's the shared service. The nameserver. The registrar. The thing they need to coordinate but can't fully control."

ORBITAL SHADOW taught me that. It's the same blind spot PHANTOM MERCY has. They need to coordinate across cities, across borders, across corrupted officials. And that coordination layer -- that's where they're visible.

### 11:00 UTC -- Adding the Third Domain to IOC Manager

The OSINT discovery of `patch-service.esa-update.org` was new intelligence. I pushed it into the IOC manager immediately.

```bash
# Add newly discovered IOC
curl -s -X POST http://localhost:3000/api/v1/iocmanager \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "ioc_type": "domain",
    "value": "patch-service.esa-update.org",
    "source": "OSINT-ORBITAL-SHADOW-002",
    "confidence": 0.85,
    "tags": ["volt-typhoon", "c2-infrastructure", "typosquat", "esa-impersonation"],
    "description": "Newly discovered C2 domain. Same registrar, nameserver, IP range, and registration window as confirmed Volt Typhoon infrastructure. Typosquats European Space Agency.",
    "tlp": "amber"
  }' | jq
```

### 14:00 UTC -- AI Analysis of the Campaign

I ran the AI analysis pipeline to get a structured assessment. Clara insisted on reviewing the prompt before I submitted it -- she had strong opinions about how you frame questions for the AI module.

"Don't ask it what's happening," she said. "Ask it what the attacker *needs* to happen next. That's where you'll find the gap."

```bash
# Run AI analysis on the collected intelligence
curl -s -X POST http://localhost:3000/api/v1/ai/analyze \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "context": "satellite_infrastructure_threat",
    "incident_id": "0194c102-aa01-7000-8000-000000000001",
    "data_sources": ["ioc_matches", "osint_findings", "genome_comparison", "network_logs"],
    "analysis_type": "campaign_assessment",
    "prompt": "Analyze the collected evidence and assess what the attacker needs to accomplish next to achieve their objective. Identify the gap between their current access and their goal."
  }' | jq
```

```json
{
  "id": "0194c201-c001-7000-8000-000000000001",
  "analysis_type": "campaign_assessment",
  "confidence": 0.89,
  "assessment": {
    "campaign_name": "ORBITAL SHADOW (Playseat designation)",
    "attribution": "Volt Typhoon / JADE PANDA (MSS-linked, HIGH confidence)",
    "intent": "Pre-positioning for disruption of European satellite ground station operations. Consistent with Volt Typhoon's documented strategy of establishing persistent access to critical infrastructure for potential activation during geopolitical crisis.",
    "capability": "HIGH -- Actor demonstrates sophisticated LOTL techniques, patient infrastructure preparation (60-day lead time), and deep knowledge of satellite ground station architecture.",
    "gap_analysis": "Attacker has VPN access and jump server presence but has NOT yet reached ground station controllers (10.100.10.x, 10.100.20.x, 10.100.30.x). The gap is lateral movement from OOB/Management network to the operational technology network. They need contractor credentials with OT access.",
    "timeline": {
      "infrastructure_setup": "2025-06-15 to 2025-06-23",
      "first_access_attempt": "2025-08-09T03:22:00Z",
      "last_known_activity": "2025-08-11T01:15:00Z",
      "estimated_dwell_time": "48-72 hours"
    },
    "recommended_actions": [
      "Isolate VPN-GW-01 and perform forensic imaging",
      "Full memory dump of JUMP-01 for implant analysis",
      "Credential rotation for all contractor VPN accounts",
      "Block 103.224.182.0/24 at perimeter",
      "DNS sinkhole all identified C2 domains",
      "Sweep all ground station controllers for lateral movement indicators",
      "Engage NATO CERT for cross-organizational intelligence sharing"
    ]
  }
}
```

Clara read the AI output and underlined one word: *contractor*. "They're going to use a contractor account," she said. "State actors always use contractor accounts to cross the IT/OT boundary. The contractor has legitimate access to both worlds. That's the bridge."

She was telling me something about how adversaries think. Not about satellites. About how they find the people who move between worlds and exploit them. I think she was also telling me something about herself -- about what it's like to be the person who moves between worlds. Between the DGSE and the analysis desk. Between the intelligence she gathered and the life she lived.

I didn't understand it then. I do now.

---

## Day 3 (Wednesday) -- Geofence Alerts at Ground Stations

### 06:45 UTC -- The Geofence Triggers

I had set up geofence monitoring around all three ground stations after Day 1. At 06:45, the system flagged exactly what Clara predicted.

```bash
# Check geofence alerts
curl -s http://localhost:3000/geotrack/geofences/0194c300-g001-7000-8000-000000000001/alerts \
  -H "Authorization: Bearer $TOKEN" | jq '.'
```

```json
[
  {
    "id": "0194c301-a001-7000-8000-000000000001",
    "geofence_id": "0194c300-g001-7000-8000-000000000001",
    "geofence_name": "Ground Station Alpha - Kourou - 5km Perimeter",
    "alert_type": "unauthorized_access_pattern",
    "severity": "high",
    "details": {
      "event": "VPN connection from contractor account 'j.zhang@subcontractor-sat.synth.com' originating from IP 45.77.102.33 (Singapore) at 06:42 UTC",
      "anomaly": "Account normally connects from Frankfurt, Germany (10.100.50.0/24). First connection from Singapore in 14 months of baseline data.",
      "accessed_resources": ["GS-ALPHA-CTRL-01 SSH (port 22)", "TLM-PROC-01 HTTP (port 8080)"],
      "geo_distance_km": 10247
    },
    "triggered_at": "2025-08-13T06:45:00Z"
  },
  {
    "id": "0194c301-a001-7000-8000-000000000002",
    "geofence_id": "0194c300-g002-7000-8000-000000000001",
    "geofence_name": "Ground Station Bravo - Darmstadt - Network Perimeter",
    "alert_type": "anomalous_login_time",
    "severity": "medium",
    "details": {
      "event": "VPN connection from contractor account 'l.chen@subcontractor-sat.synth.com' at 06:38 UTC",
      "anomaly": "Account has never logged in before 08:00 UTC in 8 months of baseline. Source IP 10.100.60.55 (internal VPN pool) but session initiated from unusual source.",
      "accessed_resources": ["GS-BRAVO-CTRL-01 SSH (port 22)"]
    },
    "triggered_at": "2025-08-13T06:45:00Z"
  }
]
```

Two contractor accounts. Both accessing ground station controllers at unusual times from unusual locations. Compromised contractor credentials -- exactly what Clara predicted. The geographic spread pointed to a coordinated operation using the subcontractor as a single point of compromise.

I texted Clara: "You were right. Contractor accounts. Two of them."

She texted back one word: "Four."

She was right about that too. But we wouldn't find the other two until Day 4.

### 07:15 UTC -- Creating Geofence for Investigation

I set up tighter monitoring.

```bash
# Create enhanced geofence for contractor account monitoring
curl -s -X POST http://localhost:3000/geotrack/geofences \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "ORBITAL-SHADOW: Contractor Account Geo-Monitoring",
    "geofence_type": "logical",
    "boundary": {
      "type": "ip_geofence",
      "allowed_countries": ["DE", "FR", "SE", "NO"],
      "allowed_cidrs": ["10.100.50.0/24", "10.100.60.0/24"],
      "monitored_accounts": [
        "j.zhang@subcontractor-sat.synth.com",
        "l.chen@subcontractor-sat.synth.com",
        "m.wang@subcontractor-sat.synth.com",
        "y.liu@subcontractor-sat.synth.com"
      ]
    },
    "alert_on": ["outside_boundary", "unusual_time", "unusual_resource"],
    "severity": "critical",
    "notify": ["ORBIT-1", "GROUND-3", "ZENITH"]
  }' | jq
```

### 08:00 UTC -- Cross-Referencing with SOAR Auto-Containment

The SOAR module had already triggered partial containment based on the geofence alert.

```bash
# Check SOAR execution log
curl -s http://localhost:3000/api/v1/soar/playbooks/executions?incident_id=0194c102-aa01-7000-8000-000000000001 \
  -H "Authorization: Bearer $TOKEN" | jq '.'
```

```json
{
  "executions": [
    {
      "id": "0194c302-s001-7000-8000-000000000001",
      "playbook_name": "PB-GEOFENCE-VIOLATION-001",
      "trigger": "geofence_alert_critical",
      "status": "completed",
      "steps_completed": [
        {
          "step": 1,
          "action": "account_lock",
          "target": "j.zhang@subcontractor-sat.synth.com",
          "status": "completed",
          "executed_at": "2025-08-13T06:46:12Z"
        },
        {
          "step": 2,
          "action": "session_terminate",
          "target": "VPN session from 45.77.102.33",
          "status": "completed",
          "executed_at": "2025-08-13T06:46:15Z"
        },
        {
          "step": 3,
          "action": "firewall_block_ip",
          "target": "45.77.102.33",
          "status": "completed",
          "executed_at": "2025-08-13T06:46:18Z"
        },
        {
          "step": 4,
          "action": "memory_snapshot",
          "target": "GS-ALPHA-CTRL-01",
          "status": "completed",
          "executed_at": "2025-08-13T06:47:01Z"
        },
        {
          "step": 5,
          "action": "notify_team",
          "target": "incident_commander",
          "status": "completed",
          "executed_at": "2025-08-13T06:47:05Z"
        }
      ]
    }
  ]
}
```

SOAR locked the account in 12 seconds, killed the VPN session in 15 seconds, and took a memory snapshot of the ground station controller. That memory dump would prove crucial on Day 5.

Twelve seconds. I keep coming back to that number. Because tonight, for STARLIGHT, we won't have twelve seconds. We'll have whatever window the GIGN assault team gives us to pull Clara's location data from PHANTOM MERCY's communications relay before they destroy the evidence. And I need that window to be enough.

### 10:00 UTC -- Timeline Reconstruction

```bash
# Retrieve full incident timeline
curl -s http://localhost:3000/api/v1/incident/incidents/0194c102-aa01-7000-8000-000000000001/timeline \
  -H "Authorization: Bearer $TOKEN" | jq '.'
```

```json
{
  "incident_id": "0194c102-aa01-7000-8000-000000000001",
  "timeline": [
    {"time": "2025-06-15T00:00:00Z", "event": "C2 infrastructure registration begins", "phase": "preparation"},
    {"time": "2025-08-09T03:22:00Z", "event": "First inbound connection from 103.224.182.47 to VPN-GW-01", "phase": "initial_access"},
    {"time": "2025-08-09T14:07:00Z", "event": "Suspicious file hash detected on JUMP-01", "phase": "installation"},
    {"time": "2025-08-10T11:42:00Z", "event": "DNS resolution of C2 typosquat domain from VPN-GW-01", "phase": "c2"},
    {"time": "2025-08-11T01:15:00Z", "event": "Latest C2 callback from 103.224.182.47", "phase": "c2"},
    {"time": "2025-08-11T08:17:00Z", "event": "ADAPT Cycle #6284 detects IOC matches (Day 1)", "phase": "detection"},
    {"time": "2025-08-12T09:45:00Z", "event": "OSINT reveals 7-domain C2 infrastructure cluster (Day 2)", "phase": "intelligence"},
    {"time": "2025-08-13T06:42:00Z", "event": "Contractor account j.zhang accesses GS-ALPHA-CTRL-01 from Singapore (Day 3)", "phase": "lateral_movement"},
    {"time": "2025-08-13T06:46:12Z", "event": "SOAR auto-containment: account locked, session killed, IP blocked", "phase": "containment"}
  ]
}
```

---

## Day 4 (Thursday) -- UEBA Detects the Other Two Contractors

### 09:00 UTC -- Clara Was Right: Four Accounts

Clara had said four. Here were the other two.

```bash
# Check behavioral anomalies for contractor accounts
curl -s http://localhost:3000/behavioral/anomalies/critical \
  -H "Authorization: Bearer $TOKEN" | jq '.'
```

```json
[
  {
    "id": "0194c401-b001-7000-8000-000000000001",
    "entity_id": "019516a3-0001-7000-8000-000000000042",
    "entity_type": "user",
    "entity_name": "m.wang@subcontractor-sat.synth.com",
    "anomaly_type": "data_access_pattern",
    "severity": "critical",
    "deviation_score": 4.7,
    "baseline_deviation": {
      "normal_files_accessed_per_day": 12,
      "observed_files_accessed": 847,
      "normal_data_volume_mb": 45,
      "observed_data_volume_mb": 3200,
      "normal_access_hours": "08:00-18:00 CET",
      "observed_access_hours": "02:00-05:00 CET"
    },
    "description": "Account m.wang accessed 847 files (70x baseline) totaling 3.2 GB (71x baseline) between 02:00-05:00 CET. Files include satellite telemetry configuration, ground station frequency tables, and orbital parameter databases. Access pattern consistent with data staging for exfiltration.",
    "detected_at": "2025-08-14T09:00:00Z"
  },
  {
    "id": "0194c401-b001-7000-8000-000000000002",
    "entity_id": "019516a3-0001-7000-8000-000000000043",
    "entity_type": "user",
    "entity_name": "y.liu@subcontractor-sat.synth.com",
    "anomaly_type": "privilege_escalation",
    "severity": "high",
    "deviation_score": 3.9,
    "baseline_deviation": {
      "normal_groups": ["sat-contractors-read"],
      "observed_groups": ["sat-contractors-read", "gs-admin", "tlm-operators"],
      "escalation_method": "Group policy modification via DC-ESOC-01"
    },
    "description": "Account y.liu was added to gs-admin and tlm-operators groups via GPO modification at 03:17 CET. Account baseline shows no prior administrative access. GPO change originated from DC-ESOC-01 using local admin credentials.",
    "detected_at": "2025-08-14T09:00:00Z"
  }
]
```

Four contractor accounts from the same subcontractor. Two caught on Day 3 (j.zhang, l.chen). Two more showing massive data staging and privilege escalation. Clara had predicted the exact number from just the behavioral pattern.

I asked her later how she knew. She said: "In intelligence work, you always assume the compromise is larger than the evidence shows. If they compromised two accounts, they compromised the subcontractor's whole identity management. And that subcontractor has four people with satellite access."

That's the same logic I'm applying to PHANTOM MERCY tonight. If they've corrupted one INTERPOL liaison officer, how many others are compromised? Clara's letter -- the one she left in the evidence vault before going under -- says twelve. Twelve officials across four countries.

### 10:00 UTC -- Insider Threat Assessment

```bash
# Run insider threat assessment on contractor group
curl -s -X POST http://localhost:3000/behavioral/insider-threats/assess \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "entity_ids": [
      "019516a3-0001-7000-8000-000000000042",
      "019516a3-0001-7000-8000-000000000043",
      "019516a3-0001-7000-8000-000000000044",
      "019516a3-0001-7000-8000-000000000045"
    ],
    "assessment_type": "coordinated_activity",
    "include_network_behavior": true,
    "include_data_access": true,
    "include_temporal_correlation": true
  }' | jq
```

```json
{
  "assessment_id": "0194c402-it01-7000-8000-000000000001",
  "assessment_type": "coordinated_activity",
  "risk_level": "critical",
  "coordination_score": 0.94,
  "findings": [
    {
      "finding": "All 4 accounts are from same subcontractor (SatLink Systems GmbH -- synthetic)",
      "significance": "Single point of compromise"
    },
    {
      "finding": "Activity windows overlap: all 4 accounts active between 02:00-05:00 CET (outside business hours)",
      "significance": "Coordinated operational window"
    },
    {
      "finding": "Data access targets are complementary: frequency tables + orbital parameters + telemetry configs = complete ground station operational picture",
      "significance": "Intelligence collection objectives"
    },
    {
      "finding": "Privilege escalation on y.liu preceded data staging on m.wang by 43 minutes",
      "significance": "Sequential attack chain"
    }
  ],
  "recommendation": "Assess as nation-state credential compromise of subcontractor. Lock all 4 accounts. Engage subcontractor security team. Preserve all evidence for attribution and potential prosecution."
}
```

### 11:30 UTC -- Zero Trust Response

```bash
# Evaluate trust for all subcontractor sessions
curl -s -X POST http://localhost:3000/api/v1/zerotrust/evaluate \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "019516a3-0001-7000-8000-000000000042",
    "resource_id": "019516a3-r001-7000-8000-000000000001",
    "resource_type": "ground_station_controller",
    "resource_sensitivity": "critical",
    "session_context": {
      "auth_method": "password_only",
      "device_id": "UNKNOWN-DEVICE",
      "device_posture": {
        "os_patched": false,
        "edr_active": false,
        "disk_encrypted": false,
        "firewall_enabled": false
      },
      "network": {
        "type": "vpn",
        "source_ip": "45.77.102.33",
        "source_country": "SG"
      },
      "behavioral_score": 0.12
    }
  }' | jq
```

```json
{
  "decision": "DENY",
  "trust_score": 0.08,
  "factors": {
    "authentication_strength": {"score": 0.20, "weight": 0.25, "reason": "Password-only auth, no MFA"},
    "device_posture": {"score": 0.00, "weight": 0.20, "reason": "Unknown device, no EDR"},
    "network_location": {"score": 0.05, "weight": 0.15, "reason": "Foreign IP, non-standard VPN"},
    "behavioral_baseline": {"score": 0.12, "weight": 0.20, "reason": "4.7 sigma deviation from baseline"},
    "time_of_day": {"score": 0.00, "weight": 0.10, "reason": "Access at 02:00 CET, outside working hours"},
    "resource_sensitivity": {"score": 0.02, "weight": 0.10, "reason": "Critical ground station controller"}
  },
  "actions_taken": [
    "Account locked",
    "All active sessions terminated",
    "Incident escalation to ZENITH",
    "Evidence preservation initiated"
  ]
}
```

Trust score 0.08. DENY. Every factor was a red flag.

Clara's note on this (I found it in the evidence vault an hour ago, re-reading everything before STARLIGHT): *"Zero trust isn't a technology. It's a philosophy. Trust nothing. Verify everything. Even the people you trust. Especially the people you trust."*

She wrote that about satellite contractors. She could have been writing it about INTERPOL liaison officers working for PHANTOM MERCY. Or about DGSE agents who go under cover and stop sending check-in signals.

---

## Day 5 (Friday) -- Full ADAPT Cycle: DISCOVER Through PROVE

### 07:00 UTC -- VALIDATE Phase: Confirming the Compromise

The forensics team had imaged JUMP-01 and analyzed the memory dump from GS-ALPHA-CTRL-01. Clara was in the forensics lab with Dr. Watanabe -- she'd volunteered for the night shift to help with the memory analysis.

```bash
# Create forensic case
curl -s -X POST http://localhost:3000/api/v1/forensics/cases \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "case_name": "FC-2025-0091 -- ORBITAL SHADOW: Volt Typhoon Satellite Infrastructure Compromise",
    "case_type": "nation_state_espionage",
    "classification": "RESTRICTED",
    "priority": "critical",
    "jurisdiction": "eu_international",
    "incident_id": "0194c102-aa01-7000-8000-000000000001",
    "description": "Forensic investigation into Volt Typhoon compromise of ESOC-PRIME satellite ground station infrastructure via contractor credential abuse.",
    "lead_examiner": "019516a3-0001-7000-8000-000000000002",
    "examiners": [
      "019516a3-0001-7000-8000-000000000002",
      "019516a3-0001-7000-8000-000000000003"
    ]
  }' | jq
```

```json
{
  "id": "0194c501-fc01-7000-8000-000000000001",
  "case_number": "FC-2025-0091",
  "status": "open",
  "created_at": "2025-08-15T07:00:00Z"
}
```

### 07:30 UTC -- Memory Forensics on GS-ALPHA-CTRL-01

Clara found it. At 07:30, she called me from the forensics lab.

"I found the implant," she said. Her voice was calm, the way it always was when she found something important. "It's living inside the DNS resolver process. It's been there for at least two weeks. And it's talking to the domain you found yesterday -- the ESA typosquat."

```bash
# Analyze memory dump for injected processes
curl -s http://localhost:3000/api/v1/memforensics/dumps/0194c302-m001-7000-8000-000000000001/injections \
  -H "Authorization: Bearer $TOKEN" | jq '.'
```

```json
[
  {
    "process_name": "systemd-resolved",
    "pid": 1847,
    "injection_type": "shared_library_injection",
    "injected_library": "/tmp/.libcurl.so.4.fake",
    "hash_sha256": "b7c8d901e2f3a4b5c6d7e8f90a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b",
    "hash_blake3": "c8d9e0f1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9",
    "connections": [
      {"remote_ip": "103.224.182.50", "remote_port": 443, "protocol": "TLS1.3", "bytes_sent": 45678}
    ],
    "note": "Living-off-the-land technique: injected into legitimate DNS resolver process. Communicates with C2 domain patch-service.esa-update.org (the domain we discovered on Day 2 via OSINT)."
  }
]
```

The OSINT finding from Day 2 just validated. The third domain -- `patch-service.esa-update.org` -- was actively receiving data from our ground station controller. The injected library was masquerading as a system library in /tmp. Classic Volt Typhoon.

Clara had flagged the injection point before the automated tools did. She noticed the process had a file descriptor open to /tmp that shouldn't have been there. "Legitimate DNS resolvers don't read from /tmp," she told Dr. Watanabe. "Something's hiding."

That's the thing about Clara. She didn't look for the malware. She looked for the behavior that didn't belong. The file descriptor that shouldn't exist. The access pattern that didn't fit. The person in the room who was too careful.

I think that's also what made her a good undercover operative. She looks for what doesn't belong. Including, apparently, a trafficking network running operations out of an abandoned hospital in Marseille.

### 09:00 UTC -- Evidence Collection and Hashing

```bash
# Collect evidence with dual hashing
curl -s -X POST http://localhost:3000/api/v1/evidence \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "case_id": "0194c501-fc01-7000-8000-000000000001",
    "incident_id": "0194c102-aa01-7000-8000-000000000001",
    "evidence_type": "memory_dump",
    "title": "GS-ALPHA-CTRL-01 Memory Dump -- Injected Process",
    "description": "Memory dump captured by SOAR auto-containment at 2025-08-13T06:47:01Z. Contains injected shared library communicating with Volt Typhoon C2. Analysis performed by PRISM-6 (Clara Dubois) and EVIDENCE-9.",
    "hash_blake3": "c8d9e0f1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9",
    "hash_sha256": "b7c8d901e2f3a4b5c6d7e8f90a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b",
    "collected_by": "019516a3-0001-7000-8000-000000000002",
    "chain_of_custody": "SOAR auto-capture -> evidence locker -> forensics workstation (PRISM-6 + EVIDENCE-9)"
  }' | jq
```

```json
{
  "id": "0194c502-ev01-7000-8000-000000000001",
  "evidence_number": "EV-2025-0091-001",
  "title": "GS-ALPHA-CTRL-01 Memory Dump -- Injected Process",
  "integrity_verified": true,
  "hash_blake3": "c8d9e0f1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9",
  "hash_sha256": "b7c8d901e2f3a4b5c6d7e8f90a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b",
  "custody_chain": [
    {"action": "collected", "by": "SOAR-AUTO", "at": "2025-08-13T06:47:01Z"},
    {"action": "analyzed", "by": "PRISM-6", "at": "2025-08-15T07:30:00Z"},
    {"action": "verified", "by": "EVIDENCE-9", "at": "2025-08-15T08:00:00Z"},
    {"action": "transferred", "by": "EVIDENCE-9", "at": "2025-08-15T09:00:00Z"}
  ],
  "created_at": "2025-08-15T09:00:00Z"
}
```

### 11:00 UTC -- FORTIFY Phase: Defense Hardening

```bash
# Execute containment actions
curl -s -X POST http://localhost:3000/api/v1/incident/contain \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "incident_id": "0194c102-aa01-7000-8000-000000000001",
    "containment_type": "full",
    "actions": [
      {"type": "firewall_block_ip", "targets": ["103.224.182.0/24"], "scope": "perimeter"},
      {"type": "dns_sinkhole", "targets": ["update-service.fortinet-cdn.net", "telemetry.esoc-patch.net", "patch-service.esa-update.org"], "scope": "all_dns"},
      {"type": "account_lock", "targets": ["j.zhang", "l.chen", "m.wang", "y.liu"], "scope": "directory"},
      {"type": "network_isolate", "targets": ["VPN-GW-01", "JUMP-01"], "scope": "segment"},
      {"type": "credential_rotation", "targets": ["all_contractor_vpn_accounts"], "scope": "directory"}
    ],
    "approved_by": "ZENITH",
    "approval_time": "2025-08-15T10:55:00Z"
  }' | jq
```

```json
{
  "containment_id": "0194c503-cn01-7000-8000-000000000001",
  "status": "completed",
  "actions_completed": 5,
  "actions_failed": 0,
  "execution_time_secs": 34,
  "rollback_available": true
}
```

### 13:00 UTC -- Evidence Packaging for NATO CERT

This was the critical step. We needed to share our intelligence with NATO CERT while maintaining evidence integrity. Clara drafted the sharing package -- she had a gift for writing intelligence summaries that were precise enough for technical audiences but clear enough for flag officers.

```bash
# Generate Mesh intelligence package for NATO CERT
curl -s -X POST http://localhost:3000/api/v1/collaboration/share \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "package_name": "ORBITAL-SHADOW-NATO-SHARE-001",
    "classification": "NATO RESTRICTED",
    "tlp": "amber",
    "recipients": ["NATO-CERT", "CERT-EU", "ANSSI", "BSI"],
    "content": {
      "incident_summary": "Chinese APT (Volt Typhoon evolution) targeting European satellite ground stations via compromised contractor credentials and LOTL techniques.",
      "iocs": {
        "ip_addresses": ["103.224.182.47", "103.224.182.48", "103.224.182.49", "103.224.182.50"],
        "domains": ["update-service.fortinet-cdn.net", "telemetry.esoc-patch.net", "patch-service.esa-update.org"],
        "file_hashes": ["a3f2c891d7e4b0056f8912ab34cd5678ef901234567890abcdef1234567890ab"],
        "ttps": ["T1190", "T1059.001", "T1071.001", "T1078", "T1021.004", "T1055.001"]
      },
      "evidence_references": ["EV-2025-0091-001", "EV-2025-0091-002", "EV-2025-0091-003"],
      "confidence": 0.91,
      "attribution": "Volt Typhoon (MSS-linked) -- HIGH confidence",
      "analyst_notes": "PRISM-6 assessment: Attacker pre-positioned for potential sabotage activation during geopolitical crisis. Recommend all European satellite operators conduct immediate review of contractor access to ground station infrastructure."
    },
    "evidence_hashes": {
      "package_blake3": "d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2b3c4d5e6f7a8b9c0d1",
      "package_sha256": "e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2b3c4d5e6f7a8b9c0d1e2"
    }
  }' | jq
```

```json
{
  "share_id": "0194c504-sh01-7000-8000-000000000001",
  "package_name": "ORBITAL-SHADOW-NATO-SHARE-001",
  "status": "shared",
  "recipients_notified": 4,
  "evidence_integrity": "verified",
  "shared_at": "2025-08-15T13:00:00Z"
}
```

### 15:00 UTC -- PROVE Phase: Executive Briefing

```bash
# Generate executive briefing
curl -s -X POST http://localhost:3000/api/v1/executive/reports/generate \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "report_type": "incident_executive_briefing",
    "incident_id": "0194c102-aa01-7000-8000-000000000001",
    "audience": "c_suite_and_board",
    "classification": "RESTRICTED",
    "sections": [
      "executive_summary",
      "threat_assessment",
      "impact_analysis",
      "response_timeline",
      "evidence_summary",
      "recommendations",
      "confidence_scores"
    ]
  }' | jq
```

```json
{
  "report_id": "0194c505-rp01-7000-8000-000000000001",
  "title": "Executive Briefing: Operation ORBITAL SHADOW",
  "generated_at": "2025-08-15T15:00:00Z",
  "sections": {
    "executive_summary": "A Chinese state-sponsored threat actor (Volt Typhoon) compromised 4 contractor accounts at subcontractor SatLink Systems GmbH to gain access to ESOC-PRIME satellite ground station infrastructure. The campaign was detected on Day 1 via STIX feed IOC matching, investigated over Days 2-4 using OSINT, geofence monitoring, and UEBA, and fully contained on Day 5. No satellite operations were disrupted. Evidence has been shared with NATO CERT. Key contributor: Analyst PRISM-6 identified injection point and predicted scope of contractor compromise.",
    "confidence_scores": {
      "attribution": {"score": 0.91, "level": "HIGH", "basis": "Genome match 0.78, 4 direct IOC matches, 5 TTP overlaps, infrastructure registration pattern"},
      "impact_assessment": {"score": 0.85, "level": "HIGH", "basis": "Data staging confirmed (3.2 GB), but no evidence of telemetry command injection or orbital parameter modification"},
      "containment_effectiveness": {"score": 0.95, "level": "VERY HIGH", "basis": "All 4 accounts locked, all C2 infrastructure blocked, VPN gateway isolated, credentials rotated"}
    },
    "financial_impact": {
      "estimated_loss_avoided": "EUR 340M (satellite constellation operational continuity)",
      "investigation_cost": "EUR 120K (5-day investigation, 6-person team)",
      "remediation_cost": "EUR 450K (VPN replacement, credential rotation, enhanced monitoring)"
    }
  }
}
```

### 16:00 UTC -- ADAPT PROVE Metrics

```bash
# Record final ADAPT PROVE metrics
curl -s -X POST http://localhost:3000/api/v1/executive/kpis/0194c506-kp01-7000-8000-000000000001/measure \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "measurement_date": "2025-08-15",
    "metrics": {
      "mean_time_to_detect_hours": 48.3,
      "mean_time_to_contain_hours": 94.8,
      "mean_time_to_respond_hours": 120.0,
      "iocs_identified": 9,
      "iocs_from_osint": 3,
      "ttps_mapped": 6,
      "evidence_items_collected": 12,
      "evidence_integrity_verified": true,
      "intel_packages_shared": 1,
      "sharing_recipients": 4,
      "false_positive_rate": 0.0,
      "adapt_cycles_during_investigation": 48,
      "soar_playbooks_executed": 3,
      "soar_auto_containment_time_secs": 12
    }
  }' | jq
```

### 17:00 UTC -- Lessons Learned

```bash
# Record lessons learned
curl -s -X POST http://localhost:3000/api/v1/incident/incidents/0194c102-aa01-7000-8000-000000000001/lessons \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "lesson_type": "operational",
    "lessons": [
      {
        "category": "detection",
        "finding": "STIX feed IOC matching detected the campaign within 48 hours of first access. OSINT enrichment discovered unknown C2 infrastructure on Day 2.",
        "recommendation": "Increase STIX feed polling frequency from 15 minutes to 5 minutes for critical infrastructure feeds.",
        "priority": "high"
      },
      {
        "category": "contractor_management",
        "finding": "All 4 compromised accounts belonged to a single subcontractor. Contractor VPN access lacked MFA and behavioral monitoring.",
        "recommendation": "Mandate MFA for all contractor VPN access. Implement UEBA baselines for all contractor accounts. Require quarterly access reviews.",
        "priority": "critical"
      },
      {
        "category": "analyst_contribution",
        "finding": "Analyst PRISM-6 identified injection point in memory dump before automated tools, predicted 4-account compromise scope from behavioral patterns, and drafted intelligence sharing package.",
        "recommendation": "Recognize analyst intuition as force multiplier for automated detection. Invest in analyst training and retention.",
        "priority": "high"
      },
      {
        "category": "soar_automation",
        "finding": "SOAR auto-containment locked compromised account in 12 seconds, preventing further access to ground station controllers.",
        "recommendation": "Expand SOAR auto-containment playbooks to cover all geofence violation scenarios.",
        "priority": "high"
      },
      {
        "category": "intelligence_sharing",
        "finding": "NATO CERT sharing via Mesh enabled 3 other satellite operators to check their infrastructure against our IOCs within hours.",
        "recommendation": "Establish standing Mesh sharing agreements with all NATO CERT members for satellite infrastructure threats.",
        "priority": "high"
      }
    ]
  }' | jq
```

---

## The Flashback Ends

That was ORBITAL SHADOW. Five days, 22 modules, 12 evidence items, zero satellite disruption.

Two weeks after we closed the case, the DGSE pulled Clara out. She told me she'd been offered a "field assignment" and might be gone for a while. She didn't say where. She didn't say what. She just said: "Keep watching the shared services. That's always where they're visible."

And she left her analysis notebook in the evidence vault. All of it. Every note she'd ever written during our eight months working together. Including notes I'd never seen -- notes on trafficking patterns, financial flows, corrupted officials. Notes that had nothing to do with satellites.

I didn't understand why she'd left them until two months later, when the DGSE contacted me and explained that Clara was under deep cover in Marseille, investigating a trafficking network called PHANTOM MERCY. And the notes she'd left -- they weren't just her intelligence analysis. They were the operational preparation for STARLIGHT.

She'd been building this case the entire time we worked together. The satellite investigation was real. But Clara was also using Playseat to map the infrastructure of something much worse. And she'd left me the map.

---

## SQL Reference: Key Queries Used During Investigation

### Query 1: Contractor Account Activity Audit

```sql
SELECT
    u.username,
    u.email,
    s.source_ip,
    s.destination_ip,
    s.destination_port,
    s.bytes_sent + s.bytes_received AS total_bytes,
    s.created_at
FROM stream_events s
JOIN users u ON u.id = s.user_id
WHERE u.email LIKE '%@subcontractor-sat.synth.com'
  AND s.created_at >= '2025-08-09T00:00:00Z'
ORDER BY s.created_at;
```

### Query 2: IOC Hit Timeline

```sql
SELECT
    i.value AS ioc_value,
    i.ioc_type,
    i.source,
    i.confidence,
    m.matched_asset,
    m.match_type,
    m.first_seen,
    m.last_seen
FROM ioc_indicators i
JOIN ioc_matches m ON m.ioc_id = i.id
WHERE i.tags @> ARRAY['volt-typhoon']
ORDER BY m.first_seen;
```

### Query 3: UEBA Anomaly Summary

```sql
SELECT
    b.entity_name,
    b.anomaly_type,
    b.severity,
    b.deviation_score,
    b.baseline_deviation,
    b.detected_at
FROM behavioral_anomalies b
WHERE b.severity IN ('critical', 'high')
  AND b.detected_at >= '2025-08-11T00:00:00Z'
  AND b.entity_name LIKE '%subcontractor-sat%'
ORDER BY b.deviation_score DESC;
```

### Query 4: Evidence Chain of Custody Audit

```sql
SELECT
    e.evidence_number,
    e.title,
    e.hash_blake3,
    e.hash_sha256,
    c.action,
    c.performed_by,
    c.performed_at,
    c.notes
FROM evidence e
JOIN evidence_custody_chain c ON c.evidence_id = e.id
WHERE e.case_id = '0194c501-fc01-7000-8000-000000000001'
ORDER BY c.performed_at;
```

---

## Summary: The Five-Day Investigation

| Day | Phase | Key Action | Module Used |
|-----|-------|------------|-------------|
| 1 (Mon) | DISCOVER + CORRELATE | STIX feed IOC match, risk score 94.7 | Feed Aggregator, IOC Manager, ADAPT |
| 2 (Tue) | Intelligence Gathering | OSINT discovers 7-domain C2 infrastructure (Clara's nameserver insight) | OSINT, Ontology, AI |
| 3 (Wed) | Containment Trigger | Geofence alerts, SOAR auto-containment in 12 secs | Geotrack, SOAR, Zero Trust |
| 4 (Thu) | Behavioral Analysis | UEBA detects data staging + privilege escalation (Clara predicted 4 accounts) | Behavioral, Insider Threat |
| 5 (Fri) | VALIDATE + FORTIFY + PROVE | Clara finds injection point, evidence packaging, NATO sharing, briefing | Forensics, Evidence, Mesh, Executive |

**Total modules used**: 22 out of 25+
**Detection to containment**: 54 hours
**SOAR auto-containment**: 12 seconds
**Intelligence shared with**: 4 NATO partners
**Satellite operations disrupted**: Zero
**Evidence items collected**: 12 (all dual-hashed, chain of custody verified)
**Attribution confidence**: 0.91 (HIGH)

---

## Application to STARLIGHT

Sitting here at T-minus 8 hours and counting, I'm applying everything ORBITAL SHADOW taught me:

1. **Shared services are the blind spot.** Volt Typhoon used shared nameservers. PHANTOM MERCY uses shared financial infrastructure. Find the shared service, map the network.

2. **Contractor credentials are the bridge.** Between IT and OT in satellites. Between legitimate institutions and criminal networks in trafficking. The person who moves between worlds is always the vector.

3. **The APT that hides inside critical infrastructure always has a blind spot.** ORBITAL SHADOW taught me that. It's the same blind spot PHANTOM MERCY has. They need infrastructure they don't fully control. They need people they can't fully trust. And those dependencies are visible if you know how to look.

4. **Clara's notes are the map.** She left them in the evidence vault for a reason. Not because she was sentimental. Because she knew that one day I'd need them to find her.

The ADAPT cycle is running. The STARLIGHT clock is ticking. And Clara's notebook is open on my desk.

---

*This scenario demonstrates the full ADAPT cycle applied to a nation-state campaign against critical satellite infrastructure. Every API call, SQL query, and JSON response in this chapter is based on actual Playseat platform endpoints and data structures. The threat actor, target organization, and all personnel are synthetic. Clara's notes remain in the evidence vault.*

---

(c) 2026 Playseat -- All Rights Reserved | Defensive Intelligence Through ADAPT
