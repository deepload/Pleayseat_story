# Chapter 8 -- Sentinel Baselines: Detecting the Anomaly

**Classification: PROPRIETARY** | **ADAPT Extension 6: Sentinel** | **Crate: `svc-adapt::sentinel` + `svc-api::routes::adapt` (Sentinel handlers)**

> Clara's last message said to look for "deviation in manifest delta." I didn't understand it until I pointed Sentinel at the Sahel Aid Coordination Platform and watched the numbers tell a story about children being moved like cargo. The baselines don't lie. They can't. That's the entire point.

---

## Table of Contents

1. [Why I Needed Sentinel Now](#why-i-needed-sentinel-now)
2. [Creating Baselines for the Aid Network](#creating-baselines)
3. [How Anomaly Detection Works](#how-anomaly-detection-works)
4. [Alert Generation and Classification](#alert-generation)
5. [Rule Engine: Custom Anomaly Patterns](#rule-engine)
6. [Scenario: Finding PHANTOM MERCY's Signature](#finding-phantom-mercys-signature)
7. [Clara's Notes -- Deviation in Manifest Delta](#claras-notes)
8. [Integration with UEBA](#integration-with-ueba)
9. [Tuning Baselines to Reduce Noise](#tuning-baselines)
10. [Sentinel Statistics](#sentinel-statistics)
11. [Database Deep Dive](#database-deep-dive)
12. [API Reference](#api-reference)

---

## Why I Needed Sentinel Now

February 17, 2026. 04:30 UTC. Four hours since the BND confirmed Clara was alive.

I'm sitting in the SOC with cold coffee and a clarity I haven't felt in weeks. The BND intercept told me where Clara was -- Niamey region, Niger. CERT-EU told me what PHANTOM MERCY was doing -- manipulating shipping manifests on the Sahel Aid Coordination Platform. NATO told me the operation spanned Sahel and Balkans.

But none of them could tell me what Clara needed me to see. Her message said *"deviation in manifest delta."* She wasn't describing the problem. She was telling me *how to find it*. She was giving me the detection method. Because that's what Clara does -- she's a cryptographer. She thinks in patterns and deviations.

So I pointed Sentinel at the aid network. If PHANTOM MERCY is systematically altering shipping manifests, those alterations will have a mathematical signature. A baseline of normal cargo operations will show what legitimate manifests look like. Any systematic deviation from that baseline is PHANTOM MERCY's operational fingerprint.

Every breach I've ever investigated had the same postmortem finding: "the anomaly was visible in the data, but nobody was looking." Sentinel looks. It watches baselines like a border guard watches a crossing point. Anything that deviates from normal gets flagged, classified, and alerted on before a human even opens their laptop.

This time, the anomaly isn't a breach. It's something worse. It's children being moved through humanitarian logistics corridors while the databases say they're shipping rice and medical supplies.

---

## Creating Baselines for the Aid Network

A baseline defines the expected behavior range for a specific metric on a specific target. I built five baselines, each targeting a different dimension of PHANTOM MERCY's operation.

| Field | Type | Description |
|-------|------|-------------|
| `baseline_type` | string | Category: `network`, `user`, `application`, `service_account`, `endpoint` |
| `target` | string | The entity being baselined |
| `metric_name` | string | What's being measured |
| `min_value` | float | Lower bound of normal range |
| `max_value` | float | Upper bound of normal range |
| `description` | string | Human-readable description |

### Baseline 1: Manifest Weight Deviation

This is the key baseline. Clara's "deviation in manifest delta" -- the difference between declared cargo weight and the weight calculated from component manifest entries.

```bash
TOKEN=$(curl -s -X POST https://playseat.local/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "soc_lead", "password": "S0C!L3ad2026"}' | jq -r '.token')

curl -s -X POST https://playseat.local/api/v1/adapt/sentinel/baselines \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "baseline_type": "application",
    "target": "SACP-MANIFEST-SYSTEM",
    "metric_name": "manifest_weight_delta_percent",
    "min_value": -2.0,
    "max_value": 2.0,
    "description": "Normal variance between declared total cargo weight and sum of itemized weights in SACP manifests. Legitimate variance due to rounding, unit conversion, and packaging: +/- 2%. PHANTOM MERCY manifest forgery produces systematic 12-18% deviations."
  }'
```

```json
{
  "id": "01954d01-base-7f00-sent-000000000001"
}
```

I typed the description with Clara's words echoing in my head. *Deviation in manifest delta.* She'd distilled weeks of observation into four words. Four words that told me exactly what metric to baseline.

### Baseline 2: Database Admin Access Frequency

PHANTOM MERCY modifies manifests through compromised admin credentials. Normal admin access to the SACP database follows predictable patterns.

```bash
curl -s -X POST https://playseat.local/api/v1/adapt/sentinel/baselines \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "baseline_type": "user",
    "target": "SACP-DATABASE-ADMINS",
    "metric_name": "admin_logins_per_day",
    "min_value": 2.0,
    "max_value": 12.0,
    "description": "SACP database administrators normally log in 4-8 times per day during business hours. After-hours admin access or > 12 logins/day suggests credential compromise or automated manifest modification."
  }'
# {"id": "01954d02-base-7f00-sent-000000000002"}
```

### Baseline 3: Shipment Route Anomalies

Humanitarian aid follows established corridors. Unexpected route changes are either logistics complications or PHANTOM MERCY redirecting cargo.

```bash
curl -s -X POST https://playseat.local/api/v1/adapt/sentinel/baselines \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "baseline_type": "application",
    "target": "SACP-ROUTING-SYSTEM",
    "metric_name": "route_deviation_count_per_week",
    "min_value": 0.0,
    "max_value": 3.0,
    "description": "Normal route deviations in Sahel aid corridor: 1-2 per week due to weather, road conditions, or security. More than 3 deviations per week suggests systematic rerouting."
  }'
# {"id": "01954d03-base-7f00-sent-000000000003"}
```

### Baseline 4: Manifest Edit Frequency

Legitimate manifests are edited 1-2 times after creation -- usually typo corrections or quantity adjustments. PHANTOM MERCY edits manifests multiple times to adjust the weight delta.

```bash
curl -s -X POST https://playseat.local/api/v1/adapt/sentinel/baselines \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "baseline_type": "application",
    "target": "SACP-MANIFEST-SYSTEM",
    "metric_name": "avg_edits_per_manifest",
    "min_value": 0.0,
    "max_value": 2.5,
    "description": "Average number of post-creation edits per shipping manifest. Normal: 1-2 edits. PHANTOM MERCY manifests show 5-8 edits as they iteratively adjust weight figures to maintain hash consistency across database replicas."
  }'
# {"id": "01954d04-base-7f00-sent-000000000004"}
```

That last part -- "iteratively adjust weight figures to maintain hash consistency across database replicas" -- came straight from Clara's cryptographic analysis. The one I'd shared with the BND under TLP:AMBER. PHANTOM MERCY doesn't just change a number. They change it, recalculate the consistency hash, verify it matches across replicas, and adjust again if it doesn't. It's a multi-step process. It leaves fingerprints in the edit log.

### Baseline 5: After-Hours API Access

PHANTOM MERCY's operators work when legitimate aid workers don't. Night shift manifest modifications are a key behavioral signature.

```bash
curl -s -X POST https://playseat.local/api/v1/adapt/sentinel/baselines \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "baseline_type": "network",
    "target": "SACP-API-GATEWAY",
    "metric_name": "after_hours_api_calls_per_night",
    "min_value": 0.0,
    "max_value": 15.0,
    "description": "API calls to SACP between 22:00 and 06:00 local time. Normal: 3-10 (automated backup, scheduled reports). PHANTOM MERCY manifest modifications generate 40-80 API calls per night during active alteration windows."
  }'
# {"id": "01954d05-base-7f00-sent-000000000005"}
```

### List All Baselines

```bash
curl -s "https://playseat.local/api/v1/adapt/sentinel/baselines?limit=10&offset=0" \
  -H "Authorization: Bearer $TOKEN" | jq '.[] | {id, baseline_type, target, metric_name, min_value, max_value, active}'
```

```json
{
  "id": "01954d01-base-7f00-sent-000000000001",
  "baseline_type": "application",
  "target": "SACP-MANIFEST-SYSTEM",
  "metric_name": "manifest_weight_delta_percent",
  "min_value": -2.0,
  "max_value": 2.0,
  "active": true
}
{
  "id": "01954d02-base-7f00-sent-000000000002",
  "baseline_type": "user",
  "target": "SACP-DATABASE-ADMINS",
  "metric_name": "admin_logins_per_day",
  "min_value": 2.0,
  "max_value": 12.0,
  "active": true
}
{
  "id": "01954d03-base-7f00-sent-000000000003",
  "baseline_type": "application",
  "target": "SACP-ROUTING-SYSTEM",
  "metric_name": "route_deviation_count_per_week",
  "min_value": 0.0,
  "max_value": 3.0,
  "active": true
}
{
  "id": "01954d04-base-7f00-sent-000000000004",
  "baseline_type": "application",
  "target": "SACP-MANIFEST-SYSTEM",
  "metric_name": "avg_edits_per_manifest",
  "min_value": 0.0,
  "max_value": 2.5,
  "active": true
}
{
  "id": "01954d05-base-7f00-sent-000000000005",
  "baseline_type": "network",
  "target": "SACP-API-GATEWAY",
  "metric_name": "after_hours_api_calls_per_night",
  "min_value": 0.0,
  "max_value": 15.0,
  "active": true
}
```

Five baselines. Five angles of observation. Between them, they cover the data integrity, access patterns, logistics routing, document lifecycle, and temporal behavior of anyone touching the SACP system.

If PHANTOM MERCY touches a manifest, Sentinel will see it.

---

## How Anomaly Detection Works

The detection is mathematically straightforward. For each baseline, Sentinel checks whether the current observed value falls outside the `[min_value, max_value]` range. If it does, the deviation is calculated as a percentage distance from the nearest boundary.

### The Rust Implementation

From `crates/svc-adapt/src/sentinel.rs`:

```rust
/// Detect if a value is anomalous given baseline bounds.
/// Returns Some(deviation) if anomalous, None if within normal range.
pub fn detect_anomaly(current_value: f64, min_value: f64, max_value: f64) -> Option<f64> {
    if current_value < min_value {
        let range = max_value - min_value;
        if range == 0.0 {
            return Some(1.0);
        }
        Some((min_value - current_value) / range)
    } else if current_value > max_value {
        let range = max_value - min_value;
        if range == 0.0 {
            return Some(1.0);
        }
        Some((current_value - max_value) / range)
    } else {
        None // Within normal range
    }
}

/// Classify severity based on deviation magnitude.
pub fn classify_severity(deviation: f64) -> &'static str {
    if deviation >= 5.0 {
        "critical"
    } else if deviation >= 2.0 {
        "high"
    } else if deviation >= 1.0 {
        "medium"
    } else {
        "low"
    }
}
```

The deviation is normalized to the baseline range. A deviation of 1.0 means the value is one full range-width outside the boundary. A deviation of 5.0 means it's five range-widths out -- massive anomaly.

### Example Calculations for SACP Monitoring

| Metric | Min | Max | Range | Current | Deviation | Severity |
|--------|-----|-----|-------|---------|-----------|----------|
| manifest_weight_delta_percent | -2.0 | 2.0 | 4.0 | 14.7 | 3.175 | high |
| admin_logins_per_day | 2.0 | 12.0 | 10.0 | 31 | 1.9 | medium |
| route_deviation_count_per_week | 0.0 | 3.0 | 3.0 | 9 | 2.0 | high |
| avg_edits_per_manifest | 0.0 | 2.5 | 2.5 | 6.3 | 1.52 | medium |
| after_hours_api_calls_per_night | 0.0 | 15.0 | 15.0 | 67 | 3.47 | high |

Look at that first row. A manifest weight delta of 14.7%. The baseline says +/- 2% is normal. This manifest's declared weight is 14.7% higher than the sum of its items. That's not a rounding error. That's someone adding phantom weight to cover for cargo that isn't what it claims to be.

Clara saw this. Standing in a warehouse in Niamey, looking at crates labeled RICE and doing the math in her head because that's what Clara does, she saw that the numbers didn't add up. And she was brave enough -- or stubborn enough, or angry enough -- to go looking for what was really inside those crates.

---

## Alert Generation and Classification

Every detected anomaly automatically generates an alert. Alerts have lifecycle states:

```
open --> acknowledged --> resolved
```

### Alert Severity Mapping

| Deviation | Severity | Expected Response |
|-----------|----------|-------------------|
| < 1.0 | `low` | Review within 24 hours |
| 1.0 - 2.0 | `medium` | Review within 4 hours |
| 2.0 - 5.0 | `high` | Review within 1 hour |
| >= 5.0 | `critical` | Immediate response required |

### Running Detection: The Manifest Weight Delta

```bash
# Detect: SACP manifest weight delta at 14.7% (baseline max: 2%)
curl -s -X POST https://playseat.local/api/v1/adapt/sentinel/detect \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "baseline_id": "01954d01-base-7f00-sent-000000000001",
    "current_value": 14.7
  }'
```

```json
{
  "anomaly_detected": true,
  "anomaly_id": "01954d10-anom-7f00-detect-00000001",
  "alert_id": "01954d10-alrt-7f00-detect-00000001",
  "deviation": 3.175,
  "severity": "high"
}
```

One API call. Anomaly detected, deviation calculated, severity classified, alert generated. All in one request.

I stared at that response for a long time. 14.7% deviation on a manifest that should be within 2%. Somewhere in the Sahel, a shipment labeled as 12 tons of rice is actually carrying something else. Or carrying 12 tons of rice plus 1.8 tons of something the manifest doesn't mention.

### Detection: After-Hours API Access

```bash
curl -s -X POST https://playseat.local/api/v1/adapt/sentinel/detect \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "baseline_id": "01954d05-base-7f00-sent-000000000005",
    "current_value": 67.0
  }'
```

```json
{
  "anomaly_detected": true,
  "anomaly_id": "01954d10-anom-7f00-detect-00000002",
  "alert_id": "01954d10-alrt-7f00-detect-00000002",
  "deviation": 3.467,
  "severity": "high"
}
```

Sixty-seven API calls between 10 PM and 6 AM. Someone's working late on the SACP system. Someone who isn't an aid worker.

### Normal Detection (Control Check)

```bash
# Control: A legitimate manifest with 1.3% weight delta
curl -s -X POST https://playseat.local/api/v1/adapt/sentinel/detect \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "baseline_id": "01954d01-base-7f00-sent-000000000001",
    "current_value": 1.3
  }'
```

```json
{
  "anomaly_detected": false,
  "current_value": 1.3,
  "baseline_min": -2.0,
  "baseline_max": 2.0
}
```

1.3% is within the +/- 2% range. Normal manifest. Normal aid shipment. No anomaly.

The system works. It separates the PHANTOM MERCY forgeries from the legitimate operations. Clara would appreciate the elegance. She always said the best detection methods are the simplest ones -- you just have to know what to measure.

### Inactive Baseline Guard

```bash
curl -s -X POST https://playseat.local/api/v1/adapt/sentinel/detect \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "baseline_id": "01954d99-disabled-baseline-id",
    "current_value": 500.0
  }'
```

```json
{
  "error": "baseline is not active"
}
```

The route handler checks `baseline.active` before proceeding:

```rust
if !baseline.active {
    return Err(err(StatusCode::CONFLICT, "baseline is not active"));
}
```

### List All Open Alerts

```bash
curl -s https://playseat.local/api/v1/adapt/sentinel/alerts \
  -H "Authorization: Bearer $TOKEN" | jq '.[] | {id, severity, status, created_at}'
```

```json
{
  "id": "01954d10-alrt-7f00-detect-00000001",
  "severity": "high",
  "status": "open",
  "created_at": "2026-02-17T05:00:00Z"
}
{
  "id": "01954d10-alrt-7f00-detect-00000002",
  "severity": "high",
  "status": "open",
  "created_at": "2026-02-17T05:05:00Z"
}
{
  "id": "01954d10-alrt-7f00-detect-00000003",
  "severity": "medium",
  "status": "open",
  "created_at": "2026-02-17T05:10:00Z"
}
{
  "id": "01954d10-alrt-7f00-detect-00000004",
  "severity": "medium",
  "status": "open",
  "created_at": "2026-02-17T05:12:00Z"
}
{
  "id": "01954d10-alrt-7f00-detect-00000005",
  "severity": "high",
  "status": "open",
  "created_at": "2026-02-17T05:15:00Z"
}
```

Five alerts in fifteen minutes. All five baselines triggered. PHANTOM MERCY's operational signature lit up the dashboard like a Christmas tree.

### Acknowledge and Investigate

```bash
curl -s -X POST https://playseat.local/api/v1/adapt/sentinel/alerts/01954d10-alrt-7f00-detect-00000001/acknowledge \
  -H "Authorization: Bearer $TOKEN" | jq
```

```json
{
  "acknowledged": true,
  "alert_id": "01954d10-alrt-7f00-detect-00000001"
}
```

```sql
UPDATE adapt_sentinel_alerts
SET status = 'acknowledged',
    acknowledged_by = $1,
    acknowledged_at = NOW()
WHERE id = $2;
```

---

## Rule Engine: Custom Anomaly Patterns

Baselines detect statistical deviations. Rules detect *patterns* -- combinations of conditions that together indicate a specific threat.

### Rule: PHANTOM MERCY Manifest Forgery Pattern

```bash
curl -s -X POST https://playseat.local/api/v1/adapt/sentinel/rules \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "PHANTOM MERCY Manifest Forgery Detection",
    "anomaly_type": "manifest_weight_delta",
    "severity_threshold": "high",
    "enabled": true,
    "description": "Triggers when shipping manifest weight deltas exceed 10% combined with above-normal edit counts. This pattern matches PHANTOM MERCY operational signature: weight manipulation with iterative hash-consistency adjustments."
  }'
```

```json
{
  "id": "01954d20-rule-7f00-sent-000000000001"
}
```

### Additional Rules

```bash
# Rule: After-hours manifest modification
curl -s -X POST https://playseat.local/api/v1/adapt/sentinel/rules \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "After-Hours Manifest Modification",
    "anomaly_type": "after_hours_api",
    "severity_threshold": "high",
    "enabled": true,
    "description": "Triggers when SACP API activity exceeds 40 calls during 22:00-06:00 window. PHANTOM MERCY operators work overnight to avoid detection by legitimate aid staff."
  }'

# Rule: Systematic route deviation
curl -s -X POST https://playseat.local/api/v1/adapt/sentinel/rules \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Systematic Route Deviation",
    "anomaly_type": "route_deviation",
    "severity_threshold": "critical",
    "enabled": true,
    "description": "Triggers when humanitarian shipment route deviations exceed 5 per week. Systematic rerouting suggests cargo diversion for trafficking purposes."
  }'

# Rule: Credential abuse pattern
curl -s -X POST https://playseat.local/api/v1/adapt/sentinel/rules \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "SACP Admin Credential Abuse",
    "anomaly_type": "admin_access",
    "severity_threshold": "high",
    "enabled": true,
    "description": "Triggers when SACP admin accounts generate > 20 logins per day. Compromised credentials being used for batch manifest modification."
  }'

# Rule: Multi-edit manifest fingerprint
curl -s -X POST https://playseat.local/api/v1/adapt/sentinel/rules \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Manifest Multi-Edit Fingerprint",
    "anomaly_type": "manifest_edits",
    "severity_threshold": "high",
    "enabled": true,
    "description": "Triggers when average edits per manifest exceeds 5. PHANTOM MERCY hash-consistency algorithm requires 5-8 iterative edits per forgery."
  }'
```

### List All Rules

```bash
curl -s https://playseat.local/api/v1/adapt/sentinel/rules \
  -H "Authorization: Bearer $TOKEN" | jq '.[] | {name, anomaly_type, severity_threshold, enabled}'
```

```json
{
  "name": "PHANTOM MERCY Manifest Forgery Detection",
  "anomaly_type": "manifest_weight_delta",
  "severity_threshold": "high",
  "enabled": true
}
{
  "name": "After-Hours Manifest Modification",
  "anomaly_type": "after_hours_api",
  "severity_threshold": "high",
  "enabled": true
}
{
  "name": "Systematic Route Deviation",
  "anomaly_type": "route_deviation",
  "severity_threshold": "critical",
  "enabled": true
}
{
  "name": "SACP Admin Credential Abuse",
  "anomaly_type": "admin_access",
  "severity_threshold": "high",
  "enabled": true
}
{
  "name": "Manifest Multi-Edit Fingerprint",
  "anomaly_type": "manifest_edits",
  "severity_threshold": "high",
  "enabled": true
}
```

---

## Scenario: Finding PHANTOM MERCY's Signature

Let me walk through the full detection sequence. This is the hour when everything clicked.

### Hour 0: Establishing Normal

February 17, 2026, 05:00 UTC. I've just finished setting up the baselines. First, I run detection against yesterday's metrics -- a known-good day when no anomalous manifests were filed.

```bash
# Normal day: manifest weight delta at 0.8%
curl -s -X POST https://playseat.local/api/v1/adapt/sentinel/detect \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "baseline_id": "01954d01-base-7f00-sent-000000000001",
    "current_value": 0.8
  }'
```

```json
{
  "anomaly_detected": false,
  "current_value": 0.8,
  "baseline_min": -2.0,
  "baseline_max": 2.0
}
```

Good. 0.8% delta on a clean day. The baseline works.

### Hour 1: The Anomalies Start

I run detection against today's SACP data. The numbers come back wrong. All of them.

```bash
# Detection 1: Manifest weight delta at 14.7%
curl -s -X POST https://playseat.local/api/v1/adapt/sentinel/detect \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "baseline_id": "01954d01-base-7f00-sent-000000000001",
    "current_value": 14.7
  }'
```

```json
{
  "anomaly_detected": true,
  "anomaly_id": "01954d30-anom-7f00-scenario-00001",
  "alert_id": "01954d30-alrt-7f00-scenario-00001",
  "deviation": 3.175,
  "severity": "high"
}
```

```bash
# Detection 2: Admin logins at 31 per day
curl -s -X POST https://playseat.local/api/v1/adapt/sentinel/detect \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "baseline_id": "01954d02-base-7f00-sent-000000000002",
    "current_value": 31.0
  }'
```

```json
{
  "anomaly_detected": true,
  "anomaly_id": "01954d31-anom-7f00-scenario-00002",
  "alert_id": "01954d31-alrt-7f00-scenario-00002",
  "deviation": 1.9,
  "severity": "medium"
}
```

```bash
# Detection 3: Route deviations at 9 per week
curl -s -X POST https://playseat.local/api/v1/adapt/sentinel/detect \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "baseline_id": "01954d03-base-7f00-sent-000000000003",
    "current_value": 9.0
  }'
```

```json
{
  "anomaly_detected": true,
  "anomaly_id": "01954d32-anom-7f00-scenario-00003",
  "alert_id": "01954d32-alrt-7f00-scenario-00003",
  "deviation": 2.0,
  "severity": "high"
}
```

```bash
# Detection 4: Average manifest edits at 6.3
curl -s -X POST https://playseat.local/api/v1/adapt/sentinel/detect \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "baseline_id": "01954d04-base-7f00-sent-000000000004",
    "current_value": 6.3
  }'
```

```json
{
  "anomaly_detected": true,
  "anomaly_id": "01954d33-anom-7f00-scenario-00004",
  "alert_id": "01954d33-alrt-7f00-scenario-00004",
  "deviation": 1.52,
  "severity": "medium"
}
```

```bash
# Detection 5: After-hours API calls at 67
curl -s -X POST https://playseat.local/api/v1/adapt/sentinel/detect \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "baseline_id": "01954d05-base-7f00-sent-000000000005",
    "current_value": 67.0
  }'
```

```json
{
  "anomaly_detected": true,
  "anomaly_id": "01954d34-anom-7f00-scenario-00005",
  "alert_id": "01954d34-alrt-7f00-scenario-00005",
  "deviation": 3.467,
  "severity": "high"
}
```

Five for five. Every baseline triggered. The picture was clear.

### The Anomaly Trail

```bash
curl -s https://playseat.local/api/v1/adapt/sentinel/anomalies \
  -H "Authorization: Bearer $TOKEN" | jq '.[] | {id, baseline_id, current_value, deviation, severity, detected_at}'
```

```json
{
  "id": "01954d30-anom-7f00-scenario-00001",
  "baseline_id": "01954d01-base-7f00-sent-000000000001",
  "current_value": 14.7,
  "deviation": 3.175,
  "severity": "high",
  "detected_at": "2026-02-17T06:00:00Z"
}
{
  "id": "01954d31-anom-7f00-scenario-00002",
  "baseline_id": "01954d02-base-7f00-sent-000000000002",
  "current_value": 31.0,
  "deviation": 1.9,
  "severity": "medium",
  "detected_at": "2026-02-17T06:02:00Z"
}
{
  "id": "01954d32-anom-7f00-scenario-00003",
  "baseline_id": "01954d03-base-7f00-sent-000000000003",
  "current_value": 9.0,
  "deviation": 2.0,
  "severity": "high",
  "detected_at": "2026-02-17T06:04:00Z"
}
{
  "id": "01954d33-anom-7f00-scenario-00004",
  "baseline_id": "01954d04-base-7f00-sent-000000000004",
  "current_value": 6.3,
  "deviation": 1.52,
  "severity": "medium",
  "detected_at": "2026-02-17T06:06:00Z"
}
{
  "id": "01954d34-anom-7f00-scenario-00005",
  "baseline_id": "01954d05-base-7f00-sent-000000000005",
  "current_value": 67.0,
  "deviation": 3.467,
  "severity": "high",
  "detected_at": "2026-02-17T06:08:00Z"
}
```

### Correlation SQL

```sql
-- Correlate all PHANTOM MERCY anomalies
SELECT
    sa.detected_at,
    sb.baseline_type,
    sb.target,
    sb.metric_name,
    sa.current_value,
    sb.min_value || ' - ' || sb.max_value AS normal_range,
    ROUND(sa.deviation::numeric, 2) AS deviation,
    sa.severity
FROM adapt_sentinel_anomalies sa
JOIN adapt_sentinel_baselines sb ON sb.id = sa.baseline_id
WHERE sa.detected_at BETWEEN '2026-02-17T05:00:00Z' AND '2026-02-17T07:00:00Z'
ORDER BY sa.deviation DESC;
```

```
 detected_at          | baseline_type | target               | metric_name                   | current | normal_range  | deviation | severity
----------------------+---------------+----------------------+-------------------------------+---------+---------------+-----------+----------
 2026-02-17T06:08:00Z | network       | SACP-API-GATEWAY     | after_hours_api_calls_per_night| 67.0   | 0.0 - 15.0    | 3.47      | high
 2026-02-17T06:00:00Z | application   | SACP-MANIFEST-SYSTEM | manifest_weight_delta_percent | 14.7    | -2.0 - 2.0    | 3.18      | high
 2026-02-17T06:04:00Z | application   | SACP-ROUTING-SYSTEM  | route_deviation_count_per_week| 9.0     | 0.0 - 3.0     | 2.00      | high
 2026-02-17T06:02:00Z | user          | SACP-DATABASE-ADMINS | admin_logins_per_day          | 31.0    | 2.0 - 12.0    | 1.90      | medium
 2026-02-17T06:06:00Z | application   | SACP-MANIFEST-SYSTEM | avg_edits_per_manifest        | 6.3     | 0.0 - 2.5     | 1.52      | medium
```

Five anomalies. Five different aspects of the SACP system. One operational pattern: PHANTOM MERCY is actively manipulating manifests on the Sahel Aid Coordination Platform. Right now. Today.

---

## Clara's Notes -- Deviation in Manifest Delta

After the detection run, I went back to Clara's message and read it again with new eyes.

*"Evidence in shipping manifests -- look for systematic deviation in declared cargo weights vs actual tonnage."*

She didn't say "random" deviation. She said "systematic." And that's exactly what Sentinel found. The deviation isn't noise. It's consistent. 12-18% across multiple manifests. Always positive -- the declared weight is always *higher* than the component sum. That means the manifests claim more weight than the itemized list accounts for.

Why would PHANTOM MERCY inflate the declared weight? Because if you're adding undeclared cargo to a shipment, the total weight at the checkpoint has to match the manifest. If a truck weighs 14.7 tons at the border crossing but the manifest says 12 tons, someone asks questions. But if the manifest says 14.7 tons and the truck weighs 14.7 tons, it sails through.

The 12-18% delta isn't an error. It's the weight of the hidden cargo. Clara figured that out standing in a warehouse. I confirmed it with math.

Her notes -- the ones I extracted from her encrypted analysis file -- also mentioned the edit pattern:

> *"Each forged manifest undergoes 5-8 modifications post-creation. The forgery algorithm adjusts weight figures iteratively to maintain hash consistency across the SACP database replicas in Niamey, Ouagadougou, and N'Djamena. The edits cluster between 23:00 and 04:00 local time."*

5-8 edits. 23:00 to 04:00. Exactly what Sentinel found. 6.3 average edits. 67 after-hours API calls.

Clara had reverse-engineered PHANTOM MERCY's operational methodology through pure observation and cryptographic reasoning. I just proved it was still happening.

---

## Integration with UEBA

Sentinel baselines feed into the broader User and Entity Behavior Analytics pipeline:

```
Raw Logs --> Metric Aggregation --> Sentinel Baselines --> Anomaly Detection --> UEBA Correlation --> ADAPT Cycle
```

The key insight: a medium-severity admin login anomaly and a medium-severity edit frequency anomaly, when correlated with three high-severity anomalies across the same system within the same time window, produce a composite severity of **critical**. The whole is greater than the sum of its parts.

PHANTOM MERCY's operational signature isn't any single anomaly. It's the *pattern* of all five occurring together. Admin credential abuse + manifest weight inflation + excessive edits + route deviations + after-hours activity = active trafficking operation using manifest forgery as cover.

---

## Tuning Baselines to Reduce Noise

### Finding Noisy Baselines

```sql
-- Top baselines by anomaly count (potentially too tight)
SELECT
    sb.id,
    sb.baseline_type,
    sb.target,
    sb.metric_name,
    sb.min_value,
    sb.max_value,
    COUNT(sa.id) AS anomaly_count,
    AVG(sa.deviation) AS avg_deviation
FROM adapt_sentinel_baselines sb
JOIN adapt_sentinel_anomalies sa ON sa.baseline_id = sb.id
WHERE sa.detected_at > NOW() - INTERVAL '7 days'
GROUP BY sb.id, sb.baseline_type, sb.target, sb.metric_name, sb.min_value, sb.max_value
ORDER BY anomaly_count DESC
LIMIT 10;
```

### Widening a Baseline

The route deviation baseline fired more often than expected due to seasonal weather patterns disrupting Sahel logistics. I widened it slightly:

```bash
curl -s -X PUT https://playseat.local/api/v1/adapt/sentinel/baselines/01954d03-base-7f00-sent-000000000003 \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "min_value": 0.0,
    "max_value": 4.0,
    "description": "TUNED: Widened from 0-3 to 0-4 after accounting for February harmattan season disruptions to Sahel road network."
  }'
```

```json
{
  "updated": true,
  "id": "01954d03-base-7f00-sent-000000000003"
}
```

### The Tuning Cycle

1. Deploy baselines with ranges based on historical data
2. Run for 1 week
3. Query anomaly counts per baseline
4. Identify baselines with high anomaly counts and low average deviations
5. Widen those baselines by 10-20%
6. Repeat until false positive rate drops below 5%
7. Review quarterly and after major infrastructure changes

For the PHANTOM MERCY baselines, I was conservative with tuning. I'd rather have a few false positives than miss an active trafficking operation. Every false positive alert on a manifest is an inconvenience. Every missed detection is a child.

---

## Sentinel Statistics

```bash
curl -s https://playseat.local/api/v1/adapt/sentinel/stats \
  -H "Authorization: Bearer $TOKEN" | jq
```

```json
{
  "total_baselines": 5,
  "active_baselines": 5,
  "total_anomalies": 23,
  "total_alerts": 23,
  "open_alerts": 5,
  "total_rules": 5,
  "enabled_rules": 5
}
```

23 anomalies detected across all baselines. 5 still open from the current detection run. All rules enabled.

### Alert Resolution Metrics

```sql
SELECT
    severity,
    COUNT(*) AS total_alerts,
    COUNT(CASE WHEN status = 'open' THEN 1 END) AS open_alerts,
    COUNT(CASE WHEN status = 'acknowledged' THEN 1 END) AS acked_alerts,
    COUNT(CASE WHEN status = 'resolved' THEN 1 END) AS resolved_alerts,
    AVG(
        CASE WHEN resolved_at IS NOT NULL
        THEN EXTRACT(EPOCH FROM (resolved_at - created_at)) / 60
        END
    ) AS avg_resolution_minutes
FROM adapt_sentinel_alerts
GROUP BY severity
ORDER BY
    CASE severity
        WHEN 'critical' THEN 1
        WHEN 'high' THEN 2
        WHEN 'medium' THEN 3
        WHEN 'low' THEN 4
    END;
```

```
 severity  | total | open | acked | resolved | avg_resolution_minutes
-----------+-------+------+-------+----------+------------------------
 critical  | 2     | 0    | 0     | 2        | 8.5
 high      | 12    | 3    | 2     | 7        | 22.4
 medium    | 7     | 2    | 1     | 4        | 45.8
 low       | 2     | 0    | 0     | 2        | 120.0
```

8.5 minutes average resolution on critical alerts. That's fast. But in the PHANTOM MERCY context, every minute matters because those manifests represent real shipments moving through real corridors.

---

## Database Deep Dive

The complete Sentinel schema:

```sql
-- Behavioral baselines
CREATE TABLE IF NOT EXISTS adapt_sentinel_baselines (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    baseline_type   TEXT NOT NULL,
    target          TEXT,
    metric_name     TEXT NOT NULL,
    min_value       REAL NOT NULL DEFAULT 0.0,
    max_value       REAL NOT NULL DEFAULT 100.0,
    description     TEXT,
    active          BOOLEAN NOT NULL DEFAULT true,
    created_by      UUID,
    created_at      TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Detected anomalies
CREATE TABLE IF NOT EXISTS adapt_sentinel_anomalies (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    baseline_id     UUID REFERENCES adapt_sentinel_baselines(id) ON DELETE CASCADE,
    current_value   REAL NOT NULL,
    deviation       REAL NOT NULL DEFAULT 0.0,
    severity        TEXT NOT NULL DEFAULT 'low',
    detected_at     TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_adapt_sentinel_anomalies_baseline ON adapt_sentinel_anomalies(baseline_id);
CREATE INDEX IF NOT EXISTS idx_adapt_sentinel_anomalies_severity ON adapt_sentinel_anomalies(severity);

-- Alerts generated from anomalies
CREATE TABLE IF NOT EXISTS adapt_sentinel_alerts (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    anomaly_id      UUID REFERENCES adapt_sentinel_anomalies(id) ON DELETE CASCADE,
    severity        TEXT NOT NULL DEFAULT 'medium',
    status          TEXT NOT NULL DEFAULT 'open',
    acknowledged_by UUID,
    acknowledged_at TIMESTAMP WITH TIME ZONE,
    resolved_by     UUID,
    resolved_at     TIMESTAMP WITH TIME ZONE,
    created_at      TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_adapt_sentinel_alerts_status ON adapt_sentinel_alerts(status);
CREATE INDEX IF NOT EXISTS idx_adapt_sentinel_alerts_anomaly ON adapt_sentinel_alerts(anomaly_id);

-- Custom anomaly detection rules
CREATE TABLE IF NOT EXISTS adapt_sentinel_rules (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name                TEXT NOT NULL,
    anomaly_type        TEXT NOT NULL,
    severity_threshold  TEXT NOT NULL DEFAULT 'medium',
    enabled             BOOLEAN NOT NULL DEFAULT true,
    description         TEXT,
    created_at          TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_adapt_sentinel_rules_enabled ON adapt_sentinel_rules(enabled);
```

---

## API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/adapt/sentinel/baselines` | Create a new baseline |
| GET | `/api/v1/adapt/sentinel/baselines` | List all baselines |
| GET | `/api/v1/adapt/sentinel/baselines/{id}` | Get baseline details |
| PUT | `/api/v1/adapt/sentinel/baselines/{id}` | Update baseline |
| POST | `/api/v1/adapt/sentinel/detect` | Run anomaly detection |
| GET | `/api/v1/adapt/sentinel/anomalies` | List all anomalies |
| GET | `/api/v1/adapt/sentinel/alerts` | List all alerts |
| POST | `/api/v1/adapt/sentinel/alerts/{id}/acknowledge` | Acknowledge an alert |
| POST | `/api/v1/adapt/sentinel/alerts/{id}/resolve` | Resolve an alert |
| POST | `/api/v1/adapt/sentinel/rules` | Create a detection rule |
| GET | `/api/v1/adapt/sentinel/rules` | List all rules |
| PUT | `/api/v1/adapt/sentinel/rules/{id}` | Update a rule |
| GET | `/api/v1/adapt/sentinel/stats` | System statistics |

---

## What the Baselines Told Me

Sentinel confirmed Clara's analysis in every dimension. The manifest weight deviations are real. The after-hours modifications are real. The routing anomalies are real. PHANTOM MERCY is operating right now, today, on the Sahel Aid Coordination Platform, manipulating shipping manifests to cover the movement of undeclared cargo.

Clara didn't die chasing a ghost. She found something real. And now I can see it too.

The baselines gave me something else: operational tempo. PHANTOM MERCY modifies manifests in clusters -- 2-3 nights of heavy activity followed by 4-5 quiet days. That rhythm maps to a shipping schedule. They're not modifying manifests randomly. They're doing it just before specific shipments cross specific border crossings.

If I can predict the next modification cluster, I can predict the next shipment. And if I can predict the next shipment, I can find which corridor Clara was investigating when she went dark.

But that analysis would have to wait. Because at 07:14 UTC on February 17, 2026, while I was still processing the Sentinel results, every screen in the SOC turned red.

Ransomware.

Someone had just encrypted our engineering VLAN.

---

*Next chapter: the ransomware attack was no coincidence. PHANTOM MERCY sent it as a distraction -- and in the chaos, Clara sent her message.*

---

(c) 2026 Playseat -- All Rights Reserved | Defensive Intelligence Through ADAPT
