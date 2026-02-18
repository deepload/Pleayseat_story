# Chapter 31 — Zero to Analyst: Clara's First Lesson

She stood at the front of the room like she owned it. And she did -- Clara Dubois had founded this academy three months after we pulled her out of that shipping container in Marseille, and already the first cohort of twelve analysts sat in tiered rows with fresh laptops and fresh faces, not one of them older than twenty-six.

I leaned against the back wall with my arms crossed. I was not supposed to be here. Clara had told me to stay away, that my presence would distract the students, that she needed to do this on her own. But I came anyway, because I needed to see it. I needed to see what she had become.

She had lost twelve pounds during captivity. She had gained back eight. The scar on her left forearm -- the one she got from the razor wire climbing out of the PHANTOM MERCY compound -- was still pink and raised, but she did not hide it anymore. She wore a charcoal blazer with the sleeves pushed up. No jewelry. No makeup. Just Clara.

"Everything you need is in the platform," she said, and her voice was steady in a way it had not been four months ago. "I know, because it saved my life."

The room went still.

"My name is Clara Dubois. I spent eleven years with the DGSE. I ran deep-cover operations on three continents. And five months ago, I was held in a container by a trafficking network called PHANTOM MERCY, and the only reason I am standing in front of you today is because a team of analysts running this platform found me before they moved me across a border I would not have come back from."

She clicked the projector. The Playseat login screen appeared on the wall behind her. Dark slate background. "PLAYSEAT" in blue letters. "Defensive Intelligence Platform" in smaller text below.

"Today, I am going to teach you how to use it. And by the end of this session, you will have a running instance, a live investigation, and a complete ADAPT cycle. Not theory. Not slides. Hands on keyboards. Understood?"

Twelve heads nodded.

I smiled from the back of the room. That was my girl.

---

## "Before We Touch a Single Line of Code"

Clara paced in front of the projector like she was briefing a field team. She had that quality -- the ability to make a technical walkthrough feel like a pre-mission brief. Every instruction was precise. Every pause was deliberate.

"Four tools," she said, holding up four fingers. "That is all you need on your machine before we begin."

She wrote on the whiteboard:

```
1. Docker Desktop (v24.0+)
2. Rust Toolchain (stable, edition 2021)
3. Node.js 18+
4. Git
```

"Docker gives us the infrastructure. Rust gives us the platform. Node gives us the desktop interface. Git gives us the code. Four tools. If you cannot install four tools, you do not belong in this room."

The analysts scrambled. Clara walked through the rows, checking screens, correcting configurations. She had a teacher's patience that I had never seen in the field. In the field, Clara was all speed and edges. Here, she slowed down. She explained.

"Docker first," she said. "Open your terminals."

```bash
docker --version
# Docker version 24.0.x or higher
docker compose version
# Docker Compose version v2.x.x
```

"If you are on Windows -- and some of you are, I can see the Taskbar -- make sure WSL2 backend is enabled. On macOS, allocate at least 4 GB of RAM to Docker in Preferences, then Resources. Do not skip this. The platform runs PostgreSQL, MinIO, and a Rust API server. They need room to breathe."

She turned to another row. "Rust next."

```bash
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
# Or on Windows, download rustup-init.exe from https://rustup.rs

rustc --version
# rustc 1.82.0 or later

cargo --version
# cargo 1.82.0 or later
```

"Rust is the backbone. Two hundred and five crates. Six thousand unit tests. Every line compiled with zero errors, or we do not ship. That is the standard. That is non-negotiable."

I watched her say that and I thought about the night I wrote the first crate -- `shared_types` -- in a hotel room in Geneva while Clara was still in the field. I had not known then what it would become.

"Node.js."

```bash
node --version
# v18.x.x or v20.x.x or v22.x.x

npm --version
# 9.x.x or later
```

"The desktop application is React, TypeScript, Tailwind CSS, and a charting library called recharts. You do not need to understand all of that yet. You need Node installed."

"Finally, Git."

```bash
git --version
# git version 2.x.x
```

"Four tools. Show me green checks on all four. Raise your hand if you are stuck."

Two hands went up. Clara helped them. I could have helped too, but I stayed at the back. This was her room.

---

## Step 1: Clone and Start

"Now we pull the code and stand up the infrastructure," Clara said. "Open your terminal. Navigate to wherever you keep projects."

```bash
git clone https://github.com/deepload/Playseat_gov.git
cd Playseat_gov
```

"What you should see is this structure."

She projected the directory tree:

```
Playseat_gov/
  crates/           # 205 Rust service crates
  apps/desktop/     # Tauri v2 desktop app (React + TypeScript)
  migrations/       # 206 PostgreSQL migrations (915 tables + seed data)
  docker-compose.yml
  .env.example
  Cargo.toml        # Workspace root
```

"Two hundred and five crates. Two hundred and six migrations. Nine hundred and fifteen database tables. Thirty-six end-to-end tests. This is not a prototype. This is a production platform. Treat it with respect."

She paused, and I saw her eyes flick to the back of the room. She found me. She held my gaze for exactly one second, then turned back to the students.

"Create your environment file."

```bash
cp .env.example .env
```

"Open it. Set these values."

```env
POSTGRES_PASSWORD=playseat_dev_2026
JWT_SECRET=super-secret-jwt-key-change-in-production
S3_ACCESS_KEY=minioadmin
S3_SECRET_KEY=minioadmin
```

"In production, these would be generated secrets stored in a vault. For training, these defaults work. But I want you to understand something."

She tapped the JWT_SECRET line on the projector.

"This string is the only thing standing between your platform and unauthorized access. Fifteen characters of entropy is the difference between a defended system and a compromised one. When we get to authentication later, you will understand why."

She had learned that the hard way. During PHANTOM MERCY, the network we tracked used a hardcoded API key for their logistics system. Eight characters. We cracked it in forty-seven minutes. That crack is why Clara is alive.

"Start the infrastructure."

```bash
docker compose up -d
```

The room filled with the sound of twelve laptops pulling Docker images. Clara stood at the front, watching progress bars.

```
[+] Running 4/4
 ✔ Network playseat_gov_playseat-internal  Created
 ✔ Container playseat-postgres             Healthy
 ✔ Container playseat-minio                Healthy
 ✔ Container playseat-minio-init           Exited (0)
```

"The `minio-init` container creates four S3 buckets -- evidence, reports, artifacts, backups -- then exits. That exit code of zero is expected. It means the buckets were created successfully."

"Verify everything is running."

```bash
docker compose ps
```

"You should see `playseat-postgres` as `running (healthy)` and `playseat-minio` as `running (healthy)`. If either shows anything else, raise your hand."

No hands.

"Check the database is responsive."

```bash
docker exec playseat-postgres pg_isready -U playseat -d playseat
# /var/run/postgresql:5432 - accepting connections
```

"Check MinIO is responsive."

```bash
curl -s http://localhost:9000/minio/health/live
# (empty 200 response = healthy)
```

"You can visit the MinIO Console at `http://localhost:9001` in your browser. Login with the S3 credentials from your `.env`. You will see four buckets. That is your object storage ready to receive evidence."

Clara looked at the clock on the wall. Nine minutes in. Right on schedule. She was running this class the way she ran surveillance operations -- every minute accounted for.

---

## Step 2: Build the Workspace

"This is the big one," Clara said. "Two hundred and five Rust crates. Deep breath."

```bash
cargo build --workspace
```

"What to expect. First time: five to eight minutes depending on your machine. Subsequent builds: thirty to ninety seconds. Incremental compilation. You will see `shared_types`, then the `core-` crates, then the `svc-` crates, and finally `svc-api`. Zero errors. If you get errors, your Rust toolchain is outdated."

The room hummed with compilation. Clara walked the rows again, checking screens. One analyst -- a young woman in the third row with close-cropped hair and sharp eyes -- had a warning on her screen. Clara leaned down, read it, typed something, nodded, and moved on. I could not see what she typed, but the warning disappeared.

"While that compiles, in a separate terminal, let's verify the test suite."

```bash
cargo test --workspace 2>&1 | tail -5
```

"You should see something like this."

```
test result: ok. 6006 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out
```

"Six thousand six tests. All green. Every crate has unit tests. Every route is tested. Every migration is validated. Zero tolerance for failures."

She let that sink in.

"I have worked in organizations where the test suite was 'run it and see if it breaks.' That is not how we work here. The test suite is your first line of defense. If a test fails, something is wrong, and you do not deploy until it is fixed. This is the same discipline that found me."

Her voice did not waver when she said that. But I noticed her hand press flat against the lectern, steadying herself.

---

## Step 3: Migrations and the API Server

"The migrations create all nine hundred and fifteen tables and seed demo data," Clara said. "Set your environment variables."

```bash
export DATABASE_URL="postgres://playseat:playseat_dev_2026@localhost:5432/playseat"
export JWT_SECRET="super-secret-jwt-key-change-in-production"
export S3_ENDPOINT="http://localhost:9000"
export S3_BUCKET="evidence"
export S3_REGION="us-east-1"
export S3_ACCESS_KEY="minioadmin"
export S3_SECRET_KEY="minioadmin"
```

"On Windows PowerShell, use `$env:DATABASE_URL = \"...\"` instead."

"Now start the API server."

```bash
cargo run --bin svc-api
```

"Watch the output."

```
[INFO  svc_api] Running 206 migrations...
[INFO  svc_api] Migrations complete. 915 tables created.
[INFO  svc_api] Playseat API v0.2.0 listening on 0.0.0.0:3000
```

"The first start runs all two hundred and six migrations. Ten to thirty seconds. Subsequent starts are instant because the migrations have already been applied."

She pointed to the terminal output on the projector.

"That line -- `915 tables created` -- that is the data model. Intelligence collections, threat indicators, evidence chains, incident timelines, forensic artifacts, SOAR playbooks, ADAPT cycles, compliance frameworks, risk registers. Every table has referential integrity. Every column has a type. Every record has a timestamp and an audit trail."

"Verify the API is alive."

```bash
curl -s http://localhost:3000/health | python -m json.tool
```

```json
{
    "status": "healthy",
    "database": "connected",
    "version": "0.2.0"
}
```

"Healthy. Connected. Version 0.2.0. That is your API running. Two hundred and four route files. Twenty-five database-connected modules. All live."

She turned to the class. "When I was in that container in Marseille, every thirty minutes, the team running the search queried this exact endpoint to make sure the platform was still alive. The platform does not sleep. Neither did they."

---

## Step 4: The Desktop App

"Open a new terminal," Clara said. "Keep the API running."

```bash
cd apps/desktop
npm install
```

"This installs React, TypeScript, Tailwind, recharts, lucide-react, react-hot-toast, and all dependencies. About thirty seconds."

```bash
npm run dev
```

```
VITE v5.x.x  ready in 800 ms
  ➜  Local:   http://localhost:1420/
```

"Open your browser to `http://localhost:1420`."

She waited while twelve browsers loaded the login page.

"What do you see?"

The young woman in the third row spoke first. "Dark slate background. 'PLAYSEAT' in blue. 'Defensive Intelligence Platform' subtitle."

"Good. Clean. Professional. Government-grade. This is not a startup landing page. This is a tool for people whose work matters."

I remembered building that login page on a flight from Washington to London. Clara was already deployed. I did not know then that the next time I saw that login screen, I would be using it to track the people who had taken her.

---

## Step 5: First Login

"The demo seed data creates four users," Clara said.

| Username | Password | Role |
|----------|----------|------|
| `admin` | `admin` | Administrator |
| `analyst` | `analyst` | Analyst |
| `operator` | `operator` | Operator |
| `viewer` | `viewer` | Read-only |

"For this exercise, log in as `admin`. Type `admin` in both fields and press Enter."

Behind the scenes, Clara explained, the login fires this request:

```bash
curl -s -X POST http://localhost:3000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin"}'
```

And receives:

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
  "expires_in": 900
}
```

"The JWT access token has a fifteen-minute expiry. The refresh token lasts seven days. The access token gets stored in localStorage. The refresh token handles silent re-authentication. You never see any of this. You just land on the Dashboard."

She paused. "For the API exercises in this session, save your token."

```bash
TOKEN=$(curl -s -X POST http://localhost:3000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin"}' | python -m json.tool | grep access_token | cut -d'"' -f4)

echo $TOKEN
# eyJhbGciOiJIUzI1NiIs...
```

"This token is your identity on the platform. Every API call requires it. Without it, you are no one."

---

## Step 6: The Tour

Clara walked the class through every section of the sidebar. She moved slowly, deliberately, like someone who had earned the right to explain something they had survived.

### The Sidebar

"On the left side of the screen, a dark sidebar. Slate-900 background, slate-700 border. 224 pixels wide. At the top, a collapse button shrinks it to 64 pixels, icon-only mode. Seven groups."

She listed them:

- **Platform**: Dashboard, ADAPT, Command Center, Campaigns, Findings
- **Intelligence**: Threat Intel, OSINT, AI Analysis, Advanced Intel, Ontology, Threat Model
- **Operations**: Labs, Red Team, Purple Team, Cyber Range, Social Eng, Security Tools, SOC Ops, Missions
- **Defense**: Incidents, SOAR, Forensics, Endpoint, Network Security, Zero Trust, Malware Analysis
- **Security Posture**: Vulnerability, Cloud Security, Identity, Hardening, Data Protection
- **Engineering**: DevSecOps, SIEM, Infra Ops
- **Governance**: Compliance, Risk, Metrics, Reporting, Awareness

"Forty pages total. Each one backed by real API routes, real database tables, real tests. No mockups. No placeholders."

---

### The Dashboard

"Click Dashboard. Or just press the home key. This is where you start every day."

Clara's voice changed when she talked about the Dashboard. She became quieter, more focused. Like a pilot describing the instruments she flies by.

"Top row. Title on the left -- 'Operations Center.' Live clock on the right, updating every second. Emerald green, monospace font. This is not decoration. In incident response, knowing the exact time you observed something matters."

"Health strip. Four green pills -- API, Database, MinIO, Audit Pipeline. Each shows a green dot and 'online.' On the far right, a pulsing green dot with 'OPERATIONAL -- v0.2.0.' Green means it works. Red means it does not. There is no yellow. In this line of work, something either works or it does not."

"KPI grid. Six cards in a row."

| Card | Color | Icon | Shows |
|------|-------|------|-------|
| Campaigns | Blue | Shield | Campaign count |
| Active Incidents | Orange | AlertTriangle | Incidents not yet closed |
| Containment | Red | Zap | Containment actions executed |
| IR Playbooks | Emerald | Activity | Playbooks available |
| IOCs Tracked | Yellow | Eye | Total indicators of compromise |
| Threat Feeds | Blue | Radio | Active feeds |

"Charts row. Three charts side by side."

She described them like someone describing a landscape she had memorized from a surveillance post:

1. **Severity Distribution** -- Donut pie chart. Red for Critical, orange for High, yellow for Medium, green for Low. "A mostly-red chart means you have urgent work. A mostly-green chart means your posture is healthy."

2. **7-Day Activity** -- Area chart. Orange gradient for incidents, blue gradient for findings. "A spike on a weekend is unusual. Investigate."

3. **Campaign Pipeline** -- Bar chart. Campaigns by status: Draft, Authorized, Executing, Reporting, Closed. Indigo bars. "If Reporting is piling up, help with the writing."

"Connected Modules panel. Three-column grid. Twenty-three modules, each with a green dot and 'Live' label."

She listed them: Campaigns, Findings, Evidence, Labs, Red Team, Social Eng, AI Analysis, Incidents, Threat Intel, Health, OSINT, Forensics, SOAR, Zero Trust, UEBA, Auth, Compliance, Reporting, Cyber Range, Purple Team, Endpoint, Risk, Metrics.

"Intelligence Overview panel. Threat Feeds, IOCs Tracked, Threat Actors, Intel Reports. Below that: Incident MTTC -- Mean Time to Contain -- in minutes. The industry average is two hundred eighty minutes. Ours is under sixty. The difference is preparation."

"Risk gauge. A horizontal gradient bar from green through yellow to red. The fill percentage represents your overall risk posture. Right now it reads fifty-five percent -- Moderate."

"Active campaigns list. The first six campaigns with status badges."

"Platform capabilities panel. The numbers that tell you what you are working with."

| Stat | Value |
|------|-------|
| Rust Crates | 205 |
| API Routes | 203 |
| Unit Tests | 6,006 |
| SQL Migrations | 206 |
| DB Tables | 915 |
| Compliance Frameworks | 7 |
| Shared Enums | 135+ |
| Agent Definitions | 28 |
| E2E Tests | 36 |
| Workflows | 8 |

"Evidence Hashing: BLAKE3 plus SHA-256. Dual-hash. Court-grade. Authentication: JWT plus RBAC, five roles, sixteen permissions."

"Footer: 'Press Ctrl+K to open Command Palette.'"

Clara looked at the class. "That is your single pane of glass. Every number is live. Every module is connected. Every chart is drawn from real data. When I was missing, this is what my rescue team was staring at."

---

### Campaigns

"Click 'Campaigns' in the sidebar. You see a list of campaigns from the seed data."

Clara had the class create their first campaign.

"Click 'New Campaign.' Name it 'Operation Sentinel Watch.' Description: 'Q1 2026 external perimeter assessment.' Click Create."

Behind the scenes:

```bash
curl -s -X POST http://localhost:3000/campaigns \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Operation Sentinel Watch",
    "description": "Q1 2026 external perimeter assessment"
  }'
```

```json
{
  "id": "01953a2b-...",
  "name": "Operation Sentinel Watch",
  "description": "Q1 2026 external perimeter assessment",
  "status": "Draft",
  "created_at": "2026-02-18T...",
  "updated_at": "2026-02-18T..."
}
```

"Save that ID. We will use it."

```bash
CAMPAIGN_ID="01953a2b-..."
```

I watched her and I remembered the campaign we named PHANTOM MERCY. I had created it from this same interface, in the middle of the night, with coffee going cold on my desk and Clara's last encrypted message open in another window. The campaign that brought her home.

---

### Findings

"Click 'Findings' in the sidebar. This page shows findings linked to campaigns."

Clara walked them through creating a finding via the ingest API:

```bash
curl -s -X POST http://localhost:3000/findings/ingest \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "campaign_id": "'$CAMPAIGN_ID'",
    "tool_output": "CRITICAL: SQL Injection found in /api/users?id=1 OR 1=1. Parameter: id. Type: Union-based. DBMS: PostgreSQL 16. CWE-89.",
    "format": "generic"
  }'
```

```json
{
  "findings_created": 1
}
```

"The platform parsed the raw tool output, extracted the severity -- Critical -- identified the CWE -- CWE-89 -- and created a structured finding. Refresh the page. Your finding appears with a red Critical badge."

"Now run AI triage."

```bash
curl -s -X POST http://localhost:3000/ai/triage \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"finding_id": "FINDING_ID_HERE"}'
```

```json
{
  "severity": "Critical",
  "confidence": "high",
  "false_positive_likelihood": "low",
  "reasoning": "Union-based SQL injection against a user-facing endpoint with direct database access. High confidence, low false-positive risk."
}
```

"The AI confirms what the tool found. High confidence. Low false-positive risk. This is not a guess. This is triangulated analysis."

---

### Evidence

Clara's voice dropped half a register when she talked about evidence. This was personal.

"Evidence management is available through the API and the UI. Upload evidence to your campaign."

```bash
curl -s http://localhost:3000/campaigns/$CAMPAIGN_ID/evidence \
  -H "Authorization: Bearer $TOKEN"
```

```json
[]
```

"Empty. Nothing uploaded yet. When you upload a file through the UI -- there is a drag-and-drop zone on the Findings page -- the platform does five things."

She held up five fingers.

"One. Uploads the file to MinIO. Two. Computes the BLAKE3 hash. Three. Computes the SHA-256 hash. Four. Records both hashes in the database. Five. Creates an immutable audit trail entry."

"Both hashes provide tamper detection. If anyone modifies the evidence, the hashes will not match. This is court-grade evidence handling."

She looked at the class with an intensity that made the room quieter.

"During the PHANTOM MERCY investigation, the evidence chain was the only thing that convinced Interpol to issue the warrants. Without cryptographic proof that our evidence had not been tampered with, forty-seven children would still be missing. Evidence integrity is not a feature. It is a moral obligation."

---

### Threat Intel

"Click 'Threat Intel' in the sidebar. Five tabs: Indicators, Feeds, Reports, STIX, Actors."

Clara walked through each tab quickly, giving the highlights. The students were taking notes. Some were typing along. The young woman in the third row was already ahead, creating IOCs without being told.

"Create an IOC manually."

```bash
curl -s -X POST http://localhost:3000/threatintel/iocs \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "ioc_type": "ip_address",
    "value": "198.51.100.42",
    "confidence": "high",
    "threat_actor": "APT-PHANTOM",
    "tags": ["c2", "cobalt-strike", "exfiltration"]
  }'
```

```json
{
  "id": "01953a3f-...",
  "status": "created"
}
```

"Feeds tab shows your STIX/TAXII feeds. STIX tab lets you browse ingested objects. Actors tab shows threat actor profiles. We will go deep on all of these in the next session."

---

### Incidents

"Click 'Incidents' in the sidebar. Declare a new incident."

```bash
curl -s -X POST http://localhost:3000/incident/incidents \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Suspected Lateral Movement - CORP-WS-047",
    "description": "EDR alert: PsExec execution detected on workstation CORP-WS-047 from unknown source.",
    "priority": "P1",
    "affected_systems": ["CORP-WS-047", "CORP-DC-01"]
  }'
```

```json
{
  "id": "01953a45-...",
  "title": "Suspected Lateral Movement - CORP-WS-047",
  "phase": "Detection",
  "priority": "P1"
}
```

"The incident starts in Detection phase. The platform never auto-advances. You advance it. Human in the loop. Always."

```bash
INCIDENT_ID="01953a45-..."

curl -s -X POST http://localhost:3000/incident/incidents/$INCIDENT_ID/advance \
  -H "Authorization: Bearer $TOKEN"
```

```json
{
  "advanced": true,
  "phase": "Triage"
}
```

"Execute containment."

```bash
curl -s -X POST http://localhost:3000/incident/contain \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "incident_id": "'$INCIDENT_ID'",
    "action_type": "isolate_host",
    "target": "CORP-WS-047"
  }'
```

```json
{
  "id": "01953a47-...",
  "action_type": "isolate_host",
  "target": "CORP-WS-047",
  "status": "executed"
}
```

---

### SOAR

Clara built a playbook live in front of the class.

```bash
curl -s -X POST http://localhost:3000/soar/playbooks \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Isolate and Investigate",
    "description": "Auto-isolate compromised host, collect memory dump, notify SOC lead",
    "trigger_type": "manual"
  }'
```

She added three steps -- isolate host, collect memory, notify SOC lead -- activated the playbook, and triggered it against the incident.

```bash
curl -s -X POST http://localhost:3000/soar/playbooks/$PLAYBOOK_ID/trigger \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"trigger_event": {"incident_id": "'$INCIDENT_ID'", "host": "CORP-WS-047"}}'
```

```json
{
  "id": "01953a55-...",
  "playbook_id": "01953a50-...",
  "status": "running",
  "started_at": "2026-02-18T..."
}
```

"Running," she said. "The playbook executes steps in sequence. Some require approval. Some are automatic. The platform records everything."

---

### The ADAPT Page

"Click ADAPT in the sidebar. This is the crown jewel."

Clara smiled when she said that. It was a small smile, private, directed at no one in particular. But I caught it.

"Fourteen tabs. Mission Control, Exposure Map, Threat Landscape, Defense Actions, Analytics, War Room, Forecast, Autopilot, Briefings, Mesh, Genome, Replay, Collab, Sentinel."

"We will run a full ADAPT cycle in Step 7. Keep reading."

---

## Step 7: Your First ADAPT Cycle

Clara cleared the projector and started fresh.

"ADAPT. Five phases. DISCOVER, CORRELATE, VALIDATE, FORTIFY, PROVE. This is the continuous defensive improvement loop. Everything else on this platform feeds into or out of this cycle."

### Create a Scope

```bash
curl -s -X POST http://localhost:3000/api/v1/adapt/scopes \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Corporate Network Q1 2026",
    "description": "Full corporate network including DMZ, internal servers, and endpoints",
    "asset_types": ["network", "endpoint", "application"],
    "subnets": ["10.0.0.0/8", "172.16.0.0/12"],
    "exclusions": ["10.0.99.0/24"]
  }'
```

```bash
SCOPE_ID="scope-01953a60-..."
```

### Create a Cycle

```bash
curl -s -X POST http://localhost:3000/api/v1/adapt/cycles \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"scope_id": "'$SCOPE_ID'"}'
```

```bash
CYCLE_ID="cycle-01953a61-..."
```

### DISCOVER

"The cycle starts in DISCOVER," Clara said. "What is exposed?"

```bash
curl -s http://localhost:3000/api/v1/adapt/dashboard \
  -H "Authorization: Bearer $TOKEN" | python -m json.tool
```

```bash
curl -s http://localhost:3000/api/v1/adapt/events \
  -H "Authorization: Bearer $TOKEN" | python -m json.tool
```

"Review each event. Acknowledge them as you go."

```bash
curl -s -X POST http://localhost:3000/api/v1/adapt/events/EVENT_ID/acknowledge \
  -H "Authorization: Bearer $TOKEN"
```

### CORRELATE

```bash
curl -s -X POST http://localhost:3000/api/v1/adapt/cycles/$CYCLE_ID/advance \
  -H "Authorization: Bearer $TOKEN"
```

"How do these exposures relate to real threats?"

```bash
curl -s http://localhost:3000/api/v1/adapt/correlations \
  -H "Authorization: Bearer $TOKEN" | python -m json.tool

curl -s http://localhost:3000/api/v1/adapt/correlations/high-risk \
  -H "Authorization: Bearer $TOKEN"
```

### VALIDATE

```bash
curl -s -X POST http://localhost:3000/api/v1/adapt/cycles/$CYCLE_ID/advance \
  -H "Authorization: Bearer $TOKEN"
```

"Are these exposures real and exploitable?"

```bash
curl -s http://localhost:3000/api/v1/adapt/exposures/confirmed \
  -H "Authorization: Bearer $TOKEN"
```

### FORTIFY

```bash
curl -s -X POST http://localhost:3000/api/v1/adapt/cycles/$CYCLE_ID/advance \
  -H "Authorization: Bearer $TOKEN"
```

"What should we fix, and in what order?"

```bash
curl -s http://localhost:3000/api/v1/adapt/actions/pending \
  -H "Authorization: Bearer $TOKEN" | python -m json.tool
```

Approve and execute:

```bash
ACTION_ID="action-..."

curl -s -X POST http://localhost:3000/api/v1/adapt/actions/$ACTION_ID/approve \
  -H "Authorization: Bearer $TOKEN"

curl -s -X POST http://localhost:3000/api/v1/adapt/actions/$ACTION_ID/execute \
  -H "Authorization: Bearer $TOKEN"
```

### PROVE

```bash
curl -s -X POST http://localhost:3000/api/v1/adapt/cycles/$CYCLE_ID/advance \
  -H "Authorization: Bearer $TOKEN"
```

"Can we demonstrate measurable improvement?"

```bash
curl -s http://localhost:3000/api/v1/adapt/score/global \
  -H "Authorization: Bearer $TOKEN"
```

```json
{
  "score": 72,
  "trend": "improving",
  "asset_count": 145
}
```

Clara held up the score on the projector.

"Seventy-two. Improving. One hundred and forty-five assets assessed. That is your baseline. Next cycle, that number goes up. The cycle after that, it goes up again. The cycle never stops."

She turned off the projector and faced the class.

"During PHANTOM MERCY, the team ran fourteen ADAPT cycles in eleven days. The defense score went from forty-one to eighty-seven. Each cycle found something the last one missed. Each cycle closed a gap. By the fourteenth cycle, we had mapped the entire network, correlated every indicator, validated every exposure, fortified every entry point, and proved -- with cryptographic evidence -- that we had found the right location."

Her voice was even. Controlled. But the room felt it.

"That is what ADAPT does. That is why it matters. And that is what I am going to teach you to master."

---

## Step 8: Your First Briefing

"Generate a briefing from the ADAPT cycle data."

```bash
curl -s http://localhost:3000/api/v1/adapt/briefing-templates \
  -H "Authorization: Bearer $TOKEN" | python -m json.tool
```

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

```bash
BRIEFING_ID="briefing-01953a80-..."

curl -s http://localhost:3000/api/v1/adapt/briefings/$BRIEFING_ID \
  -H "Authorization: Bearer $TOKEN" | python -m json.tool
```

"Publish it."

```bash
curl -s -X POST http://localhost:3000/api/v1/adapt/briefings/$BRIEFING_ID/publish \
  -H "Authorization: Bearer $TOKEN"
```

---

## What You Just Did

Clara ticked off the list on the whiteboard.

"In under an hour, you:

1. Spun up PostgreSQL and MinIO with Docker Compose
2. Built 205 Rust crates from source
3. Ran 206 database migrations creating 915 tables
4. Started the API server with 204 route files, all live
5. Launched the desktop app with 40 React pages
6. Logged in and toured the full platform
7. Created a campaign, filed a finding, declared an incident
8. Built and triggered a SOAR playbook
9. Ran a complete ADAPT cycle through all five phases
10. Generated and published an executive briefing"

She capped the marker and turned to the class.

"You are no longer beginners. You are analysts with a running platform. The rest of this course teaches you mastery."

The class broke for lunch. I stayed at the back of the room as the students filed out, talking to each other, comparing notes. The young woman from the third row lingered, asking Clara something about the ADAPT scoring algorithm. Clara answered her with patience and precision, then watched her go.

When the room was empty, Clara walked to the back where I was standing.

"You were not supposed to be here," she said.

"I know."

"How was it?"

"You are a better teacher than I am."

She laughed. It was the first time I had heard her laugh without an edge to it since before Marseille. She leaned her shoulder against mine, just for a moment, and looked at the whiteboard full of her handwriting.

"The platform saved my life," she said. "Now I am going to make sure it saves someone else's."

I did not say anything. I just stood there, beside her, watching the afternoon light move across the classroom floor.

---

## Quick Reference: Essential Commands

```bash
# Login
curl -X POST http://localhost:3000/auth/login -H "Content-Type: application/json" -d '{"username":"admin","password":"admin"}'

# Health check
curl http://localhost:3000/health

# List campaigns
curl http://localhost:3000/campaigns -H "Authorization: Bearer $TOKEN"

# List incidents
curl http://localhost:3000/incident/incidents -H "Authorization: Bearer $TOKEN"

# Incident stats
curl http://localhost:3000/incident/stats -H "Authorization: Bearer $TOKEN"

# Threat intel stats
curl http://localhost:3000/threatintel/stats -H "Authorization: Bearer $TOKEN"

# SOAR stats
curl http://localhost:3000/soar/stats -H "Authorization: Bearer $TOKEN"

# ADAPT dashboard
curl http://localhost:3000/api/v1/adapt/dashboard -H "Authorization: Bearer $TOKEN"

# Global defense score
curl http://localhost:3000/api/v1/adapt/score/global -H "Authorization: Bearer $TOKEN"
```

---

## Troubleshooting

**"Backend unreachable" on Dashboard**
The API is not running. Start it with `cargo run --bin svc-api`. Make sure DATABASE_URL is set.

**"401 Unauthorized" on API calls**
Your token expired (15-minute window). Re-run the login command to get a fresh token.

**Docker containers not starting**
Check `.env` file exists and has all required variables. Run `docker compose logs postgres` to see specific errors.

**Migrations fail**
Make sure PostgreSQL is running and accessible. Check `docker compose ps` for health status.

**Desktop app blank screen**
Open browser dev tools (F12). Check the Console tab for errors. Most common: API not reachable (start it first).

**Port conflicts**
If 3000, 5432, 9000, or 1420 are in use, edit the port mappings in `.env` or `docker-compose.yml`.

---

*Next chapter: we go deep on the Dashboard -- every widget, every chart, every keyboard shortcut. And Clara shows me something I missed.*

---

© 2026 Playseat — All Rights Reserved | Defensive Intelligence Through ADAPT
