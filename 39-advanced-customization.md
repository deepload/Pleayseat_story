# Chapter 39: Making It Yours -- The Night I Built a Custom Playbook

**Playseat Advanced Field Manual -- Book 2**
**Classification: UNCLASSIFIED // FOR OFFICIAL USE ONLY**

---

It was Thursday night, maybe 8 PM, and I was about to close my laptop when my phone buzzed. The caller ID said KSMC -- Klinikum Sankt Maria Caritas, a 1,200-bed hospital network in central Europe. Not their real name, obviously, but the situation was real enough.

"We need a custom SOAR playbook for our incident response process. The board demo is Monday morning. Can you do it?"

This was their CISO, a woman I will call Dr. Weber. I had deployed Playseat at KSMC three months earlier, and the standard deployment was working well -- threat intel, evidence collection, ADAPT cycles, all the core modules. But Dr. Weber had a problem that the default configuration could not solve, and she needed it solved before she stood in front of a hospital board that included surgeons, administrators, and a finance director who thought "cybersecurity" was an IT problem that should cost less.

"What's the process?" I asked.

"We have a 14-step approval chain for containment actions."

I laughed. I should not have, but I did.

"Fourteen steps?"

"We're a hospital. You can't just auto-isolate a server when it might be running a patient's ventilator control system. You can't quarantine a workstation if it's the only machine in the surgical suite that communicates with the anesthesia monitoring equipment. Every containment action has to be evaluated against patient safety, and that evaluation involves people from IT, clinical engineering, the department head, the duty physician, and sometimes the hospital's medical director."

She was right. I stopped laughing.

"Walk me through the 14 steps."

What followed was one of the most complex incident response workflows I have ever seen, and by the end of that phone call, I understood exactly why it had to be that complex. In most organizations, the worst case for a wrong containment decision is a business outage -- lost revenue, angry customers, a bad quarter. In a hospital, the worst case is a dead patient.

I poured a large coffee and opened my editor. This was going to be a long night.

---

## Step One: Understanding What "Custom" Really Means

The first thing you need to understand about customizing Playseat is that "custom" does not mean "hack it until it works." The platform was designed from the ground up with extensibility in mind -- every module exposes API endpoints that accept configuration as structured JSON. The SOAR engine does not have a fixed set of playbooks baked into the binary. It has a playbook execution framework that runs whatever playbook definitions you feed it.

This distinction matters because I have seen what happens when organizations try to customize platforms that were not designed for it. I spent two years at a previous job maintaining a fork of a commercial SIEM that had been "customized" by a contractor who modified the Java source code directly. Every vendor update required a manual merge. Three years in, the organization was running a version so far behind the mainline that they could not apply security patches. The "customization" had turned into technical debt that was actively making them less secure.

Playseat's approach is different. You do not modify the source. You feed configuration through the API. The platform interprets and executes that configuration at runtime. When we update the core platform, your customizations survive because they are data, not code.

That Thursday night, I was going to put this architecture to the ultimate test.

---

## The 14-Step Hospital Containment Playbook

Dr. Weber sent me the incident response workflow in a PDF that was clearly the product of months of committee meetings. It had revision marks, footnotes referencing hospital regulations, and an appendix with the signatures of seven department heads. This document had been through more review than most software specifications I have seen in my career.

I read it twice. Then I translated it into a SOAR playbook.

A typical SOAR playbook for a compromised endpoint in a corporate environment has four steps: detect, isolate, investigate, remediate. Maybe five if you add a notification. The automated containment happens in seconds because the risk of leaving a compromised endpoint connected is always greater than the risk of temporarily isolating it.

In a hospital, that calculus is inverted. A compromised endpoint that is also a medical device controller cannot be isolated until someone verifies that no patient's care depends on it right now. The risk of leaving it connected for an extra ten minutes while a nurse checks the patient might be lower than the risk of cutting off a ventilator's monitoring link.

Here is the playbook I built that night:

```bash
curl -s -X POST https://playseat-ksmc.internal:3000/api/v1/soar/playbooks \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "KSMC-IR-CLINICAL-v3",
    "description": "14-step clinical incident response with patient safety gates",
    "environment": "healthcare",
    "classification": "HIPAA_sensitive",
    "trigger": {
      "type": "alert",
      "conditions": {
        "severity": {"in": ["high", "critical"]},
        "affected_zone": {"in": ["clinical_network", "medical_devices", "surgical_suite", "icu", "emergency"]}
      }
    },
    "steps": [
      {
        "step": 1,
        "name": "initial_triage",
        "action": "automated",
        "description": "Classify affected systems and identify clinical dependencies",
        "operations": [
          {"type": "asset_lookup", "target": "${affected_device}", "include": ["clinical_function", "patient_dependency", "medical_device_links"]},
          {"type": "dependency_map", "target": "${affected_device}", "depth": 3},
          {"type": "patient_safety_check", "query": "active_patients_dependent_on(${affected_device})"}
        ],
        "timeout_seconds": 30,
        "output": "triage_report"
      },
      {
        "step": 2,
        "name": "evidence_capture",
        "action": "automated",
        "description": "Preserve forensic evidence before any containment",
        "operations": [
          {"type": "traffic_capture", "scope": "affected_segment", "duration_minutes": 60, "hash_algorithm": "blake3_sha256"},
          {"type": "memory_snapshot", "target": "${affected_device}", "if_possible": true},
          {"type": "log_preservation", "sources": ["affected_device", "adjacent_devices", "domain_controller"]}
        ],
        "evidence_chain": true,
        "timeout_seconds": 60
      },
      {
        "step": 3,
        "name": "soc_analyst_assessment",
        "action": "human_decision",
        "role": "soc_analyst",
        "description": "SOC analyst reviews triage and determines severity",
        "input": "${triage_report}",
        "options": [
          {"label": "Critical - patient safety at risk", "escalation": "immediate_clinical"},
          {"label": "High - clinical system affected, no immediate patient risk", "escalation": "clinical_review"},
          {"label": "Medium - non-clinical system in clinical zone", "escalation": "standard_review"},
          {"label": "False positive - close alert", "action": "close_alert"}
        ],
        "timeout_minutes": 10,
        "escalation_on_timeout": "shift_supervisor"
      },
      {
        "step": 4,
        "name": "clinical_engineering_review",
        "action": "human_decision",
        "role": "clinical_engineer",
        "description": "Clinical engineering assesses medical device impact",
        "notification": {"channels": ["clinical-eng-oncall", "sms-biomed"], "priority": "urgent"},
        "required_assessment": [
          "List all medical devices communicating through the affected system",
          "Identify devices in active patient use",
          "Determine if backup communication paths exist",
          "Assess patient risk if the system is isolated"
        ],
        "options": [
          {"label": "Safe to isolate - no active patient dependency", "action": "proceed_to_containment"},
          {"label": "Patient dependent - manual failover required first", "action": "initiate_failover"},
          {"label": "Patient critical - do not isolate", "action": "monitor_only_with_enhanced_alerting"}
        ],
        "timeout_minutes": 15,
        "default_on_timeout": "monitor_only_with_enhanced_alerting"
      },
      {
        "step": 5,
        "name": "department_head_notification",
        "action": "notification",
        "role": "department_head",
        "description": "Notify head of affected clinical department",
        "template": "clinical_cyber_incident",
        "include_fields": ["affected_systems", "patient_impact_assessment", "recommended_action"],
        "acknowledgment_required": true,
        "timeout_minutes": 20
      },
      {
        "step": 6,
        "name": "duty_physician_consultation",
        "action": "human_decision",
        "role": "duty_physician",
        "condition": "step_4_result == patient_dependent OR step_4_result == patient_critical",
        "description": "Duty physician assesses clinical impact of containment",
        "required_assessment": [
          "Review active patients dependent on affected systems",
          "Determine if patients can safely transition to backup",
          "Assess whether patient transfers are needed"
        ],
        "options": [
          {"label": "Clinically safe to proceed", "action": "proceed"},
          {"label": "Require patient stabilization first", "action": "delay_containment", "input_required": "delay_minutes"},
          {"label": "Unacceptable patient risk - maintain current state", "action": "monitor_only"}
        ],
        "timeout_minutes": 30
      },
      {
        "step": 7,
        "name": "it_containment_plan",
        "action": "automated_with_approval",
        "description": "Generate containment plan based on clinical assessments",
        "operations": [
          {"type": "containment_plan", "strategy": "${derived_from_steps_3_4_6}", "constraints": "${patient_safety_constraints}"},
          {"type": "rollback_plan", "description": "How to reverse containment if clinical impact detected"},
          {"type": "communication_plan", "stakeholders": ["soc", "clinical_eng", "department_head", "duty_physician"]}
        ],
        "approval_required_from": "it_security_lead"
      },
      {
        "step": 8,
        "name": "clinical_engineering_signoff",
        "action": "human_approval",
        "role": "clinical_engineer",
        "description": "Clinical engineering approves specific containment plan",
        "review_document": "${containment_plan}",
        "approval_conditions": [
          "All medical device dependencies addressed",
          "Backup communication paths verified",
          "Patient safety assessment updated"
        ]
      },
      {
        "step": 9,
        "name": "execute_containment",
        "action": "automated_with_monitoring",
        "description": "Execute the approved containment plan",
        "operations": [
          {"type": "execute_containment_plan", "plan": "${approved_plan}"},
          {"type": "monitor_clinical_systems", "duration_minutes": 15, "alert_on_degradation": true}
        ],
        "rollback_trigger": {
          "condition": "clinical_system_degradation_detected",
          "action": "immediate_rollback",
          "notify": ["clinical_eng", "duty_physician", "soc"]
        }
      },
      {
        "step": 10,
        "name": "post_containment_clinical_check",
        "action": "human_verification",
        "role": "clinical_engineer",
        "description": "Verify clinical systems functioning after containment",
        "checklist": [
          "All medical devices communicating normally",
          "No patient monitoring gaps",
          "Backup systems operational where primary isolated",
          "No clinical workflow disruption reported"
        ],
        "timeout_minutes": 30
      },
      {
        "step": 11,
        "name": "investigation",
        "action": "automated_and_manual",
        "description": "Full investigation using preserved evidence",
        "operations": [
          {"type": "forensic_analysis", "evidence": "${captured_evidence}"},
          {"type": "ioc_extraction", "source": "${forensic_results}"},
          {"type": "lateral_movement_check", "scope": "full_clinical_network"},
          {"type": "threat_intel_correlation", "iocs": "${extracted_iocs}"}
        ]
      },
      {
        "step": 12,
        "name": "remediation_plan",
        "action": "automated_with_approval",
        "description": "Generate remediation plan",
        "approval_required_from": ["it_security_lead", "clinical_engineer"],
        "approval_condition": "Remediation must not require clinical downtime during active patient care"
      },
      {
        "step": 13,
        "name": "medical_director_briefing",
        "action": "notification",
        "role": "medical_director",
        "condition": "initial_severity == critical OR patient_impact_detected",
        "description": "Brief medical director on patient-affecting incidents",
        "template": "medical_director_incident_brief",
        "include_fields": ["timeline", "patient_impact", "containment_actions", "clinical_assessment"]
      },
      {
        "step": 14,
        "name": "regulatory_reporting",
        "action": "automated",
        "description": "Generate regulatory reports",
        "operations": [
          {"type": "generate_report", "framework": "hipaa_breach_assessment", "evidence": "${full_evidence_chain}"},
          {"type": "generate_report", "framework": "health_authority_notification", "if_condition": "patient_data_exposed"},
          {"type": "generate_report", "framework": "hospital_accreditation_incident", "always": true},
          {"type": "update_risk_register", "incident": "${incident_id}"}
        ]
      }
    ],
    "metadata": {
      "version": "3.0",
      "author": "security_operations",
      "reviewed_by": "clinical_governance_committee",
      "last_review": "2025-09-01",
      "regulatory_references": ["HIPAA Security Rule 164.308(a)(6)", "ISO 27799:2024", "IEC 80001-1"]
    }
  }'
```

That playbook took me four hours to build. Not because the API was difficult -- the API is straightforward JSON -- but because I spent two hours on the phone with Dr. Weber's clinical engineer, understanding exactly what "patient-dependent system" means in practice.

It means the infusion pump controller in the ICU that manages medication dosing for twelve patients simultaneously. It means the telemetry bridge that carries heart rhythm data from 40 bedside monitors to the nursing station. It means the PACS server that surgeons are actively viewing during an operation. Isolating any of these systems without clinical preparation is not a security decision. It is a medical decision.

The default-on-timeout for Step 4 -- clinical engineering review -- is "monitor only with enhanced alerting." Not isolation. Not containment. Monitoring. Because if the clinical engineer cannot be reached at 3 AM to assess patient impact, the safe default is to watch the threat closely while keeping clinical systems running. In a corporate environment, this would be a terrible default. In a hospital, it is the only defensible one.

I finished the playbook at 1:30 AM. Then I tested it against three simulated scenarios. The first two ran clean. The third exposed a gap: if the SOC analyst classified an alert as "Medium" at Step 3, the playbook skipped clinical engineering review entirely and went straight to standard IT containment. But a "medium" alert in a clinical zone could still affect medical devices -- the severity classification was about the threat, not about the clinical impact.

I added a secondary filter. If the affected zone is clinical_network or medical_devices, clinical engineering review happens regardless of severity classification. It was 2:30 AM when I caught that. One conditional. One line of JSON. The kind of thing that, if you miss it, ends up in an incident report with the heading "Contributing Factor."

---

## Teaching the Machine to Speak Doctor

Friday morning, still running on about three hours of sleep. The second customization was more subtle and, in some ways, more interesting.

"We need to search for all incidents involving DICOM servers," Dr. Weber's SOC lead told me. "And when I search for 'imaging,' I want it to include PACS, DICOM, RIS, CR, MRI, and CT -- because those are all imaging systems. Your platform doesn't know that."

He was right. The default natural language query templates understood IT concepts: servers, endpoints, networks, vulnerabilities. They did not understand that a "medical imaging system" is actually a constellation of PACS servers, DICOM routers, RIS databases, and modality-specific workstations that all communicate over DICOM protocol, and that a compromise of any one of them could expose patient imaging data from all the others.

I built custom NL Query templates:

```bash
curl -s -X POST https://playseat-ksmc.internal:3000/api/v1/ai/nl-query/templates \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "ksmc-healthcare-terminology",
    "description": "Medical terminology mappings for healthcare queries",
    "domain": "healthcare",
    "synonyms": {
      "imaging_systems": ["PACS", "DICOM", "RIS", "radiology_workstation", "CR_system", "MRI_controller", "CT_controller", "ultrasound_workstation", "digital_xray"],
      "patient_monitoring": ["telemetry", "bedside_monitor", "central_station", "vital_signs", "pulse_oximeter", "capnography", "ecg_monitor", "fetal_monitor"],
      "infusion_systems": ["infusion_pump", "syringe_driver", "PCA_pump", "TPN_pump", "chemotherapy_pump", "IV_controller"],
      "surgical_systems": ["surgical_robot", "da_vinci", "navigation_system", "anesthesia_machine", "surgical_display", "endoscope_processor"],
      "laboratory_systems": ["LIS", "analyzer", "blood_gas", "hematology", "chemistry_analyzer", "microbiology", "pathology_scanner"],
      "pharmacy_systems": ["pharmacy_robot", "dispensing_cabinet", "CPOE", "medication_verification", "barcode_scanner"],
      "emr_systems": ["EMR", "EHR", "electronic_health_record", "patient_record", "clinical_documentation"],
      "network_medical": ["clinical_network", "medical_device_vlan", "biomedical_network", "HL7_interface", "FHIR_endpoint"]
    },
    "query_templates": [
      {
        "pattern": "show me all {medical_category} incidents",
        "expansion": "SELECT * FROM incidents WHERE affected_assets && array(SELECT id FROM assets WHERE asset_type IN ({synonym_expansion}))",
        "example": "show me all imaging_systems incidents"
      },
      {
        "pattern": "which patients are affected by {incident_id}",
        "expansion": "SELECT DISTINCT patient_zone, bed_count, department FROM clinical_impact_assessment WHERE incident_id = {incident_id}",
        "example": "which patients are affected by INC-2025-0423"
      },
      {
        "pattern": "can we safely isolate {device_id}",
        "expansion": "SELECT clinical_dependency, active_patients, backup_available, isolation_risk_score FROM device_clinical_assessment WHERE device_id = {device_id}",
        "example": "can we safely isolate PACS-PRIMARY-01"
      }
    ]
  }'
```

Here is the secret about why this matters so much. The overnight SOC analyst at KSMC is not a healthcare IT specialist. She was hired six months ago from a managed security services provider where she monitored financial services networks. She knows threats. She knows investigation techniques. She does not know that a DICOM router is part of the imaging infrastructure or that an HL7 interface engine is the backbone of clinical data exchange.

The custom terminology layer bridges that knowledge gap. When she types "show me all imaging system incidents from the last 30 days," the platform expands "imaging system" to include PACS, DICOM, RIS, all the modality controllers, and every related asset. She does not need five years of biomedical engineering experience. She needs to know what she is looking for in plain language, and the platform translates.

I tested this by having the SOC lead type ten natural language queries. Nine of them returned exactly the results he expected. The tenth -- "show me compromised pharmacy systems" -- returned nothing because no pharmacy systems had been compromised. He stared at the empty result set for a moment, then grinned. "That's actually the best result."

---

## SIGMA Rules for Things That Should Not Happen in a Hospital

The third customization kept me up until 5 AM Friday. I wrote healthcare-specific detection rules because the SIGMA community, bless them, has thousands of rules for Windows environments and Active Directory attacks and approximately zero for DICOM protocol abuse or HL7 message manipulation.

I get it. Not many SIGMA contributors work in hospital IT security. But the gap is dangerous, because hospitals are increasingly targeted by ransomware groups who understand that a hospital will pay faster than a law firm because patient lives are on the line.

```bash
curl -s -X POST https://playseat-ksmc.internal:3000/api/v1/threatintel/sigma/custom \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "rules": [
      {
        "title": "DICOM C-STORE from Unauthorized Source",
        "description": "Detects DICOM image storage from unregistered devices. May indicate data exfiltration or unauthorized access to patient imaging.",
        "status": "production",
        "level": "high",
        "logsource": {"category": "network", "product": "playseat_ot_sensor"},
        "detection": {
          "selection": {
            "destination_port": 104,
            "dicom_command": "C-STORE",
            "source_ip|not_in": "${registered_imaging_modalities}"
          },
          "condition": "selection"
        },
        "tags": ["healthcare", "dicom", "data_exfiltration", "t1041"],
        "references": ["IHE ITI TF-2: 2024", "HIPAA 164.312(e)(1)"]
      },
      {
        "title": "HL7 ADT Message from Unauthorized Source",
        "description": "HL7 ADT messages modifying patient records from unauthorized sources. Could manipulate records or disrupt clinical workflows.",
        "status": "production",
        "level": "critical",
        "logsource": {"category": "application", "product": "hl7_interface_engine"},
        "detection": {
          "selection": {
            "message_type": "ADT",
            "trigger_event|in": ["A01", "A02", "A03", "A08", "A11", "A12", "A13"],
            "sending_application|not_in": "${authorized_adt_sources}"
          },
          "condition": "selection"
        },
        "tags": ["healthcare", "hl7", "patient_safety", "data_integrity"]
      },
      {
        "title": "Medical Device Firmware Update Outside Maintenance Window",
        "description": "Firmware updates to medical devices outside scheduled windows can alter device behavior and endanger patients.",
        "status": "production",
        "level": "critical",
        "logsource": {"category": "network", "product": "playseat_ot_sensor"},
        "detection": {
          "selection": {
            "destination_ip|in": "${medical_device_ips}",
            "traffic_pattern": "firmware_update_signature",
            "time|not_during": "${maintenance_windows}"
          },
          "condition": "selection"
        },
        "tags": ["healthcare", "medical_device", "firmware", "patient_safety"]
      },
      {
        "title": "Bulk Patient Record Access",
        "description": "Single user accessing abnormal number of patient records. May indicate insider threat, compromised account, or data harvesting.",
        "status": "production",
        "level": "high",
        "logsource": {"category": "application", "product": "emr_audit_log"},
        "detection": {
          "selection": {"action": "patient_record_access", "user_id": "${any_user}"},
          "condition": "selection | count(distinct patient_id) by user_id > 50 within 1h",
          "false_positives": ["Scheduled reporting jobs", "System migrations", "Authorized quality audits"]
        },
        "tags": ["healthcare", "insider_threat", "hipaa", "data_exfiltration"]
      },
      {
        "title": "Infusion Pump Parameter Change from Network",
        "description": "Network-originated parameter changes to infusion pumps. Parameters should only change at the bedside by clinical staff. Remote changes indicate compromised drug library server or direct device manipulation.",
        "status": "production",
        "level": "critical",
        "logsource": {"category": "network", "product": "playseat_ot_sensor"},
        "detection": {
          "selection": {
            "destination_ip|in": "${infusion_pump_ips}",
            "traffic_pattern": "parameter_change",
            "source_ip|not_in": "${drug_library_servers}"
          },
          "condition": "selection"
        },
        "tags": ["healthcare", "patient_safety", "medical_device", "critical_safety"]
      }
    ]
  }'
```

That last rule. The infusion pump one. Let me tell you where it came from.

The clinical engineer described a proof-of-concept attack presented at a medical device security conference. Researchers demonstrated remote modification of dosing parameters on a networked infusion pump. Change the rate from 10 mL/hour to 100 mL/hour, and the patient receives a lethal overdose. The pump executes the command without authentication because the protocol was designed for convenience in a trusted clinical environment.

"Has anyone ever done this for real?" I asked.

"Not that we know of. But 'not that we know of' is not the same as 'never.'"

I wrote the detection rule in about ten minutes. It was the most important ten minutes of the entire project. Because someday, someone will try this at a real hospital. And when they do, those ten minutes of work could mean the difference between a detected attack and a dead patient.

---

## Building the Dashboard the Board Could Understand

Friday afternoon. I had slept three hours in the past 36. Dr. Weber needed one more thing.

"The board includes surgeons and finance people. Show them a SIGMA correlation matrix and they'll check their phones within thirty seconds. I need metrics they understand."

I built custom dashboard widgets:

```bash
curl -s -X POST https://playseat-ksmc.internal:3000/api/v1/dashboard/widgets \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "dashboard": "ksmc-board-overview",
    "layout": "executive",
    "widgets": [
      {
        "id": "patient-data-protection",
        "type": "kpi_card",
        "title": "Patient Data Protection Score",
        "description": "Composite score: encryption, access control, IR readiness",
        "data_source": {
          "type": "computed",
          "inputs": [
            {"metric": "encryption_coverage_pct", "weight": 0.30},
            {"metric": "access_control_compliance_pct", "weight": 0.30},
            {"metric": "ir_readiness_score", "weight": 0.20},
            {"metric": "days_since_patient_data_incident", "weight": 0.20}
          ]
        },
        "visualization": {
          "type": "gauge",
          "min": 0, "max": 100,
          "thresholds": [
            {"value": 90, "color": "#10b981", "label": "Excellent"},
            {"value": 70, "color": "#f59e0b", "label": "Adequate"},
            {"value": 0, "color": "#ef4444", "label": "At Risk"}
          ]
        }
      },
      {
        "id": "medical-device-security",
        "type": "kpi_card",
        "title": "Medical Device Security Coverage",
        "data_source": {
          "type": "query",
          "sql": "SELECT (monitored_count::float / total_count * 100) as pct FROM medical_device_monitoring_status"
        },
        "visualization": {"type": "progress_ring", "target": 100, "unit": "%"}
      },
      {
        "id": "incident-response-time",
        "type": "trend_chart",
        "title": "Incident Response Time (Minutes)",
        "description": "Technical response vs. patient safety review",
        "data_source": {
          "type": "query",
          "sql": "SELECT date, avg_detection_to_containment_minutes, avg_patient_safety_gate_minutes FROM ir_metrics_daily WHERE date > NOW() - INTERVAL '90 days'"
        },
        "visualization": {
          "type": "stacked_area",
          "series": [
            {"field": "avg_detection_to_containment_minutes", "label": "Technical Response", "color": "#3b82f6"},
            {"field": "avg_patient_safety_gate_minutes", "label": "Patient Safety Review", "color": "#10b981"}
          ]
        }
      },
      {
        "id": "threat-by-clinical-area",
        "type": "distribution_chart",
        "title": "Threats by Clinical Area",
        "data_source": {
          "type": "query",
          "sql": "SELECT clinical_department, threat_count, max_severity FROM threats_by_department WHERE period = 'last_30_days' ORDER BY threat_count DESC"
        },
        "visualization": {"type": "treemap", "size_field": "threat_count", "color_field": "max_severity"}
      }
    ]
  }'
```

The "Patient Data Protection Score" was Dr. Weber's idea, and it was brilliant. One number. Zero to a hundred. Trend visible. Board members understand scores. They understand trajectories. They do not need to understand what a SIGMA rule is. They need to know: are we getting better or worse?

The "Incident Response Time" chart was my personal favorite because it made the 14-step approval chain visually defensible. When the board asks "why does response take 45 minutes?" the stacked area chart shows the answer: 5 minutes technical, 40 minutes patient safety review. That 40 minutes is not waste. It is the clinical governance process doing its job. Seeing it as a distinct green band makes the board nod instead of frown.

---

## Extending the Ontology: When "Endpoint" Means "Ventilator"

Saturday morning. Still running on caffeine and stubbornness. The fourth customization.

The default Playseat ontology knows about servers, workstations, networks, and users. It does not know about ventilators, infusion pumps, surgical robots, or patient monitoring systems. When an alert fires about a "compromised endpoint," the platform needs to know: is this a billing workstation that can be isolated with zero patient impact, or is it a ventilator controller where isolation means someone stops breathing?

```bash
curl -s -X POST https://playseat-ksmc.internal:3000/api/v1/ontology/entity-types \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "entity_types": [
      {
        "name": "medical_device",
        "parent_type": "endpoint",
        "description": "FDA/CE-classified networked medical device",
        "properties": [
          {"name": "fda_class", "type": "enum", "values": ["I", "II", "III"], "required": true},
          {"name": "device_category", "type": "enum", "values": ["diagnostic", "therapeutic", "monitoring", "surgical", "life_support"], "required": true},
          {"name": "patient_dependency", "type": "enum", "values": ["none", "indirect", "direct", "life_critical"], "required": true},
          {"name": "manufacturer", "type": "string"},
          {"name": "model", "type": "string"},
          {"name": "firmware_version", "type": "string"},
          {"name": "clinical_department", "type": "string"},
          {"name": "location", "type": "string"},
          {"name": "isolation_risk", "type": "enum", "values": ["safe", "caution", "dangerous", "prohibited"]}
        ]
      },
      {
        "name": "patient_record",
        "parent_type": "data_object",
        "description": "Electronic patient health record",
        "properties": [
          {"name": "record_type", "type": "enum", "values": ["demographic", "clinical", "imaging", "lab_result", "medication", "allergy", "procedure_note"]},
          {"name": "sensitivity_level", "type": "enum", "values": ["standard", "behavioral_health", "substance_abuse", "hiv", "genetic", "vip"]},
          {"name": "hipaa_category", "type": "enum", "values": ["PHI", "ePHI", "de_identified", "limited_dataset"]}
        ]
      },
      {
        "name": "clinical_system",
        "parent_type": "application",
        "description": "Clinical software with patient data access",
        "properties": [
          {"name": "system_type", "type": "enum", "values": ["emr", "pacs", "lis", "ris", "pharmacy", "surgical_planning", "telemedicine", "patient_portal"]},
          {"name": "patient_data_access", "type": "boolean"},
          {"name": "integration_protocols", "type": "array", "item_type": "enum", "values": ["hl7v2", "fhir", "dicom", "cda", "xds"]},
          {"name": "availability_sla", "type": "float"}
        ]
      }
    ],
    "relationship_types": [
      {
        "name": "monitors_patient",
        "from_type": "medical_device",
        "to_type": "patient_record",
        "properties": [
          {"name": "monitoring_type", "type": "enum", "values": ["continuous", "periodic", "on_demand"]},
          {"name": "data_criticality", "type": "enum", "values": ["informational", "clinical_decision", "life_safety"]}
        ]
      },
      {
        "name": "clinically_depends_on",
        "from_type": "medical_device",
        "to_type": "endpoint",
        "properties": [
          {"name": "dependency_type", "type": "enum", "values": ["configuration", "data", "control", "communication"]},
          {"name": "failure_impact", "type": "enum", "values": ["degraded", "nonfunctional", "unsafe"]}
        ]
      }
    ]
  }'
```

The "isolation_risk" property is the most important field in that entire schema. When the SOAR playbook reaches Step 4 and the clinical engineer reviews containment options, the ontology automatically surfaces the isolation risk. If a device is tagged "prohibited" -- an active ventilator, a running infusion pump -- the playbook does not even offer "isolate" as a button to click. The engineer sees "monitor only" and "delay until patient safe" and nothing else.

I built this because I know that at 3 AM, under pressure, even a good engineer might click the wrong button if the wrong button exists. The solution is not better training. It is removing the button. Same principle as physical safety interlocks on industrial equipment. You do not rely on people reading the warning label. You make the dangerous action mechanically impossible.

---

## Wiring It All Together: Slack, ServiceNow, and the Splunk That Will Not Die

Saturday afternoon. The final customization was integration. KSMC had Slack for communication, ServiceNow for IT service management, and a Splunk instance the board had funded through 2027. I needed to integrate with all three.

The Splunk integration had a political dimension worth mentioning. Dr. Weber could not go to her board and say "we replaced Splunk." She could say "we enhanced Splunk with a specialized platform, and the two share data seamlessly." Same technical outcome. Very different organizational politics. If you ignore the politics, your technically superior platform will gather dust in a corner while the politically established platform continues to miss threats.

```bash
curl -s -X POST https://playseat-ksmc.internal:3000/api/v1/integrations/siem-forward \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "splunk-forwarder",
    "destination": {
      "type": "splunk_hec",
      "url": "https://splunk.ksmc.internal:8088/services/collector",
      "token": "${SPLUNK_HEC_TOKEN}",
      "index": "playseat_security",
      "sourcetype": "playseat:alert"
    },
    "filter": {
      "event_types": ["alert", "incident", "containment_action", "compliance_finding"],
      "min_severity": "low"
    },
    "enrichment": {
      "include_clinical_context": true,
      "include_evidence_hashes": true,
      "include_playbook_state": true
    },
    "format": "cef",
    "batch_size": 100,
    "flush_interval_seconds": 5
  }'
```

```bash
curl -s -X POST https://playseat-ksmc.internal:3000/api/v1/integrations/slack \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "workspace": "ksmc-security",
    "webhook_url": "${SLACK_WEBHOOK_URL}",
    "channels": [
      {
        "name": "#soc-alerts",
        "filter": {"severity": {"in": ["medium", "high", "critical"]}},
        "include_clinical_context": false
      },
      {
        "name": "#clinical-security",
        "filter": {"affected_zone": {"in": ["clinical_network", "medical_devices"]}, "severity": {"in": ["high", "critical"]}},
        "include_clinical_context": true,
        "include_patient_impact": true
      },
      {
        "name": "#ir-critical",
        "filter": {"severity": "critical", "playbook_triggered": true},
        "include_clinical_context": true,
        "thread_per_incident": true
      }
    ]
  }'
```

By Saturday evening, everything was wired. An alert in Playseat simultaneously generated a Slack notification in the right channel, created a ServiceNow incident, and forwarded the event to Splunk. Clinical context traveled with the alert through every system. Nobody had to open three tools and manually correlate.

---

## The Monday Morning Demo

Dr. Weber's board presentation. 10 AM. I was on standby via video call.

She opened with the Patient Data Protection Score gauge. "Three months ago, we were at 71. Today, 94." She walked through what changed. The board understood.

Then the simulated incident. She ran through all 14 steps. When she hit Step 4 and explained that the system would not allow isolation of a device with active patient dependencies, the chief of surgery leaned forward.

"It knows which devices have patients on them?"

"In real time."

He turned to the finance director. "I've been asking for this for three years."

The finance director asked the one question finance directors always ask: "What does this cost?"

Dr. Weber showed the comparison. Previous annual spend on Splunk license, IR consulting retainer, compliance preparation staff time, and manual device inventory management: 720,000 euros. Playseat with full customization: less than half.

The board approved the next fiscal year's cybersecurity budget that morning. No fight. No negotiation. First time in Dr. Weber's tenure.

She called me after. "They approved everything. Budget, second campus, the new clinical security engineer position."

"What sealed it?"

"The surgeon. When the chief of surgery advocates for your budget, nobody pushes back."

---

## What I Learned That Weekend

Seventy-two hours. Six customizations. One Monday morning demo that changed a hospital's security posture.

Here is what I took away.

Customization is not about the platform. It is about the domain. I could build a technically perfect SOAR playbook that violated every principle of clinical safety, and it would be worse than no playbook at all. The two hours I spent talking to the clinical engineer about infusion pumps and ventilator dependencies were more valuable than the four hours I spent writing JSON.

The 14-step approval chain is not bureaucracy. Every step exists because someone, at some point, asked "what happens if we get this wrong?" and the answer was "a patient could be harmed." When you understand that, the steps are not overhead. They are wisdom.

Default-on-timeout must be safe, not fast. In corporate environments, the default is "isolate." In a hospital, it is "watch." This is not a technical decision. It is an ethical one. And it must be enforced by software, consistently, especially at 3 AM when humans are tired and scared.

Every organization that tells you their environment is unique is probably right. The customization API exists because I learned that a one-size-fits-all platform will eventually be abandoned by the organizations that need it most -- the ones where "endpoint" means "ventilator" and "containment" means something very different than it does in a data center.

KSMC is now running the third version of their clinical playbook. They refined it after two real incidents and a tabletop exercise that found a gap in overnight staffing. The playbook is a living document -- institutional knowledge about protecting patients during a cyber incident, encoded into software that runs when the people who wrote the policy are asleep.

That is what customization is really for.

---

*Next chapter: [Chapter 40 -- The Honest Truth: How We Stack Up](40-competitive-analysis.md)*

---

`© 2026 Playseat — All Rights Reserved | Proprietary and Confidential`
