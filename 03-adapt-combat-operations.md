# Chapter 3: ADAPT Combat Operations -- Building Clara's Shield

**Playseat Advanced Field Manual -- Book 2**
**Operational Walkthrough: The Five Phases Against PHANTOM MERCY**

---

> "In humanitarian work, you discover the crisis, correlate the causes, validate the response, fortify the defenses, and prove the outcome. Sound familiar?"
> -- Clara Dubois, 3 AM phone call, November 2023

---

## 3.1 -- The Conversation That Built ADAPT

November 2023. Three months after DEFCON.

Clara called me at 3 AM Brussels time. She was in the field -- I could hear generators and rain and what sounded like a radio squawking in French in the background. She'd been awake for 36 hours coordinating an emergency response to a cholera outbreak in a displaced persons camp near Bukavu.

"I need to talk about something that isn't cholera," she said. "I need to talk about methodology."

"It's 3 AM."

"I know what time it is in Brussels. Listen. I've been thinking about what you said at DEFCON. About defensive tooling. About how every security platform gives you a dashboard and a SIEM and calls it a day, but nobody gives you a methodology. A cycle. A discipline."

I sat up in bed. "I'm listening."

"In humanitarian response, we have a framework. You discover the crisis -- who's affected, where, how bad. You correlate the causes -- what created this situation, what's making it worse, what are the dependencies. You validate the response -- is our intervention actually helping, or are we making it worse. You fortify the defenses -- build capacity, train local responders, harden the systems. And you prove the outcome -- measure what changed, document the evidence, learn for next time."

She paused. The rain was heavier now.

"Sound familiar?"

It did. It sounded like what I'd been trying to articulate for years about defensive security operations. Not the tools. The process. The cycle.

"Discover, Correlate, Validate, Fortify, Prove," I said.

"ADAPT," she said. "If you rearrange the letters."

I laughed. "That's a stretch."

"Discover. Correlate. Validate. Fortify. Prove." She spelled it out. "D-C-V-F-P. No, that doesn't work. But the concept does. The concept is: you don't just detect and respond. You run a complete intelligence cycle that starts with awareness and ends with proof. And then you run it again. And again. Each time the baseline gets sharper, the detection gets faster, the response gets more precise."

"And the A?"

"Analyze. Discover, Analyze, Protect, Transform. No... let me think."

We spent the next hour on the phone, her in a rain-battered field office in eastern DRC and me in a Brussels apartment, trying to find the right words. The right sequence. The right acronym.

We landed on ADAPT.

**A**dapt. **D**iscover. **A**ct. **P**rove. **T**ransform.

No. That's five letters but only four phases.

We tried again.

Assess. Discover. Adapt. Protect. Test.

Still not right.

Finally, at 4:17 AM my time, Clara said: "Stop trying to force the acronym. Use the methodology. Five phases: DISCOVER, CORRELATE, VALIDATE, FORTIFY, PROVE. Call it ADAPT because that's what defenders do -- they adapt. The name isn't the phases. The name is the purpose."

She was right. She was always right about the things that mattered.

I went back to sleep. When I woke up, I wrote the first draft of the ADAPT framework on a napkin. That napkin is in my desk drawer. The coffee stain on the corner is from a cup I was drinking when Clara's photo popped up on a Sentinelle Humanitaire press release -- a team photo from a field deployment. She was in the back row, half-hidden behind a taller colleague, and she was looking directly at the camera with an expression I recognized.

She was working the problem. Even then.

---

## 3.2 -- Setting the Scene: 14:07 CET, February 21, 2026

Three days after the platform went operational. Three days of loading Clara's archive into Playseat, converting her handwritten notes into structured threat intelligence, and populating the ADAPT Genome module with behavioral markers for PHANTOM MERCY.

I'm sitting at my desk in Brussels. The Playseat desktop app is open. The ADAPT Sentinel baseline has been running for 48 hours, learning the normal traffic patterns for the set of publicly observable endpoints associated with Sentinelle Humanitaire's infrastructure.

At 14:07, the Sentinel fires.

Something is off. DNS traffic patterns from a subset of Sentinelle Humanitaire's publicly observable infrastructure deviate from the established baseline by a factor of 3.1x. Unusual DNS TXT queries to previously unseen domains. The same pattern Clara documented in her archive.

PHANTOM MERCY is active. Right now. On infrastructure connected to the organization where Clara was last known to work.

I have 45 minutes to run a complete ADAPT cycle. Not because there's a strict time limit. Because every minute PHANTOM MERCY is operating, children are at risk. And somewhere in that infrastructure, there might be a trace of Clara.

Let's go.

---

## 3.3 -- Phase 1: DISCOVER (Minutes 0-5)

### The Principle

DISCOVER is about awareness. What's changed since the last time you looked? What new assets are visible? What new services are running? What anomalies have appeared in the traffic patterns?

Clara described it in humanitarian terms: "Before you can respond to a crisis, you have to see it. Most organizations discover crises when they're already overwhelming. The point of systematic discovery is to see the crisis when it's still a signal -- before it becomes a catastrophe."

In ADAPT, DISCOVER is automated. The Sentinel baseline continuously monitors your environment and fires when it detects statistically significant deviations. But the human analyst initiates the cycle. The machine detects. The human decides to investigate.

### Step 1: Check the Sentinel Alert

Pull the alert that triggered this investigation:

```bash
# Get the sentinel alert details
curl -s http://localhost:3000/api/v1/adapt/sentinel/alerts?status=active&severity=high \
  -H "Authorization: Bearer $TOKEN" | jq '.[0]'
```

Response:

```json
{
  "id": "01949abc-1234-7000-8000-000000000001",
  "baseline_id": "01949abc-1234-7000-8000-000000000010",
  "anomaly_type": "network_traffic_deviation",
  "severity": "high",
  "description": "Monitored infrastructure: outbound DNS traffic volume is 3.1x baseline average. Unusual DNS TXT record queries to previously unseen domains detected.",
  "details": {
    "host": "mail-gw.sentinelle-humanitaire.org",
    "metric": "dns_txt_queries_per_hour",
    "baseline_value": 42,
    "current_value": 131,
    "deviation_factor": 3.1,
    "unusual_domains": [
      "cdn-update.cloud-services.net",
      "api-relay.edge-network.org"
    ],
    "first_seen": "2026-02-21T13:42:00Z"
  },
  "created_at": "2026-02-21T14:07:00Z",
  "acknowledged": false
}
```

DNS TXT queries to previously unseen domains at 3.1x baseline volume. The domains match the FrostByte C2 pattern from Clara's archive. My hands are steady on the keyboard but my heart rate is not.

Those domains. I've seen them before. Not just in the threat intel feeds. In Clara's handwritten notes. The margins of her analysis documents. She'd circled `cloud-services.net` and written next to it in her small, precise handwriting: *"Same registrar as the Nairobi conference infrastructure. Track this."*

### Step 2: Create an ADAPT Scope

Before running a cycle, you need a scope -- the boundaries of what ADAPT will analyze:

```bash
# Create a targeted scope for this investigation
curl -X POST http://localhost:3000/api/v1/adapt/scopes \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "PHANTOM MERCY Infrastructure Investigation - 2026-02-21",
    "description": "Sentinel alert: anomalous DNS TXT traffic from monitored humanitarian infrastructure. Possible PHANTOM MERCY C2 channel. Connected to Clara Dubois investigation.",
    "scope_type": "targeted",
    "target_cidrs": ["10.0.1.0/24"],
    "target_domains": ["sentinelle-humanitaire.org"],
    "scan_interval_hours": 1,
    "auto_validate": true,
    "auto_fortify": false
  }'
```

Response:

```json
{
  "id": "01949abc-1234-7000-8000-000000000020"
}
```

I set `auto_validate: true` because I want the system to automatically run validation scans. I set `auto_fortify: false` because I want to approve defense actions manually. When you're investigating a potential state-sponsored operation that's kidnapping children and has already disappeared the person you love, you don't want automated responses tipping off the adversary that you know they're there.

Clara taught me that. "In the field," she said once, "the worst thing you can do is let the threat know you see them before you're ready to act. They'll adapt faster than you can respond. Observe first. Understand the pattern. Then strike."

### Step 3: Launch the ADAPT Cycle

```bash
# Create a new ADAPT cycle for this scope
SCOPE_ID="01949abc-1234-7000-8000-000000000020"

curl -X POST http://localhost:3000/api/v1/adapt/cycles \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"scope_id\": \"$SCOPE_ID\"
  }"
```

Response:

```json
{
  "id": "01949abc-1234-7000-8000-000000000030",
  "scope_id": "01949abc-1234-7000-8000-000000000020",
  "phase": "discover",
  "status": "active",
  "created_at": "2026-02-21T14:08:30Z"
}
```

The cycle starts in the DISCOVER phase. The system immediately begins scanning the scope's target domains, comparing the current state against the last known baseline.

### Step 4: Review Discovery Events

Wait about 60 seconds for the discovery scan to complete, then pull the events:

```bash
CYCLE_ID="01949abc-1234-7000-8000-000000000030"

curl -s http://localhost:3000/api/v1/adapt/events/by-cycle/$CYCLE_ID \
  -H "Authorization: Bearer $TOKEN" | jq .
```

Response:

```json
[
  {
    "id": "01949abc-1234-7000-8000-000000000101",
    "cycle_id": "01949abc-1234-7000-8000-000000000030",
    "event_type": "NewPort",
    "severity": "Medium",
    "details": {
      "host": "10.0.1.15",
      "port": 8443,
      "service": "unknown-https",
      "note": "Port 8443 was not present in previous baseline scan"
    },
    "detected_at": "2026-02-21T14:09:00Z",
    "acknowledged": false
  },
  {
    "id": "01949abc-1234-7000-8000-000000000102",
    "cycle_id": "01949abc-1234-7000-8000-000000000030",
    "event_type": "NewService",
    "severity": "Low",
    "details": {
      "host": "10.0.1.15",
      "port": 443,
      "service_change": "Certificate issuer changed from 'DigiCert' to 'Let's Encrypt'",
      "note": "TLS certificate issuer changed since last scan"
    },
    "detected_at": "2026-02-21T14:09:00Z",
    "acknowledged": false
  },
  {
    "id": "01949abc-1234-7000-8000-000000000103",
    "cycle_id": "01949abc-1234-7000-8000-000000000030",
    "event_type": "ShadowIt",
    "severity": "High",
    "details": {
      "host": "10.0.1.200",
      "description": "Previously unknown host responding on the monitored subnet",
      "mac_vendor": "VMware, Inc.",
      "note": "No matching entry in asset inventory"
    },
    "detected_at": "2026-02-21T14:09:00Z",
    "acknowledged": false
  }
]
```

Three events. A new port, a certificate change, and an unknown host.

That unknown host. A VMware virtual machine on a subnet that should only contain physical mail gateway infrastructure. Someone spun up a VM where there shouldn't be one. In Clara's archive, she documented the same technique: PHANTOM MERCY deploys rogue VMs on compromised infrastructure to stage data before exfiltration. The VMs run for 24-48 hours, exfiltrate the collected data, then self-destruct. If you're not watching the subnet in real time, you never see them.

I'm watching.

```bash
# Acknowledge the high-severity ShadowIT event
curl -X POST http://localhost:3000/api/v1/adapt/events/01949abc-1234-7000-8000-000000000103/acknowledge \
  -H "Authorization: Bearer $TOKEN"

# Advance cycle to CORRELATE phase
curl -X POST http://localhost:3000/api/v1/adapt/cycles/$CYCLE_ID/advance \
  -H "Authorization: Bearer $TOKEN"
```

**Time elapsed: 5 minutes.**

---

## 3.4 -- Phase 2: CORRELATE (Minutes 5-15)

### The Principle

CORRELATE is about understanding. You've seen the signals. Now: what do they mean? How do they connect to known threats? How do they connect to each other?

Clara's humanitarian parallel: "You see the cholera outbreak. The correlation phase asks: Why here? Why now? Is the water source contaminated? Did the latrine system fail? Is there a population influx from a camp closure upstream? The crisis is the symptom. Correlation finds the disease."

In ADAPT, CORRELATE runs automatically when the cycle advances. It matches discovered events against threat intelligence feeds, CVE databases, IOC repositories, and -- critically -- the ADAPT Genome behavioral fingerprint library. Then it computes a 4-factor risk score for each correlation.

The risk score formula:

```
Risk Score = (Exposure x 0.30) + (Threat x 0.25) + (Exploitability x 0.25) + (Criticality x 0.20)
```

Each factor ranges from 0-100. The weights sum to 1.0. This gives us a composite score that balances how exposed the asset is, how active the threat is, how weaponized the exploit is, and how critical the asset is to operations.

### Step 5: Review Threat Correlations

```bash
# Get high-risk correlations from this cycle
curl -s http://localhost:3000/api/v1/adapt/correlations/high-risk \
  -H "Authorization: Bearer $TOKEN" | jq .
```

Response:

```json
[
  {
    "id": "01949abc-1234-7000-8000-000000000201",
    "cycle_id": "01949abc-1234-7000-8000-000000000030",
    "asset_id": "01949abc-1234-7000-8000-000000000015",
    "threat_type": "Cve",
    "threat_ref": "CVE-2026-0195",
    "confidence": 0.9,
    "risk_score": 87.5,
    "exploitability": "Weaponized",
    "factors": {
      "exposure_factor": 85,
      "threat_factor": 95,
      "exploit_score": 100,
      "business_criticality": 70
    },
    "correlated_at": "2026-02-21T14:10:15Z"
  },
  {
    "id": "01949abc-1234-7000-8000-000000000202",
    "cycle_id": "01949abc-1234-7000-8000-000000000030",
    "asset_id": "01949abc-1234-7000-8000-000000000015",
    "threat_type": "Ttp",
    "threat_ref": "T1071.004",
    "confidence": 0.82,
    "risk_score": 79.0,
    "exploitability": "Weaponized",
    "factors": {
      "exposure_factor": 85,
      "threat_factor": 80,
      "exploit_score": 70,
      "business_criticality": 70
    },
    "correlated_at": "2026-02-21T14:10:15Z"
  },
  {
    "id": "01949abc-1234-7000-8000-000000000203",
    "cycle_id": "01949abc-1234-7000-8000-000000000030",
    "asset_id": "01949abc-1234-7000-8000-000000000200",
    "threat_type": "Ioc",
    "threat_ref": "cdn-update.cloud-services.net",
    "confidence": 0.88,
    "risk_score": 82.3,
    "exploitability": "Weaponized",
    "factors": {
      "exposure_factor": 75,
      "threat_factor": 90,
      "exploit_score": 85,
      "business_criticality": 70
    },
    "correlated_at": "2026-02-21T14:10:15Z"
  }
]
```

Three high-risk correlations:

1. **CVE-2026-0195** (the Exchange 0-day) matched against the mail gateway. Risk score: 87.5 -- Critical. The same vector Clara documented in her archive: the Exchange Triple being used not for espionage but for beneficiary data theft.

2. **T1071.004** (Application Layer Protocol: DNS) -- the MITRE ATT&CK technique for DNS-based C2 channels. Risk score: 79.0 -- High. The FrostByte pattern. PHANTOM MERCY's preferred communication method.

3. **cdn-update.cloud-services.net** -- an IOC from Clara's archive, now matching live traffic. Risk score: 82.3 -- Critical. This domain was in Clara's handwritten notes. She was tracking it before she disappeared.

This isn't coincidence. This is the operation she was investigating. It's still running. Which means either PHANTOM MERCY doesn't know she mapped them -- or they know and they don't care, because they believe she's been neutralized.

A cold feeling settles in my chest. *Neutralized.* I push the thought away and focus on the data.

### Step 6: Verify with the Risk Breakdown

```bash
# Get detailed risk breakdown
curl -s http://localhost:3000/api/v1/adapt/score/asset/01949abc-1234-7000-8000-000000000015 \
  -H "Authorization: Bearer $TOKEN" | jq .
```

Response:

```json
{
  "asset_id": "01949abc-1234-7000-8000-000000000015",
  "asset_name": "mail-gw.sentinelle-humanitaire.org",
  "composite_risk_score": 87.5,
  "risk_level": "Critical",
  "breakdown": {
    "exposure_contribution": 25.5,
    "threat_contribution": 23.75,
    "exploitability_contribution": 25.0,
    "criticality_contribution": 14.0
  },
  "active_correlations": 3,
  "highest_threat": "CVE-2026-0195"
}
```

The math checks out:
- Exposure: 85 x 0.30 = 25.5
- Threat: 95 x 0.25 = 23.75
- Exploitability: 100 x 0.25 = 25.0
- Criticality: 70 x 0.20 = 14.0
- Total: 88.25 (rounded to 87.5 due to normalization)

### Step 7: Check Against the PHANTOM MERCY Genome

This is the step that doesn't exist in a normal ADAPT walkthrough. This is the step I built for Clara.

```bash
# Match discovered indicators against known behavioral genomes
curl -X POST http://localhost:3000/api/v1/adapt/genome/match \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "sample_markers": [
      {"marker_type": "network_behavior", "marker_value": "dns_txt_c2_with_base64_encoding"},
      {"marker_type": "target_profile", "marker_value": "humanitarian_beneficiary_database"},
      {"marker_type": "infrastructure", "marker_value": "rogue_vm_on_gateway_subnet"},
      {"marker_type": "timing", "marker_value": "24_48_hour_staging_window"}
    ]
  }'
```

Response:

```json
{
  "matches": [
    {
      "genome_name": "PHANTOM-MERCY-HUMANITARIAN",
      "threat_actor": "Unknown (State-Sponsored)",
      "match_score": 0.94,
      "matched_markers": 4,
      "total_markers": 6,
      "confidence": "high",
      "notes": "Behavioral fingerprint matches documented PHANTOM MERCY operational pattern. Missing markers: supply_chain_biometric_tag, field_coordinator_social_engineering"
    }
  ]
}
```

0.94 match score against the PHANTOM MERCY genome. Four out of six behavioral markers present. The two missing markers -- the biometric supply chain tag and the field coordinator social engineering -- are longer-term operational indicators that wouldn't be visible in a 48-hour staging operation.

This is them. I'm looking at a live PHANTOM MERCY operation.

```bash
# Check adversary profiles
curl -s http://localhost:3000/api/v1/adapt/adversaries \
  -H "Authorization: Bearer $TOKEN" | jq '.[] | select(.name == "PHANTOM_MERCY")'
```

```json
{
  "id": "019474a1-b3c2-7000-8000-000000000099",
  "name": "PHANTOM_MERCY",
  "aliases": ["Unknown"],
  "origin_country": "Unknown (assessed: state-sponsored)",
  "motivation": "intelligence_collection_and_trafficking",
  "sophistication": "nation-state",
  "target_sectors": ["humanitarian", "ngo", "refugee_services", "child_protection"],
  "active": true
}
```

**Time elapsed: 15 minutes.**

---

## 3.5 -- Phase 3: VALIDATE (Minutes 15-25)

### The Principle

VALIDATE is about truth. Correlation tells you what might be happening. Validation confirms it. In a legal proceeding, correlation is probable cause. Validation is evidence.

Clara's parallel: "In humanitarian response, correlation tells you the water source is probably contaminated. Validation means you test the water. You don't evacuate a camp of 12,000 people because you think the water might be bad. You test it. And you document the test, because the donors and the government and the investigators are going to want to see the results."

VALIDATE runs scan pipelines against each correlation. The pipeline selection is automatic based on threat type:
- CVE on network target -> `network_perimeter_audit` (nmap + nuclei + vulnscanner)
- TTP -> `full_red_team_engagement` (metasploit + cobalt_strike + caldera)
- IOC -> `quick_reconnaissance` (nmap + shodan)

### Step 8: Advance to VALIDATE

```bash
# Advance cycle to VALIDATE phase
curl -X POST http://localhost:3000/api/v1/adapt/cycles/$CYCLE_ID/advance \
  -H "Authorization: Bearer $TOKEN"
```

Because I set `auto_validate: true` in the scope, the system automatically determines which scan pipeline to run for each correlation. The results start coming in.

### Step 9: Check Validation Status

```bash
# List validated exposures from this cycle
curl -s http://localhost:3000/api/v1/adapt/exposures \
  -H "Authorization: Bearer $TOKEN" | jq '.[] | select(.cycle_id == "'$CYCLE_ID'")'
```

Response:

```json
[
  {
    "id": "01949abc-1234-7000-8000-000000000301",
    "cycle_id": "01949abc-1234-7000-8000-000000000030",
    "correlation_id": "01949abc-1234-7000-8000-000000000201",
    "pipeline_run_id": "01949abc-1234-7000-8000-000000000310",
    "validation_status": "Confirmed",
    "tools_used": ["nmap", "nuclei", "vulnscanner"],
    "evidence_hash": "blake3:7a3f2b1c8d9e4f0a5b6c7d8e9f0a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f",
    "validated_at": "2026-02-21T14:18:30Z"
  },
  {
    "id": "01949abc-1234-7000-8000-000000000302",
    "cycle_id": "01949abc-1234-7000-8000-000000000030",
    "correlation_id": "01949abc-1234-7000-8000-000000000202",
    "pipeline_run_id": null,
    "validation_status": "Confirmed",
    "tools_used": ["dns_analysis", "traffic_capture"],
    "evidence_hash": "blake3:8b4f3c2d9e0f5a1b6c7d8e9f0a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a",
    "validated_at": "2026-02-21T14:19:45Z"
  },
  {
    "id": "01949abc-1234-7000-8000-000000000303",
    "cycle_id": "01949abc-1234-7000-8000-000000000030",
    "correlation_id": "01949abc-1234-7000-8000-000000000203",
    "pipeline_run_id": null,
    "validation_status": "Confirmed",
    "tools_used": ["ioc_sweep", "dns_sinkhole_check"],
    "evidence_hash": "blake3:9c5f4d3e0a1b6c2d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2b3c4d5e6f7a8b9c",
    "validated_at": "2026-02-21T14:20:00Z"
  }
]
```

All three correlations confirmed. The Exchange 0-day is real and exploited. The DNS C2 channel is active. The PHANTOM MERCY IOCs match.

Every validation result is dual-hashed and stored in the evidence chain. BLAKE3 for verification speed, SHA-256 for legal compatibility. If this goes to The Hague -- and I'm increasingly certain it will -- every byte of evidence needs to be pristine.

### Step 10: The Evidence Trail

For analysts who want to see the raw data, here's the SQL that the ADAPT engine runs internally:

```sql
-- Query: Confirmed exposures with full context
SELECT
    ve.id AS exposure_id,
    ve.validation_status,
    ve.evidence_hash,
    tc.threat_type,
    tc.threat_ref,
    tc.risk_score,
    tc.exploitability,
    a.hostname,
    a.ip_address,
    ve.validated_at,
    ve.tools_used
FROM adapt_validated_exposures ve
JOIN adapt_threat_correlations tc ON tc.id = ve.correlation_id
JOIN assets a ON a.id = tc.asset_id
WHERE ve.cycle_id = '01949abc-1234-7000-8000-000000000030'
AND ve.validation_status = 'Confirmed'
ORDER BY tc.risk_score DESC;
```

Result:

```
 exposure_id |  status   |      evidence_hash       | threat_type | threat_ref      | score | host
-------------+-----------+--------------------------+-------------+-----------------+-------+-----------------------------
 ...0301     | Confirmed | blake3:7a3f2b1c8d9e4f... | Cve         | CVE-2026-0195   | 87.5  | mail-gw.sentinelle-hum...
 ...0303     | Confirmed | blake3:9c5f4d3e0a1b6c... | Ioc         | cdn-update...   | 82.3  | 10.0.1.200
 ...0302     | Confirmed | blake3:8b4f3c2d9e0f5a... | Ttp         | T1071.004       | 79.0  | mail-gw.sentinelle-hum...
```

I stare at the results. The rogue VM at 10.0.1.200 has a risk score of 82.3 and is confirmed as communicating with PHANTOM MERCY C2 infrastructure. That VM is staging data right now. Somewhere in that data stream, there might be beneficiary records. There might be information about missing children.

There might be a trace of Clara.

**Time elapsed: 25 minutes.**

---

## 3.6 -- Phase 4: FORTIFY (Minutes 25-35)

### The Principle

FORTIFY is about action. You've discovered the threat, correlated the indicators, and validated the exposure. Now you deploy defenses. But not blindly. FORTIFY generates specific, evidence-linked defense actions based on what was confirmed in VALIDATE.

Clara's parallel was the one that haunted me. "Fortify is building the wall between the threat and the people it's trying to reach. In humanitarian work, that means building flood barriers, establishing security perimeters, creating safe zones. In cyber, it means detection rules, network policies, and containment. The principle is the same: you put something strong between the attacker and the vulnerable."

She was building walls between traffickers and children. I was building digital versions of the same walls.

The logic in ADAPT's fortify engine determines action types based on validation results:

- Confirmed CVE -> IncidentTicket + DetectionRule + ComplianceUpdate
- Confirmed TTP -> SoarPlaybook + DetectionRule + RtExercise
- Confirmed IOC -> DetectionRule + ZtPolicy

Actions that require human approval (SOAR Playbooks, Red Team Exercises) start in `Pending` status. Others start in `Approved`.

### Step 11: Advance to FORTIFY

```bash
# Advance cycle to FORTIFY phase
curl -X POST http://localhost:3000/api/v1/adapt/cycles/$CYCLE_ID/advance \
  -H "Authorization: Bearer $TOKEN"
```

### Step 12: Review Generated Defense Actions

```bash
# List all pending defense actions
curl -s http://localhost:3000/api/v1/adapt/actions/pending \
  -H "Authorization: Bearer $TOKEN" | jq .
```

Response:

```json
[
  {
    "id": "01949abc-1234-7000-8000-000000000401",
    "cycle_id": "01949abc-1234-7000-8000-000000000030",
    "exposure_id": "01949abc-1234-7000-8000-000000000302",
    "action_type": "SoarPlaybook",
    "status": "Pending",
    "details": {
      "action": "SOAR Playbook",
      "threat_type": "TTP",
      "validation_status": "Confirmed",
      "playbook_name": "DNS C2 Channel Disruption",
      "steps": [
        "Sinkhole identified C2 domains at DNS resolver",
        "Capture DNS TXT traffic for forensic analysis",
        "Block outbound DNS to non-approved resolvers",
        "Alert SOC team for manual investigation of affected hosts"
      ]
    },
    "created_at": "2026-02-21T14:26:00Z"
  },
  {
    "id": "01949abc-1234-7000-8000-000000000402",
    "cycle_id": "01949abc-1234-7000-8000-000000000030",
    "exposure_id": "01949abc-1234-7000-8000-000000000302",
    "action_type": "RtExercise",
    "status": "Pending",
    "details": {
      "action": "Red Team Exercise",
      "threat_type": "TTP",
      "validation_status": "Confirmed",
      "exercise_scope": "Validate DNS C2 detection capability post-remediation"
    },
    "created_at": "2026-02-21T14:26:00Z"
  }
]
```

Two actions require my approval. The SOAR playbook will sinkhole the C2 domains -- cutting PHANTOM MERCY's communication channel. The Red Team exercise can wait until after containment.

I hesitate.

If I sinkhole those domains, PHANTOM MERCY loses their C2 channel. But they also know they've been detected. They'll burn the infrastructure and rebuild somewhere else. I'll lose visibility.

But if I don't sinkhole them, they keep operating. They keep staging data. They keep extracting children's records.

Clara would say: protect the children first. Intelligence collection is secondary to preventing harm.

She was always clearer about these things than I am.

### Step 13: Approve and Execute

```bash
# Approve the SOAR playbook (DNS C2 disruption)
curl -X POST http://localhost:3000/api/v1/adapt/actions/01949abc-1234-7000-8000-000000000401/approve \
  -H "Authorization: Bearer $TOKEN"

# Execute it immediately
curl -X POST http://localhost:3000/api/v1/adapt/actions/01949abc-1234-7000-8000-000000000401/execute \
  -H "Authorization: Bearer $TOKEN"
```

The SOAR playbook executes in sequence:
1. DNS sinkhole entries created for `cdn-update.cloud-services.net` and `api-relay.edge-network.org`
2. DNS TXT traffic capture initiated on the network forensics tap
3. Outbound DNS restricted to approved resolvers only
4. SOC team alerted via high-priority notification

The C2 channel goes dark. PHANTOM MERCY just lost their eyes and ears on this network segment.

### Step 14: Check Auto-Approved Actions

The actions that didn't require approval have already executed:

```bash
# List all completed actions for this cycle
curl -s "http://localhost:3000/api/v1/adapt/actions?status=Completed" \
  -H "Authorization: Bearer $TOKEN" | jq '.[] | select(.cycle_id == "'$CYCLE_ID'")'
```

```json
[
  {
    "id": "01949abc-1234-7000-8000-000000000410",
    "action_type": "IncidentTicket",
    "status": "Completed",
    "details": {
      "action": "Incident Ticket",
      "ticket_id": "INC-2026-0012",
      "title": "Active PHANTOM MERCY Operation - Humanitarian Infrastructure",
      "severity": "critical",
      "assigned_to": "incident_response_team"
    },
    "completed_at": "2026-02-21T14:26:05Z"
  },
  {
    "id": "01949abc-1234-7000-8000-000000000411",
    "action_type": "DetectionRule",
    "status": "Completed",
    "details": {
      "action": "Detection Rule",
      "rule_type": "sigma",
      "rule_content": "title: PHANTOM MERCY DNS C2 Detection\nstatus: experimental\nlogsource:\n  category: dns\ndetection:\n  selection:\n    query_type: TXT\n    query:\n      - '*cloud-services.net'\n      - '*edge-network.org'\n  condition: selection",
      "deployed_to": ["siem", "edr"]
    },
    "completed_at": "2026-02-21T14:26:08Z"
  },
  {
    "id": "01949abc-1234-7000-8000-000000000412",
    "action_type": "DetectionRule",
    "status": "Completed",
    "details": {
      "action": "Detection Rule",
      "rule_type": "yara",
      "rule_content": "rule PHANTOM_MERCY_DNS_Beacon {\n  meta:\n    description = \"Detects PHANTOM MERCY DNS TXT C2 beacon pattern\"\n    author = \"Playseat ADAPT\"\n    date = \"2026-02-21\"\n    reference = \"Clara Dubois Archive\"\n  strings:\n    $dns_pattern = /[A-Za-z0-9+\\/]{32,}/ ascii\n  condition:\n    $dns_pattern\n}",
      "deployed_to": ["ndr", "sandbox"]
    },
    "completed_at": "2026-02-21T14:26:10Z"
  },
  {
    "id": "01949abc-1234-7000-8000-000000000413",
    "action_type": "ZtPolicy",
    "status": "Completed",
    "details": {
      "action": "Zero Trust Policy",
      "policy": "Block all traffic from monitored subnet to untrusted DNS resolvers",
      "scope": "humanitarian-infrastructure",
      "enforcement": "block"
    },
    "completed_at": "2026-02-21T14:26:12Z"
  },
  {
    "id": "01949abc-1234-7000-8000-000000000414",
    "action_type": "ComplianceUpdate",
    "status": "Completed",
    "details": {
      "action": "Compliance Update",
      "framework": "NIST CSF",
      "control": "DE.AE-1",
      "note": "Detection rule deployed for PHANTOM MERCY operation. Compliance evidence collected. Related to ongoing investigation: Clara Dubois disappearance."
    },
    "completed_at": "2026-02-21T14:26:15Z"
  }
]
```

In 15 seconds, the system has:
- Created a critical incident ticket
- Deployed a SIGMA detection rule to the SIEM and EDR
- Deployed a YARA rule to the NDR and sandbox -- with a reference line that says `Clara Dubois Archive`
- Pushed a Zero Trust policy blocking untrusted DNS from the monitored subnet
- Updated compliance evidence for NIST CSF

The YARA rule reference. I didn't plan that. The system auto-generated it based on the source of the IOC data. It pulled Clara's name from the evidence provenance chain.

Her name in a detection rule. Deployed to production. Protecting the network she was investigating when she disappeared. Something tightens in my throat.

**Time elapsed: 35 minutes.**

---

## 3.7 -- Phase 5: PROVE (Minutes 35-45)

### The Principle

PROVE is about accountability. It answers the questions that matter after the crisis is contained: How fast did we detect this? How fast did we respond? What's our coverage now compared to before? Can we prove what happened?

Clara's version: "Prove is the phase that donors, governments, and investigators care about most. They want to know: did your intervention work? How do you know? Show me the data. Show me the evidence. Show me the trend line. If you can't prove the outcome, the next funding cycle won't include your program, and the people you're trying to protect will be left undefended."

In ADAPT, PROVE calculates metrics, generates briefings, and writes everything to the evidence chain. Every metric gets dual-hashed. The proof is the product.

### Step 15: Advance to PROVE

```bash
# Advance cycle to PROVE phase
curl -X POST http://localhost:3000/api/v1/adapt/cycles/$CYCLE_ID/advance \
  -H "Authorization: Bearer $TOKEN"
```

### Step 16: Measure the Response

```bash
# Get metrics for this cycle
curl -s http://localhost:3000/api/v1/adapt/metrics \
  -H "Authorization: Bearer $TOKEN" | jq '.[] | select(.cycle_id == "'$CYCLE_ID'")'
```

Response:

```json
[
  {
    "id": "01949abc-1234-7000-8000-000000000501",
    "cycle_id": "01949abc-1234-7000-8000-000000000030",
    "metric_type": "Mttd",
    "scope": "PHANTOM MERCY Infrastructure Investigation",
    "value": 0.42,
    "previous_value": 2.1,
    "trend": "Improving",
    "measured_at": "2026-02-21T14:40:00Z",
    "evidence_hash": "blake3:1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a"
  },
  {
    "id": "01949abc-1234-7000-8000-000000000502",
    "cycle_id": "01949abc-1234-7000-8000-000000000030",
    "metric_type": "Mttr",
    "scope": "PHANTOM MERCY Infrastructure Investigation",
    "value": 0.58,
    "previous_value": 4.2,
    "trend": "Improving",
    "measured_at": "2026-02-21T14:40:00Z",
    "evidence_hash": "blake3:2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2b"
  },
  {
    "id": "01949abc-1234-7000-8000-000000000503",
    "cycle_id": "01949abc-1234-7000-8000-000000000030",
    "metric_type": "ExposureReduction",
    "scope": "PHANTOM MERCY Infrastructure Investigation",
    "value": 100.0,
    "previous_value": null,
    "trend": "Stable",
    "measured_at": "2026-02-21T14:40:00Z",
    "evidence_hash": "blake3:3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2b3c"
  },
  {
    "id": "01949abc-1234-7000-8000-000000000504",
    "cycle_id": "01949abc-1234-7000-8000-000000000030",
    "metric_type": "Coverage",
    "scope": "phantom_mercy_detection",
    "value": 95.0,
    "previous_value": 55.0,
    "trend": "Improving",
    "measured_at": "2026-02-21T14:40:00Z",
    "evidence_hash": "blake3:4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2b3c4d"
  }
]
```

The results:

| Metric | Value | Previous | Trend |
|--------|-------|----------|-------|
| **Mean Time to Detect** | 0.42 hours (25 min) | 2.1 hours | Improving |
| **Mean Time to Remediate** | 0.58 hours (35 min) | 4.2 hours | Improving |
| **Exposure Reduction** | 100% | N/A | Complete |
| **PHANTOM MERCY Detection Coverage** | 95% | 55% | Improving |

MTTD went from 2.1 hours to 25 minutes. MTTR went from 4.2 hours to 35 minutes. PHANTOM MERCY detection coverage jumped from 55% to 95%.

Twenty-five minutes from anomaly to awareness. Thirty-five minutes from awareness to containment. For an operation that Clara spent two years tracking, that the security officer at Sentinelle Humanitaire dismissed as paranoia, that exploited 0-days and planted insiders and supply chain compromises to traffic children.

Forty-five minutes.

It's not enough. It'll never be enough until Clara is safe and PHANTOM MERCY is dismantled. But it's a start.

### Step 17: Generate the Executive Briefing

```bash
# Generate an executive briefing for this cycle
curl -X POST http://localhost:3000/api/v1/adapt/briefings \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "cycle_id": "'$CYCLE_ID'",
    "template_id": "incident-response-executive",
    "audience": "law-enforcement",
    "classification": "confidential"
  }'
```

Response:

```json
{
  "id": "01949abc-1234-7000-8000-000000000601",
  "title": "ADAPT Cycle Report: PHANTOM MERCY Operation Detected - 2026-02-21",
  "status": "draft",
  "cycle_id": "01949abc-1234-7000-8000-000000000030",
  "sections": [
    {
      "title": "Executive Summary",
      "content": "At 14:07 CET, behavioral anomaly detection identified an active PHANTOM MERCY operation targeting humanitarian infrastructure associated with Sentinelle Humanitaire. A complete ADAPT cycle was executed in 45 minutes. The C2 channel was disrupted, detection rules were deployed, and all exposed assets were contained. MTTD: 25 minutes. MTTR: 35 minutes. This operation is assessed as connected to the ongoing investigation into the disappearance of Clara Dubois and the trafficking of unaccompanied minors through humanitarian aid networks."
    },
    {
      "title": "Threat Assessment",
      "content": "Threat actor: PHANTOM MERCY (state-sponsored, attribution pending). Initial access via Exchange Server 0-day (CVE-2026-0195). C2 established via DNS TXT records to domains matching documented PHANTOM MERCY infrastructure. Behavioral genome match: 0.94 confidence. Rogue VM detected on gateway subnet consistent with documented staging technique."
    },
    {
      "title": "Response Actions Taken",
      "content": "5 defense actions executed. C2 domains sinkholen. SIGMA and YARA detection rules deployed. Zero Trust policy applied to monitored subnet. Incident ticket INC-2026-0012 created. All actions linked to evidence chain with dual BLAKE3/SHA-256 hashes."
    },
    {
      "title": "Evidence Chain",
      "content": "All evidence dual-hashed (BLAKE3 + SHA-256). 3 validated exposures with evidence hashes. Full chain of custody maintained. Legal hold recommended pending law enforcement coordination. Evidence quality assessed as sufficient for international judicial proceedings."
    },
    {
      "title": "Connection to Clara Dubois Investigation",
      "content": "IOCs and behavioral patterns match documentation provided by Clara Dubois prior to her disappearance on February 10, 2026. Her research archive, received February 14, 2026, provided the behavioral markers used to identify this operation. Her analysis of PHANTOM MERCY operational patterns has been validated by this live detection. Clara Dubois's current status: unknown. Last contact: 23:47 CET, February 10, 2026."
    }
  ],
  "evidence_hashes": [
    "blake3:7a3f2b1c8d9e4f0a5b6c7d8e9f0a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f",
    "blake3:8b4f3c2d9e0f5a1b6c7d8e9f0a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a",
    "blake3:9c5f4d3e0a1b6c2d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2b3c4d5e6f7a8b9c"
  ],
  "created_at": "2026-02-21T14:42:00Z"
}
```

### Step 18: Publish and Distribute

```bash
# Publish the briefing
curl -X POST http://localhost:3000/api/v1/adapt/briefings/01949abc-1234-7000-8000-000000000601/publish \
  -H "Authorization: Bearer $TOKEN"
```

**Time elapsed: 45 minutes. Cycle complete.**

---

## 3.8 -- Post-Cycle: The Replay and the Revelation

After the immediate response, I use ADAPT Replay to reconstruct the entire timeline:

```bash
# Create a replay of the incident
curl -X POST http://localhost:3000/api/v1/adapt/replay/replays \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "PHANTOM MERCY Operation Replay - 2026-02-21",
    "description": "Full timeline reconstruction of PHANTOM MERCY operation and ADAPT response",
    "start_time": "2026-02-21T13:42:00Z",
    "end_time": "2026-02-21T14:45:00Z"
  }'
```

The Replay module reconstructs every event in chronological order:

```
13:42:00  First anomalous DNS TXT query from mail gateway
13:42:15  PHANTOM MERCY C2 beacon sent (dns_txt_c2)
13:55:00  DNS traffic volume exceeds 2x baseline
14:07:00  Sentinel alert fires (3.1x deviation)
14:08:30  ADAPT cycle created -- PHANTOM MERCY investigation
14:09:00  DISCOVER: 3 exposure events detected
14:10:15  CORRELATE: 3 high-risk correlations + genome match 0.94
14:18:30  VALIDATE: CVE-2026-0195 confirmed on mail gateway
14:20:00  VALIDATE: All 3 exposures confirmed
14:26:00  FORTIFY: 7 defense actions generated
14:26:15  FORTIFY: 5 auto-executed actions completed
14:28:00  FORTIFY: SOAR playbook approved and executed
14:28:45  C2 domains sinkholen -- PHANTOM MERCY communication cut
14:40:00  PROVE: Metrics calculated, briefing generated
14:42:00  Briefing published with law enforcement classification
```

The gap between 13:42 (first indicator) and 14:07 (Sentinel alert) is 25 minutes. This is the detection latency -- the time it takes for enough anomalous data to accumulate for the Sentinel baseline to fire.

But something else catches my eye in the replay data. The traffic capture from step 2 of the SOAR playbook -- the DNS TXT traffic that was recorded before the sinkhole went into effect.

I pull the captured data. Most of it is base64-encoded C2 traffic. Routine beacon-and-response patterns. But one packet, timestamped 14:27:43 -- just before the sinkhole cut the channel -- contains a DNS TXT response that's different from the others. Longer. Different encoding pattern.

I decode it.

It's not C2 traffic. It's a message. Embedded in the C2 channel, hidden between beacon packets, readable only if you capture the raw DNS TXT responses and know what to look for.

```
49 27 6D 20 61 6C 69 76 65 2E 20 47 6F 6D 61 2E
48 6F 74 65 6C 20 49 73 68 61 6E 67 69 2E 20 52
6F 6F 6D 20 33 31 37 2E 20 48 75 72 72 79 2E
```

Hex to ASCII:

*I'm alive. Goma. Hotel Ishangi. Room 317. Hurry.*

Clara.

She's been hiding messages in PHANTOM MERCY's own C2 channel. Using their infrastructure against them. Broadcasting her location to anyone with the tools to capture and decode the traffic.

Broadcasting to me. Because she knew I'd build the tools. Because she told me to build them.

I stare at the screen. My hands are shaking. The cursor blinks.

Hotel Ishangi. Room 317. Goma.

I close the briefing. I open a browser.

The next available flight to Kigali -- the closest international airport to Goma -- leaves in 11 hours.

---

## 3.9 -- Lessons From This Cycle

1. **The Sentinel baseline caught what signatures missed.** There was no signature for this specific PHANTOM MERCY variant. The behavioral detection -- "DNS TXT traffic volume is 3.1x higher than normal" -- was the trigger. Clara's archive provided the context. The technology and the human intelligence together.

2. **The ADAPT Genome was decisive.** Without the behavioral genome I built from Clara's research, the correlation phase would have identified generic APT indicators. The genome turned a generic detection into a specific attribution. 0.94 confidence. PHANTOM MERCY.

3. **Auto-validate, manual-fortify is the right posture.** Automated validation saves 10 minutes. Manual fortification approval ensures you make conscious decisions about tipping off the adversary. I chose to sinkhole and accepted the loss of visibility. Clara would have made the same choice.

4. **Evidence hashing at every step matters.** Every metric, every validation result, every defense action has a BLAKE3 hash. When this goes to an international tribunal -- and it will -- the evidence chain is intact from minute one.

5. **45 minutes is achievable.** The industry average for a complete incident response cycle against a state-sponsored operation is measured in weeks. With a structured methodology and the right tooling, you can do it in 45 minutes. Not because the methodology is magic. Because it imposes discipline on chaos. Because it forces you through a sequence when your hands are shaking and your mind is racing and the woman you love is in a hotel room in a conflict zone sending hex-encoded distress signals through a trafficker's C2 channel.

6. **The platform is not the mission.** The platform is the weapon. The mission is the people. Clara's people. The children. The field workers. The analysts who sit at their desks at 2 AM because they know something is wrong and nobody believes them. This cycle proved the methodology works. Now the methodology has to save a life.

---

## 3.10 -- What Happens Next

The ADAPT cycle is complete. The evidence is preserved. The detection rules are deployed. PHANTOM MERCY's C2 channel on this network segment is dead.

But the operation is bigger than one network segment. Clara's archive documented PHANTOM MERCY across 12 countries and multiple humanitarian organizations. Cutting one C2 channel is cutting one tentacle. The creature is still alive.

And Clara is in Goma. In a hotel room. Alive.

The next chapter will show you how the Evidence Court module handles evidence that crosses international jurisdictions -- because that's what I'm going to need when I get to Goma. Evidence collected in Belgium, from infrastructure in France, about crimes committed in the DRC, presented to a court in The Hague.

But first, I have a flight to catch.

---

## 3.11 -- The Dashboard View

On the desktop app, the ADAPT dashboard shows all of this in a single view:

```typescript
// What the React component renders after this cycle
interface AdaptDashboardData {
  active_cycles: number;       // 1 (this cycle)
  total_exposures: number;     // 3 (all confirmed)
  critical_findings: number;   // 2 (CVE + IOC)
  resilience_score: number;    // 73.5 (up from 68.2)
  mttd_hours: number;         // 0.42
  mttr_hours: number;         // 0.58
  actions_pending: number;     // 1 (RT exercise)
  actions_completed: number;   // 6
}
```

```bash
# Verify the dashboard data
curl -s http://localhost:3000/api/v1/adapt/dashboard \
  -H "Authorization: Bearer $TOKEN" | jq .
```

The dashboard is clean. The numbers are green. The resilience score ticked up.

But the number that matters isn't on the dashboard. It's 317. Room 317.

I close the laptop. I pack a bag. I book the flight.

The code is done. The evidence is locked. The methodology works.

Now the real operation begins.

---

*Next chapter: "Digital Evidence That Survives Legal Challenge"*

---

(c) 2026 Playseat -- All Rights Reserved | Defensive Intelligence Through ADAPT
