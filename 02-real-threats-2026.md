# Chapter 2: Real Threats 2026 -- The World That Took Clara

**Playseat Advanced Field Manual -- Book 2**
**Threat Intelligence Briefing: January-February 2026**

---

> "In the field, the map is never the territory. But without a map, you walk into minefields."
> -- Clara Dubois, encrypted voice message, March 2025

---

## 2.1 -- The Archive

Three days after I finished building Playseat, a package arrived at my apartment in Brussels.

It was a 2TB external hard drive, shipped from a PO Box in Marseille with no return address. The customs declaration said "personal effects." The drive was encrypted with a 256-bit AES key, and the only reason I could open it was that Clara and I had established a shared key-derivation scheme during DEFCON 31 -- a private joke turned operational security protocol. The passphrase was the first words I'd ever said to her, concatenated with the timestamp of her talk in the DEFCON schedule, hashed through BLAKE3.

The drive contained Clara's research archive. Two years of work. Threat analyses, network maps, IOC collections, interview transcripts, and satellite imagery with metadata that suggested she'd had access to geospatial intelligence feeds well beyond what a civilian NGO cryptographer should possess.

There was a text file at the root of the drive, unencrypted, named `READ_FIRST.txt`:

```
If you're reading this, I've been compromised.
Everything below is organized by threat category.
Every threat I documented connects to PHANTOM MERCY.
The children are the mission. Don't lose sight of that.
Trust the evidence. Trust the math. Don't trust anyone else.

-- C
```

I spent the next 72 hours reading her archive. What follows in this chapter is the real 2026 threat landscape -- every major event, every APT campaign, every emerging attack vector that shaped the platform -- but now I'm going to tell it the way Clara documented it. Through the lens of someone who lived inside these threats. Who saw them not from a SOC desk in a climate-controlled data center, but from a field office in Goma with unreliable power and satellite internet that cut out every time it rained.

Every threat in this chapter is real. The events are documented by CERTs, security vendors, and government agencies. But Clara saw connections between them that nobody else was drawing. Because nobody else was looking at the threat landscape from inside a humanitarian aid network that was being weaponized.

---

## 2.2 -- The Microsoft Exchange Server 0-Day Wave (January 2026)

### What Happened

In the second week of January 2026, Microsoft disclosed a chain of three 0-day vulnerabilities in Exchange Server 2019 that were already being exploited in the wild. The CVEs -- which I'll refer to collectively as the "Exchange Triple" -- allowed unauthenticated remote code execution through a crafted SSRF chain.

This wasn't ProxyLogon redux. The attack was more sophisticated. The initial SSRF was in the OWA authentication endpoint, chaining into a deserialization vulnerability in the transport service, which then leveraged a local privilege escalation to gain SYSTEM on the Exchange server. From there, attackers had direct access to Active Directory via the Exchange Trusted Subsystem group.

Within 48 hours of the disclosure, Shadowserver reported over 12,000 vulnerable Exchange servers still exposed to the internet. Within 72 hours, at least four distinct threat groups -- including APT-29 and a previously unattributed cluster -- were actively exploiting the chain.

### Clara's Notes on the Exchange Triple

In her archive, Clara had a folder labeled `/threats/exchange-triple/`. Inside was a 47-page analysis dated January 18, 2026 -- six days after the disclosure. The first paragraph stopped me cold:

> Sentinelle Humanitaire runs Exchange Server 2019 for approximately 340 field offices across 12 countries. As of this writing, 11 of those servers have been compromised via the Exchange Triple. The attackers are not deploying ransomware. They are not exfiltrating emails. They are modifying mail flow rules to silently BCC a subset of incoming messages to an external address. The messages being copied are exclusively those containing beneficiary tracking reports -- specifically, reports that include the names, ages, and current locations of unaccompanied minors.

> This is not opportunistic exploitation. This is targeted intelligence collection using a 0-day as the entry vector. Someone is using the Exchange Triple to find children.

I read that paragraph three times. Then I opened Playseat and started building the first real investigation scope.

### Which Playseat Modules Address This

**CVE Feed + Auto-Triage** (`crates/svc-api/src/routes/cve.rs`)

The CVE module ingests vulnerability data and automatically triages it against your asset inventory. When the Exchange Triple dropped, an organization running Playseat would see this:

```bash
# Check for new critical CVEs in the last 24 hours
curl -s http://localhost:3000/api/v1/cve/recent?severity=critical&hours=24 \
  -H "Authorization: Bearer $TOKEN" | jq .
```

Response:

```json
{
  "cves": [
    {
      "id": "019474a1-b3c2-7000-8000-000000000101",
      "cve_id": "CVE-2026-0195",
      "title": "Microsoft Exchange Server SSRF Chain - Initial Vector",
      "severity": "critical",
      "cvss_score": 9.8,
      "exploitability": "weaponized",
      "affected_products": ["Microsoft Exchange Server 2019"],
      "affected_asset_count": 3,
      "auto_triage_result": "IMMEDIATE_ACTION",
      "published_at": "2026-01-14T18:00:00Z"
    }
  ],
  "count": 1
}
```

The key field is `affected_asset_count: 3`. The platform has already cross-referenced the CVE against your asset inventory and found three Exchange servers in your environment. No manual triage needed. No spreadsheet. The analyst sees "3 of your assets are vulnerable to an actively exploited 0-day" within seconds of the CVE feed update.

But here's what Clara's research made me add to the triage logic: sector-specific risk amplification. A compromised Exchange server at a bank means financial data at risk. A compromised Exchange server at an NGO means beneficiary data at risk -- and beneficiary data includes children's identities and locations. The risk isn't the same. The consequence isn't the same.

**ADAPT DISCOVER phase** correlates this automatically:

```bash
# Check unacknowledged exposure events
curl -s http://localhost:3000/api/v1/adapt/events/unacknowledged \
  -H "Authorization: Bearer $TOKEN" | jq '.[] | select(.severity == "Critical")'
```

```json
{
  "id": "019474a1-xxxx-7000-8000-000000000201",
  "cycle_id": "019474a1-xxxx-7000-8000-000000000100",
  "event_type": "CredentialLeak",
  "severity": "Critical",
  "details": {
    "cve_id": "CVE-2026-0195",
    "asset_count": 3,
    "exploit_status": "weaponized",
    "description": "Exchange Server 0-day with active exploitation"
  },
  "detected_at": "2026-01-14T18:05:00Z",
  "acknowledged": false
}
```

**Vulnerability Lifecycle** (`crates/svc-api/src/routes/vulnlifecycle.rs`) tracks the entire remediation process:

```bash
# Get patching status for Exchange CVEs
curl -s http://localhost:3000/api/v1/vuln-lifecycle/by-cve/CVE-2026-0195 \
  -H "Authorization: Bearer $TOKEN" | jq .
```

```json
{
  "cve_id": "CVE-2026-0195",
  "status": "in_remediation",
  "affected_assets": 3,
  "patched_assets": 1,
  "mitigated_assets": 1,
  "unprotected_assets": 1,
  "remediation_progress": 66.7,
  "sla_deadline": "2026-01-16T18:00:00Z",
  "sla_status": "at_risk"
}
```

### The Analyst Workflow

1. CVE feed updates (automated, every 15 minutes)
2. Auto-triage matches CVE to 3 Exchange servers in inventory
3. ADAPT DISCOVER generates Critical exposure event
4. Analyst acknowledges event, ADAPT CORRELATE computes risk score
5. ADAPT VALIDATE recommends vulnerability scan pipeline
6. Scan confirms all 3 servers are vulnerable
7. ADAPT FORTIFY generates: Incident Ticket + Detection Rule + Compliance Update
8. Patch Manager tracks remediation progress against SLA
9. ADAPT PROVE records MTTD: 5 minutes from CVE publish to analyst awareness

**Compare this to the industry average MTTD for the Exchange Triple: 3.2 days.** Five minutes versus three days. That's the difference this platform makes.

For Sentinelle Humanitaire, those 3.2 days were 3.2 days of children's data flowing to an adversary. Clara knew this. That's why her notes were so methodical. So angry.

---

## 2.3 -- Russian APT Campaigns Against European Defense Contractors

### What Happened

Throughout January 2026, multiple European defense contractors reported coordinated intrusion attempts attributed to Russian state-sponsored groups. The campaigns used a consistent pattern: spearphishing emails with legitimate-looking NATO exercise invitations, leading to a malicious OneNote document that dropped a custom loader named "FrostByte."

FrostByte was notable for its modular architecture. The initial loader was less than 8KB, delivered via a OneNote embedded HTA file. Once executed, it established a C2 channel over DNS TXT records, then downloaded additional modules for credential harvesting, Active Directory reconnaissance, and data staging.

The campaigns targeted defense contractors in France, Germany, and Poland simultaneously, suggesting a coordinated operation with shared infrastructure.

### Clara's Notes on the FrostByte Connection

Clara's archive contained a folder I almost missed: `/threats/frostbyte-crossref/`. Inside were screenshots of DNS query logs from three different humanitarian aid organizations -- Sentinelle Humanitaire, a German medical charity, and a Polish refugee assistance program. All three showed DNS TXT queries to domains in the same C2 infrastructure as the FrostByte campaign targeting defense contractors.

Her note was dated January 29, 2026:

> The same C2 infrastructure is being used to target both defense contractors and humanitarian organizations. This is either operational laziness (using one infrastructure for multiple campaigns) or it's deliberate -- the humanitarian organizations are part of the same intelligence collection operation.
>
> If it's the latter, then we're not looking at a side effect of a defense-sector campaign. We're looking at a single operation that treats defense intelligence and humanitarian data as equal priorities. The only actor with that dual interest profile is a state intelligence service planning both military intelligence collection AND influence operations through humanitarian channels.
>
> Cross-referencing with the beneficiary data exfiltration from the Exchange Triple: the same children's records that were BCC'd through the mail flow rules are from camps in regions where FrostByte C2 infrastructure is active. The correlation is 0.87. This isn't coincidence. This is a single operation.
>
> I'm calling it PHANTOM MERCY.

Reading those words on my screen in Brussels, with the Playseat correlation engine running in the background, I felt something shift in my understanding of the threat landscape. This wasn't multiple APT campaigns that happened to overlap. This was one operation. One enemy. And Clara had mapped it from the inside.

### Which Playseat Modules Address This

**ADAPT Mesh** (`/api/v1/adapt/mesh/`)

The Mesh module enables federated threat intelligence sharing between organizations. If the French contractor detects the FrostByte loader and shares IOCs through the Mesh, the German and Polish contractors see the indicators before they're targeted.

```bash
# Share an IOC through the ADAPT Mesh
curl -X POST http://localhost:3000/api/v1/adapt/mesh/share \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "intel_type": "ioc",
    "title": "FrostByte Loader Hash",
    "content": {
      "sha256": "a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2",
      "md5": "d4e5f6a7b8c9d0e1f2a3b4c5",
      "file_type": "pe_executable",
      "file_size": 8192,
      "first_seen": "2026-01-12T14:30:00Z",
      "c2_domains": ["update-service.cloud-cdn.net", "dns-relay.cdn-edge.org"],
      "c2_protocol": "dns_txt"
    },
    "tlp": "amber",
    "confidence": 0.95,
    "source_campaign": "FrostByte-NATO-Targeting"
  }'
```

The `tlp: "amber"` field enforces Traffic Light Protocol restrictions. AMBER means the intel can be shared with members of the recipient's organization and its clients who need to know, but not publicly disclosed.

But here's what Clara's research revealed: the humanitarian sector doesn't have an ADAPT Mesh. They don't have a shared threat intelligence platform. Each NGO operates its own security -- or more often, has no security team at all. A loader that gets detected at a defense contractor takes weeks to get shared with the aid organizations using the same internet exchange points. PHANTOM MERCY exploited that gap.

**Threat Forecasting** (`/api/v1/adapt/forecasts/`)

The forecasting engine analyzes threat patterns and predicts future targeting:

```bash
# Generate threat forecasts based on current intelligence
curl -X POST http://localhost:3000/api/v1/adapt/forecasts \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "scope": "defense_sector",
    "time_horizon_days": 30,
    "include_geopolitical_context": true
  }'
```

Response:

```json
{
  "forecasts": [
    {
      "id": "019474a1-xxxx-7000-8000-000000000301",
      "threat_actor": "APT-29",
      "predicted_technique": "T1566.001",
      "technique_name": "Spearphishing Attachment",
      "probability": 0.87,
      "confidence": 0.82,
      "rationale": "Active campaign targeting defense sector with NATO-themed lures. Pattern consistent with pre-exercise intelligence collection. NATO Steadfast Defender 2026 exercise scheduled for March.",
      "recommended_actions": [
        "Deploy email gateway rules for OneNote HTA detection",
        "Block DNS TXT record C2 patterns",
        "Brief personnel on NATO-themed phishing lures"
      ],
      "materialized": false,
      "forecast_date": "2026-02-01T00:00:00Z"
    }
  ]
}
```

**ADAPT Genome** (`/api/v1/adapt/genome/`)

The Genome module fingerprints threat actor behavior:

```bash
# Create a behavioral genome for FrostByte
curl -X POST http://localhost:3000/api/v1/adapt/genome/genomes \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "FrostByte-Loader-Family",
    "threat_actor": "APT-29",
    "description": "Behavioral fingerprint of the FrostByte modular loader family"
  }'

# Add behavioral markers
curl -X POST http://localhost:3000/api/v1/adapt/genome/genomes/$GENOME_ID/markers \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "marker_type": "network_behavior",
    "marker_value": "dns_txt_c2_with_base64_encoding",
    "weight": 0.9,
    "description": "C2 communication via DNS TXT records with base64-encoded payloads"
  }'
```

I created a second genome -- one that isn't in the public documentation. I called it PHANTOM-MERCY-HUMANITARIAN. Its behavioral markers include: targeting of beneficiary management systems, exfiltration of minor identification data, use of legitimate aid distribution channels as C2 proxies, and exploitation of humanitarian communication protocols that are deliberately left unencrypted for field accessibility.

When a new sample is discovered, the Genome matcher can identify it as belonging to the FrostByte family even if the code has been recompiled or obfuscated:

```bash
# Match an unknown sample against known genomes
curl -X POST http://localhost:3000/api/v1/adapt/genome/match \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "sample_markers": [
      {"marker_type": "network_behavior", "marker_value": "dns_txt_c2_with_base64_encoding"},
      {"marker_type": "execution_pattern", "marker_value": "hta_to_powershell_stager"},
      {"marker_type": "persistence", "marker_value": "scheduled_task_com_hijack"}
    ]
  }'
```

Response:

```json
{
  "matches": [
    {
      "genome_name": "FrostByte-Loader-Family",
      "threat_actor": "APT-29",
      "match_score": 0.91,
      "matched_markers": 3,
      "total_markers": 4,
      "confidence": "high"
    }
  ]
}
```

---

## 2.4 -- Ransomware-as-a-Service Evolution (LockBit 4.0 Successor Groups)

### What Happened

After the LockBit takedown in early 2024, the ransomware landscape fragmented. By early 2026, three successor groups had emerged: BlackFlare, CryptVault, and NightShade. Each inherited portions of LockBit's affiliate network and tooling, but with significant upgrades.

The most concerning evolution was the adoption of AI-generated negotiation. BlackFlare deployed chatbots trained on previous ransom negotiations that could carry on realistic conversations with victim organizations, adjusting demands based on company revenue data scraped from public sources.

CryptVault introduced "triple extortion" as standard: encrypt + exfiltrate + DDoS the victim's public-facing infrastructure during the negotiation window. NightShade focused exclusively on critical infrastructure, demanding payments in Monero rather than Bitcoin.

### Clara's Notes on Ransomware as Cover

Her archive had a file I found buried three folders deep, named with a date instead of a descriptive title: `/threats/20260201/analysis.md`. It was short. It was devastating.

> Three NGOs in the Great Lakes region hit by NightShade ransomware in the past two weeks. All three were organizations that had recently implemented improved beneficiary tracking systems -- systems that would have made it harder to silently remove children from the records.
>
> The ransom demands were minimal. 0.3 BTC each. The organizations paid quickly. The data was decrypted. Everyone moved on.
>
> But I checked the restored databases against pre-encryption backups. In all three cases, records for between 15 and 40 unaccompanied minors were missing from the restored data. Not corrupted. Not encrypted. Missing. The decryption key restored everything except those specific records.
>
> NightShade didn't attack these organizations for money. They attacked them to delete evidence. The ransomware was cover for a targeted data destruction operation.
>
> PHANTOM MERCY is using ransomware as an eraser.

I read that entry at 2 AM and couldn't sleep for the rest of the night. The sophistication of it -- using a ransomware attack as camouflage for evidence destruction -- was elegant in a way that made me physically ill. Nobody audits the restored data after a ransomware recovery. You're just grateful to have your files back. You don't run a record-by-record comparison against pre-encryption backups. Nobody does that.

Clara did.

### Which Playseat Modules Address This

**SOAR Playbooks** (`/api/v1/soar/`)

Automated response playbooks are the first line of defense against ransomware. The moment a ransomware indicator is detected, the playbook fires:

```bash
# List available ransomware response playbooks
curl -s http://localhost:3000/api/v1/soar/playbooks?category=ransomware \
  -H "Authorization: Bearer $TOKEN" | jq .
```

```json
{
  "playbooks": [
    {
      "id": "019474a1-xxxx-7000-8000-000000000401",
      "name": "Ransomware Containment - Automated Isolation",
      "category": "ransomware",
      "trigger": "ioc_match_ransomware_family",
      "steps": [
        {
          "order": 1,
          "action": "isolate_host",
          "description": "Immediately isolate affected host from network",
          "requires_approval": false
        },
        {
          "order": 2,
          "action": "snapshot_memory",
          "description": "Capture volatile memory for forensics",
          "requires_approval": false
        },
        {
          "order": 3,
          "action": "disable_user_account",
          "description": "Disable compromised user account in AD",
          "requires_approval": true
        },
        {
          "order": 4,
          "action": "notify_soc",
          "description": "Send high-priority alert to SOC on-call",
          "requires_approval": false
        },
        {
          "order": 5,
          "action": "block_c2_indicators",
          "description": "Push IOCs to firewall and DNS sinkhole",
          "requires_approval": false
        }
      ],
      "mean_execution_time_seconds": 45,
      "last_executed": "2026-02-10T08:15:00Z"
    }
  ]
}
```

Steps 1, 2, 4, and 5 execute automatically. Step 3 -- disabling a user account -- requires human approval. This is the human-in-the-loop principle: automated response for containment, human decision for business-impacting actions.

But after reading Clara's analysis, I added a step that no other SOAR platform includes. Step 6: **post-recovery data integrity verification**. After ransomware decryption, automatically compare restored databases against the most recent pre-encryption backup. Record-by-record. Flag any records that exist in the backup but not in the restored data.

Because if PHANTOM MERCY could use ransomware to erase children's records from three NGO databases, they could do it to any organization. And the only defense is to check what's missing after recovery.

**Behavioral Analytics** (`/api/v1/behavioral/`)

Since ransomware variants change signatures constantly, behavioral detection is essential:

```bash
# Check for ransomware-like file system behavior
curl -s http://localhost:3000/api/v1/behavioral/anomalies?pattern=mass_file_encryption \
  -H "Authorization: Bearer $TOKEN" | jq .
```

```json
{
  "anomalies": [
    {
      "id": "019474a1-xxxx-7000-8000-000000000501",
      "host": "workstation-42.corp.local",
      "pattern": "mass_file_encryption",
      "details": {
        "files_modified_per_second": 47,
        "entropy_increase_avg": 0.94,
        "file_extensions_changed": true,
        "ransom_note_detected": false,
        "shadow_copies_deleted": true
      },
      "confidence": 0.97,
      "severity": "critical",
      "detected_at": "2026-02-15T14:22:17Z"
    }
  ]
}
```

The behavioral engine looks for the telltale signs: high file modification rate, entropy increase (files becoming more random as they're encrypted), file extension changes, shadow copy deletion. It doesn't need to know which ransomware family it is. The behavior is the signature.

---

## 2.5 -- AI-Powered Phishing at Scale

### What Happened

Starting in late 2025 and accelerating into January 2026, security researchers documented a dramatic increase in AI-generated phishing campaigns. The attacks used large language models to generate highly personalized spearphishing emails, deepfake voice synthesis for vishing (voice phishing) calls, and AI-generated profile photos for social media-based social engineering.

The scale was unprecedented. One campaign tracked by researchers generated over 200,000 unique spearphishing emails in a single week, each personalized with the target's name, company, recent projects (scraped from LinkedIn), and current events in their industry. The open rate was 47% -- roughly 3x the rate of traditional phishing campaigns.

A separate vishing campaign used voice cloning to impersonate CFOs, targeting accounts payable departments with fraudulent wire transfer requests. Three European firms lost a combined 12 million EUR before the pattern was identified.

### Clara's Notes on Social Engineering in the Aid Sector

Her archive had an audio file. I almost skipped it -- the archive was mostly text and images. But the filename caught my eye: `for_you.m4a`. Duration: 4 minutes 17 seconds.

It was Clara's voice. Recorded sometime in late 2025, based on context clues.

"I need to tell you something, and I can't write it down because they monitor the text channels more closely than voice. The phishing campaigns targeting the aid sector -- they're not what they look like. Yes, there are the usual Nigerian prince variants, the fake donation requests, the credentials harvesters. But there's a layer underneath.

"Someone is using AI-generated phishing to target specific individuals within humanitarian organizations. Not for credentials. Not for money. For trust. They're building relationships. AI-generated messages that mimic the writing style of known colleagues, sent from lookalike domains. They're not trying to steal passwords. They're trying to establish enough trust with field coordinators that those coordinators will share beneficiary lists, transfer schedules, and camp security protocols.

"It's social engineering in the original sense. Not hacking computers. Hacking people. And the people being hacked are the ones trying to protect vulnerable children.

"I've identified at least four field coordinators across two organizations who have been corresponding with AI-generated personas for months. They think they're talking to colleagues at partner organizations. They've been sharing data that maps directly to the PHANTOM MERCY extraction pattern.

"I'm going to confront the coordinators. I'm going to show them the evidence. And then I'm going to trace the AI infrastructure back to its source. I'm close. I think I know who's running this."

The recording ended.

I played it three more times. Her voice in my headphones. The slight catch in her breathing when she said "vulnerable children." The steel in her tone when she said "I'm close."

She confronted them. She traced the infrastructure. And then she disappeared.

### Which Playseat Modules Address This

**Social Engineering Framework** (`/api/v1/social-eng/`)

The platform includes a full phishing simulation engine:

```bash
# Create an AI-phishing simulation campaign
curl -X POST http://localhost:3000/api/v1/social-eng/campaigns \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Q1 2026 AI-Phish Awareness Test",
    "campaign_type": "email_phish",
    "template_id": "ai-personalized-invoice",
    "target_group": "all_employees",
    "personalization_level": "high",
    "send_window_hours": 72,
    "track_opens": true,
    "track_clicks": true,
    "track_submissions": true,
    "debrief_enabled": true,
    "debrief_delay_minutes": 5
  }'
```

The `debrief_enabled` flag is critical. Five minutes after an employee clicks the simulated phishing link, they receive an educational debrief explaining what they missed and how to spot similar attacks. This turns a testing moment into a training moment.

**Phishing Simulation** (`/api/v1/phishsim/`)

For more advanced simulations targeting specific individuals or departments:

```bash
# Create a targeted vishing simulation
curl -X POST http://localhost:3000/api/v1/phishsim/simulations \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "CFO Voice Clone Test - Finance Dept",
    "simulation_type": "vishing",
    "target_department": "finance",
    "scenario": "Wire transfer request impersonating CFO",
    "difficulty": "advanced",
    "expected_response": "verify_through_secondary_channel"
  }'
```

**Security Awareness Training** (`/api/v1/awareness/`, `/api/v1/sectraining/`, `/api/v1/secquiz/`)

The platform tracks training completion and quiz scores alongside phishing simulation results:

```sql
-- Query: Correlate phishing click rates with training completion
SELECT
    d.name AS department,
    COUNT(DISTINCT se.target_user_id) AS users_targeted,
    COUNT(DISTINCT CASE WHEN se.clicked THEN se.target_user_id END) AS users_clicked,
    ROUND(
        COUNT(DISTINCT CASE WHEN se.clicked THEN se.target_user_id END)::numeric /
        NULLIF(COUNT(DISTINCT se.target_user_id), 0) * 100, 1
    ) AS click_rate_pct,
    AVG(sq.score) AS avg_quiz_score,
    COUNT(DISTINCT CASE WHEN st.completed THEN st.user_id END) AS training_completed
FROM social_eng_results se
JOIN departments d ON d.id = se.department_id
LEFT JOIN security_quiz_results sq ON sq.user_id = se.target_user_id
LEFT JOIN security_training_completions st ON st.user_id = se.target_user_id
WHERE se.campaign_date >= NOW() - INTERVAL '30 days'
GROUP BY d.name
ORDER BY click_rate_pct DESC;
```

This query answers the question every CISO asks: "Are the departments with the worst phishing click rates also the ones that haven't completed their security awareness training?"

But Clara's audio message made me think about a different question. A darker one. What if the people clicking the phishing links aren't failing because of poor training? What if they're clicking because the phishing is so good -- so perfectly personalized, so convincingly written by an AI that has studied their communication patterns for months -- that no amount of training would help?

The answer is: you can't just train against AI-powered social engineering. You have to detect it. You have to identify the AI-generated personas before they build trust. That's a detection problem, not a training problem. And Playseat's behavioral analytics engine can flag communication patterns that match AI-generation signatures: consistent response times, vocabulary distribution anomalies, the absence of typos and hesitation patterns that characterize genuine human writing.

---

## 2.6 -- Supply Chain Attacks Targeting CI/CD Pipelines

### What Happened

In late January 2026, researchers discovered a sophisticated supply chain attack targeting open-source CI/CD tools. The attackers had compromised the update mechanism of a popular GitHub Action used by over 40,000 repositories. The compromised action injected a subtle backdoor into build artifacts -- not into the source code, but into the compiled output during the build process.

The attack was discovered only because a vigilant security engineer at a European cloud provider noticed that the SHA-256 hash of their compiled binary differed from a local build using the same source code and build toolchain. The investigation revealed that the GitHub Action had been modified to inject a 12-byte code cave into ELF binaries that called home to a C2 server during application startup.

### Clara's Notes on Supply Chain Compromise in Aid Networks

Her archive contained a document that chilled me for a different reason than the others. It wasn't about children. It was about infrastructure.

> The identity management system I built for UNHCR in eastern DRC uses an open-source framework for biometric enrollment. The framework depends on 47 upstream packages. I audited every one of them after the GitHub Action compromise was disclosed.
>
> Package 31 of 47. A Python library for image preprocessing used in the fingerprint enrollment pipeline. The library had a pull request merged 8 months ago by a contributor whose GitHub account was created 9 months ago. The PR added "performance improvements" to the image normalization function. The performance improvement was real -- the function runs 15% faster.
>
> But it also writes a 64-byte metadata tag to every processed image. The tag contains the enrollment center ID, the date, and a truncated hash of the biometric template. By itself, the tag is meaningless. But if you have access to the enrollment database -- which the Exchange Triple gave PHANTOM MERCY -- you can use the tags to correlate biometric templates with physical enrollment locations. You can trace a child's fingerprint to the specific camp where they were enrolled.
>
> The supply chain compromise wasn't about the software. It was about adding location metadata to biometric records. Someone spent 8 months building trust in an open-source community so they could tag children.

I closed the laptop. I walked to the window. Brussels was gray and wet and indifferent. I thought about Clara, who had found this. Who had probably confronted whoever was responsible. Who was now silent.

### Which Playseat Modules Address This

**Supply Chain Risk** (`/api/v1/supplychain/`)

```bash
# Scan a project's supply chain dependencies
curl -X POST http://localhost:3000/api/v1/supplychain/scan \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "project_name": "playseat-api",
    "manifest_type": "cargo_toml",
    "include_transitive": true,
    "check_advisories": true
  }'
```

**Software Composition Analysis** (`/api/v1/sca/`)

SCA goes deeper, analyzing the actual dependency tree:

```bash
# Run SCA analysis
curl -s http://localhost:3000/api/v1/sca/analyses?project=playseat-api \
  -H "Authorization: Bearer $TOKEN" | jq .
```

**Secret Scanning** (`/api/v1/secretscan/`)

Ensures no credentials or API keys are accidentally committed:

```bash
# Run secret scan on repository
curl -X POST http://localhost:3000/api/v1/secretscan/scan \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "repository": "playseat_gov",
    "branch": "main",
    "scan_depth": "full_history"
  }'
```

**SAST + DAST** (`/api/v1/sast/`, `/api/v1/dast/`)

Static and dynamic analysis for the application itself:

```bash
# Trigger SAST scan
curl -X POST http://localhost:3000/api/v1/sast/scan \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "project": "playseat-api",
    "language": "rust",
    "ruleset": "security-focused"
  }'
```

After reading Clara's supply chain analysis, I added a new check to the SCA module: contributor provenance scoring. For every dependency, the system now evaluates the age of contributor accounts, the ratio of contributions to account age, and the semantic relevance of changes to the stated purpose of the PR. A "performance improvement" that modifies output data gets flagged. An 8-month-old account making structural changes to a biometric library gets flagged.

It won't catch everything. But it would have caught package 31.

---

## 2.7 -- Chinese APT Targeting Satellite and GEOINT Systems

### What Happened

In early February 2026, a coordinated campaign targeting satellite ground station operators and geospatial intelligence (GEOINT) contractors was attributed to a Chinese APT cluster. The attackers used compromised VPN credentials (likely obtained through credential stuffing with previously leaked databases) to gain initial access, then deployed a custom memory-resident implant that communicated via DNS over HTTPS (DoH).

The targeting was precise: only systems involved in satellite imagery processing and geospatial analysis were affected. The attackers appeared to be specifically interested in the ground station scheduling systems and the orbit prediction databases.

### Clara's Notes on Geospatial Targeting

Clara's archive didn't directly address the Chinese APT campaign -- her research predated the February disclosure. But she had a folder labeled `/geoint/` that contained something I didn't expect: commercial satellite imagery of refugee camp layouts in eastern DRC.

The imagery was annotated. Not with intelligence markers or targeting data. With security assessments.

> Camp Mugunga III. Capacity: 12,000 IDPs. Layout creates three chokepoints at access roads (marked red). UNHCR security covers main entrance only. Eastern perimeter is 400m of unmonitored bush between the camp and Lake Kivu.
>
> Children's section is in the northeast quadrant, adjacent to the unmonitored perimeter. Response time from the nearest security post to the children's section: 11 minutes on foot. After dark, effectively unmonitored.
>
> This is where they're taking them.

She'd mapped the vulnerability not of a computer network but of a physical space. The same analytical framework -- identify the asset, map the attack surface, find the gaps in coverage, predict the adversary's route -- applied to a refugee camp.

And whoever was targeting satellite ground stations and orbit prediction databases might want that same kind of analysis. If you control the satellites, you control the imagery. If you control the imagery, you can plan physical operations at locations where ground-based surveillance has gaps.

I don't know if the Chinese APT campaign is connected to PHANTOM MERCY. Clara's archive doesn't draw that line. But the convergence of cyber targeting and physical geography -- the idea that compromising a satellite ground station could ultimately enable the physical extraction of children from an under-monitored camp perimeter -- that connection kept me awake.

### Which Playseat Modules Address This

**GeoTrack** (`/api/v1/geotrack/`)

The GeoTrack module was built specifically to monitor the security posture of geospatially distributed assets:

```bash
# Register a ground station as a tracked asset
curl -X POST http://localhost:3000/api/v1/geotrack/assets \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Ground Station Alpha",
    "asset_type": "satellite_ground_station",
    "latitude": 48.8566,
    "longitude": 2.3522,
    "classification": "restricted",
    "operational_status": "active",
    "network_segment": "geoint-isolated"
  }'
```

**Identity Risk** (`/api/v1/identityrisk/`)

Since the campaign used compromised VPN credentials:

```bash
# Check for credential exposure in breached databases
curl -s http://localhost:3000/api/v1/identityrisk/exposure-check \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "check_type": "credential_breach",
    "scope": "vpn_users",
    "include_historical": true
  }'
```

**Zero Trust** (`/api/v1/zerotrust/`)

Zero Trust policies would have prevented lateral movement even with valid VPN credentials:

```bash
# Create a Zero Trust policy for GEOINT network segment
curl -X POST http://localhost:3000/api/v1/zerotrust/policies \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "GEOINT Segment - Zero Trust Enforcement",
    "scope": "geoint-isolated",
    "rules": [
      {
        "action": "require_mfa",
        "condition": "any_access",
        "enforcement": "strict"
      },
      {
        "action": "deny_lateral_movement",
        "condition": "cross_segment",
        "enforcement": "strict"
      },
      {
        "action": "require_device_compliance",
        "condition": "any_access",
        "enforcement": "warn"
      }
    ]
  }'
```

---

## 2.8 -- Insider Threat at a Major Defense Contractor (February 2026)

### What Happened

In the first week of February 2026, a major European defense contractor disclosed that an employee in their engineering division had been exfiltrating classified technical drawings and specifications for 18 months. The employee used a combination of techniques: photographing screens with a personal phone, copying files to a personal USB drive during authorized after-hours access, and emailing documents to a personal account using a corporate-approved file sharing service.

The insider was only detected when a routine counterintelligence review noticed anomalous access patterns: the employee was accessing files related to projects they were no longer assigned to, during hours when they had no scheduled work.

### Clara's Notes on Insider Threats in the Humanitarian Sector

This was the section of her archive that made me realize Clara wasn't just a cryptographer who stumbled onto something. She was operating at a level of counterintelligence analysis that suggested training I didn't know she had.

> PHANTOM MERCY doesn't operate only through external cyber compromise. They have insiders.
>
> At Sentinelle Humanitaire, I identified two employees whose behavior matches a planted insider profile:
>
> 1. A database administrator who was hired 14 months ago with credentials that are legitimate but whose previous employment at an "IT consultancy" in Dubai traces back to a shell company with no verifiable operations. He has administrative access to the beneficiary management system. His access patterns are normal during business hours. After hours, he runs queries against the minor tracking tables that produce export files he doesn't send anywhere -- they just exist on his local workstation, which he brings home every night.
>
> 2. A field logistics coordinator who has been with the organization for 3 years and whose background is clean. But 8 months ago, she began requesting transfers to field offices in specific geographic corridors -- always corridors where children have subsequently disappeared from the records. She's not a plant. I think she's been recruited. The behavioral shift 8 months ago correlates with her attending a "conference" in Nairobi that I can't find any record of actually having occurred.
>
> I reported both to the organization's security officer. He told me I was "paranoid" and "seeing patterns that aren't there." He's the third person I need to investigate, because his dismissal of clear counterintelligence indicators is itself a counterintelligence indicator.

Clara. The precision of her analysis. The loneliness of it. Reporting threats and being called paranoid. Finding the pattern and having nobody believe her.

Until now. I believe her. And I have the tools.

### Which Playseat Modules Address This

**UEBA (User and Entity Behavior Analytics)** and **ADAPT Sentinel**

The Sentinel module establishes behavioral baselines and detects anomalies:

```bash
# Create a behavioral baseline for a user group
curl -X POST http://localhost:3000/api/v1/adapt/sentinel/baselines \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Engineering Division - Normal Access Patterns",
    "scope": "engineering_users",
    "baseline_type": "file_access",
    "learning_period_days": 30,
    "parameters": {
      "track_file_access_patterns": true,
      "track_after_hours_access": true,
      "track_cross_project_access": true,
      "track_data_volume": true,
      "anomaly_threshold": 2.5
    }
  }'
```

Once the baseline is established, the Sentinel module continuously monitors for deviations:

```bash
# Detect anomalies against established baselines
curl -X POST http://localhost:3000/api/v1/adapt/sentinel/detect \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "baseline_id": "019474a1-xxxx-7000-8000-000000000901",
    "check_type": "real_time"
  }'
```

Response showing the insider threat detection:

```json
{
  "anomalies": [
    {
      "user_id": "019474a1-xxxx-7000-8000-000000001001",
      "username": "j.dupont",
      "anomaly_type": "cross_project_access",
      "description": "User accessed 47 files from Project CENTAURE which they were reassigned from 6 months ago",
      "deviation_score": 4.2,
      "threshold": 2.5,
      "severity": "high",
      "details": {
        "files_accessed": 47,
        "project": "CENTAURE",
        "last_assignment": "2025-08-15",
        "access_times": ["02:15", "02:47", "03:12"],
        "pattern": "bulk_sequential_access"
      },
      "detected_at": "2026-02-05T03:30:00Z"
    }
  ]
}
```

The deviation score of 4.2 against a threshold of 2.5 would trigger an alert. The details show exactly what made this anomalous: accessing files from a project they left 6 months ago, at 2-3 AM, in a bulk sequential pattern.

If Sentinelle Humanitaire had been running Playseat with ADAPT Sentinel, Clara's database administrator would have been flagged within the first week of his after-hours queries against the minor tracking tables. The logistics coordinator's pattern of requesting transfers to specific corridors would have appeared as a geographic anomaly against baseline transfer request patterns.

Clara wouldn't have had to fight alone.

**Privilege Audit** (`/api/v1/privilegeaudit/`)

```bash
# Audit: Which users have access to projects they're no longer assigned to?
curl -s http://localhost:3000/api/v1/privilegeaudit/stale-access \
  -H "Authorization: Bearer $TOKEN" | jq .
```

```json
{
  "stale_access_entries": [
    {
      "user": "j.dupont",
      "resource": "Project CENTAURE - Technical Drawings",
      "access_level": "read",
      "last_assignment_end": "2025-08-15",
      "last_access": "2026-02-05T03:12:00Z",
      "days_since_reassignment": 174,
      "recommendation": "revoke_access"
    }
  ],
  "total_stale_entries": 1
}
```

**Data Loss Prevention** (`/api/v1/dlpengine/`)

```bash
# Check for unusual data transfers
curl -s http://localhost:3000/api/v1/dlpengine/alerts?severity=high \
  -H "Authorization: Bearer $TOKEN" | jq .
```

---

## 2.9 -- Mapping Threats to Modules: The Complete Matrix

Here's the full mapping of 2026 threats to Playseat modules:

| Threat Event | Primary Module | Secondary Modules | Detection Time Target |
|---|---|---|---|
| Exchange 0-Day Chain | CVE Feed + Auto-Triage | ADAPT Discover, Vuln Lifecycle, Patch Manager | < 15 min from CVE publish |
| Russian APT FrostByte | ADAPT Mesh + Genome | Threat Forecast, War Room, Email Security | < 1 hour from first IOC |
| Ransomware-as-a-Service | SOAR Playbooks | Behavioral Analytics, EDR Agent, Backup | < 5 min from first encryption |
| AI-Powered Phishing | Social Engineering FW | Phishing Sim, Security Training, Security Quiz | Proactive (testing before attack) |
| CI/CD Supply Chain Attack | Supply Chain Risk | SCA, SAST, Secret Scan, Code Review | Per-build (CI pipeline integration) |
| Satellite/GEOINT Targeting | GeoTrack | Identity Risk, Zero Trust, NDR Sensor | < 30 min from initial access |
| Insider Threat | ADAPT Sentinel + UEBA | Privilege Audit, DLP Engine, Session Guard | < 24 hours (behavioral baseline) |
| **PHANTOM MERCY** | **All of the above** | **Every module working in concert** | **Active investigation** |

### The SQL Query That Ties It All Together

```sql
-- Master threat landscape query: Active threats mapped to defense coverage
SELECT
    t.threat_name,
    t.threat_actor,
    t.severity,
    t.first_observed,
    COUNT(DISTINCT tc.technique_id) AS techniques_used,
    COUNT(DISTINCT CASE WHEN cov.coverage_status = 'covered' THEN tc.technique_id END) AS techniques_covered,
    COUNT(DISTINCT CASE WHEN cov.coverage_status = 'gap' THEN tc.technique_id END) AS techniques_gap,
    ROUND(
        COUNT(DISTINCT CASE WHEN cov.coverage_status = 'covered' THEN tc.technique_id END)::numeric /
        NULLIF(COUNT(DISTINCT tc.technique_id), 0) * 100, 1
    ) AS coverage_pct,
    CASE
        WHEN COUNT(DISTINCT CASE WHEN cov.coverage_status = 'gap' THEN tc.technique_id END) > 5 THEN 'CRITICAL GAP'
        WHEN COUNT(DISTINCT CASE WHEN cov.coverage_status = 'gap' THEN tc.technique_id END) > 2 THEN 'MODERATE GAP'
        ELSE 'ACCEPTABLE'
    END AS defense_posture
FROM active_threats t
JOIN threat_techniques tc ON tc.threat_id = t.id
LEFT JOIN technique_coverage cov ON cov.technique_id = tc.technique_id
WHERE t.active = true
GROUP BY t.threat_name, t.threat_actor, t.severity, t.first_observed
ORDER BY
    CASE t.severity
        WHEN 'critical' THEN 1
        WHEN 'high' THEN 2
        WHEN 'medium' THEN 3
    END,
    coverage_pct ASC;
```

---

## 2.10 -- The World That Took Her

The threats described in this chapter aren't theoretical. They're happening right now. By the time you read this, there will be new 0-days, new APT campaigns, new ransomware variants. The specifics change. The patterns don't.

Every threat follows the same lifecycle:
1. Initial access (phishing, credential theft, supply chain compromise, 0-day)
2. Execution and persistence
3. Lateral movement and privilege escalation
4. Data collection and staging
5. Exfiltration or impact (encryption, destruction, manipulation)

PHANTOM MERCY follows the same lifecycle. Just not in cyberspace alone.
1. Initial access -- infiltration of humanitarian organizations through planted employees, compromised systems, and social engineering
2. Execution and persistence -- establishing ongoing access to beneficiary databases, communication channels, and logistics systems
3. Lateral movement -- spreading from one NGO to another through shared infrastructure and inter-organizational data sharing
4. Data collection and staging -- identifying target children, mapping camp security, tracking transfer schedules
5. Impact -- the physical extraction of children from the aid system, with digital evidence destroyed behind them

The ADAPT cycle maps directly to this lifecycle:
1. **DISCOVER** detects the initial indicators
2. **CORRELATE** connects them to known threat patterns
3. **VALIDATE** confirms the exposure is real
4. **FORTIFY** deploys automated defenses
5. **PROVE** measures the response and builds organizational memory

Clara understood this before I did. She was running an ADAPT cycle in her head, without the tooling, without the platform, without anyone believing her. She discovered the threat. She correlated the evidence. She validated the pattern. She tried to fortify the defenses.

She didn't get to PROVE.

That's my job now.

The next chapter will walk you through running a complete ADAPT cycle. Not against a generic simulated APT-29 intrusion. Against the infrastructure Clara mapped. Against PHANTOM MERCY.

---

*Next chapter: "ADAPT Combat Operations -- Building Clara's Shield"*

---

(c) 2026 Playseat -- All Rights Reserved | Defensive Intelligence Through ADAPT
