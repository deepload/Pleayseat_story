# Chapter 30: From Zero to SOC -- Building a 24/7 Security Operation

> "I have built three SOCs from scratch. The first one nearly killed me because I did everything wrong. The second one was decent but bled money. The third one -- built on Playseat -- was profitable within 8 months and detected an APT intrusion at month 3 that would have cost the organization EUR 40M. This chapter is everything I learned, distilled into a blueprint you can follow."

---

## Why This Chapter Exists

Most SOC guides read like academic papers. They talk about "capability maturity models" and "operational frameworks" and produce a lot of PowerPoint that nobody reads. This chapter is different. This is the field manual for actually building a SOC -- from the first day you boot up Playseat to the day you are running 24/7 shifts with 50 analysts and a board that loves you because you can prove your value in euros.

I am going to cover everything: team structure, shift management, alert triage workflows, the 10 SOAR playbooks you need on day one, the metrics that matter (and the ones that do not), and how to scale without losing your mind. Every section has actual API calls, SQL queries, and configuration examples.

Let us start.

---

## Part 1: Architecture and Day-One Setup

### The Minimal Viable SOC

You need four things on day one:

1. **A Playseat instance** -- deployed, connected to your network, ingesting data
2. **One analyst** -- you, probably
3. **Three data sources** -- endpoint telemetry, network flow, authentication logs
4. **One SOAR playbook** -- automated triage for the most common alert type

That is it. Everything else scales from there.

### Platform Health Check

Before you build anything, verify the platform is healthy.

```bash
# Verify platform health
curl -s http://localhost:3000/health \
  -H "Authorization: Bearer $TOKEN" | jq '.'
```

```json
{
  "status": "healthy",
  "database": "connected",
  "version": "0.2.0"
}
```

If that does not return `"healthy"`, stop. Fix the infrastructure first. A SOC built on an unreliable platform is worse than no SOC at all, because it creates a false sense of security.

### Configuring Streaming Data Sources

Your first task is getting data flowing. The streaming analytics engine needs sources.

```bash
# Create endpoint telemetry source
curl -s -X POST http://localhost:3000/api/v1/stream/sources \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Endpoint Telemetry - EDR",
    "topic": "edr_events"
  }'
```

```json
{
  "id": "0194g100-sr01-7000-8000-000000000001"
}
```

```bash
# Create network flow source
curl -s -X POST http://localhost:3000/api/v1/stream/sources \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Network Flow - NetFlow v9",
    "topic": "netflow_events"
  }'
```

```json
{
  "id": "0194g100-sr02-7000-8000-000000000001"
}
```

```bash
# Create authentication log source
curl -s -X POST http://localhost:3000/api/v1/stream/sources \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Authentication - Active Directory",
    "topic": "ad_auth_events"
  }'
```

```json
{
  "id": "0194g100-sr03-7000-8000-000000000001"
}
```

```bash
# Verify all sources are active
curl -s http://localhost:3000/api/v1/stream/sources \
  -H "Authorization: Bearer $TOKEN" | jq '.'
```

### Configure Streaming Windows and Aggregations

Raw events are noise. Aggregations turn noise into signal.

```bash
# Create a 5-minute tumbling window for alert correlation
curl -s -X POST http://localhost:3000/api/v1/stream/windows \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Alert Correlation Window",
    "window_type": "tumbling",
    "duration_secs": 300
  }'
```

```json
{
  "id": "0194g100-wn01-7000-8000-000000000001"
}
```

```bash
# Create aggregation for failed authentication attempts
curl -s -X POST http://localhost:3000/api/v1/stream/aggregations \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Failed Auth by Source IP",
    "group_by": "source_ip",
    "agg_function": "count_where(event_type=auth_failure)"
  }'
```

```json
{
  "id": "0194g100-ag01-7000-8000-000000000001"
}
```

### Create Behavioral Baselines

On day one, you do not have baselines. You need to start building them immediately, because behavioral detection only works once you know what "normal" looks like.

```bash
# Create baseline for domain controller authentication patterns
curl -s -X POST http://localhost:3000/behavioral/baselines \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "entity_id": "0194g100-dc01-7000-8000-000000000001",
    "entity_type": "host",
    "category": "authentication_volume"
  }' | jq
```

```json
{
  "id": "0194g101-bl01-7000-8000-000000000001",
  "entity_id": "0194g100-dc01-7000-8000-000000000001",
  "entity_type": "host",
  "category": "authentication_volume",
  "baseline_data": {},
  "sample_count": 0,
  "created_at": "2026-02-18T08:00:00Z"
}
```

Sample count zero. The baseline is empty. It will take 7-14 days to build a statistically meaningful baseline. During that time, you are blind to behavioral anomalies. Accept that. Do not try to shortcut it by lowering thresholds -- you will drown in false positives.

I made that mistake with my first SOC. I set anomaly thresholds at 2 standard deviations on day three. We got 847 alerts in the first hour. My analyst quit.

---

## Part 2: Team Structure -- Tier 1/2/3 Workflows

### The Three-Tier Model

| Tier | Role | Count (Start) | Count (Scale) | Focus |
|------|------|--------------|---------------|-------|
| Tier 1 | SOC Analyst | 3 (24/7 coverage) | 12-18 | Alert triage, initial response |
| Tier 2 | Senior Analyst | 1 | 4-6 | Investigation, correlation, hunting |
| Tier 3 | Specialist | 0 (you) | 4-8 | Forensics, malware, threat intel |

At minimum viable, you need 3 Tier 1 analysts for 24/7 coverage (three 8-hour shifts). You are the Tier 2 and Tier 3 combined. That is brutal, but it works for the first 3-6 months while you prove value to the board.

### Shift Management API

```bash
# Create the three standard shifts
curl -s -X POST http://localhost:3000/api/v1/shifts/shifts \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Alpha Shift (Day)",
    "start_time": "06:00",
    "end_time": "14:00",
    "timezone": "CET"
  }'
```

```json
{
  "id": "0194g200-sh01-7000-8000-000000000001"
}
```

```bash
curl -s -X POST http://localhost:3000/api/v1/shifts/shifts \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Bravo Shift (Swing)",
    "start_time": "14:00",
    "end_time": "22:00",
    "timezone": "CET"
  }'
```

```json
{
  "id": "0194g200-sh02-7000-8000-000000000001"
}
```

```bash
curl -s -X POST http://localhost:3000/api/v1/shifts/shifts \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Charlie Shift (Night)",
    "start_time": "22:00",
    "end_time": "06:00",
    "timezone": "CET"
  }'
```

```json
{
  "id": "0194g200-sh03-7000-8000-000000000001"
}
```

### Creating Shift Rosters

```bash
# Assign analysts to Alpha shift
curl -s -X POST http://localhost:3000/api/v1/shifts/rosters \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "shift_id": "0194g200-sh01-7000-8000-000000000001",
    "analyst_ids": ["analyst-001", "analyst-002"]
  }'
```

```json
{
  "id": "0194g200-ro01-7000-8000-000000000001"
}
```

### Shift Handoff Protocol

Handoffs are where SOCs fail. If the night shift discovers something and the day shift does not know about it, you have a gap. Playseat enforces structured handoffs.

```bash
# Execute shift handoff
curl -s -X POST http://localhost:3000/api/v1/shifts/handoff \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "from_shift_id": "0194g200-sh03-7000-8000-000000000001",
    "to_shift_id": "0194g200-sh01-7000-8000-000000000001",
    "notes": "3 open alerts: 1 critical (UEBA anomaly on finance server, assigned to Tier 2), 2 medium (brute force attempts from external IPs, SOAR auto-blocked). ADAPT cycle 4721 completed overnight, 2 new correlations pending review. No active incidents."
  }'
```

```json
{
  "status": "handed_off"
}
```

### SOC Shift Tracking

```bash
# Start a shift for an analyst
curl -s -X POST http://localhost:3000/api/v1/soc/shifts \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "analyst_name": "Maria Santos",
    "shift_type": "night",
    "notes": "Covering Charlie Shift. Handoff received from Bravo at 22:00."
  }' | jq
```

```json
{
  "id": "0194g201-ss01-7000-8000-000000000001",
  "analyst_name": "Maria Santos",
  "shift_type": "night",
  "status": "active",
  "started_at": "2026-02-18T22:00:00Z"
}
```

```bash
# Check active shifts
curl -s http://localhost:3000/api/v1/soc/shifts/active \
  -H "Authorization: Bearer $TOKEN" | jq '.'
```

---

## Part 3: Alert Triage with AI Pipeline

### The Triage Workflow

Every alert follows the same path:

```
Alert Created -> Pending -> Assigned -> Triaged -> Resolved
                                |
                                v
                         (true_positive) -> Incident
                         (false_positive) -> Closed
                         (benign_true_positive) -> Tuned
```

### Tier 1 Alert Triage

When a Tier 1 analyst starts their shift, they pull the pending alerts.

```bash
# Get pending alerts sorted by severity
curl -s http://localhost:3000/api/v1/alerts/queue/pending \
  -H "Authorization: Bearer $TOKEN" | jq 'sort_by(.severity) | reverse'
```

```json
[
  {
    "id": "0194g300-al01-7000-8000-000000000001",
    "alert_name": "UEBA: Anomalous Admin Account Login Pattern",
    "source": "behavioral_analytics",
    "severity": "critical",
    "status": "pending",
    "context": {
      "entity": "svc-backup-admin",
      "deviation_score": 3.8,
      "risk_score": 0.89
    },
    "created_at": "2026-02-18T03:22:00Z"
  },
  {
    "id": "0194g300-al02-7000-8000-000000000001",
    "alert_name": "Brute Force: 47 Failed Logins from External IP",
    "source": "streaming_analytics",
    "severity": "medium",
    "status": "pending",
    "context": {
      "source_ip": "185.143.223.47",
      "target": "VPN Gateway",
      "attempts": 47,
      "window_minutes": 5
    },
    "created_at": "2026-02-18T04:15:00Z"
  }
]
```

### Assigning an Alert

```bash
# Assign the critical alert to a Tier 2 analyst
curl -s -X PUT http://localhost:3000/api/v1/alerts/queue/0194g300-al01-7000-8000-000000000001/assign \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "assigned_to": "tier2.lead"
  }' | jq
```

### Triaging with AI Assistance

For Tier 1 analysts, the NL Query module is a force multiplier. Instead of writing SQL, they ask questions in natural language.

```bash
# Use NL Query for investigation
curl -s -X POST http://localhost:3000/api/v1/nlquery/ask \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Show me all authentication events for svc-backup-admin in the last 7 days, grouped by source IP and time of day"
  }' | jq
```

```json
{
  "query_id": "0194g301-nq01-7000-8000-000000000001",
  "intent": "authentication_pattern_analysis",
  "generated_sql": "SELECT DATE_TRUNC('hour', timestamp) AS hour, details->>'source_ip' AS source_ip, COUNT(*) AS auth_count FROM stream_events WHERE details->>'user' = 'svc-backup-admin' AND timestamp >= NOW() - INTERVAL '7 days' GROUP BY hour, source_ip ORDER BY hour DESC",
  "results": [
    {"hour": "2026-02-18T03:00", "source_ip": "10.80.60.22", "auth_count": 3},
    {"hour": "2026-02-17T09:00", "source_ip": "10.80.60.10", "auth_count": 1},
    {"hour": "2026-02-17T10:00", "source_ip": "10.80.60.10", "auth_count": 2},
    {"hour": "2026-02-16T09:00", "source_ip": "10.80.60.10", "auth_count": 1}
  ],
  "interpretation": "The account normally authenticates during business hours from 10.80.60.10 (jump server). The 03:00 authentication from 10.80.60.22 is anomalous."
}
```

A Tier 1 analyst just performed a behavioral investigation using natural language. No SQL skills required. That is how you make a SOC scale -- you lower the skill barrier for common tasks.

### Triage Decision

```bash
# Triage the alert
curl -s -X PUT http://localhost:3000/api/v1/alerts/queue/0194g300-al01-7000-8000-000000000001/triage \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "triage_result": "true_positive",
    "severity_override": "critical",
    "notes": "svc-backup-admin authenticated from non-baseline IP at 03:00. NL Query confirms this source IP (10.80.60.22) has never been used by this account. Escalating to incident.",
    "recommended_action": "create_incident"
  }' | jq
```

### Alert Statistics

```bash
# Get alert triage stats for the SOC
curl -s http://localhost:3000/api/v1/alerts/stats \
  -H "Authorization: Bearer $TOKEN" | jq '.'
```

```json
{
  "total_alerts_24h": 127,
  "pending": 3,
  "assigned": 5,
  "triaged": 114,
  "resolved": 5,
  "triage_results": {
    "true_positive": 12,
    "false_positive": 89,
    "benign_true_positive": 13,
    "escalated_to_incident": 2
  },
  "mean_triage_time_minutes": 4.7,
  "false_positive_rate": 0.70,
  "auto_triaged_by_soar": 67
}
```

A 70% false positive rate is normal for a young SOC. Do not panic. It drops to 15-20% within 6 months as you tune your detection rules and SOAR playbooks handle the repetitive stuff.

---

## Part 4: 10 Essential SOAR Playbooks for Day One

These are the playbooks that will save your analysts' sanity. Each one automates a repetitive task that would otherwise consume hours of Tier 1 time.

### Playbook 1: Brute Force Auto-Block

```bash
# Create brute force playbook
curl -s -X POST http://localhost:3000/soar/playbooks \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "PB-BRUTE-FORCE-001",
    "description": "Auto-blocks external IPs after 10+ failed auth attempts in 5 minutes. Adds IOC. Resolves alert.",
    "trigger_type": "alert_auto",
    "trigger_config": {
      "alert_source": "streaming_analytics",
      "alert_pattern": "brute_force",
      "min_attempts": 10,
      "window_minutes": 5
    }
  }' | jq
```

```json
{
  "id": "0194g400-pb01-7000-8000-000000000001",
  "name": "PB-BRUTE-FORCE-001",
  "status": "draft"
}
```

```bash
# Add steps
curl -s -X POST http://localhost:3000/soar/playbooks/0194g400-pb01-7000-8000-000000000001/steps \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Block Source IP at Firewall",
    "action_type": "firewall_block_ip",
    "action_config": {"duration_hours": 24, "direction": "inbound"},
    "timeout_secs": 30,
    "requires_approval": false,
    "on_failure": "alert_analyst"
  }' | jq
```

```bash
# Activate the playbook
curl -s -X POST http://localhost:3000/soar/playbooks/0194g400-pb01-7000-8000-000000000001/activate \
  -H "Authorization: Bearer $TOKEN" | jq
```

### Playbooks 2-10: The Complete Day-One Set

Here is the complete set. I am showing the creation calls for each.

```bash
# PB-002: Phishing Email Auto-Quarantine
curl -s -X POST http://localhost:3000/soar/playbooks \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "PB-PHISHING-QUARANTINE-002",
    "description": "Auto-quarantines reported phishing emails, extracts IOCs, blocks sender domain.",
    "trigger_type": "alert_auto",
    "trigger_config": {"alert_source": "email_security", "alert_pattern": "phishing_reported"}
  }'

# PB-003: Malware Detection Auto-Isolate
curl -s -X POST http://localhost:3000/soar/playbooks \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "PB-MALWARE-ISOLATE-003",
    "description": "Auto-isolates endpoint on confirmed malware detection. Preserves memory. Creates forensic case.",
    "trigger_type": "alert_auto",
    "trigger_config": {"alert_source": "edr", "severity": ["critical", "high"]}
  }'

# PB-004: Suspicious PowerShell Triage
curl -s -X POST http://localhost:3000/soar/playbooks \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "PB-POWERSHELL-TRIAGE-004",
    "description": "Auto-collects PowerShell script block logs, checks for obfuscation, enriches with threat intel.",
    "trigger_type": "alert_auto",
    "trigger_config": {"alert_source": "edr", "alert_pattern": "suspicious_powershell"}
  }'

# PB-005: Failed MFA Auto-Lockout
curl -s -X POST http://localhost:3000/soar/playbooks \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "PB-MFA-LOCKOUT-005",
    "description": "Locks account after 5 MFA failures. Notifies user and SOC. Requires manual unlock.",
    "trigger_type": "alert_auto",
    "trigger_config": {"alert_source": "identity", "alert_pattern": "mfa_failure_threshold"}
  }'

# PB-006: Tor Exit Node Connection Block
curl -s -X POST http://localhost:3000/soar/playbooks \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "PB-TOR-BLOCK-006",
    "description": "Blocks outbound connections to known Tor exit nodes. Alerts analyst for investigation.",
    "trigger_type": "alert_auto",
    "trigger_config": {"alert_source": "network_flow", "alert_pattern": "tor_connection"}
  }'

# PB-007: New Admin Account Alert
curl -s -X POST http://localhost:3000/soar/playbooks \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "PB-NEW-ADMIN-007",
    "description": "Alerts on new admin account creation. Verifies against change request system.",
    "trigger_type": "alert_auto",
    "trigger_config": {"alert_source": "ad_monitoring", "alert_pattern": "admin_account_created"}
  }'

# PB-008: External Scan Detection
curl -s -X POST http://localhost:3000/soar/playbooks \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "PB-SCAN-DETECT-008",
    "description": "Detects and blocks external port scanning. Enriches source IP with threat intel.",
    "trigger_type": "alert_auto",
    "trigger_config": {"alert_source": "network_flow", "alert_pattern": "port_scan_external"}
  }'

# PB-009: Certificate Expiry Warning
curl -s -X POST http://localhost:3000/soar/playbooks \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "PB-CERT-EXPIRY-009",
    "description": "Alerts on certificates expiring within 30 days. Creates remediation ticket.",
    "trigger_type": "scheduled",
    "trigger_config": {"schedule": "daily_0800", "check_type": "certificate_expiry"}
  }'

# PB-010: Ransomware Early Detection
curl -s -X POST http://localhost:3000/soar/playbooks \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "PB-RANSOMWARE-EARLY-010",
    "description": "Detects file entropy spikes indicating encryption. Auto-isolates host. Preserves memory.",
    "trigger_type": "alert_auto",
    "trigger_config": {"alert_source": "streaming_analytics", "alert_pattern": "file_entropy_spike"}
  }'
```

### SOAR Efficiency Stats

```bash
# Check SOAR efficiency
curl -s http://localhost:3000/soar/stats/efficiency \
  -H "Authorization: Bearer $TOKEN" | jq '.'
```

```json
{
  "total_executions_30d": 1847,
  "successful_executions": 1789,
  "failed_executions": 58,
  "success_rate": 0.969,
  "mean_execution_time_seconds": 12.4,
  "analyst_hours_saved_30d": 312.5,
  "auto_resolved_alerts": 1423,
  "auto_resolution_rate": 0.77,
  "playbook_rankings": [
    {"name": "PB-BRUTE-FORCE-001", "executions": 487, "success_rate": 0.99},
    {"name": "PB-PHISHING-QUARANTINE-002", "executions": 312, "success_rate": 0.97},
    {"name": "PB-SCAN-DETECT-008", "executions": 289, "success_rate": 0.98},
    {"name": "PB-POWERSHELL-TRIAGE-004", "executions": 201, "success_rate": 0.94}
  ]
}
```

312.5 analyst hours saved per month. At an average Tier 1 cost of EUR 45/hour, that is EUR 14,062 in direct labor savings monthly. Ten playbooks. EUR 168K annual savings. That is your first ROI number for the board.

---

## Part 5: Metrics That Matter

### The Four Metrics That Define SOC Performance

```sql
-- SOC KPI Dashboard Query
SELECT
    -- MTTD: Mean Time to Detect
    AVG(EXTRACT(EPOCH FROM (a.created_at - a.context->>'first_event_time')::INTERVAL)) / 60.0 AS mttd_minutes,

    -- MTTR: Mean Time to Respond (triage + initial response)
    AVG(EXTRACT(EPOCH FROM (a.triaged_at - a.created_at))) / 60.0 AS mttr_minutes,

    -- False Positive Rate
    COUNT(*) FILTER (WHERE a.triage_result = 'false_positive')::FLOAT / COUNT(*) AS fp_rate,

    -- Alert Volume
    COUNT(*) AS total_alerts,
    COUNT(*) / 30.0 AS alerts_per_day

FROM alert_queue a
WHERE a.created_at >= NOW() - INTERVAL '30 days'
  AND a.status IN ('triaged', 'resolved');
```

| Metric | Your Target (Day 1) | Your Target (Month 6) | World Class |
|--------|---------------------|----------------------|-------------|
| MTTD | < 60 minutes | < 15 minutes | < 5 minutes |
| MTTR | < 30 minutes | < 10 minutes | < 3 minutes |
| False Positive Rate | < 80% | < 30% | < 10% |
| Alerts per Analyst per Day | < 50 | < 30 | < 15 |

The false positive rate will be terrible at first. That is expected. Every time you tune a rule or add a SOAR playbook, it drops. Track the trend, not the absolute number.

### KPI Tracking API

```bash
# Create KPI trackers
curl -s -X POST http://localhost:3000/api/v1/kpi-trackers/create \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "kpis": [
      {"name": "MTTD", "unit": "minutes", "target": 15, "direction": "lower_is_better"},
      {"name": "MTTR", "unit": "minutes", "target": 10, "direction": "lower_is_better"},
      {"name": "False Positive Rate", "unit": "percentage", "target": 30, "direction": "lower_is_better"},
      {"name": "SOAR Auto-Resolution Rate", "unit": "percentage", "target": 70, "direction": "higher_is_better"},
      {"name": "Evidence Chain Integrity", "unit": "percentage", "target": 100, "direction": "higher_is_better"},
      {"name": "Analyst Hours Saved (SOAR)", "unit": "hours", "target": 300, "direction": "higher_is_better"}
    ]
  }' | jq
```

### SOC Performance Stats

```bash
# Get SOC overall stats
curl -s http://localhost:3000/api/v1/soc/stats \
  -H "Authorization: Bearer $TOKEN" | jq '.'
```

```json
{
  "total_shifts_30d": 90,
  "total_analyst_hours_30d": 720,
  "alerts_handled_30d": 3847,
  "alerts_per_analyst_hour": 5.34,
  "escalations_30d": 23,
  "escalation_rate": 0.006,
  "shift_coverage_rate": 1.0,
  "overtime_hours_30d": 12
}
```

### Shift-Level Performance

```bash
# Get shift coverage report
curl -s http://localhost:3000/api/v1/shifts/coverage \
  -H "Authorization: Bearer $TOKEN" | jq '.'
```

```json
{
  "status": "ok",
  "coverage": {
    "alpha_shift": {"coverage_rate": 1.0, "avg_alerts_per_shift": 47},
    "bravo_shift": {"coverage_rate": 1.0, "avg_alerts_per_shift": 38},
    "charlie_shift": {"coverage_rate": 0.95, "avg_alerts_per_shift": 42}
  }
}
```

Charlie shift at 95% coverage means 1-2 gaps per month. That needs fixing. Night shift gaps are where incidents happen.

---

## Part 6: The NL Query Power Tool for Tier 1

Natural Language Query is what makes Tier 1 analysts effective from day one. Instead of training them on SQL and log formats for six months, you train them to ask questions.

### Common NL Queries for SOC Analysts

```bash
# "What happened on this host in the last hour?"
curl -s -X POST http://localhost:3000/api/v1/nlquery/ask \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query": "Show me all events on host 10.0.1.50 in the last hour sorted by time"}'
```

```bash
# "Is this IP known bad?"
curl -s -X POST http://localhost:3000/api/v1/nlquery/ask \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query": "Check if IP 185.143.223.47 appears in any threat intel feeds or IOC lists"}'
```

```bash
# "How many alerts did we get today by severity?"
curl -s -X POST http://localhost:3000/api/v1/nlquery/ask \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query": "Count today alerts grouped by severity"}'
```

### Create NL Query Templates

For common SOC questions, create templates so the NL engine responds faster and more accurately.

```bash
# Create a template for host investigation
curl -s -X POST http://localhost:3000/api/v1/nlquery/templates \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Host Event Investigation",
    "pattern": "show.*events.*host.*{ip}.*last.*{duration}",
    "intent": "host_event_lookup",
    "sql_template": "SELECT timestamp, event_type, source, severity, details FROM stream_events WHERE source_ip = $1 AND timestamp >= NOW() - INTERVAL $2 ORDER BY timestamp DESC LIMIT 100",
    "parameters": {"ip": "string", "duration": "interval"},
    "examples": [
      "show me events on host 10.0.1.50 last 24 hours",
      "what happened on 10.0.1.50 in the last hour"
    ],
    "priority": 1
  }' | jq
```

---

## Part 7: Command Center Dashboard Configuration

### Dashboard API

The command center is what goes on the big screens in the SOC.

```bash
# Get the ADAPT dashboard overview
curl -s http://localhost:3000/api/v1/adapt/dashboard \
  -H "Authorization: Bearer $TOKEN" | jq '.'
```

```json
{
  "global_risk_score": 34.2,
  "active_cycles": 2,
  "pending_actions": 7,
  "open_incidents": 2,
  "critical_alerts": 1,
  "soar_executions_24h": 47,
  "streaming_eps": 1247,
  "behavioral_anomalies_24h": 3,
  "threat_feeds_active": 5,
  "coverage_score": 0.78,
  "last_updated": "2026-02-18T14:00:00Z"
}
```

### Global Risk Score

```bash
# Get the global security score
curl -s http://localhost:3000/api/v1/adapt/score/global \
  -H "Authorization: Bearer $TOKEN" | jq '.'
```

```json
{
  "global_score": 34.2,
  "components": {
    "exposure_score": 28.5,
    "threat_score": 42.0,
    "vulnerability_score": 31.1,
    "compliance_score": 35.2
  },
  "trend": "improving",
  "trend_delta_30d": -8.3,
  "risk_level": "moderate"
}
```

Score trending down (improving) by 8.3 points over 30 days. That is the kind of metric a board understands.

---

## Part 8: Scaling from 5 to 50 People

### The Scaling Milestones

| Team Size | Structure | Key Changes |
|-----------|-----------|-------------|
| 3-5 | Flat. Everyone does everything. | Survive. Build playbooks. Prove value. |
| 5-10 | Add Tier 2. Split triage from investigation. | Hire specialists. Add threat hunting. |
| 10-20 | Add Tier 3. Dedicated forensics and threat intel. | Formalize processes. Add ADAPT cycles. |
| 20-35 | Add SOC Manager. Split into functional teams. | Add shift leads. Build career paths. |
| 35-50 | Full maturity. Purple team. 24/7 dedicated coverage. | Optimize. Automate. Prove ROI monthly. |

### Budget Justification with ROI Metrics

Here is the conversation I have with every board:

```bash
# Get ROI calculations
curl -s http://localhost:3000/api/v1/roi-calculations \
  -H "Authorization: Bearer $TOKEN" | jq '.'
```

```json
{
  "roi_calculations": [
    {
      "period": "2025-Q4",
      "incidents_handled": 12,
      "losses_prevented_eur": 2400000,
      "soar_labor_savings_eur": 42000,
      "false_positive_reduction_savings_eur": 18000,
      "total_value_eur": 2460000,
      "soc_cost_eur": 450000,
      "roi_percentage": 447
    }
  ],
  "count": 1
}
```

447% ROI in the first quarter. That is how you get budget. Not by talking about threats in abstract terms, but by showing the board a number they understand: "We spent EUR 450K and prevented EUR 2.46M in losses."

### The Budget Template

| Line Item | Year 1 | Year 2 | Year 3 |
|-----------|--------|--------|--------|
| Platform License | EUR 180,000 | EUR 180,000 | EUR 180,000 |
| Tier 1 Analysts (3 FTE) | EUR 195,000 | EUR 195,000 | EUR 195,000 |
| Tier 2 Analysts (1 FTE) | EUR 85,000 | EUR 170,000 | EUR 170,000 |
| Tier 3 Specialist (0.5 FTE) | EUR 55,000 | EUR 110,000 | EUR 165,000 |
| Training | EUR 25,000 | EUR 15,000 | EUR 15,000 |
| **Total** | **EUR 540,000** | **EUR 670,000** | **EUR 725,000** |
| **Expected Loss Prevention** | **EUR 2.4M** | **EUR 5.0M** | **EUR 8.0M** |
| **ROI** | **344%** | **646%** | **1,003%** |

The numbers get better every year because your detection capability compounds. Year 1, you catch the obvious stuff. Year 2, you catch the subtle stuff. Year 3, you are running ADAPT cycles and catching APTs before they get past initial access.

---

## Part 9: SOC Setup Complete Checklist

This is the checklist I use on day one of every SOC build.

```sql
-- SOC Readiness Check Query
SELECT
    'Streaming Sources' AS component,
    COUNT(*) AS count,
    CASE WHEN COUNT(*) >= 3 THEN 'READY' ELSE 'INCOMPLETE' END AS status
FROM stream_sources WHERE status = 'active'

UNION ALL

SELECT
    'SOAR Playbooks',
    COUNT(*),
    CASE WHEN COUNT(*) >= 10 THEN 'READY' ELSE 'INCOMPLETE' END
FROM soar_playbooks WHERE status = 'active'

UNION ALL

SELECT
    'Behavioral Baselines',
    COUNT(*),
    CASE WHEN COUNT(*) >= 5 THEN 'READY' ELSE 'BUILDING' END
FROM behavioral_baselines WHERE sample_count >= 100

UNION ALL

SELECT
    'Threat Intel Feeds',
    COUNT(*),
    CASE WHEN COUNT(*) >= 3 THEN 'READY' ELSE 'INCOMPLETE' END
FROM threat_intel_feeds WHERE status = 'active'

UNION ALL

SELECT
    'Shift Schedules',
    COUNT(*),
    CASE WHEN COUNT(*) >= 3 THEN 'READY' ELSE 'INCOMPLETE' END
FROM shift_schedules WHERE active = true;
```

| Component | Count | Status |
|-----------|-------|--------|
| Streaming Sources | 5 | READY |
| SOAR Playbooks | 10 | READY |
| Behavioral Baselines | 8 | READY |
| Threat Intel Feeds | 4 | READY |
| Shift Schedules | 3 | READY |

When every row says READY, you are operational. Open the SOC. Start the shifts. Take your first alert.

---

## The Real Talk

Building a SOC is hard. The first three months are brutal. You will be understaffed, underfunded, and drowning in false positives. Your analysts will complain about alert fatigue. Your boss will ask why you are not catching everything. Your board will question the investment.

Here is what I tell every SOC manager I mentor: **The goal is not perfection. The goal is improvement.** Track your metrics every week. Show the trend. Week 1: 80% false positive rate. Week 12: 45%. Week 24: 22%. That downward line is your career.

Build the playbooks. Tune the rules. Train the analysts. Run the tabletops. Improve the ADAPT cycles. And above all, prove your value in numbers the business understands.

The SOC that can demonstrate its ROI never gets its budget cut. The SOC that runs on "trust us, threats are real" gets eliminated in the next cost reduction exercise.

I have seen both happen. Build the first kind.

---

## Complete API Call Reference

| Section | Module | Endpoint | Purpose |
|---------|--------|----------|---------|
| Setup | Health | `/health` | Platform health check |
| Setup | Streaming | `/api/v1/stream/sources` | Create data sources |
| Setup | Streaming | `/api/v1/stream/windows` | Create correlation windows |
| Setup | Streaming | `/api/v1/stream/aggregations` | Create aggregations |
| Setup | Behavioral | `/behavioral/baselines` | Create baselines |
| Shifts | Shift Mgr | `/api/v1/shifts/shifts` | Create shifts |
| Shifts | Shift Mgr | `/api/v1/shifts/rosters` | Assign analysts |
| Shifts | Shift Mgr | `/api/v1/shifts/handoff` | Shift handoff |
| Shifts | Shift Mgr | `/api/v1/shifts/coverage` | Coverage report |
| Shifts | SOC | `/api/v1/soc/shifts` | Analyst shift tracking |
| Shifts | SOC | `/api/v1/soc/shifts/active` | Active shifts |
| Shifts | SOC | `/api/v1/soc/stats` | SOC statistics |
| Triage | Alerts | `/api/v1/alerts/queue/pending` | Pending alerts |
| Triage | Alerts | `/api/v1/alerts/queue/{id}/assign` | Assign alert |
| Triage | Alerts | `/api/v1/alerts/queue/{id}/triage` | Triage alert |
| Triage | Alerts | `/api/v1/alerts/stats` | Alert statistics |
| NL Query | NLQ | `/api/v1/nlquery/ask` | Natural language query |
| NL Query | NLQ | `/api/v1/nlquery/templates` | Create query templates |
| SOAR | SOAR | `/soar/playbooks` | Create playbooks |
| SOAR | SOAR | `/soar/playbooks/{id}/steps` | Add playbook steps |
| SOAR | SOAR | `/soar/playbooks/{id}/activate` | Activate playbook |
| SOAR | SOAR | `/soar/stats/efficiency` | SOAR efficiency metrics |
| Metrics | KPI | `/api/v1/kpi-trackers/create` | Create KPI trackers |
| Metrics | ADAPT | `/api/v1/adapt/dashboard` | Dashboard overview |
| Metrics | ADAPT | `/api/v1/adapt/score/global` | Global risk score |
| Budget | ROI | `/api/v1/roi-calculations` | ROI calculations |
| Budget | Shifts | `/api/v1/shifts/stats` | Shift statistics |

---

*This guide is based on operational experience building SOCs for defense contractors, financial institutions, and government agencies. Your mileage will vary based on organizational size, threat landscape, and budget. Start small, prove value, scale.*

---

(c) 2026 Playseat -- All Rights Reserved | Proprietary and Confidential
