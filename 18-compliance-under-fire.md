# Chapter 18: Passing Audits While Under Attack

Let me tell you about the worst Tuesday of 2025. We were three days into a SOC 2
Type II audit when our EDR flagged lateral movement across the finance network.
Ransomware. Active. Moving fast. And the auditor was sitting in the conference
room next door, waiting for me to walk through our access control evidence.

Most organizations treat compliance and incident response as separate concerns.
The compliance team maintains their control matrices in SharePoint. The IR team
runs their playbooks in a different system entirely. And when both happen
simultaneously -- which they will, because threat actors do not check your audit
schedule -- the result is chaos. People scramble to collect evidence that
satisfies both the auditor and the incident commander, often collecting it twice,
in different formats, with different chains of custody.

Playseat solves this by unifying compliance management with the operational
platform. The same evidence that feeds your incident investigation also feeds
your compliance controls. The same audit trail that the auditor reviews is the
same audit trail that the IR team relies on. There is one source of truth, and
it serves both purposes simultaneously.

This chapter walks through the complete compliance automation system: framework
management, control mapping, automated assessments, gap analysis, and -- most
critically -- how to maintain compliance posture during an active incident.

---

## The Compliance Data Model

The compliance mapping module manages frameworks, controls, and the relationships
between them:

```sql
-- Frameworks: NIST 800-53, ISO 27001, SOC 2, GDPR, etc.
CREATE TABLE IF NOT EXISTS compliance_auto_frameworks (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name            TEXT NOT NULL,
    version         TEXT NOT NULL,
    authority       TEXT NOT NULL,
    description     TEXT NOT NULL DEFAULT '',
    total_controls  INTEGER NOT NULL DEFAULT 0,
    status          TEXT NOT NULL DEFAULT 'active',
    created_by      UUID,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Controls: individual requirements within a framework
CREATE TABLE IF NOT EXISTS compliance_auto_controls (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    framework_id    UUID NOT NULL REFERENCES compliance_auto_frameworks(id),
    control_code    TEXT NOT NULL,
    title           TEXT NOT NULL,
    description     TEXT NOT NULL DEFAULT '',
    category        TEXT NOT NULL DEFAULT 'general',
    severity        TEXT NOT NULL DEFAULT 'medium',
    implemented     BOOLEAN NOT NULL DEFAULT false,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Mappings: cross-framework control relationships
CREATE TABLE IF NOT EXISTS compliance_auto_mappings (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_control_id   UUID NOT NULL REFERENCES compliance_auto_controls(id),
    target_control_id   UUID NOT NULL REFERENCES compliance_auto_controls(id),
    confidence          DOUBLE PRECISION NOT NULL DEFAULT 0.0,
    mapping_type        TEXT NOT NULL DEFAULT 'manual',
    rationale           TEXT NOT NULL DEFAULT '',
    created_by          UUID,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Assessments: point-in-time compliance evaluations
CREATE TABLE IF NOT EXISTS compliance_auto_assessments (
    id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    framework_id      UUID NOT NULL REFERENCES compliance_auto_frameworks(id),
    assessor          TEXT NOT NULL DEFAULT 'system',
    status            TEXT NOT NULL DEFAULT 'in_progress',
    total_controls    INTEGER NOT NULL DEFAULT 0,
    controls_met      INTEGER NOT NULL DEFAULT 0,
    controls_partial  INTEGER NOT NULL DEFAULT 0,
    controls_not_met  INTEGER NOT NULL DEFAULT 0,
    score             DOUBLE PRECISION NOT NULL DEFAULT 0.0,
    findings          JSONB NOT NULL DEFAULT '{}',
    created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at      TIMESTAMPTZ
);
```

And the SOC 2-specific tables for audit evidence:

```sql
-- SOC 2 controls
CREATE TABLE IF NOT EXISTS soc2_controls (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    control_id  TEXT NOT NULL UNIQUE,
    category    TEXT NOT NULL,
    title       TEXT NOT NULL,
    description TEXT NOT NULL,
    status      TEXT NOT NULL DEFAULT 'not_started',
    tested_at   TIMESTAMPTZ,
    tester      TEXT,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- SOC 2 evidence attachments
CREATE TABLE IF NOT EXISTS soc2_evidence (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    control_id      TEXT NOT NULL,
    title           TEXT NOT NULL,
    description     TEXT NOT NULL,
    evidence_type   TEXT NOT NULL,
    content_hash    TEXT NOT NULL,
    collected_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

The two-tier design is intentional. The `compliance_auto_*` tables handle
cross-framework mapping and assessment (NIST to ISO, SOC 2 to GDPR). The
`soc2_*` tables handle framework-specific evidence collection with content
hashing for integrity verification.

---

## Framework Management

Let me set up the frameworks we need for a typical defense contractor that has
to comply with multiple standards simultaneously:

```bash
# Register NIST 800-53 Rev 5
NIST_ID=$(curl -s -X POST http://localhost:3000/api/v1/compliance-map/frameworks \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "NIST 800-53",
    "version": "Rev 5",
    "authority": "NIST",
    "description": "Security and Privacy Controls for Information Systems and Organizations"
  }' | jq -r '.id')

echo "NIST Framework: $NIST_ID"

# Register SOC 2 Type II
SOC2_ID=$(curl -s -X POST http://localhost:3000/api/v1/compliance-map/frameworks \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "SOC 2 Type II",
    "version": "2024",
    "authority": "AICPA",
    "description": "Trust Services Criteria for Security, Availability, Processing Integrity, Confidentiality, and Privacy"
  }' | jq -r '.id')

# Register ISO 27001
ISO_ID=$(curl -s -X POST http://localhost:3000/api/v1/compliance-map/frameworks \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "ISO 27001",
    "version": "2022",
    "authority": "ISO",
    "description": "Information security management systems - Requirements"
  }' | jq -r '.id')

# Register GDPR
GDPR_ID=$(curl -s -X POST http://localhost:3000/api/v1/compliance-map/frameworks \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "GDPR",
    "version": "2016/679",
    "authority": "European Parliament",
    "description": "General Data Protection Regulation"
  }' | jq -r '.id')
```

List all frameworks to verify:

```bash
curl -s http://localhost:3000/api/v1/compliance-map/frameworks \
  -H "Authorization: Bearer $TOKEN" | jq '.[] | {name, version, authority, total_controls}'
```

```json
{"name": "GDPR", "version": "2016/679", "authority": "European Parliament", "total_controls": 0}
{"name": "ISO 27001", "version": "2022", "authority": "ISO", "total_controls": 0}
{"name": "SOC 2 Type II", "version": "2024", "authority": "AICPA", "total_controls": 0}
{"name": "NIST 800-53", "version": "Rev 5", "authority": "NIST", "total_controls": 0}
```

All frameworks start with zero controls. Let me populate them.

---

## Adding Controls

Controls are the individual requirements within each framework. Here is a
representative sample for NIST 800-53:

```bash
# NIST 800-53 Access Control family
for CTRL in \
  "AC-1|Access Control Policy and Procedures|access_control|high" \
  "AC-2|Account Management|access_control|high" \
  "AC-3|Access Enforcement|access_control|critical" \
  "AC-6|Least Privilege|access_control|high" \
  "AC-7|Unsuccessful Logon Attempts|access_control|medium" \
  "AC-17|Remote Access|access_control|high"; do

  IFS='|' read -r CODE TITLE CATEGORY SEVERITY <<< "$CTRL"

  curl -s -X POST "http://localhost:3000/api/v1/compliance-map/frameworks/$NIST_ID/controls" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d "{
      \"control_code\": \"$CODE\",
      \"title\": \"$TITLE\",
      \"category\": \"$CATEGORY\",
      \"severity\": \"$SEVERITY\"
    }" > /dev/null
done

# NIST Incident Response family
for CTRL in \
  "IR-1|Incident Response Policy|incident_response|high" \
  "IR-4|Incident Handling|incident_response|critical" \
  "IR-5|Incident Monitoring|incident_response|high" \
  "IR-6|Incident Reporting|incident_response|high" \
  "IR-8|Incident Response Plan|incident_response|critical"; do

  IFS='|' read -r CODE TITLE CATEGORY SEVERITY <<< "$CTRL"

  curl -s -X POST "http://localhost:3000/api/v1/compliance-map/frameworks/$NIST_ID/controls" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d "{
      \"control_code\": \"$CODE\",
      \"title\": \"$TITLE\",
      \"category\": \"$CATEGORY\",
      \"severity\": \"$SEVERITY\"
    }" > /dev/null
done

echo "NIST controls loaded."
```

The framework's `total_controls` counter is automatically incremented:

```rust
// Update framework total_controls count
sqlx::query(
    "UPDATE compliance_auto_frameworks SET total_controls = total_controls + 1, \
     updated_at = $1 WHERE id = $2",
)
.bind(now)
.bind(framework_id)
.execute(&state.db)
.await?;
```

Verify the control count:

```bash
curl -s "http://localhost:3000/api/v1/compliance-map/frameworks/$NIST_ID" \
  -H "Authorization: Bearer $TOKEN" | jq '{name, total_controls}'
```

```json
{"name": "NIST 800-53", "total_controls": 11}
```

---

## Cross-Framework Control Mapping

This is where the compliance automation truly shines. A single control
implementation often satisfies requirements across multiple frameworks.
NIST AC-2 (Account Management) maps to SOC 2 CC6.1 (Logical Access Controls),
ISO 27001 A.9.2 (User Access Management), and GDPR Article 32 (Security of
Processing). Instead of implementing and evidencing each one separately, you
map them:

```bash
# First, get the control IDs we need to map
NIST_AC2=$(curl -s "http://localhost:3000/api/v1/compliance-map/frameworks/$NIST_ID/controls" \
  -H "Authorization: Bearer $TOKEN" | jq -r '.[] | select(.control_code=="AC-2") | .id')

SOC2_CC61=$(curl -s "http://localhost:3000/api/v1/compliance-map/frameworks/$SOC2_ID/controls" \
  -H "Authorization: Bearer $TOKEN" | jq -r '.[] | select(.control_code=="CC6.1") | .id')

# Create the mapping
curl -s -X POST http://localhost:3000/api/v1/compliance-map/mappings \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"source_control_id\": \"$NIST_AC2\",
    \"target_control_id\": \"$SOC2_CC61\",
    \"confidence\": 0.92,
    \"mapping_type\": \"manual\",
    \"rationale\": \"NIST AC-2 Account Management directly satisfies SOC 2 CC6.1 logical access controls. Both require user provisioning, deprovisioning, and periodic access review.\"
  }" | jq .
```

```json
{
  "id": "01957000-ff01-7000-8000-000000000001",
  "source_control_id": "01956f00-aa01-7000-8000-000000000002",
  "target_control_id": "01956f00-bb01-7000-8000-000000000012",
  "confidence": 0.92,
  "mapping_type": "manual",
  "rationale": "NIST AC-2 Account Management directly satisfies SOC 2 CC6.1...",
  "created_at": "2026-02-05T10:00:00Z"
}
```

The confidence score (0.92) indicates how strongly the mapping holds. A 0.92
means the controls are nearly equivalent. A 0.5 would mean partial overlap.
Below 0.3, the mapping is probably too weak to rely on.

---

## Auto-Mapping: Heuristic Cross-Framework Correlation

Manually mapping hundreds of controls across four frameworks is tedious. The
auto-map endpoint provides a heuristic starting point:

```bash
curl -s -X POST http://localhost:3000/api/v1/compliance-map/auto-map \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"source_framework_id\": \"$NIST_ID\",
    \"target_framework_id\": \"$SOC2_ID\"
  }" | jq 'length'
```

```
8
```

Eight auto-generated mappings based on category matching. The algorithm is
straightforward:

```rust
for src in &source_controls {
    for tgt in &target_controls {
        if src.category == tgt.category {
            let confidence = if src.severity == tgt.severity {
                0.9
            } else {
                0.5
            };
            // Create the mapping with type 'auto'
        }
    }
}
```

Controls with matching categories get mapped. Same-severity matches get 0.9
confidence; cross-severity matches get 0.5. This is deliberately simple --
the auto-map is a starting point that a human analyst then reviews and refines.
Auto-generated mappings are tagged with `mapping_type: "auto"` so you can
distinguish them from manual expert mappings.

---

## Running Assessments

An assessment is a point-in-time evaluation of your compliance posture against
a specific framework:

```bash
curl -s -X POST http://localhost:3000/api/v1/compliance-map/assessments \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"framework_id\": \"$NIST_ID\",
    \"assessor\": \"analyst-compliance-01\"
  }" | jq .
```

```json
{
  "id": "01957100-aa01-7000-8000-000000000001",
  "framework_id": "01956f00-aa01-7000-8000-000000000001",
  "assessor": "analyst-compliance-01",
  "status": "completed",
  "total_controls": 11,
  "controls_met": 7,
  "controls_partial": 0,
  "controls_not_met": 4,
  "score": 63.6,
  "findings": {
    "summary": "7 of 11 controls met",
    "score_pct": 63.6
  },
  "created_at": "2026-02-05T14:00:00Z",
  "completed_at": "2026-02-05T14:00:00Z"
}
```

63.6% compliance. Not great. The assessment automatically counts implemented
vs. not-implemented controls and generates a score. Let me see what is missing:

```bash
curl -s "http://localhost:3000/api/v1/compliance-map/gap-analysis/$NIST_ID" \
  -H "Authorization: Bearer $TOKEN" | jq .
```

```json
{
  "framework_id": "01956f00-aa01-7000-8000-000000000001",
  "framework_name": "NIST 800-53",
  "total_controls": 11,
  "not_implemented": [
    {"control_code": "AC-7", "title": "Unsuccessful Logon Attempts", "severity": "medium", "implemented": false},
    {"control_code": "AC-17", "title": "Remote Access", "severity": "high", "implemented": false},
    {"control_code": "IR-5", "title": "Incident Monitoring", "severity": "high", "implemented": false},
    {"control_code": "IR-6", "title": "Incident Reporting", "severity": "high", "implemented": false}
  ],
  "gap_pct": 36.4
}
```

Four gaps: unsuccessful logon attempt lockout, remote access controls, incident
monitoring, and incident reporting. Three of those are high severity. This is
the kind of visibility that makes auditors happy -- you are not guessing at
your gaps, you are measuring them.

---

## SOC 2 Evidence Collection

Now let me get specific about SOC 2. The compliance audit module handles
framework-specific evidence collection with content hashing:

```bash
# List SOC 2 controls
curl -s http://localhost:3000/api/v1/compliance/soc2/controls \
  -H "Authorization: Bearer $TOKEN" | jq '.[0:3]'
```

```json
[
  {
    "id": "01957200-aa01-7000-8000-000000000001",
    "control_id": "CC1.1",
    "category": "Control Environment",
    "title": "COSO Principle 1: Demonstrates commitment to integrity and ethical values",
    "description": "The entity demonstrates a commitment to integrity and ethical values.",
    "status": "passed",
    "tested_at": "2026-01-15T10:00:00Z",
    "tester": "external-auditor-01",
    "created_at": "2025-11-01T00:00:00Z"
  }
]
```

Attach evidence to a control:

```bash
curl -s -X POST http://localhost:3000/api/v1/compliance/soc2/controls/CC6.1/evidence \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Access Review Report Q1 2026",
    "description": "Quarterly access review covering all privileged accounts across production systems. 847 accounts reviewed, 12 revoked, 3 escalated for investigation.",
    "evidence_type": "access_review_report",
    "content_hash": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
  }' | jq .
```

```json
{
  "id": "01957300-bb01-7000-8000-000000000001",
  "control_id": "CC6.1",
  "title": "Access Review Report Q1 2026",
  "description": "Quarterly access review covering all privileged accounts...",
  "evidence_type": "access_review_report",
  "content_hash": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
  "collected_at": "2026-02-05T15:00:00Z"
}
```

The `content_hash` is a SHA-256 hash of the actual evidence document. This
creates an immutable reference -- even if the document is later modified, the
hash on record proves what was collected at what time. When the auditor asks
"can you prove this document has not been altered since collection?" you point
to the hash.

---

## The Real Scenario: SOC 2 Audit + Ransomware

Here is where everything comes together. It is February 11, 2026. The SOC 2
auditor is reviewing our access control evidence in Conference Room B. At
09:47, our streaming analytics engine fires a critical alert: ransomware
lateral movement detected on the finance network.

Step 1: The IR team creates an incident:

```bash
INCIDENT=$(curl -s -X POST http://localhost:3000/api/v1/incident/incidents \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "RANSOMWARE: Finance Network Lateral Movement",
    "description": "EDR detected lateral movement consistent with LockBit 4.0 across finance-srv-01 through finance-srv-04. Initial vector suspected: phishing email to finance-user-0847.",
    "priority": "P0",
    "affected_systems": ["finance-srv-01", "finance-srv-02", "finance-srv-03", "finance-srv-04"]
  }' | jq -r '.id')

echo "Incident: $INCIDENT"
```

Step 2: Simultaneously, attach the incident detection as SOC 2 evidence:

```bash
# This evidence proves IR-4 (Incident Handling) is operational
curl -s -X POST http://localhost:3000/api/v1/compliance/soc2/controls/CC7.3/evidence \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"title\": \"Live Incident Detection - Ransomware Response\",
    \"description\": \"Real-time detection of ransomware lateral movement via EDR integration. Incident $INCIDENT declared at 09:47 UTC. Detection-to-declaration: 3 minutes.\",
    \"evidence_type\": \"incident_detection\",
    \"content_hash\": \"blake3:7b2f1a9e4c5d3f8b...\"
  }"
```

Step 3: Execute containment and log it as both IR action AND compliance evidence:

```bash
# Containment action
CONTAIN=$(curl -s -X POST http://localhost:3000/api/v1/incident/contain \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"incident_id\": \"$INCIDENT\",
    \"action_type\": \"network_isolation\",
    \"target\": \"finance-vlan-200\"
  }" | jq -r '.id')

# Also record as SOC 2 evidence for CC7.4 (Response Activities)
curl -s -X POST http://localhost:3000/api/v1/compliance/soc2/controls/CC7.4/evidence \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"title\": \"Containment Action: Network Isolation\",
    \"description\": \"VLAN 200 (finance) isolated at 09:52 UTC. Containment action ID: $CONTAIN. All east-west traffic blocked. North-south traffic restricted to DNS only.\",
    \"evidence_type\": \"containment_action\",
    \"content_hash\": \"blake3:3d8a7c2e1f94b0a5...\"
  }"
```

Step 4: Advance the incident through phases while collecting evidence at each
stage:

```bash
# Advance to triage
curl -s -X POST "http://localhost:3000/api/v1/incident/incidents/$INCIDENT/advance" \
  -H "Authorization: Bearer $TOKEN"

# Add timeline event with compliance reference
curl -s -X POST "http://localhost:3000/api/v1/incident/incidents/$INCIDENT/timeline" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "event_type": "triage",
    "description": "Triage complete. 4 servers confirmed compromised. Ransomware variant: LockBit 4.0 (BLAKE3: 9c4e2b7a...). No data exfiltration detected. Encryption has not started -- caught during lateral movement phase.",
    "actor": "ir-lead-01"
  }'

# Advance to containment
curl -s -X POST "http://localhost:3000/api/v1/incident/incidents/$INCIDENT/advance" \
  -H "Authorization: Bearer $TOKEN"

# Advance to eradication
curl -s -X POST "http://localhost:3000/api/v1/incident/incidents/$INCIDENT/advance" \
  -H "Authorization: Bearer $TOKEN"
```

---

## The Auditor Conversation

Here is the beautiful part. When the auditor walks out of Conference Room B and
asks "I heard there is an incident -- how does this affect your compliance
posture?" you pull up the readiness assessment:

```bash
curl -s http://localhost:3000/api/v1/compliance/soc2/readiness \
  -H "Authorization: Bearer $TOKEN" | jq .
```

```json
{
  "total_controls": 42,
  "tested": 38,
  "passed": 35,
  "gaps": 3,
  "readiness_percentage": 83.3
}
```

And then you show them the evidence that was collected *during the incident*:

"CC7.3 -- Detection Activities: our streaming analytics detected the lateral
movement within 3 minutes of the initial compromise. Here is the detection
evidence with its BLAKE3 hash."

"CC7.4 -- Response Activities: we isolated the affected network segment within
5 minutes of detection. Here is the containment action record."

"CC7.5 -- Recovery Activities: we will attach the recovery evidence once
eradication is complete."

The incident is not a compliance failure. It is *compliance evidence*. It proves
that your controls work in practice, under real conditions. That is what SOC 2
Type II is actually testing -- not whether you have policies on paper, but
whether your controls operate effectively over time.

---

## Coverage Reports

The coverage endpoint shows your compliance posture per framework:

```bash
curl -s "http://localhost:3000/api/v1/compliance-map/coverage/$NIST_ID" \
  -H "Authorization: Bearer $TOKEN" | jq .
```

```json
{
  "framework_id": "01956f00-aa01-7000-8000-000000000001",
  "framework_name": "NIST 800-53",
  "total_controls": 11,
  "implemented_controls": 8,
  "coverage_pct": 72.7,
  "mapped_to_other_frameworks": 6
}
```

72.7% coverage with 6 controls mapped to other frameworks. Those 6 mapped
controls mean that a single implementation satisfies requirements in multiple
frameworks simultaneously.

---

## Global Stats

The stats endpoint gives you the big picture:

```bash
curl -s http://localhost:3000/api/v1/compliance-map/stats \
  -H "Authorization: Bearer $TOKEN" | jq .
```

```json
{
  "frameworks": 4,
  "controls": 186,
  "mappings": 47,
  "assessments": 3,
  "avg_coverage_pct": 71.2
}
```

Four frameworks, 186 total controls, 47 cross-framework mappings, 3 assessments
run, 71.2% average coverage. This is the dashboard view that your CISO shows
the board of directors.

---

## Accreditation-Ready vs. Accredited

A note on language, because this matters in government and defense contexts.

Playseat is **accreditation-ready**. This means the platform provides the
controls, evidence collection, audit trails, and assessment capabilities that
an accreditation body requires. It does NOT mean the platform is accredited.

Accreditation is a formal determination made by an authorized official (an
Authorizing Official in NIST parlance, or an auditor in SOC 2 parlance) based
on a review of evidence. The platform cannot accredit itself, and we will never
claim that it does.

What we do claim: when the AO or auditor comes knocking, every piece of evidence
they need is already collected, hashed, timestamped, and organized by control.
The platform does the work so the humans can make the decisions.

---

## Building Audit Evidence Queries

For auditors who want to dig deep, here are the SQL queries that power the
compliance system:

```sql
-- Which controls are mapped across frameworks?
SELECT
    cf1.name AS source_framework,
    c1.control_code AS source_control,
    cf2.name AS target_framework,
    c2.control_code AS target_control,
    m.confidence,
    m.mapping_type
FROM compliance_auto_mappings m
JOIN compliance_auto_controls c1 ON c1.id = m.source_control_id
JOIN compliance_auto_controls c2 ON c2.id = m.target_control_id
JOIN compliance_auto_frameworks cf1 ON cf1.id = c1.framework_id
JOIN compliance_auto_frameworks cf2 ON cf2.id = c2.framework_id
ORDER BY m.confidence DESC;

-- Evidence collection for a specific SOC 2 control
SELECT
    e.title,
    e.description,
    e.evidence_type,
    e.content_hash,
    e.collected_at
FROM soc2_evidence e
WHERE e.control_id = 'CC7.3'
ORDER BY e.collected_at DESC;

-- Compliance coverage trend over time
SELECT
    a.framework_id,
    f.name AS framework_name,
    a.score,
    a.controls_met,
    a.total_controls,
    a.created_at
FROM compliance_auto_assessments a
JOIN compliance_auto_frameworks f ON f.id = a.framework_id
ORDER BY a.created_at ASC;

-- Find controls with no evidence
SELECT
    c.control_id,
    c.title,
    c.category,
    c.status
FROM soc2_controls c
WHERE NOT EXISTS (
    SELECT 1 FROM soc2_evidence e
    WHERE e.control_id = c.control_id
)
ORDER BY c.category, c.control_id;
```

That last query -- controls with no evidence -- is the one I run before every
audit. If a control has no evidence attached, it will be flagged as a gap.
Better to find out yourself than have the auditor find it.

---

## Operational Lessons

**Compliance is a continuous process, not an event.** Run assessments weekly, not
annually. The auto-assessment takes seconds. The gap analysis is instant. There
is no reason to wait until audit season to discover you have gaps.

**Map controls early and often.** Every time you implement a new security control,
immediately map it to every framework it satisfies. The upfront investment saves
enormous time during audits.

**Dual-purpose evidence.** Train your IR team to think about compliance evidence
during incidents. A containment action log is both IR evidence and SOC 2 CC7.4
evidence. A detection alert is both IR triage data and SOC 2 CC7.3 evidence.
One action, two purposes, zero extra work.

**Content hashing is non-negotiable.** Every piece of evidence must have a hash.
When an auditor asks "how do I know this document has not been modified?" the
hash is your answer. SHA-256 for compatibility, BLAKE3 for speed. We use both.

**The gap analysis is your friend.** Run it before the auditor does. If you know
your gaps before the audit, you can explain them, show remediation plans, and
demonstrate progress. If the auditor discovers your gaps, you are on the
defensive.

**"Accreditation-ready" is the only honest claim.** Unless you have been through a
formal accreditation process with an authorized body, you are not accredited. The
platform gives you everything you need to pass that process. It does not
replace the process itself.

That Tuesday in 2025, when the ransomware hit during the SOC 2 audit? We passed.
Not because the incident did not happen, but because our detection, containment,
and evidence collection proved that our controls worked exactly as designed. The
auditor wrote in the final report: "Controls operated effectively, including
during an active security incident." That is what compliance under fire looks
like.

---

*Next: Chapter 19 -- Real-Time: Processing 2,000 Events Per Second*

---

(c) 2026 Playseat -- All Rights Reserved | Proprietary and Confidential
