# Chapter 33 — Mastering Threat Intel: The Way Clara Thinks

Clara had a rule about threat intelligence that she repeated to every new analyst until they could recite it without thinking.

"Start with the human. Why would someone do this? Then work backwards through the technical."

The first time she said it to me, we were in a rented apartment in Lisbon, four days after the rescue, debriefing over takeout and cheap wine. Her hands were still shaking from the cortisol withdrawal -- eleven weeks of fight-or-flight does things to the nervous system that do not undo themselves quickly -- but her mind was running clean. She had a notebook open and she was diagramming the PHANTOM MERCY network from memory, reconstructing every link between every actor, every node, every money flow, and she kept stopping to ask a question that had nothing to do with the technical evidence.

"Why did they move me to Marseille instead of directly across the Mediterranean?"

"Logistics," I said. "The shipping route."

"No. Think about the human. The person who made that decision. Why Marseille?"

I stared at the diagram. Then I saw it. "Because the handler in Marseille was the one with the corrupt port official. Personal relationship. They trusted him specifically."

"Now you have a target," Clara said. "Not an IP address. A person with a relationship and a reason."

That was the Clara method. Start with the human. Work backwards through the technical. And it changed the way I thought about every piece of intelligence that ever passed through this platform.

---

## The Threat Intel Page

Navigate to **Intelligence > Threat Intel** or go directly to `http://localhost:1420/threat-intel`.

Five tabs across the top:

| Tab | What it does |
|-----|-------------|
| **Indicators** | IOC management -- create, search, import, enrich |
| **Feeds** | Threat feed management -- add, poll, enable/disable |
| **Reports** | Intelligence reports -- create, view, share |
| **STIX** | STIX object browser -- indicators, malware, actors, attack patterns |
| **Actors** | Threat actor profiles -- aliases, campaigns, sophistication |

Clara and I worked through every one of these tabs together in the weeks after PHANTOM MERCY. We were processing the aftermath: debrief sessions, threat profile updates, detection rule creation, the patient and exhausting work of turning a crisis into institutional knowledge. Every night, after the academy students went home, we would sit in Lab Two and process another piece of the puzzle.

Here is what we built. Here is how it works.

---

## Part 1: Feed Management

Click the **Feeds** tab. The seed data shows:

| Feed | Type | Status | Poll Interval |
|------|------|--------|--------------|
| CISA Known Exploited Vulnerabilities | TAXII 2.1 | Active | Every hour |
| MITRE ATT&CK STIX | TAXII 2.1 | Active | Daily |
| AlienVault OTX STIX Feed | TAXII 2.0 | Disabled | Every 2 hours |
| FS-ISAC Threat Indicators | TAXII 2.1 | Active | Every 30 minutes |

### Adding a Feed

"Feeds are your automated eyes," Clara told the class. "They watch when you sleep."

In the UI, click "Add Feed." Or via API:

```bash
curl -s -X POST http://localhost:3000/threatintel/feeds \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "MITRE ATT&CK STIX",
    "feed_type": "stix",
    "url": "https://cti-taxii.mitre.org/taxii2",
    "poll_interval_secs": 86400
  }'
```

```json
{
  "id": "feed-01953b10-...",
  "status": "created"
}
```

An AlienVault OTX feed:

```bash
curl -s -X POST http://localhost:3000/threatintel/feeds \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "AlienVault OTX",
    "feed_type": "stix",
    "url": "https://otx.alienvault.com/taxii2",
    "poll_interval_secs": 7200
  }'
```

A custom internal feed for your team's manual IOCs:

```bash
curl -s -X POST http://localhost:3000/threatintel/feeds \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Internal Threat Team - Manual IOCs",
    "feed_type": "custom",
    "poll_interval_secs": 0
  }'
```

Poll interval of zero means manual-only. No automated polling. Your team pushes IOCs by hand.

### Polling a Feed

Manually trigger a poll:

```bash
FEED_ID="feed-01953b10-..."

curl -s -X POST http://localhost:3000/threatintel/feeds/$FEED_ID/poll \
  -H "Authorization: Bearer $TOKEN"
```

```json
{
  "id": "feed-01953b10-...",
  "status": "polling"
}
```

"During PHANTOM MERCY," Clara said, "we added a private feed from the DGSE's counter-trafficking unit. Poll interval of fifteen minutes. Every quarter-hour, new IOCs from French intelligence flowed into our platform automatically. That feed gave us the Marseille port official's phone number. A phone number that led to a shipping manifest. A manifest that led to a container. A container that led to me."

She said it plainly, like a fact. Not for sympathy. For instruction.

### Viewing and Managing Feeds

```bash
# View a specific feed
curl -s http://localhost:3000/threatintel/feeds/$FEED_ID \
  -H "Authorization: Bearer $TOKEN"

# List all STIX feeds with details
curl -s http://localhost:3000/stix-feeds \
  -H "Authorization: Bearer $TOKEN"

# View STIX objects from a feed
curl -s http://localhost:3000/stix-feeds/$FEED_ID/objects \
  -H "Authorization: Bearer $TOKEN"

# Feed statistics
curl -s http://localhost:3000/stix-feeds/stats \
  -H "Authorization: Bearer $TOKEN"
```

---

## Part 2: IOC Management

Click the **Indicators** tab. This is where all Indicators of Compromise live.

Clara's approach to IOCs was methodical and human-centered. She did not just record what she found. She recorded why it mattered.

### Creating IOCs

**IP Address:**

```bash
curl -s -X POST http://localhost:3000/threatintel/iocs \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "ioc_type": "ip_address",
    "value": "198.51.100.42",
    "confidence": "high",
    "threat_actor": "APT-PHANTOM",
    "tags": ["c2", "cobalt-strike"]
  }'
```

**Domain:**

```bash
curl -s -X POST http://localhost:3000/threatintel/iocs \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "ioc_type": "domain",
    "value": "malware-c2.example.net",
    "confidence": "high",
    "tags": ["dns-tunneling", "exfiltration"]
  }'
```

**File Hash:**

```bash
curl -s -X POST http://localhost:3000/threatintel/iocs \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "ioc_type": "file_hash",
    "value": "sha256:a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2",
    "confidence": "medium",
    "threat_actor": "BlackCat",
    "tags": ["ransomware", "alphv"]
  }'
```

**Email:**

```bash
curl -s -X POST http://localhost:3000/threatintel/iocs \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "ioc_type": "email",
    "value": "phishing-sender@evil-domain.example",
    "confidence": "medium",
    "tags": ["phishing", "spear-phishing"]
  }'
```

"Notice the tags," Clara said, pointing at the screen. "Tags are not optional metadata. Tags are the connective tissue between IOCs. When you tag an IP as 'c2' and 'cobalt-strike,' you are telling the next analyst -- who might be working at 3 AM, exhausted, and scared -- exactly what this IP does and what tool it runs. That context saves time. Time saves people."

### Bulk Import

```bash
curl -s -X POST http://localhost:3000/threatintel/iocs/bulk \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '[
    {"ioc_type": "ip_address", "value": "203.0.113.10", "confidence": "high"},
    {"ioc_type": "ip_address", "value": "203.0.113.11", "confidence": "high"},
    {"ioc_type": "ip_address", "value": "203.0.113.12", "confidence": "medium"},
    {"ioc_type": "domain", "value": "evil-c2-1.example.com", "confidence": "high"},
    {"ioc_type": "domain", "value": "evil-c2-2.example.com", "confidence": "high"},
    {"ioc_type": "file_hash", "value": "sha256:deadbeef01234567deadbeef01234567deadbeef01234567deadbeef01234567", "confidence": "medium"},
    {"ioc_type": "email", "value": "attacker@phish.example", "confidence": "low"}
  ]'
```

```json
{
  "imported": 7,
  "duplicates": 0
}
```

Automatic deduplication. Import the same IOC twice and duplicates increments, but no duplicate record is created.

**CSV to JSON conversion:**

```bash
python -c "
import csv, json, sys
rows = []
for r in csv.DictReader(open('iocs.csv')):
    rows.append({'ioc_type': r['type'], 'value': r['value'], 'confidence': r['confidence']})
print(json.dumps(rows))
" > iocs.json

curl -s -X POST http://localhost:3000/threatintel/iocs/bulk \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d @iocs.json
```

### Searching IOCs

```bash
# By type and confidence
curl -s -X POST http://localhost:3000/threatintel/iocs/search \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "ioc_type": "ip_address",
    "confidence_min": "high"
  }'
```

```json
{
  "results": [
    {
      "id": "...",
      "ioc_type": "ip_address",
      "value": "198.51.100.42",
      "confidence": "high",
      "threat_actor": "APT-PHANTOM",
      "tags": ["c2", "cobalt-strike"]
    }
  ],
  "total": 1
}
```

```bash
# By value (partial match)
curl -s -X POST http://localhost:3000/threatintel/iocs/search \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"value": "198.51"}'
```

```bash
# List all IOCs
curl -s http://localhost:3000/threatintel/iocs \
  -H "Authorization: Bearer $TOKEN"
```

### IOC Enrichment

Clara's favorite workflow. She called it "making the indicator talk."

**OSINT enrichment:**

```bash
curl -s -X POST http://localhost:3000/osint/search \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "target_name": "malware-c2.example.net",
    "max_results": 5
  }'
```

Searches OSINT sources: registration data, DNS records, historical hosting, related infrastructure.

**Entity resolution:**

```bash
curl -s -X POST http://localhost:3000/osint/entities/resolve \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "campaign_id": "'$CAMPAIGN_ID'",
    "target_name": "198.51.100.42"
  }'
```

Returns the IP's owner, ASN, geolocation, hosting provider, related domains.

"Enrichment is where the Clara method lives," I told the class one afternoon when she was out of the room. "Anyone can record an IP address. Clara asks who registered it, who hosts it, who pays for it, and who visits it. She turns an indicator into a biography."

She walked back in as I was saying it and gave me a look that was equal parts annoyance and affection. "Stop flattering me in front of the students."

"It is not flattery if it is operational doctrine."

---

## Part 3: Threat Actor Profiles

Click the **Actors** tab.

This is where Clara came alive. She understood adversaries the way a novelist understands characters -- from the inside.

### Viewing Actor Profiles

```bash
curl -s http://localhost:3000/actors/profiles \
  -H "Authorization: Bearer $TOKEN"
```

### Creating a Profile

```bash
curl -s -X POST http://localhost:3000/actors/profiles \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "PHANTOM BEAR",
    "actor_type": "apt",
    "origin_country": "RU",
    "motivation": "espionage",
    "sophistication": "high",
    "aliases": ["APT-PHANTOM", "GhostPaw"],
    "description": "State-sponsored APT group targeting defense industrial base"
  }'
```

Or through the Threat Intel API:

```bash
curl -s -X POST http://localhost:3000/threatintel/actors \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "PHANTOM BEAR",
    "actor_type": "apt",
    "aliases": ["APT-PHANTOM", "GhostPaw"],
    "motivation": "espionage"
  }'
```

"When you create an actor profile," Clara told the class, "you are not filling out a form. You are building a psychological model. The motivation field is not a dropdown you click. It is a hypothesis you test. Why espionage? What are they trying to learn? For whom? What would they do differently if their motivation were financial? Ask those questions, and the IOCs start making sense."

### Actor Campaigns

```bash
ACTOR_ID="actor-..."

curl -s http://localhost:3000/actors/profiles/$ACTOR_ID/campaigns \
  -H "Authorization: Bearer $TOKEN"
```

### Searching Actors

```bash
curl -s "http://localhost:3000/actors/search?name=PHANTOM&actor_type=apt" \
  -H "Authorization: Bearer $TOKEN"
```

Filter by name, type, origin country, sophistication, or motivation.

---

## Part 4: Intelligence Reports

Click the **Reports** tab.

### Creating a Report

Clara and I wrote the PHANTOM MERCY debrief report together over the course of three nights. It was the hardest thing I have ever written, because the facts were tangled with emotions I did not want to examine, and Clara insisted on clarity above all else.

"The report is for the next analyst," she said. "Not for us. Write it so someone who was not there can understand everything."

```bash
curl -s -X POST http://localhost:3000/threatintel/reports \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "PHANTOM MERCY Network Analysis - February 2026",
    "summary": "Analysis of trafficking network dismantled in Operation PHANTOM MERCY. Key actors, infrastructure, financial flows, and technical indicators documented for future detection. 47 victims recovered. 12 arrests across 4 jurisdictions.",
    "confidence": "high",
    "tlp_level": "amber"
  }'
```

```json
{
  "id": "report-01953b30-...",
  "status": "created"
}
```

**TLP levels** (Traffic Light Protocol):
- `white` -- Unlimited distribution
- `green` -- Community-wide distribution
- `amber` -- Limited distribution (need-to-know)
- `red` -- Named recipients only

"PHANTOM MERCY was TLP:AMBER," Clara said. "Need-to-know. Because the techniques we used to find the network are also the techniques someone else could use to rebuild it. Intelligence reports are weapons. Handle them accordingly."

### Listing Reports

```bash
curl -s http://localhost:3000/threatintel/reports \
  -H "Authorization: Bearer $TOKEN"
```

---

## Part 5: STIX Object Browser

Click the **STIX** tab. All STIX objects ingested from feeds.

| STIX Type | Description | Example |
|-----------|-------------|---------|
| `indicator` | Observable pattern for detection | Malicious IP indicator |
| `malware` | Malware definition | BlackCat Ransomware |
| `attack-pattern` | ATT&CK technique | T1566.001 Spearphishing |
| `threat-actor` | Adversary group | APT29 (Cozy Bear) |
| `vulnerability` | CVE or weakness | CVE-2026-1234 |
| `campaign` | Named adversary campaign | Operation Dark Horizon |
| `relationship` | Link between objects | "uses" / "targets" |

### Threat Genome

The Genome feature creates behavioral DNA fingerprints from STIX data:

```bash
curl -s -X POST http://localhost:3000/api/v1/adapt/genome/genomes \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "PHANTOM MERCY Network Genome",
    "threat_actor": "PHANTOM_MERCY",
    "confidence": 85
  }'
```

Add markers:

```bash
GENOME_ID="genome-01953b40-..."

# TTPs marker
curl -s -X POST http://localhost:3000/api/v1/adapt/genome/genomes/$GENOME_ID/markers \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "marker_type": "ttp",
    "marker_value": "T1566.001:T1059.001:T1021.002:T1048.003",
    "weight": 0.9
  }'

# Infrastructure marker
curl -s -X POST http://localhost:3000/api/v1/adapt/genome/genomes/$GENOME_ID/markers \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "marker_type": "infrastructure",
    "marker_value": "cobalt-strike:cloudflare-tunnel:tor-exit",
    "weight": 0.7
  }'
```

"I built the PHANTOM MERCY genome after we dismantled the network," Clara said. "Every technique they used, every infrastructure pattern, every behavioral fingerprint. Now if anyone sets up a similar network -- same TTPs, same infrastructure choices, same operational tempo -- the genome matcher will flag it. We turned the worst experience of my life into a detection rule."

She said it without bitterness. She said it like an engineer describing a bridge she built over a river that once drowned someone.

---

## Part 6: SIGMA Rules

SIGMA rules are vendor-agnostic detection rules.

### Writing a SIGMA Rule

Here is one Clara wrote for detecting the lateral movement pattern used in PHANTOM MERCY:

```yaml
title: PsExec Remote Execution
id: sigma-rule-psexec-001
status: experimental
level: high
description: Detects PsExec service installation indicating lateral movement
logsource:
  category: process_creation
  product: windows
detection:
  selection:
    EventID: 1
    Image|endswith:
      - '\PSEXESVC.exe'
      - '\psexec.exe'
    User|endswith:
      - 'SYSTEM'
  condition: selection
falsepositives:
  - Legitimate admin usage of PsExec
tags:
  - attack.lateral_movement
  - attack.t1021.002
  - attack.execution
```

### Testing with Sentinel

```bash
curl -s -X POST http://localhost:3000/api/v1/adapt/sentinel/rules \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "PsExec Remote Execution Detection",
    "condition": "process_name contains psexec AND user = SYSTEM",
    "threshold": 1,
    "severity": "high"
  }'
```

```bash
curl -s -X POST http://localhost:3000/api/v1/adapt/sentinel/detect \
  -H "Authorization: Bearer $TOKEN"
```

```json
{
  "anomalies_detected": 3
}
```

```bash
curl -s http://localhost:3000/api/v1/adapt/sentinel/alerts \
  -H "Authorization: Bearer $TOKEN"
```

Acknowledge and resolve:

```bash
ALERT_ID="alert-..."

curl -s -X POST http://localhost:3000/api/v1/adapt/sentinel/alerts/$ALERT_ID/acknowledge \
  -H "Authorization: Bearer $TOKEN"

curl -s -X POST http://localhost:3000/api/v1/adapt/sentinel/alerts/$ALERT_ID/resolve \
  -H "Authorization: Bearer $TOKEN"
```

---

## Part 7: YARA Rules

YARA rules for malware identification.

### Writing a Rule

```yara
rule BlackCat_ALPHV_Ransomware {
    meta:
        description = "Detects BlackCat/ALPHV ransomware indicators"
        author = "Playseat Threat Team"
        date = "2026-02-18"
        reference = "Internal Analysis"
        severity = "critical"
        tlp = "amber"

    strings:
        $s1 = "access_token" ascii wide
        $s2 = "--access-token" ascii
        $s3 = "encrypt" ascii wide
        $s4 = ".onion" ascii
        $s5 = "bcdedit" ascii wide

        $hex1 = { 48 8B 05 ?? ?? ?? ?? 48 89 44 24 }

    condition:
        uint16(0) == 0x5A4D and
        filesize < 5MB and
        3 of ($s*) and
        $hex1
}
```

### Genome Matching

```bash
curl -s -X POST http://localhost:3000/api/v1/adapt/genome/match \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "sample_hash": "sha256:a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2"
  }'
```

### Clustering

```bash
curl -s -X POST http://localhost:3000/api/v1/adapt/genome/cluster \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"algorithm": "dbscan"}'
```

```bash
curl -s http://localhost:3000/api/v1/adapt/genome/clusters \
  -H "Authorization: Bearer $TOKEN"
```

---

## Part 8: The Real Workflow -- Processing PHANTOM MERCY

This is not a hypothetical. This is how Clara and I processed the aftermath of the operation, night by night, in Lab Two, building the threat intelligence that would protect the next person.

### Night 1: Feed Integration

We added the DGSE's counter-trafficking feed and the Interpol maritime feed. We set both to poll every fifteen minutes. Within the first hour, 847 new IOCs appeared in the system.

```bash
curl -s http://localhost:3000/threatintel/stats \
  -H "Authorization: Bearer $TOKEN"
```

### Night 2: IOC Triage

Clara went through every single IOC. She tagged them by function -- c2, logistics, financial, communication, recruitment. She added context notes to each one. She worked for six hours straight. I brought her dinner and she forgot to eat it.

"Every IOC is a person's decision," she said at 2 AM, eyes red, voice hoarse. "This IP address was chosen by someone. This domain was registered by someone. This email was created by someone. When you tag an IOC, you are mapping a human's choices."

### Night 3: Actor Profiles

We built profiles for seven actors in the PHANTOM MERCY network. Clara insisted on writing each description herself.

```bash
curl -s -X POST http://localhost:3000/actors/profiles \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "PHANTOM MERCY Handler Alpha",
    "actor_type": "criminal",
    "origin_country": "Multiple",
    "motivation": "financial",
    "sophistication": "medium",
    "description": "Primary logistics coordinator. Controls shipping manifests and port access. Relationship-dependent -- operates through personal trust networks rather than technical infrastructure."
  }'
```

"Notice the description," she said. "Relationship-dependent. That is the vulnerability. Not a CVE. Not a misconfiguration. A human trait that we can exploit defensively. If we ever see this pattern again -- personal trust networks, relationship-based logistics, low technical sophistication but high social engineering -- we know what we are looking at."

### Night 4: Detection Rules

Clara wrote twelve SIGMA rules based on the TTPs we observed. Network beaconing patterns. DNS tunneling signatures. Encrypted communication intervals. Financial transaction anomalies. Each rule was tested against the historical data from the investigation.

### Night 5: The Report

We wrote the final intelligence report together. TLP:AMBER. Forty-seven pages. It covered the full network: actors, infrastructure, financial flows, operational patterns, detection indicators, and lessons learned. Clara wrote the executive summary. I wrote the technical appendix.

At the end, she added one line to the lessons learned section: "Human intelligence and technical intelligence must be treated as equal and complementary. Neither is sufficient alone."

I read it and I did not change a word.

### Night 6: Threat Level Reset

With the network dismantled and detection rules in place, we lowered the threat level:

```bash
curl -s -X POST http://localhost:3000/command/threat-level \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "level": "guarded",
    "reason": "PHANTOM MERCY network dismantled. Detection rules active. Monitoring for reconstitution."
  }'
```

That was the first night Clara did not have nightmares. I know because I was sleeping on the couch in the apartment next door, and for the first time in weeks, I did not hear her wake up screaming at 3 AM.

---

## Feed Health Monitoring

```bash
# List all feeds
curl -s http://localhost:3000/threatintel/feeds \
  -H "Authorization: Bearer $TOKEN"

# Feed statistics
curl -s http://localhost:3000/stix-feeds/stats \
  -H "Authorization: Bearer $TOKEN"
```

**Troubleshooting feeds:**
1. Check the URL is accessible
2. Check the TAXII version matches
3. Check authentication requirements
4. Check poll interval -- very frequent polling may be rate-limited

---

## Actor Statistics

```bash
curl -s http://localhost:3000/actors/stats \
  -H "Authorization: Bearer $TOKEN"
```

Aggregate statistics: total count, breakdown by type, top active actors, recent additions.

---

## Threat Intel Statistics

```bash
curl -s http://localhost:3000/threatintel/stats \
  -H "Authorization: Bearer $TOKEN" | python -m json.tool
```

```json
{
  "total_feeds": 5,
  "total_iocs": 1254,
  "total_actors": 24,
  "total_reports": 9
}
```

"Track these numbers daily," Clara said. "They should be growing. Flat means stagnation. Declining means failure. Growing means your intelligence capability is maturing."

---

## The Threat Intel Hierarchy

Clara drew this on the whiteboard during her third lecture. It became the diagram the students referenced most.

1. **Feeds** -- Automated ingestion of structured threat data (STIX/TAXII)
2. **IOCs** -- Individual indicators extracted from feeds or added manually
3. **Actors** -- Adversary profiles linking IOCs to groups with TTPs
4. **Reports** -- Human-written analysis tying everything together
5. **SIGMA/YARA** -- Detection rules derived from intelligence
6. **Sentinel** -- Automated detection using those rules
7. **Genome** -- Behavioral DNA fingerprinting for attribution

"Each layer feeds the next," she said. "Feeds produce IOCs. IOCs link to actors. Actors inform reports. Reports drive detection rules. Rules trigger alerts. Alerts become incidents. Incidents generate lessons. Lessons improve your feeds and rules."

She drew a circle connecting the last point back to the first.

"The cycle never stops."

Then she drew a stick figure in the center of the circle and labeled it "analyst."

"You are at the center. The technology is the circle. You are the point. Never forget that."

---

The students left. Clara erased the whiteboard. I was still sitting in the back row.

"You added something to the hierarchy that I never had," I said.

"What?"

"The stick figure. The human at the center."

"Because that is the part you always forget," she said. "You build beautiful systems. Elegant code. Perfect architecture. But you forget that the system exists for a person. A person who is tired, or scared, or overwhelmed. The interface is not the dashboard. The interface is the analyst's eyes. Design for their exhaustion, and everything else follows."

She picked up her bag and walked toward the door.

"Coming?" she said.

"Always."

We walked out together into the evening. The academy was quiet. The parking lot was empty except for our two cars, parked side by side, the way they always were now.

---

*Next chapter: Incident Response -- what I learned from losing Clara. The worst night of my career, and the procedures it taught me.*

---

© 2026 Playseat — All Rights Reserved | Defensive Intelligence Through ADAPT
