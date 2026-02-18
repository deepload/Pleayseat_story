# Chapter 28: Case Study -- Ransomware Hits a Hospital Network

**Classification: UNCLASSIFIED // FOR OFFICIAL USE ONLY**
**Platform Version: 0.2.0 | Scenario Type: Critical Infrastructure Incident Response**

> "At 03:00 AM on a Tuesday in February, I got the call that every healthcare CISO has nightmares about. Imaging servers were encrypting. The ER was running on paper. And somewhere in that network, a ransomware operator was deciding whether to exfiltrate 340,000 patient records before we cut the cord. This is how we stopped them."

---

## Overview

**Operation Codename**: SCALPEL SHIELD
**Threat Actor**: PHANTOM SPIDER (synthetic) -- composite TTPs of Rhysida, BlackCat/ALPHV, and Royal ransomware groups
**Target Organization**: European Central Hospital Network (ECHN) -- *synthetic*
**Target Infrastructure**: 3 hospitals, 1 central data center, 2,400 endpoints, PACS imaging, EHR systems, medical IoT
**Duration**: 72 hours (initial response through restoration) + 7 days (forensics and regulatory)
**ADAPT Phases Exercised**: All five -- continuous cycling under crisis conditions
**Platform Modules Used**: 23 of 25+ available
**Estimated Loss Avoided**: EUR 47M (ransom demand + operational disruption + regulatory fines)
**Patient Impact Assessment**: Zero patient harm (systems restored before critical care degradation)

### Background: Healthcare Under Siege

By early 2026, healthcare had become the number one ransomware target globally. CISA's Healthcare Cybersecurity Advisory Board reported 147 major healthcare ransomware incidents in 2025 alone. The average ransom demand had climbed to EUR 4.2M, and the average downtime was 23 days. In November 2025, a German hospital chain lost access to its EHR for 19 days, and three patients died because of delayed diagnoses.

I was the CISO at ECHN when we got hit. I had been in the role for 18 months. We had deployed Playseat 11 months prior, and I had spent most of that time building SOAR playbooks for exactly this scenario. Every tabletop exercise, every after-hours drill, every argument with the board about security budget -- it all came down to one phone call at 03:00 on a Tuesday morning.

This is the complete incident response, told through every API call, every SOAR execution, every forensic artifact, and every decision point. Including the ones I got wrong.

### Dramatis Personae (All Synthetic)

| Role | Name | Callsign | Contact |
|------|------|----------|---------|
| CISO / Incident Commander | Dr. Stefan Weiss | SCALPEL-1 | +49-555-1101 |
| SOC Lead (Night Shift) | Lieutenant Maria Santos | NIGHTWATCH-3 | +34-555-1102 |
| Forensics Lead | Dr. Kenji Tanaka | EVIDENCE-7 | +49-555-1103 |
| SOAR Lead | Captain Elise Dubois | AUTOMATE-5 | +33-555-1104 |
| Network Security Lead | Ingvar Lindqvist | FIREWALL-9 | +46-555-1105 |
| Hospital IT Director | Dr. Anna Bergmann | CLINICAL-2 | +49-555-1106 |
| Legal Counsel | Advocate Martina Schlegel | COUNSEL-1 | +49-555-1107 |
| DPA Liaison | Inspector Thomas Richter | PRIVACY-4 | +49-555-1108 |
| FBI Cyber (Interpol Liaison) | Special Agent James Torres | FEDERAL-6 | +1-555-1109 |

### Hospital Network Topology (Synthetic)

| Segment | CIDR | Purpose | Classification |
|---------|------|---------|---------------|
| Hospital Alpha (Main Campus) | 10.50.10.0/24 | 800-bed teaching hospital | CRITICAL |
| Hospital Bravo (Women & Children) | 10.50.20.0/24 | 400-bed specialty hospital | CRITICAL |
| Hospital Charlie (Rehabilitation) | 10.50.30.0/24 | 200-bed rehab facility | HIGH |
| Central Data Center | 10.50.40.0/24 | EHR, PACS, lab systems | CRITICAL |
| Medical IoT / Biomedical | 10.50.50.0/24 | Infusion pumps, monitors, ventilators | CRITICAL |
| Administrative LAN | 10.50.60.0/24 | Billing, HR, finance, email | MEDIUM |
| Guest WiFi | 10.50.70.0/24 | Patient and visitor WiFi | LOW |
| Backup Network (Air-gapped) | 10.50.80.0/24 | Offline backup infrastructure | CRITICAL |

### Key Infrastructure (Synthetic)

| Hostname | IP | OS | Role |
|----------|----|----|------|
| PACS-SRV-01 | 10.50.40.10 | Windows Server 2022 | PACS imaging primary |
| PACS-SRV-02 | 10.50.40.11 | Windows Server 2022 | PACS imaging replica |
| EHR-APP-01 | 10.50.40.20 | RHEL 9 | Electronic health record |
| EHR-DB-01 | 10.50.40.21 | RHEL 9 + PostgreSQL 16 | EHR database primary |
| LAB-SRV-01 | 10.50.40.30 | Windows Server 2019 | Laboratory information system |
| DC-ECHN-01 | 10.50.60.5 | Windows Server 2022 | Domain controller primary |
| DC-ECHN-02 | 10.50.60.6 | Windows Server 2022 | Domain controller secondary |
| MAIL-GW-01 | 10.50.60.20 | Exchange 2019 | Email gateway |
| VPN-GW-01 | 10.50.60.1 | Fortinet FortiGate 7.4 | VPN/Remote access |
| BACKUP-SRV-01 | 10.50.80.5 | Ubuntu 22.04 | Veeam backup (air-gapped) |
| SOC-PLAYSEAT | 10.50.60.100 | Ubuntu 22.04 | Playseat platform instance |

---

## 02:47 AM -- The First Encryption Alert

Maria Santos was 5 hours into her night shift when the streaming analytics engine flagged anomalous file system activity on PACS-SRV-01. I was asleep. She was not.

The streaming processor had a real-time window configured for exactly this pattern:

```bash
# Check streaming analytics alert (Maria's first action)
curl -s http://localhost:3000/api/v1/stream/sources/stats \
  -H "Authorization: Bearer $TOKEN" | jq '.'
```

```json
{
  "active_sources": 12,
  "events_per_second": 847,
  "alerts_fired_last_hour": 1,
  "critical_alerts": 1,
  "alert_details": {
    "id": "0194e100-a001-7000-8000-000000000001",
    "rule": "RANSOMWARE-FILE-ENTROPY-001",
    "description": "File entropy spike on PACS-SRV-01: 847 files modified in 120 seconds with entropy > 7.9 (encrypted). Extension changes detected: .dcm -> .phantom",
    "source_ip": "10.50.40.10",
    "severity": "critical",
    "fired_at": "2026-02-17T02:47:14Z"
  }
}
```

Entropy 7.9 on DICOM medical imaging files. The `.phantom` extension. Maria told me later that her hands were steady but her stomach dropped. She had kids of her own at Hospital Bravo.

She pulled the alert queue immediately.

```bash
# Check all pending critical alerts
curl -s http://localhost:3000/api/v1/alerts/queue/pending \
  -H "Authorization: Bearer $TOKEN" | jq '.[] | select(.severity == "critical")'
```

```json
[
  {
    "id": "0194e100-al01-7000-8000-000000000001",
    "alert_name": "RANSOMWARE: Active Encryption Detected on PACS-SRV-01",
    "source": "streaming_analytics",
    "severity": "critical",
    "status": "pending",
    "context": {
      "host": "PACS-SRV-01 (10.50.40.10)",
      "files_affected": 847,
      "encryption_rate": "7.1 files/second",
      "file_extension_change": ".dcm -> .phantom",
      "average_entropy": 7.92,
      "process": "svchost_helper.exe (PID 4812)",
      "parent_process": "cmd.exe (PID 3201)",
      "user_context": "NT AUTHORITY\\SYSTEM",
      "first_encryption": "2026-02-17T02:45:33Z",
      "ransom_note_detected": true,
      "ransom_note_path": "C:\\PACS\\RECOVER_FILES.txt"
    },
    "created_at": "2026-02-17T02:47:14Z"
  },
  {
    "id": "0194e100-al01-7000-8000-000000000002",
    "alert_name": "RANSOMWARE: Ransom Note Dropped on PACS-SRV-01",
    "source": "endpoint_detection",
    "severity": "critical",
    "status": "pending",
    "context": {
      "host": "PACS-SRV-01 (10.50.40.10)",
      "file_path": "C:\\PACS\\RECOVER_FILES.txt",
      "content_preview": "YOUR FILES HAVE BEEN ENCRYPTED BY PHANTOM SPIDER. DO NOT ATTEMPT RECOVERY...",
      "bitcoin_address": "bc1q[REDACTED]",
      "tor_site": "phantomxxxx[.]onion",
      "demand_amount": "50 BTC (~EUR 4.7M)",
      "deadline": "72 hours"
    },
    "created_at": "2026-02-17T02:47:22Z"
  }
]
```

Two critical alerts within 8 seconds of each other. Active encryption at 7.1 files per second. Ransom note already dropped. 50 BTC demand -- about EUR 4.7M at February 2026 rates.

Maria triaged immediately.

```bash
# Triage the primary alert
curl -s -X PUT http://localhost:3000/api/v1/alerts/queue/0194e100-al01-7000-8000-000000000001/triage \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "triage_result": "true_positive",
    "severity_override": "critical",
    "notes": "Active ransomware encryption on PACS-SRV-01. Process svchost_helper.exe encrypting DICOM imaging files. Extension .phantom matches no known family in our database. Rate: 7.1 files/sec. Ransom note demands 50 BTC. TRIGGERING RANSOMWARE RESPONSE PLAYBOOK.",
    "recommended_action": "execute_ransomware_playbook"
  }' | jq
```

```json
{
  "id": "0194e100-al01-7000-8000-000000000001",
  "status": "triaged",
  "triage_result": "true_positive",
  "triaged_at": "2026-02-17T02:48:01Z",
  "triaged_by": "maria.santos"
}
```

---

## 03:00 AM -- SOAR Auto-Containment Triggers

The moment Maria's triage confirmed true positive, the SOAR engine fired our ransomware response playbook. This is the playbook I had built over three tabletop exercises. It had seven steps, three of which required no human approval. The first three steps -- network isolation, process kill, and credential lockdown -- were designed to execute in under 60 seconds.

```bash
# SOAR playbook execution (auto-triggered by triage confirmation)
curl -s http://localhost:3000/soar/executions?status=running \
  -H "Authorization: Bearer $TOKEN" | jq '.'
```

```json
{
  "executions": [
    {
      "id": "0194e101-s001-7000-8000-000000000001",
      "playbook_id": "0194e100-pb01-7000-8000-000000000001",
      "playbook_name": "PB-RANSOMWARE-CRITICAL-001",
      "trigger_event": {
        "alert_id": "0194e100-al01-7000-8000-000000000001",
        "triage_result": "true_positive",
        "severity": "critical",
        "threat_type": "ransomware_active_encryption"
      },
      "status": "running",
      "started_at": "2026-02-17T02:48:05Z",
      "steps_total": 7,
      "steps_completed": 0
    }
  ]
}
```

Let me show you the playbook definition. This is what I built during those tabletop exercises:

```bash
# Get the ransomware playbook definition
curl -s http://localhost:3000/soar/playbooks/0194e100-pb01-7000-8000-000000000001 \
  -H "Authorization: Bearer $TOKEN" | jq '.'
```

```json
{
  "id": "0194e100-pb01-7000-8000-000000000001",
  "name": "PB-RANSOMWARE-CRITICAL-001",
  "description": "Critical ransomware response. Auto-isolates affected hosts, kills encryption processes, locks credentials. Steps 4-7 require IC approval.",
  "status": "active",
  "trigger_type": "alert_triage",
  "trigger_config": {
    "triage_result": "true_positive",
    "severity": ["critical"],
    "threat_type": ["ransomware_active_encryption", "ransomware_pre_encryption"]
  },
  "version": 4,
  "author": "stefan.weiss",
  "approved_by": "board_security_committee",
  "created_at": "2025-06-15T10:00:00Z",
  "updated_at": "2026-01-28T14:30:00Z"
}
```

Version 4. Four iterations. Each one after a tabletop that found a gap. The board security committee had to approve it because steps 1-3 automatically isolate hospital network segments, and that has patient safety implications. I fought for three months to get that approval. The argument that won was: "An encryption running at 7 files per second will destroy 25,000 files in an hour. No human can react fast enough. The playbook can."

### Step 1: Network Isolation (Auto -- No Approval Required)

```bash
# Check step 1 execution
curl -s http://localhost:3000/soar/executions/0194e101-s001-7000-8000-000000000001/steps \
  -H "Authorization: Bearer $TOKEN" | jq '.steps[0]'
```

```json
{
  "id": "0194e101-st01-7000-8000-000000000001",
  "execution_id": "0194e101-s001-7000-8000-000000000001",
  "step_order": 1,
  "name": "Network Isolation - PACS Segment",
  "action_type": "firewall_isolate",
  "action_config": {
    "target_segment": "10.50.40.0/24",
    "isolation_level": "quarantine",
    "allow_list": ["10.50.60.100"],
    "block_direction": "both",
    "preserve_dns": false,
    "preserve_ntp": true
  },
  "status": "completed",
  "output": {
    "rules_applied": 14,
    "connections_terminated": 23,
    "segment_isolated": true,
    "allow_list_preserved": ["SOC-PLAYSEAT (10.50.60.100)"],
    "clinical_impact": "PACS imaging unavailable. EHR accessible via alternate path."
  },
  "started_at": "2026-02-17T02:48:06Z",
  "completed_at": "2026-02-17T02:48:09Z",
  "error_message": null
}
```

Three seconds. Fourteen firewall rules applied. Twenty-three active connections terminated. The PACS segment was now an island, reachable only by our Playseat instance for forensic investigation. The allow list preserved our SOC platform's access -- because if you isolate the segment and lock yourself out, you are flying blind.

Notice `preserve_dns: false`. I made that decision after our second tabletop. DNS is how the ransomware phones home. Kill it. NTP stays because you need accurate timestamps for forensics.

The clinical impact note is critical. PACS imaging was now unavailable. That means radiology goes to paper. CT scans queue up. But the EHR was on a different segment and still accessible. This is why we segmented the network in 2024 -- at the time, the hospital IT director said I was being paranoid. She does not say that anymore.

### Step 2: Process Kill on Affected Host (Auto -- No Approval Required)

```json
{
  "id": "0194e101-st02-7000-8000-000000000001",
  "step_order": 2,
  "name": "Kill Encryption Process",
  "action_type": "endpoint_kill_process",
  "action_config": {
    "target_host": "10.50.40.10",
    "process_name": "svchost_helper.exe",
    "pid": 4812,
    "kill_children": true,
    "preserve_memory": true
  },
  "status": "completed",
  "output": {
    "process_killed": true,
    "child_processes_killed": 2,
    "memory_dump_initiated": true,
    "memory_dump_size_mb": 4096,
    "encryption_stopped_at": "2026-02-17T02:48:14Z",
    "files_encrypted_final_count": 1247,
    "files_remaining_unencrypted": 184553
  },
  "started_at": "2026-02-17T02:48:10Z",
  "completed_at": "2026-02-17T02:48:14Z"
}
```

Five seconds. Process killed, children killed, memory preserved. The encryption stopped at 1,247 files out of 185,800 total DICOM images. We caught it at 0.67% encryption. If Maria had waited 10 more minutes, we would have lost 4,200+ files. If she had waited an hour, the entire PACS archive would be gone.

The `preserve_memory: true` flag is why this playbook went through four versions. The first version just killed the process. After the second tabletop, our forensics lead pointed out that the encryption key might still be in memory. So we added the memory dump before the kill. That 4GB memory dump would turn out to be the most important artifact in the entire investigation.

### Step 3: Credential Lockdown (Auto -- No Approval Required)

```json
{
  "id": "0194e101-st03-7000-8000-000000000001",
  "step_order": 3,
  "name": "Emergency Credential Lockdown",
  "action_type": "credential_lockdown",
  "action_config": {
    "scope": "compromised_segment",
    "actions": ["disable_service_accounts", "rotate_krbtgt", "force_password_reset"],
    "exclude_accounts": ["emergency_break_glass_01", "emergency_break_glass_02"],
    "segment_cidr": "10.50.40.0/24"
  },
  "status": "completed",
  "output": {
    "service_accounts_disabled": 8,
    "krbtgt_rotated": true,
    "password_resets_queued": 47,
    "golden_ticket_window_closed": true,
    "break_glass_accounts_preserved": 2
  },
  "started_at": "2026-02-17T02:48:15Z",
  "completed_at": "2026-02-17T02:48:22Z"
}
```

Seven seconds. Eight service accounts disabled. KRBTGT rotated -- which invalidates any Golden Ticket or Silver Ticket the attacker might have crafted. Forty-seven password resets queued for all accounts that had authenticated to the PACS segment in the last 30 days.

The break-glass accounts stayed alive. Those are the emergency accounts that let the hospital IT team access critical systems even when Active Directory is compromised. We created them offline, stored the passwords in a physical safe, and never -- not once -- used them on any networked system. That separation saved us.

### 03:04 AM -- Maria's Call

Sixty seconds had passed. Three automated steps complete. Maria picked up the phone and called me.

I will never forget the sound of her voice. Completely calm. Professional. But underneath it, the kind of tension that only comes from knowing that lives depend on the next few hours.

"Stefan, it is Maria. We have active ransomware on PACS-SRV-01. SOAR playbook executed. Segment isolated. Encryption stopped at 1,247 files. I need you as IC."

I was out of bed and at my laptop in 90 seconds.

---

## 03:08 AM -- Incident Commander Opens War Room

My first action was to open an incident and activate the war room.

```bash
# Create the incident
curl -s -X POST http://localhost:3000/api/v1/incident/incidents \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "INC-2026-0147: Active Ransomware -- PHANTOM SPIDER on PACS Infrastructure",
    "description": "Active ransomware encryption detected on PACS-SRV-01 at 02:47 UTC. SOAR playbook PB-RANSOMWARE-CRITICAL-001 auto-executed: segment isolated, process killed, credentials locked. 1,247 of 185,800 DICOM files encrypted (0.67%). Ransom demand: 50 BTC. Ransom note references PHANTOM SPIDER. Patient care impact: PACS imaging offline, radiology operating on paper.",
    "priority": "critical",
    "affected_systems": ["PACS-SRV-01", "PACS-SRV-02", "DC-ECHN-01", "MAIL-GW-01"]
  }' | jq
```

```json
{
  "id": "0194e102-aa01-7000-8000-000000000001",
  "title": "INC-2026-0147: Active Ransomware -- PHANTOM SPIDER on PACS Infrastructure",
  "phase": "identification",
  "priority": "critical",
  "status": "open",
  "created_at": "2026-02-17T03:08:00Z"
}
```

### 03:10 AM -- Assemble the Team

I called in the full incident response team. Everyone on the dramatis personae list got a phone call in the next five minutes. By 03:15, I had six people in a secure video call and Kenji was driving to the data center.

```bash
# Add timeline event for team assembly
curl -s -X POST http://localhost:3000/api/v1/incident/incidents/0194e102-aa01-7000-8000-000000000001/timeline \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "event_type": "team_assembly",
    "description": "Full IR team assembled via secure video. CISO (IC), SOC Lead, Forensics Lead, SOAR Lead, Network Lead, Hospital IT Director on call. Forensics Lead en route to data center.",
    "severity": "info",
    "source": "incident_commander"
  }' | jq
```

### 03:15 AM -- SOAR Step 4: Extended Network Scan (Requires IC Approval)

The playbook was waiting for my approval on step 4 -- an extended network scan to determine if the ransomware had spread beyond PACS.

```bash
# View pending approval
curl -s http://localhost:3000/soar/executions/0194e101-s001-7000-8000-000000000001/steps \
  -H "Authorization: Bearer $TOKEN" | jq '.steps[3]'
```

```json
{
  "id": "0194e101-st04-7000-8000-000000000001",
  "step_order": 4,
  "name": "Extended Network Sweep - All Hospital Segments",
  "action_type": "network_scan_ransomware",
  "action_config": {
    "target_segments": ["10.50.10.0/24", "10.50.20.0/24", "10.50.30.0/24", "10.50.40.0/24", "10.50.60.0/24"],
    "scan_type": "ransomware_indicators",
    "indicators": [".phantom", "svchost_helper.exe", "RECOVER_FILES.txt"],
    "include_memory_scan": true,
    "include_registry_scan": true
  },
  "requires_approval": true,
  "status": "pending_approval",
  "started_at": null,
  "completed_at": null
}
```

I approved immediately.

```bash
# Approve the extended scan
curl -s -X POST http://localhost:3000/soar/executions/0194e101-s001-7000-8000-000000000001/approve \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "approved": true,
    "comment": "IC approves extended network scan. Priority: determine blast radius. Maria, coordinate with Ingvar on clinical impact assessment."
  }' | jq
```

```json
{
  "id": "0194e101-st04-7000-8000-000000000001",
  "status": "running",
  "approved_by": "stefan.weiss",
  "approved_at": "2026-02-17T03:15:30Z"
}
```

The scan took 12 minutes. The results were better than I feared but worse than I hoped.

```json
{
  "scan_results": {
    "segments_scanned": 5,
    "hosts_scanned": 847,
    "hosts_with_indicators": 3,
    "details": [
      {
        "host": "PACS-SRV-01 (10.50.40.10)",
        "status": "COMPROMISED",
        "indicators": [".phantom files", "svchost_helper.exe", "RECOVER_FILES.txt"],
        "encryption_status": "stopped (process killed)"
      },
      {
        "host": "PACS-SRV-02 (10.50.40.11)",
        "status": "COMPROMISED",
        "indicators": ["svchost_helper.exe present (not running)", "scheduled task found"],
        "encryption_status": "pre-encryption (staged but not executed)"
      },
      {
        "host": "DC-ECHN-01 (10.50.60.5)",
        "status": "SUSPICIOUS",
        "indicators": ["unusual PowerShell execution log", "new scheduled task", "LSASS memory access"],
        "encryption_status": "no encryption detected"
      }
    ],
    "clean_segments": ["Hospital Alpha", "Hospital Bravo", "Hospital Charlie", "Medical IoT"],
    "scan_completed_at": "2026-02-17T03:27:45Z"
  }
}
```

Three hosts affected. PACS-SRV-01 was the active encryption. PACS-SRV-02 had the ransomware staged but not yet executed -- probably scheduled for 03:00 but our detection at 02:47 on SRV-01 triggered the response before SRV-02 fired. The domain controller showed signs of compromise -- PowerShell activity and LSASS access, which means credential harvesting. The rest of the network was clean.

I remember feeling a wave of relief about the medical IoT segment. If the ransomware had reached infusion pumps or ventilators, we would have had to evacuate patients. That did not happen because of the network segmentation we implemented in 2024.

---

## 03:30 AM -- War Room Active

I advanced the incident to containment phase and documented the decisions.

```bash
# Advance incident phase
curl -s -X POST http://localhost:3000/api/v1/incident/incidents/0194e102-aa01-7000-8000-000000000001/advance \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "new_phase": "containment",
    "notes": "Blast radius determined: 3 hosts compromised. PACS segment already isolated. Extending isolation to DC-ECHN-01. Clean segments confirmed. Advancing to active containment. War room established."
  }' | jq
```

```json
{
  "id": "0194e102-aa01-7000-8000-000000000001",
  "phase": "containment",
  "advanced_at": "2026-02-17T03:30:00Z",
  "advanced_by": "stefan.weiss"
}
```

### War Room Decisions (03:30 - 03:45)

Four decisions made in fifteen minutes:

1. **Isolate DC-ECHN-01** -- The domain controller was compromised. We had a secondary (DC-ECHN-02) that showed no indicators. I authorized SOAR to isolate the primary DC and promote the secondary.

2. **Notify hospital administration** -- Dr. Bergmann called the Chief Medical Officers of all three hospitals. Paper-based PACS workaround activated. Elective surgeries postponed. Emergency procedures unaffected (they use portable imaging).

3. **Activate backup verification** -- Ingvar was tasked with verifying our air-gapped backups were intact. If the attackers had been in our network for days, they might have tried to corrupt our backups.

4. **Do NOT pay the ransom** -- This was not a hard decision. We had air-gapped backups. The question was whether they had exfiltrated patient data before encrypting. That answer would determine our regulatory exposure.

```bash
# Execute containment on domain controller
curl -s -X POST http://localhost:3000/api/v1/incident/contain \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "incident_id": "0194e102-aa01-7000-8000-000000000001",
    "containment_type": "network_isolation",
    "target_host": "DC-ECHN-01 (10.50.60.5)",
    "actions": ["network_isolate", "disable_ad_replication", "promote_dc_echn_02"],
    "approved_by": "stefan.weiss",
    "notes": "Isolate compromised DC. Promote secondary. Verify AD replication integrity via DC-ECHN-02 before re-enabling services."
  }' | jq
```

```json
{
  "id": "0194e102-cn01-7000-8000-000000000001",
  "incident_id": "0194e102-aa01-7000-8000-000000000001",
  "status": "executed",
  "actions_completed": 3,
  "rollback_available": true,
  "executed_at": "2026-02-17T03:35:00Z"
}
```

---

## 04:00 AM -- Kill Chain Reconstruction

With containment in place, I pivoted to understanding how they got in. Kenji had arrived at the data center and was beginning forensic acquisition. Meanwhile, I started reconstructing the kill chain using the platform.

### ADAPT Cycle Under Crisis

I launched a targeted ADAPT cycle focused on the three compromised hosts.

```bash
# Create targeted ADAPT scope
curl -X POST http://localhost:3000/api/v1/adapt/scopes \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "INC-2026-0147 Kill Chain Reconstruction",
    "description": "Targeted analysis of PACS-SRV-01, PACS-SRV-02, DC-ECHN-01 to reconstruct ransomware kill chain.",
    "scope_type": "targeted",
    "target_cidrs": ["10.50.40.10/32", "10.50.40.11/32", "10.50.60.5/32"],
    "scan_interval_hours": 0,
    "auto_validate": false,
    "auto_fortify": false
  }'
```

```json
{
  "id": "0194e103-sc01-7000-8000-000000000001"
}
```

```bash
# Launch the ADAPT cycle
curl -X POST http://localhost:3000/api/v1/adapt/cycles \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "scope_id": "0194e103-sc01-7000-8000-000000000001"
  }'
```

```json
{
  "id": "0194e103-cy01-7000-8000-000000000001",
  "scope_id": "0194e103-sc01-7000-8000-000000000001",
  "phase": "discover",
  "status": "active",
  "created_at": "2026-02-17T04:00:00Z"
}
```

### The Phishing Email (Day -3)

The discovery phase found the initial access vector almost immediately. The streaming analytics had been recording all email gateway logs, and the pattern was unmistakable.

```sql
-- Reconstruct the initial phishing attack (Day -3)
SELECT
    e.id,
    e.timestamp,
    e.source,
    e.event_type,
    e.details->>'sender' AS sender,
    e.details->>'recipient' AS recipient,
    e.details->>'subject' AS subject,
    e.details->>'attachment_name' AS attachment,
    e.details->>'attachment_hash' AS hash,
    e.details->>'link_clicked' AS clicked
FROM stream_events e
WHERE e.source = 'email_gateway'
  AND e.details->>'recipient' LIKE '%pacs-admin%'
  AND e.timestamp >= '2026-02-14T00:00:00Z'
  AND e.timestamp <= '2026-02-17T03:00:00Z'
ORDER BY e.timestamp ASC;
```

| timestamp | sender | recipient | subject | attachment | clicked |
|-----------|--------|-----------|---------|------------|---------|
| 2026-02-14T09:17:00Z | imaging-support@philips-service[.]net | pacs-admin@echn.synth.de | RE: PACS Software Update v14.2.3 -- Action Required | PACS_Update_v14.2.3.exe | true |

There it was. Three days before the encryption. A single phishing email to the PACS administrator. Sender: `imaging-support@philips-service[.]net` -- a typosquat of the real Philips medical imaging support domain. Subject line referencing a software update for the exact PACS version we ran. The attachment was an executable disguised as an update package.

The PACS admin clicked it. I cannot blame him -- it was a pitch-perfect spearphish. The sender domain was registered 5 days prior, the email referenced our exact software version, and it came in during normal business hours from what looked like a legitimate vendor.

```bash
# Add the phishing IOC
curl -s -X POST http://localhost:3000/api/v1/iocmanager \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "ioc_type": "domain",
    "value": "philips-service.net",
    "source": "INC-2026-0147-FORENSICS",
    "confidence": 0.97,
    "tags": ["phantom-spider", "spearphish", "healthcare-targeting", "vendor-impersonation"],
    "description": "Spearphishing domain impersonating Philips medical imaging support. Used to deliver initial ransomware payload via fake PACS update.",
    "tlp": "amber"
  }' | jq
```

```json
{
  "id": "0194e104-io01-7000-8000-000000000001",
  "ioc_type": "domain",
  "value": "philips-service.net",
  "status": "active",
  "created_at": "2026-02-17T04:15:00Z"
}
```

### Lateral Movement Timeline (Day -3 to Day 0)

The attacker was patient. Three days of quiet lateral movement before triggering the encryption.

```bash
# Build forensic timeline
curl -s -X POST http://localhost:3000/forensics/timeline/build \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "case_id": "0194e102-aa01-7000-8000-000000000001",
    "start_time": "2026-02-14T09:00:00Z",
    "end_time": "2026-02-17T03:00:00Z",
    "sources": ["email_gateway", "endpoint_detection", "ad_logs", "network_flow", "syslog"],
    "hosts": ["PACS-SRV-01", "PACS-SRV-02", "DC-ECHN-01", "MAIL-GW-01"],
    "enrichment": ["mitre_attack", "threat_intel", "geo"]
  }' | jq
```

```json
{
  "id": "0194e105-tl01-7000-8000-000000000001",
  "case_id": "0194e102-aa01-7000-8000-000000000001",
  "events_count": 847,
  "critical_events": 23,
  "kill_chain": [
    {
      "phase": "initial_access",
      "mitre": "T1566.001",
      "timestamp": "2026-02-14T09:17:00Z",
      "host": "MAIL-GW-01",
      "description": "Spearphishing email delivered. Attachment PACS_Update_v14.2.3.exe clicked by pacs-admin account.",
      "confidence": 0.97
    },
    {
      "phase": "execution",
      "mitre": "T1204.002",
      "timestamp": "2026-02-14T09:22:00Z",
      "host": "PACS-SRV-01",
      "description": "User execution of malicious file. PACS_Update_v14.2.3.exe spawned cmd.exe -> PowerShell.exe (encoded command).",
      "confidence": 0.95
    },
    {
      "phase": "persistence",
      "mitre": "T1053.005",
      "timestamp": "2026-02-14T09:25:00Z",
      "host": "PACS-SRV-01",
      "description": "Scheduled task 'PACS Maintenance' created. Runs svchost_helper.exe at 03:00 daily.",
      "confidence": 0.98
    },
    {
      "phase": "credential_access",
      "mitre": "T1003.001",
      "timestamp": "2026-02-14T14:33:00Z",
      "host": "PACS-SRV-01",
      "description": "LSASS process access via Mimikatz variant. Domain admin credentials extracted.",
      "confidence": 0.91
    },
    {
      "phase": "lateral_movement",
      "mitre": "T1021.002",
      "timestamp": "2026-02-14T22:17:00Z",
      "host": "DC-ECHN-01",
      "description": "SMB lateral movement using stolen domain admin credentials. New service installed on domain controller.",
      "confidence": 0.93
    },
    {
      "phase": "lateral_movement",
      "mitre": "T1021.002",
      "timestamp": "2026-02-15T02:45:00Z",
      "host": "PACS-SRV-02",
      "description": "SMB lateral movement to PACS replica. svchost_helper.exe deployed. Scheduled task created.",
      "confidence": 0.94
    },
    {
      "phase": "discovery",
      "mitre": "T1083",
      "timestamp": "2026-02-15T10:00:00Z",
      "host": "PACS-SRV-01",
      "description": "File system enumeration. 185,800 DICOM files cataloged across PACS shares.",
      "confidence": 0.89
    },
    {
      "phase": "collection",
      "mitre": "T1560.001",
      "timestamp": "2026-02-16T01:30:00Z",
      "host": "PACS-SRV-01",
      "description": "Archive creation: patient_data_export.7z (2.3GB). Contains sample patient records for extortion.",
      "confidence": 0.87
    },
    {
      "phase": "exfiltration",
      "mitre": "T1048.003",
      "timestamp": "2026-02-16T02:15:00Z",
      "host": "PACS-SRV-01",
      "description": "Outbound HTTPS to 185.220.101.44 (Tor exit node). 2.3GB transferred over 45 minutes.",
      "confidence": 0.92
    },
    {
      "phase": "impact",
      "mitre": "T1486",
      "timestamp": "2026-02-17T02:45:33Z",
      "host": "PACS-SRV-01",
      "description": "Ransomware encryption initiated. svchost_helper.exe activated by scheduled task. .phantom extension appended.",
      "confidence": 0.99
    }
  ]
}
```

The kill chain was textbook. Initial access via spearphishing on Day -3. Credential theft within 5 hours. Lateral movement to the domain controller and PACS replica on Day -2. File enumeration on Day -1. Data exfiltration on Day -1 (the night before encryption). And then the scheduled task fired at 02:45 on Day 0.

The exfiltration was the punch in the gut. 2.3GB of patient data to a Tor exit node. They had exfiltrated before encrypting. This changed the entire calculus of the incident -- even though we stopped the encryption, they had patient data, and that meant regulatory notification.

---

## 05:00 AM -- Threat Genome Matches Ransomware Family

I ran the genome comparison to identify the ransomware family.

```bash
# Run threat genome comparison
curl -s -X POST http://localhost:3000/api/v1/threatintel/genome/compare \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "ioc_set": [
      "philips-service.net",
      "185.220.101.44",
      "svchost_helper.exe",
      ".phantom",
      "a7b3c891d7e4b0056f8912ab34cd5678ef901234567890abcdef1234567890ef"
    ],
    "compare_against": "all_ransomware"
  }'
```

```json
{
  "matches": [
    {
      "actor": "Rhysida",
      "jaccard_similarity": 0.72,
      "matching_iocs": 3,
      "confidence": "HIGH",
      "ttp_overlap": {
        "T1566.001": "Spearphishing Attachment",
        "T1053.005": "Scheduled Task/Job",
        "T1003.001": "LSASS Memory",
        "T1486": "Data Encrypted for Impact"
      }
    },
    {
      "actor": "BlackCat/ALPHV",
      "jaccard_similarity": 0.58,
      "matching_iocs": 2,
      "confidence": "MEDIUM",
      "ttp_overlap": {
        "T1048.003": "Exfiltration Over Alternative Protocol",
        "T1486": "Data Encrypted for Impact",
        "T1204.002": "User Execution: Malicious File"
      }
    }
  ],
  "assessment": "Likely Rhysida affiliate or evolution. TTP overlap and healthcare targeting pattern consistent with Rhysida operations post-Q3 2025. The .phantom extension is new -- possibly a rebranded affiliate operation."
}
```

Rhysida affiliate. That tracked. Rhysida had been hitting healthcare since 2023, and their affiliates had been rebranding every quarter to avoid detection signatures. The `.phantom` extension was new, but the underlying playbook -- spearphishing, Mimikatz, scheduled tasks, double extortion -- was pure Rhysida.

### Memory Analysis Confirms Encryption Key

Kenji had arrived at the data center and was working on the memory dump from PACS-SRV-01.

```bash
# Create memory forensics dump entry
curl -s -X POST http://localhost:3000/api/v1/memforensics/dumps \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "source_host": "PACS-SRV-01",
    "dump_format": "raw",
    "os_profile": "Win2022x64_22H2"
  }'
```

```json
{
  "id": "0194e106-md01-7000-8000-000000000001"
}
```

```bash
# Run process analysis on the memory dump
curl -s http://localhost:3000/api/v1/memforensics/dumps/0194e106-md01-7000-8000-000000000001/processes \
  -H "Authorization: Bearer $TOKEN" | jq '.'
```

```json
[
  {
    "pid": 4812,
    "name": "svchost_helper.exe",
    "ppid": 3201,
    "parent_name": "cmd.exe",
    "user": "NT AUTHORITY\\SYSTEM",
    "create_time": "2026-02-17T02:45:30Z",
    "terminate_time": "2026-02-17T02:48:14Z",
    "status": "terminated",
    "cmdline": "C:\\Windows\\Temp\\svchost_helper.exe --encrypt --path C:\\PACS --ext .phantom --note RECOVER_FILES.txt",
    "memory_regions": 247,
    "suspicious": true,
    "findings": [
      "Binary not in known-good list",
      "Running from Temp directory",
      "Command line contains encryption parameters",
      "AES-256 key material found in heap (offset 0x7FFE0040A000)"
    ]
  },
  {
    "pid": 3201,
    "name": "cmd.exe",
    "ppid": 2844,
    "parent_name": "schtasks.exe",
    "user": "NT AUTHORITY\\SYSTEM",
    "create_time": "2026-02-17T02:45:28Z",
    "status": "terminated",
    "findings": [
      "Spawned by scheduled task execution",
      "Spawned ransomware process"
    ]
  }
]
```

The critical finding: **AES-256 key material found in heap at offset 0x7FFE0040A000**. Because we preserved the memory before killing the process, the encryption key was still resident. Kenji extracted it, and that meant we could decrypt the 1,247 files without paying a single cent.

I sent a message to the war room: "Kenji found the key. We can decrypt. Ransom payment is off the table."

```bash
# Check for suspicious processes
curl -s http://localhost:3000/api/v1/memforensics/dumps/0194e106-md01-7000-8000-000000000001/suspicious \
  -H "Authorization: Bearer $TOKEN" | jq '.'
```

```json
[
  {
    "pid": 4812,
    "name": "svchost_helper.exe",
    "risk_score": 0.99,
    "reasons": ["temp_directory", "encryption_params", "unsigned_binary", "scheduled_task_spawn"],
    "mitre_techniques": ["T1486", "T1036.004", "T1053.005"]
  },
  {
    "pid": 5201,
    "name": "powershell.exe",
    "risk_score": 0.87,
    "reasons": ["encoded_command", "amsi_bypass_attempt", "credential_access"],
    "mitre_techniques": ["T1059.001", "T1562.001", "T1003.001"]
  }
]
```

```bash
# Add forensic artifact for the memory dump
curl -s -X POST http://localhost:3000/forensics/cases/0194e102-aa01-7000-8000-000000000001/artifacts \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "artifact_type": "memory_dump",
    "source_path": "/evidence/INC-2026-0147/PACS-SRV-01/memory_20260217_024814.raw",
    "size_bytes": 4294967296,
    "acquisition_method": "live_memory_dump_pre_process_kill",
    "notes": "Contains AES-256 encryption key at heap offset 0x7FFE0040A000. Key extracted and verified against encrypted samples. Full decryption possible."
  }' | jq
```

```json
{
  "id": "0194e106-ar01-7000-8000-000000000001",
  "case_id": "0194e102-aa01-7000-8000-000000000001",
  "artifact_type": "memory_dump",
  "hash_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
  "hash_blake3": "af1349b9f5f9a1a6a0404dea36dcc9499bcb25c9adc112b7cc9a93cae41f3262",
  "custody_chain_started": true,
  "acquired_at": "2026-02-17T05:15:00Z"
}
```

BLAKE3 and SHA-256 dual hashing. The evidence chain was now cryptographically sealed. Every artifact from this point forward would be hashed, timestamped, and added to an append-only custody chain.

---

## 06:00 AM -- Restore from Backup vs. Pay Ransom

With the encryption key recovered, the "pay ransom" question was already answered. But the data exfiltration question remained.

### Backup Verification

Ingvar reported in at 05:45. The air-gapped backups were intact. The attacker had never reached the backup network because it was physically disconnected and only connected during scheduled backup windows via a manually-enabled network link.

```bash
# Check confirmed exposures for backup infrastructure
curl -s http://localhost:3000/api/v1/adapt/exposures/confirmed \
  -H "Authorization: Bearer $TOKEN" | jq '.'
```

```json
[
  {
    "id": "0194e107-ex01-7000-8000-000000000001",
    "asset": "BACKUP-SRV-01",
    "status": "clean",
    "last_verified": "2026-02-17T05:42:00Z",
    "details": {
      "backup_integrity": "verified",
      "backup_age_hours": 18,
      "pacs_backup_files": 185800,
      "ehr_backup_tables": 47,
      "verification_method": "checksum_comparison",
      "notes": "Air-gapped backup verified clean. Last backup completed 2026-02-16T12:00:00Z."
    }
  }
]
```

The backup was 18 hours old. That meant we would lose the PACS images acquired between 12:00 PM on Day -1 and 02:45 AM on Day 0. But PACS-SRV-02 still had those images -- it was in pre-encryption stage (staged but not yet executed). We could recover from a combination of backup and the clean data on SRV-02.

### The Restoration Decision

```bash
# Add timeline event for restoration decision
curl -s -X POST http://localhost:3000/api/v1/incident/incidents/0194e102-aa01-7000-8000-000000000001/timeline \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "event_type": "decision",
    "description": "RESTORATION PLAN APPROVED. Three-phase approach: (1) Decrypt 1,247 encrypted files using recovered AES key. (2) Restore remaining PACS data from air-gapped backup. (3) Recover 18-hour gap from PACS-SRV-02 clean partition. Estimated restoration time: 4-6 hours. No ransom payment. DC-ECHN-01 will be rebuilt from clean image.",
    "severity": "high",
    "source": "incident_commander"
  }' | jq
```

---

## 08:00 AM -- Patient Data Exposure Assessment with DLP

The hard question. Did they exfiltrate patient data? And if so, how much?

The forensic timeline showed 2.3GB exfiltrated to a Tor exit node. I needed to know exactly what was in that 2.3GB.

```bash
# Run DLP data exposure assessment
curl -s -X POST http://localhost:3000/api/v1/dlp/create \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "scan_type": "exfiltration_assessment",
    "incident_id": "0194e102-aa01-7000-8000-000000000001",
    "source_host": "PACS-SRV-01",
    "exfiltration_details": {
      "destination_ip": "185.220.101.44",
      "destination_type": "tor_exit_node",
      "data_size_bytes": 2469606195,
      "transfer_start": "2026-02-16T02:15:00Z",
      "transfer_end": "2026-02-16T03:00:00Z",
      "protocol": "https"
    },
    "data_classification_scan": true,
    "pii_detection": true,
    "phi_detection": true,
    "regulatory_frameworks": ["GDPR", "HIPAA", "NIS2"]
  }' | jq
```

```json
{
  "created": true,
  "module": "dlpengine",
  "data": {
    "assessment_id": "0194e108-dl01-7000-8000-000000000001",
    "scan_status": "completed",
    "exfiltration_confirmed": true,
    "data_classification": {
      "total_size_gb": 2.3,
      "files_estimated": 4200,
      "data_types": [
        {
          "type": "DICOM_images",
          "count": 3800,
          "contains_phi": true,
          "phi_fields": ["patient_name", "patient_id", "date_of_birth", "referring_physician"],
          "patients_affected": 847
        },
        {
          "type": "radiology_reports",
          "count": 340,
          "contains_phi": true,
          "phi_fields": ["patient_name", "diagnosis", "medical_record_number"],
          "patients_affected": 312
        },
        {
          "type": "system_config_files",
          "count": 60,
          "contains_phi": false,
          "security_impact": "PACS credentials, network topology exposed"
        }
      ],
      "unique_patients_affected": 1047,
      "regulatory_impact": {
        "gdpr": {
          "breach_notification_required": true,
          "notification_deadline": "72 hours from awareness",
          "supervisory_authority": "BfDI (German Federal DPA)",
          "data_subjects_to_notify": 1047,
          "special_category_data": true,
          "notes": "Health data is special category under GDPR Art. 9. High risk -- individual notification required per Art. 34."
        },
        "nis2": {
          "significant_incident": true,
          "early_warning_deadline": "24 hours",
          "incident_notification_deadline": "72 hours",
          "final_report_deadline": "1 month",
          "authority": "BSI (German Federal Office for Information Security)"
        }
      }
    }
  }
}
```

1,047 patients. Health data -- special category under GDPR. Mandatory notification to every single one of them, plus the German Federal Data Protection Authority within 72 hours.

I called Martina Schlegel, our legal counsel. She had been on standby since 03:30.

"Martina, confirmed exfiltration. 1,047 patients. DICOM images and radiology reports. Special category data. We have 72 hours for GDPR notification and 24 hours for NIS2 early warning."

She did not hesitate: "I will draft both notifications. Get me the evidence package by noon."

---

## 10:00 AM -- Forensic Evidence Collection

Kenji had been working since 04:00, methodically acquiring forensic images and building the chain of custody.

```bash
# Create forensic case
curl -s -X POST http://localhost:3000/forensics/cases \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "campaign_id": "0194e102-aa01-7000-8000-000000000001",
    "title": "FORENSIC-2026-0147: PHANTOM SPIDER Ransomware -- ECHN Hospital Network",
    "description": "Full forensic investigation of ransomware incident. Three compromised hosts. Evidence collection for regulatory notification (GDPR, NIS2) and law enforcement (FBI/Interpol, ANSSI, BSI).",
    "status": "active",
    "analyst": "kenji.tanaka"
  }' | jq
```

```json
{
  "id": "0194e109-fc01-7000-8000-000000000001",
  "campaign_id": "0194e102-aa01-7000-8000-000000000001",
  "title": "FORENSIC-2026-0147: PHANTOM SPIDER Ransomware -- ECHN Hospital Network",
  "status": "active",
  "analyst": "kenji.tanaka",
  "created_at": "2026-02-17T10:00:00Z"
}
```

### Disk Forensics -- PACS-SRV-01

```bash
# Initiate disk analysis
curl -s -X POST http://localhost:3000/forensics/disk/analyze \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "case_id": "0194e109-fc01-7000-8000-000000000001",
    "source_host": "PACS-SRV-01",
    "disk_image_path": "/evidence/INC-2026-0147/PACS-SRV-01/disk_20260217_100000.E01",
    "analysis_type": "full",
    "include_deleted": true,
    "include_slack_space": true,
    "include_registry": true,
    "os_profile": "Win2022x64_22H2"
  }' | jq
```

```json
{
  "id": "0194e109-da01-7000-8000-000000000001",
  "status": "analyzing",
  "estimated_duration_minutes": 45
}
```

```bash
# Check disk forensics for encryption artifacts
curl -s http://localhost:3000/forensics/disk/0194e109-da01-7000-8000-000000000001/encryption \
  -H "Authorization: Bearer $TOKEN" | jq '.'
```

```json
{
  "disk_id": "0194e109-da01-7000-8000-000000000001",
  "encryption_detected": true,
  "details": {
    "encrypted_files": 1247,
    "encryption_algorithm": "AES-256-CBC",
    "file_extension": ".phantom",
    "ransom_note_count": 47,
    "encryption_binary": {
      "path": "C:\\Windows\\Temp\\svchost_helper.exe",
      "size_bytes": 2847293,
      "compile_time": "2026-02-10T14:22:00Z",
      "pdb_path": "C:\\Users\\dev\\phantom\\Release\\phantom.pdb",
      "digital_signature": "none",
      "packed": false,
      "language": "Rust"
    },
    "persistence_mechanisms": [
      {
        "type": "scheduled_task",
        "name": "PACS Maintenance",
        "schedule": "daily at 03:00",
        "command": "C:\\Windows\\Temp\\svchost_helper.exe --encrypt"
      },
      {
        "type": "registry_run_key",
        "path": "HKLM\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Run",
        "name": "PACSUpdate",
        "value": "C:\\Windows\\Temp\\svchost_helper.exe --persist"
      }
    ],
    "deleted_files_recovered": [
      {
        "path": "C:\\Users\\pacs-admin\\Downloads\\PACS_Update_v14.2.3.exe",
        "deleted_at": "2026-02-14T09:30:00Z",
        "hash_sha256": "a7b3c891d7e4b0056f8912ab34cd5678ef901234567890abcdef1234567890ef",
        "notes": "Original phishing payload. Deleted by attacker after execution."
      },
      {
        "path": "C:\\Windows\\Temp\\patient_data_export.7z",
        "deleted_at": "2026-02-16T03:05:00Z",
        "size_bytes": 2469606195,
        "notes": "Exfiltration staging archive. Deleted after transfer to Tor exit node."
      }
    ]
  }
}
```

The ransomware was written in Rust. The PDB path showed `phantom` as the project name. Compiled on February 10 -- one week before deployment. The attacker deleted the original phishing payload and the exfiltration staging archive, but disk forensics recovered both from slack space.

### Recover deleted files for evidence

```bash
# Recover the deleted phishing payload
curl -s -X POST http://localhost:3000/forensics/disk/0194e109-da01-7000-8000-000000000001/recover \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "recovery_targets": [
      "C:\\Users\\pacs-admin\\Downloads\\PACS_Update_v14.2.3.exe",
      "C:\\Windows\\Temp\\patient_data_export.7z"
    ],
    "output_path": "/evidence/INC-2026-0147/recovered/",
    "preserve_metadata": true
  }' | jq
```

```json
{
  "recovered_files": 2,
  "total_bytes_recovered": 2472453488,
  "details": [
    {
      "original_path": "C:\\Users\\pacs-admin\\Downloads\\PACS_Update_v14.2.3.exe",
      "recovered_to": "/evidence/INC-2026-0147/recovered/PACS_Update_v14.2.3.exe",
      "integrity": "complete",
      "hash_sha256": "a7b3c891d7e4b0056f8912ab34cd5678ef901234567890abcdef1234567890ef"
    },
    {
      "original_path": "C:\\Windows\\Temp\\patient_data_export.7z",
      "recovered_to": "/evidence/INC-2026-0147/recovered/patient_data_export.7z",
      "integrity": "complete",
      "hash_sha256": "b8c4d902e8f5c1167g9023bc45de6789fg012345678901bcdefg2345678901fg"
    }
  ]
}
```

### Evidence Chain Verification

```bash
# Verify evidence integrity
curl -s -X POST http://localhost:3000/forensics/artifacts/0194e106-ar01-7000-8000-000000000001/verify \
  -H "Authorization: Bearer $TOKEN" | jq '.'
```

```json
{
  "artifact_id": "0194e106-ar01-7000-8000-000000000001",
  "verification_status": "verified",
  "hash_sha256_match": true,
  "hash_blake3_match": true,
  "custody_chain_intact": true,
  "custody_events": [
    {
      "event": "acquired",
      "by": "soar_playbook_pb001",
      "at": "2026-02-17T02:48:14Z",
      "notes": "Auto-acquired by SOAR during process kill step"
    },
    {
      "event": "transferred",
      "by": "kenji.tanaka",
      "at": "2026-02-17T05:15:00Z",
      "notes": "Transferred to evidence server via secure channel"
    },
    {
      "event": "analyzed",
      "by": "kenji.tanaka",
      "at": "2026-02-17T05:30:00Z",
      "notes": "Encryption key extracted from heap at offset 0x7FFE0040A000"
    },
    {
      "event": "verified",
      "by": "stefan.weiss",
      "at": "2026-02-17T10:30:00Z",
      "notes": "IC verified evidence integrity for regulatory submission"
    }
  ]
}
```

```bash
# Get full custody chain
curl -s http://localhost:3000/forensics/artifacts/0194e106-ar01-7000-8000-000000000001/custody \
  -H "Authorization: Bearer $TOKEN" | jq '.'
```

```json
{
  "artifact_id": "0194e106-ar01-7000-8000-000000000001",
  "custody_chain": [
    {
      "sequence": 1,
      "action": "acquisition",
      "actor": "SOAR Playbook PB-RANSOMWARE-CRITICAL-001",
      "timestamp": "2026-02-17T02:48:14Z",
      "hash_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
      "hash_blake3": "af1349b9f5f9a1a6a0404dea36dcc9499bcb25c9adc112b7cc9a93cae41f3262",
      "integrity": "verified"
    },
    {
      "sequence": 2,
      "action": "analysis",
      "actor": "Dr. Kenji Tanaka (EVIDENCE-7)",
      "timestamp": "2026-02-17T05:30:00Z",
      "hash_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
      "hash_blake3": "af1349b9f5f9a1a6a0404dea36dcc9499bcb25c9adc112b7cc9a93cae41f3262",
      "integrity": "verified",
      "notes": "Read-only analysis. No modification to original artifact."
    },
    {
      "sequence": 3,
      "action": "packaging",
      "actor": "Dr. Stefan Weiss (SCALPEL-1)",
      "timestamp": "2026-02-17T11:00:00Z",
      "hash_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
      "hash_blake3": "af1349b9f5f9a1a6a0404dea36dcc9499bcb25c9adc112b7cc9a93cae41f3262",
      "integrity": "verified",
      "destination": "Law enforcement evidence package"
    }
  ],
  "chain_integrity": "intact",
  "total_custodians": 3,
  "hash_consistency": "all_match"
}
```

---

## 12:00 PM -- Systems Restored, Evidence Packaged for FBI/ANSSI

By noon, three parallel workstreams completed simultaneously.

### Workstream 1: System Restoration

The PACS service was back online at 11:47 UTC. All 1,247 encrypted files decrypted. The 18-hour gap from backup was filled from PACS-SRV-02's clean data. Total downtime: 9 hours and 2 minutes. The industry average for ransomware recovery is 23 days.

```bash
# Timeline event: restoration complete
curl -s -X POST http://localhost:3000/api/v1/incident/incidents/0194e102-aa01-7000-8000-000000000001/timeline \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "event_type": "restoration",
    "description": "PACS-SRV-01: All 1,247 encrypted files decrypted using recovered AES key. Full PACS archive restored. PACS service online at 11:47 UTC. Total downtime: 9h02m. PACS-SRV-02: Ransomware removed, clean reimage scheduled. DC-ECHN-01: Full rebuild from clean image, rejoined domain via DC-ECHN-02.",
    "severity": "info",
    "source": "network_lead"
  }' | jq
```

### Workstream 2: Regulatory Notifications

```bash
# Timeline event: regulatory notifications
curl -s -X POST http://localhost:3000/api/v1/incident/incidents/0194e102-aa01-7000-8000-000000000001/timeline \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "event_type": "regulatory",
    "description": "NIS2 early warning submitted to BSI at 10:30 UTC (within 24-hour deadline). GDPR breach notification to BfDI drafted -- submission scheduled for 14:00 UTC (within 72-hour deadline). Patient notification letters in preparation for 1,047 affected individuals.",
    "severity": "high",
    "source": "legal_counsel"
  }' | jq
```

### Workstream 3: Law Enforcement Evidence Package

Kenji assembled 14 forensic artifacts, all dual-hashed, all with intact chain of custody.

```sql
-- Summary of evidence artifacts
SELECT
    a.artifact_type,
    a.source_path,
    a.size_bytes,
    a.hash_sha256,
    a.hash_blake3,
    a.acquired_at
FROM forensic_artifacts a
WHERE a.case_id = '0194e109-fc01-7000-8000-000000000001'
ORDER BY a.acquired_at ASC;
```

| artifact_type | source | size_bytes | acquired_at |
|--------------|--------|-----------|-------------|
| memory_dump | PACS-SRV-01 | 4,294,967,296 | 02:48 |
| disk_image | PACS-SRV-01 | 512,000,000,000 | 04:30 |
| disk_image | PACS-SRV-02 | 512,000,000,000 | 05:00 |
| disk_image | DC-ECHN-01 | 256,000,000,000 | 05:30 |
| malware_sample | svchost_helper.exe | 2,847,293 | 06:00 |
| phishing_payload | PACS_Update_v14.2.3.exe | 3,456,789 | 06:15 |
| ransom_note | RECOVER_FILES.txt | 2,847 | 06:20 |
| email_header | phishing email | 12,456 | 06:30 |
| network_capture | exfiltration pcap | 2,469,606,195 | 07:00 |
| ad_logs | DC-ECHN-01 EVTX | 847,293,456 | 07:30 |
| registry_hive | PACS-SRV-01 SYSTEM | 45,678,901 | 08:00 |
| scheduled_tasks | all hosts | 34,567 | 08:15 |
| ioc_export | full IOC list | 89,012 | 09:00 |
| timeline_export | forensic timeline | 1,234,567 | 10:00 |

### Sharing Intelligence via Mesh

I shared the IOCs with the healthcare ISAC and Interpol.

```bash
# Create threat intelligence report for sharing
curl -s -X POST http://localhost:3000/api/v1/threatintel/reports \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "PHANTOM SPIDER Ransomware -- Healthcare Targeting Campaign (Feb 2026)",
    "summary": "Active ransomware campaign targeting European healthcare PACS infrastructure. Initial access via vendor-impersonation spearphishing. Double extortion: data theft + encryption. Ransomware written in Rust, AES-256-CBC, .phantom extension. Kill chain: 3-day dwell time, Mimikatz credential theft, SMB lateral movement, Tor exfiltration, scheduled task encryption trigger.",
    "confidence": "high",
    "tlp_level": "amber"
  }' | jq
```

```json
{
  "id": "0194e110-rp01-7000-8000-000000000001",
  "status": "created"
}
```

---

## Day +7 -- Board Briefing

One week later. Systems fully restored. Regulatory notifications filed. Law enforcement engaged. Patient notification letters sent. And now I had to stand in front of the board and explain what happened, what we did, and what it cost.

### ADAPT PROVE Phase -- Metrics for the Board

```bash
# Get ADAPT metrics for the incident period
curl -s http://localhost:3000/api/v1/adapt/metrics/trends \
  -H "Authorization: Bearer $TOKEN" | jq '.'
```

```json
{
  "period": "2026-02-17 to 2026-02-24",
  "metrics": {
    "mean_time_to_detect": {
      "value_minutes": 2.23,
      "benchmark_minutes": 197,
      "performance": "99th_percentile",
      "notes": "Detection at 02:47, 2m13s after first encryption event at 02:45"
    },
    "mean_time_to_contain": {
      "value_minutes": 3.08,
      "benchmark_minutes": 1440,
      "performance": "99th_percentile",
      "notes": "SOAR auto-containment completed at 02:48:22, 3m5s after first encryption"
    },
    "mean_time_to_recover": {
      "value_hours": 9.03,
      "benchmark_hours": 552,
      "performance": "99th_percentile",
      "notes": "PACS restored at 11:47. Full recovery by 16:00. Benchmark is 23 days."
    },
    "data_encrypted_percentage": 0.67,
    "ransom_paid": false,
    "patient_harm": "none",
    "regulatory_deadlines_met": "all",
    "evidence_chain_integrity": "100%"
  }
}
```

Two minutes and thirteen seconds to detect. Three minutes and five seconds to contain. Nine hours to full PACS restoration. Against an industry average of 197 minutes to detect and 23 days to recover.

### ROI Calculation

```bash
# Calculate incident ROI
curl -s -X POST http://localhost:3000/api/v1/roi-calculations/create \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "incident_id": "0194e102-aa01-7000-8000-000000000001",
    "calculation_type": "ransomware_avoidance",
    "costs_avoided": {
      "ransom_payment": 4700000,
      "extended_downtime_23_days": 20470000,
      "regulatory_fines_avoided": 8500000,
      "reputation_damage_estimate": 5000000,
      "patient_lawsuits_estimate": 12000000,
      "total_avoided": 50670000
    },
    "costs_incurred": {
      "incident_response_team": 45000,
      "legal_counsel": 35000,
      "patient_notification_1047": 52350,
      "system_rebuild": 28000,
      "credit_monitoring": 125640,
      "total_incurred": 285990
    },
    "platform_investment_annual": 300000,
    "roi_percentage": 16789
  }' | jq
```

```json
{
  "created": true,
  "module": "roicalc",
  "data": {
    "roi_percentage": 16789,
    "costs_avoided": 50670000,
    "costs_incurred": 285990,
    "net_savings": 50384010,
    "platform_payback_period_incidents": 0.006
  }
}
```

I stood in front of the board with those numbers. I did not have to argue for the security budget renewal.

### Lessons Learned

```bash
# Create lessons learned
curl -s -X POST http://localhost:3000/api/v1/incident/incidents/0194e102-aa01-7000-8000-000000000001/lessons \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "lesson_type": "incident_postmortem",
    "findings": [
      {
        "category": "what_worked",
        "items": [
          "SOAR auto-containment stopped encryption at 0.67%",
          "Memory preservation during process kill recovered encryption key",
          "Air-gapped backups were intact and uncompromised",
          "Network segmentation prevented spread to medical IoT",
          "Streaming analytics detected encryption within 2 minutes",
          "Evidence chain maintained 100% integrity",
          "Pre-built SOAR playbook executed steps 1-3 in 17 seconds"
        ]
      },
      {
        "category": "what_failed",
        "items": [
          "Email security did not catch the vendor-impersonation spearphish",
          "PACS admin had local admin privileges (over-provisioned)",
          "No MFA on PACS server local admin accounts",
          "2.3GB exfiltration went undetected in real time",
          "NIS2 early warning template was not pre-drafted"
        ]
      },
      {
        "category": "improvements",
        "items": [
          "Deploy DMARC strict for all vendor domains",
          "Remove local admin from PACS service accounts",
          "Deploy MFA on all server local accounts",
          "Add DLP egress monitoring for DICOM file types",
          "Pre-draft NIS2 and GDPR notification templates",
          "Add exfiltration detection rules to streaming analytics",
          "Quarterly vendor-impersonation phishing simulation"
        ]
      }
    ]
  }' | jq
```

```json
{
  "id": "0194e112-ll01-7000-8000-000000000001",
  "incident_id": "0194e102-aa01-7000-8000-000000000001",
  "created_at": "2026-02-24T14:00:00Z",
  "status": "approved"
}
```

### Final Incident Statistics

```bash
# Get overall incident stats
curl -s http://localhost:3000/api/v1/incident/stats \
  -H "Authorization: Bearer $TOKEN" | jq '.'
```

```json
{
  "total_incidents": 147,
  "open_incidents": 2,
  "critical_incidents_ytd": 3,
  "average_mttr_hours": 4.2,
  "ransomware_incidents_ytd": 1,
  "ransomware_payments_ytd": 0,
  "evidence_integrity_rate": 1.0,
  "soar_auto_containment_rate": 0.94,
  "false_positive_rate": 0.08
}
```

---

## The Aftermath

Three months later, Interpol traced the bitcoin wallet from the ransom note to a Rhysida affiliate operating out of Eastern Europe. The forensic evidence package we provided -- with its intact chain of custody, dual-hashed artifacts, and complete kill chain timeline -- was cited in the arrest warrant.

The PACS admin who clicked the phishing email was not fired. I fought for that. He had been targeted with a sophisticated, personalized spearphish that impersonated our exact PACS vendor. Instead, we used the incident to justify a comprehensive security awareness program and removed local admin privileges from all service accounts.

The board approved a 40% increase in the security budget for the next fiscal year. Not because I asked for it, but because the numbers spoke for themselves.

And Maria Santos -- the night shift SOC analyst who caught the alert at 02:47 and executed flawlessly under pressure -- was promoted to Senior SOC Lead. She earned it.

The ransomware binary sits in our evidence vault. Written in Rust. Clean code, actually. The attacker knew what they were doing. They just did not count on us knowing too.

---

## Key Takeaways

1. **SOAR playbooks must be pre-approved for auto-execution** -- You cannot wait for human approval when encryption runs at 7 files per second. Fight for those approvals now.

2. **Memory preservation before process kill is non-negotiable** -- The encryption key in memory was worth EUR 4.7M.

3. **Air-gapped backups are the last line of defense** -- Our backups were intact because they were physically disconnected.

4. **Network segmentation saves lives** -- Literally. If ransomware reaches infusion pumps, patients die.

5. **Detection speed is everything** -- Two minutes versus two hours is the difference between losing 0.67% and losing everything.

6. **Evidence chain integrity is a regulatory requirement** -- GDPR, NIS2, HIPAA all require demonstrable evidence handling.

7. **The exfiltration is the real damage** -- Encryption was stopped. But 2.3GB of patient data was already gone.

8. **Practice** -- Three tabletop exercises. Four playbook versions. Version 4 saved us.

---

## Complete API Call Reference

| Time | Module | Endpoint | Purpose |
|------|--------|----------|---------|
| 02:47 | Streaming | `/api/v1/stream/sources/stats` | Entropy alert |
| 02:47 | Alert Triage | `/api/v1/alerts/queue/pending` | Pull critical alerts |
| 02:48 | Alert Triage | `/api/v1/alerts/queue/{id}/triage` | Confirm true positive |
| 02:48 | SOAR | `/soar/executions` | Auto-playbook execution |
| 02:48 | SOAR | `/soar/playbooks/{id}` | Playbook definition |
| 02:48 | SOAR | `/soar/executions/{id}/steps` | Step-by-step results |
| 03:08 | Incident | `/api/v1/incident/incidents` | Create incident |
| 03:08 | Incident | `/api/v1/incident/incidents/{id}/timeline` | Timeline events |
| 03:15 | SOAR | `/soar/executions/{id}/approve` | IC approval |
| 03:30 | Incident | `/api/v1/incident/incidents/{id}/advance` | Phase advancement |
| 03:35 | Incident | `/api/v1/incident/contain` | Containment execution |
| 04:00 | ADAPT | `/api/v1/adapt/scopes` | Targeted scope |
| 04:00 | ADAPT | `/api/v1/adapt/cycles` | Kill chain cycle |
| 04:15 | IOC Manager | `/api/v1/iocmanager` | Add phishing IOC |
| 04:15 | Forensics | `/forensics/timeline/build` | Build kill chain |
| 05:00 | Threat Intel | `/api/v1/threatintel/genome/compare` | Family identification |
| 05:15 | Mem Forensics | `/api/v1/memforensics/dumps` | Memory dump entry |
| 05:15 | Mem Forensics | `/api/v1/memforensics/dumps/{id}/processes` | Process analysis |
| 05:15 | Mem Forensics | `/api/v1/memforensics/dumps/{id}/suspicious` | Suspicious process scan |
| 05:15 | Forensics | `/forensics/cases/{id}/artifacts` | Add artifact |
| 06:00 | ADAPT | `/api/v1/adapt/exposures/confirmed` | Backup verification |
| 08:00 | DLP | `/api/v1/dlp/create` | Data exposure assessment |
| 10:00 | Forensics | `/forensics/cases` | Create forensic case |
| 10:00 | Forensics | `/forensics/disk/analyze` | Disk analysis |
| 10:00 | Forensics | `/forensics/disk/{id}/encryption` | Encryption detection |
| 10:00 | Forensics | `/forensics/disk/{id}/recover` | Recover deleted files |
| 10:30 | Forensics | `/forensics/artifacts/{id}/verify` | Evidence verification |
| 10:30 | Forensics | `/forensics/artifacts/{id}/custody` | Chain of custody |
| 12:00 | Threat Intel | `/api/v1/threatintel/reports` | Intelligence sharing |
| Day+7 | ADAPT | `/api/v1/adapt/metrics/trends` | Performance metrics |
| Day+7 | ROI | `/api/v1/roi-calculations/create` | ROI calculation |
| Day+7 | Incident | `/api/v1/incident/incidents/{id}/lessons` | Lessons learned |
| Day+7 | Incident | `/api/v1/incident/stats` | Incident statistics |

---

*This case study is based on synthetic data and infrastructure. All names, organizations, IP addresses, and patient counts are fictional. The ransomware techniques, response procedures, and regulatory frameworks are based on real-world patterns observed in healthcare cybersecurity operations through early 2026.*

---

(c) 2026 Playseat -- All Rights Reserved | Proprietary and Confidential
