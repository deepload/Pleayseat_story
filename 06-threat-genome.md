# Chapter 6: Threat Genome -- Clara's DNA Fingerprint

**Playseat Advanced Field Manual -- Book 2**
**87% Match. That's Not a Coincidence. That's a Conviction.**

---

> "Her fingerprints were in the metadata. She'd been studying this malware for months."
> -- My analyst notes, 2026-02-18, 14:22 CET. The moment everything connected.

---

## 6.1 -- The Workstation

**2026-02-18 | 13:00 CET | Playseat Operations Center**

ANSSI arrived at 11:00. Three people. Two I'd never met. One I recognized from the phone call -- lean face, gray eyes, the kind of stillness that comes from decades of intelligence work. He introduced himself as Commandant Renard. I don't believe that's his real name.

They went straight for Clara's evidence vault. I showed them the case, the exhibits, the custody chains, the legal hold. Renard verified three random exhibits himself -- pulled the hashes, recomputed them, compared. He nodded once when they matched. That was his entire emotional range.

Then he told me something I didn't know.

Clara's last known physical location was a field office in [REDACTED], Eastern Mediterranean, October 4th, 2025. Two days after her last Playseat upload. The field office was shared with three other humanitarian organizations. When DGSE went looking for her, they found the office cleared out. Her personal effects were gone. Her workstation was still there.

The workstation had been wiped. Factory reset. But DGSE's forensics team did a partial recovery from the SSD's wear-leveling reserve blocks. They pulled fragments: partial executables, registry hives, event logs, file system metadata.

Renard handed me a USB drive. "We need you to run this through your Genome system. Clara mentioned it. She said it was the best attribution tool she'd ever seen."

She'd said that. About my tool. I took the drive and my hand didn't shake.

I plugged it in.

---

## 6.2 -- Why Threat DNA

Let me tell you what Threat Genome does, because this is the module that's about to crack PHANTOM MERCY wide open.

The problem with traditional threat intelligence is fragmentation. An IP address here. A MITRE technique there. A malware hash somewhere else. Every indicator is treated as an isolated fact. Nobody fuses them into a single identity.

That's what Genome does. It takes every observable artifact from a threat actor -- their TTPs, their infrastructure patterns, their malware signatures, their behavioral quirks -- and hashes them into a single deterministic DNA fingerprint using BLAKE3.

Same inputs, same hash. Every time. Order doesn't matter. And because BLAKE3 is a cryptographic hash, even one different TTP produces a completely different fingerprint. So when two incidents share 87% of their genome, you know -- mathematically, not intuitively -- that you're looking at the same family.

I built Genome at 2 AM on February 15th, 2026, because I was tired of reading attribution reports that said "we assess with moderate confidence" and then listed three possible threat groups. Moderate confidence is a fancy way of saying "we're guessing."

Genome doesn't guess. It computes.

And today, with the fragments from Clara's workstation, it's going to compute who PHANTOM MERCY really is.

---

## 6.3 -- How Genomes Work

A Threat Genome is a structured DNA fingerprint composed of three types of markers:

| Marker Category | Examples | Weight in Similarity |
|----------------|----------|---------------------|
| **TTPs** (Tactics, Techniques, Procedures) | T1566.001 (Spearphishing), T1059.001 (PowerShell), T1055 (Process Injection) | 50% |
| **IOCs** (Indicators of Compromise) | Malware hashes, C2 domains, IP addresses, certificate thumbprints | 20% |
| **Behavioral Markers** | Lateral movement speed, credential harvesting patterns, data staging methods, time-of-day activity | 30% |

The weighting isn't arbitrary. TTPs are the hardest thing for an adversary to change -- you can rotate IPs in minutes, but you can't easily change your entire attack methodology. Behavioral patterns are next -- they're muscle memory. IOCs are the most volatile, so they get the lowest weight.

Clara understood this instinctively. When she was documenting PHANTOM MERCY's operations, she didn't just collect IP addresses and malware hashes. She documented behavior. Working hours. Lateral movement patterns. How long they waited between initial access and first credential dump. How they staged data before exfiltration. The things that are hardest to fake and hardest to change.

She was building a genome before I built the Genome engine.

### The Genome Data Model

Here's the actual Rust struct from `crates/svc-collaboration/src/threat_genome.rs`:

```rust
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ThreatGenome {
    pub id: Id,
    pub name: String,
    pub genome_type: ThreatGenomeType,
    /// BLAKE3 hash of the combined TTP+IOC+behavioral data
    pub dna_hash: String,
    pub ttps: Vec<String>,
    pub iocs: Vec<String>,
    pub behavioral_markers: Vec<String>,
    /// Confidence score (0.0-1.0) in the fingerprint's accuracy
    pub confidence: f64,
    /// Optional cluster identifier for related threat genomes
    pub similarity_cluster: Option<String>,
}
```

And the genome types the engine auto-classifies:

```rust
pub enum ThreatGenomeType {
    Apt,          // 15+ total markers: nation-state level complexity
    SupplyChain,  // 5+ TTPs: sophisticated attack chain
    Malware,      // 5+ IOCs: heavy infrastructure footprint
    Phishing,     // 3+ behavioral markers: social engineering focus
    ZeroDay,      // Default: insufficient data to classify further
}
```

The classification is automatic. You feed in markers, the engine tells you what kind of threat you're looking at. More data equals better classification.

---

## 6.4 -- The BLAKE3 Fingerprinting Engine

Here's the core of the fingerprinting algorithm. I want you to see how simple it actually is:

```rust
pub fn fingerprint(
    &self,
    name: String,
    ttps: &[String],
    iocs: &[String],
    behavioral_markers: &[String],
) -> ThreatGenome {
    // Build deterministic input: sort each category then concatenate
    let mut sorted_ttps = ttps.to_vec();
    sorted_ttps.sort();
    let mut sorted_iocs = iocs.to_vec();
    sorted_iocs.sort();
    let mut sorted_markers = behavioral_markers.to_vec();
    sorted_markers.sort();

    let input = format!(
        "TTPs:{}\nIOCs:{}\nBehavior:{}",
        sorted_ttps.join("|"),
        sorted_iocs.join("|"),
        sorted_markers.join("|"),
    );

    let hash = blake3::hash(input.as_bytes());
    let dna_hash = hash.to_hex().to_string();

    // Auto-classify genome type based on TTP count and marker patterns
    let genome_type = self.classify_genome_type(ttps, iocs, behavioral_markers);

    // Compute confidence based on data richness
    let confidence = self.compute_confidence(ttps, iocs, behavioral_markers);

    ThreatGenome {
        id: Id::new(),
        name,
        genome_type,
        dna_hash,
        ttps: ttps.to_vec(),
        iocs: iocs.to_vec(),
        behavioral_markers: behavioral_markers.to_vec(),
        confidence,
        similarity_cluster: None,
    }
}
```

Three critical design decisions:

1. **Sort before hash.** `["T1566", "T1059"]` and `["T1059", "T1566"]` produce the same DNA hash. Order independence means two analysts can independently build a genome and get the same fingerprint. Clara could build one in the field. I could build one from her evidence. If we used the same markers, we'd get the same hash.

2. **BLAKE3 not SHA-256.** BLAKE3 is 14x faster than SHA-256 on modern hardware. When you're comparing hundreds of genomes in a cluster operation, speed matters. We still use SHA-256 for evidence chain-of-custody (legal reasons), but for computational genomics, BLAKE3 wins.

3. **Category separation.** The `TTPs:...\nIOCs:...\nBehavior:...` format means that a TTP value "T1566" and an IOC value "T1566" produce different hashes. The categories are cryptographically isolated.

---

## 6.5 -- Building PHANTOM MERCY's Genome from Clara's Evidence

Before touching the workstation fragments, I built a baseline genome using everything Clara had documented across her 48 exhibits. I spent two hours going through her evidence descriptions, extracting every TTP, IOC, and behavioral marker she'd recorded.

### Step 1: Create the Genome Record

```bash
curl -s -X POST http://localhost:3000/api/v1/adapt/genome/genomes \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "PHANTOM-MERCY-BASELINE-2025",
    "threat_actor": "PHANTOM MERCY",
    "description": "Baseline genome constructed from Clara Dubois evidence vault (CASE-PM-2025-0001, 48 exhibits). Represents PHANTOM MERCY cyber operations as documented July-October 2025.",
    "family": "PHANTOM-MERCY"
  }'
```

```json
{
  "id": "01949abc-gen1-7000-8000-00000000gn01"
}
```

### Step 2: Add TTP Markers

```bash
GENOME_ID="01949abc-gen1-7000-8000-00000000gn01"

# Supply chain compromise (EX-014)
curl -s -X POST http://localhost:3000/api/v1/adapt/genome/genomes/$GENOME_ID/markers \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "marker_type": "ttp",
    "value": "T1195.002",
    "weight": 0.95,
    "description": "Compromise Software Supply Chain - modified humanitarian aid platform update packages. Source: Clara EX-014."
  }'

# PowerShell execution (EX-027)
curl -s -X POST http://localhost:3000/api/v1/adapt/genome/genomes/$GENOME_ID/markers \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "marker_type": "ttp",
    "value": "T1059.001",
    "weight": 0.70,
    "description": "PowerShell with base64-encoded download cradle. Source: Clara EX-027."
  }'

# Domain account hijacking (EX-031)
curl -s -X POST http://localhost:3000/api/v1/adapt/genome/genomes/$GENOME_ID/markers \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "marker_type": "ttp",
    "value": "T1078.002",
    "weight": 0.90,
    "description": "Domain account hijacking for persistent access across field offices. 7 compromised accounts documented. Source: Clara EX-031."
  }'

# LSASS credential harvesting (EX-031)
curl -s -X POST http://localhost:3000/api/v1/adapt/genome/genomes/$GENOME_ID/markers \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "marker_type": "ttp",
    "value": "T1003.001",
    "weight": 0.85,
    "description": "Bespoke LSASS credential harvester (not Mimikatz). Custom tooling. Source: Clara EX-031."
  }'

# Evidence/log deletion (EX-035)
curl -s -X POST http://localhost:3000/api/v1/adapt/genome/genomes/$GENOME_ID/markers \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "marker_type": "ttp",
    "value": "T1070.004",
    "weight": 0.90,
    "description": "Systematic log and evidence deletion within 4 hours of investigative query. Source: Clara EX-035."
  }'

# Email harvesting (EX-039)
curl -s -X POST http://localhost:3000/api/v1/adapt/genome/genomes/$GENOME_ID/markers \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "marker_type": "ttp",
    "value": "T1114.002",
    "weight": 0.85,
    "description": "Remote email collection targeting investigators and auditors. Clara own mailbox accessed 3x. Source: Clara EX-039."
  }'

# Domain fronting C2 (EX-014)
curl -s -X POST http://localhost:3000/api/v1/adapt/genome/genomes/$GENOME_ID/markers \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "marker_type": "ttp",
    "value": "T1071.001",
    "weight": 0.80,
    "description": "HTTPS C2 using domain fronting through legitimate humanitarian websites. Source: Clara EX-014."
  }'

# Data destruction (EX-042)
curl -s -X POST http://localhost:3000/api/v1/adapt/genome/genomes/$GENOME_ID/markers \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "marker_type": "ttp",
    "value": "T1485",
    "weight": 0.95,
    "description": "Targeted database destruction when investigation detected. Wiped beneficiary records 6 hours after audit query. Source: Clara EX-042."
  }'
```

### Step 3: Add IOC Markers

```bash
# Custom backdoor hash (EX-014)
curl -s -X POST http://localhost:3000/api/v1/adapt/genome/genomes/$GENOME_ID/markers \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "marker_type": "ioc_hash",
    "value": "sha256:d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8",
    "weight": 0.99,
    "description": "Custom backdoor injected into aid platform update packages. Clara designated this GHOSTAID-LOADER. Source: Clara EX-014."
  }'

# C2 domain (EX-014)
curl -s -X POST http://localhost:3000/api/v1/adapt/genome/genomes/$GENOME_ID/markers \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "marker_type": "ioc_domain",
    "value": "cdn-humanitarian-updates.syntheticexample.org",
    "weight": 0.90,
    "description": "Primary C2 domain disguised as humanitarian update CDN. Domain fronted through legitimate aid organization. Source: Clara EX-014."
  }'

# Secondary C2 (EX-027)
curl -s -X POST http://localhost:3000/api/v1/adapt/genome/genomes/$GENOME_ID/markers \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "marker_type": "ioc_domain",
    "value": "api-relief-services.syntheticexample.net",
    "weight": 0.85,
    "description": "Secondary C2 domain. Used for credential exfiltration specifically. Source: Clara EX-027."
  }'

# Self-signed TLS certificate (EX-014)
curl -s -X POST http://localhost:3000/api/v1/adapt/genome/genomes/$GENOME_ID/markers \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "marker_type": "ioc_cert",
    "value": "thumbprint:4a5b6c7d8e9f0a1b2c3d4e5f6a7b8c9d0e1f2a3b",
    "weight": 0.88,
    "description": "Self-signed TLS cert on C2 infrastructure. Subject CN=UNHCR Relief Portal. Source: Clara EX-014."
  }'

# Hawala network cryptocurrency wallet (EX-001)
curl -s -X POST http://localhost:3000/api/v1/adapt/genome/genomes/$GENOME_ID/markers \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "marker_type": "ioc_wallet",
    "value": "bc1q9h5yjkf4qv0e8n3z7w2x1c6m5b4a3s2d1f0g9h",
    "weight": 0.75,
    "description": "Primary Monero mixing wallet used for laundering aid funds. 14-wallet cluster identified. Source: Clara EX-001."
  }'
```

### Step 4: Add Behavioral Markers

This is where Clara's documentation was extraordinary. She didn't just record what PHANTOM MERCY did. She recorded *how* they did it.

```bash
# Working hours
curl -s -X POST http://localhost:3000/api/v1/adapt/genome/genomes/$GENOME_ID/markers \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "marker_type": "behavioral",
    "value": "working-hours:utc+3:0900-1800",
    "weight": 0.70,
    "description": "Primary operator activity window: UTC+3, 0900-1800. Suggests Eastern Mediterranean or East African timezone. Minimal weekend activity except during active counter-investigation operations. Source: Clara EX-035."
  }'

# Counter-investigation response time
curl -s -X POST http://localhost:3000/api/v1/adapt/genome/genomes/$GENOME_ID/markers \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "marker_type": "behavioral",
    "value": "ci-response-time:4-hours-max",
    "weight": 0.90,
    "description": "Maximum observed time between investigative query hitting their infrastructure and evidence destruction response: 4 hours. Suggests active monitoring with alerting, not periodic review. Source: Clara EX-035 and EX-042."
  }'

# Credential harvesting pattern
curl -s -X POST http://localhost:3000/api/v1/adapt/genome/genomes/$GENOME_ID/markers \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "marker_type": "behavioral",
    "value": "credential-targeting:investigators-auditors-oversight",
    "weight": 0.85,
    "description": "Specifically targets credentials of personnel with investigation, audit, or oversight roles. Ignores general staff accounts. Source: Clara EX-039."
  }'

# Data staging method
curl -s -X POST http://localhost:3000/api/v1/adapt/genome/genomes/$GENOME_ID/markers \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "marker_type": "behavioral",
    "value": "data-staging:encrypted-7z-in-temp",
    "weight": 0.75,
    "description": "Stages exfiltration data in AES-256 encrypted 7z archives in temporary directories. Archives named to mimic legitimate update packages. Source: Clara EX-027."
  }'

# Lateral movement patience
curl -s -X POST http://localhost:3000/api/v1/adapt/genome/genomes/$GENOME_ID/markers \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "marker_type": "behavioral",
    "value": "lateral-movement-speed:5-7-day-dwell",
    "weight": 0.65,
    "description": "5-7 day dwell time between lateral movement hops. Exceptionally patient. Consistent with operator training, not automated tooling. Source: Clara EX-031."
  }'
```

### Verify the Genome

```bash
curl -s http://localhost:3000/api/v1/adapt/genome/genomes/$GENOME_ID/markers \
  -H "Authorization: Bearer $TOKEN" | jq length
# 18
```

Eighteen markers. Eight TTPs, five IOCs, five behavioral markers. A rich genome.

```bash
curl -s http://localhost:3000/api/v1/adapt/genome/genomes/$GENOME_ID \
  -H "Authorization: Bearer $TOKEN" | jq '{name, threat_actor, marker_count, confidence, genome_hash}'
```

```json
{
  "name": "PHANTOM-MERCY-BASELINE-2025",
  "threat_actor": "PHANTOM MERCY",
  "marker_count": 18,
  "confidence": 0.95,
  "genome_hash": "7b3f8a2c1d4e5f6089a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3"
}
```

Confidence: 0.95. The engine assessed our data richness and determined we have a near-complete picture of this threat actor.

---

## 6.6 -- Fingerprinting Clara's Workstation

**2026-02-18 | 14:00 CET**

Renard was sitting across the room, watching me work. The DGSE forensics team had recovered 23 distinct artifacts from Clara's workstation: partial executables, DLL fragments, registry entries, event log remnants, prefetch files, and file system metadata.

I created a second genome -- not from Clara's evidence documentation, but from the raw forensic artifacts found on her machine.

```bash
curl -s -X POST http://localhost:3000/api/v1/adapt/genome/genomes \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "CLARA-WORKSTATION-FORENSIC-2025",
    "threat_actor": "Unknown",
    "description": "Genome constructed from forensic recovery of Clara Dubois workstation, field office [REDACTED], October 2025. Partial artifacts recovered from SSD wear-leveling blocks after factory reset.",
    "family": "PHANTOM-MERCY"
  }'
```

```json
{
  "id": "01949abc-gen2-7000-8000-00000000gn02"
}
```

Then I went through the DGSE forensic report, marker by marker.

```bash
WS_GENOME="01949abc-gen2-7000-8000-00000000gn02"

# TTP: PowerShell with encoded commands (from prefetch and event log fragments)
curl -s -X POST http://localhost:3000/api/v1/adapt/genome/genomes/$WS_GENOME/markers \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "marker_type": "ttp",
    "value": "T1059.001",
    "weight": 0.80,
    "description": "PowerShell execution artifacts in prefetch cache. Base64-encoded commands consistent with download cradle pattern. Recovered from wear-leveling blocks."
  }'

# TTP: Domain account persistence (from registry hive fragments)
curl -s -X POST http://localhost:3000/api/v1/adapt/genome/genomes/$WS_GENOME/markers \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "marker_type": "ttp",
    "value": "T1078.002",
    "weight": 0.75,
    "description": "Registry evidence of 3 domain accounts with cached credentials. Accounts belonged to aid workers at different organizations. Consistent with credential harvesting + reuse."
  }'

# TTP: LSASS memory access (from Sysmon event log fragments)
curl -s -X POST http://localhost:3000/api/v1/adapt/genome/genomes/$WS_GENOME/markers \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "marker_type": "ttp",
    "value": "T1003.001",
    "weight": 0.85,
    "description": "Sysmon Event ID 10 fragments showing LSASS.exe process access from unknown DLL. Not Mimikatz signature - custom tooling."
  }'

# TTP: Evidence deletion (the wipe itself)
curl -s -X POST http://localhost:3000/api/v1/adapt/genome/genomes/$WS_GENOME/markers \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "marker_type": "ttp",
    "value": "T1070.004",
    "weight": 0.95,
    "description": "Factory reset of the workstation itself is the clearest evidence of T1070.004. Selective file deletion artifacts also present in MFT fragments."
  }'

# TTP: Email collection (from browser cache fragments)
curl -s -X POST http://localhost:3000/api/v1/adapt/genome/genomes/$WS_GENOME/markers \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "marker_type": "ttp",
    "value": "T1114.002",
    "weight": 0.70,
    "description": "Browser cache fragments showing OWA (Outlook Web App) access from unfamiliar user-agent string. Multiple mailboxes accessed in rapid succession."
  }'

# TTP: Data destruction
curl -s -X POST http://localhost:3000/api/v1/adapt/genome/genomes/$WS_GENOME/markers \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "marker_type": "ttp",
    "value": "T1485",
    "weight": 0.90,
    "description": "Evidence of database connection strings in recovered PowerShell script fragments. DROP TABLE commands partially recovered. Consistent with targeted data destruction."
  }'

# IOC: Malware hash (partial DLL recovery)
curl -s -X POST http://localhost:3000/api/v1/adapt/genome/genomes/$WS_GENOME/markers \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "marker_type": "ioc_hash",
    "value": "sha256:d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8",
    "weight": 0.99,
    "description": "CRITICAL MATCH: Recovered DLL fragment hashes to same SHA-256 as GHOSTAID-LOADER documented in Clara EX-014. Partial recovery - first 48KB of PE header and .text section."
  }'

# IOC: C2 domain (from DNS cache fragments)
curl -s -X POST http://localhost:3000/api/v1/adapt/genome/genomes/$WS_GENOME/markers \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "marker_type": "ioc_domain",
    "value": "cdn-humanitarian-updates.syntheticexample.org",
    "weight": 0.90,
    "description": "Primary PM C2 domain found in recovered DNS client cache. Multiple resolution timestamps spanning 3 weeks."
  }'

# IOC: C2 certificate (from TLS session cache)
curl -s -X POST http://localhost:3000/api/v1/adapt/genome/genomes/$WS_GENOME/markers \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "marker_type": "ioc_cert",
    "value": "thumbprint:4a5b6c7d8e9f0a1b2c3d4e5f6a7b8c9d0e1f2a3b",
    "weight": 0.88,
    "description": "TLS session cache contained certificate with matching thumbprint to PM C2 infrastructure. Subject CN=UNHCR Relief Portal (fraudulent)."
  }'

# Behavioral: Working hours pattern (from event log timestamps)
curl -s -X POST http://localhost:3000/api/v1/adapt/genome/genomes/$WS_GENOME/markers \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "marker_type": "behavioral",
    "value": "working-hours:utc+3:0900-1800",
    "weight": 0.65,
    "description": "Recovered event log timestamps show malicious activity concentrated in UTC+3 business hours. Consistent with baseline genome."
  }'

# Behavioral: Counter-investigation response
curl -s -X POST http://localhost:3000/api/v1/adapt/genome/genomes/$WS_GENOME/markers \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "marker_type": "behavioral",
    "value": "ci-response-time:4-hours-max",
    "weight": 0.80,
    "description": "Timeline reconstruction shows factory reset initiated approximately 3.5 hours after Clara last Playseat session on Oct 2. Within the documented 4-hour CI response window."
  }'

# Behavioral: Targeting investigators specifically
curl -s -X POST http://localhost:3000/api/v1/adapt/genome/genomes/$WS_GENOME/markers \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "marker_type": "behavioral",
    "value": "credential-targeting:investigators-auditors-oversight",
    "weight": 0.85,
    "description": "Browser history fragments show targeted access to email accounts of Clara and two other individuals with oversight roles. General staff accounts untouched."
  }'

# Behavioral: Data staging
curl -s -X POST http://localhost:3000/api/v1/adapt/genome/genomes/$WS_GENOME/markers \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "marker_type": "behavioral",
    "value": "data-staging:encrypted-7z-in-temp",
    "weight": 0.70,
    "description": "File system MFT entries show 7z.exe execution and creation of encrypted archives in C:\\Users\\<redacted>\\AppData\\Local\\Temp\\svc_update\\. Consistent with PM staging pattern."
  }'
```

### Final Workstation Genome

```bash
curl -s http://localhost:3000/api/v1/adapt/genome/genomes/$WS_GENOME/markers \
  -H "Authorization: Bearer $TOKEN" | jq length
# 14
```

Fourteen markers from the workstation forensics. Six TTPs, three IOCs, four behavioral markers. Not as rich as the baseline (it's recovered fragments, not complete evidence), but substantial.

---

## 6.7 -- The Match: 87%

**2026-02-18 | 14:22 CET**

This is the moment.

I ran the workstation genome's markers against all genomes in the database:

```bash
curl -s -X POST http://localhost:3000/api/v1/adapt/genome/match \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "markers": [
      {"marker_type": "ttp", "value": "T1059.001"},
      {"marker_type": "ttp", "value": "T1078.002"},
      {"marker_type": "ttp", "value": "T1003.001"},
      {"marker_type": "ttp", "value": "T1070.004"},
      {"marker_type": "ttp", "value": "T1114.002"},
      {"marker_type": "ttp", "value": "T1485"},
      {"marker_type": "ioc_hash", "value": "sha256:d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8"},
      {"marker_type": "ioc_domain", "value": "cdn-humanitarian-updates.syntheticexample.org"},
      {"marker_type": "ioc_cert", "value": "thumbprint:4a5b6c7d8e9f0a1b2c3d4e5f6a7b8c9d0e1f2a3b"},
      {"marker_type": "behavioral", "value": "working-hours:utc+3:0900-1800"},
      {"marker_type": "behavioral", "value": "ci-response-time:4-hours-max"},
      {"marker_type": "behavioral", "value": "credential-targeting:investigators-auditors-oversight"},
      {"marker_type": "behavioral", "value": "data-staging:encrypted-7z-in-temp"}
    ],
    "threshold": 0.20
  }'
```

```json
[
  {
    "id": "01949abc-mtch-7000-8000-00000000mt01",
    "sample_hash": "sample_c1a2r3a4w5o6r7k8",
    "genome_id": "01949abc-gen1-7000-8000-00000000gn01",
    "similarity": 0.872222,
    "matched_markers": 13,
    "matched_at": "2026-02-18T13:22:15Z"
  }
]
```

**Similarity: 0.872222.**

**Eighty-seven percent.**

Thirteen of fourteen workstation markers matched the PHANTOM MERCY baseline genome. The only unmatched marker was T1195.002 (supply chain compromise) -- which makes sense, because that's an *initial access* technique. It wouldn't leave artifacts on a *victim's* workstation. It would leave artifacts on the *compromised update server*.

Thirteen out of fourteen. Eighty-seven percent Jaccard similarity.

That's not a coincidence. That's not "moderate confidence." That's a mathematical certainty.

The malware on Clara's workstation came from PHANTOM MERCY.

### How the Matching SQL Works

Here's the actual query from the route handler:

```sql
SELECT m.id, $1::text AS sample_hash, m.genome_id,
  CAST(COUNT(gm.id) AS float8) / GREATEST(g.marker_count, 1) AS similarity,
  CAST(COUNT(gm.id) AS int4) AS matched_markers,
  NOW() AS matched_at
FROM adapt_genome_genomes g
JOIN adapt_genome_markers gm ON gm.genome_id = g.id
CROSS JOIN LATERAL (SELECT gen_random_uuid() AS id) m
WHERE gm.value = ANY($2)
GROUP BY g.id, g.marker_count, m.id
HAVING CAST(COUNT(gm.id) AS float8) / GREATEST(g.marker_count, 1) >= $3
ORDER BY similarity DESC LIMIT 20;
```

It does a set intersection against every genome in the database. For each genome, it counts how many of its markers appear in the sample, divides by the genome's total marker count, and returns anything above the threshold. The `GREATEST(g.marker_count, 1)` prevents division by zero on empty genomes.

### The Jaccard Similarity Engine (Rust Side)

For the in-memory comparison, the Rust engine uses weighted Jaccard similarity:

```rust
pub fn compare(&self, a: &ThreatGenome, b: &ThreatGenome) -> f64 {
    let ttp_overlap = jaccard_similarity(&a.ttps, &b.ttps);
    let ioc_overlap = jaccard_similarity(&a.iocs, &b.iocs);
    let marker_overlap = jaccard_similarity(&a.behavioral_markers, &b.behavioral_markers);
    // Weighted combination: TTPs matter most, then behavior, then IOCs
    ttp_overlap * 0.5 + marker_overlap * 0.3 + ioc_overlap * 0.2
}

fn jaccard_similarity(a: &[String], b: &[String]) -> f64 {
    if a.is_empty() && b.is_empty() {
        return 1.0;
    }
    let set_a: HashSet<&str> = a.iter().map(|s| s.as_str()).collect();
    let set_b: HashSet<&str> = b.iter().map(|s| s.as_str()).collect();
    let intersection = set_a.intersection(&set_b).count() as f64;
    let union = set_a.union(&set_b).count() as f64;
    if union == 0.0 { 1.0 } else { intersection / union }
}
```

Jaccard similarity: |A intersection B| / |A union B|. When the weighted calculation ran, the numbers broke down like this:

- **TTP overlap**: 5 shared out of 9 union = 0.556 (weight: 0.5) = **0.278**
- **IOC overlap**: 3 shared out of 5 union = 0.600 (weight: 0.2) = **0.120**
- **Behavioral overlap**: 4 shared out of 5 union = 0.800 (weight: 0.3) = **0.240**
- **Weighted total**: 0.278 + 0.120 + 0.240 = **0.638**

But the raw marker-count similarity -- the one the API returns -- was 0.872. The 87% number. That's the one that matters for attribution. It says: of all the markers we know about PHANTOM MERCY, 87% of them were found on Clara's workstation.

I looked across the room at Renard.

"Eighty-seven percent match to PHANTOM MERCY," I said.

He didn't blink. "Show me the markers."

---

## 6.8 -- The Overlapping Markers

```sql
-- Find overlapping markers between baseline genome and workstation genome
SELECT
    gm1.marker_type,
    gm1.value,
    gm1.weight AS baseline_weight,
    gm2.weight AS workstation_weight,
    gm1.description AS baseline_source
FROM adapt_genome_markers gm1
JOIN adapt_genome_markers gm2 ON gm1.value = gm2.value
WHERE gm1.genome_id = '01949abc-gen1-7000-8000-00000000gn01'
  AND gm2.genome_id = '01949abc-gen2-7000-8000-00000000gn02'
ORDER BY gm1.weight DESC;
```

```
 marker_type | value                                                          | baseline_weight | ws_weight | baseline_source
-------------+----------------------------------------------------------------+-----------------+-----------+--------------------------------------------------
 ioc_hash    | sha256:d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2b3c4d5e6f7a8b9c0...  | 0.99            | 0.99      | GHOSTAID-LOADER from Clara EX-014
 ttp         | T1070.004                                                      | 0.90            | 0.95      | Evidence deletion within 4 hours
 ttp         | T1485                                                          | 0.95            | 0.90      | Targeted database destruction
 ttp         | T1078.002                                                      | 0.90            | 0.75      | Domain account hijacking
 ioc_domain  | cdn-humanitarian-updates.syntheticexample.org                  | 0.90            | 0.90      | Primary C2 domain
 behavioral  | ci-response-time:4-hours-max                                   | 0.90            | 0.80      | 4-hour CI response window
 ioc_cert    | thumbprint:4a5b6c7d8e9f0a1b2c3d4e5f6a7b8c9d0e1f2a3b           | 0.88            | 0.88      | Fraudulent UNHCR cert
 behavioral  | credential-targeting:investigators-auditors-oversight          | 0.85            | 0.85      | Targets investigators specifically
 ttp         | T1003.001                                                      | 0.85            | 0.85      | Custom LSASS harvester
 ttp         | T1114.002                                                      | 0.85            | 0.70      | Email harvesting of investigators
 behavioral  | data-staging:encrypted-7z-in-temp                              | 0.75            | 0.70      | Encrypted 7z staging
 behavioral  | working-hours:utc+3:0900-1800                                  | 0.70            | 0.65      | UTC+3 business hours
 ttp         | T1059.001                                                      | 0.70            | 0.80      | PowerShell encoded commands
```

Thirteen rows. Thirteen independent correlations between what Clara documented and what was found on her machine.

The GHOSTAID-LOADER hash match is the smoking gun. The exact same malware binary that Clara documented in her evidence -- the one she described as "injected into aid platform update packages" -- was recovered from her workstation's SSD. The custom tool they used to compromise humanitarian networks was running on her machine.

They'd found her. They'd compromised her workstation. And then they'd wiped it.

Renard read the table. He read it twice. Then he asked, "The woman who documented the baseline -- she built this evidence specifically so this comparison would be possible?"

"Yes."

"She knew the workstation would be compromised."

It wasn't a question. But I answered anyway: "She knew it was possible. She planned for it."

Her fingerprints were in the metadata. She'd been studying this malware for months. Documenting every hash, every domain, every behavioral pattern. Building the baseline genome that would, months later, match against the forensic evidence from her own compromised workstation.

Clara built the weapon that would identify her attackers.

---

## 6.9 -- Cluster Analysis: The Network Behind PHANTOM MERCY

Individual genome matching told us the workstation was compromised by PHANTOM MERCY. Clustering tells us something bigger: who else is connected.

### Triggering Cluster Analysis

```bash
curl -s -X POST http://localhost:3000/api/v1/adapt/genome/cluster \
  -H "Authorization: Bearer $TOKEN" | jq
```

```json
{
  "cluster_id": "01949abc-clst-7000-8000-00000000cl01",
  "cluster_name": "cluster_20260218_143000",
  "member_count": 4,
  "classification": "small"
}
```

Four genomes in the cluster. That was unexpected. We only created two PHANTOM MERCY genomes. Let me check what else clustered.

```bash
curl -s http://localhost:3000/api/v1/adapt/genome/clusters \
  -H "Authorization: Bearer $TOKEN" | jq
```

```json
[
  {
    "id": "01949abc-clst-7000-8000-00000000cl01",
    "cluster_name": "cluster_20260218_143000",
    "member_count": 4,
    "classification": "small",
    "centroid_genome_id": null,
    "created_at": "2026-02-18T13:30:00Z"
  }
]
```

### Deep Dive: What's in the Cluster?

```sql
SELECT
    g.id,
    g.name,
    g.threat_actor,
    g.marker_count,
    g.family,
    COUNT(CASE WHEN gm.marker_type = 'ttp' THEN 1 END) AS ttp_count,
    COUNT(CASE WHEN gm.marker_type LIKE 'ioc_%' THEN 1 END) AS ioc_count,
    COUNT(CASE WHEN gm.marker_type = 'behavioral' THEN 1 END) AS behavioral_count
FROM adapt_genome_genomes g
LEFT JOIN adapt_genome_markers gm ON gm.genome_id = g.id
WHERE g.family = 'PHANTOM-MERCY'
   OR g.similarity_cluster = 'cluster_20260218_143000'
GROUP BY g.id, g.name, g.threat_actor, g.marker_count, g.family
ORDER BY g.marker_count DESC;
```

```
 id                                   | name                            | threat_actor      | marker_count | family          | ttp_count | ioc_count | behavioral_count
--------------------------------------+---------------------------------+-------------------+--------------+-----------------+-----------+-----------+------------------
 01949abc-gen1-7000-8000-00000000gn01 | PHANTOM-MERCY-BASELINE-2025     | PHANTOM MERCY     | 18           | PHANTOM-MERCY   | 8         | 5         | 5
 01949abc-gen2-7000-8000-00000000gn02 | CLARA-WORKSTATION-FORENSIC-2025 | Unknown           | 14           | PHANTOM-MERCY   | 6         | 3         | 4 (*)
 01954b3a-8c7d-7f00-a1b2-3c4d5e6f7890| TEMP-FORGE-2026-EU-01          | TEMP.Forge        | 13           | APT-SupplyChain | 6         | 4         | 3
 01954b3e-aaaa-7f00-1111-222233334444 | TEMP-FORGE-2026-EU-02          | TEMP.Forge        | 11           | APT-SupplyChain | 5         | 3         | 3
```

I stared at the screen.

TEMP.Forge.

The supply chain threat actor from the European defense contractor breaches in January-February 2026. The one that hit three contractors in eleven days. The one that the German BSI, French ANSSI, and CISA couldn't agree on.

TEMP.Forge clustered with PHANTOM MERCY.

### The Cross-Comparison

```sql
SELECT
    gm1.marker_type,
    gm1.value,
    gm1.weight AS pm_weight,
    gm2.weight AS forge_weight
FROM adapt_genome_markers gm1
JOIN adapt_genome_markers gm2 ON gm1.value = gm2.value
WHERE gm1.genome_id = '01949abc-gen1-7000-8000-00000000gn01'
  AND gm2.genome_id = '01954b3a-8c7d-7f00-a1b2-3c4d5e6f7890'
ORDER BY gm1.weight DESC;
```

```
 marker_type | value                              | pm_weight | forge_weight
-------------+------------------------------------+-----------+--------------
 ttp         | T1195.002                          | 0.95      | 0.95
 ttp         | T1059.001                          | 0.70      | 0.70
 behavioral  | data-staging:encrypted-7z-in-temp  | 0.75      | 0.70
 behavioral  | working-hours:utc+3:0900-1800      | 0.70      | 0.65 (*)
```

Four shared markers between a trafficking network's cyber arm and a group targeting European defense contractors.

T1195.002 -- supply chain compromise. Both groups modify software update mechanisms to inject backdoors. Same technique. Same approach.

The data staging pattern -- encrypted 7z archives in temp directories. The same operational habit. The same muscle memory.

And the working hours: UTC+3, 0900-1800. The same timezone. The same schedule.

I ran the full weighted Jaccard comparison:

```bash
curl -s -X POST http://localhost:3000/api/v1/adapt/genome/match \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "markers": [
      {"marker_type": "ttp", "value": "T1195.002"},
      {"marker_type": "ttp", "value": "T1059.001"},
      {"marker_type": "ttp", "value": "T1078.002"},
      {"marker_type": "ttp", "value": "T1003.001"},
      {"marker_type": "ttp", "value": "T1070.004"},
      {"marker_type": "ttp", "value": "T1114.002"},
      {"marker_type": "ttp", "value": "T1071.001"},
      {"marker_type": "ttp", "value": "T1485"},
      {"marker_type": "ioc_hash", "value": "sha256:d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8"},
      {"marker_type": "behavioral", "value": "working-hours:utc+3:0900-1800"},
      {"marker_type": "behavioral", "value": "data-staging:encrypted-7z-in-temp"}
    ],
    "threshold": 0.15
  }'
```

```json
[
  {
    "id": "01949abc-mtch-7000-8000-00000000mt10",
    "sample_hash": "sample_pm_full_baseline",
    "genome_id": "01949abc-gen1-7000-8000-00000000gn01",
    "similarity": 0.611111,
    "matched_markers": 11,
    "matched_at": "2026-02-18T14:35:00Z"
  },
  {
    "id": "01949abc-mtch-7000-8000-00000000mt11",
    "sample_hash": "sample_pm_full_baseline",
    "genome_id": "01954b3a-8c7d-7f00-a1b2-3c4d5e6f7890",
    "similarity": 0.307692,
    "matched_markers": 4,
    "matched_at": "2026-02-18T14:35:00Z"
  }
]
```

30.7% similarity between PHANTOM MERCY and TEMP.Forge. On its own, that might not be conclusive. But combined with the identical working hours, the identical staging technique, and the identical supply chain compromise methodology -- this isn't a coincidence.

PHANTOM MERCY and TEMP.Forge share operational resources. Either they're the same group with different mission sets, or they're separate groups using the same tooling provider. Either way, the entity that targeted European defense contractors is connected to the entity that ran a child trafficking network.

I told Renard. He made a phone call. I don't know who he called, but his voice dropped to a murmur and he walked to the far corner of the room.

When he came back, he said: "Continue."

---

## 6.10 -- Feeding Genome Data Back into ADAPT

Genome analysis doesn't end at attribution. The whole point of identifying an adversary's DNA is to predict what they'll do next.

The PHANTOM MERCY genome's TTPs feed directly into the ADAPT War Room:

```bash
curl -s http://localhost:3000/api/v1/adapt/genome/genomes/$GENOME_ID/markers \
  -H "Authorization: Bearer $TOKEN" | jq '[.[] | select(.marker_type == "ttp") | .value]'
```

```json
["T1195.002", "T1059.001", "T1078.002", "T1003.001", "T1070.004", "T1114.002", "T1071.001", "T1485"]
```

Eight techniques. Every one maps to a coverage matrix entry. The War Room simulation from Chapter 5 was built on this data. The remediation roadmap flows directly from the genome analysis.

```bash
# Check coverage against PM-specific techniques
for TTP in T1195.002 T1059.001 T1078.002 T1003.001 T1070.004 T1114.002 T1071.001 T1485; do
  curl -s "http://localhost:3000/api/v1/adapt/coverage/$TTP" \
    -H "Authorization: Bearer $TOKEN" | jq "{technique: .technique_id, coverage: .coverage_status, confidence: .confidence}"
done
```

Any technique that returns `"coverage_status": "gap"` is a fortification priority driven directly by genome intelligence. Discover the threat. Fingerprint it. Fortify against its specific TTPs. Prove the fortification works.

That's the loop. Clara would recognize it. She'd call it good tradecraft.

---

## 6.11 -- Database Deep Dive

The complete schema for the Genome subsystem spans four tables:

```sql
-- The core genome record
CREATE TABLE IF NOT EXISTS adapt_genome_genomes (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name            TEXT NOT NULL,
    threat_actor    TEXT,
    description     TEXT NOT NULL DEFAULT '',
    family          TEXT,
    marker_count    INTEGER NOT NULL DEFAULT 0,
    confidence      REAL NOT NULL DEFAULT 0.0,
    evidence_hash   TEXT,
    genome_hash     TEXT,
    created_by      UUID,
    created_at      TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_adapt_genome_genomes_actor ON adapt_genome_genomes(threat_actor);
CREATE INDEX IF NOT EXISTS idx_adapt_genome_genomes_family ON adapt_genome_genomes(family);

-- Individual markers that compose a genome
CREATE TABLE IF NOT EXISTS adapt_genome_markers (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    genome_id       UUID REFERENCES adapt_genome_genomes(id) ON DELETE CASCADE,
    marker_type     TEXT NOT NULL,
    value           TEXT NOT NULL,
    weight          REAL NOT NULL DEFAULT 0.5,
    confidence      REAL NOT NULL DEFAULT 0.5,
    created_at      TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_adapt_genome_markers_genome ON adapt_genome_markers(genome_id);
CREATE INDEX IF NOT EXISTS idx_adapt_genome_markers_type ON adapt_genome_markers(marker_type);

-- Cross-genome match results
CREATE TABLE IF NOT EXISTS adapt_genome_matches (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    genome_a_id     UUID REFERENCES adapt_genome_genomes(id) ON DELETE CASCADE,
    genome_b_id     UUID REFERENCES adapt_genome_genomes(id) ON DELETE CASCADE,
    similarity      REAL NOT NULL DEFAULT 0.0,
    matching_markers JSONB NOT NULL DEFAULT '[]',
    matched_at      TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    matched_by      UUID
);
CREATE INDEX IF NOT EXISTS idx_adapt_genome_matches_a ON adapt_genome_matches(genome_a_id);
CREATE INDEX IF NOT EXISTS idx_adapt_genome_matches_b ON adapt_genome_matches(genome_b_id);

-- Cluster groupings of related genomes
CREATE TABLE IF NOT EXISTS adapt_genome_clusters (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    cluster_name    TEXT,
    member_count    INTEGER NOT NULL DEFAULT 0,
    classification  TEXT NOT NULL DEFAULT 'unknown',
    avg_similarity  REAL NOT NULL DEFAULT 0.0,
    evidence_hash   TEXT,
    created_at      TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);
```

Every genome, every marker, every match, every cluster -- stored with evidence hashes. The genome analysis itself is evidence. Dual-hashed. Chain-of-custody'd. Admissible.

---

## 6.12 -- Confidence Scoring Math

The confidence score is a data richness metric -- how much do we know about this genome?

```rust
fn compute_confidence(
    &self,
    ttps: &[String],
    iocs: &[String],
    behavioral_markers: &[String],
) -> f64 {
    let ttp_score = (ttps.len() as f64 * 0.1).min(0.4);
    let ioc_score = (iocs.len() as f64 * 0.05).min(0.3);
    let marker_score = (behavioral_markers.len() as f64 * 0.1).min(0.3);
    ttp_score + ioc_score + marker_score
}
```

| TTPs | IOCs | Behavioral | Confidence |
|------|------|-----------|------------|
| 1 | 0 | 0 | 0.10 |
| 3 | 2 | 1 | 0.50 |
| 4 | 4 | 2 | 0.60 |
| 4+ | 6+ | 3+ | 1.00 (max) |

Our PHANTOM MERCY baseline: 8 TTPs, 5 IOCs, 5 behavioral markers. The engine computed 0.95 confidence. Near maximum. Clara's documentation was that thorough.

The workstation genome: 6 TTPs, 3 IOCs, 4 behavioral markers. Confidence: 0.85. Lower because it's partial recovery, but still strong.

The unit tests verify the scoring:

```rust
#[test]
fn confidence_increases_with_data() {
    let engine = ThreatGenomeEngine::new();
    let small = engine.fingerprint("Small".to_string(), &["T1".to_string()], &[], &[]);
    let large = engine.fingerprint(
        "Large".to_string(),
        &(0..5).map(|i| format!("T{}", i)).collect::<Vec<_>>(),
        &(0..5).map(|i| format!("ioc:{}", i)).collect::<Vec<_>>(),
        &(0..3).map(|i| format!("b-{}", i)).collect::<Vec<_>>(),
    );
    assert!(large.confidence > small.confidence);
}
```

---

## 6.13 -- Genome Stats

```bash
curl -s http://localhost:3000/api/v1/adapt/genome/stats \
  -H "Authorization: Bearer $TOKEN" | jq
```

```json
{
  "total_genomes": 9,
  "total_markers": 121,
  "total_clusters": 2,
  "total_matches": 17
}
```

Nine genomes. A hundred and twenty-one markers. Two clusters. Seventeen matches.

The PHANTOM MERCY cluster alone connects a trafficking network to European defense contractor breaches. That's the kind of intelligence fusion that takes human analysts months of cross-referencing. Genome did it in seconds.

---

## 6.14 -- API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/adapt/genome/genomes` | Create a new genome |
| GET | `/api/v1/adapt/genome/genomes` | List all genomes |
| GET | `/api/v1/adapt/genome/genomes/{id}` | Get genome by ID |
| POST | `/api/v1/adapt/genome/genomes/{id}/markers` | Add a marker to a genome |
| GET | `/api/v1/adapt/genome/genomes/{id}/markers` | List markers for a genome |
| POST | `/api/v1/adapt/genome/match` | Match a sample against all genomes |
| GET | `/api/v1/adapt/genome/matches` | List all match results |
| GET | `/api/v1/adapt/genome/clusters` | List all clusters |
| POST | `/api/v1/adapt/genome/cluster` | Trigger cluster analysis |
| GET | `/api/v1/adapt/genome/stats` | Get genome subsystem statistics |

---

## 6.15 -- Comparison: Why We Do It Better

| Feature | Recorded Future | CrowdStrike | Mandiant | Playseat Genome |
|---------|----------------|-------------|----------|-----------------|
| Attribution method | Analyst assessment | Analyst + ML | Human analysts | Deterministic BLAKE3 hashing |
| Reproducibility | Low (human judgment) | Medium (ML varies) | Low (human judgment) | Perfect (same input = same hash) |
| Speed | Hours-days | Hours | Days-weeks | Seconds |
| Custom markers | No | Limited | No | Unlimited -- any string is a marker |
| Cross-org comparison | Paid add-on | Paid add-on | Manual sharing | Built-in via Mesh network |
| Self-hosted | No (SaaS only) | No (SaaS only) | No (SaaS only) | Yes -- your data never leaves your infra |
| Open matching | No -- black box | No -- black box | No -- black box | Full SQL access to all match data |

The fundamental difference: other platforms give you conclusions. Playseat gives you the math. You can query any genome match, see exactly which markers overlapped, verify the similarity score yourself, and disagree with the system if your analysis warrants it.

Human-in-the-loop. Evidence-first. Always.

Clara would approve.

---

## 6.16 -- What the Genome Tells Us About Clara

**2026-02-18 | 15:30 CET**

Renard and his team have been on the phone for an hour. I've been staring at the cluster analysis results, running analytics queries, trying to understand the full picture.

Here's what the genome tells us about Clara:

**She was identified.** The GHOSTAID-LOADER on her workstation proves PHANTOM MERCY targeted her specifically. The behavioral markers -- the 4-hour CI response window, the investigator-targeting pattern -- match exactly. They knew she was investigating them.

**She probably knew they were coming.** Her last uploads were October 1-2. The workstation was wiped October 4-5. In the two days between, she didn't log into Playseat. She didn't upload new evidence. She didn't update any exhibits.

But she'd already finished. EX-048 -- the consolidated timeline -- was her final document. She compressed three months of investigation into a single prosecutable narrative, verified it, and signed off.

She finished the case. Then she went dark.

**She left breadcrumbs.** Not just the evidence vault. The genome markers she documented -- the behavioral observations, the working hours, the data staging patterns -- these are the exact markers that allowed us to link PHANTOM MERCY to TEMP.Forge. She couldn't have known about the defense contractor breaches (they happened after she disappeared). But she documented the behavioral signatures that would eventually make the connection.

She was building a net. Even if she didn't catch them, whoever came after her would.

I stood at the window of the operations center and watched the rain.

Clara told me once, in Amsterdam, that the best intelligence work is the kind that outlives the analyst. "Write it down. Hash it. Chain it. Make it survive you."

She did exactly that.

---

## 6.17 -- Closing Thoughts

I built the Genome engine in six hours on February 15th, three days before I found Clara's vault. Three hundred and fourteen lines of Rust. The most impactful code I've ever written relative to its size.

Today, that code proved that the malware on Clara's workstation came from PHANTOM MERCY with 87% Jaccard similarity. It connected a trafficking network's cyber operations to European defense contractor breaches. It gave ANSSI and the DGSE the mathematical proof they need to pursue this across borders.

The genome is the key. Not because it's clever technology -- it's not, it's sorting and hashing and set intersection. It's the key because it turns scattered indicators into mathematical certainty. It turns "we assess with moderate confidence" into "87% marker overlap, 0.95 confidence, here are the thirteen matching data points."

Clara understood that before I did. She was building genomes by hand, documenting every behavioral marker, every TTP, every IOC, because she knew that someday the math would matter more than the intuition.

Renard came back from his phone call. He asked me one question:

"Can you run the PHANTOM MERCY genome against international threat intelligence databases through the Mesh network?"

"Yes."

"Do it. We need to know how far this network extends."

That's the next chapter. Mesh intelligence sharing. Taking Clara's genome fingerprint and searching for it across every partner agency's database without revealing the underlying markers.

But first, I'm going to sit here for a minute. I'm going to look at the cluster analysis results one more time. I'm going to read Clara's exhibit descriptions one more time.

Her fingerprints are in the metadata. Her intelligence is in the markers. Her courage is in the timestamps -- 3 AM, 4 AM, field locations, cellular connections, knowing they were watching.

The genome is her gift. The evidence vault is her insurance. And this platform -- this thing I built at 2 AM on sleepless nights because I believed defensive intelligence could be done better -- held it all. Every hash verified. Every chain unbroken. Every exhibit intact.

I'm going to find her. The genome told me who took her. The evidence tells me where to look.

Eighty-seven percent match. That's not a coincidence.

That's a conviction.

---

*Next chapter: "Mesh Intelligence Sharing -- The Search Goes Global"*

---

(c) 2026 Playseat -- All Rights Reserved | Defensive Intelligence Through ADAPT
