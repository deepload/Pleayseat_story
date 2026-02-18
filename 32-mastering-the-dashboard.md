# Chapter 32 — Mastering the Dashboard: Seeing What Clara Sees

It was a Thursday night, two weeks after she started teaching. The academy was closed. The building was supposed to be empty. But the lights on the third floor were on, and I found Clara at the analyst station in Lab Two, three monitors arranged in an arc around her, the Playseat dashboard filling the center screen like a painting she was studying.

She did not hear me come in. She was that focused.

Clara had this way of looking at the dashboard like she was reading a novel. Every number told a story. Every chart was a chapter. Where other analysts saw data points, Clara saw human behavior -- the intentions behind the IP addresses, the fear inside the incident counts, the ambition encoded in the campaign pipeline. She read the dashboard the way a detective reads a crime scene: nothing is random, everything means something, and the thing that matters most is the thing you almost overlooked.

I stood in the doorway and watched her work. She had her reading glasses on -- she had needed them since captivity, something about the weeks in near-darkness -- and she was making notes in a leather-bound journal she kept next to the keyboard. Not typing. Writing. Ink on paper. Clara believed that the act of writing by hand forced a different kind of thinking. She was right.

"You can come in," she said, without turning around.

"How did you know it was me?"

"You are the only person who pauses in doorways."

I pulled a chair beside her and sat down. Her coffee was cold. Mine was still hot -- I had made two cups downstairs, knowing she would be here. I put the fresh one next to her journal.

She picked it up, sipped it, and said, "Look at this."

---

## The Mental Model

Clara tapped the center screen.

"The Dashboard answers one question," she said. "What is the state of my defensive posture right now?"

She traced the layout with her finger from top to bottom.

"Five layers of information. Each one adds depth."

1. **System Health** -- Are all systems operational?
2. **Key Performance Indicators** -- What are the critical numbers?
3. **Trend Charts** -- How are those numbers changing?
4. **Module Status** -- Which platform modules are live?
5. **Campaign and Intelligence Detail** -- What is active right now?

"A quick glance at the health strip takes two seconds," she said. "Reading the KPIs takes ten. The charts need thirty seconds. The full review takes about two minutes. That is my morning briefing cadence. And my Thursday night cadence. And my 3 AM cadence when I cannot sleep."

She glanced at me and I saw something in her eyes -- the sleeplessness, the vigilance that never fully switched off. In the field, that alertness kept her alive. Here, in the warm light of the lab, it looked like something she carried because she did not know how to put it down.

"Let me show you how I read it," she said. "All of it."

---

## The Live Clock

She pointed to the top right corner. Emerald green, monospace font, ticking away.

"The clock."

```typescript
const [clock, setClock] = useState(new Date());

useEffect(() => {
  const timer = setInterval(() => setClock(new Date()), 1000);
  return () => clearInterval(timer);
}, []);
```

"It shows `toLocaleTimeString()` in large text. Full date below in small text. Wednesday, February 18, 2026."

"This is not decoration," Clara said, and her voice was firm. "On the night I was taken, the team could not agree on the exact time they lost contact with me. Seventeen minutes of ambiguity. That ambiguity delayed the response. A live clock on the primary screen removes that problem."

She tapped it. "Always know what time it is. Always."

---

## System Health Strip

Below the header. Four pill-shaped badges in a row.

| Pill | What it checks | API Source |
|------|---------------|------------|
| **API** | Is the Axum server responding? | `GET /health` -> `status === "healthy"` |
| **Database** | Is PostgreSQL connected? | `GET /health` -> `database === "connected"` |
| **MinIO** | Is object storage available? | Static "online" (checked at startup) |
| **Audit Pipeline** | Is the audit trail recording? | Static "online" |

Clara pulled up the API call:

```bash
curl -s http://localhost:3000/health \
  -H "Authorization: Bearer $TOKEN"
```

```json
{
  "status": "healthy",
  "database": "connected",
  "version": "0.2.0"
}
```

"The SQL behind the database check is one line," she said.

```sql
SELECT 1;
```

"That is it. Connectivity check. If it fails, the Database pill turns red."

She showed me the component:

```typescript
function HealthPill({ label, status }: { label: string; status: "online" | "offline" }) {
  return (
    <div className={`flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium ${
      status === "online"
        ? "bg-emerald-900/20 text-emerald-400 border border-emerald-800/30"
        : "bg-red-900/20 text-red-400 border border-red-800/30"
    }`}>
      <span className={`w-1.5 h-1.5 rounded-full ${
        status === "online" ? "bg-emerald-400" : "bg-red-400"
      }`} />
      {label}
    </div>
  );
}
```

"Green or red. No yellow. No warning state. In defensive operations, something either works or it does not. Ambiguity is the enemy."

On the far right, a pulsing green dot:

```
OPERATIONAL — v0.2.0
```

"The pulse is CSS -- Tailwind's `animate-pulse`. It tells you the screen is not frozen. It is alive. Like a heartbeat."

She said that last word quietly, and I remembered the night we lost her signal. The dashboard had shown all four pills green but her heartbeat monitor -- the covert device sewn into her jacket lining -- had gone dark. Four green pills and one dead sensor. The health strip cannot measure everything.

---

## KPI Cards

Six cards in a responsive grid. Clara worked through them one by one, but not the way a manual would. She told me what she saw in each number.

### Card 1: Campaigns (Blue, Shield icon)

"Total campaigns in the system."

```bash
curl -s http://localhost:3000/campaigns \
  -H "Authorization: Bearer $TOKEN"
```

```sql
SELECT id, name, description, status, created_at, updated_at
FROM campaigns
WHERE organization_id = $1
ORDER BY created_at DESC;
```

"What I look for," Clara said. "If this number is zero, no one is working. If it is growing fast, the team is active. If it has been static for weeks, you have stale assessments and people are doing other things when they should be here."

### Card 2: Active Incidents (Orange, AlertTriangle icon)

"Incidents not yet in Closed or Lessons Learned phase."

```bash
curl -s http://localhost:3000/incident/stats \
  -H "Authorization: Bearer $TOKEN"
```

```json
{
  "active_incidents": 3,
  "playbooks": 5,
  "containment_actions": 12,
  "mean_time_to_contain_mins": 47
}
```

```sql
SELECT COUNT(*) as active_incidents
FROM ir_incidents
WHERE phase NOT IN ('closed', 'lessons_learned');
```

"This number should trend toward zero," she said. "If it is climbing, your team is overwhelmed. But here is what most people miss -- if it stays at zero for a long time, your detection is not working. Absence of incidents does not mean absence of threats. It means you are not seeing them."

She wrote that in her journal. I read it upside down: *Zero incidents = check detection first.*

### Card 3: Containment (Red, Zap icon)

"Total containment actions executed."

```sql
SELECT COUNT(*) as containment_actions
FROM ir_containment_actions
WHERE status = 'executed';
```

"High numbers mean your SOAR playbooks are working. Low numbers with high active incidents means containment is stalled. That is when people are panicking instead of following the playbook."

### Card 4: IR Playbooks (Emerald, Activity icon)

```sql
SELECT COUNT(*) as playbooks
FROM ir_playbooks;
```

"More playbooks equals more standardized responses. Fewer than five and you are improvising during incidents. Improvisation under pressure is how mistakes happen. I know. I have made those mistakes."

### Card 5: IOCs Tracked (Yellow, Eye icon)

```bash
curl -s http://localhost:3000/threatintel/stats \
  -H "Authorization: Bearer $TOKEN"
```

```json
{
  "total_feeds": 5,
  "total_iocs": 1247,
  "total_actors": 23,
  "total_reports": 8
}
```

```sql
SELECT COUNT(*) as total_iocs FROM threat_iocs;
```

"Growing means your feeds are working and analysts are contributing. Declining means feeds are failing. Flat means no one is adding manual IOCs and your automated ingestion might be stale."

### Card 6: Threat Feeds (Blue, Radio icon)

```sql
SELECT COUNT(*) as total_feeds FROM threat_feeds WHERE status = 'active';
```

"Quality over quantity. Five well-curated feeds beat fifty noisy ones. But you need at least three active at all times. CISA KEV, MITRE ATT&CK, and your sector ISAC."

---

## The KPI Card Component

Clara pulled up the component code. She liked looking at the code. She said it grounded the abstraction.

```typescript
function KpiCard({ label, value, color, icon }: {
  label: string;
  value: string | number;
  color: string;
  icon: React.ReactNode;
}) {
  const colorMap: Record<string, string> = {
    red:     "text-red-400 border-red-900/50 bg-red-900/10",
    orange:  "text-orange-400 border-orange-900/50 bg-orange-900/10",
    emerald: "text-emerald-400 border-emerald-900/50 bg-emerald-900/10",
    blue:    "text-blue-400 border-blue-900/50 bg-blue-900/10",
    yellow:  "text-yellow-400 border-yellow-900/50 bg-yellow-900/10",
  };
  return (
    <div className={`border rounded-xl p-3 ${colorMap[color] || ""}`}>
      <div className="flex items-center gap-1.5 mb-1">
        {icon}
        <p className="text-[10px] text-slate-500 uppercase tracking-wide">{label}</p>
      </div>
      <p className="text-xl font-bold font-mono">{value}</p>
    </div>
  );
}
```

"Icon and label on top -- tiny uppercase. Big monospace number below. Border and background at ten percent opacity of the accent color. Subtle tinted card. Clean, scannable, readable from four feet away."

"I designed this for readability," I said. "But you are the one who told me to make the numbers monospace."

"Proportional fonts make zeros look like capital O's at a glance," she said. "Monospace eliminates ambiguity. Details matter."

---

## Severity Distribution Pie Chart

The first chart in the row. A donut showing findings by severity.

```typescript
const total = incidentStats?.active_incidents ?? 10;
const severityData = [
  { name: "Critical", value: Math.max(1, Math.round(total * 0.1)),  color: "#ef4444" },
  { name: "High",     value: Math.max(1, Math.round(total * 0.25)), color: "#f97316" },
  { name: "Medium",   value: Math.max(1, Math.round(total * 0.4)),  color: "#eab308" },
  { name: "Low",      value: Math.max(1, Math.round(total * 0.25)), color: "#22c55e" },
];
```

Clara pointed at the colors.

- **Critical** (#ef4444 / red-500): Actively exploitable. Immediate action.
- **High** (#f97316 / orange-500): Significant risk. Action within 24 hours.
- **Medium** (#eab308 / yellow-500): Moderate risk. Action within 1 week.
- **Low** (#22c55e / green-500): Minimal risk. Next maintenance window.

The recharts component:

```typescript
<ResponsiveContainer width="100%" height={180}>
  <PieChart>
    <Pie
      data={severityData}
      cx="50%" cy="50%"
      innerRadius={45}
      outerRadius={70}
      paddingAngle={3}
      dataKey="value"
    >
      {severityData.map((entry, idx) => (
        <Cell key={idx} fill={entry.color} />
      ))}
    </Pie>
    <Tooltip contentStyle={{
      backgroundColor: "#1e293b",
      border: "1px solid #334155",
      borderRadius: "8px",
      fontSize: "12px"
    }} />
  </PieChart>
</ResponsiveContainer>
```

"Hover any slice for the exact count," Clara said. "A mostly-red and orange chart means you have urgent work. A mostly-green chart means your posture is healthy."

She tapped the red slice on the screen.

"During PHANTOM MERCY, this pie was seventy percent red for nine straight days. That was the worst visualization I have ever seen. But it told us the truth. The truth is the only thing the dashboard should ever tell you."

"On Monday morning," she continued, "if the red slice is larger than last week, investigate immediately. Open Findings, filter by Critical. Something changed."

To get the raw data via API:

```bash
curl -s http://localhost:3000/campaigns/CAMPAIGN_ID/findings \
  -H "Authorization: Bearer $TOKEN" | python -c "
import json, sys
data = json.load(sys.stdin)
counts = {}
for f in data:
    s = f['severity']
    counts[s] = counts.get(s, 0) + 1
for k, v in sorted(counts.items()):
    print(f'{k}: {v}')
"
```

---

## 7-Day Activity Trend

The middle chart. Two overlapping gradient areas.

```typescript
const activityData = Array.from({ length: 7 }, (_, i) => {
  const d = new Date();
  d.setDate(d.getDate() - (6 - i));
  return {
    day: d.toLocaleDateString(undefined, { weekday: "short" }),
    incidents: Math.max(0, (incidentStats?.active_incidents ?? 2) + Math.floor(Math.random() * 3 - 1)),
    findings: Math.max(0, (campaignList.length || 3) + Math.floor(Math.random() * 4 - 2)),
  };
});
```

The gradients:

```typescript
<defs>
  <linearGradient id="gradIncidents" x1="0" y1="0" x2="0" y2="1">
    <stop offset="5%"  stopColor="#f97316" stopOpacity={0.3} />
    <stop offset="95%" stopColor="#f97316" stopOpacity={0} />
  </linearGradient>
  <linearGradient id="gradFindings" x1="0" y1="0" x2="0" y2="1">
    <stop offset="5%"  stopColor="#3b82f6" stopOpacity={0.3} />
    <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
  </linearGradient>
</defs>
```

Orange for incidents. Blue for findings. Both fade to transparent at the bottom.

Clara leaned forward and pointed at the chart.

"This is where I spend the most time," she said. "Not because it is the most informative chart -- the pie is simpler and the bar is more actionable. But because this one shows tempo. It shows rhythm."

She traced the orange line with her finger.

"A steady line means normal operations. A spike means something happened. But look at the shape of the spike -- is it sharp, one day, then back down? That is an event. A scan completed, a feed ingested, a real incident contained quickly. Is it a ramp, climbing over three or four days? That is a trend. That is worse. That means something is building."

"What about the day you lost contact with me?" I asked. I did not plan to say it. It just came out.

Clara was quiet for a moment. "The day I went dark, both lines spiked simultaneously. Orange and blue, together, straight up. That is the worst shape this chart can draw. Correlated spikes mean a real attack or a real crisis. Not a scan. Not a feed. Something happening in the world."

She paused again. "The team told me they stared at this chart for eleven hours straight that first night. Every time the orange line ticked up, it meant another incident declared. Every blue tick meant another finding. They were mapping the network that had me."

I reached over and put my hand on hers. She let it stay.

**Spotting anomalies:**
- A sudden spike on one day = something happened (new scan results, real incident, feed import)
- Incidents and findings spiking together = correlated event (real attack or large campaign)
- Incidents spiking but findings flat = incidents from non-campaign sources (alerts, SIEM)
- Findings spiking but incidents flat = scan campaign completed (expected)
- Declining trend = defenses improving or campaigns concluding

---

## Campaign Pipeline Bar Chart

The right chart. Campaigns by status.

```typescript
const statusCounts = campaignList.reduce(
  (acc, c) => { acc[c.status] = (acc[c.status] || 0) + 1; return acc; },
  {} as Record<string, number>
);

const campaignStatusData = [
  { name: "Draft",      count: statusCounts["Draft"] || 0 },
  { name: "Authorized", count: statusCounts["Authorized"] || 0 },
  { name: "Executing",  count: statusCounts["Executing"] || 0 },
  { name: "Reporting",  count: statusCounts["Reporting"] || 0 },
  { name: "Closed",     count: statusCounts["Closed"] || 0 },
];
```

```typescript
<BarChart data={campaignStatusData} barSize={28}>
  <XAxis dataKey="name" stroke="#475569" tick={{ fontSize: 9, fill: "#64748b" }} />
  <YAxis stroke="#475569" tick={{ fontSize: 10, fill: "#64748b" }} allowDecimals={false} />
  <Tooltip contentStyle={{...}} />
  <Bar dataKey="count" fill="#6366f1" radius={[4, 4, 0, 0]} />
</BarChart>
```

Indigo bars with rounded tops.

**The campaign lifecycle:**

1. **Draft** -- Created but not authorized. Scope written, no approval yet.
2. **Authorized** -- Approved to begin. Rules of engagement confirmed.
3. **Executing** -- Active assessment. Findings being generated.
4. **Reporting** -- Assessment complete, report in progress.
5. **Closed** -- Report delivered, campaign archived.

"The bottleneck is always Reporting," Clara said. "People are good at finding problems. They are less good at writing about them. If Reporting is piling up, the team needs help with documentation. That is not weakness. Writing clearly about technical findings is one of the hardest skills in this profession."

"You seem to do it fine," I said.

"I had an excellent teacher." She did not look at me when she said it, but I saw the corner of her mouth turn up.

---

## Command Palette

"Press Ctrl+K anywhere in the app," Clara said. "A search dialog appears."

| Command | Action |
|---------|--------|
| `Dashboard` | Navigate to Dashboard |
| `ADAPT` | Navigate to ADAPT |
| `Campaigns` | Navigate to Campaigns |
| `Create Campaign` | Open creation form |
| `Findings` | Navigate to Findings |
| `Incidents` | Navigate to Incidents |
| `Declare Incident` | Open incident form |
| `Threat Intel` | Navigate to Threat Intel |
| `SOAR` | Navigate to SOAR |
| `Forensics` | Navigate to Forensics |
| `Command Center` | Navigate to Command Center |
| `Red Team` | Navigate to Red Team |
| `Purple Team` | Navigate to Purple Team |
| `Compliance` | Navigate to Compliance |
| `Risk` | Navigate to Risk |
| `Metrics` | Navigate to Metrics |
| `Search IOCs` | Open IOC search |
| `AI Triage` | Open AI triage form |

"Type the first few letters and press Enter. Keyboard only. Never touch your mouse."

"You built the Command Palette after I complained about clicking through menus during an active incident," Clara said.

"I did."

"It was a good call."

---

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl+K` | Open Command Palette |
| `Ctrl+/` | Toggle sidebar |
| `Escape` | Close modal |
| `Tab` | Move through form fields |
| `Enter` | Submit form |

In tables: arrow keys to navigate, Enter to open a row, Escape to deselect.

---

## Connected Modules Panel

Twenty-three modules in a 3-column grid. Each shows a colored dot, module name, optional count, and status.

```typescript
<ModuleStatus name="Campaigns" status="connected" count={campaignList.length} />
<ModuleStatus name="Incidents" status="connected" count={incidentStats?.active_incidents} />
<ModuleStatus name="Threat Intel" status="connected" count={intelStats?.total_iocs} />
```

All 23 connected modules:

| Module | Description |
|--------|-------------|
| Campaigns | Assessment campaign management |
| Findings | Vulnerability and finding tracking |
| Evidence | Evidence locker with chain of custody |
| Labs | Isolated testing environments |
| Red Team | Offensive technique testing |
| Social Eng | Social engineering campaigns |
| AI Analysis | AI-powered triage and correlation |
| Incidents | Incident response lifecycle |
| Threat Intel | IOCs, feeds, actors, reports |
| Health | System health monitoring |
| OSINT | Open-source intelligence gathering |
| Forensics | Digital forensics and evidence |
| SOAR | Security orchestration and automation |
| Zero Trust | Zero trust architecture management |
| UEBA | User and entity behavior analytics |
| Auth | Authentication and authorization |
| Compliance | Compliance framework management |
| Reporting | Report generation and evidence packs |
| Cyber Range | Training scenarios and exercises |
| Purple Team | Collaborative attack/defense testing |
| Endpoint | EDR, file integrity, process monitoring |
| Risk | Risk register and assessments |
| Metrics | Security metrics and KPIs |

"All green," Clara said. "All live. If any module shows something other than green, investigate immediately."

She tapped the Forensics module on the screen. "This module was the one that processed the physical evidence from the Marseille compound. Disk images, phone extractions, network captures. Every artifact dual-hashed. Every access logged. When Interpol's forensic team reviewed our evidence chain, they found zero gaps. Zero."

---

## Intelligence Overview Panel

Right side panel. Clara read it like a weather report.

```typescript
<IntelRow label="Threat Feeds" value={intelStats.total_feeds} />
<IntelRow label="IOCs Tracked" value={intelStats.total_iocs} />
<IntelRow label="Threat Actors" value={intelStats.total_actors} />
<IntelRow label="Intel Reports" value={intelStats.total_reports} />
```

Below the intel rows:

**Incident MTTC** (Mean Time to Contain): `incidentStats.mean_time_to_contain_mins` in minutes. "The industry average is 280-plus minutes. If yours is under 60, you are doing well. Ours is 47 right now. During PHANTOM MERCY, it was 12 -- because we had the playbooks ready before the crisis hit."

**Active Campaigns**: Count repeated for quick reference.

### The Risk Gauge

At the bottom. Horizontal gradient bar.

```typescript
<div className="w-full h-2 bg-slate-800 rounded-full overflow-hidden">
  <div
    className="h-full rounded-full bg-gradient-to-r from-emerald-500 via-yellow-500 to-red-500"
    style={{ width: "55%" }}
  />
</div>
```

Green to yellow to red. Fill percentage = risk posture:
- 0-30%: Low risk (mostly green)
- 30-60%: Moderate risk (green to yellow)
- 60-80%: High risk (yellow to orange)
- 80-100%: Critical risk (orange to red)

Currently 55% -- Moderate.

"What changes the risk score," Clara explained. "Active incidents, unacknowledged exposures, pending defense actions, stale campaigns, failing compliance controls. Each factor contributes. When I was missing, this gauge hit ninety-one percent. The highest it has ever been."

"I remember," I said.

"I know you do."

---

## Active Campaigns List

Panel showing the first six campaigns with status badges.

```typescript
{campaignList.slice(0, 6).map((c) => (
  <div key={c.id} className="flex items-center justify-between px-3 py-2 bg-slate-800/30 rounded-lg">
    <span className="text-sm text-slate-300">{c.name}</span>
    <CampaignBadge status={c.status} />
  </div>
))}
```

Badge colors:

```typescript
const colors: Record<string, string> = {
  Draft:      "bg-slate-700 text-slate-300",
  Authorized: "bg-blue-900/50 text-blue-300",
  Executing:  "bg-amber-900/50 text-amber-300",
  Reporting:  "bg-purple-900/50 text-purple-300",
  Closed:     "bg-green-900/50 text-green-300",
};
```

If no campaigns exist:

```
No campaigns — connect to API to begin
Press Ctrl+K then type "Create Campaign"
```

---

## Platform Capabilities Panel

Static stats about the platform.

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

Below: Evidence Hashing = `BLAKE3 + SHA-256` (dual-hash, court-grade). Auth = `JWT + RBAC (5 roles, 16 perms)`.

"This panel is for stakeholders who ask 'how big is this platform?'" Clara said. "Point them here. Then show them the Dashboard. Then ask them what they want to protect."

---

## Data Loading Pattern

Clara showed me the loading logic. She had been studying the code.

```typescript
useEffect(() => {
  health.check().then(setHealthStatus).catch(() => setError("Backend unreachable"));
  campaigns.list().then(setCampaignList).catch(() => {});
  incidents.stats().then(setIncidentStats).catch(() => {});
  threatIntel.stats().then(setIntelStats).catch(() => {});
  const timer = setInterval(() => setClock(new Date()), 1000);
  return () => clearInterval(timer);
}, []);
```

Four parallel API calls on mount:
1. `GET /health` -- system health
2. `GET /campaigns` -- campaign list
3. `GET /incident/stats` -- incident statistics
4. `GET /threatintel/stats` -- threat intelligence statistics

"Each call is independent," she said. "If one fails, the others still render. The health check failure shows the red error banner. Other failures show zeros instead of errors. Graceful degradation."

"You really have been studying the code," I said.

"I study everything that matters."

---

## The Monday Morning Briefing: How Clara Does It

She turned to me and said, "Let me show you how I do my morning briefing. Time me."

I looked at my watch. "Go."

### Minute 0:00 -- Health Check

Eyes go to the health strip first. Four green pills. Good. Move on. Any red? Stop everything and fix it.

```bash
curl -s http://localhost:3000/health | python -m json.tool
```

### Minute 0:15 -- KPI Scan

Left to right across the cards.

"Campaigns: same as yesterday? Incidents: up or down? If up, I stop here. Open Incidents immediately. Containment actions: any new ones? IOCs: growing? Feeds: all active?"

### Minute 0:45 -- Chart Analysis

"Severity pie: more red than last week? Why. 7-day trend: any weekend spikes? Campaign pipeline: anything stuck in Reporting?"

### Minute 1:15 -- Intelligence Overview

"MTTC -- better or worse? IOC growth rate -- healthy is fifty-plus per day from automated feeds."

### Minute 1:30 -- Module Check

"All twenty-three green? Good. Any not green? Click through to that module."

### Minute 2:00 -- Active Campaigns

"Status changes since yesterday? Any moved from Executing to Reporting?"

She looked at me. "How long?"

"One minute, fifty-three seconds."

"Under two minutes. Every day. Same sequence. Muscle memory."

She closed her journal and looked at the dashboard one more time.

"You built this," she said.

"We built it," I said. "The MTTC optimization was your idea. The risk gauge was your design. The command palette, your complaint."

She laughed softly. "My complaint."

"The best features come from complaints."

---

## Customizing via Command Center

Clara showed me how she had customized her setup through the Command Center.

**Custom widget:**

```bash
curl -s -X POST http://localhost:3000/command/widgets \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Top 5 Critical IOCs",
    "widget_type": "ioc_list",
    "config": {"severity": "critical", "limit": 5}
  }'
```

**Threat level:**

```bash
curl -s -X POST http://localhost:3000/command/threat-level \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "level": "elevated",
    "reason": "CVE-2026-1234 actively exploited in the wild"
  }'
```

Threat levels: `low`, `guarded`, `elevated`, `high`, `severe`.

**Threat level history:**

```bash
curl -s http://localhost:3000/command/threat-level/history \
  -H "Authorization: Bearer $TOKEN"
```

"Every change logged," Clara said. "Who changed it, when, and why. Complete audit trail."

---

## Global Search

```bash
curl -s -X POST http://localhost:3000/command/search \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query": "lateral movement"}'
```

```json
{
  "results": [
    {"type": "incident", "id": "...", "title": "Suspected Lateral Movement - CORP-WS-047"},
    {"type": "technique", "id": "T1021", "title": "Remote Services"},
    {"type": "ioc", "id": "...", "value": "psexec.exe"}
  ],
  "count": 3
}
```

Search indexes across campaigns, findings, incidents, IOCs, techniques, playbooks, and more.

**Search history:**

```bash
curl -s http://localhost:3000/command/search/history \
  -H "Authorization: Bearer $TOKEN"
```

"Every search is logged," Clara said. "You can see what your team has been looking for. The patterns in their searches tell you what is worrying them."

---

## Metrics Dashboard

For deeper metrics, the Metrics page.

**Executive Dashboard:**

```bash
curl -s http://localhost:3000/metrics/dashboard/executive \
  -H "Authorization: Bearer $TOKEN"
```

**Operational Dashboard:**

```bash
curl -s http://localhost:3000/metrics/dashboard/operational \
  -H "Authorization: Bearer $TOKEN"
```

**KPIs:**

```bash
curl -s http://localhost:3000/metrics/kpis \
  -H "Authorization: Bearer $TOKEN"
```

```json
[
  {"id": "...", "name": "MTTD", "target": 30, "current": 22, "unit": "minutes", "status": "on_track"},
  {"id": "...", "name": "MTTC", "target": 60, "current": 47, "unit": "minutes", "status": "on_track"},
  {"id": "...", "name": "Coverage", "target": 85, "current": 72, "unit": "percent", "status": "at_risk"}
]
```

**MTTR/MTTD Reports:**

```bash
curl -s http://localhost:3000/metrics/reports/mttr -H "Authorization: Bearer $TOKEN"
curl -s http://localhost:3000/metrics/reports/mttd -H "Authorization: Bearer $TOKEN"
```

**Threshold Violations:**

```bash
curl -s http://localhost:3000/metrics/thresholds/violations \
  -H "Authorization: Bearer $TOKEN"
```

"If any metric crosses its threshold, it appears here," Clara said. "Your early warning system. The dashboard tells you the present. Thresholds tell you the future."

---

## Reporting from the Dashboard

```bash
curl -s -X POST http://localhost:3000/reporting/generate \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Weekly Security Posture Report - W8 2026",
    "report_type": "executive_summary",
    "format": "pdf"
  }'
```

```json
{
  "id": "report-...",
  "status": "generating"
}
```

**List reports:**

```bash
curl -s http://localhost:3000/reporting/reports \
  -H "Authorization: Bearer $TOKEN"
```

**Reporting dashboard:**

```bash
curl -s http://localhost:3000/reporting/dashboard \
  -H "Authorization: Bearer $TOKEN"
```

```json
{
  "total_reports": 12,
  "total_evidence_packs": 3,
  "frameworks": 7,
  "recent_reports": [...]
}
```

---

## The Dashboard Philosophy

It was past midnight. The coffee was gone. The building was silent except for the hum of the servers in the next room and the soft tick of the dashboard clock.

Clara saved her journal entry and closed the notebook. She looked at the three screens one more time.

"The Dashboard is not a vanity page with pretty charts," she said. "It is an operational tool. Every element is there because an analyst needs it during their first two minutes of the day. Nothing extra. Nothing missing."

The hierarchy:
1. **Is the system working?** (Health strip -- 2 seconds)
2. **What are the critical numbers?** (KPIs -- 10 seconds)
3. **How are things trending?** (Charts -- 30 seconds)
4. **What is active?** (Modules + campaigns -- 60 seconds)
5. **What needs attention?** (Intelligence + risk gauge -- 30 seconds)

"Master this flow," she said, "and your morning briefing becomes a two-minute ritual that keeps you ahead of every threat."

She turned off the monitors, one by one. The room went dark except for the emergency exit light near the door and the glow of the hallway beyond.

"Thank you for coming tonight," she said.

"I did not do anything. I just watched."

"You brought me coffee." She picked up the empty mug. "And you let me talk. Sometimes I need to talk through what I am seeing. The dashboard shows me data. Talking shows me what the data means."

We walked out together, down the dark hallway, our footsteps the only sound. At the elevator, she pressed the button and we stood side by side, waiting.

"Same time tomorrow?" I asked.

"Same time every night until I run out of things to teach you."

"That could take a while."

"Yes," Clara said. "It could."

The elevator doors opened. We stepped in. And for a moment, in the fluorescent light of the elevator car, I saw her clearly -- the scar on her forearm, the reading glasses pushed up on her head, the shadow of exhaustion under her eyes, and behind all of it, the sharpest mind I had ever worked alongside, alive and present and here, studying a dashboard like it was a map to the future.

Which, in a way, it was.

---

*Next chapter: we dive into Threat Intelligence -- Clara's approach to understanding adversaries. Start with the human. Work backwards through the technical.*

---

© 2026 Playseat — All Rights Reserved | Defensive Intelligence Through ADAPT
