# Chapter 5: War Room Masterclass -- Profiling PHANTOM MERCY

**Playseat Advanced Field Manual -- Book 2**
**The Enemy Is Not Who You Think They Are**

---

> "You can map any adversary if you understand what they protect."
> -- Clara Dubois, FIRST Conference, Amsterdam, November 2024. She was talking about threat modeling. She was talking about everything.

---

## 5.1 -- The Morning After

**2026-02-18 | 09:15 CET | Playseat Operations Center**

I haven't slept. The coffee is cold and I've lost count of the cups. Clara's evidence vault is still open on my screen -- 48 exhibits, three prosecution packages, all verified, all intact. The ANSSI contact told me they'd send a team. They haven't arrived yet.

I can't just sit here.

I know what Clara would do. She wouldn't wait for the cavalry. She'd use the waiting time to understand the enemy. She'd build a profile. She'd map every technique, every pattern, every weakness in their operational security. She'd walk into the War Room and not come out until she could predict their next move.

So that's what I'm going to do. I'm going to use Playseat's War Room to build a complete adversary profile for PHANTOM MERCY. Not the trafficking network itself -- that's Clara's evidence, and ANSSI can handle the prosecution. I'm profiling the cyber operations arm. The APT that provided PHANTOM MERCY with technical capabilities: compromised humanitarian networks, intercepted communications, corrupted databases, destroyed evidence.

The APT that might have helped them find Clara.

---

## 5.2 -- What the War Room Actually Is

I need to clear something up first, because the name trips people up. The ADAPT War Room is not a physical room. It's not a Slack channel. It's a module inside Playseat that lets you load an adversary profile -- or create one from scratch -- and then systematically answer the question: "If this adversary targets us, where exactly do we get owned?"

That's the entire point. Not threat modeling in the abstract. Not drawing attack trees on a whiteboard. Actually loading a specific adversary's known TTPs, mapping them against your detection and prevention coverage, identifying the gaps, and producing a remediation roadmap with owners and deadlines.

I've sat through too many tabletop exercises where a facilitator reads a scenario out loud, people nod and say "we would do X," then everyone goes back to their desks and nothing changes. The War Room is the opposite. When it tells you that PHANTOM MERCY's T1059.001 (PowerShell execution) hits a detection gap in your environment, that's not a theoretical concern. That's a line item on a work order.

The War Room is built on four database tables: `adapt_adversary_profiles`, `adapt_adversary_techniques`, `adapt_technique_coverage`, and `adapt_simulation_runs`. Everything flows from profile to technique to coverage to simulation. Straightforward relational modeling. No magic.

Today I'm not running a tabletop exercise. I'm hunting.

---

## 5.3 -- Creating the PHANTOM MERCY Profile

The seed profiles in Playseat cover major known threat groups -- APT-29, APT-41, FIN7, Lazarus Group. PHANTOM MERCY isn't in there. Nobody's published a profile for a trafficking network's cyber operations arm, because nobody's connected the dots yet.

Clara did. Her evidence told me what this group does. Now I'm going to formalize it.

### The Profile Schema

```sql
-- Schema: adapt_adversary_profiles
CREATE TABLE IF NOT EXISTS adapt_adversary_profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL UNIQUE,
    aliases TEXT[] DEFAULT '{}',
    origin_country TEXT,
    motivation TEXT NOT NULL CHECK (motivation IN ('espionage','financial','disruption','hacktivism','unknown')),
    sophistication TEXT NOT NULL CHECK (sophistication IN ('nation-state','advanced','intermediate','basic')),
    target_sectors TEXT[] DEFAULT '{}',
    description TEXT,
    active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

### Creating the Profile

```bash
curl -X POST http://localhost:3000/api/v1/adapt/adversaries \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "PHANTOM MERCY",
    "aliases": ["PM-APT", "GhostAid", "MIRAGE CORRIDOR"],
    "origin_country": "Unknown - Multi-national with state protection",
    "motivation": "financial",
    "sophistication": "advanced",
    "target_sectors": ["humanitarian", "government", "ngo", "border_control", "telecommunications"],
    "description": "Cyber operations arm of transnational trafficking network. Uses compromised humanitarian aid infrastructure as operational cover. Capabilities include network infiltration, communications interception, evidence destruction, and counter-intelligence. Assessed as having access to state-level resources through corrupt official relationships. Operational since at least 2023 based on infrastructure registration dates. Primary mission: protect trafficking logistics, destroy evidence, identify and neutralize investigators."
  }'
```

```json
{
  "id": "01949abc-pm00-7000-8000-00000000pm00"
}
```

I paused after typing the description. *"Identify and neutralize investigators."* That's what they may have done to Clara. I'm profiling the entity that might have disappeared the woman I love.

My hands were steady. You learn that. You learn to keep your hands steady when your chest is on fire.

### Verifying the Profile

```bash
PROFILE_ID="01949abc-pm00-7000-8000-00000000pm00"

curl -s http://localhost:3000/api/v1/adapt/adversaries/$PROFILE_ID \
  -H "Authorization: Bearer $TOKEN" | jq .
```

```json
{
  "id": "01949abc-pm00-7000-8000-00000000pm00",
  "name": "PHANTOM MERCY",
  "aliases": ["PM-APT", "GhostAid", "MIRAGE CORRIDOR"],
  "origin_country": "Unknown - Multi-national with state protection",
  "motivation": "financial",
  "sophistication": "advanced",
  "target_sectors": ["humanitarian", "government", "ngo", "border_control", "telecommunications"],
  "description": "Cyber operations arm of transnational trafficking network...",
  "active": true,
  "created_at": "2026-02-18T08:15:00Z",
  "updated_at": "2026-02-18T08:15:00Z"
}
```

Active. Yes, they're active. That's the whole problem.

---

## 5.4 -- MITRE ATT&CK Technique Mapping

Every adversary profile links to techniques in `adapt_adversary_techniques`. These map directly to MITRE ATT&CK. I built PHANTOM MERCY's technique map from Clara's evidence -- her PCAPs, her malware samples, her network analysis, her behavioral observations documented across 48 exhibits.

```bash
# Add techniques - Initial Access
curl -X POST http://localhost:3000/api/v1/adapt/adversaries/$PROFILE_ID/techniques \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "technique_id": "T1195.002",
    "technique_name": "Compromise Software Supply Chain",
    "tactic": "initial-access",
    "platform": "linux",
    "severity": "critical",
    "description": "Compromises humanitarian aid management software update mechanisms. Injects backdoors into aid distribution platform updates. Clara documented this in EX-014: modified update packages for three separate aid management platforms."
  }'

# Execution
curl -X POST http://localhost:3000/api/v1/adapt/adversaries/$PROFILE_ID/techniques \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "technique_id": "T1059.001",
    "technique_name": "PowerShell",
    "tactic": "execution",
    "platform": "windows",
    "severity": "critical",
    "description": "Encoded PowerShell used for post-compromise execution on Windows-based aid coordination servers. Base64-encoded download cradles observed in Clara EX-027."
  }'

# Persistence
curl -X POST http://localhost:3000/api/v1/adapt/adversaries/$PROFILE_ID/techniques \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "technique_id": "T1078.002",
    "technique_name": "Domain Accounts",
    "tactic": "persistence",
    "platform": "windows",
    "severity": "critical",
    "description": "Hijacks legitimate aid worker domain accounts for persistent access. Particularly targets accounts with VPN access to multiple field offices. Clara noted in EX-031 that 7 compromised accounts were used across 3 organizations."
  }'

# Credential Access
curl -X POST http://localhost:3000/api/v1/adapt/adversaries/$PROFILE_ID/techniques \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "technique_id": "T1003.001",
    "technique_name": "LSASS Memory",
    "tactic": "credential-access",
    "platform": "windows",
    "severity": "critical",
    "description": "Credential harvesting from LSASS process memory on compromised aid coordination servers. Memory dumps found on Clara staging server EX-031. Custom credential harvester, not Mimikatz -- bespoke tooling."
  }'

# Defense Evasion
curl -X POST http://localhost:3000/api/v1/adapt/adversaries/$PROFILE_ID/techniques \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "technique_id": "T1070.004",
    "technique_name": "File Deletion",
    "tactic": "defense-evasion",
    "platform": "linux",
    "severity": "high",
    "description": "Systematic deletion of log files and evidence artifacts on compromised systems. Clara documented in EX-035 that PM wiped access logs within 4 hours of any investigative query touching their infrastructure. They have someone watching the logs."
  }'

# Lateral Movement
curl -X POST http://localhost:3000/api/v1/adapt/adversaries/$PROFILE_ID/techniques \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "technique_id": "T1021.001",
    "technique_name": "Remote Desktop Protocol",
    "tactic": "lateral-movement",
    "platform": "windows",
    "severity": "high",
    "description": "Uses RDP with stolen credentials to move between aid organization field offices. Leverages legitimate VPN tunnels. Traffic blends with normal remote worker patterns -- difficult to distinguish from authorized access."
  }'

# Collection
curl -X POST http://localhost:3000/api/v1/adapt/adversaries/$PROFILE_ID/techniques \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "technique_id": "T1114.002",
    "technique_name": "Remote Email Collection",
    "tactic": "collection",
    "platform": "windows",
    "severity": "high",
    "description": "Harvests email from aid worker mailboxes. Specifically targets investigators, auditors, and anyone with oversight responsibilities. Clara flagged in EX-039 that her own email was accessed 3 times before she switched to out-of-band communication."
  }'

# Command and Control
curl -X POST http://localhost:3000/api/v1/adapt/adversaries/$PROFILE_ID/techniques \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "technique_id": "T1071.001",
    "technique_name": "Web Protocols",
    "tactic": "command-and-control",
    "platform": "linux",
    "severity": "high",
    "description": "C2 traffic disguised as legitimate HTTPS to cloud CDN endpoints. Uses domain fronting through legitimate humanitarian organization websites. Extremely difficult to detect without TLS inspection of aid traffic, which most organizations refuse to do for privacy reasons."
  }'

# Exfiltration
curl -X POST http://localhost:3000/api/v1/adapt/adversaries/$PROFILE_ID/techniques \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "technique_id": "T1048.002",
    "technique_name": "Exfiltration Over Asymmetric Encrypted Non-C2 Protocol",
    "tactic": "exfiltration",
    "platform": "linux",
    "severity": "critical",
    "description": "Exfiltrates investigator data and internal communications through DNS-over-HTTPS tunnels. Volume is low but targeted -- they are not stealing bulk data, they are stealing investigation progress. They want to know who is looking at them."
  }'

# Impact
curl -X POST http://localhost:3000/api/v1/adapt/adversaries/$PROFILE_ID/techniques \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "technique_id": "T1485",
    "technique_name": "Data Destruction",
    "tactic": "impact",
    "platform": "linux",
    "severity": "critical",
    "description": "Destroys evidence on compromised systems when investigation activity is detected. Clara documented in EX-042 a case where an entire PostgreSQL database of beneficiary records was wiped 6 hours after an auditor queried it for anomalies. The database contained records that could have identified victims."
  }'
```

### Pull the Full Technique Map

```bash
curl -s http://localhost:3000/api/v1/adapt/adversaries/$PROFILE_ID/techniques \
  -H "Authorization: Bearer $TOKEN" | jq '.[] | {technique_id, technique_name, tactic, severity}'
```

```json
{"technique_id": "T1195.002", "technique_name": "Compromise Software Supply Chain", "tactic": "initial-access", "severity": "critical"}
{"technique_id": "T1059.001", "technique_name": "PowerShell", "tactic": "execution", "severity": "critical"}
{"technique_id": "T1078.002", "technique_name": "Domain Accounts", "tactic": "persistence", "severity": "critical"}
{"technique_id": "T1003.001", "technique_name": "LSASS Memory", "tactic": "credential-access", "severity": "critical"}
{"technique_id": "T1070.004", "technique_name": "File Deletion", "tactic": "defense-evasion", "severity": "high"}
{"technique_id": "T1021.001", "technique_name": "Remote Desktop Protocol", "tactic": "lateral-movement", "severity": "high"}
{"technique_id": "T1114.002", "technique_name": "Remote Email Collection", "tactic": "collection", "severity": "high"}
{"technique_id": "T1071.001", "technique_name": "Web Protocols", "tactic": "command-and-control", "severity": "high"}
{"technique_id": "T1048.002", "technique_name": "Exfiltration Over Asymmetric Encrypted Non-C2 Protocol", "tactic": "exfiltration", "severity": "critical"}
{"technique_id": "T1485", "technique_name": "Data Destruction", "tactic": "impact", "severity": "critical"}
```

Ten techniques across ten tactics. A complete kill chain. And this is just what Clara documented -- the real list is almost certainly longer.

The SQL that orders them by kill chain position:

```sql
SELECT id, profile_id, technique_id, technique_name, tactic, platform, severity, description, created_at
FROM adapt_adversary_techniques
WHERE profile_id = '01949abc-pm00-7000-8000-00000000pm00'
ORDER BY
    CASE tactic
        WHEN 'initial-access' THEN 1
        WHEN 'execution' THEN 2
        WHEN 'persistence' THEN 3
        WHEN 'credential-access' THEN 4
        WHEN 'defense-evasion' THEN 5
        WHEN 'lateral-movement' THEN 6
        WHEN 'collection' THEN 7
        WHEN 'command-and-control' THEN 8
        WHEN 'exfiltration' THEN 9
        WHEN 'impact' THEN 10
    END;
```

When you lay it out like that, the operational pattern is clear. They don't just infiltrate and steal data. They infiltrate, persist, *watch*, and then destroy evidence when they detect an investigation. T1048.002 followed by T1485. They exfiltrate investigator progress, then destroy the evidence the investigator was looking at.

Clara was being hunted while she hunted them. She knew it. EX-039 says they accessed her email three times. That's why she moved to out-of-band communication. That's why she was uploading evidence to Playseat at 3 AM from mobile devices on cellular connections. She was staying one step ahead of a counter-intelligence operation.

She stayed one step ahead until she didn't.

---

## 5.5 -- The Coverage Matrix: Where We Stand

The coverage matrix is the heart of the War Room. It maps every technique to our detection status: `covered`, `partial`, or `gap`. This is stored in `adapt_technique_coverage`:

```bash
curl -s http://localhost:3000/api/v1/adapt/coverage/matrix \
  -H "Authorization: Bearer $TOKEN" | jq '.[] | select(.technique_id | test("T1195|T1059|T1078|T1003|T1070|T1021|T1114|T1071|T1048|T1485"))'
```

```json
{"technique_id": "T1195.002", "technique_name": "Compromise Software Supply Chain", "tactic": "initial-access", "coverage_status": "gap", "confidence": 0.0}
{"technique_id": "T1059.001", "technique_name": "PowerShell", "tactic": "execution", "coverage_status": "partial", "confidence": 0.55}
{"technique_id": "T1078.002", "technique_name": "Domain Accounts", "tactic": "persistence", "coverage_status": "gap", "confidence": 0.0}
{"technique_id": "T1003.001", "technique_name": "LSASS Memory", "tactic": "credential-access", "coverage_status": "partial", "confidence": 0.40}
{"technique_id": "T1070.004", "technique_name": "File Deletion", "tactic": "defense-evasion", "coverage_status": "gap", "confidence": 0.0}
{"technique_id": "T1021.001", "technique_name": "Remote Desktop Protocol", "tactic": "lateral-movement", "coverage_status": "partial", "confidence": 0.50}
{"technique_id": "T1114.002", "technique_name": "Remote Email Collection", "tactic": "collection", "coverage_status": "gap", "confidence": 0.0}
{"technique_id": "T1071.001", "technique_name": "Web Protocols", "tactic": "command-and-control", "coverage_status": "covered", "confidence": 0.90}
{"technique_id": "T1048.002", "technique_name": "Exfiltration Over Asymmetric Encrypted Non-C2 Protocol", "tactic": "exfiltration", "coverage_status": "gap", "confidence": 0.0}
{"technique_id": "T1485", "technique_name": "Data Destruction", "tactic": "impact", "coverage_status": "partial", "confidence": 0.35}
```

I sat back and looked at the matrix.

Five gaps. Four partial detections. One covered.

If PHANTOM MERCY targeted us tomorrow, we'd see their C2 traffic (90% confidence). We'd *maybe* catch their PowerShell execution, their credential harvesting, their RDP lateral movement, and their data destruction. And we'd be completely blind to their initial access, their persistence, their evidence tampering, their email harvesting, and their exfiltration.

Completely blind.

The cross-reference SQL tells the full story:

```sql
SELECT
    at.technique_id,
    at.technique_name,
    at.tactic,
    at.severity,
    COALESCE(tc.coverage_status, 'gap') AS coverage_status,
    COALESCE(tc.confidence, 0.0) AS confidence,
    tc.detection_source,
    tc.last_tested
FROM adapt_adversary_techniques at
LEFT JOIN adapt_technique_coverage tc ON tc.technique_id = at.technique_id
WHERE at.profile_id = '01949abc-pm00-7000-8000-00000000pm00'
ORDER BY
    CASE COALESCE(tc.coverage_status, 'gap')
        WHEN 'gap' THEN 1 WHEN 'partial' THEN 2 WHEN 'covered' THEN 3
    END,
    CASE at.severity
        WHEN 'critical' THEN 1 WHEN 'high' THEN 2 WHEN 'medium' THEN 3
    END;
```

```
 technique_id | technique_name               | tactic              | severity | coverage | confidence | detection_source
--------------+------------------------------+---------------------+----------+----------+------------+----------------------------
 T1195.002    | Software Supply Chain         | initial-access      | critical | gap      |       0.00 |
 T1078.002    | Domain Accounts              | persistence         | critical | gap      |       0.00 |
 T1048.002    | Encrypted Exfil              | exfiltration        | critical | gap      |       0.00 |
 T1070.004    | File Deletion                | defense-evasion     | high     | gap      |       0.00 |
 T1114.002    | Remote Email Collection      | collection          | high     | gap      |       0.00 |
 T1059.001    | PowerShell                   | execution           | critical | partial  |       0.55 | Sysmon + Sigma rules
 T1003.001    | LSASS Memory                 | credential-access   | critical | partial  |       0.40 | CrowdStrike LSASS alert
 T1485        | Data Destruction             | impact              | critical | partial  |       0.35 | Custom file-integrity monitor
 T1021.001    | Remote Desktop Protocol      | lateral-movement    | high     | partial  |       0.50 | Anomalous RDP detection
 T1071.001    | Web Protocols                | command-and-control | high     | covered  |       0.90 | Zscaler TLS inspection
```

The LEFT JOIN forces techniques with no coverage record to appear as gaps. You can't hide from missing data.

Five of their ten techniques are critical severity and we have zero detection for three of them. This isn't just a bad coverage matrix. This is an invitation.

### Querying Gaps Only

```bash
curl -s http://localhost:3000/api/v1/adapt/coverage/gaps \
  -H "Authorization: Bearer $TOKEN" | jq '.[] | {technique_id, technique_name, tactic, severity}'
```

```json
{"technique_id": "T1195.002", "technique_name": "Compromise Software Supply Chain", "tactic": "initial-access", "severity": "critical"}
{"technique_id": "T1078.002", "technique_name": "Domain Accounts", "tactic": "persistence", "severity": "critical"}
{"technique_id": "T1048.002", "technique_name": "Exfiltration Over Asymmetric Encrypted Non-C2 Protocol", "tactic": "exfiltration", "severity": "critical"}
{"technique_id": "T1070.004", "technique_name": "File Deletion", "tactic": "defense-evasion", "severity": "high"}
{"technique_id": "T1114.002", "technique_name": "Remote Email Collection", "tactic": "collection", "severity": "high"}
```

Five gaps. Three critical. Two high.

If Clara were here, she'd look at that list and say something dry. Something like, "Well, at least we can see their C2. We'll know exactly when they're robbing us."

God, I miss her.

---

## 5.6 -- Running the Simulation: How Bad Is It?

A simulation takes an adversary profile, runs all their techniques against your coverage matrix, and produces a resilience score with specific recommendations.

```bash
curl -X POST http://localhost:3000/api/v1/adapt/adversaries/$PROFILE_ID/simulate \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{}'
```

```json
{
  "id": "01949abc-sim1-7000-8000-00000000sm01",
  "profile_id": "01949abc-pm00-7000-8000-00000000pm00",
  "resilience_score": 0.32,
  "techniques_tested": 10,
  "techniques_detected": 5,
  "techniques_blocked": 1,
  "gap_count": 5,
  "gaps": [
    {
      "technique_id": "T1195.002",
      "technique_name": "Compromise Software Supply Chain",
      "tactic": "initial-access",
      "severity": "critical",
      "recommendation": "Implement software bill of materials (SBOM) verification for all third-party updates. Deploy code-signing verification. Monitor update channels for anomalous package modifications."
    },
    {
      "technique_id": "T1078.002",
      "technique_name": "Domain Accounts",
      "tactic": "persistence",
      "severity": "critical",
      "recommendation": "Deploy identity-based anomaly detection. Implement impossible-travel detection for VPN logins. Require MFA for all domain accounts with cross-site access."
    },
    {
      "technique_id": "T1048.002",
      "technique_name": "Exfiltration Over Asymmetric Encrypted Non-C2 Protocol",
      "tactic": "exfiltration",
      "severity": "critical",
      "recommendation": "Implement DNS-over-HTTPS monitoring. Deploy DLP with encrypted traffic analysis. Monitor for anomalous DNS query patterns."
    },
    {
      "technique_id": "T1070.004",
      "technique_name": "File Deletion",
      "tactic": "defense-evasion",
      "severity": "high",
      "recommendation": "Deploy immutable audit logging. Forward all logs to write-once storage in real-time. Implement file integrity monitoring with tamper alerts."
    },
    {
      "technique_id": "T1114.002",
      "technique_name": "Remote Email Collection",
      "tactic": "collection",
      "severity": "high",
      "recommendation": "Deploy Microsoft 365 Advanced Audit. Monitor for MailItemsAccessed events from unusual IPs. Implement conditional access policies restricting mailbox access by location and device."
    }
  ],
  "recommendations": [
    "CRITICAL: Close T1195.002 gap immediately - this is their primary entry vector into humanitarian networks",
    "CRITICAL: Close T1078.002 gap - stolen domain accounts provide persistent invisible access",
    "CRITICAL: Close T1048.002 gap - they are exfiltrating investigation progress and using it to anticipate our moves",
    "HIGH: Close T1070.004 gap - evidence destruction is their signature move when cornered",
    "HIGH: Close T1114.002 gap - they read investigator email to identify who is looking at them",
    "MEDIUM: Improve T1059.001 detection from partial to covered - PowerShell is their execution workhorse",
    "MEDIUM: Improve T1003.001 detection - bespoke credential harvesters bypass standard Mimikatz signatures",
    "MEDIUM: Improve T1485 detection - data destruction alerts need faster response times"
  ],
  "run_by": "019474a1-b3c2-7000-8000-000000000001",
  "started_at": "2026-02-18T09:30:00Z",
  "completed_at": "2026-02-18T09:30:03Z"
}
```

Resilience score: **0.32**.

Thirty-two percent. We detect or block 32% of PHANTOM MERCY's known techniques.

When I first ran this against APT-29, the score was 0.58 and I thought that was bad. This is catastrophically worse. And the reason is structural: PHANTOM MERCY doesn't operate like a traditional APT. They don't need to be stealthy in the classic sense because they operate inside humanitarian networks where security is thin, budgets are low, and nobody wants to inspect aid worker traffic.

They've optimized their TTPs for an environment with almost no detection. And now I'm looking at our coverage against those TTPs and realizing -- we're not much better than a humanitarian organization. Five full gaps. Four partial detections with confidence below 0.55.

The simulation data persists to `adapt_simulation_runs`:

```sql
SELECT id, profile_id, resilience_score, techniques_tested, techniques_detected,
       techniques_blocked, gap_count, started_at
FROM adapt_simulation_runs
WHERE profile_id = '01949abc-pm00-7000-8000-00000000pm00'
ORDER BY started_at DESC
LIMIT 5;
```

---

## 5.7 -- What-If Analysis: Closing the Gaps

The what-if analysis asks: "What would our resilience score be if we closed these specific gaps?" -- without actually closing them. This is how you prioritize remediation work.

I ran three scenarios.

### Scenario 1: Close the three critical gaps only

```bash
curl -X POST http://localhost:3000/api/v1/adapt/what-if \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "profile_id": "01949abc-pm00-7000-8000-00000000pm00",
    "gaps_to_close": ["T1195.002", "T1078.002", "T1048.002"]
  }'
```

```json
{
  "profile_id": "01949abc-pm00-7000-8000-00000000pm00",
  "current_resilience": 0.32,
  "projected_resilience": 0.62,
  "improvement": 0.30,
  "gaps_closed": ["T1195.002", "T1078.002", "T1048.002"],
  "remaining_gaps": ["T1070.004", "T1114.002"],
  "remaining_partial": ["T1059.001", "T1003.001", "T1021.001", "T1485"],
  "recommendation": "Closing these 3 critical gaps would provide a 30 percentage point improvement. This addresses the primary entry vector, persistence mechanism, and data exfiltration channel."
}
```

Thirty-point improvement. From 0.32 to 0.62. Not great, but survivable.

### Scenario 2: Close all five gaps

```bash
curl -X POST http://localhost:3000/api/v1/adapt/what-if \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "profile_id": "01949abc-pm00-7000-8000-00000000pm00",
    "gaps_to_close": ["T1195.002", "T1078.002", "T1048.002", "T1070.004", "T1114.002"]
  }'
```

```json
{
  "profile_id": "01949abc-pm00-7000-8000-00000000pm00",
  "current_resilience": 0.32,
  "projected_resilience": 0.75,
  "improvement": 0.43,
  "gaps_closed": ["T1195.002", "T1078.002", "T1048.002", "T1070.004", "T1114.002"],
  "remaining_gaps": [],
  "remaining_partial": ["T1059.001", "T1003.001", "T1021.001", "T1485"],
  "recommendation": "Closing all 5 gaps eliminates blind spots and raises resilience to 0.75. Remaining risk is in partial detections that need confidence improvement."
}
```

From 0.32 to 0.75. Forty-three-point improvement. No remaining gaps, but four partial detections still need work.

### Scenario 3: The full hardening -- close all gaps and upgrade all partials

This is the scenario I care about. If we're going to go after PHANTOM MERCY -- if we're going to find Clara -- we need to be invisible to them while we do it. That means full coverage.

```bash
curl -X POST http://localhost:3000/api/v1/adapt/what-if \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "profile_id": "01949abc-pm00-7000-8000-00000000pm00",
    "gaps_to_close": ["T1195.002", "T1078.002", "T1048.002", "T1070.004", "T1114.002", "T1059.001", "T1003.001", "T1021.001", "T1485"]
  }'
```

```json
{
  "profile_id": "01949abc-pm00-7000-8000-00000000pm00",
  "current_resilience": 0.32,
  "projected_resilience": 0.95,
  "improvement": 0.63,
  "gaps_closed": ["T1195.002", "T1078.002", "T1048.002", "T1070.004", "T1114.002", "T1059.001", "T1003.001", "T1021.001", "T1485"],
  "remaining_gaps": [],
  "remaining_partial": [],
  "recommendation": "Full coverage achieved. 95% resilience means only novel zero-day techniques would bypass detection. This is the target posture for active counter-operations."
}
```

0.95. Ninety-five percent. The remaining 5% represents novel techniques we haven't mapped yet. That's acceptable. That's what active threat hunting is for.

---

## 5.8 -- The Simulation I Didn't Want to Run

**2026-02-18 | 10:45 CET**

I've been avoiding this. But the War Room is about confronting uncomfortable truths, and the most uncomfortable truth is one I need to model.

*What happens if Clara's cover was blown?*

I'm going to model this as a what-if against Clara's operational signature -- her patterns of Playseat access, her communication channels, her field locations. Not because I want to. Because I need to understand what PHANTOM MERCY might have seen, and what they might have done about it.

I created a secondary profile: PHANTOM MERCY's counter-intelligence operation targeting Clara specifically.

```bash
curl -X POST http://localhost:3000/api/v1/adapt/adversaries \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "PHANTOM MERCY - CI OPS",
    "aliases": ["PM-CI", "GHOST HUNTER"],
    "origin_country": "Unknown",
    "motivation": "espionage",
    "sophistication": "advanced",
    "target_sectors": ["intelligence", "law_enforcement"],
    "description": "Counter-intelligence branch of PHANTOM MERCY, specifically tasked with identifying and neutralizing investigators. Operates on investigator communications, operational patterns, and institutional contacts."
  }'
```

```json
{
  "id": "01949abc-pmci-7000-8000-00000000pmci"
}
```

I mapped the techniques they'd use against an undercover investigator:

```bash
CI_PROFILE="01949abc-pmci-7000-8000-00000000pmci"

# T1114.002 - Email monitoring of investigator accounts
# T1557.001 - LLMNR/NBT-NS Poisoning (to intercept local network auth on field networks)
# T1040 - Network Sniffing (to capture investigator HTTPS traffic)
# T1056.001 - Keylogging
# T1120 - Peripheral Device Discovery (to detect evidence collection devices)
# T1497.001 - System Checks (to detect forensic tools on investigator workstations)
```

Then I ran the simulation. Not against our infrastructure. Against the operational security posture of a single undercover officer working inside a hostile network.

```bash
curl -X POST http://localhost:3000/api/v1/adapt/adversaries/$CI_PROFILE/simulate \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{}'
```

```json
{
  "id": "01949abc-sim2-7000-8000-00000000sm02",
  "profile_id": "01949abc-pmci-7000-8000-00000000pmci",
  "resilience_score": 0.15,
  "techniques_tested": 6,
  "techniques_detected": 1,
  "techniques_blocked": 0,
  "gap_count": 5,
  "gaps": [
    {
      "technique_id": "T1040",
      "technique_name": "Network Sniffing",
      "tactic": "credential-access",
      "severity": "critical",
      "recommendation": "Investigator must use end-to-end encrypted channels for ALL communications. Assume all local network traffic is monitored."
    },
    {
      "technique_id": "T1056.001",
      "technique_name": "Keylogging",
      "tactic": "collection",
      "severity": "critical",
      "recommendation": "Use hardware tokens for authentication. Never type passwords on potentially compromised systems."
    },
    {
      "technique_id": "T1120",
      "technique_name": "Peripheral Device Discovery",
      "tactic": "discovery",
      "severity": "high",
      "recommendation": "Evidence collection devices must be physically indistinguishable from standard personal electronics."
    }
  ],
  "recommendations": [
    "CRITICAL: Individual operator OPSEC is insufficient against a dedicated CI team with local network access",
    "CRITICAL: Evidence collection over ANY network the adversary controls is inherently compromising",
    "HIGH: The investigator's access pattern to external systems creates a detectable signature"
  ],
  "run_by": "019474a1-b3c2-7000-8000-000000000001",
  "started_at": "2026-02-18T10:45:00Z",
  "completed_at": "2026-02-18T10:45:02Z"
}
```

Resilience score: **0.15**.

Fifteen percent. A solo operator, no matter how skilled, operating inside a hostile network controlled by an adversary with counter-intelligence capability, has a 15% resilience score against detection.

I stared at that number for a long time.

Clara's late-night uploads. The 3 AM sessions. The cellular connections. The minimal operational footprint. She was doing everything right -- and the model says she still had only a 15% chance of remaining undetected over a three-month collection window.

The recommendation line hit me like a punch: *"Evidence collection over ANY network the adversary controls is inherently compromising."*

She knew. She must have known. Every time she connected to Playseat from a field location, she was creating a detectable signature. She did it anyway, because the evidence was more important than her safety.

That's who Clara is.

I closed the simulation window. I needed a minute.

---

## 5.9 -- Building the Remediation Roadmap

**2026-02-18 | 11:30 CET**

I'm back. Minutes are for humans. The War Room doesn't wait.

Based on the three what-if analyses, here's the remediation roadmap for hardening our posture against PHANTOM MERCY:

| Priority | Gap | Technique | Owner | Deadline | Expected Impact | Status |
|----------|-----|-----------|-------|----------|-----------------|--------|
| 1 | T1048.002 | Encrypted Exfiltration | Network Team | Feb 21 | +10 points | **Urgent** -- they're watching |
| 2 | T1195.002 | Supply Chain Compromise | DevSecOps | Feb 23 | +10 points | SBOM verification |
| 3 | T1078.002 | Domain Account Abuse | Identity Team | Feb 25 | +10 points | MFA + impossible travel |
| 4 | T1114.002 | Email Collection | Cloud Security | Feb 26 | +7 points | M365 Advanced Audit |
| 5 | T1070.004 | Evidence Tampering | Platform Team | Feb 27 | +6 points | Immutable logging |
| 6 | T1059.001 | PowerShell (partial) | Endpoint Team | Feb 22 | +4 points | Script block logging |
| 7 | T1003.001 | LSASS Memory (partial) | Endpoint Team | Feb 22 | +3 points | Credential Guard |
| 8 | T1021.001 | RDP (partial) | Network Team | Feb 24 | +2 points | Jump server + NLA |
| 9 | T1485 | Data Destruction (partial) | Platform Team | Feb 28 | +1 point | Immutable backups |

T1048.002 is first. Not because it has the highest impact per point, but because if PHANTOM MERCY is monitoring our investigation progress, every hour we spend unprotected on that technique is an hour they know what we're doing. That exfiltration channel has to die first.

---

## 5.10 -- Integration with the ADAPT Cycle

The War Room feeds directly into ADAPT's five-phase cycle. This isn't a standalone tool -- it drives the entire defensive posture improvement loop.

### DISCOVER Phase

War Room gaps become ADAPT exposure events:

```sql
SELECT ae.event_type, ae.severity, ae.details->>'technique_id' AS gap, ae.details->>'source' AS source
FROM adapt_exposure_events ae
WHERE ae.details->>'source' = 'war_room_simulation'
AND ae.details->>'profile_name' = 'PHANTOM MERCY';
```

### FORTIFY Phase

Recommendations generate defense actions:

```sql
SELECT da.action_type, da.status, da.details->>'technique_id' AS technique
FROM adapt_defense_actions da
WHERE da.details->>'adversary' = 'PHANTOM MERCY'
ORDER BY da.created_at;
```

```
 action_type      | status  | technique
------------------+---------+-----------
 dns_monitoring   | pending | T1048.002
 sbom_verification| pending | T1195.002
 identity_mfa     | pending | T1078.002
 email_audit      | pending | T1114.002
 immutable_logs   | pending | T1070.004
 detection_rule   | pending | T1059.001
 credential_guard | pending | T1003.001
 rdp_restriction  | pending | T1021.001
 backup_policy    | pending | T1485
```

Nine defense actions. All pending. All mine.

### PROVE Phase

After remediation, PROVE verifies by re-running the simulation. If the resilience score improves from 0.32 to 0.95, the cycle worked. If not, we go back to FORTIFY.

This is the loop Clara would have wanted. Discover the threat. Map it. Fortify against it. Prove the fortification works. Repeat.

---

## 5.11 -- The War Room Summary

```bash
curl -s http://localhost:3000/api/v1/adapt/war-room/summary \
  -H "Authorization: Bearer $TOKEN" | jq .
```

```json
{
  "total_profiles": 6,
  "total_techniques": 34,
  "coverage_covered": 11,
  "coverage_partial": 12,
  "coverage_gap": 11,
  "average_resilience": 0.51,
  "latest_simulations": [
    {
      "id": "01949abc-sim1-7000-8000-00000000sm01",
      "profile_id": "01949abc-pm00-7000-8000-00000000pm00",
      "resilience_score": 0.32,
      "techniques_tested": 10,
      "techniques_detected": 5,
      "techniques_blocked": 1,
      "gap_count": 5,
      "started_at": "2026-02-18T09:30:00Z"
    },
    {
      "id": "01949abc-sim2-7000-8000-00000000sm02",
      "profile_id": "01949abc-pmci-7000-8000-00000000pmci",
      "resilience_score": 0.15,
      "techniques_tested": 6,
      "techniques_detected": 1,
      "techniques_blocked": 0,
      "gap_count": 5,
      "started_at": "2026-02-18T10:45:00Z"
    }
  ]
}
```

Six adversary profiles now. Thirty-four techniques mapped. Average resilience of 0.51. But the average lies -- against our worst-case adversary (PHANTOM MERCY CI operations), we're at 0.15.

---

## 5.12 -- Multi-Adversary Analysis: PHANTOM MERCY in Context

The real power of the War Room shows up when you compare across adversary profiles:

```sql
SELECT
    at.technique_id,
    at.technique_name,
    COUNT(DISTINCT at.profile_id) AS adversary_count,
    STRING_AGG(DISTINCT ap.name, ', ') AS used_by,
    COALESCE(tc.coverage_status, 'gap') AS status,
    COALESCE(tc.confidence, 0.0) AS confidence
FROM adapt_adversary_techniques at
JOIN adapt_adversary_profiles ap ON ap.id = at.profile_id
LEFT JOIN adapt_technique_coverage tc ON tc.technique_id = at.technique_id
GROUP BY at.technique_id, at.technique_name, tc.coverage_status, tc.confidence
HAVING COALESCE(tc.coverage_status, 'gap') != 'covered'
ORDER BY COUNT(DISTINCT at.profile_id) DESC;
```

```
 technique_id | technique_name         | adversary_count | used_by                               | status  | confidence
--------------+------------------------+-----------------+---------------------------------------+---------+-----------
 T1059.001    | PowerShell             |               4 | APT-29, APT-41, FIN7, PHANTOM MERCY  | partial |       0.55
 T1078.002    | Domain Accounts        |               3 | APT-29, Lazarus, PHANTOM MERCY        | gap     |       0.00
 T1003.001    | LSASS Memory           |               3 | APT-29, APT-41, PHANTOM MERCY         | partial |       0.40
 T1048.002    | Encrypted Exfil        |               2 | APT-29, PHANTOM MERCY                 | gap     |       0.00
 T1195.002    | Supply Chain           |               2 | APT-41, PHANTOM MERCY                 | gap     |       0.00
 T1485        | Data Destruction       |               2 | Lazarus, PHANTOM MERCY                | partial |       0.35
```

PHANTOM MERCY shares techniques with every major APT group in our database. T1059.001 (PowerShell) is used by 4 of 6 profiles and we only have partial detection. T1078.002 (Domain Accounts) is used by 3 and we have zero detection.

The overlap tells us something important: fixing our gaps against PHANTOM MERCY simultaneously improves our posture against APT-29, APT-41, Lazarus, and FIN7. The remediation roadmap isn't just about one adversary -- it's about raising the floor for everything.

---

## 5.13 -- The Collaborative Workspace

I created a War Room workspace for this investigation. Not because I have a team right now -- I'm working alone. Because when ANSSI arrives, when the investigation expands, the workspace becomes the institutional memory of everything we've done.

```bash
curl -X POST http://localhost:3000/api/v1/adapt/collab/workspaces \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "War Room: PHANTOM MERCY Defense Assessment - Feb 18 2026",
    "description": "Complete adversary profile, coverage analysis, simulation results, and remediation roadmap for PHANTOM MERCY APT. Initiated after discovery of Clara Dubois evidence vault."
  }'
```

```bash
WS_ID="01949abc-ws01-7000-8000-00000000ws01"

# Save the critical gap query to the workspace
curl -X POST http://localhost:3000/api/v1/adapt/collab/workspaces/$WS_ID/queries \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "query_type": "sql",
    "query_text": "SELECT at.technique_id, at.technique_name, at.severity, COALESCE(tc.coverage_status, '\''gap'\'') AS status FROM adapt_adversary_techniques at LEFT JOIN adapt_technique_coverage tc ON tc.technique_id = at.technique_id WHERE at.profile_id = '\''01949abc-pm00-7000-8000-00000000pm00'\'' AND COALESCE(tc.coverage_status, '\''gap'\'') != '\''covered'\'' ORDER BY at.severity DESC",
    "description": "PHANTOM MERCY uncovered techniques - sorted by severity for remediation prioritization"
  }'
```

When ANSSI walks through that door, I'll hand them the workspace ID and they'll have everything: the adversary profile, the technique mapping, the coverage gaps, the simulation results, the what-if analyses, and the remediation roadmap.

Evidence-based. Reproducible. Verifiable.

Exactly how Clara would have wanted it.

---

## 5.14 -- Lessons from This War Room Session

I've run War Room sessions for APT-29, APT-41, FIN7, and Lazarus Group. This one was different. Not because the methodology changed -- the methodology is the same regardless of the adversary. It was different because the adversary is personal.

But the lessons still apply.

**The score matters less than the trend.** Our 0.32 is terrifying. But once we close the gaps, we'll re-simulate and that number will climb. The trend is what the CISO presents to the board: "We identified a critical adversary with a 0.32 resilience score. Within two weeks, we project 0.95."

**Focus on technique overlap.** PHANTOM MERCY shares techniques with every major APT in our database. Fixing one adversary's gaps fixes everyone's. That's the efficiency argument for War Room-driven remediation.

**Partial coverage is a trap.** A confidence of 0.40 on LSASS Memory detection means we catch it 40% of the time. PHANTOM MERCY uses bespoke tools, not Mimikatz. Our partial detection is almost certainly optimistic against their specific implementation.

**The counter-intelligence simulation was the most important one.** A 0.15 resilience score for a solo operator against a dedicated CI team isn't a failure of the operator. It's a failure of the operational model. No individual should be operating at that risk level without real-time monitoring and extraction capability.

Clara didn't have that. She had a JWT token and a curl command.

**Run the session when it matters, not on a schedule.** I didn't run this because it was the third Tuesday of the month. I ran it because I found evidence that a woman I love had been fighting alone against an adversary I hadn't even profiled. The War Room isn't a compliance checkbox. It's a weapon. Use it when you need it.

**Record everything in the platform.** Every simulation, every what-if, every remediation decision. When the investigation reaches a courtroom -- and it will reach a courtroom -- the War Room data becomes part of the prosecution's evidence chain. These simulations are dual-hashed just like everything else in Playseat.

Clara once told me, in Amsterdam, walking along the Keizersgracht at midnight: "You can map any adversary if you understand what they protect."

PHANTOM MERCY protects a trafficking network. They protect the routes, the money, and the officials who look the other way. Everything they do -- every technique, every tool, every operational pattern -- serves that protection.

I understand what they protect now.

And I know how to take it apart.

---

*Next chapter: "Threat Genome -- Clara's DNA Fingerprint"*

---

(c) 2026 Playseat -- All Rights Reserved | Defensive Intelligence Through ADAPT
