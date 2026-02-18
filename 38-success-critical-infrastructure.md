# Chapter 38: Success Story -- Power Grid Security Operations Center

**Playseat Advanced Field Manual -- Book 2**
**Classification: UNCLASSIFIED // FOR OFFICIAL USE ONLY**
**Deployment Period: Q3 2025 | Full Production: November 2025**

---

> "We detected a compromised remote terminal unit in 47 minutes. Under our previous monitoring, the best-case detection estimate was 14 days. That single incident justified the entire investment."
> -- Chief Security Officer, National Power Grid Operator (synthetic attribution)

---

## 38.1 -- The Environment

The call came from a national power grid operator in a NATO-allied country. I am not naming the country, and I am not naming the operator. Critical infrastructure security is not something you discuss loosely. But I will give you the scale.

This organization operates the national electricity transmission grid. They are responsible for keeping the lights on for 28 million people. Their infrastructure spans:

| Category | Count | Notes |
|----------|-------|-------|
| Substations | 847 | 110kV to 400kV transmission |
| Remote Terminal Units (RTUs) | 6,200 | SCADA field devices |
| Intelligent Electronic Devices (IEDs) | 4,800 | Protection relays, meters |
| PLCs | 2,100 | Programmable logic controllers |
| HMI Workstations | 1,200 | Human-machine interfaces |
| Engineering Workstations | 340 | Configuration and maintenance |
| Corporate IT Endpoints | 8,500 | Standard IT infrastructure |
| Network Devices | 2,400 | Routers, switches, firewalls |
| **Total Monitored Devices** | **~26,000** | IT + OT combined |

The IT/OT convergence problem was the core challenge. Like most utilities, this operator had evolved from two completely separate networks -- a corporate IT network running Windows, Active Directory, and standard enterprise tools, and an operational technology (OT) network running SCADA, EMS (Energy Management System), and industrial protocols. Over the past decade, those networks had been connected for operational efficiency. Remote monitoring, remote maintenance, centralized dashboards -- all of it required connectivity between IT and OT.

That connectivity also created attack paths that did not exist before.

Their existing security posture:

| Domain | Tool | Coverage | Problem |
|--------|------|----------|---------|
| IT SIEM | Splunk Enterprise | Corporate IT | No OT visibility |
| OT IDS | Claroty CTD | 40% of OT network | Expensive per-sensor licensing |
| Firewall | Fortinet FortiGate | IT/OT boundary | Rules last reviewed 18 months ago |
| Endpoint | Microsoft Defender | IT endpoints only | Zero OT coverage |
| Physical Security | Honeywell ProWatch | Substations | Not integrated with cyber |
| Compliance | Manual spreadsheets | NERC CIP | 2,000+ hours/year manual effort |

The CSO was blunt: "We have six security tools that do not talk to each other, 40% OT visibility, and our compliance team spends more time filling out spreadsheets than actually securing the grid. Last year we had three unplanned outages that we later attributed to cyber incidents -- two DNS amplification attacks that overwhelmed our SCADA comms, and one unauthorized firmware update on a protection relay that caused a cascade trip. None of them were detected by our security tools. They were detected by the grid operators when the lights went out."

Three cyber-caused outages in one year. For a national grid operator, that is a crisis.

---

## 38.2 -- Threat Model: Why Power Grids Are Different

Before I discuss the deployment, I need to explain why power grid security is fundamentally different from enterprise IT security and even from the financial institution deployment in Chapter 37.

**Availability over confidentiality.** In banking, the worst case is stolen money. In power grids, the worst case is cascading blackouts that affect hospitals, water treatment, transportation, and telecommunications. The CIA triad is inverted: Availability > Integrity > Confidentiality.

**Decades-old devices.** Some RTUs in this grid were installed in the 1990s. They run firmware that has not been updated since 2008. They communicate over serial links using DNP3 (Distributed Network Protocol 3) and IEC 60870-5-104. You cannot install agents on them. You cannot patch them. You can only monitor their network traffic and behavioral patterns.

**Safety-critical operations.** A misconfigured detection rule that generates a false positive and triggers an automated containment action could open a circuit breaker and cause a blackout. Automated containment, which we used aggressively in the banking deployment, must be approached with extreme caution in OT environments.

**Air gaps are a myth.** The operator believed their most critical substations were air-gapped. During our pre-deployment assessment, we discovered 7 substations with cellular modems installed by maintenance contractors for remote access. Those modems were not in any network inventory. They were invisible to the existing security tools. I have seen this in every single OT assessment I have done. The "air gap" exists on the network diagram but not in reality.

**Nation-state adversaries are real.** Power grid operators are explicitly targeted by nation-state cyber programs. CRASHOVERRIDE (Industroyer), TRITON/TRISIS, and the December 2015 Ukraine blackout are not theoretical scenarios. They are documented attacks. The threat actors behind them are sophisticated, persistent, and well-funded.

---

## 38.3 -- Zero Trust for OT Access

The first module we deployed was Zero Trust, via the `svc-zerotrust` crate. The principle is simple: no device or user gets network access to OT systems without continuous verification. In practice, it is incredibly complex for OT environments.

### The Problem with Traditional OT Access

Traditional OT networks use flat network architectures. An engineer who logs into the VPN can reach every RTU, every HMI, and every PLC on the network. There is no segmentation, no role-based access, and no session monitoring. Once you are in, you are in everywhere.

This is how the unauthorized firmware update happened. A contractor logged into the VPN with valid credentials (shared among three team members, naturally), navigated to a protection relay, and uploaded a firmware version that had not been tested against the grid's configuration. The relay malfunctioned during a load spike, tripped a circuit breaker, and cascaded to three adjacent substations. The lights went out for 47,000 people for three hours.

Shared credentials. No session recording. No change ticket required. No impact analysis performed. Every one of those failures is a direct consequence of a flat OT network with no access governance.

### Zero Trust Configuration for OT

```bash
# Zero Trust policy for OT access
curl -s -X POST https://playseat-grid.internal:3000/api/v1/zerotrust/policies \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "ot-access-policy-v1",
    "scope": "ot_network",
    "default_action": "deny",
    "rules": [
      {
        "name": "ot-engineer-access",
        "description": "OT engineers can access assigned substations during business hours",
        "subjects": {
          "roles": ["ot_engineer"],
          "authentication": "mfa_required",
          "mfa_methods": ["hardware_token"],
          "device_compliance": "required"
        },
        "resources": {
          "type": "substation",
          "match": "assigned_substations_only",
          "protocols": ["dnp3", "iec104", "modbus_tcp", "ssh"]
        },
        "conditions": {
          "time_window": "06:00-22:00",
          "geofence": "within_country",
          "risk_score_max": 0.7,
          "concurrent_sessions_max": 1
        },
        "session": {
          "max_duration_hours": 8,
          "idle_timeout_minutes": 30,
          "record_session": true,
          "require_justification": true,
          "require_change_ticket": true
        },
        "action": "allow_with_monitoring"
      },
      {
        "name": "vendor-access",
        "description": "Vendor access requires dual approval and full session recording",
        "subjects": {
          "roles": ["vendor_engineer"],
          "authentication": "mfa_required",
          "mfa_methods": ["hardware_token"],
          "sponsor_required": true
        },
        "resources": {
          "type": "substation",
          "match": "ticket_specified_only",
          "protocols": ["ssh", "https"]
        },
        "conditions": {
          "approval_required": "dual",
          "approvers": ["ot_manager", "security_team"],
          "time_window": "08:00-18:00_weekdays",
          "geofence": "on_premises_only",
          "max_duration_hours": 4
        },
        "session": {
          "record_session": true,
          "record_keystrokes": true,
          "require_justification": true,
          "require_change_ticket": true,
          "auto_terminate_on_geofence_exit": true
        },
        "action": "allow_with_monitoring"
      },
      {
        "name": "emergency-access",
        "description": "Emergency access bypasses time windows but requires post-incident review",
        "subjects": {
          "roles": ["ot_engineer", "ot_manager"],
          "authentication": "mfa_required"
        },
        "resources": {
          "type": "substation",
          "match": "any",
          "protocols": ["dnp3", "iec104", "modbus_tcp", "ssh"]
        },
        "conditions": {
          "emergency_declared": true,
          "emergency_approver": "ot_manager_or_security_lead"
        },
        "session": {
          "record_session": true,
          "record_keystrokes": true,
          "max_duration_hours": 12,
          "post_incident_review_required": true
        },
        "action": "allow_with_enhanced_monitoring"
      }
    ],
    "catch_all": {
      "action": "deny",
      "log": true,
      "alert": true,
      "alert_severity": "high"
    }
  }'
```

Let me walk through the key decisions.

**Hardware token MFA only.** No SMS, no TOTP app, no email codes. For OT access to a national power grid, the authentication must be phishing-resistant. Hardware tokens (FIDO2/WebAuthn) are the only method that meets that bar. The CSO initially pushed back on this because some engineers work from locations with poor connectivity. We deployed offline-capable FIDO2 tokens that work without a network connection to the identity provider.

**Assigned substations only.** Engineers are assigned to specific substations. An engineer responsible for the Northern Region cannot access Southern Region substations. This is the principle of least privilege applied to physical infrastructure. We imported the assignment matrix from their HR system and linked it to the Zero Trust policy engine.

**Geofencing.** OT engineering access must originate from within the country. Vendor access must originate from on-premises. If a vendor's session exits the geofence -- meaning their VPN endpoint moves outside the physical boundary -- the session terminates automatically. This caught 7 sessions in the first 90 days where vendors were attempting to work remotely from outside approved locations.

**Dual approval for vendors.** Every vendor access session requires approval from both an OT manager and a security team member. This is the control that would have prevented the unauthorized firmware update. Two people, from two different departments, must agree that the access is authorized, scoped, and necessary.

**Change ticket required.** No OT access without a change ticket. This creates an audit trail that links every access session to an authorized change request.

### Zero Trust Deployment Results (First 90 Days)

| Metric | Value |
|--------|-------|
| Access sessions authorized | 12,847 |
| Access sessions denied (policy violation) | 2,341 |
| Sessions terminated (geofence exit) | 7 |
| Sessions terminated (idle timeout) | 891 |
| Vendor sessions requiring dual approval | 1,247 |
| Emergency access invocations | 23 |
| Post-incident reviews completed | 23/23 (100%) |
| Unauthorized access attempts detected | 14 |
| Policy exceptions granted | 0 |

Those 2,341 denied sessions are the number that keeps me awake at night. Before Zero Trust, all 2,341 of those access attempts would have succeeded. Some were engineers accessing substations outside their assignment. Some were vendors connecting outside approved hours. Some were engineers using personal devices that did not meet compliance requirements. None of them were malicious -- but any of them could have been an attacker using stolen credentials, and nobody would have known.

The 14 unauthorized access attempts were from the 7 cellular modems we discovered during the pre-deployment assessment. External actors were scanning those modems and attempting to authenticate with default credentials. Before Playseat, those attempts were invisible because the modems were not in any inventory and not monitored by any tool.

---

## 38.4 -- Digital Twin: Modeling the Grid

The `svc-digitaltwin` crate creates a virtual model of the physical grid topology. Every substation, every transmission line, every transformer, every protection relay -- represented as entities in the `ontology_entities` table with relationships in `ontology_relationships`.

Why does a cybersecurity platform need a digital twin of a power grid? Because you cannot understand the impact of a cyber event without understanding the physical infrastructure it affects.

If an attacker compromises a protection relay at Substation 47, the question is not "what data was stolen?" The question is "what happens to the grid if that relay operates incorrectly?" To answer that, you need to know: what circuit does that relay protect? What load does that circuit carry? What happens to adjacent substations if that circuit trips? Is there redundancy? What is the cascading failure risk?

The `svc-ontology` crate stores the topology. The digital twin is built on top of it.

### Grid Topology Import

```bash
# Import grid topology from CIM (Common Information Model) export
curl -s -X POST https://playseat-grid.internal:3000/api/v1/ontology/import \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "source": "cim_xml",
    "file": "/data/grid-topology/grid-model-2025-q3.xml",
    "mapping": {
      "Substation": {
        "entity_type": "infrastructure_node",
        "properties_map": {
          "mRID": "external_id",
          "name": "name",
          "Region": "region",
          "BaseVoltage": "voltage_kv"
        }
      },
      "BreakerSwitch": {
        "entity_type": "ot_device",
        "properties_map": {
          "mRID": "external_id",
          "name": "name",
          "normalOpen": "normal_state",
          "ratedCurrent": "rated_current_a"
        }
      },
      "ProtectionRelay": {
        "entity_type": "ot_device",
        "properties_map": {
          "mRID": "external_id",
          "name": "name",
          "relayType": "device_subtype",
          "protectedCircuit": "protected_asset"
        }
      },
      "ACLineSegment": {
        "entity_type": "infrastructure_link",
        "properties_map": {
          "mRID": "external_id",
          "name": "name",
          "length": "length_km",
          "r": "resistance_ohm",
          "ratedPower": "capacity_mw"
        }
      }
    },
    "relationships": {
      "Substation.Equipment": "contains",
      "ACLineSegment.Terminal": "connects_to",
      "ProtectionRelay.ProtectedSwitch": "protects"
    },
    "options": {
      "dedup_strategy": "merge_by_external_id",
      "update_existing": true,
      "dry_run": false
    }
  }'
```

After import: 847 substations, 6,200 RTUs, 4,800 IEDs, 2,100 PLCs, and 12,400 transmission line segments -- all represented in the ontology with proper relationships. The CIM (Common Information Model, IEC 61970/61968) is the standard data exchange format for power systems. Every grid operator has one.

### Impact Analysis Query

```bash
# What is the blast radius if Substation 47 loses all protection relays?
curl -s https://playseat-grid.internal:3000/api/v1/ontology/impact-analysis \
  -H "Authorization: Bearer $TOKEN" \
  -G \
  -d 'entity_type=infrastructure_node' \
  -d 'entity_name=Substation-047' \
  -d 'scenario=loss_of_protection' \
  -d 'cascade_depth=3' | jq
```

```json
{
  "target": "Substation-047",
  "scenario": "loss_of_protection",
  "direct_impact": {
    "affected_circuits": 4,
    "total_load_mw": 340,
    "customers_affected": 142000,
    "critical_loads": ["Regional Hospital", "Water Treatment Plant Alpha"]
  },
  "cascade_level_1": {
    "substations_affected": ["Sub-044", "Sub-051", "Sub-053"],
    "additional_load_mw": 890,
    "additional_customers": 367000,
    "overload_risk": "Sub-051 transformer T2 at 94% capacity"
  },
  "cascade_level_2": {
    "substations_affected": ["Sub-039", "Sub-048", "Sub-055", "Sub-057"],
    "additional_load_mw": 1240,
    "additional_customers": 521000,
    "grid_stability_risk": "high"
  },
  "total_impact": {
    "substations_at_risk": 8,
    "total_load_mw": 2470,
    "total_customers": 1030000,
    "estimated_restoration_time_hours": 4,
    "critical_infrastructure_affected": 7
  },
  "mitigation_options": [
    "Isolate Sub-047 circuit C3 to prevent cascade",
    "Transfer load from Sub-051 T2 to Sub-052 T1",
    "Pre-position restoration crews at Sub-044 and Sub-053"
  ]
}
```

One million people. That is the blast radius of a successful cyber attack on a single substation. The digital twin computes this in 340 milliseconds because the graph traversal is pre-indexed. When a SOC analyst sees an alert about Substation 47, that impact analysis is attached automatically. They do not need to open a separate tool, look up a network diagram, and manually trace circuits. The platform tells them: this alert, if real, affects 1 million people, including a hospital and a water treatment plant. Prioritize accordingly.

---

## 38.5 -- Sentinel Baselines for Industrial Protocols

The `svc-behavioral` crate's Sentinel baseline system was originally built for IT network traffic. For this deployment, we extended it to handle 500+ industrial protocol behaviors.

Traditional IT baselines monitor things like: which IPs does this server talk to? What ports are open? How much bandwidth? Industrial protocol baselines go deeper. An RTU communicating on DNP3 port 20000 is normal. But what DNP3 function codes is it sending? At what frequency? To which master station? With what data values?

### Baseline Configuration for OT

```bash
# Sentinel baselines for industrial protocols
curl -s -X POST https://playseat-grid.internal:3000/api/v1/behavioral/baselines \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "ot-protocol-baseline-v1",
    "entity_type": "ot_device",
    "entity_source": "asset_inventory",
    "entity_count": 15100,
    "baseline_period_days": 60,
    "update_frequency": "weekly",
    "features": [
      {
        "name": "dnp3_function_codes",
        "type": "categorical_distribution",
        "field": "dnp3.function_code",
        "source": "ot_network_capture",
        "applicable_to": ["rtu", "ied"],
        "description": "Distribution of DNP3 function codes (read, write, direct_operate, etc.)"
      },
      {
        "name": "polling_interval",
        "type": "temporal_regularity",
        "field": "timestamp",
        "source": "ot_network_capture",
        "group_by": ["src_ip", "dst_ip"],
        "expected_interval_ms": 1000,
        "jitter_tolerance_ms": 100,
        "description": "Regularity of master-to-RTU polling (should be exactly 1000ms +/- 100ms)"
      },
      {
        "name": "data_point_ranges",
        "type": "numeric_range",
        "fields": ["analog_input_value"],
        "source": "ot_network_capture",
        "group_by": ["device_id", "point_index"],
        "description": "Expected value ranges for each analog data point (voltage, current, power)"
      },
      {
        "name": "communication_partners",
        "type": "graph_pattern",
        "fields": ["src_ip", "dst_ip", "protocol"],
        "source": "ot_network_capture",
        "description": "Which devices talk to which devices (should be very stable in OT)"
      },
      {
        "name": "firmware_version",
        "type": "categorical_fixed",
        "field": "firmware_version",
        "source": "asset_inventory",
        "description": "Firmware version should never change without a change ticket"
      },
      {
        "name": "configuration_hash",
        "type": "categorical_fixed",
        "field": "config_hash",
        "source": "configuration_audit",
        "description": "Device configuration hash should never change without authorization"
      },
      {
        "name": "iec104_asdu_types",
        "type": "categorical_distribution",
        "field": "iec104.asdu_type",
        "source": "ot_network_capture",
        "applicable_to": ["rtu", "gateway"],
        "description": "Distribution of IEC 104 ASDU types"
      },
      {
        "name": "modbus_registers",
        "type": "set_membership",
        "field": "modbus.register_address",
        "source": "ot_network_capture",
        "applicable_to": ["plc"],
        "description": "Set of Modbus registers accessed (should be fixed per device role)"
      }
    ],
    "anomaly_detection": {
      "method": "ensemble",
      "models": ["isolation_forest", "one_class_svm", "statistical_process_control"],
      "voting": "majority",
      "alert_threshold": 0.85,
      "critical_threshold": 0.95
    },
    "ot_specific_settings": {
      "safety_mode": true,
      "never_auto_contain_ot_devices": true,
      "alert_ot_manager_on_critical": true,
      "require_human_approval_for_any_action": true
    }
  }'
```

The `safety_mode: true` and `never_auto_contain_ot_devices: true` settings are the most important lines in that configuration. In the banking deployment (Chapter 37), we auto-blocked cards and auto-held SWIFT transfers. In a power grid, you never auto-contain. A false positive that isolates an RTU could cause a protection relay to lose its communication link with the master station. Depending on the relay's fail-safe configuration, that could either leave the circuit unprotected (dangerous) or trip the circuit breaker (blackout).

Every containment action in an OT environment requires human approval. Period. No exceptions. I will say it again because some product manager will inevitably ask: **never auto-contain OT devices.**

The `ensemble` anomaly detection with majority voting is also crucial. A single model might flag a transient network glitch as an anomaly. Requiring two of three models to agree dramatically reduces false positives. In 90 days of production, the ensemble approach produced a false positive rate of 3.8% -- compared to 14.2% with a single isolation forest model in our testing.

### OT Detection Rules

```bash
# Detection rule: Unauthorized DNP3 write operation
curl -s -X POST https://playseat-grid.internal:3000/api/v1/streaming/rules \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "OT-001-UNAUTHORIZED-DNP3-WRITE",
    "description": "Detect DNP3 write/operate commands from unauthorized sources",
    "severity": "critical",
    "rule": {
      "type": "allowlist_violation",
      "source": "ot_network_capture",
      "match": {
        "protocol": "dnp3",
        "function_code": {"in": [2, 3, 4, 5, 6, 7, 8, 17, 18]}
      },
      "allowlist": {
        "source": "zero_trust_active_sessions",
        "match_fields": ["src_ip", "dst_ip"],
        "description": "Only allow DNP3 write commands from IPs with active Zero Trust sessions"
      },
      "alert": {
        "title": "Unauthorized DNP3 write to ${dst_ip} (${device_name})",
        "details": "Source ${src_ip} sent DNP3 function code ${function_code} (${function_name}) to ${device_name} at ${substation_name}. No active Zero Trust session found.",
        "impact_analysis": true,
        "actions": ["alert_ot_soc", "alert_ot_manager", "log_evidence", "capture_pcap"]
      }
    },
    "enabled": true
  }'
```

```bash
# Detection rule: Polling interval deviation (man-in-the-middle indicator)
curl -s -X POST https://playseat-grid.internal:3000/api/v1/streaming/rules \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "OT-002-POLLING-ANOMALY",
    "description": "Detect deviation from expected SCADA polling intervals",
    "severity": "high",
    "rule": {
      "type": "temporal_deviation",
      "source": "ot_network_capture",
      "match": {"protocol": {"in": ["dnp3", "iec104"]}, "direction": "master_to_slave"},
      "baseline": {
        "reference": "ot-protocol-baseline-v1",
        "feature": "polling_interval",
        "group_by": ["src_ip", "dst_ip"]
      },
      "conditions": [
        "abs(interval_ms - expected_interval_ms) > jitter_tolerance_ms * 3",
        "consecutive_deviations > 5"
      ],
      "alert": {
        "title": "SCADA polling anomaly: ${src_ip} -> ${dst_ip}",
        "details": "Polling interval deviated to ${interval_ms}ms (expected ${expected_interval_ms}ms +/- ${jitter_tolerance_ms}ms) for ${consecutive_deviations} consecutive polls. May indicate network congestion, device malfunction, or man-in-the-middle activity.",
        "actions": ["alert_ot_soc", "log_evidence", "trigger_network_capture"]
      }
    },
    "enabled": true
  }'
```

```bash
# Detection rule: Firmware change without change ticket
curl -s -X POST https://playseat-grid.internal:3000/api/v1/streaming/rules \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "OT-003-UNAUTHORIZED-FIRMWARE",
    "description": "Detect firmware version changes without corresponding change ticket",
    "severity": "critical",
    "rule": {
      "type": "state_change",
      "source": "configuration_audit",
      "match": {"event_type": "firmware_version_change"},
      "correlation": {
        "source": "change_management_system",
        "match_fields": ["device_id"],
        "required_status": "approved",
        "time_window_hours": 24
      },
      "alert_on": "no_correlation",
      "alert": {
        "title": "Unauthorized firmware change on ${device_name} at ${substation_name}",
        "details": "Firmware changed from ${old_version} to ${new_version}. No approved change ticket found. This is a NERC CIP violation and potential compromise indicator.",
        "impact_analysis": true,
        "actions": ["alert_ot_soc", "alert_security_lead", "alert_compliance", "log_evidence"]
      }
    },
    "enabled": true
  }'
```

```bash
# Detection rule: Protocol role violation (the rule that caught RTU-4471)
curl -s -X POST https://playseat-grid.internal:3000/api/v1/streaming/rules \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "OT-007-PROTOCOL-ROLE-VIOLATION",
    "description": "Detect devices sending protocol messages inconsistent with their role",
    "severity": "critical",
    "rule": {
      "type": "role_violation",
      "source": "ot_network_capture",
      "role_mapping": {
        "rtu": {"allowed_roles": ["slave"], "disallowed_functions": ["command", "configure"]},
        "ied": {"allowed_roles": ["slave"], "disallowed_functions": ["command"]},
        "hmi": {"allowed_roles": ["master"], "disallowed_functions": ["firmware_update"]},
        "plc": {"allowed_roles": ["slave"], "disallowed_functions": ["command", "configure"]}
      },
      "alert": {
        "title": "Protocol role violation: ${device_name} acting as ${observed_role} (expected ${expected_role})",
        "details": "Device ${device_name} (${device_type}) at ${substation_name} sent ${function_name} frames which are ${observed_role} operations. This device is registered as a ${expected_role}. Strongly indicates compromise.",
        "impact_analysis": true,
        "actions": ["alert_ot_soc", "alert_ot_manager", "alert_security_lead", "capture_pcap", "log_evidence"]
      }
    },
    "enabled": true
  }'
```

That last rule is the one that caught the compromised RTU. A slave device sending master commands is unambiguous. The device was not doing what devices of that type are supposed to do. This violation has a near-zero false positive rate because role assignments are deterministic, not statistical.

---

## 38.6 -- Geofencing for Substations

The `svc-geoint` crate provides geofencing. In the banking deployment, we used it for login location verification. In a power grid, geofencing is physical security.

```bash
# Geofence for Substation 47
curl -s -X POST https://playseat-grid.internal:3000/api/v1/geoint/geofences \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Substation-047-perimeter",
    "fence_type": "polygon",
    "polygon": [
      {"lat": 52.4847, "lon": 13.3902},
      {"lat": 52.4852, "lon": 13.3918},
      {"lat": 52.4843, "lon": 13.3923},
      {"lat": 52.4838, "lon": 13.3907}
    ],
    "alert_on_enter": true,
    "alert_on_exit": true,
    "linked_assets": ["substation-047-*"],
    "correlation_rules": [
      {
        "name": "cyber-physical-correlation",
        "description": "Correlate cyber access with physical presence",
        "condition": "cyber_access AND NOT physical_presence",
        "alert_severity": "high",
        "alert_message": "Cyber access to Sub-047 from ${src_ip} without physical badge-in."
      },
      {
        "name": "after-hours-physical-access",
        "description": "Physical access outside business hours without emergency",
        "condition": "physical_entry AND (hour < 6 OR hour > 22) AND NOT emergency_declared",
        "alert_severity": "medium",
        "alert_message": "After-hours physical access to Sub-047 by ${badge_holder} at ${timestamp}."
      },
      {
        "name": "unknown-vehicle-detection",
        "description": "Vehicle activity without authorized work order",
        "condition": "vehicle_detected AND NOT work_order_active",
        "alert_severity": "medium",
        "alert_message": "Unscheduled vehicle near Sub-047 perimeter at ${timestamp}."
      }
    ],
    "status": "active"
  }'
```

### The Two Unauthorized Physical Access Attempts

**Attempt 1 (Week 3):** At 02:17 on a Saturday, a badge-in at Substation 112. Badge belonged to a contractor whose access had been revoked two weeks earlier but whose badge was never collected. Geofence alert fired: outside business hours, no emergency, no work order. Security patrol found the individual retrieving personal tools. No malicious intent, but a critical gap in badge revocation.

**Attempt 2 (Week 9):** Vehicle detected near Substation 47 at 23:40 on a Tuesday. No work order. No badge-in. Vehicle remained for 47 minutes. Security found two individuals photographing the substation from outside the fence, claiming to be journalists. Incident documented and reported to national infrastructure protection agency.

Neither incident would have been detected by existing tools. The badge system recorded events but did not cross-reference against revocation lists or work orders. The camera analytics feed was not connected to any alerting system before Playseat.

---

## 38.7 -- The Compromised RTU: 47 Minutes to Detection

Six weeks into the deployment, the platform detected its first genuine cyber incident.

**14:23:17 UTC** -- Sentinel baseline anomaly. RTU-4471 at Substation 23 begins sending IEC 104 ASDU Type 45 (Single Command) frames. RTU-4471 is a slave device. It should never send command frames. Two of three ensemble models flag anomaly immediately. Third model flags 3 seconds later.

**14:23:17.400 UTC** -- Rule OT-007-PROTOCOL-ROLE-VIOLATION fires. Critical severity. Impact analysis attached: Substation 23 protects 4 circuits serving 89,000 customers, including a regional hospital.

**14:23:18 UTC** -- SOAR playbook OT-CRITICAL-RESPONSE activates. Simultaneous notifications to OT SOC, OT manager, security lead. Automated packet capture begins. Incident record created with evidence chain.

**14:24 UTC** -- SOC analyst reviews. RTU-4471 is sending command frames to RTU-4472 and RTU-4473, attempting to open circuit breakers.

**14:27 UTC** -- OT engineer confirms: no maintenance, no change ticket, no authorized session.

**14:31 UTC** -- OT manager approves isolation. SOAR executes: substation switch configured to drop all traffic from RTU-4471.

**14:35 UTC** -- Grid operations confirms protection scheme degraded but circuits energized. Manual protection activated. Crew dispatched.

**14:47 UTC** -- Forensic analysis reveals: RTU-4471 compromised via web-based configuration interface vulnerability. Interface was exposed on OT network (installed before Zero Trust deployment, missed during initial inventory).

**15:10 UTC** -- Full incident declared. All 127 RTUs of same model audited. Three additional show reconnaissance activity from external IPs via cellular modems.

**Detection to containment: 8 minutes. Detection to incident declaration: 47 minutes.**

Previous estimated detection time with Claroty on 40% of network: **14 days** -- because RTU-4471 was in the unmonitored 60%.

The commands RTU-4471 was sending would have caused a blackout affecting 89,000 customers. The attack was contained before any breaker operated.

---

## 38.8 -- NERC CIP Compliance Automation

```bash
# NERC CIP compliance status
curl -s https://playseat-grid.internal:3000/api/v1/compliance/frameworks/nerc-cip/status \
  -H "Authorization: Bearer $TOKEN" | jq '.summary'
```

```json
{
  "framework": "NERC CIP v7",
  "total_requirements": 97,
  "fully_automated": 71,
  "semi_automated": 19,
  "manual_only": 7,
  "compliant": 93,
  "partially_compliant": 4,
  "non_compliant": 0,
  "key_standards": {
    "CIP-002": {"status": "compliant", "method": "automated", "description": "BES Cyber System Categorization"},
    "CIP-005": {"status": "compliant", "method": "automated", "description": "Electronic Security Perimeters"},
    "CIP-007": {"status": "compliant", "method": "automated", "description": "System Security Management"},
    "CIP-008": {"status": "compliant", "method": "automated", "description": "Incident Reporting & Response"},
    "CIP-010": {"status": "compliant", "method": "automated", "description": "Configuration Change Management"},
    "CIP-013": {"status": "partially_compliant", "method": "manual", "description": "Supply Chain Risk Management"}
  },
  "audit_evidence": {
    "auto_generated_reports": 847,
    "evidence_items_collected": 12400,
    "evidence_integrity_verified": "BLAKE3 + SHA-256",
    "estimated_manual_hours_saved": 1680
  }
}
```

71 of 97 requirements fully automated. 1,680 manual hours saved per year -- approximately $252,000 at fully loaded rates. But the real value is faster audit cycles, fewer findings, and compliance staff freed to do actual security work.

---

## 38.9 -- Results Summary (First 6 Months)

| Category | Metric | Value |
|----------|--------|-------|
| **Security** | Compromised devices detected | 1 (RTU-4471) |
| | Reconnaissance attempts detected | 3 additional RTUs |
| | Unauthorized physical access attempts | 2 |
| | Cyber-caused outages | **0** (vs 3 prior year) |
| | Detection time (RTU compromise) | 0 seconds (automated) |
| | Containment time (RTU compromise) | 8 minutes |
| **Zero Trust** | Access sessions monitored | 12,847 |
| | Policy violations blocked | 2,341 |
| | Rogue cellular modems discovered | 7 |
| | Unauthorized access attempts | 14 |
| **Compliance** | NERC CIP automated | 71/97 (73%) |
| | Manual hours saved/year | 1,680 |
| | Compliance cost reduction | $252,000/year |
| **OT Monitoring** | Devices baselined | 15,100 |
| | Industrial protocols | 3 (DNP3, IEC 104, Modbus) |
| | Features per device | 8 |
| | Anomaly detection accuracy | 96.2% |
| **Cost** | Servers deployed | 12 |
| | Deployment time | 8 weeks |
| | Previous annual security spend | $4.2M |
| | Playseat annual cost | $680,000 |

Zero cyber-caused outages. 28 million people kept their lights on. That is the only metric that matters.

---

## 38.10 -- Lessons Learned

1. **Never auto-contain OT devices.** In IT, automated containment saves time. In OT, it can cause the outage you are trying to prevent. Human approval required for every action.

2. **Baseline at the protocol function-code level.** IP addresses and ports are not enough for OT. You need function codes, polling intervals, data value ranges, communication partners.

3. **Physical and cyber security are inseparable in critical infrastructure.** Geofencing caught two incidents that pure cyber monitoring missed entirely.

4. **Discover shadow infrastructure first.** The 7 cellular modems were the most critical finding. You cannot protect what you do not know exists.

5. **Digital twins enable impact-aware alerting.** "Anomalous traffic from 10.47.3.12" does not convey urgency. "Compromised RTU protecting circuits serving 89,000 customers" does.

6. **Ensemble models beat single models in OT.** Majority voting across three models reduced false positives from 14.2% to 3.8%. In safety-critical environments, false positive reduction is a safety requirement, not a nice-to-have.

---

*Next chapter: [Chapter 39 -- Making It Yours: Advanced Customization Guide](39-advanced-customization.md)*

---

`(c) 2026 Playseat -- All Rights Reserved | Proprietary and Confidential`
