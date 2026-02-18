# Chapter 34 -- Incident Response: The Complete Operator's Playbook

> "Incident response is not a checklist you follow. It is a muscle you train. Every phase has decisions that depend on context, and the only way to make those decisions well under pressure is to have made them a hundred times before -- in tabletops, in drills, and in this platform. This chapter gives you the muscle memory."

---

## The Incident Response Lifecycle in Playseat

Playseat follows a six-phase model that maps to NIST SP 800-61r3 and SANS PICERL:

| Phase | NIST Mapping | Playseat Module | Key Question |
|-------|-------------|-----------------|-------------|
| Phase 0: Preparation | Preparation | SOAR + Shifts + ADAPT | "Are we ready?" |
| Phase 1: Detection | Detection & Analysis | Streaming + UEBA + Alert Triage | "Is this real?" |
| Phase 2: Containment | Containment | SOAR + Incident + ADAPT | "How do we stop the bleeding?" |
| Phase 3: Investigation | Analysis (continued) | Forensics + Ontology + Threat Intel | "What happened and how?" |
| Phase 4: Eradication | Eradication | ADAPT + SOAR + Endpoint | "Are we clean?" |
| Phase 5: Recovery | Recovery | ADAPT VALIDATE + Monitoring | "Are we safe to restore?" |
| Phase 6: Lessons Learned | Post-Incident | Incident Lessons + ADAPT PROVE | "What did we learn?" |

Every phase has specific API calls, specific decision points, and specific evidence requirements. Let me walk you through all of them.

---

## Phase 0: Preparation -- Before the Incident

Preparation is the most important phase and the one everyone skips. I have been in rooms where a CISO said "we will figure it out when it happens." Those are the rooms where people panic during incidents.

### Team Roster

You need a documented team with clear roles and contact information. Not "we know who to call." Documented. In the platform.

```bash
# Create the IR team roster as shifts
curl -s -X POST http://localhost:3000/api/v1/shifts/shifts \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "IR Team - On Call",
    "start_time": "00:00",
    "end_time": "23:59",
    "timezone": "CET"
  }'
```

```json
{
  "id": "0194h100-sh01-7000-8000-000000000001"
}
```

```bash
# Assign the IR team
curl -s -X POST http://localhost:3000/api/v1/shifts/rosters \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "shift_id": "0194h100-sh01-7000-8000-000000000001",
    "analyst_ids": ["ic_primary", "ic_backup", "forensics_lead", "soar_lead", "network_lead", "legal_counsel", "comms_lead"]
  }'
```

### Pre-Built SOAR Playbooks

You need playbooks for your top 5 incident types BEFORE the incident. Not during.

```bash
# List all active SOAR playbooks
curl -s http://localhost:3000/soar/playbooks \
  -H "Authorization: Bearer $TOKEN" | jq '.playbooks[] | select(.status == "active") | {name, trigger_type, version}'
```

```json
[
  {"name": "PB-RANSOMWARE-CRITICAL-001", "trigger_type": "alert_triage", "version": 4},
  {"name": "PB-APT-INVESTIGATION-002", "trigger_type": "manual", "version": 2},
  {"name": "PB-DATA-BREACH-003", "trigger_type": "alert_triage", "version": 3},
  {"name": "PB-INSIDER-THREAT-004", "trigger_type": "alert_triage", "version": 2},
  {"name": "PB-DDOS-RESPONSE-005", "trigger_type": "alert_auto", "version": 3}
]
```

Five playbooks. Five versions each (at least two). Each one tested in at least two tabletop exercises. If you have not tested a playbook, it does not exist. It is a document, not a capability.

### Communication Plan

During an incident, you need to know:
- Who talks to the press? (Not you.)
- Who talks to regulators? (Legal counsel.)
- Who talks to law enforcement? (IC only.)
- Who talks to affected customers? (Comms lead, with legal review.)

```bash
# Create incident communication playbook
curl -s -X POST http://localhost:3000/soar/playbooks \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "PB-COMMS-PLAN-IR-001",
    "description": "Automated incident communications. Notifies IR team, activates war room, pre-drafts regulatory notifications based on incident classification.",
    "trigger_type": "incident_created",
    "trigger_config": {
      "incident_priority": ["critical", "high"],
      "auto_notify": true
    }
  }' | jq
```

### ADAPT Autopilot Configuration

Your ADAPT Autopilot should be running continuously. During preparation, configure it for aggressive detection.

```bash
# Check autopilot config
curl -s http://localhost:3000/api/v1/adapt/autopilot/config \
  -H "Authorization: Bearer $TOKEN" | jq '.'
```

```json
{
  "enabled": true,
  "cycle_interval_hours": 4,
  "auto_discover": true,
  "auto_correlate": true,
  "auto_validate": false,
  "auto_fortify": false,
  "escalation_threshold": "high",
  "heartbeat_interval_minutes": 15,
  "kill_switch_enabled": true
}
```

Auto-discover and auto-correlate are on. Auto-validate and auto-fortify are off -- because those actions can be noisy and might tip off an adversary. The kill switch is enabled so you can shut down the autopilot instantly if needed during an active incident.

---

## Phase 1: Detection -- "Is This Real?"

Detection is the transition from "everything is fine" to "something is wrong." The quality of your detection determines everything that follows.

### Alert Flow

Alerts come from five sources in Playseat:

| Source | Type | Speed | Accuracy |
|--------|------|-------|----------|
| Streaming Analytics | Rule-based, real-time | Milliseconds | High (if rules are good) |
| UEBA / Behavioral | Baseline deviation | Minutes | Very high (low FP) |
| ADAPT Cycle | Exposure discovery | Minutes to hours | Very high |
| Threat Intel Match | IOC correlation | Minutes | Moderate (depends on feed quality) |
| External Report | Human submission | Hours to days | Variable |

### The Triage Decision

When an alert arrives, the analyst must answer one question: **Is this a true positive?**

```bash
# Pull the alert
curl -s http://localhost:3000/api/v1/alerts/queue/0194h200-al01-7000-8000-000000000001 \
  -H "Authorization: Bearer $TOKEN" | jq '.'
```

```json
{
  "id": "0194h200-al01-7000-8000-000000000001",
  "alert_name": "Suspicious Lateral Movement: SMB to Domain Controller",
  "source": "streaming_analytics",
  "severity": "high",
  "status": "pending",
  "context": {
    "source_host": "WS-FINANCE-12 (10.0.1.47)",
    "destination_host": "DC-01 (10.0.1.5)",
    "protocol": "SMB",
    "user": "svc-backup",
    "time": "2026-02-18T03:17:00Z",
    "baseline_violation": "service_account_non_baseline_source"
  },
  "created_at": "2026-02-18T03:17:05Z"
}
```

The analyst investigates. They check three things:
1. Is the source IP expected for this account? (Check behavioral baseline.)
2. Is the time of day normal? (Check session patterns.)
3. Is there a change request or maintenance window? (Check with IT.)

```bash
# Check behavioral baseline for this entity
curl -s http://localhost:3000/behavioral/baselines/0194h200-bl01-7000-8000-000000000001 \
  -H "Authorization: Bearer $TOKEN" | jq '.'
```

```json
{
  "id": "0194h200-bl01-7000-8000-000000000001",
  "entity_id": "svc-backup",
  "entity_type": "user_account",
  "category": "authentication_pattern",
  "baseline_data": {
    "normal_source_ips": ["10.0.1.100"],
    "normal_hours": {"start": "01:00", "end": "03:00"},
    "normal_destinations": ["DC-01", "FILE-SRV-01", "BACKUP-SRV-01"],
    "normal_protocols": ["SMB", "RPC"]
  },
  "sample_count": 2847
}
```

Wait. The backup service account normally runs between 01:00 and 03:00, and DC-01 is a normal destination. The source IP is different (10.0.1.47 vs baseline 10.0.1.100), but that could be a reconfigured backup agent.

This is a judgment call. The analyst checks with IT ops, confirms there was a backup agent migration yesterday, and triages as benign true positive.

```bash
# Triage as benign true positive
curl -s -X PUT http://localhost:3000/api/v1/alerts/queue/0194h200-al01-7000-8000-000000000001/triage \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "triage_result": "benign_true_positive",
    "notes": "svc-backup source IP changed from .100 to .47 due to backup agent migration (IT ticket CHG-2847). Updating baseline.",
    "recommended_action": "update_baseline"
  }' | jq
```

### Promotion to Incident

When the triage result is true_positive and the severity warrants it, the alert becomes an incident.

```bash
# Create incident from alert
curl -s -X POST http://localhost:3000/api/v1/incident/incidents \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "INC-2026-0215: Unauthorized Access to Domain Controller via Stolen Credentials",
    "description": "Alert AL-2026-4782 confirmed true positive. Service account svc-exchange authenticated to DC-01 from non-baseline workstation using Kerberos ticket at 03:17. No maintenance window. No change request. Possible credential compromise.",
    "priority": "high",
    "affected_systems": ["DC-01", "WS-FINANCE-12"]
  }' | jq
```

```json
{
  "id": "0194h201-aa01-7000-8000-000000000001",
  "title": "INC-2026-0215: Unauthorized Access to Domain Controller via Stolen Credentials",
  "phase": "identification",
  "priority": "high",
  "status": "open",
  "created_at": "2026-02-18T03:25:00Z"
}
```

---

## Phase 2: Containment -- "How Do We Stop the Bleeding?"

Containment is where speed matters most. Every minute the attacker has access, they can exfiltrate data, move laterally, or destroy evidence.

### The Containment Decision Matrix

| Factor | Quick Contain | Measured Contain | Observe (No Contain) |
|--------|--------------|-----------------|---------------------|
| Active data destruction | YES | - | - |
| Active exfiltration | YES | - | - |
| Ransomware encryption | YES | - | - |
| Lateral movement detected | - | YES | - |
| Single compromised host | - | YES | - |
| APT (want to map scope) | - | - | YES |
| Insider threat (legal hold) | - | - | YES |

### SOAR-Assisted Containment

For quick containment, trigger a SOAR playbook.

```bash
# Execute containment via SOAR
curl -s -X POST http://localhost:3000/api/v1/incident/contain \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "incident_id": "0194h201-aa01-7000-8000-000000000001",
    "containment_type": "network_isolation",
    "target_host": "WS-FINANCE-12 (10.0.1.47)",
    "actions": ["network_isolate", "disable_user_account", "force_password_reset"],
    "approved_by": "ic_primary",
    "notes": "Isolating compromised workstation. Disabling svc-exchange. Forcing password reset for all accounts authenticated from this host in last 30 days."
  }' | jq
```

```json
{
  "id": "0194h202-cn01-7000-8000-000000000001",
  "incident_id": "0194h201-aa01-7000-8000-000000000001",
  "status": "executed",
  "actions_completed": 3,
  "rollback_available": true,
  "executed_at": "2026-02-18T03:28:00Z"
}
```

### Manual Containment with Evidence Preservation

For measured containment, you do it step by step, preserving evidence at each stage.

```bash
# Add containment timeline event
curl -s -X POST http://localhost:3000/api/v1/incident/incidents/0194h201-aa01-7000-8000-000000000001/timeline \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "event_type": "containment_action",
    "description": "STEP 1: Memory dump acquired from WS-FINANCE-12 before network isolation. STEP 2: Network isolation applied -- host quarantined to forensics VLAN. STEP 3: svc-exchange account disabled in AD. STEP 4: KRBTGT double-rotated to invalidate potential Golden Tickets.",
    "severity": "high",
    "source": "incident_commander"
  }' | jq
```

### Advance to Containment Phase

```bash
# Advance the incident
curl -s -X POST http://localhost:3000/api/v1/incident/incidents/0194h201-aa01-7000-8000-000000000001/advance \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "new_phase": "containment",
    "notes": "WS-FINANCE-12 isolated. svc-exchange disabled. KRBTGT rotated. Memory and disk evidence preserved. Moving to investigation."
  }' | jq
```

### Containment Rollback

Sometimes containment was too aggressive, or you contained the wrong host. Playseat tracks every containment action with a rollback capability.

```bash
# Rollback containment if needed
curl -s -X POST http://localhost:3000/api/v1/incident/contain/0194h202-cn01-7000-8000-000000000001/rollback \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "reason": "False positive confirmed after investigation. Host was performing legitimate backup operations.",
    "rollback_actions": ["restore_network", "re-enable_account"],
    "approved_by": "ic_primary"
  }' | jq
```

---

## Phase 3: Investigation -- "What Happened and How?"

Investigation is where you spend the most time. This is the detective work: building the timeline, mapping the kill chain, extracting IOCs, and understanding the attacker's objectives.

### Forensic Case Creation

Every investigation needs a forensic case. This creates the container for all evidence, artifacts, and the chain of custody.

```bash
# Create forensic case
curl -s -X POST http://localhost:3000/forensics/cases \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "campaign_id": "0194h201-aa01-7000-8000-000000000001",
    "title": "FORENSIC-2026-0215: DC Credential Compromise Investigation",
    "description": "Full forensic investigation of unauthorized DC access. Evidence collection for potential law enforcement referral.",
    "status": "active",
    "analyst": "forensics_lead"
  }' | jq
```

```json
{
  "id": "0194h300-fc01-7000-8000-000000000001",
  "status": "active",
  "analyst": "forensics_lead",
  "created_at": "2026-02-18T04:00:00Z"
}
```

### Memory Analysis

Always start with memory. Memory is volatile -- it disappears when the machine reboots. Disk evidence persists. Prioritize the ephemeral.

```bash
# Create memory dump entry
curl -s -X POST http://localhost:3000/api/v1/memforensics/dumps \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "source_host": "WS-FINANCE-12",
    "dump_format": "raw",
    "os_profile": "Win11x64_23H2"
  }'
```

```json
{
  "id": "0194h301-md01-7000-8000-000000000001"
}
```

```bash
# Analyze processes
curl -s http://localhost:3000/api/v1/memforensics/dumps/0194h301-md01-7000-8000-000000000001/processes \
  -H "Authorization: Bearer $TOKEN" | jq '.[] | select(.suspicious == true)'
```

```bash
# Check for injection
curl -s http://localhost:3000/api/v1/memforensics/dumps/0194h301-md01-7000-8000-000000000001/injections \
  -H "Authorization: Bearer $TOKEN" | jq '.'
```

```bash
# Find suspicious processes
curl -s http://localhost:3000/api/v1/memforensics/dumps/0194h301-md01-7000-8000-000000000001/suspicious \
  -H "Authorization: Bearer $TOKEN" | jq '.'
```

### Disk Forensics

```bash
# Initiate disk analysis
curl -s -X POST http://localhost:3000/forensics/disk/analyze \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "case_id": "0194h300-fc01-7000-8000-000000000001",
    "source_host": "WS-FINANCE-12",
    "disk_image_path": "/evidence/INC-2026-0215/WS-FINANCE-12/disk.E01",
    "analysis_type": "full",
    "include_deleted": true,
    "include_slack_space": true,
    "include_registry": true,
    "os_profile": "Win11x64_23H2"
  }' | jq
```

```bash
# Recover deleted files
curl -s -X POST http://localhost:3000/forensics/disk/0194h301-da01-7000-8000-000000000001/recover \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "recovery_targets": ["C:\\Users\\j.finance\\AppData\\Local\\Temp\\*"],
    "output_path": "/evidence/INC-2026-0215/recovered/",
    "preserve_metadata": true
  }' | jq
```

### Kill Chain Timeline

The timeline is the most important artifact in any investigation. It tells the story of the attack from first access to last action.

```bash
# Build the timeline
curl -s -X POST http://localhost:3000/forensics/timeline/build \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "case_id": "0194h300-fc01-7000-8000-000000000001",
    "start_time": "2026-02-10T00:00:00Z",
    "end_time": "2026-02-18T04:00:00Z",
    "sources": ["endpoint_detection", "ad_logs", "network_flow", "email_gateway", "proxy_logs"],
    "hosts": ["WS-FINANCE-12", "DC-01"],
    "enrichment": ["mitre_attack", "threat_intel", "geo"]
  }' | jq
```

```json
{
  "id": "0194h302-tl01-7000-8000-000000000001",
  "events_count": 1247,
  "critical_events": 18,
  "kill_chain": [
    {
      "phase": "initial_access",
      "mitre": "T1566.002",
      "timestamp": "2026-02-14T10:15:00Z",
      "host": "WS-FINANCE-12",
      "description": "Spearphishing link clicked. User directed to credential harvesting page.",
      "confidence": 0.94
    },
    {
      "phase": "credential_access",
      "mitre": "T1003.001",
      "timestamp": "2026-02-15T02:30:00Z",
      "host": "WS-FINANCE-12",
      "description": "Mimikatz variant executed. LSASS process accessed. Domain credentials harvested.",
      "confidence": 0.91
    },
    {
      "phase": "lateral_movement",
      "mitre": "T1021.002",
      "timestamp": "2026-02-18T03:17:00Z",
      "host": "DC-01",
      "description": "SMB lateral movement to domain controller using stolen svc-exchange credentials.",
      "confidence": 0.97
    }
  ]
}
```

### Timeline Anomaly Detection

```bash
# Detect anomalies in the timeline
curl -s http://localhost:3000/forensics/timeline/0194h302-tl01-7000-8000-000000000001/anomalies \
  -H "Authorization: Bearer $TOKEN" | jq '.'
```

```json
{
  "timeline_id": "0194h302-tl01-7000-8000-000000000001",
  "anomalies": [
    {
      "type": "timestamp_gap",
      "description": "No events from WS-FINANCE-12 between 2026-02-15T02:45:00Z and 2026-02-18T03:15:00Z. Possible log deletion or dormant period.",
      "significance": "high"
    },
    {
      "type": "timestamp_manipulation",
      "description": "svchost_helper.exe has a compilation timestamp of 2025-01-01T00:00:00Z but was first seen on 2026-02-14. Likely timestomped.",
      "significance": "medium"
    }
  ]
}
```

### IOC Extraction

Every investigation produces IOCs. Push them into the IOC manager immediately so your detection rules can catch repeat attacks.

```bash
# Add IOCs discovered during investigation
curl -s -X POST http://localhost:3000/api/v1/iocmanager \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "ioc_type": "file_hash",
    "value": "d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2c3d4",
    "source": "INC-2026-0215-FORENSICS",
    "confidence": 0.95,
    "tags": ["mimikatz-variant", "credential-theft", "lateral-movement"],
    "description": "Mimikatz variant hash found on WS-FINANCE-12. Timestomped to 2025-01-01."
  }' | jq
```

### Ontology Graph -- Visualizing the Attack

```bash
# Build ontology graph
curl -s -X POST http://localhost:3000/api/v1/ontology/graph \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "root_entity": "0194h201-aa01-7000-8000-000000000001",
    "entity_type": "incident",
    "depth": 5,
    "include_types": ["host", "user_account", "process", "file", "ip_address", "domain"]
  }' | jq
```

---

## Phase 4: Eradication -- "Are We Clean?"

Eradication is about finding every foothold the attacker has and removing it. If you miss one persistence mechanism, you will be back here in a week.

### ADAPT Cycle for Eradication

Launch a targeted ADAPT cycle to verify eradication.

```bash
# Create eradication scope
curl -X POST http://localhost:3000/api/v1/adapt/scopes \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "INC-2026-0215 Eradication Verification",
    "description": "Full network sweep to verify all attacker footholds have been removed.",
    "scope_type": "organization_wide",
    "target_cidrs": ["10.0.0.0/8"],
    "scan_interval_hours": 0,
    "auto_validate": true,
    "auto_fortify": false
  }'
```

```bash
# Launch the cycle
curl -X POST http://localhost:3000/api/v1/adapt/cycles \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "scope_id": "0194h400-sc01-7000-8000-000000000001"
  }'
```

### Check for Persistence Mechanisms

```sql
-- Find all hosts with indicators of compromise
SELECT
    a.asset_hostname,
    a.asset_ip,
    e.event_type,
    e.severity,
    e.details
FROM adapt_events e
JOIN asset_inventory a ON a.id = e.asset_id
WHERE e.cycle_id = '0194h400-cy01-7000-8000-000000000001'
  AND e.event_type IN ('NewScheduledTask', 'NewService', 'NewRunKey', 'SuspiciousProcess')
ORDER BY e.severity DESC;
```

| hostname | ip | event_type | severity | details |
|----------|-----|-----------|----------|---------|
| WS-FINANCE-12 | 10.0.1.47 | NewScheduledTask | High | "WindowsUpdate Helper" - runs daily at 02:00 |
| DC-01 | 10.0.1.5 | NewService | Medium | "SysHealthMonitor" - unknown binary |

Two persistence mechanisms found. Both need to be removed.

### ADAPT Actions for Eradication

```bash
# Check pending eradication actions
curl -s http://localhost:3000/api/v1/adapt/actions/pending \
  -H "Authorization: Bearer $TOKEN" | jq '.'
```

```json
[
  {
    "id": "0194h401-ac01-7000-8000-000000000001",
    "action_type": "remove_scheduled_task",
    "target": "WS-FINANCE-12",
    "details": "Remove scheduled task 'WindowsUpdate Helper'",
    "risk_level": "low",
    "auto_approved": false
  },
  {
    "id": "0194h401-ac02-7000-8000-000000000001",
    "action_type": "remove_service",
    "target": "DC-01",
    "details": "Remove service 'SysHealthMonitor' and associated binary",
    "risk_level": "medium",
    "auto_approved": false
  }
]
```

```bash
# Approve and execute eradication actions
curl -s -X POST http://localhost:3000/api/v1/adapt/actions/0194h401-ac01-7000-8000-000000000001/approve \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"approved_by": "ic_primary", "notes": "Confirmed malicious. Remove."}'

curl -s -X POST http://localhost:3000/api/v1/adapt/actions/0194h401-ac01-7000-8000-000000000001/execute \
  -H "Authorization: Bearer $TOKEN"
```

```bash
curl -s -X POST http://localhost:3000/api/v1/adapt/actions/0194h401-ac02-7000-8000-000000000001/approve \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"approved_by": "ic_primary", "notes": "Confirmed malicious. Remove service and binary."}'

curl -s -X POST http://localhost:3000/api/v1/adapt/actions/0194h401-ac02-7000-8000-000000000001/execute \
  -H "Authorization: Bearer $TOKEN"
```

### Advance to Eradication Phase

```bash
curl -s -X POST http://localhost:3000/api/v1/incident/incidents/0194h201-aa01-7000-8000-000000000001/advance \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "new_phase": "eradication",
    "notes": "Two persistence mechanisms identified and removed. Scheduled task on WS-FINANCE-12 and service on DC-01. Full network sweep shows no additional indicators. Credential rotation complete."
  }' | jq
```

---

## Phase 5: Recovery -- "Are We Safe to Restore?"

Recovery is not "turn everything back on." Recovery is a controlled, validated return to normal operations with enhanced monitoring.

### ADAPT VALIDATE

Run validation scans to confirm the environment is clean before restoring full connectivity.

```bash
# Check confirmed exposures (should be empty after eradication)
curl -s http://localhost:3000/api/v1/adapt/exposures/confirmed \
  -H "Authorization: Bearer $TOKEN" | jq '.'
```

```json
[]
```

Empty. No confirmed exposures remaining. That is what we want to see.

```bash
# Revalidate to be certain
curl -s -X POST http://localhost:3000/api/v1/adapt/exposures/0194h500-ex01-7000-8000-000000000001/revalidate \
  -H "Authorization: Bearer $TOKEN" | jq '.'
```

### Restore Operations

```bash
# Timeline event: recovery
curl -s -X POST http://localhost:3000/api/v1/incident/incidents/0194h201-aa01-7000-8000-000000000001/timeline \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "event_type": "recovery",
    "description": "ADAPT VALIDATE confirms clean environment. Restoring WS-FINANCE-12 from clean image. DC-01 malicious service removed, AD objects cleaned. Credential rotation complete for all affected accounts. Enhanced monitoring enabled for 30 days.",
    "severity": "info",
    "source": "incident_commander"
  }' | jq
```

### Enhanced Monitoring Period

After recovery, increase monitoring sensitivity for 30 days. If the attacker comes back, you want to catch them immediately.

```bash
# Update autopilot for enhanced monitoring
curl -s -X PUT http://localhost:3000/api/v1/adapt/autopilot/config \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "cycle_interval_hours": 1,
    "auto_discover": true,
    "auto_correlate": true,
    "auto_validate": true,
    "auto_fortify": false,
    "escalation_threshold": "medium"
  }' | jq
```

Cycle interval reduced from 4 hours to 1 hour. Auto-validate enabled. Escalation threshold lowered from high to medium. For 30 days, the platform will be on heightened alert.

---

## Phase 6: Lessons Learned -- "What Did We Learn?"

This is the phase everyone skips and the one that matters most for preventing the next incident.

### ADAPT PROVE Phase

```bash
# Get metrics for the incident period
curl -s http://localhost:3000/api/v1/adapt/metrics \
  -H "Authorization: Bearer $TOKEN" | jq '.'
```

```json
{
  "metrics": [
    {"name": "mean_time_to_detect", "value": 47.0, "unit": "hours"},
    {"name": "mean_time_to_contain", "value": 11.0, "unit": "minutes"},
    {"name": "mean_time_to_eradicate", "value": 8.5, "unit": "hours"},
    {"name": "mean_time_to_recover", "value": 24.0, "unit": "hours"},
    {"name": "evidence_chain_integrity", "value": 100.0, "unit": "percentage"},
    {"name": "iocs_extracted", "value": 12.0, "unit": "count"},
    {"name": "soar_actions_executed", "value": 7.0, "unit": "count"}
  ]
}
```

### Create the Lessons Learned Record

```bash
# Create lessons learned
curl -s -X POST http://localhost:3000/api/v1/incident/incidents/0194h201-aa01-7000-8000-000000000001/lessons \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "lesson_type": "incident_postmortem",
    "findings": [
      {
        "category": "what_worked",
        "items": [
          "UEBA detected the anomaly within minutes of behavior change",
          "SOAR containment executed in under 3 minutes",
          "Forensic evidence chain maintained 100% integrity",
          "ADAPT eradication scan found both persistence mechanisms",
          "Kill chain timeline was complete within 4 hours of containment"
        ]
      },
      {
        "category": "what_failed",
        "items": [
          "47-hour dwell time before detection (initial access to UEBA alert)",
          "Phishing link not blocked by email security",
          "Service account had SPN that allowed Kerberoasting",
          "No detection of Mimikatz execution on endpoint"
        ]
      },
      {
        "category": "improvements",
        "items": [
          "Add URL sandboxing to email security gateway",
          "Remove unnecessary SPNs from service accounts",
          "Add LSASS protection (PPL) to all workstations",
          "Deploy credential guard on all domain-joined endpoints",
          "Add Mimikatz YARA rule to EDR policy"
        ]
      }
    ]
  }' | jq
```

### Close the Incident

```bash
# Get incident timeline
curl -s http://localhost:3000/api/v1/incident/incidents/0194h201-aa01-7000-8000-000000000001/timeline \
  -H "Authorization: Bearer $TOKEN" | jq '.'
```

```bash
# Advance to lessons learned (final phase)
curl -s -X POST http://localhost:3000/api/v1/incident/incidents/0194h201-aa01-7000-8000-000000000001/advance \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "new_phase": "lessons_learned",
    "notes": "Incident resolved. All phases complete. Evidence packaged. Lessons learned documented. Improvements tasked to respective teams. 30-day enhanced monitoring active."
  }' | jq
```

### The Postmortem Briefing

This is the meeting where you present findings to leadership. The data comes from the ADAPT PROVE phase.

```bash
# Get global score before and after the incident
curl -s http://localhost:3000/api/v1/adapt/score/global \
  -H "Authorization: Bearer $TOKEN" | jq '.'
```

```json
{
  "global_score": 29.7,
  "components": {
    "exposure_score": 22.3,
    "threat_score": 38.1,
    "vulnerability_score": 27.4,
    "compliance_score": 31.0
  },
  "trend": "improving",
  "trend_delta_30d": -5.2,
  "risk_level": "moderate"
}
```

The global risk score improved by 5.2 points because of the incident -- not despite it. The detection rules you tuned, the SOAR playbooks you improved, the credentials you rotated, the baselines you updated -- all of those made the organization more secure. An incident is not just a bad thing. It is a forcing function for improvement.

---

## The Complete IR Flowchart

```
PREPARATION
  |
  v
DETECTION (Alert -> Triage -> True Positive?)
  |                               |
  No -> Tune & Close           Yes
  |                               |
  v                               v
  (loop)                    CREATE INCIDENT
                                  |
                                  v
                         CONTAINMENT (SOAR + Manual)
                                  |
                                  v
                         INVESTIGATION (Forensics + Timeline + IOCs)
                                  |
                                  v
                         ERADICATION (ADAPT + SOAR)
                                  |
                                  v
                         RECOVERY (ADAPT VALIDATE + Monitoring)
                                  |
                                  v
                         LESSONS LEARNED (ADAPT PROVE + Briefing)
                                  |
                                  v
                         CLOSE INCIDENT
```

---

## Complete API Call Reference

| Phase | Module | Endpoint | Purpose |
|-------|--------|----------|---------|
| 0 | Shifts | `/api/v1/shifts/shifts` | Create IR team shifts |
| 0 | Shifts | `/api/v1/shifts/rosters` | Assign team members |
| 0 | SOAR | `/soar/playbooks` | Create/list playbooks |
| 0 | ADAPT | `/api/v1/adapt/autopilot/config` | Configure autopilot |
| 1 | Alerts | `/api/v1/alerts/queue/pending` | Pull pending alerts |
| 1 | Alerts | `/api/v1/alerts/queue/{id}` | Get alert details |
| 1 | Behavioral | `/behavioral/baselines/{id}` | Check baselines |
| 1 | Alerts | `/api/v1/alerts/queue/{id}/triage` | Triage alert |
| 1 | Incident | `/api/v1/incident/incidents` | Create incident |
| 2 | Incident | `/api/v1/incident/contain` | Execute containment |
| 2 | Incident | `/api/v1/incident/contain/{id}/rollback` | Rollback containment |
| 2 | Incident | `/api/v1/incident/incidents/{id}/timeline` | Add timeline events |
| 2 | Incident | `/api/v1/incident/incidents/{id}/advance` | Advance phase |
| 3 | Forensics | `/forensics/cases` | Create forensic case |
| 3 | Mem Forensics | `/api/v1/memforensics/dumps` | Memory acquisition |
| 3 | Mem Forensics | `/api/v1/memforensics/dumps/{id}/processes` | Process analysis |
| 3 | Mem Forensics | `/api/v1/memforensics/dumps/{id}/injections` | Injection detection |
| 3 | Mem Forensics | `/api/v1/memforensics/dumps/{id}/suspicious` | Suspicious processes |
| 3 | Forensics | `/forensics/disk/analyze` | Disk analysis |
| 3 | Forensics | `/forensics/disk/{id}/recover` | Recover deleted files |
| 3 | Forensics | `/forensics/timeline/build` | Build kill chain |
| 3 | Forensics | `/forensics/timeline/{id}/anomalies` | Timeline anomalies |
| 3 | IOC Manager | `/api/v1/iocmanager` | Add IOCs |
| 3 | Ontology | `/api/v1/ontology/graph` | Attack visualization |
| 4 | ADAPT | `/api/v1/adapt/scopes` | Eradication scope |
| 4 | ADAPT | `/api/v1/adapt/cycles` | Eradication cycle |
| 4 | ADAPT | `/api/v1/adapt/actions/pending` | Pending eradication |
| 4 | ADAPT | `/api/v1/adapt/actions/{id}/approve` | Approve action |
| 4 | ADAPT | `/api/v1/adapt/actions/{id}/execute` | Execute action |
| 5 | ADAPT | `/api/v1/adapt/exposures/confirmed` | Verify clean |
| 5 | ADAPT | `/api/v1/adapt/exposures/{id}/revalidate` | Revalidate |
| 5 | ADAPT | `/api/v1/adapt/autopilot/config` | Enhanced monitoring |
| 6 | ADAPT | `/api/v1/adapt/metrics` | Incident metrics |
| 6 | Incident | `/api/v1/incident/incidents/{id}/lessons` | Lessons learned |
| 6 | Incident | `/api/v1/incident/incidents/{id}/timeline` | Final timeline |
| 6 | ADAPT | `/api/v1/adapt/score/global` | Posture improvement |

---

*This playbook is based on handling hundreds of incidents across government, defense, financial, and healthcare organizations. Adapt it to your context, test it in tabletops, and revise it after every real incident. A playbook that does not evolve is a playbook that fails.*

---

(c) 2026 Playseat -- All Rights Reserved | Proprietary and Confidential
