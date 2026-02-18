# Chapter 20: Incident Commander -- Running Two Operations

---

> *"In an incident, the plan does not survive first contact.*
> *What survives is the process."*
>
> *But what happens when you're running two incidents at once --*
> *one the world can see, and one nobody can know about?*

---

## 20.1 -- The Call at 04:17 AM

Forty-two minutes after the CONVERGENCE alert fired, my secure phone rang again. Not Marchetti this time. It was Langdon from the DC operations center, and his voice had that flat quality that means someone's reading from a screen while trying not to panic.

"We've got a problem. Fondation Lumiere Bleue just hit the Children's Global Alliance network with a credential-stuffing attack. CGA's humanitarian logistics platform is down across West Africa and the Mediterranean. They're losing real-time tracking on 340 unaccompanied minors being processed through transit camps in Libya, Tunisia, and southern Italy."

I closed my eyes. CGA is one of the largest humanitarian organizations in the Mediterranean. Their logistics platform tracks aid shipments, refugee transport schedules, and -- critically -- the location and status of unaccompanied children moving through processing centers. Real children. Real tracking. Real infrastructure.

And PHANTOM MERCY had just knocked it offline.

This wasn't random. This was the cover operation. While we were watching their financial activity and Clara's distress signal, they'd launched a cyber attack against the very infrastructure that tracks the children they traffic. Blind the system that tracks kids, then move the kids.

I now had two operations to run simultaneously:

1. **The official incident**: PHANTOM MERCY's cyber attack on CGA's humanitarian infrastructure -- a genuine NIST 800-61 incident requiring detection, containment, eradication, and recovery.

2. **The classified operation**: Operation STARLIGHT -- tracking the convergence of intelligence that tells us PHANTOM MERCY is about to move, and Clara with it.

Same enemy. Same 24-hour clock. Two completely different incident response tracks that could not, under any circumstances, be allowed to contaminate each other. The official incident goes through normal channels -- CGA, law enforcement, CISA because CGA receives US government funding. STARLIGHT stays compartmented.

I am the incident commander for both.

This is the chapter about running an incident. But it's really about running two incidents when the universe conspires to make them inseparable.

---

## 20.2 -- The Incident Data Model

Both operations use the same incident management system. The data model:

```sql
-- The incident record
CREATE TABLE IF NOT EXISTS ir_incidents (
    id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title             TEXT NOT NULL,
    description       TEXT NOT NULL,
    phase             TEXT NOT NULL DEFAULT 'detection',
    priority          TEXT NOT NULL DEFAULT 'P2',
    affected_systems  JSONB NOT NULL DEFAULT '[]',
    commander_id      UUID,
    created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    resolved_at       TIMESTAMPTZ
);

-- Timeline of events during the incident
CREATE TABLE IF NOT EXISTS ir_timelines (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    incident_id     UUID NOT NULL REFERENCES ir_incidents(id),
    event_type      TEXT NOT NULL,
    description     TEXT NOT NULL,
    actor           TEXT,
    occurred_at     TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Containment actions taken
CREATE TABLE IF NOT EXISTS containment_actions (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    incident_id     UUID NOT NULL,
    action_type     TEXT NOT NULL,
    target          TEXT NOT NULL,
    status          TEXT NOT NULL DEFAULT 'executed',
    rolled_back     BOOLEAN NOT NULL DEFAULT false,
    executed_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Response playbooks
CREATE TABLE IF NOT EXISTS ir_playbooks (
    id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name                    TEXT NOT NULL,
    incident_type           TEXT NOT NULL,
    steps                   JSONB NOT NULL DEFAULT '[]',
    estimated_duration_mins INTEGER NOT NULL DEFAULT 60,
    created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Post-incident lessons
CREATE TABLE IF NOT EXISTS lessons_learned (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    incident_id     UUID NOT NULL,
    what_happened   TEXT NOT NULL,
    root_cause      TEXT NOT NULL,
    what_worked     TEXT NOT NULL,
    improvements    TEXT NOT NULL,
    action_items    JSONB NOT NULL DEFAULT '[]',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

The phase field follows the NIST 800-61 state machine:

```
Detection -> Triage -> Containment -> Eradication -> Recovery -> Lessons Learned
```

The Rust implementation enforces strict ordering:

```rust
// crates/svc-incident/src/manager.rs

pub struct IncidentManager;

impl IncidentManager {
    pub fn advance_phase(&self, incident: &mut Incident) -> bool {
        let next = match incident.phase {
            IncidentPhase::Detection => IncidentPhase::Triage,
            IncidentPhase::Triage => IncidentPhase::Containment,
            IncidentPhase::Containment => IncidentPhase::Eradication,
            IncidentPhase::Eradication => IncidentPhase::Recovery,
            IncidentPhase::Recovery => IncidentPhase::LessonsLearned,
            IncidentPhase::LessonsLearned => return false,
        };
        incident.phase = next;
        true
    }
}
```

You can't skip phases. You can't go backward. Every phase transition is logged. In a crisis, people want to skip steps. Especially when a French cryptographer's life depends on moving fast.

The system doesn't let them. The system doesn't let me.

---

## 20.3 -- Declaring Two Incidents

### Incident 1: CGA Infrastructure Attack (Official)

```bash
# Declare the official incident
curl -s -X POST http://localhost:3000/incident/incidents \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "PHANTOM MERCY cyber attack on CGA humanitarian logistics platform",
    "description": "Credential-stuffing attack originating from IPs associated with Fondation Lumiere Bleue has disabled Children Global Alliance logistics platform. Real-time tracking of 340 unaccompanied minors across Libya, Tunisia, and southern Italy is offline. Attack appears coordinated with broader PHANTOM MERCY trafficking operation. CGA receives US government humanitarian funding -- CISA notification required under CIRCIA.",
    "priority": "critical",
    "affected_systems": [
      "cga-logistics-platform",
      "cga-child-tracking-system",
      "cga-transport-scheduler",
      "cga-donor-database",
      "cga-api-gateway",
      "10.50.0.0/16"
    ]
  }' | jq .
```

```json
{
  "id": "01950b1a-0001-7000-8000-000000000001",
  "title": "PHANTOM MERCY cyber attack on CGA humanitarian logistics platform",
  "phase": "detection",
  "priority": "P0"
}
```

### Incident 2: Operation STARLIGHT (Compartmented)

```bash
# Declare the classified operation
curl -s -X POST http://localhost:3000/incident/incidents \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "STARLIGHT -- PHANTOM MERCY movement imminent, asset rescue coordination",
    "description": "COMPARTMENTED. CONVERGENCE alert triggered 03:25 EST. Three-source correlation confirms PHANTOM MERCY preparing movement operation. Financial precursors, network operational activity, and SIGINT distress signal from embedded asset. UAE transit accounts not yet active -- estimated 24-48h window before physical movement. Rescue coordination with DGSE and Europol via Marchetti. Legal evidence package generating for French magistrate authorization.",
    "priority": "critical",
    "affected_systems": [
      "SIGINT-relay-corsican",
      "FINTRAC-shell-monitor",
      "FLB-network-mirror",
      "evidence-locker-starlight"
    ]
  }' | jq .
```

```json
{
  "id": "01950b1a-0001-7000-8000-000000000002",
  "title": "STARLIGHT -- PHANTOM MERCY movement imminent, asset rescue coordination",
  "phase": "detection",
  "priority": "P0"
}
```

Two P0 incidents. Simultaneously. One public, one compartmented. Same incident commander. Same 24-hour clock.

I've run dozens of incidents in my career. Some lasted 20 minutes. Some lasted days. But I've never run two P0s at the same time where the containment actions on one could compromise the other.

If we shut down FLB's network too aggressively while containing the CGA attack, we lose the network intelligence feed that's tracking PHANTOM MERCY's operational communications. If we move too slowly on containment, children lose tracking coverage and PHANTOM MERCY uses the chaos to move.

The discipline has to be perfect. The documentation has to be perfect. The separation has to be perfect.

---

## 20.4 -- Phase 1: Detection (Both Tracks)

### CGA Track: Assembling the Public Team

```bash
curl -s -X POST http://localhost:3000/incident/incidents/01950b1a-0001-7000-8000-000000000001/timeline \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "event_type": "team_assembly",
    "description": "Bridge call opened at 04:25 EST. IR leads: K. Langdon (DC ops), T. Okafor (CGA security liaison), R. Vasquez (network forensics), L. Park (credential analysis). CISO notified. CGA executive team briefed on impact to child tracking systems. CISA notification timeline: 72 hours per CIRCIA.",
    "actor": "incident_commander"
  }' | jq .
```

```bash
curl -s -X POST http://localhost:3000/incident/incidents/01950b1a-0001-7000-8000-000000000001/timeline \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "event_type": "communication",
    "description": "Comm plan activated: Bridge #IR-20260218-CGA, Slack #incident-cga-attack, email distro ir-cga@ops.internal. Status updates every 30 minutes. CGA SOC integrated at 04:30 EST.",
    "actor": "incident_commander"
  }' | jq .
```

### STARLIGHT Track: Compartmented Team

```bash
curl -s -X POST http://localhost:3000/incident/incidents/01950b1a-0001-7000-8000-000000000002/timeline \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "event_type": "team_assembly",
    "description": "STARLIGHT coordination: Marchetti (Europol, operational lead), DGSE liaison officer (rescue planning), legal counsel (evidence admissibility), self (intelligence coordination and streaming analytics). Secure channel only. No bridge call -- face-to-face and encrypted comms only.",
    "actor": "incident_commander"
  }' | jq .
```

Two teams. Two communication channels. Two bridges. No overlap. The CGA team doesn't know about STARLIGHT. The STARLIGHT team knows about the CGA attack but treats it as intelligence context, not as their operational problem.

I'm on both bridges. Muted on one while talking on the other. Switching between tabs on my screen. Drinking coffee that's gone cold because I keep forgetting to drink it.

---

## 20.5 -- Phase 2: Triage

### CGA Track: Scope Assessment

```bash
curl -s -X POST http://localhost:3000/incident/incidents/01950b1a-0001-7000-8000-000000000001/advance \
  -H "Authorization: Bearer $TOKEN" | jq .
```

```json
{
  "advanced": true,
  "phase": "triage"
}
```

```bash
curl -s -X POST http://localhost:3000/incident/incidents/01950b1a-0001-7000-8000-000000000001/timeline \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "event_type": "assessment",
    "description": "Initial scope: Credential-stuffing attack using approximately 47,000 credential pairs against CGA API gateway. Attack source IPs trace to Fondation Lumiere Bleue network (Marseille) and 3 VPS providers (OVH, Hetzner, DigitalOcean). 1,247 valid credentials identified. Attackers used valid sessions to corrupt child tracking database records and disable transport scheduling API. 340 unaccompanied minors across 7 transit facilities have lost real-time tracking. No evidence of data exfiltration -- this appears to be disruption, not theft. Attack timeline: first credential attempt at 04:02 EST, API gateway overload at 04:11, child tracking offline at 04:14.",
    "actor": "T. Okafor"
  }' | jq .
```

### Selecting the Playbook

```bash
curl -s http://localhost:3000/incident/playbooks \
  -H "Authorization: Bearer $TOKEN" | jq .
```

```json
[
  {
    "id": "01950b1a-0010-7000-8000-000000000010",
    "name": "Ransomware Response",
    "incident_type": "ransomware",
    "step_count": 8
  },
  {
    "id": "01950b1a-0011-7000-8000-000000000011",
    "name": "Data Breach Response",
    "incident_type": "data_breach",
    "step_count": 8
  },
  {
    "id": "01950b1a-0012-7000-8000-000000000012",
    "name": "DDoS Mitigation",
    "incident_type": "ddos",
    "step_count": 7
  },
  {
    "id": "01950b1a-0013-7000-8000-000000000013",
    "name": "Insider Threat Response",
    "incident_type": "insider_threat",
    "step_count": 8
  }
]
```

None of these fit exactly. This isn't ransomware, it isn't DDoS, and it's not a data breach in the traditional sense. It's a targeted disruption of critical humanitarian infrastructure by a trafficking network. I need a custom playbook.

```bash
curl -s -X POST http://localhost:3000/incident/playbooks \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Humanitarian Infrastructure Disruption Response",
    "incident_type": "targeted_disruption",
    "steps": [
      "Identify and block attack source IPs and compromised credentials",
      "Restore child tracking system from verified backup",
      "Verify integrity of all minor records against last known good state",
      "Re-establish transport scheduling for active transit operations",
      "Deploy additional authentication controls (MFA enforcement)",
      "Coordinate with CISA and relevant law enforcement",
      "Preserve forensic evidence of attack for legal proceedings",
      "Conduct post-incident review with CGA security team"
    ]
  }' | jq .
```

```json
{
  "id": "01950b1a-0014-7000-8000-000000000014",
  "name": "Humanitarian Infrastructure Disruption Response",
  "incident_type": "targeted_disruption",
  "step_count": 8
}
```

Eight steps. The estimated duration is 480 minutes. But that doesn't account for the fact that I'm running this in parallel with a rescue operation. Real time: probably double.

### STARLIGHT Track: Intelligence Update

```bash
curl -s -X POST http://localhost:3000/incident/incidents/01950b1a-0001-7000-8000-000000000002/advance \
  -H "Authorization: Bearer $TOKEN" | jq .
```

```json
{
  "advanced": true,
  "phase": "triage"
}
```

```bash
curl -s -X POST http://localhost:3000/incident/incidents/01950b1a-0001-7000-8000-000000000002/timeline \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "event_type": "assessment",
    "description": "STARLIGHT intelligence assessment: The CGA cyber attack is assessed as a cover operation for PHANTOM MERCY physical movement. By disabling child tracking across Mediterranean transit facilities, PHANTOM MERCY creates a window where unaccompanied minors cannot be tracked in real-time. This window enables them to insert trafficked children into legitimate transit flows or extract children from processing facilities without immediate detection. The 04:02 attack start time aligns with the 02:47 financial precursor -- 75 minutes of preparation between wire transfers and cyber attack launch. Clara distress signal at 03:22 preceded the attack by 40 minutes -- she may have had advance warning of the plan.",
    "actor": "incident_commander"
  }' | jq .
```

The connection hit me like a punch to the chest. Clara sent the distress signal 40 minutes before the CGA attack. She knew. She knew they were about to launch the cyber attack, and she tried to warn us. That's why she powered the phone on out of cycle. That's why she sent the double ping.

She gave us 40 minutes of lead time. And I spent 30 of those minutes processing financial data.

---

## 20.6 -- Phase 3: Containment

This is where it gets brutally complicated.

### The Containment Dilemma

Normal containment for the CGA attack would mean blocking all traffic from FLB's network immediately. But FLB's network is one of our three intelligence sources for STARLIGHT. If I block their traffic at the firewall, I lose visibility into their operational communications. I lose the network mirror that's telling us what PHANTOM MERCY is planning.

I can't optimize for both. I have to choose.

I chose children.

```bash
# Advance CGA incident to containment
curl -s -X POST http://localhost:3000/incident/incidents/01950b1a-0001-7000-8000-000000000001/advance \
  -H "Authorization: Bearer $TOKEN" | jq .
```

```json
{
  "advanced": true,
  "phase": "containment"
}
```

### Containment Action 1: Block Attack Sources

```bash
curl -s -X POST http://localhost:3000/incident/contain \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "incident_id": "01950b1a-0001-7000-8000-000000000001",
    "action_type": "block_ip_range",
    "target": "FLB network block (91.234.xx.0/24) + 3 VPS source IPs at CGA perimeter"
  }' | jq .
```

```json
{
  "id": "01950b1a-0020-7000-8000-000000000020",
  "incident_id": "01950b1a-0001-7000-8000-000000000001",
  "action_type": "block_ip_range",
  "target": "FLB network block (91.234.xx.0/24) + 3 VPS source IPs at CGA perimeter",
  "status": "executed",
  "created_at": "2026-02-18T09:35:00Z"
}
```

I blocked them at CGA's perimeter, not at the source. The FLB network mirror is on their upstream provider -- it's upstream of the block. The intelligence feed stays alive. The attack traffic gets stopped at CGA's door.

It's not perfect. They could pivot to new source IPs. But it buys time.

### Containment Action 2: Revoke Compromised Credentials

```bash
curl -s -X POST http://localhost:3000/incident/contain \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "incident_id": "01950b1a-0001-7000-8000-000000000001",
    "action_type": "credential_revocation",
    "target": "1,247 compromised CGA API credentials -- forced reset and session termination"
  }' | jq .
```

### Containment Action 3: Isolate Corrupted Child Tracking Database

```bash
curl -s -X POST http://localhost:3000/incident/contain \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "incident_id": "01950b1a-0001-7000-8000-000000000001",
    "action_type": "database_isolation",
    "target": "CGA child tracking database -- snapshot current state, isolate from write operations, begin integrity verification against backup from 03:00 EST"
  }' | jq .
```

### Containment Action 4: Emergency Manual Tracking Activation

This one hurt to write. Because it means people -- real aid workers in real transit camps -- have to go back to paper tracking for 340 children while we restore the digital system.

```bash
curl -s -X POST http://localhost:3000/incident/contain \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "incident_id": "01950b1a-0001-7000-8000-000000000001",
    "action_type": "manual_fallback",
    "target": "Activate CGA manual tracking protocol for 7 transit facilities. Paper-based headcounts every 2 hours until digital tracking restored. Priority: verify all 340 registered minors are physically accounted for."
  }' | jq .
```

The containment engine tracks every action with rollback capability:

```rust
// crates/svc-incident/src/containment.rs

pub struct ContainmentEngine;

impl ContainmentEngine {
    pub fn execute(
        &self,
        incident_id: Id,
        action_type: ContainmentAction,
        target: String,
    ) -> ContainmentActionRecord {
        ContainmentActionRecord {
            id: Id::new(),
            incident_id,
            action_type,
            target,
            status: "executed".into(),
            executed_at: Utc::now(),
            rolled_back: false,
        }
    }

    pub fn rollback(&self, action: &mut ContainmentActionRecord) {
        action.rolled_back = true;
    }
}
```

### The Rollback That Almost Cost Us

At 05:15 EST, Langdon called. "The IP block is catching legitimate CGA partner traffic. Three field offices in Tunisia can't reach the API at all."

I pulled up the block rule. The /24 was too broad -- it was catching CGA's Tunisian partner ISP that shares part of the same address space as FLB's upstream provider. This is the nightmare scenario: containment causing collateral damage to the very humanitarian operations you're trying to protect.

```bash
# Rollback the overly broad IP block
curl -s -X POST http://localhost:3000/incident/contain/01950b1a-0020-7000-8000-000000000020/rollback \
  -H "Authorization: Bearer $TOKEN" | jq .
```

```json
{
  "rolled_back": true
}
```

```bash
# Apply surgical blocks -- specific IPs only
curl -s -X POST http://localhost:3000/incident/contain \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "incident_id": "01950b1a-0001-7000-8000-000000000001",
    "action_type": "block_ip_specific",
    "target": "7 specific attack source IPs identified in credential-stuffing logs (91.234.xx.15, 91.234.xx.42, 91.234.xx.108 from FLB + 4 VPS IPs). /32 blocks only. Tunisian partner traffic restored."
  }' | jq .
```

```bash
curl -s -X POST http://localhost:3000/incident/incidents/01950b1a-0001-7000-8000-000000000001/timeline \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "event_type": "containment_rollback",
    "description": "Rolled back /24 network block -- collateral impact on CGA Tunisian partner offices. Three field offices lost API access for 18 minutes (04:57-05:15 EST). Replaced with /32 blocks on 7 specific attack source IPs. Partner traffic restored at 05:17 EST. No impact to child tracking restoration efforts.",
    "actor": "R. Vasquez"
  }' | jq .
```

Eighteen minutes. Three field offices in Tunisia went dark for eighteen minutes because I was too aggressive with a network block. Those offices are tracking children. Actual children in transit camps.

This is why rollback exists. This is why you document everything. And this is why the incident commander doesn't do technical work -- I should have had Vasquez review the block scope before I executed it. I was too tired, too fast, too afraid of what happens if we don't contain quickly enough.

### STARLIGHT Track: Parallel Containment

While the CGA containment was happening, I advanced STARLIGHT to containment too. But "containment" in STARLIGHT means something different -- it means containing the intelligence, not containing an attack.

```bash
curl -s -X POST http://localhost:3000/incident/incidents/01950b1a-0001-7000-8000-000000000002/advance \
  -H "Authorization: Bearer $TOKEN" | jq .
```

```json
{
  "advanced": true,
  "phase": "containment"
}
```

```bash
curl -s -X POST http://localhost:3000/incident/incidents/01950b1a-0001-7000-8000-000000000002/timeline \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "event_type": "containment",
    "description": "STARLIGHT containment actions: (1) Evidence snapshot of all three stream sources preserved at 03:25 EST with BLAKE3+SHA256 dual hash. (2) FLB network mirror remains operational -- CGA containment blocks applied at CGA perimeter, not at FLB upstream. Intelligence feed preserved. (3) SIGINT relay collection rate increased 4x per SOAR playbook approval at 04:00 EST. (4) Financial monitoring continues -- watching for UAE transit account activation. (5) Clara last ping: 08:25 CET from tower 13-Joliette. No subsequent pings -- may have powered down to avoid detection during heightened activity.",
    "actor": "incident_commander"
  }' | jq .
```

---

## 20.7 -- Evidence Collection (Both Tracks)

### CGA Track: Forensic Preservation

```bash
curl -s -X POST http://localhost:3000/incident/incidents/01950b1a-0001-7000-8000-000000000001/timeline \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "event_type": "evidence_collection",
    "description": "CGA API gateway logs preserved: 47,231 credential-stuffing attempts from 04:02-04:14 EST. 1,247 successful authentications identified. Attack payload analysis: automated tool using combo-list format, 3 concurrent threads per source IP, 0.2s delay between attempts (designed to stay below standard rate limiting). Credential source appears to be a 2025 third-party breach of a CGA partner organization. SHA-256 hash of log archive: e7f2a3b4c5d6... BLAKE3: 8a9b0c1d2e3f...",
    "actor": "L. Park"
  }' | jq .
```

```bash
curl -s -X POST http://localhost:3000/incident/incidents/01950b1a-0001-7000-8000-000000000001/timeline \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "event_type": "evidence_collection",
    "description": "Child tracking database integrity analysis: 340 minor records examined. 47 records show modification during attack window (04:11-04:14 EST). Modifications include: status changes from tracked to unknown (31 records), transport schedule deletions (12 records), facility assignment changes (4 records). All modifications originated from compromised credential sessions. No records deleted -- data corruption is reversible from backup. Pre-attack backup verified: 03:00 EST automated snapshot, SHA-256 confirmed.",
    "actor": "T. Okafor"
  }' | jq .
```

47 child records modified. 31 changed from "tracked" to "unknown." That's not random damage. That's targeted. Someone told the attack tool which records to modify. Someone inside the trafficking network who knows which children PHANTOM MERCY plans to move.

### STARLIGHT Track: The Evidence That Matters for Court

```bash
curl -s -X POST http://localhost:3000/incident/incidents/01950b1a-0001-7000-8000-000000000002/timeline \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "event_type": "evidence_collection",
    "description": "STARLIGHT legal evidence package delivered to Marchetti at 06:00 EST. Contents: (1) Financial transaction records -- 4 wire transfers totaling $36,500 with beneficiary analysis. (2) FLB network metadata -- Tor circuit, encrypted VoIP to Libya, 75MB TLS burst. (3) Clara signal logs -- 274 ping events over 11 days, including distress double-ping. (4) Cross-source convergence analysis -- 38-minute window, 3/3 correlation. (5) CGA attack correlation -- attack launched 75 minutes after financial precursor, 40 minutes after Clara distress signal. All items dual-hashed BLAKE3+SHA256. Chain of custody automated via SOAR engine. French magistrate review expected by 12:00 EST.",
    "actor": "incident_commander"
  }' | jq .
```

Every piece of evidence, dual-hashed. Every chain of custody entry automated. Because when this gets to court -- and Marchetti insists it will get to court -- the defense will attack the evidence chain. They'll argue the digital evidence was tampered with. They'll argue the streaming data was selectively captured. They'll argue the correlation was post-hoc rationalization.

The hashes prove they're wrong. The timestamps prove the sequence. The annotations prove we understood what we were seeing in real time.

---

## 20.8 -- Phase 4: Eradication

### CGA Track: Cleaning the Infrastructure

```bash
curl -s -X POST http://localhost:3000/incident/incidents/01950b1a-0001-7000-8000-000000000001/advance \
  -H "Authorization: Bearer $TOKEN" | jq .
```

```json
{
  "advanced": true,
  "phase": "eradication"
}
```

```bash
curl -s -X POST http://localhost:3000/incident/incidents/01950b1a-0001-7000-8000-000000000001/timeline \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "event_type": "eradication",
    "description": "Eradication Phase 1: All 1,247 compromised credentials force-reset. Active sessions terminated. MFA enforcement enabled across entire CGA API gateway -- previously optional, now mandatory. Rate limiting tightened: max 5 auth attempts per IP per minute (was 50). GeoIP blocking enabled for source countries not associated with CGA operations.",
    "actor": "L. Park"
  }' | jq .
```

```bash
curl -s -X POST http://localhost:3000/incident/incidents/01950b1a-0001-7000-8000-000000000001/timeline \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "event_type": "eradication",
    "description": "Eradication Phase 2: Child tracking database restored from 03:00 EST backup. 47 corrupted records reverted to pre-attack state. Integrity check: all 340 minor records verified against backup. Transport schedules reconstructed from field office confirmations. Database write access restricted to authenticated sessions with MFA + role-based access control.",
    "actor": "T. Okafor"
  }' | jq .
```

```bash
curl -s -X POST http://localhost:3000/incident/incidents/01950b1a-0001-7000-8000-000000000001/timeline \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "event_type": "eradication",
    "description": "Eradication Phase 3: Full credential audit across CGA platform. 4,200 accounts reviewed. 847 accounts found with passwords from the same 2025 partner breach (password reuse detection via hash comparison). All 847 force-reset with notification. 12 orphaned service accounts disabled. API key rotation completed for all 23 partner integrations.",
    "actor": "R. Vasquez"
  }' | jq .
```

### STARLIGHT Track: Eradication Means Something Different

For STARLIGHT, eradication isn't about cleaning infected systems. It's about dismantling the trafficking network's digital infrastructure -- but carefully, on Marchetti's timeline, not ours.

```bash
curl -s -X POST http://localhost:3000/incident/incidents/01950b1a-0001-7000-8000-000000000002/advance \
  -H "Authorization: Bearer $TOKEN" | jq .
```

```json
{
  "advanced": true,
  "phase": "eradication"
}
```

```bash
curl -s -X POST http://localhost:3000/incident/incidents/01950b1a-0001-7000-8000-000000000002/timeline \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "event_type": "eradication",
    "description": "STARLIGHT eradication planning (NOT yet executed -- pending magistrate authorization and rescue operation completion). Targets identified: (1) FLB upstream network infrastructure -- 3 servers, 2 Tor relays. (2) Financial shell network -- 6 accounts across 3 jurisdictions, freeze orders drafted for Malta FSA, Cyprus CySEC, UAE CBUAE. (3) Dark web marketplace presence -- hosting infrastructure identified (see Chapter 22 analysis). (4) PHANTOM MERCY operational communications -- VoIP servers, Tor hidden services. Eradication to be executed SIMULTANEOUSLY with physical rescue operation to prevent PHANTOM MERCY from alerting other cells.",
    "actor": "Marchetti"
  }' | jq .
```

Marchetti's principle: you don't dismantle the network until you've rescued the assets and arrested the operators. If we take down their infrastructure too early, they scatter. Clara disappears. The children disappear. The evidence disappears.

So we wait. We watch. We build the legal case. And we prepare to strike everything at once.

---

## 20.9 -- Phase 5: Recovery

### CGA Track: Bringing Systems Back

```bash
curl -s -X POST http://localhost:3000/incident/incidents/01950b1a-0001-7000-8000-000000000001/advance \
  -H "Authorization: Bearer $TOKEN" | jq .
```

```json
{
  "advanced": true,
  "phase": "recovery"
}
```

```bash
curl -s -X POST http://localhost:3000/incident/incidents/01950b1a-0001-7000-8000-000000000001/timeline \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "event_type": "recovery_validation",
    "description": "ADAPT VALIDATE cycle completed for CGA platform. Child tracking system restored and verified -- all 340 minors accounted for across 7 facilities. Paper-based manual tracking confirmed 100% match with restored digital records. Transport scheduling operational -- 3 active transits resumed with real-time tracking. API gateway hardened: MFA mandatory, rate limiting enforced, GeoIP filtering active. CGA SOC monitoring re-established with Playseat streaming integration for anomaly detection. Recovery time: 6 hours 12 minutes from detection to full restoration.",
    "actor": "incident_commander"
  }' | jq .
```

Six hours and twelve minutes. Not great. Not terrible. The child tracking system was offline for the most critical window -- the early morning hours when PHANTOM MERCY wanted the blindspot. But the manual tracking protocol caught the gap. All 340 children accounted for.

But here's what keeps me up at night: those 47 modified records targeted specific children. Someone in the trafficking network knew which children they planned to extract. The fact that we restored the records doesn't mean the plan is cancelled. It means they'll try a different way.

```bash
curl -s -X POST http://localhost:3000/incident/incidents/01950b1a-0001-7000-8000-000000000001/timeline \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "event_type": "recovery",
    "description": "Enhanced monitoring deployed for 47 specifically targeted minor records. Real-time alerts configured for any status change, facility transfer, or transport assignment modification. CGA field offices briefed on heightened risk for these individuals. UNHCR liaison notified. Physical security increased at 3 facilities housing the most targeted minors: Tunis-Central, Lampedusa-Processing, Catania-Transit.",
    "actor": "T. Okafor"
  }' | jq .
```

### STARLIGHT Track: Recovery Means Rescue

```bash
curl -s -X POST http://localhost:3000/incident/incidents/01950b1a-0001-7000-8000-000000000002/advance \
  -H "Authorization: Bearer $TOKEN" | jq .
```

```json
{
  "advanced": true,
  "phase": "recovery"
}
```

```bash
curl -s -X POST http://localhost:3000/incident/incidents/01950b1a-0001-7000-8000-000000000002/timeline \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "event_type": "recovery",
    "description": "STARLIGHT recovery status (12:00 EST update): French magistrate has reviewed the evidence package. Authorization for operational phase GRANTED at 11:47 EST. Marchetti confirms DGSE tactical team briefed on Joliette warehouse location. UAE transit accounts still dormant -- window holding. Clara last confirmed ping: 12:15 CET from tower 13-Joliette, signal strength -91 dBm (consistent -- she has not been moved). Marchetti timeline: rescue operation within 18-24 hours, coordinated with simultaneous infrastructure takedown across 3 jurisdictions. Legal: freeze orders filed with Malta FSA, Cyprus CySEC. UAE CBUAE coordination via Interpol red notice channel.",
    "actor": "incident_commander"
  }' | jq .
```

The magistrate said yes. The evidence package -- built from streaming data, dual-hashed, chain-of-custody automated -- was enough. The legal foundation is solid.

Clara's 12:15 CET ping from the same tower confirmed she hasn't been moved. The warehouse in Joliette. She's still there.

Marchetti's team is moving. The DGSE tactical unit is briefed. In 18 to 24 hours, if everything holds, they go in.

---

## 20.10 -- Phase 6: Lessons Learned

### CGA Track: The Post-Mortem

```bash
curl -s -X POST http://localhost:3000/incident/incidents/01950b1a-0001-7000-8000-000000000001/advance \
  -H "Authorization: Bearer $TOKEN" | jq .
```

```json
{
  "advanced": true,
  "phase": "lessons_learned"
}
```

```bash
curl -s -X POST http://localhost:3000/incident/incidents/01950b1a-0001-7000-8000-000000000001/lessons \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "what_happened": "PHANTOM MERCY trafficking network launched a coordinated credential-stuffing attack against Children Global Alliance humanitarian logistics platform. The attack used 47,231 credential pairs from a 2025 third-party partner breach. 1,247 valid credentials were exploited to access the child tracking system. 47 specific minor records were deliberately modified to blind tracking of children targeted for trafficking. The attack was a cover operation designed to create a tracking blindspot for a physical trafficking movement.",
    "root_cause": "Three compounding failures: (1) CGA API gateway did not enforce MFA -- authentication was single-factor for all API access. (2) CGA did not monitor for credential reuse from known breaches -- the credentials came from a partner breach 9 months earlier. (3) Rate limiting on the API gateway was set to 50 attempts per IP per minute -- far too high to prevent automated credential stuffing. Additionally, CGA had no anomaly detection on child record modifications -- the 47 targeted changes happened in 3 minutes without triggering any alert.",
    "what_worked": "Detection via Playseat streaming analytics identified the attack within 12 minutes. Manual tracking fallback protocol preserved accountability for all 340 minors. Database restoration from verified backup recovered all corrupted records within 4 hours. Evidence collection was automated via SOAR playbook -- forensic integrity maintained throughout. Cross-timezone coordination between DC ops and CGA field offices was effective.",
    "improvements": "Mandatory MFA for all CGA API access. Credential monitoring against breach databases for all partner organizations. Rate limiting reduction to 5 attempts per IP per minute. Real-time anomaly detection on child record modifications. Pre-positioned manual tracking kits at all transit facilities. Quarterly tabletop exercises for humanitarian infrastructure attack scenarios."
  }' | jq .
```

```json
{
  "id": "01950b1a-0099-7000-8000-000000000099",
  "incident_id": "01950b1a-0001-7000-8000-000000000001",
  "root_cause": "Three compounding failures...",
  "improvements": "Mandatory MFA for all CGA API access...",
  "action_items": [
    "Investigate: Three compounding failures...",
    "Implement: Mandatory MFA for all CGA API access..."
  ],
  "created_at": "2026-02-18T18:00:00Z"
}
```

The lessons manager auto-generates action items:

```rust
// crates/svc-incident/src/lessons.rs

pub fn create(
    &self,
    what_happened: String,
    root_cause: String,
    what_worked: String,
    improvements: String,
) -> LessonsLearned {
    let action_items: Vec<String> = improvements
        .split(". ")
        .map(|s| s.trim().to_string())
        .filter(|s| !s.is_empty())
        .collect();

    LessonsLearned {
        id: Id::new(),
        what_happened,
        root_cause,
        what_worked,
        improvements,
        action_items,
    }
}
```

### STARLIGHT Track: Lessons Learned Will Come Later

STARLIGHT doesn't get a lessons learned yet. You can't write a post-mortem on an operation that's still running. The state machine sits at recovery phase. It'll stay there until Clara is safe, the arrests are made, and the infrastructure is dismantled.

```bash
# STARLIGHT remains in recovery phase
curl -s -X POST http://localhost:3000/incident/incidents/01950b1a-0001-7000-8000-000000000002/advance \
  -H "Authorization: Bearer $TOKEN" | jq .
```

```json
{
  "advanced": true,
  "phase": "lessons_learned"
}
```

I advanced it anyway. Because the NIST state machine requires it, and because the lessons I'm learning right now -- at hour 42 with no sleep, running two incidents, trying to keep a woman alive through streaming data and SQL queries -- those lessons need to be recorded while they're raw.

```bash
curl -s -X POST http://localhost:3000/incident/incidents/01950b1a-0001-7000-8000-000000000002/lessons \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "what_happened": "PRELIMINARY -- operation ongoing. PHANTOM MERCY trafficking network activated movement operation. Three-source convergence detected via streaming analytics: financial precursors, network operational activity, embedded asset distress signal. Simultaneously launched cyber attack against humanitarian infrastructure to create tracking blindspot for physical trafficking movement. Dual-track incident response maintained separation between official CGA response and compartmented rescue operation.",
    "root_cause": "PHANTOM MERCY has deeply penetrated humanitarian infrastructure. The aid organization (Fondation Lumiere Bleue) is a front. The trafficking network has insider knowledge of which children are targeted and which database records to modify. Root cause of the broader situation: inadequate vetting of humanitarian organizations, insufficient monitoring of aid infrastructure for dual-use by criminal networks.",
    "what_worked": "Streaming analytics with cross-source correlation detected the convergence 40 minutes before the cyber attack launched. Clara distress signal provided advance warning. Automated evidence preservation via SOAR maintained legal admissibility. Dual-track incident management maintained operational separation. Financial pattern detection provided 24-48 hour early warning of physical movement.",
    "improvements": "PENDING OPERATION COMPLETION. Interim: (1) streaming pipeline proves essential for multi-source intelligence fusion. (2) Human-in-the-loop decisions on containment scope prevented intelligence loss. (3) Evidence automation is non-negotiable for legal proceedings. (4) Sleep deprivation impairs containment decisions -- the /24 block rollback was avoidable."
  }' | jq .
```

That last line. The /24 block. That was me. Sleep-deprived, scared, making a containment decision that was too broad because I was thinking about Clara instead of thinking about CIDR notation. The system recorded it. The rollback is documented. The 18-minute gap in Tunisian field office connectivity is in the timeline.

That's what accountability looks like.

---

## 20.11 -- The Complete Dual Timeline

```bash
curl -s http://localhost:3000/incident/incidents/01950b1a-0001-7000-8000-000000000001/timeline \
  -H "Authorization: Bearer $TOKEN" | jq '.[] | {occurred_at, event_type, description}' | head -80
```

**CGA Track:**
```
04:17 UTC  declaration            CGA incident declared
04:25 UTC  team_assembly          Bridge call: Langdon, Okafor, Vasquez, Park
04:28 UTC  communication          Comm plan: Bridge #IR-20260218-CGA
04:35 UTC  phase_change           Phase: triage
04:40 UTC  assessment             47,231 credential-stuffing attempts...
04:55 UTC  phase_change           Phase: containment
04:57 UTC  containment            IP block: FLB network + 3 VPS IPs
05:02 UTC  containment            Credential revocation: 1,247 accounts
05:08 UTC  containment            Database isolation: child tracking
05:12 UTC  containment            Manual tracking activated: 7 facilities
05:15 UTC  containment_rollback   Rolled back /24 block -- Tunisian offices
05:17 UTC  containment            Surgical /32 blocks: 7 specific IPs
06:30 UTC  evidence_collection    API gateway logs: 47,231 attempts...
07:00 UTC  evidence_collection    Child tracking DB: 47 modified records...
08:00 UTC  phase_change           Phase: eradication
08:30 UTC  eradication            1,247 credentials reset, MFA enforced
09:00 UTC  eradication            Database restored from 03:00 backup
09:30 UTC  eradication            Full credential audit: 847 more resets
10:00 UTC  phase_change           Phase: recovery
10:17 UTC  recovery_validation    ADAPT VALIDATE: all 340 minors confirmed
10:30 UTC  recovery               Enhanced monitoring: 47 targeted minors
12:00 UTC  phase_change           Phase: lessons_learned
13:00 UTC  lessons_learned        Post-incident review documented
```

**STARLIGHT Track:**
```
03:25 UTC  CONVERGENCE alert      3/3 sources converged in 38 minutes
03:26 UTC  declaration            STARLIGHT incident declared
03:31 UTC  team_assembly          Marchetti, DGSE, legal, self
04:00 UTC  phase_change           Phase: triage
04:05 UTC  assessment             CGA attack is cover operation...
04:30 UTC  phase_change           Phase: containment
04:35 UTC  containment            Intelligence preserved, monitoring increased
06:00 UTC  evidence_collection    Legal package to Marchetti
09:00 UTC  phase_change           Phase: eradication
09:05 UTC  eradication            Targets identified, execution pending
10:00 UTC  phase_change           Phase: recovery
11:47 UTC  recovery               MAGISTRATE AUTHORIZATION GRANTED
12:15 UTC  recovery               Clara ping confirmed: Joliette, not moved
```

Two timelines. One enemy. Twenty hours of parallel operations documented in forensic detail.

---

## 20.12 -- Incident Metrics

```bash
curl -s http://localhost:3000/incident/stats \
  -H "Authorization: Bearer $TOKEN" | jq .
```

```json
{
  "active_incidents": 2,
  "playbooks": 5,
  "containment_actions": 8,
  "mean_time_to_contain_mins": 38
}
```

```sql
-- Containment actions by type for both incidents
SELECT
    action_type,
    COUNT(*) AS total,
    SUM(CASE WHEN rolled_back THEN 1 ELSE 0 END) AS rollbacks,
    ROUND(100.0 * SUM(CASE WHEN rolled_back THEN 1 ELSE 0 END)
        / COUNT(*), 1) AS rollback_pct
FROM containment_actions
WHERE incident_id IN (
    '01950b1a-0001-7000-8000-000000000001',
    '01950b1a-0001-7000-8000-000000000002'
)
GROUP BY action_type
ORDER BY total DESC;
```

```
 action_type          | total | rollbacks | rollback_pct
----------------------+-------+-----------+--------------
 block_ip_range       |     1 |         1 |        100.0
 block_ip_specific    |     1 |         0 |          0.0
 credential_revocation|     1 |         0 |          0.0
 database_isolation   |     1 |         0 |          0.0
 manual_fallback      |     1 |         0 |          0.0
```

One rollback out of five containment actions. 20% rollback rate. Higher than my career average of 9.5%. Sleep deprivation.

---

## 20.13 -- What I Learned Running Two Incidents

After this day -- this impossible, exhausting, terrifying day -- here is what I know:

**1. The incident commander does not do technical work.** I said this before and I violated it. I wrote the /24 block myself instead of having Vasquez scope it. The rollback cost 18 minutes of field office connectivity. Delegate. Even when you're scared. Especially when you're scared.

**2. Compartmentation requires discipline, not cleverness.** The CGA team never knew about STARLIGHT. The STARLIGHT team knew about CGA but treated it as context. The separation was maintained through discipline -- separate channels, separate bridges, separate evidence stores -- not through clever technical controls.

**3. Document everything in real time.** Both timelines were complete because I documented as events happened, not after. The CGA timeline is the legal shield. The STARLIGHT timeline is the prosecution evidence. Both would collapse if I'd tried to reconstruct them from memory 12 hours later.

**4. Containment will cause collateral damage.** Budget for it. The manual tracking fallback for 340 children was planned. The Tunisian office outage was not. Have rollback capability for every containment action, and have a human review the scope before execution.

**5. Marchetti's principle is right: don't dismantle until you've rescued.** Every instinct in my body wanted to take down FLB's infrastructure the moment I saw the CGA attack. If I had, we'd have lost the network mirror that's tracking PHANTOM MERCY's communications. We'd have lost Clara's last lifeline of intelligence. Patience isn't passive. Patience is strategic.

**6. The system has to be smarter than you at 3 AM.** The automated evidence collection, the dual-hashing, the chain of custody logging, the SOAR playbook triggers -- all of that worked because I built it when I was rested and thinking clearly. At 3 AM, running on adrenaline and fear, I could not have done any of it manually without errors.

**7. Sleep deprivation is a security vulnerability.** The /24 block, the moment of forgetting to drink coffee, the 60 seconds of staring at the distress signal before I acknowledged it because my brain couldn't process what it meant -- all of that was fatigue. After this operation, I'm instituting mandatory 8-hour stand-down for any IC who's been on shift for more than 16 hours. Including myself.

**8. Love is a variable the incident response framework doesn't account for.** NIST 800-61 doesn't have a phase for "the person you love is being held by the people you're fighting." There's no playbook step for separating your professional analysis from the fact that every ping from tower 13-Joliette makes your chest tight. I ran both operations by the book. But the book doesn't know about Clara.

Marchetti called at 14:00 EST. His voice was different. Steady. Certain.

"We go tomorrow. 04:00 CET. Are you ready?"

I looked at the streaming dashboard. Three sources. All green. Clara's last ping: 17:42 CET, tower 13-Joliette, signal strength -93 dBm. Still there. Still alive. Still waiting.

"I'm ready."

---

*Next: Chapter 21 -- The Aid Network's Skeleton: How Critical Infrastructure Became a Weapon*

---

`© 2026 Playseat — All Rights Reserved | Defensive Intelligence Through ADAPT`
