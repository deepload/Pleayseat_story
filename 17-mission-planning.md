# Chapter 17: Mission Planning -- Operation STARLIGHT

**Playseat Advanced Field Manual -- Book 2**

---

> "A rescue without a plan is a second hostage situation. A plan without
> intelligence is a fantasy. What we need is both -- and we need them in
> forty-eight hours."

---

## 17.1 -- Marchetti

**2026-02-06, 11:00 UTC. Building 9, Conference Room Alpha. Secure SCIF.**

He arrived without announcement. No email. No phone call. Just a knock on the
SCIF door at 11:00 sharp, and there was Jean-Luc Marchetti, DGSE Directorate
of Intelligence, standing in the hallway with a leather briefcase and the kind
of thousand-yard stare you get from twenty years of running agents in places
that don't appear on official maps.

I'd sent the AI-generated PHANTOM MERCY briefing through the Mesh twelve hours
earlier. I'd expected a response in a few days. Instead, I got Marchetti in
person. Which told me everything I needed to know about how seriously Paris was
taking this.

"You found her signal," he said. Not a question.

"Intermittent. Fading. But yes. Three locations in Marseille. Primary holding
site near the Vieux-Port."

He set the briefcase down. Opened it. Inside: a tablet, a Cryptophone 500
identical to Clara's, and a dossier stamped CONFIDENTIEL DEFENSE.

"Clara is one of ours," he said. "Deep cover. Eighteen months in the PHANTOM
MERCY investigation. She went dark on January 15th. We've had zero contact
since." His jaw tightened. "Until your Mesh report."

"What's in the dossier?"

"Everything we have on PHANTOM MERCY from the French side. Financial
intercepts. Port authority informants. A partial organizational chart." He
paused. "And a mole warning."

My blood went cold. "What kind of mole warning?"

"Someone inside our liaison network has been feeding PHANTOM MERCY operational
data. We don't know who. We don't know how long. But Clara suspected it before
she went dark -- her last encrypted message to her handler mentioned that the
network seemed to know her movements before she made them."

I sat down heavily. A mole. That changed everything. It meant anyone we brought
into the operation was a potential leak. It meant every communication channel
was suspect. It meant the rescue plan had to be built inside a sealed room
with a sealed team, using a platform that nobody outside this building could
access.

It meant Playseat's mission workspace wasn't just a nice-to-have. It was the
only tool we could trust.

---

## 17.2 -- The Collaboration Data Model

I opened Playseat and navigated to the collaboration module. Marchetti watched
over my shoulder as I explained the architecture.

The collaboration system uses five core tables:

```sql
-- Mission boards: the investigation workspace
CREATE TABLE IF NOT EXISTS mission_boards (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name        TEXT NOT NULL,
    description TEXT,
    status      TEXT NOT NULL DEFAULT 'active',
    created_by  UUID,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Board members: who has access
CREATE TABLE IF NOT EXISTS mission_board_members (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    board_id    UUID NOT NULL REFERENCES mission_boards(id),
    user_id     UUID NOT NULL,
    role        TEXT NOT NULL DEFAULT 'analyst',
    joined_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(board_id, user_id)
);

-- Pins: evidence, IOCs, notes attached to the board
CREATE TABLE IF NOT EXISTS mission_pins (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    board_id    UUID NOT NULL REFERENCES mission_boards(id),
    entity_id   UUID,
    pin_type    TEXT NOT NULL DEFAULT 'note',
    title       TEXT NOT NULL,
    content     TEXT,
    position_x  INTEGER NOT NULL DEFAULT 0,
    position_y  INTEGER NOT NULL DEFAULT 0,
    color       TEXT NOT NULL DEFAULT '#22c55e',
    created_by  UUID,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Hypotheses: structured analytical assessments
CREATE TABLE IF NOT EXISTS mission_hypotheses (
    id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    board_id          UUID NOT NULL REFERENCES mission_boards(id),
    title             TEXT NOT NULL,
    description       TEXT,
    status            TEXT NOT NULL DEFAULT 'proposed',
    confidence        DOUBLE PRECISION NOT NULL DEFAULT 0.5,
    evidence_for      JSONB NOT NULL DEFAULT '[]',
    evidence_against  JSONB NOT NULL DEFAULT '[]',
    created_by        UUID,
    created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at        TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Annotations: comments and analysis on pins
CREATE TABLE IF NOT EXISTS mission_annotations (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    board_id        UUID NOT NULL REFERENCES mission_boards(id),
    pin_id          UUID REFERENCES mission_pins(id),
    content         TEXT NOT NULL,
    annotation_type TEXT NOT NULL DEFAULT 'comment',
    created_by      UUID,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

And the unified timeline:

```sql
-- Unified timeline: all events from all modules
CREATE TABLE IF NOT EXISTS unified_timeline_events (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_type      TEXT NOT NULL,
    source_module   TEXT NOT NULL,
    source_id       UUID,
    title           TEXT NOT NULL,
    description     TEXT,
    severity        TEXT NOT NULL DEFAULT 'info',
    metadata        JSONB NOT NULL DEFAULT '{}',
    occurred_at     TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

"Everything on this board stays on this hardware," I told Marchetti. "No cloud.
No sync. No Mesh relay for operational details. The mole can't leak what they
can't see."

He nodded. "Create the board."

---

## 17.3 -- Creating Operation STARLIGHT

```bash
curl -s -X POST http://localhost:3000/api/v1/collab/workspaces \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Op STARLIGHT",
    "description": "CLASSIFICATION: TOP SECRET // COMPARTMENTED. Rescue operation for DGSE Officer Clara Dubois. Held by PHANTOM MERCY trafficking network at one of three identified locations in Marseille, France. Operational window: 48 hours. MOLE WARNING IN EFFECT -- restrict access to named personnel only."
  }' | jq .
```

```json
{
  "id": "01956a00-aa01-7000-8000-000000000001",
  "name": "Op STARLIGHT",
  "description": "CLASSIFICATION: TOP SECRET // COMPARTMENTED...",
  "status": "active",
  "created_by": "01945000-0000-7000-8000-000000000001",
  "created_at": "2026-02-06T11:15:00Z",
  "updated_at": "2026-02-06T11:15:00Z"
}
```

The system auto-added me as owner:

```rust
// Auto-join the creator as owner
let member_id = Uuid::now_v7();
sqlx::query(
    "INSERT INTO mission_board_members (id, board_id, user_id, role, joined_at) \
     VALUES ($1, $2, $3, 'owner', $4) ON CONFLICT (board_id, user_id) DO NOTHING",
)
.bind(member_id)
.bind(id)
.bind(user_id)
.bind(now)
.execute(&state.db)
.await?;
```

Operation STARLIGHT. I'd picked the name at 04:00 that morning, half-asleep,
staring at Clara's notebook. Page 83: she'd drawn a five-pointed star next to
a note about the Marseille port authority's night-shift schedule. Below it,
in English (she sometimes switched languages when thinking fast): *"The light
comes at night."*

---

## 17.4 -- Assembling the Team (Trust No One Except These People)

The mole warning meant the team had to be small. Brutally small. Three people
besides myself:

- **Marchetti** -- DGSE liaison, Clara's operational chain
- **Dr. Kira Vasquez** -- our forensic analyst, twelve years with the platform
- **Yusuf al-Rashid** -- SIGINT specialist, ex-NSA, now contractor

Nobody else. No management chain. No inter-agency coordination. If the mole
was in the liaison network, then the fewer people who knew about STARLIGHT,
the fewer ways it could leak.

```bash
BOARD="01956a00-aa01-7000-8000-000000000001"

# Marchetti joins
curl -s -X POST http://localhost:3000/api/v1/collab/workspaces/$BOARD/join \
  -H "Authorization: Bearer $MARCHETTI_TOKEN" | jq .
```

```json
{
  "joined": true,
  "board_id": "01956a00-aa01-7000-8000-000000000001",
  "user_id": "01945000-0000-7000-8000-000000000002"
}
```

```bash
# Vasquez joins
curl -s -X POST http://localhost:3000/api/v1/collab/workspaces/$BOARD/join \
  -H "Authorization: Bearer $VASQUEZ_TOKEN" | jq .

# Al-Rashid joins
curl -s -X POST http://localhost:3000/api/v1/collab/workspaces/$BOARD/join \
  -H "Authorization: Bearer $ALRASHID_TOKEN" | jq .
```

Verify the team:

```bash
curl -s http://localhost:3000/api/v1/collab/workspaces/$BOARD/members \
  -H "Authorization: Bearer $TOKEN" | jq '.[] | {user_id, role, joined_at}'
```

```json
{"user_id": "01945000-0000-7000-8000-000000000001", "role": "owner",   "joined_at": "2026-02-06T11:15:00Z"}
{"user_id": "01945000-0000-7000-8000-000000000002", "role": "analyst", "joined_at": "2026-02-06T11:20:00Z"}
{"user_id": "01945000-0000-7000-8000-000000000003", "role": "analyst", "joined_at": "2026-02-06T11:22:00Z"}
{"user_id": "01945000-0000-7000-8000-000000000004", "role": "analyst", "joined_at": "2026-02-06T11:25:00Z"}
```

The workspace detail with member count:

```bash
curl -s http://localhost:3000/api/v1/collab/workspaces/$BOARD \
  -H "Authorization: Bearer $TOKEN" | jq .
```

```json
{
  "id": "01956a00-aa01-7000-8000-000000000001",
  "name": "Op STARLIGHT",
  "description": "CLASSIFICATION: TOP SECRET // COMPARTMENTED...",
  "status": "active",
  "created_by": "01945000-0000-7000-8000-000000000001",
  "created_at": "2026-02-06T11:15:00Z",
  "updated_at": "2026-02-06T11:15:00Z",
  "member_count": 4
}
```

Using the serde flatten pattern for the computed field:

```rust
#[derive(Serialize)]
struct WorkspaceDetail {
    #[serde(flatten)]
    board: BoardRow,
    member_count: i64,
}
```

Four people. One board. One objective: bring Clara home.

---

## 17.5 -- Pinning the Intelligence (Building the War Board)

We spent the next three hours pinning everything we had to the STARLIGHT board.
Every GEOINT finding. Every AI pipeline result. Every piece of DGSE intelligence
from Marchetti's dossier.

First, the location pins:

```bash
# Pin PHANTOM-SITE-ALPHA (primary holding)
curl -s -X POST http://localhost:3000/api/v1/collab/workspaces/$BOARD/pins \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "entity_id": "01954a00-bb01-7000-8000-000000000001",
    "pin_type": "geo_target",
    "title": "ALPHA: Primary Holding Site (Vieux-Port, 2nd arr.)",
    "content": "43.2960, 5.3701. Clara Cryptophone signal detected intermittently. Last ping Feb 5 16:30 UTC. Signal weakening. Movement pattern: stationary 80% of observation period. One transfer to BRAVO Jan 30, returned Feb 2. GEOINT assessment: PRIMARY HOLDING LOCATION with high confidence (0.88).",
    "position_x": 100,
    "position_y": 100,
    "color": "#ef4444"
  }' | jq .
```

```json
{
  "id": "01956b00-bb01-7000-8000-000000000001",
  "board_id": "01956a00-aa01-7000-8000-000000000001",
  "entity_id": "01954a00-bb01-7000-8000-000000000001",
  "pin_type": "geo_target",
  "title": "ALPHA: Primary Holding Site (Vieux-Port, 2nd arr.)",
  "content": "43.2960, 5.3701. Clara Cryptophone signal detected...",
  "position_x": 100,
  "position_y": 100,
  "color": "#ef4444",
  "created_by": "01945000-0000-7000-8000-000000000001",
  "created_at": "2026-02-06T12:00:00Z"
}
```

```bash
# Pin PHANTOM-SITE-BRAVO (secondary)
curl -s -X POST http://localhost:3000/api/v1/collab/workspaces/$BOARD/pins \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "pin_type": "geo_target",
    "title": "BRAVO: Secondary Safe House (Castellane, 6th arr.)",
    "content": "43.2833, 5.3842. Lower burst frequency (23 events). Clara signal detected here Jan 30-Feb 2 only. Assessment: backup holding location, used during operational movements. 1.72 km from ALPHA.",
    "position_x": 100,
    "position_y": 250,
    "color": "#f59e0b"
  }'

# Pin PHANTOM-SITE-CHARLIE (operational hub)
curl -s -X POST http://localhost:3000/api/v1/collab/workspaces/$BOARD/pins \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "pin_type": "geo_target",
    "title": "CHARLIE: Operational Hub (L Estaque, 15th arr.)",
    "content": "43.3614, 5.3147. Highest burst frequency (89 events). Near port facilities. Assessment: PHANTOM MERCY operational command center. NOT a likely holding site but coordinates all movements including Clara transfers. 7.94 km from ALPHA.",
    "position_x": 100,
    "position_y": 400,
    "color": "#dc2626"
  }'
```

Then Marchetti pinned the DGSE intelligence:

```bash
# DGSE financial intelligence
curl -s -X POST http://localhost:3000/api/v1/collab/workspaces/$BOARD/pins \
  -H "Authorization: Bearer $MARCHETTI_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "pin_type": "intelligence",
    "title": "DGSE: Fondation Lumiere Financial Analysis",
    "content": "Fondation Lumiere registered 2019, Marseille. Director: nominally Marcel Fournier (clean record, possibly unwitting). Real control: unknown individual(s) using Cypriot holding structure. EUR 2.3M routed through foundation in past 12 months. TRACFIN flagged but investigation stalled due to political connections. Clara was investigating the Fournier link when she went dark.",
    "position_x": 300,
    "position_y": 100,
    "color": "#8b5cf6"
  }'

# DGSE organizational chart fragment
curl -s -X POST http://localhost:3000/api/v1/collab/workspaces/$BOARD/pins \
  -H "Authorization: Bearer $MARCHETTI_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "pin_type": "intelligence",
    "title": "DGSE: PHANTOM MERCY Org Chart (Partial)",
    "content": "Three tiers identified. Tier 1 (leadership): unknown, possibly outside France. Tier 2 (operations): 4-6 individuals in Marseille, controlling logistics, finance, and port access. Tier 3 (logistics): 10-15 drivers, warehouse workers, port employees. Clara estimated Tier 2 controls the holding sites. Tier 2 members likely present at CHARLIE during operations.",
    "position_x": 300,
    "position_y": 250,
    "color": "#8b5cf6"
  }'

# The mole warning
curl -s -X POST http://localhost:3000/api/v1/collab/workspaces/$BOARD/pins \
  -H "Authorization: Bearer $MARCHETTI_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "pin_type": "warning",
    "title": "MOLE WARNING: Liaison Network Compromised",
    "content": "Clara last encrypted message (Jan 14): Subject stated PHANTOM MERCY appeared to anticipate her surveillance positions. Assessment: information leak within DGSE liaison or partner agency coordination channel. OPSEC REQUIREMENT: all STARLIGHT operational details restricted to board members only. No external coordination until mole is identified or operation is complete.",
    "position_x": 300,
    "position_y": 400,
    "color": "#dc2626"
  }'
```

Vasquez added the evidence chain analysis:

```bash
# Evidence chain summary
curl -s -X POST http://localhost:3000/api/v1/collab/workspaces/$BOARD/pins \
  -H "Authorization: Bearer $VASQUEZ_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "pin_type": "evidence",
    "title": "Evidence Chain: Linking PHANTOM MERCY to Dubois Capture",
    "content": "Chain of evidence: (1) Clara files cargo manifest finding Jan 15. (2) Clara phone goes dark Jan 15 evening. (3) ALPHA satphone emissions begin Jan 18. (4) Clara Cryptophone intermittent pings begin Jan 22 at ALPHA location. (5) Timing correlation between CHARLIE signals, Clara movements, and Fondation Lumiere transfers established. BLAKE3 hash chain maintained for all evidence artifacts. Prosecution-grade custody.",
    "position_x": 500,
    "position_y": 100,
    "color": "#22c55e"
  }'
```

And al-Rashid pinned the SIGINT assessment:

```bash
# SIGINT operational assessment
curl -s -X POST http://localhost:3000/api/v1/collab/workspaces/$BOARD/pins \
  -H "Authorization: Bearer $ALRASHID_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "pin_type": "intelligence",
    "title": "SIGINT: Emission Pattern Analysis",
    "content": "CHARLIE emissions: Thuraya XT-Pro encrypted, 15-min burst protocol, consistent with pre-planned coordination. ALPHA emissions: same Thuraya model but different unit. ALPHA secondary signal (Clara Cryptophone): brief power-on events, 5-15 seconds duration, consistent with device being powered intermittently -- either by captor for verification or by Clara covertly. Signal strength declining: battery degradation or deliberate power conservation. Estimated battery life at current usage: 7-10 days.",
    "position_x": 500,
    "position_y": 250,
    "color": "#3b82f6"
  }'
```

Seven to ten days. That was our window. After that, the signal would die and
we'd lose our only electronic link to Clara's location.

Now the full board picture:

```bash
curl -s http://localhost:3000/api/v1/collab/workspaces/$BOARD/pins \
  -H "Authorization: Bearer $TOKEN" | jq '.[] | {title, pin_type, color, created_by}'
```

```json
{"title": "ALPHA: Primary Holding Site...", "pin_type": "geo_target", "color": "#ef4444", "created_by": "01945000-...001"}
{"title": "BRAVO: Secondary Safe House...", "pin_type": "geo_target", "color": "#f59e0b", "created_by": "01945000-...001"}
{"title": "CHARLIE: Operational Hub...", "pin_type": "geo_target", "color": "#dc2626", "created_by": "01945000-...001"}
{"title": "DGSE: Fondation Lumiere Financial Analysis", "pin_type": "intelligence", "color": "#8b5cf6", "created_by": "01945000-...002"}
{"title": "DGSE: PHANTOM MERCY Org Chart (Partial)", "pin_type": "intelligence", "color": "#8b5cf6", "created_by": "01945000-...002"}
{"title": "MOLE WARNING: Liaison Network Compromised", "pin_type": "warning", "color": "#dc2626", "created_by": "01945000-...002"}
{"title": "Evidence Chain: Linking PHANTOM MERCY...", "pin_type": "evidence", "color": "#22c55e", "created_by": "01945000-...003"}
{"title": "SIGINT: Emission Pattern Analysis", "pin_type": "intelligence", "color": "#3b82f6", "created_by": "01945000-...004"}
```

Eight pins. Four analysts. Four different intelligence disciplines. One target.

---

## 17.6 -- Hypothesis Management (Three Scenarios for Clara)

The heart of structured analysis. The Analysis of Competing Hypotheses
methodology requires you to articulate what you believe AND what would
disprove it. No shortcuts. No gut feelings dressed up as analysis.

Hypotheses follow a lifecycle:

```
proposed -> investigating -> confirmed
                          -> rejected
                          -> inconclusive
```

Each carries evidence_for and evidence_against in JSONB arrays.

I created three scenarios:

```bash
# Hypothesis 1: Clara held at ALPHA
curl -s -X POST http://localhost:3000/api/v1/collab/workspaces/$BOARD/hypotheses \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "H1: Clara held at ALPHA (Vieux-Port, 2nd arr.) -- PRIMARY",
    "description": "Clara is being held in a building within 200m of coordinates 43.2960, 5.3701. The Cryptophone signal intermittently detected at this location is hers. She is alive but captive, being held by PHANTOM MERCY Tier 2 operators.",
    "status": "investigating",
    "confidence": 0.75,
    "evidence_for": [
      "Cryptophone 500 emission signature matches DGSE-issue device",
      "Signal detected at ALPHA for 80% of observation period (14 days)",
      "Movement pattern consistent with captive: stationary with rare transfers",
      "GEOINT co-travel analysis shows ALPHA-CHARLIE coordination (12 events)",
      "Signal first appeared 3 days after Clara went dark (transit time from last known location)"
    ],
    "evidence_against": [
      "Could be a different Cryptophone 500 -- DGSE issues multiple units",
      "Signal is intermittent and weakening -- could be discarded device, not active use",
      "No voice intercept confirming Clara identity",
      "Vieux-Port area is residential/commercial -- unusual for a holding site"
    ]
  }' | jq .
```

```json
{
  "id": "01956c00-cc01-7000-8000-000000000001",
  "board_id": "01956a00-aa01-7000-8000-000000000001",
  "title": "H1: Clara held at ALPHA (Vieux-Port, 2nd arr.) -- PRIMARY",
  "status": "investigating",
  "confidence": 0.75,
  "evidence_for": ["Cryptophone 500 emission signature...", "..."],
  "evidence_against": ["Could be a different Cryptophone 500...", "..."],
  "created_by": "01945000-0000-7000-8000-000000000001",
  "created_at": "2026-02-06T14:00:00Z",
  "updated_at": "2026-02-06T14:00:00Z"
}
```

```bash
# Hypothesis 2: Clara held at BRAVO
curl -s -X POST http://localhost:3000/api/v1/collab/workspaces/$BOARD/hypotheses \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "H2: Clara held at BRAVO (Castellane, 6th arr.) -- SECONDARY",
    "description": "Clara was moved to BRAVO and remains there. The ALPHA signal is a decoy or discarded device. BRAVO is the actual long-term holding location.",
    "status": "proposed",
    "confidence": 0.15,
    "evidence_for": [
      "Clara signal was detected at BRAVO Jan 30 - Feb 2",
      "BRAVO has lower emission activity -- consistent with a quieter holding site",
      "Castellane has more residential buildings suitable for discrete captivity"
    ],
    "evidence_against": [
      "Most recent Cryptophone signal is at ALPHA, not BRAVO",
      "BRAVO emission pattern suggests secondary/backup role",
      "Only 3 days of detection at BRAVO vs 14 days at ALPHA",
      "Transfer pattern shows ALPHA to BRAVO to ALPHA -- BRAVO is transit"
    ]
  }'

# Hypothesis 3: Clara held at CHARLIE or already moved out
curl -s -X POST http://localhost:3000/api/v1/collab/workspaces/$BOARD/hypotheses \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "H3: Clara at CHARLIE or exfiltrated from Marseille -- WORST CASE",
    "description": "Clara has been moved to the CHARLIE operational hub near port facilities, or has already been moved out of Marseille entirely via port logistics. The Cryptophone signal at ALPHA is a discarded device or deliberate misdirection.",
    "status": "proposed",
    "confidence": 0.10,
    "evidence_for": [
      "CHARLIE is near port facilities with access to shipping containers",
      "PHANTOM MERCY uses humanitarian cargo as cover for transport",
      "If network detected the signal monitoring, they may have relocated her",
      "Signal weakening could indicate device left behind, not battery degradation"
    ],
    "evidence_against": [
      "CHARLIE emission pattern is consistent with operational coordination, not detention",
      "No port authority records show unusual cargo activity since Feb 1",
      "Cryptophone signal shows micro-movement consistent with human handling, not static placement",
      "PHANTOM MERCY still coordinating operations in Marseille -- no indication of emergency evacuation"
    ]
  }'
```

Three hypotheses. H1 at 75% confidence. H2 at 15%. H3 at 10%.

Then al-Rashid's SIGINT analysis came in and changed everything:

```bash
# Al-Rashid updates H1 confidence based on new SIGINT
curl -s -X PUT http://localhost:3000/api/v1/collab/hypotheses/01956c00-cc01-7000-8000-000000000001 \
  -H "Authorization: Bearer $ALRASHID_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "confidence": 0.85,
    "status": "investigating",
    "evidence_for": [
      "Cryptophone 500 emission signature matches DGSE-issue device",
      "Signal detected at ALPHA for 80% of observation period (14 days)",
      "Movement pattern consistent with captive: stationary with rare transfers",
      "GEOINT co-travel analysis shows ALPHA-CHARLIE coordination (12 events)",
      "Signal first appeared 3 days after Clara went dark (transit time)",
      "NEW: SIGINT analysis of Cryptophone power-on pattern shows 5-15 second bursts at irregular intervals -- consistent with covert operation by person with device access, NOT with captor powering device for check"
    ]
  }' | jq '{status, confidence}'
```

```json
{
  "status": "investigating",
  "confidence": 0.85
}
```

Al-Rashid's insight was crucial. The power-on pattern -- brief, irregular,
deliberate -- suggested Clara was turning the phone on herself. Briefly.
Secretly. Knowing the signal might be detected. Knowing we might be looking.

She was sending us a beacon.

The update handler preserves fields not included in the request:

```rust
async fn update_hypothesis(
    State(state): State<AppState>,
    Extension(_auth): Extension<AuthContext>,
    Path(id): Path<Uuid>,
    Json(req): Json<UpdateHypothesisRequest>,
) -> Result<Json<HypothesisRow>, (StatusCode, String)> {
    let existing = sqlx::query_as::<_, HypothesisRow>(
        "SELECT id, board_id, title, description, status, confidence, \
         evidence_for, evidence_against, created_by, created_at, updated_at \
         FROM mission_hypotheses WHERE id = $1",
    )
    .bind(id)
    .fetch_optional(&state.db)
    .await
    .map_err(|e| (StatusCode::INTERNAL_SERVER_ERROR, format!("db error: {e}")))?
    .ok_or_else(|| (StatusCode::NOT_FOUND, "hypothesis not found".into()))?;

    let title = req.title.unwrap_or(existing.title);
    let description = req.description.or(existing.description);
    let status = req.status.unwrap_or(existing.status);
    let confidence = req.confidence.unwrap_or(existing.confidence);
    let evidence_for = req.evidence_for.unwrap_or(existing.evidence_for);
    let evidence_against = req.evidence_against.unwrap_or(existing.evidence_against);

    sqlx::query(
        "UPDATE mission_hypotheses \
         SET title = $1, description = $2, status = $3, confidence = $4, \
             evidence_for = $5, evidence_against = $6, updated_at = $7 \
         WHERE id = $8",
    )
    .bind(&title).bind(&description).bind(&status)
    .bind(confidence).bind(&evidence_for).bind(&evidence_against)
    .bind(now).bind(id)
    .execute(&state.db).await?;

    // Return updated row
}
```

---

## 17.7 -- Annotations: The War Council

The team started annotating. Every pin became a discussion thread. Every
observation was recorded, timestamped, attributed.

```bash
PIN_ID="01956b00-bb01-7000-8000-000000000001"  # ALPHA location pin

# Marchetti adds DGSE context
curl -s -X POST http://localhost:3000/api/v1/collab/pins/$PIN_ID/annotations \
  -H "Authorization: Bearer $MARCHETTI_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "DGSE has a safe house 800m from the ALPHA coordinates. Last used 2025-08. Could serve as forward staging for rescue team. I can authorize access within 4 hours. Building has rooftop observation point with line of sight to Vieux-Port waterfront.",
    "annotation_type": "action_item",
    "board_id": "01956a00-aa01-7000-8000-000000000001"
  }' | jq .
```

```json
{
  "id": "01956d00-dd01-7000-8000-000000000001",
  "board_id": "01956a00-aa01-7000-8000-000000000001",
  "pin_id": "01956b00-bb01-7000-8000-000000000001",
  "content": "DGSE has a safe house 800m from the ALPHA coordinates...",
  "annotation_type": "action_item",
  "created_by": "01945000-0000-7000-8000-000000000002",
  "created_at": "2026-02-06T14:30:00Z"
}
```

```bash
# Vasquez raises a concern
curl -s -X POST http://localhost:3000/api/v1/collab/pins/$PIN_ID/annotations \
  -H "Authorization: Bearer $VASQUEZ_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "If the mole is inside DGSE, using a DGSE safe house is a risk. The safe house address may be in compromised records. Recommend alternative staging location -- commercial rental under cover identity, booked within 24 hours.",
    "annotation_type": "contradiction",
    "board_id": "01956a00-aa01-7000-8000-000000000001"
  }'

# Marchetti responds
curl -s -X POST http://localhost:3000/api/v1/collab/pins/$PIN_ID/annotations \
  -H "Authorization: Bearer $MARCHETTI_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Valid concern. The safe house is listed in compartmented records only -- but compartmented means nothing if the mole has elevated access. I will arrange alternative staging through a cutout. Airbnb rental in the 1st arrondissement, paid cash, booked under a name that is not in any intelligence database.",
    "annotation_type": "analysis",
    "board_id": "01956a00-aa01-7000-8000-000000000001"
  }'

# Al-Rashid adds tactical context
curl -s -X POST http://localhost:3000/api/v1/collab/pins/$PIN_ID/annotations \
  -H "Authorization: Bearer $ALRASHID_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Re: entry approach. The Vieux-Port area is dense residential. Multiple narrow streets. Entry team needs to account for civilian presence. Recommend 03:00-04:00 window based on PHANTOM MERCY own transfer pattern (Jan 30 transfer at 03:10 suggests they consider this the quietest operational window). We use their own timing against them.",
    "annotation_type": "analysis",
    "board_id": "01956a00-aa01-7000-8000-000000000001"
  }'
```

The annotation discussion threaded perfectly. Marchetti proposed. Vasquez
challenged. Marchetti adapted. Al-Rashid added tactical timing. All
recorded, all timestamped, all attributed.

The annotation types we used:

| Type            | Purpose                                           |
|-----------------|---------------------------------------------------|
| `comment`       | General observation or question                   |
| `analysis`      | Structured analytical finding                     |
| `corroboration` | Evidence supporting the pin's assertion           |
| `contradiction` | Evidence challenging the pin's assertion          |
| `action_item`   | Something that needs to be done                   |
| `context`       | Background information relevant to the pin        |

---

## 17.8 -- The Timeline: Watching the Clock

Every action on the board generated a timeline event. With a 7-10 day window
before Clara's phone battery died, the timeline became our operational clock:

```bash
curl -s http://localhost:3000/api/v1/collab/notifications \
  -H "Authorization: Bearer $TOKEN" | jq '.[0:3]'
```

```json
[
  {
    "id": "01956e00-ee01-7000-8000-000000000001",
    "event_type": "hypothesis",
    "source_module": "mission",
    "source_id": "01956c00-cc01-7000-8000-000000000001",
    "title": "H1 confidence updated to 0.85 -- SIGINT confirms covert beacon pattern",
    "description": "Al-Rashid SIGINT analysis: Cryptophone power-on pattern consistent with deliberate covert signaling by Clara...",
    "severity": "info",
    "metadata": {},
    "occurred_at": "2026-02-06T15:22:00Z"
  },
  {
    "id": "01956e00-ee01-7000-8000-000000000002",
    "event_type": "annotation",
    "source_module": "collab",
    "source_id": "01956d00-dd01-7000-8000-000000000001",
    "title": "Alternative staging arranged -- Airbnb 1st arr. under cover ID",
    "description": "Marchetti: commercial rental under cutout identity...",
    "severity": "info",
    "metadata": {},
    "occurred_at": "2026-02-06T15:00:00Z"
  }
]
```

Acknowledging notifications:

```bash
curl -s -X POST http://localhost:3000/api/v1/collab/notifications/01956e00-ee01-7000-8000-000000000001/read \
  -H "Authorization: Bearer $TOKEN" | jq .
```

```json
{
  "read": true,
  "event_id": "01956e00-ee01-7000-8000-000000000001",
  "user_id": "01945000-0000-7000-8000-000000000001"
}
```

---

## 17.9 -- The Mission Plan Takes Shape

**2026-02-06, 18:00 UTC.**

After seven hours on the STARLIGHT board, the plan was taking shape. I
summarized it in a final pin:

```bash
curl -s -X POST http://localhost:3000/api/v1/collab/workspaces/$BOARD/pins \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "pin_type": "mission_plan",
    "title": "Op STARLIGHT: Execution Plan v1.0",
    "content": "OBJECTIVE: Recover DGSE Officer Clara Dubois from PHANTOM MERCY holding site.\n\nPHASE 1 - CONFIRM (Feb 7-8): Deploy passive SIGINT collection from alternative staging location (1st arr. Airbnb). Confirm Clara signal at ALPHA with building-level precision. Establish visual surveillance on ALPHA and CHARLIE.\n\nPHASE 2 - ISOLATE (Feb 8): Cut CHARLIE-ALPHA communication. Al-Rashid deploys targeted interference on CHARLIE Thuraya frequency during the operation window. This blinds the operational hub while the rescue team moves on ALPHA.\n\nPHASE 3 - EXTRACT (Feb 8-9, 03:00-04:00): Entry team (Marchetti DGSE asset, 4 operators) enters ALPHA building. Extracts Clara. Evacuates to secondary vehicle at pre-positioned point in 7th arrondissement.\n\nPHASE 4 - EVIDENCE (concurrent): Vasquez secures all digital evidence at ALPHA for prosecution. Playseat evidence chain maintained -- BLAKE3 + SHA-256 dual hashing on all seized materials.\n\nCONTINGENCY: If Clara is at BRAVO, redirect team. If CHARLIE shows alert response, abort and regroup. If mole compromise detected, go dark and evacuate.\n\nWINDOW: 48-72 hours. Clara phone battery estimated at 7-10 days from Feb 5. Hard deadline: Feb 15.",
    "position_x": 700,
    "position_y": 250,
    "color": "#22c55e"
  }'
```

---

## 17.10 -- The Mole Warning From the Mesh

**2026-02-06, 21:30 UTC.**

We were almost done when the Mesh delivered one final intelligence product.
A warning from a partner node -- unattributed, encrypted, routed through three
relays:

> STARLIGHT MAY BE COMPROMISED. ANOMALOUS QUERY ACTIVITY AGAINST MARSEILLE
> GEOLOCATION DATA IN PARTNER DATABASE. QUERY ORIGIN: INTERNAL. QUERY
> TIMING: 6 HOURS AFTER PHANTOM MERCY BRIEFING DISTRIBUTED. RECOMMEND
> ASSUME WORST CASE.

Someone inside the liaison network had queried Marseille geolocation data
six hours after my PHANTOM MERCY briefing hit the Mesh. That briefing
didn't mention Marseille by name -- but it mentioned Fondation Lumiere, and
anyone with a search engine could connect that to Marseille.

The mole was real. And they were moving.

I pinned the warning:

```bash
curl -s -X POST http://localhost:3000/api/v1/collab/workspaces/$BOARD/pins \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "pin_type": "warning",
    "title": "MESH ALERT: Anomalous Marseille Query Activity",
    "content": "Partner Mesh node reports anomalous query against Marseille geolocation data. Timing: 6 hours after PHANTOM MERCY briefing. Origin: internal to partner network. ASSESSMENT: Mole is active and may be aware of operational interest in Marseille. STARLIGHT timeline must accelerate. If they move Clara before we are in position, we lose her.",
    "position_x": 700,
    "position_y": 400,
    "color": "#dc2626"
  }'
```

Marchetti read the alert over my shoulder. His face didn't change. Twenty
years of running agents in hostile territory will do that to your expressions.

"We move tomorrow," he said quietly.

"The plan isn't--"

"The plan is good enough. If the mole knows we're looking at Marseille, they'll
move her within 48 hours. We go tomorrow night or we don't go at all."

I looked at the board. Eight pins from earlier. Plus the mission plan. Plus
the Mesh warning. Ten pieces of intelligence, meticulously structured and
cross-referenced, all pointing to one conclusion: we had one shot at this,
and the window was closing faster than we'd planned.

---

## 17.11 -- Collaboration Statistics (The Weight of a Rescue)

```bash
curl -s http://localhost:3000/api/v1/collab/stats \
  -H "Authorization: Bearer $TOKEN" | jq .
```

```json
{
  "workspaces": 1,
  "members": 4,
  "pins": 10,
  "hypotheses": 3,
  "annotations": 12,
  "timeline_events": 27
}
```

One workspace. Four people. Ten pins. Three hypotheses. Twelve annotations.
Twenty-seven timeline events. The smallest collaboration board I'd ever
built, and the most important.

The queries behind those numbers:

```sql
SELECT COUNT(*) FROM mission_boards;
SELECT COUNT(*) FROM mission_board_members;
SELECT COUNT(*) FROM mission_pins;
SELECT COUNT(*) FROM mission_hypotheses;
SELECT COUNT(*) FROM mission_annotations;
SELECT COUNT(*) FROM unified_timeline_events
WHERE source_module = 'collab' OR source_module = 'mission';
```

---

## 17.12 -- Operational Lessons

**Start with hypotheses, not conclusions.** When Clara's life was at stake, the
temptation to skip structured analysis and just go to ALPHA with a rescue team
was overwhelming. But the hypothesis framework forced us to consider BRAVO and
CHARLIE, which led to the tactical insight about cutting CHARLIE communications
during the rescue. Structure saves lives.

**Use colors consistently.** Red for critical/confirmed threats. Amber for
assessed locations. Blue for SIGINT. Purple for DGSE intelligence. Green for
the mission plan. When the board had ten pins at 03:00 in the morning and
everyone was running on caffeine and fear, color coding was the difference
between clarity and chaos.

**Annotate aggressively.** Vasquez's contradiction of Marchetti's safe house
proposal probably prevented a catastrophic operational security failure. If
she hadn't annotated, we might have staged from a DGSE location the mole
could compromise. The annotation thread is where analysis actually happens.

**The evidence_against array matters more than evidence_for.** When I wanted
H1 to be true with every fiber of my being -- when I *needed* Clara to be
at ALPHA because that was where we could reach her -- the discipline of
documenting the counter-evidence kept us honest. Four counter-arguments for
H1. If any of them proved true, we needed a different plan.

**Archive, don't delete.** When this is over, the STARLIGHT board becomes the
permanent record of a rescue operation. Every decision documented. Every
alternative considered. Every warning heeded. That's not just good intelligence
practice -- it's the foundation for the prosecution case that will dismantle
PHANTOM MERCY.

Mission boards aren't just tools. They're a way of thinking. And when the
thinking has to be right because someone's life depends on it, the structure
isn't a luxury -- it's a lifeline.

---

**2026-02-06, 22:00 UTC.**

Marchetti left at 22:00. He had calls to make. People to position. A rescue
team to assemble without triggering any of the channels the mole might be
watching.

I stayed at my desk. Stared at the board. Stared at the three hypothesis cards.
H1: 85%. H2: 15%. H3: 10%. The confidence numbers were good. The evidence was
solid. The plan was... adequate.

Adequate. For a rescue operation where one mistake means Clara dies.

I opened her notebook one more time. Page 112. The last page she'd written on.
Three words, underlined twice:

*"Trust the evidence."*

I closed the notebook. Tomorrow we'd find out if the evidence was right.

---

*Next chapter: Compliance Under Fire -- Building the Legal Case*

---

`© 2026 Playseat — All Rights Reserved | Defensive Intelligence Through ADAPT`
