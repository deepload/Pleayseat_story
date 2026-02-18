# Chapter 7 -- Mesh Intelligence: The Network That Found Clara

**Classification: PROPRIETARY** | **ADAPT Extension 7: Mesh** | **Crate: `svc-api::routes::adapt` (Mesh handlers)**

> I didn't build the Mesh to share threat intel with partner agencies. I mean, that's what it does. That's what the documentation says. But the reason I sat up for seventy-two hours writing the trust-scoring algorithm was because Clara Dubois had gone dark, and no single agency on this planet had enough of the picture to tell me where she was.

---

## Table of Contents

1. [The Night Everything Changed](#the-night-everything-changed)
2. [Mesh Architecture -- Building the Net](#mesh-architecture)
3. [Registering the Three Partners](#registering-the-three-partners)
4. [Trust Scoring: Who Deserves to Know About Clara](#trust-scoring)
5. [The First Push: Clara's PHANTOM MERCY IOCs](#the-first-push)
6. [Receiving Intel from Peers](#receiving-intel-from-peers)
7. [The BND Lead -- Callsign PASSERELLE](#the-bnd-lead)
8. [Sync Log Monitoring](#sync-log-monitoring)
9. [Privacy Controls: Protecting Clara While Searching for Her](#privacy-controls)
10. [Mesh Health and the Waiting Game](#mesh-health)
11. [Database Schema](#database-schema)
12. [API Reference](#api-reference)

---

## The Night Everything Changed

February 14, 2026. Valentine's Day. There's a bitter joke in that.

Six weeks ago, Clara sent her last verified communication -- a PGP-signed message routed through three Tor relays, delivered to my personal dead drop. The message was short. Classic Clara. No pleasantries, no romance, no fear. Just data:

> *Trafficking network uses humanitarian logistics as cover. Codename PHANTOM MERCY. Operating across Sahel, Eastern Mediterranean, Balkans. Evidence in shipping manifests -- look for systematic deviation in declared cargo weights vs actual tonnage. Children. They're moving children.*
>
> *I'm going to Niamey to photograph the manifests. If I don't check in within 14 days, activate the mesh. Find me.*
> *-- C.D.*

She didn't check in.

I stared at that message for three days before I accepted what it meant. Clara -- brilliant, stubborn, fearless Clara -- had walked into the mouth of something that eats people. The DGSE either couldn't or wouldn't tell me anything. Her official cover was "field cryptographer attached to an aid coordination unit." Her unofficial role, the one she'd whispered to me in a hotel room in Lyon while rain streaked the windows, was intelligence collector. She'd been mapping trafficking routes disguised as legitimate humanitarian supply chains.

And now she was gone.

So I built the Mesh. Not because the world needed another intel-sharing protocol. Because I needed to ask three agencies the same question at the same time: *Have you seen her?*

---

## Mesh Architecture -- Building the Net

The ADAPT Federated Defense Mesh is peer-to-peer. No central server. No single point of control. That matters for my purposes because the moment a centralized authority controls the information flow, politics enters the equation. And politics is what keeps Clara missing.

### Core Design

```
+------------------+         TLS + mTLS         +------------------+
|   Playseat       |<=========================>|   Playseat       |
|   Instance A     |    Shared Intel (TLP)      |   Instance B     |
|   (Our SOC)      |                            |   (NATO NCIRC)   |
|                  |    Trust Score Exchange     |                  |
|  Local DB        |                            |  Local DB        |
|  (full data)     |    Sync Log                |  (full data)     |
+------------------+                            +------------------+
        |                                               |
        |           TLS + mTLS                          |
        +=====================================+         |
                                              |         |
                                     +------------------+
                                     |   Playseat       |
                                     |   Instance C     |
                                     |   (BND Cyber)    |
                                     +------------------+
```

Each instance maintains full sovereignty over its own data. Nothing leaves your database unless you push it. That's not a feature -- it's the only way I could convince three different national agencies to join a network run by a guy whose primary motivation is finding a missing French woman.

I didn't tell them about Clara, of course. I told them about PHANTOM MERCY. About the trafficking network that had compromised humanitarian logistics. About the cybersecurity angle -- because there is one. PHANTOM MERCY doesn't just move cargo. They manipulate digital shipping manifests, falsify aid coordination databases, and run a sophisticated infrastructure of shell logistics companies with their own IT networks. That's a cyber threat. That's what I pitched.

And it worked. Because it's true. The fact that somewhere inside that network is a woman I love -- well, that part I kept to myself.

### Data Flow Principles

| Principle | Implementation |
|-----------|---------------|
| **Sovereignty** | Your data never leaves unless you explicitly push it |
| **TLP enforcement** | `TLP:RED` intel never enters the sharing pipeline |
| **Trust-gated** | Low-trust peers receive less detailed intel |
| **Audit trail** | Every share, receive, and sync is logged |
| **Bidirectional** | Peers that only consume get trust penalties |

---

## Registering the Three Partners

I chose my partners carefully. Three agencies, three capabilities, three reasons to care about PHANTOM MERCY.

### Partner 1: NATO NCIRC

NATO's incident response capability. They've been tracking logistics-sector cyber threats as part of their supply chain security program. They don't know about Clara, but they know about trafficking networks that piggyback on legitimate shipping infrastructure. Good enough.

```bash
TOKEN=$(curl -s -X POST https://playseat.local/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "mesh_admin", "password": "M3sh!Adm1n2026"}' | jq -r '.token')

curl -s -X POST https://playseat.local/api/v1/adapt/mesh/peers \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "NATO NCIRC",
    "endpoint_url": "https://mesh-ncirc.nato.int/api/v1/adapt/mesh",
    "organization": "NATO Communications and Information Agency",
    "capabilities": ["threat_intel", "ioc_sharing", "apt_tracking", "logistics_security"]
  }'
```

```json
{
  "id": "01954c01-nato-7f00-mesh-peer00000001"
}
```

### Partner 2: CERT-EU

The European Union's cybersecurity arm. They have visibility into aid organization networks across the continent. If PHANTOM MERCY's digital footprint touches any EU-funded humanitarian program, CERT-EU would have telemetry.

```bash
curl -s -X POST https://playseat.local/api/v1/adapt/mesh/peers \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "CERT-EU",
    "endpoint_url": "https://mesh.cert.europa.eu/api/v1/adapt/mesh",
    "organization": "European Union Agency for Cybersecurity",
    "capabilities": ["threat_intel", "ioc_sharing", "incident_response", "humanitarian_network_monitoring"]
  }'
# {"id": "01954c02-cert-7f00-mesh-peer00000002"}
```

### Partner 3: BND Cyber Division

This is the one that matters most, though I didn't know it yet.

Germany's Bundesnachrichtendienst -- their foreign intelligence service -- runs one of the most sophisticated SIGINT operations in Europe. The BND's cyber division monitors communications across the Sahel region as part of Germany's counter-terrorism and anti-trafficking mandates. If Clara was transmitting anything -- even a burst transmission, even a callsign -- the BND might have picked it up.

I registered them carefully. The BND doesn't share lightly. I had to frame PHANTOM MERCY as a cyber threat to European critical logistics infrastructure. Which it is. I just didn't mention the part about a woman I haven't slept properly since losing.

```bash
curl -s -X POST https://playseat.local/api/v1/adapt/mesh/peers \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "BND Cyber Division",
    "endpoint_url": "https://mesh.bnd-cyber.de/api/v1/adapt/mesh",
    "organization": "Bundesnachrichtendienst - Cyber & IT Security",
    "capabilities": ["sigint_correlation", "apt_tracking", "threat_intel", "comms_intercept", "sahel_monitoring"]
  }'
# {"id": "01954c03-bnd-7f00-mesh-peer00000003"}
```

### Verify All Peers

```bash
curl -s https://playseat.local/api/v1/adapt/mesh/peers \
  -H "Authorization: Bearer $TOKEN" | jq '.[] | {name, organization, trust_score, active}'
```

```json
{
  "name": "NATO NCIRC",
  "organization": "NATO Communications and Information Agency",
  "trust_score": 0.5,
  "active": true
}
{
  "name": "CERT-EU",
  "organization": "European Union Agency for Cybersecurity",
  "trust_score": 0.5,
  "active": true
}
{
  "name": "BND Cyber Division",
  "organization": "Bundesnachrichtendienst - Cyber & IT Security",
  "trust_score": 0.5,
  "active": true
}
```

Three peers. All at 0.5 trust -- the neutral starting point. Nobody's proven themselves yet. But the network exists. The net is cast.

My hands were shaking when I hit enter on the BND registration. Not from fear. From hope. Hope is worse.

---

## Trust Scoring: Who Deserves to Know About Clara

Trust in the Mesh isn't a handshake. It's math. Multi-dimensional, decay-weighted, continuously recalculated math. I built it this way because I can't afford to share Clara-related intelligence with anyone who might leak, delay, or politicize it. The trust score determines what each peer gets to see.

### Trust Dimensions

| Dimension | What It Measures | Weight |
|-----------|-----------------|--------|
| `intel_quality` | Accuracy of shared IOCs (verified vs false positives) | 0.35 |
| `timeliness` | How quickly intel is shared after discovery | 0.25 |
| `reciprocity` | Ratio of intel shared vs intel consumed | 0.20 |
| `reliability` | Uptime and sync completion rate | 0.10 |
| `coverage` | Breadth of capability overlap | 0.10 |

### Scoring NATO's Intel Quality

Two weeks in, NATO shared their first package. Sixteen IOCs related to logistics-sector malware campaigns. I verified each one independently. Fifteen confirmed. One stale IP that had rotated 72 hours before sharing. Good enough.

```bash
curl -s -X POST https://playseat.local/api/v1/adapt/mesh/peers/01954c01-nato-7f00-mesh-peer00000001/trust \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "dimension": "intel_quality",
    "score": 0.92,
    "reason": "15/16 shared IOCs confirmed as true positives via independent verification. One IP was stale (rotated 72h before sharing). Excellent quality."
  }'
```

```json
{
  "id": "01954c10-trust-7f00-score-000000001"
}
```

The backend recalculates automatically:

```sql
-- Runs after every trust score update:
UPDATE adapt_mesh_peers SET trust_score =
  (SELECT COALESCE(AVG(score), 0.5) FROM adapt_mesh_trust_scores WHERE peer_id = $1),
  updated_at = NOW() WHERE id = $1;
```

### Building the Full Trust Profile

```bash
# NATO timeliness
curl -s -X POST https://playseat.local/api/v1/adapt/mesh/peers/01954c01-nato-7f00-mesh-peer00000001/trust \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "dimension": "timeliness",
    "score": 0.85,
    "reason": "Average 4.2 hours from detection to sharing. Within 24h SLA."
  }'

# NATO reciprocity
curl -s -X POST https://playseat.local/api/v1/adapt/mesh/peers/01954c01-nato-7f00-mesh-peer00000001/trust \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "dimension": "reciprocity",
    "score": 0.78,
    "reason": "Shared 23 IOC packages, consumed 29. Slightly more consumer than producer."
  }'

# NATO reliability
curl -s -X POST https://playseat.local/api/v1/adapt/mesh/peers/01954c01-nato-7f00-mesh-peer00000001/trust \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "dimension": "reliability",
    "score": 0.99,
    "reason": "Zero failed syncs in 14 days. 99.97% uptime."
  }'

# BND scores -- they're slower but more precise
curl -s -X POST https://playseat.local/api/v1/adapt/mesh/peers/01954c03-bnd-7f00-mesh-peer00000003/trust \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "dimension": "intel_quality",
    "score": 0.97,
    "reason": "Every IOC verified. Zero false positives. The Germans are meticulous."
  }'

curl -s -X POST https://playseat.local/api/v1/adapt/mesh/peers/01954c03-bnd-7f00-mesh-peer00000003/trust \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "dimension": "timeliness",
    "score": 0.62,
    "reason": "Average 18 hours from detection to sharing. Slow but thorough."
  }'
```

### Trust History Query

```bash
curl -s https://playseat.local/api/v1/adapt/mesh/peers/01954c03-bnd-7f00-mesh-peer00000003/trust \
  -H "Authorization: Bearer $TOKEN" | jq
```

```json
[
  {
    "id": "01954c10-trust-7f00-score-000000008",
    "peer_id": "01954c03-bnd-7f00-mesh-peer00000003",
    "dimension": "timeliness",
    "score": 0.62,
    "reason": "Average 18 hours from detection to sharing. Slow but thorough.",
    "scored_by": "01954b39-1234-7f00-aaaa-bbbbccccdddd",
    "scored_at": "2026-02-16T11:30:00Z"
  },
  {
    "id": "01954c10-trust-7f00-score-000000007",
    "peer_id": "01954c03-bnd-7f00-mesh-peer00000003",
    "dimension": "intel_quality",
    "score": 0.97,
    "reason": "Every IOC verified. Zero false positives. The Germans are meticulous.",
    "scored_by": "01954b39-1234-7f00-aaaa-bbbbccccdddd",
    "scored_at": "2026-02-16T11:25:00Z"
  }
]
```

### Trust Decay

Trust rots if you go silent. I built this in because if a peer disappears for thirty days without sharing, they're either compromised, bureaucratically paralyzed, or playing games. None of those scenarios earns my confidence.

```sql
-- Decay trust for peers not seen in 30+ days
UPDATE adapt_mesh_peers
SET trust_score = GREATEST(trust_score * 0.95, 0.1),
    updated_at = NOW()
WHERE active = true
  AND last_seen_at < NOW() - INTERVAL '30 days';

-- Find stale peers
SELECT name, organization, trust_score, last_seen_at,
    EXTRACT(EPOCH FROM (NOW() - last_seen_at)) / 86400 AS days_since_seen
FROM adapt_mesh_peers
WHERE active = true
ORDER BY last_seen_at ASC;
```

A 5% decay per 30-day window. A silent peer drops from 0.885 to about 0.66 in six months. Still in the mesh, but their intel gets lower weight.

I thought about Clara when I wrote the decay function. She'd been silent for 42 days. If she were a peer in the mesh, her trust score would've dropped by now. But she's not a peer. She's a person. And people don't decay on a schedule. They disappear in places where schedules don't exist.

---

## The First Push: Clara's PHANTOM MERCY IOCs

I had to be careful with this. I couldn't share anything that identified Clara. Her operational security -- and possibly her life -- depended on it. But I could share the intelligence she'd gathered about PHANTOM MERCY's digital infrastructure. Stripped of her name. Stripped of her DGSE affiliation. Just the IOCs.

### Share PHANTOM MERCY Infrastructure IOCs

```bash
curl -s -X POST https://playseat.local/api/v1/adapt/mesh/share \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "peer_id": "01954c01-nato-7f00-mesh-peer00000001",
    "intel_type": "ioc_package",
    "intel_payload": {
      "title": "PHANTOM MERCY Logistics Network - Digital Infrastructure IOCs",
      "description": "C2 domains and IPs for trafficking network using humanitarian logistics as cover. Operating across Sahel, Eastern Mediterranean, and Balkans. Network manipulates shipping manifests and aid coordination databases.",
      "iocs": [
        {
          "type": "domain",
          "value": "sahel-logistics-coord.syntheticexample.net",
          "confidence": "high",
          "first_seen": "2025-11-15T00:00:00Z",
          "last_seen": "2026-02-10T23:59:59Z"
        },
        {
          "type": "domain",
          "value": "aid-manifest-portal.syntheticexample.org",
          "confidence": "high",
          "first_seen": "2025-12-01T00:00:00Z",
          "last_seen": "2026-02-12T12:00:00Z"
        },
        {
          "type": "ip",
          "value": "198.51.100.73",
          "confidence": "medium",
          "first_seen": "2025-11-15T00:00:00Z",
          "last_seen": "2026-01-28T00:00:00Z"
        },
        {
          "type": "ip",
          "value": "203.0.113.141",
          "confidence": "high",
          "first_seen": "2026-01-05T00:00:00Z",
          "last_seen": "2026-02-14T00:00:00Z"
        },
        {
          "type": "hash_sha256",
          "value": "d7a3f891c4e5b6f708192a3b4c5d6e7f8091a2b3c4d5e6f708192a3b4c5d6e7f",
          "confidence": "high",
          "first_seen": "2026-01-10T00:00:00Z",
          "malware_family": "ManifestForger"
        }
      ],
      "ttps": ["T1036.005", "T1565.001", "T1078.004", "T1071.001"],
      "tlp": "TLP:GREEN",
      "source": "playseat_independent_analysis",
      "operation_reference": "PHANTOM-MERCY-2026"
    },
    "classification": "TLP:GREEN"
  }'
```

```json
{
  "id": "01954c20-share-7f00-intel-000000001"
}
```

I pushed the same package to all three peers:

```bash
for PEER_ID in \
  "01954c01-nato-7f00-mesh-peer00000001" \
  "01954c02-cert-7f00-mesh-peer00000002" \
  "01954c03-bnd-7f00-mesh-peer00000003"; do

  curl -s -X POST https://playseat.local/api/v1/adapt/mesh/share \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d "{
      \"peer_id\": \"$PEER_ID\",
      \"intel_type\": \"ioc_package\",
      \"intel_payload\": {
        \"title\": \"PHANTOM MERCY Logistics Network - Infrastructure IOCs\",
        \"description\": \"Trafficking network using humanitarian logistics cover. Digital manifest manipulation. Seeking any corroborating intelligence.\",
        \"operation_reference\": \"PHANTOM-MERCY-2026\",
        \"iocs\": [
          {\"type\": \"domain\", \"value\": \"sahel-logistics-coord.syntheticexample.net\"},
          {\"type\": \"domain\", \"value\": \"aid-manifest-portal.syntheticexample.org\"},
          {\"type\": \"ip\", \"value\": \"198.51.100.73\"},
          {\"type\": \"ip\", \"value\": \"203.0.113.141\"},
          {\"type\": \"hash_sha256\", \"value\": \"d7a3f891c4e5b6f708192a3b4c5d6e7f8091a2b3c4d5e6f708192a3b4c5d6e7f\"}
        ],
        \"ttps\": [\"T1036.005\", \"T1565.001\", \"T1078.004\", \"T1071.001\"],
        \"tlp\": \"TLP:GREEN\",
        \"urgency\": \"high\"
      },
      \"classification\": \"TLP:GREEN\"
    }"
done
```

### Sensitive Intel: Clara's Analysis (TLP:AMBER -- BND Only)

There was one piece I shared only with the BND. Clara's cryptographic analysis of the manifest-forging algorithm. She'd reverse-engineered the mathematical transformation PHANTOM MERCY used to alter cargo weights in the shipping database. It was brilliant work -- pure Clara. But sharing it openly would reveal that someone had been inside their systems. Someone who might still be alive.

```bash
curl -s -X POST https://playseat.local/api/v1/adapt/mesh/share \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "peer_id": "01954c03-bnd-7f00-mesh-peer00000003",
    "intel_type": "attribution_assessment",
    "intel_payload": {
      "title": "PHANTOM MERCY Manifest Forgery Algorithm Analysis - AMBER",
      "description": "Cryptographic analysis of the algorithm used to modify shipping manifest weights. The transformation applies a deterministic offset to declared tonnage, making forgeries internally consistent across database replicas. This analysis was performed by an asset who may be compromised. Handle accordingly.",
      "assessment": {
        "threat_actor": "PHANTOM MERCY",
        "confidence": "high",
        "motivation": "trafficking_logistics",
        "sophistication": "advanced",
        "operating_regions": ["sahel", "eastern_mediterranean", "balkans"],
        "manifest_algorithm": "deterministic_weight_offset_with_hash_consistency",
        "source_status": "unknown -- asset dark since Jan 3 2026"
      },
      "tlp": "TLP:AMBER"
    },
    "classification": "TLP:AMBER"
  }'
# {"id": "01954c21-share-7f00-intel-000000002"}
```

I stared at the words "asset dark since Jan 3 2026" for a long time before I sent that. She's not an asset. She's Clara. But to the BND, that's all she can be.

### Listing All Shared Intel

```bash
curl -s https://playseat.local/api/v1/adapt/mesh/shared \
  -H "Authorization: Bearer $TOKEN" | jq '.[] | {id, peer_id, direction, intel_type, classification, shared_at}'
```

```json
{
  "id": "01954c20-share-7f00-intel-000000001",
  "peer_id": "01954c01-nato-7f00-mesh-peer00000001",
  "direction": "push",
  "intel_type": "ioc_package",
  "classification": "TLP:GREEN",
  "shared_at": "2026-02-14T22:00:00Z"
}
{
  "id": "01954c20-share-7f00-intel-000000003",
  "peer_id": "01954c02-cert-7f00-mesh-peer00000002",
  "direction": "push",
  "intel_type": "ioc_package",
  "classification": "TLP:GREEN",
  "shared_at": "2026-02-14T22:01:00Z"
}
{
  "id": "01954c20-share-7f00-intel-000000004",
  "peer_id": "01954c03-bnd-7f00-mesh-peer00000003",
  "direction": "push",
  "intel_type": "ioc_package",
  "classification": "TLP:GREEN",
  "shared_at": "2026-02-14T22:02:00Z"
}
{
  "id": "01954c21-share-7f00-intel-000000002",
  "peer_id": "01954c03-bnd-7f00-mesh-peer00000003",
  "direction": "push",
  "intel_type": "attribution_assessment",
  "classification": "TLP:AMBER",
  "shared_at": "2026-02-14T22:10:00Z"
}
```

Four pushes. Three GREEN packages to everyone. One AMBER assessment to the BND only.

Then I waited.

Waiting is the worst part of intelligence work. You push intel into the void and you hope the void pushes something back. I refreshed the sync log every twenty minutes for three days. I slept on the couch in the SOC. I dreamed about Niamey, about dust and heat and Clara's voice saying *"deviation in manifest delta"* like it was the most natural phrase in the world.

---

## Receiving Intel from Peers

Three days after the push, the mesh started delivering.

### CERT-EU Response: Humanitarian Network Compromise

```bash
# Incoming from CERT-EU
curl -s -X POST https://playseat.local/api/v1/adapt/mesh/share \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "peer_id": "01954c02-cert-7f00-mesh-peer00000002",
    "intel_type": "corroborating_intel",
    "intel_payload": {
      "operation": "PHANTOM-MERCY-2026",
      "source": "cert_eu_humanitarian_monitoring",
      "observation": "We have been tracking anomalous database modifications in the EU-funded Sahel Aid Coordination Platform (SACP) since December 2025. Shipping manifests for three NGO logistics partners show systematic discrepancies between declared and actual cargo weights. Average deviation: 12-18% per shipment. Pattern is consistent with your PHANTOM MERCY assessment.",
      "additional_iocs": [
        {"type": "domain", "value": "sacp-admin.syntheticexample.eu", "confidence": "high"},
        {"type": "ip", "value": "198.51.100.89", "confidence": "medium"},
        {"type": "email", "value": "logistics-coord@syntheticaid.org", "confidence": "high"}
      ],
      "additional_ttps": ["T1565.001", "T1114.002"],
      "note": "We see the manifest manipulation but did not have attribution until your IOCs correlated with our data. Database access originates from compromised admin credentials in the SACP platform.",
      "tlp": "TLP:GREEN"
    },
    "classification": "TLP:GREEN"
  }'
```

CERT-EU confirmed the pattern. The Sahel Aid Coordination Platform was compromised. Manifests were being altered. Average deviation: 12-18% per shipment. That's exactly what Clara described. She was right. She was always right.

### NATO NCIRC Response: Balkans Logistics

```bash
curl -s -X POST https://playseat.local/api/v1/adapt/mesh/share \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "peer_id": "01954c01-nato-7f00-mesh-peer00000001",
    "intel_type": "corroborating_intel",
    "intel_payload": {
      "operation": "PHANTOM-MERCY-2026",
      "source": "nato_ncirc_supply_chain_monitoring",
      "observation": "Your PHANTOM MERCY domain sahel-logistics-coord.syntheticexample.net shares DNS infrastructure with a domain we have been tracking in the Balkans context: balkan-transit-hub.syntheticexample.net. Both resolve through the same bulletproof hosting provider. The Balkans domain is associated with logistics fraud targeting humanitarian aid shipments to Bosnia.",
      "additional_iocs": [
        {"type": "domain", "value": "balkan-transit-hub.syntheticexample.net", "confidence": "high"},
        {"type": "ip", "value": "203.0.113.156", "confidence": "medium"},
        {"type": "hash_sha256", "value": "e8b4f901d5c6a7e809203b4d5c6e7f80a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6", "confidence": "high"}
      ],
      "note": "Shared DNS infrastructure strongly suggests same operator across Sahel and Balkans operations. Consistent with your multi-region assessment.",
      "tlp": "TLP:GREEN"
    },
    "classification": "TLP:GREEN"
  }'
```

NATO connected the Sahel and Balkans operations via shared DNS infrastructure. Clara had said Balkans. She'd mapped this before anyone else.

### Trust-Weighted Confidence Scoring

I don't blindly trust what peers send. Every received intel piece gets confidence-scored:

```sql
SELECT
    si.id,
    si.intel_type,
    si.intel_payload->>'title' AS title,
    si.classification,
    mp.name AS peer_name,
    mp.trust_score,
    CASE
        WHEN mp.trust_score >= 0.8 THEN 'high'
        WHEN mp.trust_score >= 0.5 THEN 'medium'
        ELSE 'low'
    END AS effective_confidence,
    si.shared_at
FROM adapt_mesh_shared_intel si
JOIN adapt_mesh_peers mp ON mp.id = si.peer_id
WHERE si.direction = 'push'
ORDER BY si.shared_at DESC;
```

Both NATO and CERT-EU had earned trust scores above 0.8 by this point. Their corroborations landed as high-confidence.

But the intel that mattered -- the one that cracked the case open -- came from the BND.

---

## The BND Lead -- Callsign PASSERELLE

**February 17, 2026. 02:47 UTC.**

I was half-asleep on the SOC couch when the sync notification fired. BND Cyber Division had pushed an AMBER-classified intel package. My hands fumbled with the laptop in the dark. I pulled up the mesh shared intel feed with one eye open and both hands shaking.

```bash
# BND incoming -- simulated
curl -s -X POST https://playseat.local/api/v1/adapt/mesh/share \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "peer_id": "01954c03-bnd-7f00-mesh-peer00000003",
    "intel_type": "sigint_correlation",
    "intel_payload": {
      "operation": "PHANTOM-MERCY-2026",
      "source": "bnd_sigint_sahel_monitoring",
      "classification_note": "AMBER -- limited distribution",
      "observation": "On 2026-02-11, our Sahel SIGINT collection intercepted a burst HF transmission from coordinates approximately 13.5N 2.1E (Niamey region, Niger). The transmission used a known DGSE field encoding protocol. Within the encoded payload, we identified the callsign PASSERELLE. Cross-referencing with your PHANTOM MERCY asset assessment, PASSERELLE matches the operational profile of your source who went dark on January 3.",
      "assessment": {
        "callsign": "PASSERELLE",
        "intercept_date": "2026-02-11T14:32:00Z",
        "intercept_location": "13.5N 2.1E -- Niamey region, Niger",
        "encoding_protocol": "DGSE field burst, HF band",
        "signal_duration_ms": 340,
        "content_summary": "Partial decode only. Keywords extracted: MERCY, MANIFEST, ENFANTS, PHOTOGRAPHIER. Full decode requires DGSE cooperation.",
        "analyst_note": "If PASSERELLE is your asset, she was alive and transmitting eleven days ago. The brevity and encoding suggest she is operational but constrained. Recommend immediate coordination with DGSE Directorate of Intelligence."
      },
      "tlp": "TLP:AMBER"
    },
    "classification": "TLP:AMBER"
  }'
```

I read it three times. Then I read it again.

PASSERELLE. *Passerelle*. It's French for footbridge. Clara used it as her field callsign because she said she was a bridge between the world of cryptography and the world of action. I'd teased her about it once. She'd thrown a pillow at me and said it was better than naming yourself after a chess piece.

February 11. She was alive on February 11. Transmitting in the Niamey region. Using DGSE field burst encoding on HF -- the kind of transmission you make when you have no satellite, no internet, no cellphone. Just a field radio and a few hundred milliseconds of hope.

The keywords: MERCY, MANIFEST, ENFANTS, PHOTOGRAPHIER.

PHANTOM MERCY. Manifests. Children. Photographing.

She was still working. Still collecting evidence. Still inside the network.

I sat in the dark with my laptop screen burning my retinas, and I did something I hadn't done since I was eight years old. I cried.

Then I wiped my face, poured three fingers of cold coffee, and got to work.

### Record the BND Lead as a Finding

```bash
curl -s -X POST https://playseat.local/api/v1/adapt/mesh/share \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "peer_id": "01954c03-bnd-7f00-mesh-peer00000003",
    "intel_type": "acknowledgment",
    "intel_payload": {
      "operation": "PHANTOM-MERCY-2026",
      "message": "PASSERELLE correlation confirmed on our end. Requesting ongoing monitoring of Niamey region HF spectrum for additional burst transmissions matching DGSE field protocol. Will coordinate with French counterparts through diplomatic channels. Priority: IMMEDIATE.",
      "tlp": "TLP:AMBER"
    },
    "classification": "TLP:AMBER"
  }'
```

---

## Sync Log Monitoring

After the BND lead, I ran syncs obsessively. Every six hours. Looking for any follow-up transmission.

### Trigger a Sync

```bash
# Sync with BND
curl -s -X POST https://playseat.local/api/v1/adapt/mesh/sync/01954c03-bnd-7f00-mesh-peer00000003 \
  -H "Authorization: Bearer $TOKEN"
```

```json
{
  "id": "01954c30-sync-7f00-log-0000000001"
}
```

The backend records everything:

```rust
// From the route handler:
sqlx::query(
    "INSERT INTO adapt_mesh_sync_log (id, peer_id, direction, items_sent, items_received, \
     status, started_at) \
     VALUES ($1, $2, 'bidirectional', 0, 0, 'running', NOW())"
)
.bind(id)
.bind(peer_id)
.execute(&state.db)
.await?;

// Update peer last_seen
sqlx::query(
    "UPDATE adapt_mesh_peers SET last_seen_at = NOW(), updated_at = NOW() WHERE id = $1"
)
.bind(peer_id)
.execute(&state.db)
.await;

// Mark sync as completed
sqlx::query(
    "UPDATE adapt_mesh_sync_log SET status = 'completed', completed_at = NOW() WHERE id = $1"
)
.bind(id)
.execute(&state.db)
.await;
```

### View Sync Log

```bash
curl -s https://playseat.local/api/v1/adapt/mesh/sync-log \
  -H "Authorization: Bearer $TOKEN" | jq '.[] | {id, peer_id, direction, status, started_at, completed_at}'
```

```json
{
  "id": "01954c30-sync-7f00-log-0000000001",
  "peer_id": "01954c03-bnd-7f00-mesh-peer00000003",
  "direction": "bidirectional",
  "status": "completed",
  "started_at": "2026-02-17T03:15:00Z",
  "completed_at": "2026-02-17T03:15:04Z"
}
{
  "id": "01954c30-sync-7f00-log-0000000002",
  "peer_id": "01954c01-nato-7f00-mesh-peer00000001",
  "direction": "bidirectional",
  "status": "completed",
  "started_at": "2026-02-17T03:20:00Z",
  "completed_at": "2026-02-17T03:20:02Z"
}
{
  "id": "01954c30-sync-7f00-log-0000000003",
  "peer_id": "01954c02-cert-7f00-mesh-peer00000002",
  "direction": "bidirectional",
  "status": "completed",
  "started_at": "2026-02-17T03:25:00Z",
  "completed_at": "2026-02-17T03:25:03Z"
}
```

### Sync Analytics

```sql
-- Sync frequency and health per peer
SELECT
    mp.name AS peer_name,
    COUNT(sl.id) AS total_syncs,
    COUNT(CASE WHEN sl.status = 'completed' THEN 1 END) AS successful_syncs,
    COUNT(CASE WHEN sl.status = 'failed' THEN 1 END) AS failed_syncs,
    ROUND(100.0 * COUNT(CASE WHEN sl.status = 'completed' THEN 1 END) / COUNT(sl.id), 1) AS success_rate,
    MAX(sl.completed_at) AS last_successful_sync
FROM adapt_mesh_peers mp
LEFT JOIN adapt_mesh_sync_log sl ON sl.peer_id = mp.id
WHERE mp.active = true
GROUP BY mp.name
ORDER BY total_syncs DESC;
```

```
 peer_name           | total_syncs | successful | failed | success_rate | last_successful_sync
---------------------+-------------+------------+--------+--------------+----------------------
 BND Cyber Division  | 31          | 31         | 0      | 100.0        | 2026-02-17T03:15:04Z
 NATO NCIRC          | 28          | 27         | 1      | 96.4         | 2026-02-17T03:20:02Z
 CERT-EU             | 24          | 24         | 0      | 100.0        | 2026-02-17T03:25:03Z
```

I'd synced with the BND more than anyone else. Thirty-one times in two weeks. The numbers told their own story about where my attention was.

---

## Privacy Controls: Protecting Clara While Searching for Her

This is the part that kept me up at night. I needed to share enough about PHANTOM MERCY to get useful intel back. But I couldn't share anything that would identify Clara, compromise her cover, or tip off PHANTOM MERCY that someone was close to them.

### The Rules

1. **TLP:RED never enters the sharing pipeline.** Clara's identity, her DGSE affiliation, her personal details -- all TLP:RED. Locked in my local database. Never touches the mesh.

2. **TLP:AMBER is trust-gated.** Only peers above 0.7 trust get AMBER intel. The BND earned AMBER access through quality sharing. The others haven't yet.

3. **Metadata-only sharing for sensitive contexts.** When I needed to hint that we had a source inside PHANTOM MERCY without revealing who:

```bash
curl -s -X POST https://playseat.local/api/v1/adapt/mesh/share \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "peer_id": "01954c01-nato-7f00-mesh-peer00000001",
    "intel_type": "metadata_only",
    "intel_payload": {
      "title": "PHANTOM MERCY -- Source Reporting Available",
      "category": "trafficking_logistics",
      "severity": "critical",
      "region": "sahel",
      "note": "We have source reporting from inside the PHANTOM MERCY logistics network. Manifest forgery algorithm has been analyzed. Details available at TLP:AMBER upon trust score qualification.",
      "tlp": "TLP:AMBER+STRICT"
    },
    "classification": "TLP:AMBER+STRICT"
  }'
```

NATO knows something exists. They don't know it came from a French cryptographer who's been dark for six weeks. They don't know I'm searching for her while pretending to build a threat intel platform.

### Audit Query: Complete Outbound Sharing Log

```sql
-- What did we share, with whom, about Clara?
SELECT
    mp.name AS peer_name,
    si.intel_type,
    si.classification,
    si.intel_payload->>'title' AS intel_title,
    si.shared_at,
    si.shared_by
FROM adapt_mesh_shared_intel si
JOIN adapt_mesh_peers mp ON mp.id = si.peer_id
WHERE si.direction = 'push'
  AND si.intel_payload->>'operation' = 'PHANTOM-MERCY-2026'
ORDER BY si.shared_at DESC;
```

This is my accountability log. If anyone ever asks what I shared and with whom, every entry is timestamped, user-attributed, and TLP-classified. I'm searching for Clara within the rules. Bending them, maybe. But not breaking them.

---

## Mesh Health and the Waiting Game

After the BND lead, I monitored the mesh health obsessively.

### Mesh Status

```bash
curl -s https://playseat.local/api/v1/adapt/mesh/status \
  -H "Authorization: Bearer $TOKEN" | jq
```

```json
{
  "active_peers": 3,
  "average_trust_score": 0.76,
  "syncs_last_24h": 9,
  "mesh_healthy": true
}
```

Three active peers. Average trust of 0.76 -- above the AMBER threshold. Nine syncs in the last 24 hours. The mesh is healthy.

The `mesh_healthy` flag is computed server-side:

```rust
"mesh_healthy": total_peers.0 > 0 && avg_trust.0 > 0.3
```

### Aggregate Statistics

```bash
curl -s https://playseat.local/api/v1/adapt/mesh/stats \
  -H "Authorization: Bearer $TOKEN" | jq
```

```json
{
  "total_peers": 3,
  "active_peers": 3,
  "shared_intel_count": 11,
  "total_syncs": 83
}
```

Eleven intel packages shared. Eighty-three syncs. One confirmed sighting of a woman alive in Niamey.

### Network Capability Map

```bash
curl -s https://playseat.local/api/v1/adapt/mesh/capabilities \
  -H "Authorization: Bearer $TOKEN" | jq
```

```json
{
  "peer_count": 3,
  "unique_capabilities": [
    "apt_tracking",
    "comms_intercept",
    "humanitarian_network_monitoring",
    "incident_response",
    "ioc_sharing",
    "logistics_security",
    "sahel_monitoring",
    "sigint_correlation",
    "threat_intel"
  ],
  "capability_count": 9
}
```

Nine capabilities across three peers. The one that mattered was `sahel_monitoring`. That was the BND's ear pressed against the frequencies where Clara might transmit.

### Health Monitoring SQL

```sql
-- Peers that haven't synced in 7+ days
SELECT name, organization, trust_score, last_seen_at,
    NOW() - last_seen_at AS time_since_last_seen
FROM adapt_mesh_peers
WHERE active = true
  AND last_seen_at < NOW() - INTERVAL '7 days'
ORDER BY last_seen_at ASC;

-- Intel sharing velocity by day
SELECT
    DATE(shared_at) AS share_date,
    COUNT(*) AS intel_packages_shared,
    COUNT(DISTINCT peer_id) AS unique_peers_involved
FROM adapt_mesh_shared_intel
WHERE shared_at > NOW() - INTERVAL '30 days'
GROUP BY DATE(shared_at)
ORDER BY share_date DESC;

-- Average trust scores across the mesh
SELECT
    ROUND(AVG(trust_score)::numeric, 3) AS avg_trust,
    MIN(trust_score) AS min_trust,
    MAX(trust_score) AS max_trust,
    COUNT(*) AS peer_count
FROM adapt_mesh_peers
WHERE active = true;
```

I ran these queries every morning before coffee. They'd become a ritual. Check the mesh. Check the sync log. Check if anyone had heard Clara's voice on the radio.

---

## Database Schema

The complete Mesh subsystem schema:

```sql
-- Peer registry
CREATE TABLE IF NOT EXISTS adapt_mesh_peers (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_name        TEXT NOT NULL,
    peer_url        TEXT NOT NULL,
    api_key_hash    TEXT,
    name            TEXT,
    endpoint_url    TEXT,
    organization    TEXT,
    trust_score     DOUBLE PRECISION NOT NULL DEFAULT 0.5,
    active          BOOLEAN NOT NULL DEFAULT true,
    status          TEXT NOT NULL DEFAULT 'pending',
    capabilities    TEXT[] DEFAULT '{}',
    last_seen_at    TIMESTAMPTZ,
    joined_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_by      UUID,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Shared intelligence records
CREATE TABLE IF NOT EXISTS adapt_mesh_shared_intel (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    peer_id         UUID REFERENCES adapt_mesh_peers(id) ON DELETE CASCADE,
    direction       TEXT NOT NULL DEFAULT 'outbound',
    intel_type      TEXT NOT NULL,
    intel_payload   JSONB NOT NULL DEFAULT '{}',
    classification  TEXT,
    confidence      REAL NOT NULL DEFAULT 0.5,
    shared_at       TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    shared_by       UUID
);

-- Multi-dimensional trust scores
CREATE TABLE IF NOT EXISTS adapt_mesh_trust_scores (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    peer_id         UUID REFERENCES adapt_mesh_peers(id) ON DELETE CASCADE,
    dimension       TEXT NOT NULL,
    score           REAL NOT NULL DEFAULT 0.5,
    reason          TEXT,
    scored_by       UUID,
    scored_at       TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Synchronization log
CREATE TABLE IF NOT EXISTS adapt_mesh_sync_log (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    peer_id         UUID REFERENCES adapt_mesh_peers(id) ON DELETE CASCADE,
    direction       TEXT NOT NULL DEFAULT 'bidirectional',
    items_sent      INTEGER NOT NULL DEFAULT 0,
    items_received  INTEGER NOT NULL DEFAULT 0,
    status          TEXT NOT NULL DEFAULT 'in_progress',
    error_message   TEXT,
    started_at      TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    completed_at    TIMESTAMP WITH TIME ZONE
);
```

---

## API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/adapt/mesh/peers` | Register a new mesh peer |
| GET | `/api/v1/adapt/mesh/peers` | List all peers |
| GET | `/api/v1/adapt/mesh/peers/{id}` | Get peer details |
| PUT | `/api/v1/adapt/mesh/peers/{id}` | Update peer config |
| DELETE | `/api/v1/adapt/mesh/peers/{id}` | Remove a peer |
| POST | `/api/v1/adapt/mesh/share` | Share intel with a peer |
| GET | `/api/v1/adapt/mesh/shared` | List all shared intel |
| POST | `/api/v1/adapt/mesh/peers/{id}/trust` | Add a trust score dimension |
| GET | `/api/v1/adapt/mesh/peers/{id}/trust` | Get trust score history |
| POST | `/api/v1/adapt/mesh/sync/{id}` | Trigger sync with a peer |
| GET | `/api/v1/adapt/mesh/sync-log` | View sync history |
| GET | `/api/v1/adapt/mesh/status` | Mesh health status |
| GET | `/api/v1/adapt/mesh/capabilities` | Aggregate capability map |
| GET | `/api/v1/adapt/mesh/stats` | Mesh statistics |

---

## What the Mesh Told Me

The Mesh turned three isolated bureaucracies into a connected search party. NATO confirmed PHANTOM MERCY's multi-region infrastructure. CERT-EU confirmed the manifest manipulation pattern. The BND -- God bless the BND and their Sahel SIGINT arrays -- confirmed that Clara was alive eleven days ago.

I built the trust scoring so that good intelligence rises and noise sinks. I built the TLP enforcement so that Clara's identity stays protected even as we search for her. I built the sync log so that every question I ask and every answer I receive is recorded, timestamped, and auditable.

The mesh works. It solved in two weeks a trust problem that governments have been failing to solve with committees for twenty years. The math handles the trust. The TLP handles the classification. The audit log handles the accountability.

But the mesh also told me something I wasn't ready for. The BND analyst's note said: *"she is operational but constrained."* Constrained. That word could mean a lot of things. It could mean she's hiding. It could mean she's captured but has access to a radio. It could mean she's being moved and found a window.

I don't know which one. But I know she's alive. And I know PHANTOM MERCY is real. And I know the next step is to set up Sentinel baselines on every logistics network Clara touched -- because if I can see the manifest deviations in real time, I can see where PHANTOM MERCY is operating right now. And where they're operating is where Clara is.

---

*Next chapter: we use Sentinel to baseline the aid network where Clara worked -- and the patterns we find are exactly what she warned us about.*

---

(c) 2026 Playseat -- All Rights Reserved | Defensive Intelligence Through ADAPT
