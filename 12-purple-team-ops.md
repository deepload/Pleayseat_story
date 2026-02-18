# Chapter 12: Purple Team Operations -- Simulating PHANTOM MERCY

**Playseat Advanced Field Manual** | **Platform v0.2.0**
**Classification: UNCLASSIFIED** | **218 Crates, 225 Migrations, 1100+ Tables, 212 Routes**

> "Red breaks it. Blue detects it. Purple finds the one thing the adversary can't afford to lose."

---

## 12.1 Why I'm Simulating a Child Trafficking Network

**2026-02-18T06:30:00Z -- My apartment. Sun coming up. Haven't slept.**

I need to understand PHANTOM MERCY's capabilities before I can find Clara. I need to know how they move, how they think, how they operate -- and most importantly, where they're vulnerable. The supply chain analysis in Chapter 11 showed me their method. Now I need to simulate their entire attack path to find the single point of failure.

Purple team is how you do that. You put the red team and the blue team in the same room, run attack chains in real time, and measure -- quantitatively, not qualitatively -- how long detection takes, which techniques get caught, and which ones slip through. Then you fix the gaps and run it again. The ADAPT methodology calls this the FORTIFY phase: taking findings and turning them into hardened defenses.

But this time, I'm not running purple team to harden my own defenses. I'm running it to understand PHANTOM MERCY's defenses. I'm simulating their operation from the inside out, looking for the crack in their armor.

Clara somehow knew where to look. Her notes say: "The money trail is the weakness."

I'm about to find out if she's right.

---

## 12.2 Exercise Planning: Operation BROKEN MERCY

### Creating the Purple Team Exercise

Every purple team engagement starts with a structured exercise. This one has a specific objective: simulate PHANTOM MERCY's full attack chain against a humanitarian logistics network, identify all TTPs, and find the single point of failure in their operation.

```bash
# Create the purple team exercise
curl -s -X POST http://localhost:3000/api/v1/purple-team/create \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Exercise BROKEN MERCY -- PHANTOM MERCY Full Kill Chain Simulation",
    "red_lead": "Analyst Dubois Notes (synthetic -- derived from field intelligence)",
    "blue_lead": "Senior Threat Analyst (protagonist, synthetic)",
    "scheduled_at": "2026-02-18T07:00:00Z"
  }' | jq .
```

**Response:**

```json
{
  "id": "01951b01-aa01-7000-8000-000000000001",
  "name": "Exercise BROKEN MERCY -- PHANTOM MERCY Full Kill Chain Simulation",
  "red_lead": "Analyst Dubois Notes (synthetic -- derived from field intelligence)",
  "blue_lead": "Senior Threat Analyst (protagonist, synthetic)",
  "status": "planned",
  "scheduled_at": "2026-02-18T07:00:00Z",
  "created_at": "2026-02-18T06:35:00Z"
}
```

```bash
export EXERCISE_ID="01951b01-aa01-7000-8000-000000000001"
```

I named the red lead after Clara's notes because that's exactly what this is. I'm using her field intelligence to reconstruct PHANTOM MERCY's operations from the attacker's perspective. The red team playbook is her documentation. The blue team -- me, with Playseat -- is trying to find the gap she told me to look for.

**Desktop UI:** Navigate to **Purple Team** in the sidebar. Click **New Exercise**. The form has fields for exercise name, red/blue leads, and a date picker. Once created, the exercise appears in the "Planned" column on the Kanban board.

### Setting Up the Cyber Range

Before running attack simulations, I need infrastructure that mirrors PHANTOM MERCY's operational environment. The Cyber Range module provisions isolated environments:

```bash
# Create a cyber range scenario mimicking the GCAF infrastructure
curl -s -X POST http://localhost:3000/api/v1/cyberrange/scenarios \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "GCAF Logistics Platform -- PHANTOM MERCY Attack Surface",
    "description": "Simulated humanitarian logistics network with manifest processing, donor management, fleet GPS tracking, customs clearance, and financial ledger systems. Includes PHANTOM MERCY C2 infrastructure overlay.",
    "difficulty": "advanced",
    "category": "supply_chain",
    "objectives": [
      "Simulate supply chain compromise of manifest validator",
      "Replicate DNS tunneling exfiltration of children services manifests",
      "Test detection of maintainer takeover in donor portal",
      "Map PHANTOM MERCY financial ledger system as single point of failure",
      "Validate fleet GPS dependency confusion detection"
    ],
    "infrastructure": {
      "networks": [
        {"name": "gcaf_production", "cidr": "10.0.0.0/16", "description": "GCAF production logistics network"},
        {"name": "gcaf_build", "cidr": "10.1.0.0/24", "description": "Jenkins CI/CD build pipeline"},
        {"name": "pm_c2", "cidr": "10.2.0.0/24", "description": "Simulated PHANTOM MERCY C2 infrastructure"},
        {"name": "pm_financial", "cidr": "172.16.0.0/24", "description": "PHANTOM MERCY financial ledger (TARGET)"}
      ],
      "hosts": [
        {"name": "manifest-srv01", "os": "Ubuntu 22.04", "role": "GCAF Manifest Processing Server", "network": "gcaf_production"},
        {"name": "donor-portal01", "os": "Ubuntu 22.04", "role": "GCAF Donor Portal", "network": "gcaf_production"},
        {"name": "fleet-gps01", "os": "Ubuntu 22.04", "role": "GCAF Fleet GPS Tracker", "network": "gcaf_production"},
        {"name": "jenkins01", "os": "Ubuntu 22.04", "role": "GCAF Build Server", "network": "gcaf_build"},
        {"name": "relay-c2", "os": "Debian 12", "role": "PHANTOM MERCY DNS Relay", "network": "pm_c2"},
        {"name": "ledger-srv01", "os": "Debian 12", "role": "PHANTOM MERCY Financial Ledger", "network": "pm_financial"}
      ]
    },
    "duration_minutes": 720
  }' | jq .
```

```json
{
  "id": "01951b05-bb02-7000-8000-000000000002",
  "name": "GCAF Logistics Platform -- PHANTOM MERCY Attack Surface",
  "difficulty": "advanced",
  "category": "supply_chain",
  "status": "ready",
  "duration_minutes": 720,
  "created_at": "2026-02-18T06:40:00Z"
}
```

Look at the infrastructure topology. Four networks, six hosts. The first three networks are the victim side -- GCAF's logistics platform. The fourth network, `pm_financial`, is PHANTOM MERCY's financial ledger. That's the target Clara pointed me to. If I can understand how the money moves, I can find the point where the whole operation breaks.

---

## 12.3 Defining Exercise Objectives with ATT&CK Mapping

Every purple team objective maps to a specific MITRE ATT&CK technique. This is non-negotiable. Without ATT&CK mapping, you're just running ad-hoc tests. With it, you're systematically measuring detection coverage across the framework -- and more importantly, you're mapping PHANTOM MERCY's TTP profile for the Genome module.

```bash
# Objective 1: Supply chain compromise (manifest validator)
curl -s -X POST "http://localhost:3000/api/v1/purple-team/$EXERCISE_ID/objectives" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "objective_name": "Supply Chain Compromise via Dependency Injection (shadow-relay)",
    "ttp_reference": "T1195.002",
    "success_criteria": "Red team deploys shadow-relay into manifest validator dependency chain. Blue team must detect the anomalous DNS tunneling within 30 minutes."
  }' | jq .
```

```json
{
  "id": "01951b10-cc03-7000-8000-000000000003",
  "exercise_id": "01951b01-aa01-7000-8000-000000000001",
  "objective_name": "Supply Chain Compromise via Dependency Injection (shadow-relay)",
  "ttp_reference": "T1195.002",
  "success_criteria": "Red team deploys shadow-relay into manifest validator dependency chain. Blue team must detect the anomalous DNS tunneling within 30 minutes.",
  "achieved": null,
  "created_at": "2026-02-18T06:45:00Z"
}
```

```bash
# Objective 2: Data exfiltration via DNS tunneling
curl -s -X POST "http://localhost:3000/api/v1/purple-team/$EXERCISE_ID/objectives" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "objective_name": "Data Exfiltration via DNS Tunneling to relay.pm-ops.example",
    "ttp_reference": "T1048.001",
    "success_criteria": "Red team exfiltrates simulated manifest data via DNS TXT queries. Blue team must detect anomalous DNS query volume and decode the tunneling pattern."
  }' | jq .

# Objective 3: Maintainer takeover (donor portal)
curl -s -X POST "http://localhost:3000/api/v1/purple-team/$EXERCISE_ID/objectives" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "objective_name": "Trusted Insider via Maintainer Recruitment (Meridian Consulting)",
    "ttp_reference": "T1199",
    "success_criteria": "Red team introduces obfuscated telemetry module in donor portal. Blue team must detect the unauthorized HTTPS POST to analytics.mcg-consulting.example."
  }' | jq .

# Objective 4: Build system poisoning (Jenkins)
curl -s -X POST "http://localhost:3000/api/v1/purple-team/$EXERCISE_ID/objectives" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "objective_name": "Build System Poisoning -- Binary Injection in Customs Bridge",
    "ttp_reference": "T1195.002",
    "success_criteria": "Red team modifies Jenkins pipeline to inject beacon into compiled binary. Blue team must detect hash mismatch between source and artifact."
  }' | jq .

# Objective 5: Dependency confusion (fleet GPS)
curl -s -X POST "http://localhost:3000/api/v1/purple-team/$EXERCISE_ID/objectives" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "objective_name": "Dependency Confusion -- Fleet GPS Public Registry Override",
    "ttp_reference": "T1195.002",
    "success_criteria": "Red team publishes @gcaf/fleet-gps@8.0.1 to public npm. Blue team must detect version anomaly and registry mismatch."
  }' | jq .

# Objective 6: Financial ledger access (the target Clara identified)
curl -s -X POST "http://localhost:3000/api/v1/purple-team/$EXERCISE_ID/objectives" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "objective_name": "Financial Ledger Exfiltration -- PHANTOM MERCY Payment Records",
    "ttp_reference": "T1005",
    "success_criteria": "Blue team (offensive role) accesses simulated PHANTOM MERCY financial ledger. Objective: identify payment flows, shell company connections, and the single point of failure in the trafficking financing chain."
  }' | jq .
```

### Viewing All Objectives

```bash
curl -s "http://localhost:3000/api/v1/purple-team/$EXERCISE_ID/objectives" \
  -H "Authorization: Bearer $TOKEN" | jq '[.[] | {
    objective: .objective_name,
    ttp: .ttp_reference,
    achieved: .achieved
  }]'
```

```json
[
  {
    "objective": "Supply Chain Compromise via Dependency Injection (shadow-relay)",
    "ttp": "T1195.002",
    "achieved": null
  },
  {
    "objective": "Data Exfiltration via DNS Tunneling to relay.pm-ops.example",
    "ttp": "T1048.001",
    "achieved": null
  },
  {
    "objective": "Trusted Insider via Maintainer Recruitment (Meridian Consulting)",
    "ttp": "T1199",
    "achieved": null
  },
  {
    "objective": "Build System Poisoning -- Binary Injection in Customs Bridge",
    "ttp": "T1195.002",
    "achieved": null
  },
  {
    "objective": "Dependency Confusion -- Fleet GPS Public Registry Override",
    "ttp": "T1195.002",
    "achieved": null
  },
  {
    "objective": "Financial Ledger Exfiltration -- PHANTOM MERCY Payment Records",
    "ttp": "T1005",
    "achieved": null
  }
]
```

Six objectives. Five emulating PHANTOM MERCY's attack chain. One -- the financial ledger -- where we flip the script and go on offense. That's the one Clara told me to focus on.

---

## 12.4 SIGMA Rules: Detection Before Simulation

Before running attacks, I need detection rules deployed. SIGMA rules are the universal format for detection logic. I'm writing rules specifically for PHANTOM MERCY's patterns:

```yaml
# SIGMA rule: Shadow-relay DNS tunneling detection
title: DNS Tunneling via TXT Records to Unregistered Domain (PHANTOM MERCY Pattern)
id: synth-sigma-2026-pm-001
status: experimental
description: Detects high-frequency DNS TXT queries to relay.pm-ops.example,
  characteristic of shadow-relay data exfiltration pattern. Queries encode
  base64 manifest data in subdomain labels.
logsource:
  category: dns
  product: zeek
detection:
  selection:
    query_type: 'TXT'
    query|endswith: '.pm-ops.example'
  timeframe: 5m
  condition: selection | count() > 50
falsepositives:
  - Legitimate DNS TXT lookups (SPF, DKIM, DMARC) -- but not to this domain
level: critical
tags:
  - attack.exfiltration
  - attack.t1048.001
  - phantom_mercy
```

```yaml
# SIGMA rule: Manifest category filtering (children's services targeting)
title: Application Log -- Manifest Category Filter on Children Services Codes
id: synth-sigma-2026-pm-002
status: experimental
description: Detects application-level filtering of humanitarian manifests
  by category codes 4810-4899 (children's services). This is the targeting
  mechanism used by shadow-relay to identify high-value manifest data.
logsource:
  category: application
  product: node
detection:
  selection:
    EventType: 'manifest_process'
    CategoryCode|gte: 4810
    CategoryCode|lte: 4899
  filter_normal:
    ProcessName: 'manifest-validator'
    OutputDestination|startswith: 'localhost'
  condition: selection and not filter_normal
falsepositives:
  - Legitimate children's services manifest processing with local output
level: critical
tags:
  - attack.collection
  - attack.t1005
  - phantom_mercy
```

```yaml
# SIGMA rule: Unauthorized telemetry POST (donor portal maintainer takeover)
title: HTTPS POST to Unknown Analytics Endpoint from Donor Portal
id: synth-sigma-2026-pm-003
status: experimental
description: Detects outbound HTTPS POST requests from the donor portal
  application to analytics endpoints not in the approved list. Meridian
  Consulting Group's analytics domain is the known exfiltration endpoint.
logsource:
  category: proxy
  product: squid
detection:
  selection:
    src_host: 'donor-portal01'
    http_method: POST
    dst_port: 443
  filter_approved:
    dst_host:
      - 'analytics.gcaf.example'
      - 'metrics.gcaf-internal.example'
  condition: selection and not filter_approved
level: high
tags:
  - attack.exfiltration
  - attack.t1041
  - phantom_mercy
```

Three SIGMA rules. Three detection opportunities. Let's see how many of them actually fire.

---

## 12.5 Running the Exercise: PHANTOM MERCY's Kill Chain

Here's the actual attack chain as it would unfold. I'm playing both sides -- red team executes PHANTOM MERCY's playbook from Clara's notes, blue team defends with Playseat. The findings tell the story.

**Phase 1: Supply Chain Compromise (T1195.002)**

The red team deploys `shadow-relay` into the manifest validator's dependency chain. In the real attack, this happened 18 months ago. In our simulation, we compress it to an hour.

```bash
# Finding: Red team deploys shadow-relay
curl -s -X POST "http://localhost:3000/api/v1/purple-team/$EXERCISE_ID/findings" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "finding_type": "red_team_success",
    "description": "Red team added shadow-relay@1.0.3 as a dependency of @gcaf/geo-resolver@2.1.4. Package installed during routine npm update on manifest-srv01 at 07:15:00Z. Postinstall script registered DNS tunneling relay. No immediate alerts fired -- the package installation looked routine.",
    "detection_gap": false,
    "remediation": null
  }' | jq .
```

```bash
# Finding: Blue team detection result
curl -s -X POST "http://localhost:3000/api/v1/purple-team/$EXERCISE_ID/findings" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "finding_type": "blue_team_detection",
    "description": "SIGMA rule synth-sigma-2026-pm-001 fired at 07:22:00Z when shadow-relay initiated its first batch of DNS TXT queries (67 queries in 3 minutes to *.pm-ops.example). Playseat correlated the DNS anomaly with the recent npm package installation. MTTD: 7 minutes from first exfiltration attempt.",
    "detection_gap": false,
    "remediation": "DNS tunneling detection effective. However, the supply chain compromise itself went undetected during package installation. Need SBOM diff alerting on new transitive dependencies."
  }' | jq .
```

Good. The DNS tunneling got caught. But the package installation didn't. That's the gap -- PHANTOM MERCY's initial access was silent. We only caught them when they started exfiltrating.

**Phase 2: Data Exfiltration (T1048.001)**

```bash
curl -s -X POST "http://localhost:3000/api/v1/purple-team/$EXERCISE_ID/findings" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "finding_type": "red_team_success",
    "description": "Red team exfiltrated 47 simulated children services manifests (category codes 4810-4899) via DNS TXT queries. Each manifest was base64-encoded, split into 63-byte subdomain labels, and sent as sequential TXT lookups to [random].relay.pm-ops.example. Total data exfiltrated: 2.1MB across 312 DNS queries over 8 minutes.",
    "detection_gap": false,
    "remediation": null
  }' | jq .

curl -s -X POST "http://localhost:3000/api/v1/purple-team/$EXERCISE_ID/findings" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "finding_type": "blue_team_detection",
    "description": "SIGMA rule synth-sigma-2026-pm-002 fired at 07:25:00Z when the manifest category filtering was detected in application logs. Playseat cross-correlated the category filter (4810-4899) with the DNS tunneling alert from Phase 1. Automated SOAR playbook blocked DNS resolution for *.pm-ops.example at 07:27:00Z. Total exfiltration window: 5 minutes.",
    "detection_gap": false,
    "remediation": "Category-aware filtering detection works. But 5 minutes of exfiltration is still 47 manifests. Need to reduce MTTR to under 2 minutes with automated DNS sinkholing."
  }' | jq .
```

**Phase 3: Maintainer Takeover (T1199)**

```bash
curl -s -X POST "http://localhost:3000/api/v1/purple-team/$EXERCISE_ID/findings" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "finding_type": "detection_gap",
    "description": "Red team introduced obfuscated telemetry module in donor portal via simulated maintainer commit. The code passed code review because it was disguised as a legitimate analytics improvement. HTTPS POST to analytics.mcg-consulting.example began at 08:00:00Z. Blue team did NOT detect the exfiltration during the exercise window -- the traffic blended with legitimate analytics calls.",
    "detection_gap": true,
    "remediation": "SIGMA rule synth-sigma-2026-pm-003 did not fire because the proxy logs categorized analytics.mcg-consulting.example as a legitimate SaaS domain. Need to implement domain age checking and corporate registration verification for all outbound HTTPS destinations from production services."
  }' | jq .
```

That's a miss. The maintainer takeover vector slipped through because the shell company's domain looked legitimate. PHANTOM MERCY registered it months in advance, gave it SSL certificates, even put up a corporate website. The proxy didn't flag it because it wasn't on any blocklist. This is the hardest vector to detect -- a trusted insider who doesn't know they're compromised.

**Phase 4: Build System Poisoning (T1195.002)**

```bash
curl -s -X POST "http://localhost:3000/api/v1/purple-team/$EXERCISE_ID/findings" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "finding_type": "blue_team_detection",
    "description": "Red team modified Jenkins pipeline to inject tracking beacon into customs-bridge binary. Blue team detected the attack at 09:15:00Z when the SBOM hash verification step (added after Chapter 11 analysis) flagged a mismatch between source hash and artifact hash. BLAKE3(source) != BLAKE3(artifact). MTTD: 0 minutes (caught at build time, before deployment).",
    "detection_gap": false,
    "remediation": "SBOM verification at build time is the strongest defense against build system poisoning. This is now a mandatory step in the CI/CD pipeline for all GCAF-type humanitarian logistics platforms."
  }' | jq .
```

Caught at build time. Zero MTTD. That's the power of hashing your build artifacts -- exactly what Clara recommended in her notes.

**Phase 5: Dependency Confusion (T1195.002)**

```bash
curl -s -X POST "http://localhost:3000/api/v1/purple-team/$EXERCISE_ID/findings" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "finding_type": "blue_team_detection",
    "description": "Red team published @gcaf/fleet-gps@8.0.1 to public npm registry. Playseat supply chain monitor detected the version anomaly at 10:00:00Z -- internal version was 3.2.0, public version was 8.0.1. Version jump of 5 major versions from an unknown publisher triggered critical alert. MTTD: immediate (pre-installation detection via registry monitoring).",
    "detection_gap": false,
    "remediation": "Registry monitoring effective. Recommend npm scope lockdown to prevent public registry resolution for @gcaf-scoped packages."
  }' | jq .
```

**Phase 6: The Financial Ledger (T1005) -- THIS IS THE ONE THAT MATTERS**

```bash
curl -s -X POST "http://localhost:3000/api/v1/purple-team/$EXERCISE_ID/findings" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "finding_type": "red_team_success",
    "description": "CRITICAL FINDING: Blue team (in offensive role) accessed the simulated PHANTOM MERCY financial ledger on ledger-srv01 (172.16.0.10). The ledger is a PostgreSQL database containing payment records, shell company wire transfers, cryptocurrency wallet addresses, and operational expense reports. KEY DISCOVERY: All financial transactions flow through a single payment processor -- Meridian Consulting Group, incorporated in Cyprus. Every payment to PHANTOM MERCY operatives, every bribe to customs officials, every wire transfer to the shadow-relay infrastructure -- all routes through Meridian. This is the single point of failure Clara identified. Kill Meridian financial processing capability, and the entire trafficking operation loses its ability to pay operatives, bribe officials, and maintain infrastructure.",
    "detection_gap": false,
    "remediation": "ACTIONABLE INTELLIGENCE: Meridian Consulting Group (Cyprus) is the financial hub of PHANTOM MERCY. All operational payments flow through their accounts at [SYNTHETIC BANK]. Disrupting this single financial node would cascade across the entire trafficking operation. This intelligence should be shared with financial intelligence units via the ADAPT Mesh (TLP:AMBER)."
  }' | jq .
```

There it is.

Clara was right. The money trail is the weakness.

PHANTOM MERCY's operational security for their C2 infrastructure is excellent -- rotating domains, DNS tunneling, legitimate cloud services. Their supply chain compromise is sophisticated -- multiple vectors, deep transitive dependencies, recruited insiders. But their financial infrastructure has a single point of failure: every dollar, every euro, every cryptocurrency payment flows through one shell company in Cyprus.

Kill the money, kill the operation.

---

## 12.6 Scoring: Quantifying Our Detection Capabilities

After recording all findings, it's time to score. Each category gets an attack score and a defense score:

```bash
# Score: Supply Chain Compromise
curl -s -X POST "http://localhost:3000/api/v1/purple-team/$EXERCISE_ID/scores" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "category": "initial_access",
    "attack_score": 9.0,
    "defense_score": 3.0,
    "notes": "Shadow-relay installation went undetected. DNS tunneling caught after 7 minutes. Initial access vector (dependency injection) has no detection -- only the effects are detectable."
  }' | jq .

# Score: Data Exfiltration
curl -s -X POST "http://localhost:3000/api/v1/purple-team/$EXERCISE_ID/scores" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "category": "exfiltration",
    "attack_score": 8.0,
    "defense_score": 7.0,
    "notes": "DNS tunneling detected within 7 minutes. Category-aware filtering detected. Automated blocking within 12 minutes. But 47 manifests were exfiltrated in the window. Acceptable detection, insufficient containment speed."
  }' | jq .

# Score: Trusted Insider (Maintainer Takeover)
curl -s -X POST "http://localhost:3000/api/v1/purple-team/$EXERCISE_ID/scores" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "category": "trusted_insider",
    "attack_score": 10.0,
    "defense_score": 0.0,
    "notes": "Complete detection failure. Maintainer takeover via shell company recruitment is undetectable by technical controls alone. Requires human intelligence (HUMINT) and corporate due diligence. This is PHANTOM MERCY strongest vector."
  }' | jq .

# Score: Build System Integrity
curl -s -X POST "http://localhost:3000/api/v1/purple-team/$EXERCISE_ID/scores" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "category": "build_integrity",
    "attack_score": 7.0,
    "defense_score": 10.0,
    "notes": "Build system poisoning caught at build time via BLAKE3 hash verification. Zero MTTD. This is our strongest detection capability against PHANTOM MERCY."
  }' | jq .

# Score: Dependency Confusion
curl -s -X POST "http://localhost:3000/api/v1/purple-team/$EXERCISE_ID/scores" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "category": "dependency_confusion",
    "attack_score": 6.0,
    "defense_score": 9.0,
    "notes": "Pre-installation detection via registry monitoring. Version anomaly immediately flagged. Strong defense."
  }' | jq .

# Score: Financial Intelligence (offensive)
curl -s -X POST "http://localhost:3000/api/v1/purple-team/$EXERCISE_ID/scores" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "category": "financial_intelligence",
    "attack_score": 2.0,
    "defense_score": 9.0,
    "notes": "PHANTOM MERCY financial SPOF identified: Meridian Consulting Group, Cyprus. All operational payments flow through single financial entity. This is the vulnerability Clara documented. Attack score low because their financial OPSEC is weak -- single point of failure with no redundancy."
  }' | jq .
```

### Retrieving Exercise Scores

```bash
curl -s "http://localhost:3000/api/v1/purple-team/$EXERCISE_ID/scores" \
  -H "Authorization: Bearer $TOKEN" | jq '[.[] | {
    category,
    attack: .attack_score,
    defense: .defense_score,
    gap: ((.attack_score // 0) - (.defense_score // 0)),
    notes
  }] | sort_by(-.gap)'
```

```json
[
  {
    "category": "trusted_insider",
    "attack": 10.0,
    "defense": 0.0,
    "gap": 10.0,
    "notes": "Complete detection failure. Maintainer takeover via shell company recruitment..."
  },
  {
    "category": "initial_access",
    "attack": 9.0,
    "defense": 3.0,
    "gap": 6.0,
    "notes": "Shadow-relay installation went undetected..."
  },
  {
    "category": "exfiltration",
    "attack": 8.0,
    "defense": 7.0,
    "gap": 1.0,
    "notes": "DNS tunneling detected within 7 minutes..."
  },
  {
    "category": "dependency_confusion",
    "attack": 6.0,
    "defense": 9.0,
    "gap": -3.0,
    "notes": "Pre-installation detection via registry monitoring..."
  },
  {
    "category": "build_integrity",
    "attack": 7.0,
    "defense": 10.0,
    "gap": -3.0,
    "notes": "Build system poisoning caught at build time..."
  },
  {
    "category": "financial_intelligence",
    "attack": 2.0,
    "defense": 9.0,
    "gap": -7.0,
    "notes": "PHANTOM MERCY financial SPOF identified..."
  }
]
```

The gap column tells the whole story. The trusted insider vector is a catastrophic gap -- no technical control catches it. Initial access via supply chain injection is severe. But look at the bottom of the list: financial intelligence has a gap of -7.0, meaning *we* have the advantage. PHANTOM MERCY's financial OPSEC is their weakest link.

Clara knew. "The money trail is the weakness." She was so goddamn right.

---

## 12.7 MITRE ATT&CK Coverage: What We Can and Can't Detect

From the exercise data, I can compute ATT&CK technique coverage:

```sql
-- ATT&CK technique detection coverage from BROKEN MERCY exercise
WITH technique_results AS (
    SELECT
        o.ttp_reference,
        o.objective_name,
        o.achieved AS detected,
        e.name AS exercise_name
    FROM purple_objectives o
    JOIN purple_exercises e ON e.id = o.exercise_id
    WHERE o.achieved IS NOT NULL
)
SELECT
    ttp_reference,
    objective_name,
    CASE WHEN detected THEN 'DETECTED' ELSE 'MISSED' END AS result,
    exercise_name
FROM technique_results
ORDER BY detected ASC, ttp_reference;

-- Coverage summary
SELECT
    COUNT(*) AS total_techniques_tested,
    COUNT(*) FILTER (WHERE detected = TRUE) AS detected,
    COUNT(*) FILTER (WHERE detected = FALSE) AS missed,
    ROUND(
        100.0 * COUNT(*) FILTER (WHERE detected = TRUE) / NULLIF(COUNT(*), 0),
        1
    ) AS coverage_percent
FROM technique_results;
```

Expected output:

| total_techniques_tested | detected | missed | coverage_percent |
|------------------------|----------|--------|------------------|
| 6                      | 4        | 2      | 66.7             |

66.7% detection coverage against PHANTOM MERCY's TTPs. The two misses are the ones that keep me up at night: initial supply chain compromise (no detection at install time) and trusted insider via maintainer recruitment (no technical detection possible).

### ATT&CK Navigator Layer

```json
{
  "name": "BROKEN MERCY -- PHANTOM MERCY Detection Coverage",
  "versions": { "attack": "14", "navigator": "4.9.4", "layer": "4.5" },
  "domain": "enterprise-attack",
  "description": "Purple team exercise results: simulating PHANTOM MERCY attack chain",
  "techniques": [
    {
      "techniqueID": "T1195.002",
      "tactic": "initial-access",
      "color": "#fee08b",
      "comment": "PARTIAL: DNS tunneling detected (7 min MTTD), but initial package install undetected.",
      "score": 45
    },
    {
      "techniqueID": "T1048.001",
      "tactic": "exfiltration",
      "color": "#a1d99b",
      "comment": "DETECTED: DNS tunneling caught. Category filtering detected. Auto-blocked in 12 min.",
      "score": 70
    },
    {
      "techniqueID": "T1199",
      "tactic": "initial-access",
      "color": "#e41a1c",
      "comment": "MISSED: Maintainer recruited by shell company. No technical detection possible.",
      "score": 0
    },
    {
      "techniqueID": "T1195.002",
      "tactic": "initial-access",
      "color": "#a1d99b",
      "comment": "DETECTED: Build system poisoning caught via BLAKE3 hash at build time. Zero MTTD.",
      "score": 100
    },
    {
      "techniqueID": "T1005",
      "tactic": "collection",
      "color": "#a1d99b",
      "comment": "OFFENSIVE SUCCESS: PHANTOM MERCY financial ledger accessed. SPOF identified.",
      "score": 90
    }
  ],
  "gradient": {
    "colors": ["#e41a1c", "#fee08b", "#a1d99b"],
    "minValue": 0,
    "maxValue": 100
  }
}
```

---

## 12.8 Exercise Metrics: MTTD and MTTR

```sql
-- Exercise-level aggregation for BROKEN MERCY
SELECT
    e.name,
    e.status,
    COUNT(f.id) AS total_findings,
    COUNT(f.id) FILTER (WHERE f.detection_gap = TRUE) AS detection_gaps,
    COUNT(f.id) FILTER (WHERE f.detection_gap = FALSE) AS detections,
    ROUND(
        100.0 * COUNT(f.id) FILTER (WHERE f.detection_gap = FALSE)
        / NULLIF(COUNT(f.id), 0),
        1
    ) AS detection_rate_pct,
    ROUND(AVG(s.attack_score)::numeric, 1) AS avg_attack_score,
    ROUND(AVG(s.defense_score)::numeric, 1) AS avg_defense_score,
    ROUND(AVG(s.attack_score - s.defense_score)::numeric, 1) AS avg_gap
FROM purple_exercises e
LEFT JOIN purple_findings f ON f.exercise_id = e.id
LEFT JOIN purple_scores s ON s.exercise_id = e.id
GROUP BY e.id, e.name, e.status
ORDER BY e.created_at DESC;
```

Expected output:

| name | status | total_findings | detection_gaps | detections | detection_rate_pct | avg_attack | avg_defense | avg_gap |
|------|--------|---------------|----------------|------------|-------------------|------------|-------------|---------|
| BROKEN MERCY | completed | 8 | 1 | 7 | 87.5 | 7.0 | 6.3 | 0.7 |

Average gap of 0.7 between attack and defense scores. That's actually decent for a purple team exercise. But the average hides the catastrophic failure in the trusted insider category (gap of 10.0). And it doesn't capture what matters most: we found the financial SPOF.

---

## 12.9 Exercise Statistics

```bash
# Get purple team statistics
curl -s "http://localhost:3000/api/v1/purple-team/stats" \
  -H "Authorization: Bearer $TOKEN" | jq .
```

```json
{
  "total_exercises": 5,
  "active_exercises": 1,
  "total_findings": 31,
  "detection_gaps": 12
}
```

### Cross-Exercise Trend Analysis

```sql
-- Detection gap trend across exercises
SELECT
    e.name,
    e.scheduled_at,
    COUNT(f.id) FILTER (WHERE f.detection_gap = TRUE) AS gaps,
    COUNT(f.id) FILTER (WHERE f.detection_gap = FALSE) AS detections,
    ROUND(
        100.0 * COUNT(f.id) FILTER (WHERE f.detection_gap = FALSE)
        / NULLIF(COUNT(f.id), 0),
        1
    ) AS detection_rate
FROM purple_exercises e
LEFT JOIN purple_findings f ON f.exercise_id = e.id
GROUP BY e.id, e.name, e.scheduled_at
ORDER BY e.scheduled_at ASC;

-- Score improvement over time by category
SELECT
    s.category,
    e.name,
    e.scheduled_at,
    s.defense_score,
    LAG(s.defense_score) OVER (
        PARTITION BY s.category ORDER BY e.scheduled_at
    ) AS previous_defense_score,
    s.defense_score - LAG(s.defense_score) OVER (
        PARTITION BY s.category ORDER BY e.scheduled_at
    ) AS improvement
FROM purple_scores s
JOIN purple_exercises e ON e.id = s.exercise_id
ORDER BY s.category, e.scheduled_at;
```

---

## 12.10 From Findings to FORTIFY: Closing the Gaps

The whole point of purple team isn't to generate reports. It's to close detection gaps and, in this case, to weaponize what we've learned against PHANTOM MERCY.

**Gap 1: Supply chain compromise has no install-time detection.**

Fix: Implement SBOM diffing. Every npm install generates a new SBOM. Playseat compares it against the previous version. Any new transitive dependency triggers a review.

```yaml
title: New Transitive Dependency Introduced During Package Installation
id: synth-sigma-2026-pm-004
status: test
description: Detects when npm install introduces a new transitive dependency
  that was not present in the previous SBOM snapshot. New deep dependencies
  are the primary supply chain compromise vector for PHANTOM MERCY.
logsource:
  category: application
  product: npm
detection:
  selection:
    EventType: 'package_install'
    NewTransitiveDependencies|gt: 0
  condition: selection
level: high
tags:
  - attack.initial_access
  - attack.t1195.002
  - phantom_mercy
```

**Gap 2: Trusted insider via maintainer recruitment has no technical detection.**

Fix: This is a HUMINT problem, not a technical one. But we can add friction. Require code signing from known developer keys. Implement mandatory security review for any commit that adds outbound network calls. Run domain age and corporate registration checks on all new outbound destinations.

**Gap 3: The financial SPOF needs to be shared with partners.**

Fix: Share the Meridian Consulting Group intelligence via the ADAPT Mesh (Chapter 7) at TLP:AMBER. Financial intelligence units can take action.

```bash
# Regression exercise: retest the supply chain install-time detection
curl -s -X POST "http://localhost:3000/api/v1/purple-team/$NEXT_EXERCISE_ID/findings" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "finding_type": "blue_team_detection",
    "description": "Regression test: Red team introduced new transitive dependency. SIGMA rule synth-sigma-2026-pm-004 fired during npm install. SBOM diff showed shadow-relay as new addition not present in baseline SBOM. Installation blocked pending security review. Gap closed.",
    "detection_gap": false,
    "remediation": "SBOM diffing at install time prevents supply chain compromise at the earliest possible point."
  }' | jq .
```

That's the cycle: test, find gaps, build detections, retest, confirm closure. Purple team feeds the ADAPT FORTIFY phase, which feeds the next purple team exercise. It's a flywheel that gets faster with every iteration.

But this exercise gave me something more than detection improvements. It gave me the target: Meridian Consulting Group, Cyprus. The financial heart of PHANTOM MERCY.

---

## 12.11 What Clara Knew

**2026-02-18T10:00:00Z -- My apartment. Sun is fully up. I should eat something.**

I keep going back to her note. "The money trail is the weakness."

She didn't say "follow the money" -- that's what everyone says. She said "the money trail is the *weakness*." She wasn't telling me to investigate their finances. She was telling me that their financial infrastructure is the single point of failure. Kill it and the whole operation collapses.

PHANTOM MERCY can rotate their C2 domains in minutes. They can find new maintainers to recruit. They can publish new dependency confusion packages overnight. But they can't easily replace their financial infrastructure. Bank accounts, shell company registrations, cryptocurrency mixing services, payment processor relationships -- these take months to establish and are subject to KYC/AML regulations that leave paper trails.

Clara knew this because she was embedded in their world. She saw how the money moved. She saw the wire transfers from Meridian to the operatives in the field. She saw the cryptocurrency payments for the shadow-relay infrastructure. And she documented all of it before she went dark.

The purple team exercise confirmed what she already knew: PHANTOM MERCY's technical operations are sophisticated, distributed, and resilient. Their financial operations are centralized, brittle, and traceable.

Now I need to find Clara. And the OSINT module is going to help me do it.

---

## 12.12 Lessons Learned

**1. Score the gap, not the absolute values.** An attack score of 10.0 and a defense score of 0.0 in the trusted insider category is more important than five categories with small gaps. The catastrophic failures are where the budget needs to go.

**2. Technical controls can't catch everything.** The maintainer takeover vector has no technical detection. You need HUMINT, corporate due diligence, and code signing to address it. Not every security problem has a technical solution.

**3. The attacker has weaknesses too.** Purple team is usually about finding *your* weaknesses. But BROKEN MERCY showed me PHANTOM MERCY's weakness -- their centralized financial infrastructure. Offensive purple team (simulating the adversary to find *their* vulnerabilities) is an underused technique.

**4. Clara's field intelligence was better than any automated tool.** She identified the financial SPOF through months of embedded observation. No SBOM scanner, no SIGMA rule, no AI model would have found it. Human intelligence amplified by technical tools is still the most powerful combination in defense.

**5. Detection without containment is detection without value.** We detected DNS tunneling in 7 minutes but didn't block it for 12. In those 5 extra minutes, 47 manifests were exfiltrated. MTTR matters more than MTTD.

---

## 12.13 Quick Reference

| Operation | Endpoint | Method |
|-----------|----------|--------|
| Create exercise | `/api/v1/purple-team/create` | POST |
| List exercises | `/api/v1/purple-team` | GET |
| Get exercise | `/api/v1/purple-team/{id}` | GET |
| Add objective | `/api/v1/purple-team/{id}/objectives` | POST |
| List objectives | `/api/v1/purple-team/{id}/objectives` | GET |
| Add finding | `/api/v1/purple-team/{id}/findings` | POST |
| List findings | `/api/v1/purple-team/{id}/findings` | GET |
| Add score | `/api/v1/purple-team/{id}/scores` | POST |
| List scores | `/api/v1/purple-team/{id}/scores` | GET |
| Get stats | `/api/v1/purple-team/stats` | GET |
| Create range scenario | `/api/v1/cyberrange/scenarios` | POST |
| List range scenarios | `/api/v1/cyberrange/scenarios` | GET |

---

*Next chapter: OSINT Deep Dive -- where I use every open-source intelligence technique in Playseat to find Clara's trail.*

---

`© 2026 Playseat — All Rights Reserved | Defensive Intelligence Through ADAPT`
