# Chapter 24: Red Team Advanced — Simulating the Rescue

> *"You don't send twelve people into a building controlled by a transnational crime syndicate without testing every door, every camera angle, and every second of the plan against the worst case scenario. You test it. Then you test it again. Then you test the version where everything goes wrong."*

---

**OPERATION STARLIGHT — T-minus 16 hours**
**Playseat Tactical Operations Center, undisclosed NATO facility**
**February 18, 2026 — 13:30 UTC**

---

The disinformation was in play. Duval had taken the bait — all three decoy documents, downloaded and presumably transmitted to PHANTOM MERCY by now. If our analysis was right, they were reinforcing the north wall of the hospital and preparing for a 22:00 assault by a twenty-four-person team that didn't exist.

That bought us time. It didn't buy us certainty.

Marchetti sat across the table, sleeves rolled up, the overhead lights throwing hard shadows under his eyes. Between us: a twelve-inch tablet showing the Playseat red team module, and a pot of coffee that had gone cold two hours ago.

"We simulate it," he said. "All three entry vectors. Full adversary emulation. I want to know what happens when things go wrong."

He was right. The difference between a rescue operation and a suicide mission is the simulation that happens before boots hit ground. Playseat's red team module wasn't built for hostage rescue — it was built for penetration testing, adversary emulation, kill chain analysis. But the architecture is the same. An attacker. A defender. A building with defenses. And the question: *can we get in, achieve the objective, and get out alive?*

I opened the module and started building the scenario.

---

## Rules of Engagement: Simulating PHANTOM MERCY's Defenses

Every red team engagement starts with Rules of Engagement. Even simulated ones. Especially simulated ones — because the ROE defines the boundaries of what we're testing, and if the boundaries are wrong, the simulation is worthless.

```bash
# Create the STARLIGHT rescue simulation engagement
curl -X POST https://playseat.internal/api/v1/redteam/playbooks \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "STARLIGHT-SIM: Rescue Operation War Game — Hôpital Saint-Lazare",
    "description": "Full adversary emulation of PHANTOM MERCY defensive capabilities at the abandoned Hôpital Saint-Lazare, Marseille. Three entry vectors tested against estimated threat posture. Objective: extract one hostage from basement level B2.",
    "roe": {
      "engagement_type": "adversary_emulation_simulation",
      "duration_weeks": 0,
      "start_date": "2026-02-18",
      "end_date": "2026-02-18",
      "authorized_by": "Operation Commander STARLIGHT — Marchetti, G. (NATO SOF)",
      "scope": {
        "in_scope": [
          "Hôpital Saint-Lazare — all floors including basement levels B1 and B2",
          "Surrounding perimeter — 200m radius",
          "PHANTOM MERCY estimated personnel (8-12 armed operatives)",
          "Known surveillance systems (CCTV, motion sensors, ICS building management)",
          "Communication interception capabilities",
          "Counter-surveillance measures"
        ],
        "out_of_scope": [
          "Civilian structures within 200m radius",
          "Municipal infrastructure (power grid, water, telecom)",
          "Law enforcement response modeling (GIGN on standby, not modeled as adversary)",
          "PHANTOM MERCY reinforcement from external locations (contained scenario)"
        ]
      },
      "constraints": {
        "simulation_only": true,
        "no_live_systems_accessed": true,
        "no_real_network_interaction": true,
        "objective": "Extract hostage CLARA from basement B2, minimize engagement, zero civilian casualties",
        "max_acceptable_friendly_casualties": 0,
        "max_operation_duration_minutes": 45,
        "abort_criteria": [
          "Hostage confirmed killed",
          "More than 2 friendly casualties",
          "Operation duration exceeds 45 minutes",
          "PHANTOM MERCY initiates building destruction"
        ]
      },
      "emergency_contacts": {
        "simulation_lead": "analyst_primary",
        "operation_commander": "marchetti_g",
        "intelligence_lead": "analyst_primary"
      }
    }
  }'
```

Response:

```json
{
  "id": "01951000-0000-7000-8000-000000000001",
  "name": "STARLIGHT-SIM: Rescue Operation War Game — Hôpital Saint-Lazare",
  "status": "planning",
  "created_at": "2026-02-18T13:35:00Z"
}
```

---

## Phase 1: Reconnaissance — Mapping the Kill Zone

Before we could simulate the rescue, we needed to model the target. Everything we knew about the hospital, compiled from OSINT, satellite imagery, architectural records, and Clara's own intelligence drops before she went dark.

```bash
# Phase 1: Log all reconnaissance data on the target facility
curl -X POST https://playseat.internal/api/v1/redteam/playbooks/${PLAYBOOK_ID}/techniques \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "technique_id": "T1592.004",
    "technique_name": "Gather Victim Host Information: Client Configurations",
    "tactic": "reconnaissance",
    "phase": 1,
    "status": "completed",
    "details": {
      "method": "Multi-source intelligence fusion: OSINT, IMINT, SIGINT, HUMINT (Clara pre-capture drops)",
      "target_facility": {
        "name": "Hôpital Saint-Lazare",
        "location": "Zone Industrielle Nord, Marseille, France",
        "type": "Abandoned hospital, built 1967, closed 2019",
        "floors": 4,
        "basement_levels": 2,
        "total_area_sqm": 8200,
        "structural_condition": "Degraded but structurally sound — concrete frame, brick infill walls",
        "known_access_points": {
          "main_entrance_north": "Double doors, boarded. PHANTOM MERCY primary entry. 2 cameras.",
          "service_entrance_east": "Single steel door. Loading dock. 1 camera, motion sensor.",
          "emergency_exit_south": "Fire escape, ground floor. Partially concealed by vegetation. 1 camera (PTZ, 12-min gap).",
          "basement_ventilation_west": "Industrial ventilation shaft. 1.2m diameter. No camera. Drops to B1.",
          "roof_access": "Service ladder from adjacent building (3m gap). No camera coverage."
        }
      },
      "surveillance_systems": {
        "cctv_cameras": 14,
        "camera_types": {
          "fixed": 8,
          "ptz": 4,
          "thermal": 2
        },
        "motion_sensors": 6,
        "locations": [
          "Main entrance (2x fixed + 1x thermal)",
          "East service door (1x fixed + 1x motion)",
          "South fire escape (1x PTZ)",
          "West parking area (1x PTZ + 1x thermal)",
          "Interior hallway ground floor (2x fixed + 2x motion)",
          "Stairwell to basement (2x fixed + 1x motion)",
          "Basement B1 corridor (1x fixed + 1x motion)",
          "Basement B2 — holding area (1x PTZ + 1x motion)"
        ],
        "monitoring": "Central monitoring room, ground floor northeast corner. 2 operators estimated.",
        "recording": "Local NVR, no cloud backup (confirmed via network scan from Clara's SIGINT drop)"
      },
      "building_management_system": {
        "type": "Schneider Electric EcoStruxure (legacy installation, 2015)",
        "status": "Partially operational — PHANTOM MERCY reactivated HVAC and lighting on occupied floors",
        "accessible_via_network": true,
        "default_credentials_likely": true,
        "capabilities": [
          "HVAC control (all floors)",
          "Emergency lighting",
          "Fire suppression (CO2 system — B1 and B2)",
          "Door access control (magnetic locks, B1 and B2 stairwell)"
        ]
      },
      "time_spent_hours": 72,
      "sources": ["satellite_imagery", "architectural_records_marseille", "clara_humint_drops", "sigint_passive", "osint_web"]
    }
  }'
```

Fourteen cameras. Six motion sensors. A building management system from 2015 that was probably still running default credentials. And a CO2 fire suppression system in the basement that could be lethal if triggered while our people were inside.

I stared at the building model on screen. Four floors of abandoned hospital, slowly being eaten by the Marseille weather. Two basement levels where they were holding the most important person in this investigation.

Clara had chosen this place on purpose. I was sure of it now. She'd let herself be captured by PHANTOM MERCY knowing they'd take her to this hospital — because she'd already mapped it. She'd already assessed the surveillance. She'd already identified the thermal coverage gap on the south wall.

She'd planned her own rescue.

---

## Phase 2: Mobile Device & Communication Exploitation Analysis

PHANTOM MERCY's operatives used phones. Of course they did. Everyone uses phones. The question was: what could we learn from their communications, and could we disrupt them during the operation?

```bash
# Phase 2: Mobile device exploitation assessment
curl -X POST https://playseat.internal/api/v1/redteam/playbooks/${PLAYBOOK_ID}/techniques \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "technique_id": "T1422",
    "technique_name": "System Network Configuration Discovery (Mobile)",
    "tactic": "discovery",
    "phase": 2,
    "status": "completed",
    "details": {
      "method": "Passive SIGINT analysis of cellular traffic within 200m of target facility",
      "findings": {
        "unique_imsi_detected": 14,
        "unique_imei_detected": 12,
        "device_analysis": [
          {
            "identifier": "PHANTOM-PHONE-01",
            "type": "Samsung Galaxy A54",
            "os": "Android 14",
            "sim_origin": "Romania (Orange RO)",
            "pattern": "Present 24/7 — likely guard rotation supervisor",
            "encrypted_messaging": "Signal detected (cannot intercept content)",
            "calls_to": "3 Romanian numbers, 1 Turkish number"
          },
          {
            "identifier": "PHANTOM-PHONE-02",
            "type": "iPhone 15",
            "os": "iOS 17.3",
            "sim_origin": "France (SFR prepaid)",
            "pattern": "Present 08:00-20:00 — day shift operative",
            "encrypted_messaging": "WhatsApp detected",
            "calls_to": "Local Marseille numbers only"
          },
          {
            "identifier": "PHANTOM-PHONE-03 through PHANTOM-PHONE-09",
            "type": "Mixed Android devices",
            "pattern": "Rotating presence — consistent with 3 shifts of 3-4 operatives",
            "encrypted_messaging": "Signal primary, Telegram secondary"
          }
        ],
        "communication_pattern_summary": {
          "shift_changes": "08:00, 16:00, 00:00 — 8-hour shifts",
          "peak_communication": "Shift change windows (15 min before/after)",
          "minimum_communication": "02:00-05:00 — night shift, minimal traffic",
          "external_check_in": "PHANTOM-PHONE-01 calls Romanian number at 09:00 and 21:00 daily"
        },
        "jamming_feasibility": {
          "cellular_jamming": "Feasible — portable jammer effective within 50m radius",
          "wifi_deauthentication": "Feasible — building WiFi network identified (SSID: 'maintenance')",
          "risk": "Jamming triggers alert if monitoring station detects signal loss",
          "recommendation": "Jam at H-hour only — 30-second window before entry"
        }
      },
      "time_spent_hours": 48,
      "detection_risk": "low — passive SIGINT only, no active probing"
    }
  }'
```

Three shifts. Three to four operatives per shift. One supervisor who never left the building. The night shift — our window — had the thinnest crew: three operatives and the supervisor, with communication traffic dropping to near-zero between 02:00 and 05:00.

The shift change at 00:00 would bring fresh bodies. The one at 08:00 would bring more. Our window was the dead hours between 04:00 and 06:00, when the night shift was tired, the supervisor had done his evening check-in eight hours ago, and the building was as quiet as it would ever be.

05:30. That was the number. Marchetti had picked it three days ago based on instinct. The data confirmed it.

---

## Phase 3: IoT Assessment — Camera Systems and Sensor Networks

**14:15 UTC**

This was the critical phase. Fourteen cameras and six motion sensors stood between us and Clara. Each one needed to be mapped, timed, and either avoided or neutralized.

```bash
# Phase 3: IoT security assessment — surveillance infrastructure
curl -X POST https://playseat.internal/api/v1/redteam/playbooks/${PLAYBOOK_ID}/techniques \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "technique_id": "T1040",
    "technique_name": "Network Sniffing (IoT Device Analysis)",
    "tactic": "discovery",
    "phase": 3,
    "status": "completed",
    "details": {
      "method": "Passive network analysis of surveillance system + Clara HUMINT drops on camera positions",
      "camera_analysis": [
        {
          "id": "CAM-01",
          "type": "fixed",
          "location": "Main entrance north, exterior",
          "field_of_view_degrees": 90,
          "resolution": "1080p",
          "night_vision": true,
          "blind_spots": "None — covers full approach from north",
          "vulnerability": "Network-connected to NVR via unencrypted RTSP stream"
        },
        {
          "id": "CAM-02",
          "type": "fixed",
          "location": "Main entrance north, interior vestibule",
          "field_of_view_degrees": 120,
          "resolution": "1080p",
          "night_vision": true,
          "blind_spots": "Left corner, 15-degree dead zone behind support column",
          "vulnerability": "Same RTSP stream, default admin/admin credentials on web interface"
        },
        {
          "id": "CAM-07",
          "type": "PTZ",
          "location": "South fire escape, exterior",
          "field_of_view_degrees": 340,
          "resolution": "4K",
          "night_vision": true,
          "patrol_cycle_seconds": 720,
          "blind_spots": "12-minute patrol cycle creates gap at position 240-252 degrees (south wall approach vector)",
          "gap_window": "05:18 to 05:30 every 12 minutes — confirmed by 72-hour observation",
          "vulnerability": "PTZ protocol (ONVIF) accessible on local network without authentication"
        },
        {
          "id": "CAM-13",
          "type": "PTZ",
          "location": "Basement B2 — holding area",
          "field_of_view_degrees": 180,
          "resolution": "1080p",
          "night_vision": true,
          "patrol_cycle_seconds": 300,
          "coverage": "Covers cell area and approach corridor",
          "vulnerability": "Power supply runs through B1 junction box — can be cut physically"
        },
        {
          "id": "CAM-11",
          "type": "thermal",
          "location": "West parking area, elevated mount",
          "detection_range_meters": 100,
          "field_of_view_degrees": 60,
          "blind_spots": "Vegetation along south wall partially blocks thermal signature if approach is low and slow",
          "vulnerability": "Thermal contrast lowest at dawn when building walls are warmest — 05:15-05:45 optimal"
        }
      ],
      "motion_sensor_analysis": [
        {
          "id": "MS-01",
          "type": "PIR (passive infrared)",
          "location": "East service door, interior",
          "range_meters": 12,
          "bypass_method": "PIR sensors detect heat differential — space blanket reduces thermal signature below threshold"
        },
        {
          "id": "MS-04",
          "type": "PIR",
          "location": "Stairwell to basement, B1 landing",
          "range_meters": 8,
          "bypass_method": "Sensor mounted at 2.1m height, detection cone starts at 1.5m — crawl approach viable"
        },
        {
          "id": "MS-06",
          "type": "Microwave",
          "location": "Basement B2 corridor",
          "range_meters": 15,
          "bypass_method": "Cannot bypass without triggering — must be neutralized via BMS or physically disabled"
        }
      ],
      "nvr_analysis": {
        "make": "Hikvision DS-7732NI-K4",
        "firmware": "V4.30.085 (2021 — known CVEs)",
        "network_accessible": true,
        "default_credentials": "admin/admin123 (NOT changed — confirmed via Clara SIGINT)",
        "capabilities": [
          "Disable individual camera feeds",
          "Loop playback (show recorded footage instead of live)",
          "Disable motion detection alerts"
        ],
        "attack_plan": "Access NVR at H-5 minutes via BMS network. Loop CAM-07 and CAM-11 feeds. Disable MS-06 alert."
      }
    }
  }'
```

I read the NVR analysis three times. Admin/admin123. A building full of surveillance equipment protecting a kidnapped intelligence officer, and they hadn't changed the default password on the recording system.

Clara had confirmed it. One of her SIGINT drops — a burst transmission from inside the hospital, probably taken at enormous personal risk — included the NVR credentials. She'd done a network scan from inside the building. From inside her cell. With a device she'd somehow concealed on her person when she allowed herself to be captured.

That was Clara. She didn't get captured. She infiltrated.

---

## Phase 4: ICS Security — The Building Management System

**15:00 UTC**

The abandoned hospital still had a functioning building management system. PHANTOM MERCY had reactivated it for HVAC and lighting. Which meant it could be used against them.

```bash
# Phase 4: ICS/BMS security assessment
curl -X POST https://playseat.internal/api/v1/redteam/playbooks/${PLAYBOOK_ID}/techniques \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "technique_id": "T0883",
    "technique_name": "ICS — Internet Accessible Device",
    "tactic": "initial_access",
    "phase": 4,
    "status": "completed",
    "details": {
      "method": "BMS network accessible from NVR subnet — lateral pivot from NVR compromise",
      "bms_details": {
        "system": "Schneider Electric EcoStruxure Building Expert",
        "version": "3.2.1 (2015 installation, never updated)",
        "protocol": "BACnet/IP on port 47808",
        "authentication": "None — BACnet communications unauthenticated",
        "network_segment": "Same subnet as NVR — no segmentation",
        "known_cves": [
          "CVE-2023-37196 — Authentication bypass in EcoStruxure",
          "CVE-2023-37197 — Remote code execution via crafted BACnet packet"
        ]
      },
      "controllable_systems": [
        {
          "system": "HVAC — all floors",
          "tactical_use": "Can be used to mask thermal signatures during approach (raise building temp to ambient)",
          "risk": "Low — HVAC changes are gradual, unlikely to alert guards"
        },
        {
          "system": "Emergency lighting",
          "tactical_use": "Can kill all lights simultaneously at H-hour. Night vision advantage to our team.",
          "risk": "Medium — sudden darkness will alert guards, but disorientation advantage is significant"
        },
        {
          "system": "Magnetic door locks — B1/B2 stairwell",
          "tactical_use": "Can unlock basement access doors remotely. Eliminates breaching requirement.",
          "risk": "Low — lock state change may produce audible click but no alarm"
        },
        {
          "system": "CO2 fire suppression — B1 and B2",
          "tactical_use": "MUST NOT be triggered — CO2 displacement in enclosed basement is lethal",
          "risk": "CRITICAL — ensure fire suppression cannot be triggered accidentally or by adversary",
          "mitigation": "Disable fire suppression system via BMS before entry. Verify disable state."
        }
      ],
      "attack_sequence": [
        {"time": "H-10 min", "action": "Access NVR via RTSP default credentials"},
        {"time": "H-8 min", "action": "Loop CAM-07 and CAM-11 feeds (south approach cameras)"},
        {"time": "H-5 min", "action": "Pivot to BMS via NVR subnet"},
        {"time": "H-5 min", "action": "DISABLE CO2 fire suppression on B1 and B2"},
        {"time": "H-3 min", "action": "Raise HVAC temperature to mask thermal approach"},
        {"time": "H-1 min", "action": "Unlock magnetic locks on B1/B2 stairwell doors"},
        {"time": "H-0", "action": "Kill emergency lighting on all floors"},
        {"time": "H-0", "action": "Jam cellular communications (30-second window)"},
        {"time": "H+0:30", "action": "Entry team moves through south fire escape"}
      ]
    }
  }'
```

The CO2 fire suppression was the thing that kept me awake. Two basement levels, enclosed, with an industrial CO2 system designed to flood the space and suffocate a fire by displacing all oxygen. If PHANTOM MERCY triggered it — or if we accidentally triggered it during the BMS compromise — everyone in the basement would be dead in ninety seconds. Including Clara.

"The fire suppression gets disabled first," I said to Marchetti. "Before anything else. Before we touch the cameras, before we touch the lights. The CO2 system goes offline."

"Agreed. And we verify."

"And we verify."

---

## Phase 5: Attack Path Simulation — Three Entry Vectors

**16:00 UTC**

This was the heart of the simulation. Three possible ways into the building, each scored by risk, speed, and probability of success. Playseat's red team module ran the numbers.

```bash
# Phase 5: Attack path simulation — three entry vectors
curl -X POST https://playseat.internal/api/v1/redteam/playbooks/${PLAYBOOK_ID}/techniques \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "technique_id": "T1190",
    "technique_name": "Exploit Public-Facing Application (Attack Path Simulation)",
    "tactic": "initial_access",
    "phase": 5,
    "status": "completed",
    "details": {
      "simulation_type": "multi_vector_comparison",
      "vectors": [
        {
          "name": "VECTOR ALPHA — North Main Entrance",
          "description": "Direct breach through boarded main entrance. Maximum speed, maximum exposure.",
          "entry_point": "Main entrance, north side",
          "approach_route": "Rue de l Industrie -> parking area -> 30m open ground to doors",
          "exposure_time_seconds": 45,
          "cameras_in_path": ["CAM-01", "CAM-02", "CAM-03"],
          "sensors_in_path": ["MS-02"],
          "guards_estimated": 2,
          "breaching_required": true,
          "noise_level": "high",
          "time_to_basement_minutes": 4,
          "advantages": [
            "Shortest path to stairwell",
            "Direct route — no navigation required"
          ],
          "disadvantages": [
            "Highest camera coverage",
            "Guard post within 10m of entry",
            "Breaching noise alerts entire building",
            "THIS IS WHERE DECOY INTEL SAYS WE ARE COMING — PHANTOM MERCY WILL REINFORCE"
          ],
          "risk_score": 92,
          "success_probability": 0.25,
          "expected_friendly_casualties": 2.1,
          "verdict": "REJECTED — unacceptable risk, especially with PHANTOM MERCY reinforcement"
        },
        {
          "name": "VECTOR BRAVO — South Fire Escape (PRIMARY)",
          "description": "Entry through south fire escape during PTZ camera gap. BMS-assisted approach.",
          "entry_point": "Fire escape, south side, ground floor",
          "approach_route": "Chemin des Oliviers -> vegetation line -> 15m low crawl to fire escape",
          "exposure_time_seconds": 12,
          "cameras_in_path": ["CAM-07 (looped)", "CAM-11 (thermal, masked by HVAC)"],
          "sensors_in_path": [],
          "guards_estimated": 0,
          "breaching_required": false,
          "noise_level": "minimal",
          "time_to_basement_minutes": 7,
          "advantages": [
            "12-minute PTZ gap confirmed by 72-hour surveillance",
            "Thermal camera masked by HVAC temperature manipulation",
            "No guards on south side (standard posture) — even fewer after decoy",
            "No breaching — fire escape door can be picked silently",
            "Vegetation provides concealment for approach",
            "BMS unlocks basement doors — no breaching below ground"
          ],
          "disadvantages": [
            "Longer route to basement (7 min vs 4 min)",
            "Window is tight — 12 minutes from approach to interior",
            "Requires precise timing with PTZ cycle"
          ],
          "risk_score": 31,
          "success_probability": 0.87,
          "expected_friendly_casualties": 0.3,
          "verdict": "RECOMMENDED — lowest risk, highest success probability, aligned with disinformation plan"
        },
        {
          "name": "VECTOR CHARLIE — West Ventilation Shaft",
          "description": "Entry through industrial ventilation shaft directly to basement B1.",
          "entry_point": "Ventilation shaft, west side, ground level",
          "approach_route": "Adjacent lot -> fence gap -> 8m to shaft opening",
          "exposure_time_seconds": 20,
          "cameras_in_path": ["CAM-09 (PTZ, west parking)"],
          "sensors_in_path": [],
          "guards_estimated": 0,
          "breaching_required": false,
          "noise_level": "low",
          "time_to_basement_minutes": 3,
          "advantages": [
            "Direct access to B1 — bypasses ground floor entirely",
            "No cameras inside shaft",
            "Fastest route to hostage (3 min)"
          ],
          "disadvantages": [
            "1.2m diameter shaft — single file only, no tactical flexibility",
            "Vertical drop of 4m to B1 — requires rope descent",
            "If detected, no retreat option — team trapped in shaft",
            "Maximum 2 operators through shaft before timing window closes",
            "No room to carry extraction equipment"
          ],
          "risk_score": 58,
          "success_probability": 0.62,
          "expected_friendly_casualties": 0.8,
          "verdict": "CONTINGENCY — use as secondary insertion point for 2-person advance team"
        }
      ],
      "recommended_plan": {
        "primary": "VECTOR BRAVO",
        "secondary": "VECTOR CHARLIE (2-person advance team)",
        "contingency": "VECTOR ALPHA (only if BRAVO and CHARLIE both compromised)",
        "combined_success_probability": 0.93,
        "combined_risk_score": 28
      }
    }
  }'
```

I stared at the numbers. Vector Bravo: 87% success probability. 0.3 expected friendly casualties. Risk score of 31 out of 100.

With the disinformation factored in — PHANTOM MERCY expecting us at the north entrance at 22:00 instead of the south entrance at 05:30 — the combined success probability climbed to 93%.

"Entrance B, 05:30," Marchetti said, reading the same numbers. "Thermal coverage is weakest. PTZ gap is confirmed. And thanks to our friend Duval, they'll have half their people watching the north wall."

He paused. "I want the two-person team through the ventilation shaft as well. Vector Charlie. They go in at H-minus-2, position themselves on B1, and hold the stairwell while the main team comes down from ground level."

"That puts people in the building before we've disabled the BMS."

"Two people. In a ventilation shaft. With no electronics. They sit, they wait, they hold the door when it's time." He looked at me. "I've done worse."

I believed him.

---

## The Kill Chain: Full Simulation Sequence

**17:00 UTC**

I built the complete kill chain in Playseat. Every phase, every technique, every second accounted for. The simulation would run against the modeled defenses and tell us where we'd be detected, where we'd succeed, and where someone might die.

```bash
# Build the complete kill chain for the rescue simulation
curl -X POST https://playseat.internal/api/v1/exploit/killchain/reconstruct \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "finding_id": "01951100-0000-7000-8000-000000000001",
    "campaign_id": "01951000-0000-7000-8000-000000000001",
    "title": "STARLIGHT Kill Chain: Full Rescue Sequence",
    "description": "Complete operational sequence from approach to extraction",
    "chain": [
      {
        "phase": "reconnaissance",
        "technique": "T1592.004",
        "target": "Hôpital Saint-Lazare",
        "action": "72-hour multi-source intelligence collection on target facility",
        "timestamp": "2026-02-15T00:00:00Z",
        "detected": false
      },
      {
        "phase": "initial_access",
        "technique": "T0883",
        "target": "NVR (Hikvision DS-7732NI-K4)",
        "action": "H-10: Access NVR via default RTSP credentials",
        "timestamp": "2026-02-19T05:20:00Z",
        "detected": false,
        "detection_detail": "RTSP login generates log entry but no alert configured"
      },
      {
        "phase": "defense_evasion",
        "technique": "T1562.001",
        "target": "CAM-07, CAM-11",
        "action": "H-8: Loop camera feeds on south approach cameras",
        "timestamp": "2026-02-19T05:22:00Z",
        "detected": false,
        "detection_detail": "Feed loop indistinguishable from live at monitoring station"
      },
      {
        "phase": "initial_access",
        "technique": "T0883",
        "target": "Schneider EcoStruxure BMS",
        "action": "H-5: Pivot from NVR to BMS via shared subnet. Disable CO2 fire suppression.",
        "timestamp": "2026-02-19T05:25:00Z",
        "detected": false,
        "detection_detail": "BACnet unauthenticated — no login event"
      },
      {
        "phase": "defense_evasion",
        "technique": "T0816",
        "target": "HVAC system",
        "action": "H-3: Raise building temperature to mask thermal approach signatures",
        "timestamp": "2026-02-19T05:27:00Z",
        "detected": false,
        "detection_detail": "HVAC changes are gradual — no perceptible shift for 15+ minutes"
      },
      {
        "phase": "initial_access",
        "technique": "T0812",
        "target": "Magnetic door locks B1/B2",
        "action": "H-1: Unlock basement stairwell doors via BMS",
        "timestamp": "2026-02-19T05:29:00Z",
        "detected": false,
        "detection_detail": "Lock state change produces soft click — inaudible from guard positions"
      },
      {
        "phase": "execution",
        "technique": "T1498",
        "target": "Cellular communications",
        "action": "H-0: Jam cellular in 50m radius. Kill emergency lighting via BMS.",
        "timestamp": "2026-02-19T05:30:00Z",
        "detected": true,
        "detection_detail": "Guards will notice lights off and phone signal loss. 30-second confusion window."
      },
      {
        "phase": "lateral_movement",
        "technique": "T1021",
        "target": "Ground floor to B2",
        "action": "H+0:30: Entry team through south fire escape. Move to basement via pre-unlocked stairwell.",
        "timestamp": "2026-02-19T05:30:30Z",
        "detected": false,
        "detection_detail": "Guards focused on power loss and comms failure. South approach clear."
      },
      {
        "phase": "actions_on_objectives",
        "technique": "T1005",
        "target": "Basement B2 — holding area",
        "action": "H+7:00: Reach hostage. Confirm identity. Begin extraction.",
        "timestamp": "2026-02-19T05:37:00Z",
        "detected": true,
        "detection_detail": "B2 guard will be engaged. Engagement time estimated 15-30 seconds."
      },
      {
        "phase": "exfiltration",
        "technique": "T1052",
        "target": "South fire escape to extraction vehicle",
        "action": "H+12:00: Extract hostage via ground floor south exit to waiting vehicle.",
        "timestamp": "2026-02-19T05:42:00Z",
        "detected": true,
        "detection_detail": "By this point, full alert. Extraction must be complete before organized response."
      }
    ]
  }'
```

### Kill Chain Detection Gap Analysis

```sql
-- Analyze detection gaps in the STARLIGHT simulation
WITH kill_chain_steps AS (
    SELECT
        step_index,
        (details->>'phase') AS phase,
        (details->>'technique') AS technique,
        (details->>'target') AS target,
        (details->>'action') AS action,
        (details->>'detected')::BOOLEAN AS detected,
        details->>'detection_detail' AS detection_detail,
        (details->>'timestamp')::TIMESTAMPTZ AS step_time
    FROM simulation_results sr
    WHERE sr.simulation_id = '01951100-0000-7000-8000-000000000001'
    ORDER BY step_index
),
detection_analysis AS (
    SELECT
        phase,
        COUNT(*) AS total_steps,
        COUNT(*) FILTER (WHERE detected) AS detected_steps,
        COUNT(*) FILTER (WHERE NOT detected) AS undetected_steps,
        ROUND(
            100.0 * COUNT(*) FILTER (WHERE detected) / GREATEST(COUNT(*), 1),
            1
        ) AS detection_rate_pct
    FROM kill_chain_steps
    GROUP BY phase
)
SELECT
    phase,
    total_steps,
    detected_steps,
    undetected_steps,
    detection_rate_pct,
    CASE
        WHEN detection_rate_pct = 0 THEN 'EXPLOITABLE: No detection'
        WHEN detection_rate_pct < 50 THEN 'FAVORABLE: Low detection'
        WHEN detection_rate_pct < 80 THEN 'CONTESTED: Mixed detection'
        ELSE 'HOSTILE: High detection'
    END AS assessment
FROM detection_analysis
ORDER BY
    CASE phase
        WHEN 'reconnaissance' THEN 1
        WHEN 'initial_access' THEN 2
        WHEN 'defense_evasion' THEN 3
        WHEN 'execution' THEN 4
        WHEN 'lateral_movement' THEN 5
        WHEN 'actions_on_objectives' THEN 6
        WHEN 'exfiltration' THEN 7
    END;
```

Results:

| phase | total_steps | detected | undetected | detection_rate | assessment |
|---|---|---|---|---|---|
| reconnaissance | 1 | 0 | 1 | 0% | EXPLOITABLE |
| initial_access | 3 | 0 | 3 | 0% | EXPLOITABLE |
| defense_evasion | 2 | 0 | 2 | 0% | EXPLOITABLE |
| execution | 1 | 1 | 0 | 100% | HOSTILE |
| lateral_movement | 1 | 0 | 1 | 0% | EXPLOITABLE |
| actions_on_objectives | 1 | 1 | 0 | 100% | HOSTILE |
| exfiltration | 1 | 1 | 0 | 100% | HOSTILE |

Seven phases undetected. Three detected. The three that were detected — execution, action on objective, exfiltration — were unavoidable. You can't rescue someone without the captors eventually knowing. The question was how much time we had between first detection and organized response.

The simulation said thirty seconds of confusion when the lights went out and phones died. Then ninety seconds before the guards oriented themselves. Then three to five minutes before they reached the basement.

We needed seven minutes to get from the fire escape to Clara's cell in B2.

It was tight. But it was doable.

---

## Clara's Contingency Plan

**18:30 UTC**

This is the part I didn't expect. The part that changed everything.

I was reviewing the evidence vault — the real one, not the decoy we'd built for Duval — checking the integrity of Clara's intelligence drops. Three burst transmissions over the past ten days, each one a compressed data package sent from inside the hospital during the night shift's low-communication window.

The first two I'd already analyzed: building schematics, camera positions, NVR credentials, guard rotation patterns. Standard HUMINT collection from a deep-cover operative working from inside enemy territory.

The third drop was different. It was encrypted with a key that only I had — a personal cipher we'd established months ago, long before PHANTOM MERCY, long before she went dark. It wasn't addressed to the investigation team. It was addressed to me.

I decrypted it in the evidence vault:

```bash
# Access the classified evidence item — Clara's personal contingency plan
curl -X GET "https://playseat.internal/api/v1/evidence?finding_id=01951200-0000-7000-8000-000000000001&evidence_type=humint_drop_encrypted" \
  -H "Authorization: Bearer ${TOKEN}"
```

The decrypted file was a single document. Title: **CONTINGENCY PLAN — IF I'M NOT RESCUED BY FEB 20.**

I read it three times. My hands didn't shake. I wouldn't let them.

Clara had planned for the possibility that we wouldn't come for her. Or that we'd come too late. The document contained:

1. **The location of the PHANTOM MERCY command server** — physically inside the hospital, B1 server room, rack 3. She'd already cloned the hard drive. The clone was taped behind a loose ventilation panel in her cell.

2. **A complete network diagram of PHANTOM MERCY's financial infrastructure** — twelve banks, four countries, forty-seven shell companies. She'd exfiltrated it from the command server during the twelve-minute windows when the B2 camera was in the far position of its patrol cycle.

3. **The identity of the mole** — "Jean-Marc Duval, INTERPOL Marseille. Recruited 2024 via financial leverage — gambling debts. Handler: Codename VIOREL, Romanian national, believed to be the caller on PHANTOM-PHONE-01."

She'd known. She'd known about Duval before we did. She'd known about the Romanian handler. She'd gathered the evidence from inside her cell.

4. **Extraction instructions for herself** — written in third person, clinical, precise. Entry via south fire escape during PTZ gap. BMS compromise sequence for the locks and lighting. The CO2 fire suppression warning. Everything we'd independently simulated in the red team module, she'd already planned.

She'd written our rescue plan for us. From inside the prison.

5. **A personal note.** Four words. Encrypted with our private cipher inside the already-encrypted document. A cipher inside a cipher.

*Come get me. Please.*

I closed the file. I pressed my palms against the desk until the grain of the wood cut into my skin.

Marchetti appeared in the doorway. He looked at my face and said nothing for a long time.

"She left instructions," I said.

"Of course she did."

"She identified the mole."

"Of course she did."

"She planned the rescue herself."

Marchetti sat down across from me. "Clara Dubois is the most capable officer I've worked with in thirty years. She walked into that building on purpose. She let them take her so she could access their server. She mapped their security from her cell. She identified the mole from inside a concrete box in a basement in Marseille." He leaned forward. "And she's waiting for you to come get her."

---

## Red Team Simulation Results: Final Assessment

**20:00 UTC**

I ran the final simulation. All inputs updated. Clara's intelligence integrated with our independent analysis. The disinformation confirmed in play. The BMS attack sequence validated.

```bash
# Generate the final simulation assessment report
curl -X POST https://playseat.internal/api/v1/reporting/generate \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "report_type": "red_team_executive",
    "campaign_id": "01951000-0000-7000-8000-000000000001",
    "template": "red_team_engagement_executive",
    "sections": {
      "engagement_overview": {
        "name": "STARLIGHT-SIM Final Assessment",
        "duration": "8 hours simulation (Feb 18, 2026)",
        "scope": "Full adversary emulation — PHANTOM MERCY defenses at Hôpital Saint-Lazare",
        "emulated_threat": "PHANTOM MERCY (transnational organized crime, 8-12 armed operatives)",
        "simulation_team_size": 2
      },
      "bottom_line": "Operation STARLIGHT is assessed as VIABLE with HIGH confidence. Primary entry vector (BRAVO — south fire escape) has 87% standalone success probability, rising to 93% with disinformation factored. Critical dependencies: (1) NVR/BMS compromise must succeed, (2) CO2 fire suppression must be disabled before basement entry, (3) timing must align with PTZ camera gap. The hostage has independently confirmed the entry vector and provided additional intelligence that increases confidence.",
      "risk_assessment": {
        "overall_risk": "MODERATE",
        "entry_vectors_analyzed": 3,
        "primary_vector_risk_score": 31,
        "combined_success_probability": 0.93,
        "expected_friendly_casualties": 0.3,
        "critical_dependencies": 3,
        "disinformation_effectiveness": "HIGH — confirmed delivery via compromised liaison"
      },
      "key_recommendations": [
        "EXECUTE: Vector BRAVO at 05:30 UTC+1, Feb 19",
        "ADVANCE TEAM: 2 operators via Vector CHARLIE at 05:28 to hold B1 stairwell",
        "CYBER: BMS/NVR compromise sequence beginning H-10 minutes",
        "CRITICAL: CO2 fire suppression disabled FIRST — non-negotiable",
        "COMMS: 30-second cellular jam at H-0 to disrupt guard coordination",
        "CONTINGENCY: Vector ALPHA available but PHANTOM MERCY will be reinforced there due to decoy",
        "MEDICAL: Trauma team staged 400m south at extraction point",
        "LEGAL: GIGN cordon established at 200m radius — no French law enforcement inside perimeter"
      ]
    }
  }'
```

93% probability of success. 0.3 expected friendly casualties. Those numbers were better than any rescue simulation I'd ever run. And they were better because of three things: Playseat's analytical engine, Marchetti's operational experience, and Clara Dubois — who'd turned her captivity into an intelligence operation and written the rescue plan from inside her own prison.

---

## Exploit Engine Stats: What We're Working With

```bash
# Get exploit engine statistics for the simulation
curl -X GET https://playseat.internal/api/v1/exploit-engine/stats \
  -H "Authorization: Bearer ${TOKEN}"
```

Response:

```json
{
  "total_modules": 342,
  "by_type": {
    "exploit": 156,
    "auxiliary": 89,
    "post": 67,
    "payload": 22,
    "encoder": 8
  },
  "by_reliability": {
    "excellent": 78,
    "great": 112,
    "good": 89,
    "normal": 52,
    "low": 11
  },
  "active_sessions": 0,
  "active_handlers": 0,
  "total_engagements": 48,
  "simulation_note": "All modules used in STARLIGHT-SIM are simulation-only. No live exploitation performed."
}
```

---

## 21:00 UTC — Eight Hours Out

The simulation was complete. The plan was set. The disinformation was in play.

In eight hours, twelve people would move through the darkness toward an abandoned hospital in Marseille. Two of them would already be inside, crouched in a ventilation shaft, waiting. One of them would be accessing a twenty-year-old building management system to disable locks, lights, and a fire suppression system that could kill everyone in the basement.

And at the end of it all — if the simulation was right, if the disinformation held, if the cameras looped cleanly and the doors unlocked silently and the guards looked north while we came from the south — I'd find Clara in a concrete room in basement B2, with a cloned hard drive taped behind a ventilation panel and evidence that could dismantle PHANTOM MERCY's entire operation.

93% isn't 100%.

Marchetti knew that. I knew that. Every operator on the team knew that. The 7% was the space where things went wrong. Where a guard turned at the wrong moment. Where a camera loop glitched. Where the CO2 system failed to disable. Where someone tripped a sensor that wasn't on the map.

7% is the space where people die.

I looked at the simulation results one more time. Vector Bravo. South fire escape. 05:30. PTZ gap confirmed. BMS compromise sequence validated. Disinformation delivered.

Then I closed the laptop and went to the briefing room, where twelve operators were waiting to be told that tomorrow morning they were going to rescue a woman who'd already done most of the work herself.

Clara. Hold on.

We're coming.

---

## What This Chapter Taught Me

1. **The ROE is your shield — even in simulation.** We defined the abort criteria before we ran a single scenario. Maximum operation duration, maximum casualties, conditions for calling it off. Without those boundaries, the simulation would have been optimistic garbage. Define your constraints first. Then test against them.

2. **Detection rate is the metric that matters.** Seven of ten phases went undetected. The three that were detected were inevitable — you can't extract a hostage silently. The question isn't "will they know?" It's "how long before they respond?" Every second of that gap was measured, tested, and planned for.

3. **IoT and ICS systems are the skeleton key.** A building management system from 2015 with unauthenticated BACnet communications gave us control over locks, lights, HVAC, and fire suppression. In a world of encrypted communications and hardened endpoints, it's the forgotten infrastructure that provides the decisive advantage.

4. **Red team simulations save lives.** If we'd gone in without simulating, we might have chosen Vector Alpha — the obvious path, the fastest path, the path PHANTOM MERCY expected. The simulation showed it was a death trap. 25% success, 2.1 expected casualties. The numbers made the decision for us.

5. **Never underestimate the person you're rescuing.** Clara mapped the building from inside. She identified the mole. She wrote the extraction plan. She left a cloned hard drive of the enemy's command server taped behind a ventilation panel. The simulation confirmed her analysis independently. She wasn't a victim waiting for rescue. She was an operator running a mission from inside a cell.

6. **Disinformation multiplies every advantage.** Alone, Vector Bravo had an 87% success probability. With the decoy intelligence delivered through Duval, it rose to 93%. The mole we'd identified in Chapter 23 became our most valuable asset — a controlled channel for feeding PHANTOM MERCY exactly the lies we needed them to believe.

---

*Next chapter: The knowledge graph connects everything — every entity, every relationship, every thread of the PHANTOM MERCY network mapped in a single, searchable intelligence web. The graph shows why Clara had to be rescued. She's the only person who's seen the entire picture.*

---

© 2026 Playseat — All Rights Reserved | Defensive Intelligence Through ADAPT
