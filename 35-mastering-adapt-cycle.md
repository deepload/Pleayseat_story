# Chapter 35 — ADAPT Mastery: Running Cycles Like a Pro

ADAPT is the core methodology of this platform. It stands for Assess, Discover, Adapt, Protect, Track -- but in practice, the cycle has five operational phases: DISCOVER, CORRELATE, VALIDATE, FORTIFY, and PROVE. This chapter is the definitive guide. Every button, every API call, every sub-feature. By the end you will be running cycles in your sleep.

Navigate to **Platform > ADAPT** or `http://localhost:1420/adapt`.

You see 14 tabs across the top. We will cover every single one.

---

## The ADAPT Page Layout

The 14 tabs:

| Tab | Purpose |
|-----|---------|
| **Mission Control** | Cycle dashboard, global score, phase status |
| **Exposure Map** | Exposure events from discovery |
| **Threat Landscape** | Correlations and threat patterns |
| **Defense Actions** | Recommended and executed defense actions |
| **Analytics** | Metrics, trends, and historical data |
| **War Room** | Adversary profiles, gap analysis, simulations |
| **Forecast** | Threat forecasting based on org profile |
| **Autopilot** | Autonomous cycle execution with human oversight |
| **Briefings** | Executive and technical briefing generation |
| **Mesh** | Federated defense network peer sharing |
| **Genome** | Threat DNA fingerprinting and clustering |
| **Replay** | Incident time-travel and reconstruction |
| **Collab** | Collaborative threat hunting workspaces |
| **Sentinel** | Behavioral anomaly detection baselines |

---

## Setting Up: Scopes

Before you can run a cycle, you need a scope -- what you are assessing.

### List Existing Scopes

```bash
curl -s http://localhost:3000/api/v1/adapt/scopes \
  -H "Authorization: Bearer $TOKEN" | python -m json.tool
```

### Create a Scope

```bash
curl -s -X POST http://localhost:3000/api/v1/adapt/scopes \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Enterprise Network Q1 2026",
    "description": "Complete enterprise network assessment including DMZ, internal subnets, cloud assets, and endpoints",
    "asset_types": ["network", "endpoint", "application", "cloud"],
    "subnets": ["10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16"],
    "exclusions": ["10.0.99.0/24", "10.0.100.0/24"]
  }'
```

```json
{
  "id": "scope-01953d10-..."
}
```

```bash
SCOPE_ID="scope-01953d10-..."
```

**Scope design tips**:
- Include everything you want to assess. Exclusions are for lab/test subnets.
- Asset types control which discovery modules activate:
  - `network`: Network scanning, port discovery
  - `endpoint`: EDR integration, host scanning
  - `application`: Web scanning, API testing
  - `cloud`: Cloud configuration audit

### Update a Scope

```bash
curl -s -X PUT http://localhost:3000/api/v1/adapt/scopes/$SCOPE_ID \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Enterprise Network Q1 2026 (Updated)",
    "exclusions": ["10.0.99.0/24"]
  }'
```

### Delete a Scope

```bash
curl -s -X DELETE http://localhost:3000/api/v1/adapt/scopes/$SCOPE_ID \
  -H "Authorization: Bearer $TOKEN"
```

---

## DISCOVER Deep Dive

DISCOVER is the first phase. It answers: **"What is exposed?"**

### Starting a Cycle

```bash
curl -s -X POST http://localhost:3000/api/v1/adapt/cycles \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"scope_id": "'$SCOPE_ID'"}'
```

```json
{
  "id": "cycle-01953d20-..."
}
```

```bash
CYCLE_ID="cycle-01953d20-..."
```

The cycle starts in DISCOVER phase automatically.

### Viewing Discovery Events

Discovery generates exposure events -- things the platform found:

```bash
curl -s http://localhost:3000/api/v1/adapt/events \
  -H "Authorization: Bearer $TOKEN" | python -m json.tool
```

Each event includes:
- **event_type**: What was found (open_port, vulnerable_service, misconfiguration, etc.)
- **severity**: How bad is it (critical, high, medium, low, info)
- **asset_id**: Which asset is affected
- **description**: Human-readable explanation
- **evidence**: Supporting data

### Viewing Unacknowledged Events

These are events no one has reviewed yet:

```bash
curl -s http://localhost:3000/api/v1/adapt/events/unacknowledged \
  -H "Authorization: Bearer $TOKEN"
```

This is your work queue. Go through each one.

### Acknowledging Events

As you review each event, acknowledge it:

```bash
EVENT_ID="event-..."

curl -s -X POST http://localhost:3000/api/v1/adapt/events/$EVENT_ID/acknowledge \
  -H "Authorization: Bearer $TOKEN"
```

Acknowledging does not mean "fixed" -- it means "reviewed by a human." This is the human-in-the-loop gate.

### Events by Cycle

View events from a specific cycle only:

```bash
curl -s http://localhost:3000/api/v1/adapt/events/by-cycle/$CYCLE_ID \
  -H "Authorization: Bearer $TOKEN"
```

### Discovery Types

The platform discovers different things based on scope asset types:

**Network discovery**: Open ports, exposed services, network misconfigurations, default credentials, unencrypted protocols.

**Application discovery**: Web vulnerabilities (SQL injection, XSS, SSRF), API misconfigurations, authentication weaknesses, exposed admin panels.

**Endpoint discovery**: Missing patches, disabled security controls, unauthorized software, weak configurations, rogue processes.

**Cloud discovery**: Misconfigured S3 buckets, overly permissive IAM roles, unencrypted databases, public-facing resources that should be private.

### Scheduling: One-Time vs Recurring

A single cycle is one-time by default. For continuous monitoring, use Autopilot (covered later in this chapter) to schedule recurring cycles.

### Reading Discovery Results: Severity Scoring

Events are scored on a 5-level scale:

| Severity | Score | Meaning | Action Timeline |
|----------|-------|---------|-----------------|
| Critical | 9.0-10.0 | Actively exploitable, no auth required | Immediate (hours) |
| High | 7.0-8.9 | Exploitable with some conditions | Within 24 hours |
| Medium | 4.0-6.9 | Requires specific conditions | Within 1 week |
| Low | 1.0-3.9 | Theoretical risk, difficult to exploit | Next maintenance window |
| Info | 0.1-0.9 | Informational, no direct risk | Document and monitor |

### Prioritization

Process events in this order:
1. Critical events first (these are active threats)
2. High events that are internet-facing
3. High events that are internal
4. Medium events on sensitive systems
5. Everything else

---

## CORRELATE Deep Dive

Advance the cycle from DISCOVER to CORRELATE:

```bash
curl -s -X POST http://localhost:3000/api/v1/adapt/cycles/$CYCLE_ID/advance \
  -H "Authorization: Bearer $TOKEN"
```

CORRELATE answers: **"How do these exposures relate to real threats?"**

### Viewing Correlations

```bash
curl -s http://localhost:3000/api/v1/adapt/correlations \
  -H "Authorization: Bearer $TOKEN" | python -m json.tool
```

Each correlation connects:
- An exposure event to a known threat (IOC match)
- Multiple events to a pattern (behavioral correlation)
- Events to a timeline (temporal correlation)
- Events to a geography or sector (contextual correlation)

### High-Risk Correlations

The most dangerous correlations:

```bash
curl -s http://localhost:3000/api/v1/adapt/correlations/high-risk \
  -H "Authorization: Bearer $TOKEN"
```

These are exposures that match known active threats. If a high-risk correlation exists, the threat is real and targeting you (or something very similar to you).

### Correlations by Asset

See all correlations affecting a specific asset:

```bash
ASSET_ID="asset-..."

curl -s http://localhost:3000/api/v1/adapt/correlations/by-asset/$ASSET_ID \
  -H "Authorization: Bearer $TOKEN"
```

### How Correlation Works Internally

The correlation engine runs several algorithms:

**1. IOC Matching**: Compares discovered IPs, domains, and hashes against the threat intelligence IOC database.

```sql
SELECT e.id, e.asset_id, i.value, i.confidence, i.threat_actor
FROM adapt_exposure_events e
JOIN threat_iocs i ON (
  (e.details->>'ip_address' = i.value AND i.ioc_type = 'ip_address')
  OR (e.details->>'domain' = i.value AND i.ioc_type = 'domain')
  OR (e.details->>'file_hash' = i.value AND i.ioc_type = 'file_hash')
)
WHERE e.cycle_id = $1;
```

**2. Behavioral Correlation**: Groups events that share behavioral patterns (same ATT&CK techniques, same attack tools, same time windows).

**3. Temporal Correlation**: Events that happen close together on the same asset or network segment are likely related.

**4. Geographic/Sector Correlation**: Events matching threat patterns known to target your industry sector or geographic region.

### Confidence Scoring

Each correlation has a confidence score (0-100):

- **90-100**: Near certain. Multiple independent evidence sources confirm the correlation.
- **70-89**: High confidence. Strong indicators with minor ambiguity.
- **50-69**: Medium confidence. Plausible but could be coincidence.
- **Below 50**: Low confidence. Weak indicators, possible false positive.

### Manual Correlation

Sometimes the automated engine misses connections you can see. Create manual correlations by linking findings:

```bash
# Use the AI correlate endpoint
curl -s -X POST http://localhost:3000/ai/correlate \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"campaign_id": "'$CAMPAIGN_ID'"}'
```

```json
{
  "patterns": [
    "Events on FINANCE-WS-012 and FILE-SERVER-01 share temporal proximity and technique overlap (T1021.002, T1059.001)",
    "C2 infrastructure 198.51.100.0/24 matches BlackCat IOC cluster with 92% confidence",
    "Credential harvesting pattern matches APT-PHANTOM TTP profile"
  ]
}
```

---

## VALIDATE Deep Dive

Advance to VALIDATE:

```bash
curl -s -X POST http://localhost:3000/api/v1/adapt/cycles/$CYCLE_ID/advance \
  -H "Authorization: Bearer $TOKEN"
```

VALIDATE answers: **"Are these exposures real and exploitable?"**

### Viewing Validated Exposures

```bash
curl -s http://localhost:3000/api/v1/adapt/exposures \
  -H "Authorization: Bearer $TOKEN"
```

### Confirmed Exposures

Exposures that have been validated as real:

```bash
curl -s http://localhost:3000/api/v1/adapt/exposures/confirmed \
  -H "Authorization: Bearer $TOKEN"
```

### Re-validating an Exposure

After remediation, re-validate to confirm the fix:

```bash
EXPOSURE_ID="exposure-..."

curl -s -X POST http://localhost:3000/api/v1/adapt/exposures/$EXPOSURE_ID/revalidate \
  -H "Authorization: Bearer $TOKEN"
```

If the vulnerability is fixed, the exposure status changes to "remediated." If it is still there, it stays "confirmed."

### BAS Simulation

Breach and Attack Simulation tests whether your defenses actually detect and block attacks:

```bash
# Run a simulation against an adversary profile
PROFILE_ID="adversary-..."

curl -s -X POST http://localhost:3000/api/v1/adapt/adversaries/$PROFILE_ID/simulate \
  -H "Authorization: Bearer $TOKEN"
```

```json
{
  "id": "sim-01953d40-...",
  "adversary_profile_id": "adversary-...",
  "status": "running",
  "technique_count": 12,
  "started_at": "2026-02-18T..."
}
```

The simulation runs the adversary's known techniques against your environment (safely, using BAS tools) and records which defenses detected/blocked each technique.

### Viewing Simulations

```bash
curl -s http://localhost:3000/api/v1/adapt/simulations \
  -H "Authorization: Bearer $TOKEN"
```

### SIGMA Rule Validation

Check if your SIGMA detection rules actually fire on simulated events:

```bash
# Trigger Sentinel detection
curl -s -X POST http://localhost:3000/api/v1/adapt/sentinel/detect \
  -H "Authorization: Bearer $TOKEN"
```

```json
{
  "anomalies_detected": 5
}
```

If your detection rules catch the simulated attacks, they work. If they don't, you have detection gaps.

### Exposure Validation: Confirming Vulnerabilities are Real

For each discovered exposure, validation checks:
1. Is the vulnerable service actually running? (not just open port)
2. Is the vulnerability actually exploitable? (not just theoretical)
3. Are compensating controls in place? (WAF, IPS, segmentation)
4. What is the real-world impact if exploited?

---

## FORTIFY Deep Dive

Advance to FORTIFY:

```bash
curl -s -X POST http://localhost:3000/api/v1/adapt/cycles/$CYCLE_ID/advance \
  -H "Authorization: Bearer $TOKEN"
```

FORTIFY answers: **"What should we fix, and in what order?"**

### Defense Action Generation

The platform generates recommended defense actions based on validated exposures:

```bash
curl -s http://localhost:3000/api/v1/adapt/actions \
  -H "Authorization: Bearer $TOKEN" | python -m json.tool
```

Each action includes:
- **action_type**: What to do (patch, block, reconfigure, add_rule, etc.)
- **priority**: Based on exposure severity and exploit likelihood
- **target**: Which system or component
- **description**: Human-readable explanation
- **status**: pending, approved, executing, completed, failed

### Pending Actions

Your work queue:

```bash
curl -s http://localhost:3000/api/v1/adapt/actions/pending \
  -H "Authorization: Bearer $TOKEN"
```

### Approving Actions

Review each action and approve it:

```bash
ACTION_ID="action-..."

curl -s -X POST http://localhost:3000/api/v1/adapt/actions/$ACTION_ID/approve \
  -H "Authorization: Bearer $TOKEN"
```

In the UI (Defense Actions tab), click the checkmark button next to each action to approve it.

### Executing Actions

Once approved, execute:

```bash
curl -s -X POST http://localhost:3000/api/v1/adapt/actions/$ACTION_ID/execute \
  -H "Authorization: Bearer $TOKEN"
```

Some actions trigger SOAR playbooks automatically. Others require manual execution with the platform recording the outcome.

### SOAR Playbook Integration

For automated hardening, SOAR playbooks can be triggered from defense actions:

```bash
# Trigger a SOAR playbook as part of fortification
PLAYBOOK_ID="pb-..."

curl -s -X POST http://localhost:3000/soar/playbooks/$PLAYBOOK_ID/trigger \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "trigger_event": {
      "action_id": "'$ACTION_ID'",
      "action_type": "patch_system",
      "target": "web-prod-01"
    }
  }'
```

### War Room: Gap Analysis

The War Room provides strategic defense analysis. Navigate to the **War Room** tab.

**Get the War Room summary**:

```bash
curl -s http://localhost:3000/api/v1/adapt/war-room/summary \
  -H "Authorization: Bearer $TOKEN" | python -m json.tool
```

Returns: total adversary profiles tracked, technique coverage percentage, gap count, simulation results summary.

**View Adversary Profiles**:

```bash
curl -s http://localhost:3000/api/v1/adapt/adversaries \
  -H "Authorization: Bearer $TOKEN"
```

Each adversary has a profile with their known techniques. Compare their techniques against your defenses:

**View Technique Coverage**:

```bash
curl -s http://localhost:3000/api/v1/adapt/coverage \
  -H "Authorization: Bearer $TOKEN"
```

Returns a list of ATT&CK techniques with your coverage status: detected, blocked, not_covered.

**Coverage Matrix**:

```bash
curl -s http://localhost:3000/api/v1/adapt/coverage/matrix \
  -H "Authorization: Bearer $TOKEN"
```

```json
[
  {"technique_id": "T1566.001", "technique_name": "Spearphishing Attachment", "tactic": "initial-access", "coverage_status": "detected", "confidence": 85},
  {"technique_id": "T1059.001", "technique_name": "PowerShell", "tactic": "execution", "coverage_status": "blocked", "confidence": 92},
  {"technique_id": "T1021.002", "technique_name": "SMB/Windows Admin Shares", "tactic": "lateral-movement", "coverage_status": "not_covered", "confidence": 0}
]
```

**Identify Gaps**:

```bash
curl -s http://localhost:3000/api/v1/adapt/coverage/gaps \
  -H "Authorization: Bearer $TOKEN"
```

Returns all techniques where coverage_status is "not_covered." These are your defense gaps.

**What-If Analysis**:

What happens to coverage if you close specific gaps?

```bash
curl -s -X POST http://localhost:3000/api/v1/adapt/what-if \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "profile_id": "adversary-...",
    "gaps_to_close": ["T1021.002", "T1048.003", "T1003.001"]
  }'
```

Returns a projected coverage improvement: current coverage percentage vs projected, and which adversary TTPs would be fully covered after closing those gaps.

### Technique Coverage: Before and After

Track coverage improvement over time:

```bash
# Current metrics
curl -s http://localhost:3000/api/v1/adapt/metrics \
  -H "Authorization: Bearer $TOKEN"

# Trends over time
curl -s http://localhost:3000/api/v1/adapt/metrics/trends \
  -H "Authorization: Bearer $TOKEN"
```

```json
[
  {
    "metric_type": "technique_coverage",
    "values": [
      {"date": "2026-02-11", "value": 62},
      {"date": "2026-02-12", "value": 62},
      {"date": "2026-02-13", "value": 65},
      {"date": "2026-02-14", "value": 68},
      {"date": "2026-02-15", "value": 68},
      {"date": "2026-02-16", "value": 72},
      {"date": "2026-02-17", "value": 72},
      {"date": "2026-02-18", "value": 78}
    ]
  }
]
```

Coverage went from 62% to 78% in one week. That is the FORTIFY phase working.

---

## PROVE Deep Dive

Advance to the final phase:

```bash
curl -s -X POST http://localhost:3000/api/v1/adapt/cycles/$CYCLE_ID/advance \
  -H "Authorization: Bearer $TOKEN"
```

PROVE answers: **"Can we demonstrate measurable improvement?"**

### Global Defense Score

```bash
curl -s http://localhost:3000/api/v1/adapt/score/global \
  -H "Authorization: Bearer $TOKEN"
```

```json
{
  "score": 78,
  "trend": "improving",
  "asset_count": 145
}
```

The score is a composite of:
- Technique coverage percentage
- Exposure remediation rate
- Mean time to detect/contain
- Compliance posture
- Active threat exposure

### Asset-Level Scoring

Score for a specific asset:

```bash
ASSET_ID="asset-..."

curl -s http://localhost:3000/api/v1/adapt/score/asset/$ASSET_ID \
  -H "Authorization: Bearer $TOKEN"
```

```json
{
  "asset_id": "asset-...",
  "score": 85,
  "factors": {
    "patch_level": 90,
    "detection_coverage": 80,
    "configuration": 85,
    "exposure_count": 0
  }
}
```

### Briefing Generation

Generate briefings from cycle data.

**List templates**:

```bash
curl -s http://localhost:3000/api/v1/adapt/briefing-templates \
  -H "Authorization: Bearer $TOKEN"
```

Available template types:
- **Executive Summary**: High-level risk posture for leadership
- **Technical Deep Dive**: Detailed findings for the security team
- **Compliance Status**: Framework compliance for auditors

**Generate a briefing**:

```bash
TEMPLATE_ID="template-..."

curl -s -X POST http://localhost:3000/api/v1/adapt/briefings \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "template_id": "'$TEMPLATE_ID'",
    "period_start": "2026-02-11T00:00:00Z",
    "period_end": "2026-02-18T23:59:59Z"
  }'
```

```json
{
  "id": "briefing-01953d80-..."
}
```

```bash
BRIEFING_ID="briefing-01953d80-..."
```

**View the briefing**:

```bash
curl -s http://localhost:3000/api/v1/adapt/briefings/$BRIEFING_ID \
  -H "Authorization: Bearer $TOKEN" | python -m json.tool
```

**View briefing sections**:

```bash
curl -s http://localhost:3000/api/v1/adapt/briefings/$BRIEFING_ID/sections \
  -H "Authorization: Bearer $TOKEN" | python -m json.tool
```

Sections include: Executive Summary, Threat Landscape, Discovery Findings, Correlation Analysis, Validation Results, Defense Actions Taken, Coverage Metrics, Recommendations.

**Publish the briefing**:

```bash
curl -s -X POST http://localhost:3000/api/v1/adapt/briefings/$BRIEFING_ID/publish \
  -H "Authorization: Bearer $TOKEN"
```

**Get the latest published briefing**:

```bash
curl -s http://localhost:3000/api/v1/adapt/briefings/latest \
  -H "Authorization: Bearer $TOKEN"
```

**Regenerate a briefing** (with updated data):

```bash
curl -s -X POST http://localhost:3000/api/v1/adapt/briefings/$BRIEFING_ID/regenerate \
  -H "Authorization: Bearer $TOKEN"
```

### Evidence Packaging

Generate evidence packs for compliance or legal:

```bash
curl -s -X POST http://localhost:3000/reporting/evidence-packs/create \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "ADAPT Cycle Q1-W8 Evidence Pack",
    "framework": "nist_csf"
  }'
```

The evidence pack includes all findings, actions, metrics, and hashes from the cycle -- everything an auditor needs.

### Historical Comparison

Compare this cycle with previous ones:

```bash
# List all cycles
curl -s http://localhost:3000/api/v1/adapt/cycles \
  -H "Authorization: Bearer $TOKEN"

# Get metrics for a specific cycle
curl -s http://localhost:3000/api/v1/adapt/metrics/by-scope/$SCOPE_ID \
  -H "Authorization: Bearer $TOKEN"
```

Track: exposure count, remediation rate, coverage percentage, defense score. These should improve with each cycle.

---

## Advanced: Autopilot Mode

Navigate to the **Autopilot** tab. Autopilot runs ADAPT cycles automatically on a schedule.

### Check Autopilot Status

```bash
curl -s http://localhost:3000/api/v1/adapt/autopilot/status \
  -H "Authorization: Bearer $TOKEN"
```

### Configure Autopilot

```bash
curl -s http://localhost:3000/api/v1/adapt/autopilot/config \
  -H "Authorization: Bearer $TOKEN"
```

Update configuration:

```bash
curl -s -X PUT http://localhost:3000/api/v1/adapt/autopilot/config \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "cycle_interval_hours": 24,
    "auto_acknowledge_below": "low",
    "require_approval_above": "high",
    "max_concurrent_cycles": 2
  }'
```

### Enable Autopilot

```bash
curl -s -X POST http://localhost:3000/api/v1/adapt/autopilot/enable \
  -H "Authorization: Bearer $TOKEN"
```

### Disable Autopilot

```bash
curl -s -X POST http://localhost:3000/api/v1/adapt/autopilot/disable \
  -H "Authorization: Bearer $TOKEN"
```

### Kill Switch

Emergency stop -- immediately halts all autonomous activity:

```bash
curl -s -X POST http://localhost:3000/api/v1/adapt/autopilot/kill-switch \
  -H "Authorization: Bearer $TOKEN"
```

Use this if autopilot is taking actions you did not expect. Human-in-the-loop override.

### Force a Cycle

Trigger an immediate cycle outside the schedule:

```bash
curl -s -X POST http://localhost:3000/api/v1/adapt/autopilot/force-cycle \
  -H "Authorization: Bearer $TOKEN"
```

### Escalations

When autopilot encounters something it cannot handle autonomously, it escalates:

```bash
curl -s http://localhost:3000/api/v1/adapt/autopilot/escalations \
  -H "Authorization: Bearer $TOKEN"
```

Acknowledge escalations:

```bash
ESCALATION_ID="esc-..."

curl -s -X POST http://localhost:3000/api/v1/adapt/autopilot/escalations/$ESCALATION_ID/acknowledge \
  -H "Authorization: Bearer $TOKEN"
```

### Heartbeats

Monitor autopilot health:

```bash
curl -s http://localhost:3000/api/v1/adapt/autopilot/heartbeats \
  -H "Authorization: Bearer $TOKEN"
```

Record a manual heartbeat:

```bash
curl -s -X POST http://localhost:3000/api/v1/adapt/autopilot/heartbeat \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "status": "healthy",
    "cycles_completed": 5,
    "last_cycle_duration_secs": 3600
  }'
```

---

## Advanced: Threat Forecasting

Navigate to the **Forecast** tab. The forecast engine predicts future threats based on your organization's profile.

### Set Your Organization Profile

```bash
curl -s http://localhost:3000/api/v1/adapt/org-profile \
  -H "Authorization: Bearer $TOKEN"
```

Update it:

```bash
curl -s -X PUT http://localhost:3000/api/v1/adapt/org-profile \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "sector": "defense",
    "size": "large",
    "region": "north_america",
    "regulatory_frameworks": ["nist_csf", "cmmc", "fedramp"],
    "threat_exposure": "high"
  }'
```

### Generate Forecasts

```bash
curl -s -X POST http://localhost:3000/api/v1/adapt/forecasts \
  -H "Authorization: Bearer $TOKEN"
```

### View Forecasts

```bash
curl -s http://localhost:3000/api/v1/adapt/forecasts \
  -H "Authorization: Bearer $TOKEN"
```

### Trending Threats

```bash
curl -s http://localhost:3000/api/v1/adapt/forecasts/trending \
  -H "Authorization: Bearer $TOKEN"
```

### Forecast Accuracy

Track how accurate previous forecasts were:

```bash
curl -s http://localhost:3000/api/v1/adapt/forecasts/accuracy \
  -H "Authorization: Bearer $TOKEN"
```

### Mark a Forecast as Materialized

When a predicted threat actually occurs:

```bash
FORECAST_ID="forecast-..."

curl -s -X POST http://localhost:3000/api/v1/adapt/forecasts/$FORECAST_ID/materialize \
  -H "Authorization: Bearer $TOKEN"
```

---

## Advanced: Federated Defense Mesh

Navigate to the **Mesh** tab. The mesh connects your Playseat instance with trusted peers for intel sharing.

### Add a Peer

```bash
curl -s -X POST http://localhost:3000/api/v1/adapt/mesh/peers \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "org_name": "Sector ISAC Partner",
    "peer_url": "https://partner.example.com/api/v1/adapt/mesh",
    "trust_score": 80,
    "capabilities": ["ioc_sharing", "threat_reports", "technique_coverage"]
  }'
```

### Share Intel with a Peer

```bash
PEER_ID="peer-..."

curl -s -X POST http://localhost:3000/api/v1/adapt/mesh/share \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "peer_id": "'$PEER_ID'",
    "intel_type": "ioc",
    "stix_id": "indicator--a1b2c3",
    "confidence": 85
  }'
```

### Sync with a Peer

```bash
curl -s -X POST http://localhost:3000/api/v1/adapt/mesh/peers/$PEER_ID/sync \
  -H "Authorization: Bearer $TOKEN"
```

### View Mesh Status

```bash
curl -s http://localhost:3000/api/v1/adapt/mesh/status \
  -H "Authorization: Bearer $TOKEN"
```

### View Mesh Statistics

```bash
curl -s http://localhost:3000/api/v1/adapt/mesh/stats \
  -H "Authorization: Bearer $TOKEN"
```

### Trust Management

Update trust score for a peer:

```bash
curl -s -X PUT http://localhost:3000/api/v1/adapt/mesh/peers/$PEER_ID/trust \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"trust_score": 90}'
```

---

## Advanced: Collaborative Hunting

Navigate to the **Collab** tab.

### Create a Hunting Workspace

```bash
curl -s -X POST http://localhost:3000/api/v1/adapt/collab/workspaces \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Q1 2026 Threat Hunt: Lateral Movement",
    "description": "Collaborative hunt for lateral movement indicators across the enterprise"
  }'
```

```bash
WORKSPACE_ID="ws-..."
```

### Add Team Members

```bash
curl -s -X POST http://localhost:3000/api/v1/adapt/collab/workspaces/$WORKSPACE_ID/members \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"user_id": "analyst-user-id", "role": "hunter"}'
```

### Share Hunt Queries

```bash
curl -s -X POST http://localhost:3000/api/v1/adapt/collab/workspaces/$WORKSPACE_ID/queries \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "query_text": "SELECT * FROM network_flows WHERE dst_port IN (445, 139) AND src_ip != dst_subnet ORDER BY timestamp DESC",
    "query_type": "sql",
    "shared": true
  }'
```

### Record Hunt Findings

```bash
curl -s -X POST http://localhost:3000/api/v1/adapt/collab/workspaces/$WORKSPACE_ID/findings \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Anomalous SMB traffic from FINANCE-WS-012",
    "severity": "high",
    "status": "investigating"
  }'
```

### Collaboration Statistics

```bash
curl -s http://localhost:3000/api/v1/adapt/collab/stats \
  -H "Authorization: Bearer $TOKEN"
```

---

## Chaining Cycles

For continuous defense improvement, chain cycles:

1. Run Cycle 1 with full scope -- establish baseline
2. Fix the critical/high findings
3. Run Cycle 2 -- validate fixes, discover new issues
4. Compare Cycle 2 metrics with Cycle 1
5. Repeat

Each cycle should show:
- Fewer critical/high exposures
- Higher technique coverage
- Lower MTTD and MTTC
- Higher overall defense score

Track this with the metrics trend API:

```bash
curl -s http://localhost:3000/api/v1/adapt/metrics/trends \
  -H "Authorization: Bearer $TOKEN"
```

---

## Cycle Pause and Resume

Need to pause a cycle mid-way?

```bash
curl -s -X POST http://localhost:3000/api/v1/adapt/cycles/$CYCLE_ID/pause \
  -H "Authorization: Bearer $TOKEN"
```

The cycle freezes in its current phase. All data is preserved. Resume by advancing:

```bash
curl -s -X POST http://localhost:3000/api/v1/adapt/cycles/$CYCLE_ID/advance \
  -H "Authorization: Bearer $TOKEN"
```

---

## The Complete ADAPT API Reference

```bash
# Scopes
GET    /api/v1/adapt/scopes                      # List scopes
POST   /api/v1/adapt/scopes                      # Create scope
PUT    /api/v1/adapt/scopes/:id                   # Update scope
DELETE /api/v1/adapt/scopes/:id                   # Delete scope

# Cycles
GET    /api/v1/adapt/cycles                      # List cycles
GET    /api/v1/adapt/cycles/:id                   # Get cycle
GET    /api/v1/adapt/cycles/current               # Get current cycle
POST   /api/v1/adapt/cycles                      # Create cycle
POST   /api/v1/adapt/cycles/:id/advance           # Advance phase
POST   /api/v1/adapt/cycles/:id/pause             # Pause cycle

# Events (DISCOVER)
GET    /api/v1/adapt/events                      # List events
GET    /api/v1/adapt/events/unacknowledged        # Unreviewed events
POST   /api/v1/adapt/events/:id/acknowledge       # Acknowledge event
GET    /api/v1/adapt/events/by-cycle/:id          # Events by cycle

# Correlations (CORRELATE)
GET    /api/v1/adapt/correlations                 # List correlations
GET    /api/v1/adapt/correlations/high-risk       # High-risk only
GET    /api/v1/adapt/correlations/by-asset/:id    # By asset

# Exposures (VALIDATE)
GET    /api/v1/adapt/exposures                   # List exposures
GET    /api/v1/adapt/exposures/confirmed          # Confirmed only
POST   /api/v1/adapt/exposures/:id/revalidate     # Re-validate

# Actions (FORTIFY)
GET    /api/v1/adapt/actions                     # List actions
GET    /api/v1/adapt/actions/pending              # Pending approval
POST   /api/v1/adapt/actions/:id/approve          # Approve action
POST   /api/v1/adapt/actions/:id/execute          # Execute action

# Metrics (PROVE)
GET    /api/v1/adapt/metrics                     # List metrics
GET    /api/v1/adapt/metrics/trends               # Metric trends
GET    /api/v1/adapt/metrics/by-scope/:id         # By scope

# Scoring
GET    /api/v1/adapt/score/global                 # Global score
GET    /api/v1/adapt/score/asset/:id              # Asset score
GET    /api/v1/adapt/dashboard                    # Full dashboard

# War Room
GET    /api/v1/adapt/war-room/summary             # War room summary
GET    /api/v1/adapt/adversaries                  # Adversary profiles
POST   /api/v1/adapt/adversaries/:id/simulate     # Run simulation
GET    /api/v1/adapt/coverage                     # Technique coverage
GET    /api/v1/adapt/coverage/matrix              # Coverage matrix
GET    /api/v1/adapt/coverage/gaps                # Coverage gaps
POST   /api/v1/adapt/what-if                      # What-if analysis

# Forecast
GET    /api/v1/adapt/org-profile                  # Org profile
PUT    /api/v1/adapt/org-profile                  # Update org profile
GET    /api/v1/adapt/forecasts                    # List forecasts
POST   /api/v1/adapt/forecasts                    # Generate forecasts
GET    /api/v1/adapt/forecasts/trending           # Trending threats
GET    /api/v1/adapt/forecasts/accuracy           # Accuracy stats

# Autopilot
GET    /api/v1/adapt/autopilot/status             # Status
GET    /api/v1/adapt/autopilot/config             # Configuration
PUT    /api/v1/adapt/autopilot/config             # Update config
POST   /api/v1/adapt/autopilot/enable             # Enable
POST   /api/v1/adapt/autopilot/disable            # Disable
POST   /api/v1/adapt/autopilot/kill-switch        # Emergency stop
POST   /api/v1/adapt/autopilot/force-cycle        # Force immediate cycle
GET    /api/v1/adapt/autopilot/heartbeats         # Health heartbeats
GET    /api/v1/adapt/autopilot/escalations        # Pending escalations

# Briefings
GET    /api/v1/adapt/briefing-templates           # List templates
GET    /api/v1/adapt/briefings                    # List briefings
POST   /api/v1/adapt/briefings                    # Generate briefing
GET    /api/v1/adapt/briefings/:id                # Get briefing
GET    /api/v1/adapt/briefings/:id/sections       # Get sections
POST   /api/v1/adapt/briefings/:id/publish        # Publish
POST   /api/v1/adapt/briefings/:id/regenerate     # Regenerate
GET    /api/v1/adapt/briefings/latest             # Latest published

# Mesh
GET    /api/v1/adapt/mesh/peers                   # List peers
POST   /api/v1/adapt/mesh/peers                   # Add peer
POST   /api/v1/adapt/mesh/share                   # Share intel
POST   /api/v1/adapt/mesh/peers/:id/sync          # Sync with peer
GET    /api/v1/adapt/mesh/status                  # Mesh status
GET    /api/v1/adapt/mesh/stats                   # Mesh statistics

# Genome
GET    /api/v1/adapt/genome/genomes               # List genomes
POST   /api/v1/adapt/genome/genomes               # Create genome
POST   /api/v1/adapt/genome/genomes/:id/markers   # Add marker
POST   /api/v1/adapt/genome/match                 # Match sample
GET    /api/v1/adapt/genome/clusters              # List clusters
POST   /api/v1/adapt/genome/cluster               # Trigger clustering
GET    /api/v1/adapt/genome/stats                 # Genome stats

# Replay
GET    /api/v1/adapt/replay/replays               # List replays
POST   /api/v1/adapt/replay/replays               # Create replay
POST   /api/v1/adapt/replay/replays/:id/events    # Add event
POST   /api/v1/adapt/replay/replays/:id/snapshots # Add snapshot
POST   /api/v1/adapt/replay/replays/:id/play      # Play replay
GET    /api/v1/adapt/replay/stats                 # Replay stats

# Collab
GET    /api/v1/adapt/collab/workspaces            # List workspaces
POST   /api/v1/adapt/collab/workspaces            # Create workspace
POST   /api/v1/adapt/collab/workspaces/:id/members  # Add member
POST   /api/v1/adapt/collab/workspaces/:id/queries  # Share query
POST   /api/v1/adapt/collab/workspaces/:id/findings # Add finding
GET    /api/v1/adapt/collab/stats                 # Collab stats

# Sentinel
POST   /api/v1/adapt/sentinel/baselines           # Create baseline
GET    /api/v1/adapt/sentinel/baselines           # List baselines
POST   /api/v1/adapt/sentinel/detect              # Run detection
GET    /api/v1/adapt/sentinel/anomalies           # List anomalies
GET    /api/v1/adapt/sentinel/alerts              # List alerts
POST   /api/v1/adapt/sentinel/alerts/:id/acknowledge  # Acknowledge
POST   /api/v1/adapt/sentinel/alerts/:id/resolve      # Resolve
POST   /api/v1/adapt/sentinel/rules               # Create rule
GET    /api/v1/adapt/sentinel/rules               # List rules
GET    /api/v1/adapt/sentinel/stats               # Sentinel stats
```

That is 90+ endpoints just for ADAPT. Master these and you master defensive intelligence.

---

*You have reached ADAPT mastery. Every phase, every feature, every API endpoint. Now go run your first autonomous cycle and watch the defense score climb.*

---

© 2026 Playseat — All Rights Reserved | Proprietary and Confidential
