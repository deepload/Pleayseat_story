# Chapter 25: The Knowledge Graph — Connecting Everything

> "We had 47,000 indicators in the database. IP addresses, domains, hashes, threat actors, CVEs. All of them sitting in tables like polite strangers at a dinner party. Nobody was talking to anybody. Then we turned on the ontology engine and ran a single graph traversal from one suspicious IP address. Fourteen minutes later we were staring at a campaign network that had been operating inside our infrastructure for nine months."
> — Senior Intelligence Analyst, post-deployment debrief, January 2026

---

## Why This Chapter Exists

Intelligence without context is trivia. A list of 10,000 IOCs is a spreadsheet. A graph of 10,000 IOCs with relationships, confidence scores, and traversal paths is a weapon.

Every chapter in this book has produced data: findings, incidents, red team results, AI triage classifications, evidence chains. Each of those data points is an entity. And every entity is connected to other entities in ways that matter. An IP address resolves to a domain. A domain hosts malware. That malware exploits a CVE. That CVE targets an asset. That asset belongs to a campaign. That campaign is attributed to a threat actor.

Playseat's ontology system is how we make those connections explicit, queryable, and traversable. It is not a graph database -- it is a graph layer built on PostgreSQL, powered by recursive CTEs, and designed for intelligence analysts who need to follow a thread from a single indicator to an entire adversary operation in minutes, not days.

This chapter covers the complete ontology system: 12 entity types, 10 relationship types, graph traversal with recursive CTEs, shortest path finding, entity resolution (deduplication), timeline analysis, and a real scenario where a single IOC unraveled a nine-month campaign.

I built this system because I was tired of switching between six different tools to answer one question: "What does this IP address connect to?"

---

## The Ontology Data Model

### Entity Types

The ontology defines 12 canonical entity types. These are not arbitrary -- they represent the fundamental objects in cyber threat intelligence, aligned with STIX 2.1 observable types and extended for defensive operations.

From `crates/svc-ontology/src/entity.rs`:

```rust
/// The 12 canonical entity types in the ontology.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub enum EntityType {
    IpAddress,
    Domain,
    Hostname,
    Url,
    Email,
    UserAccount,
    Asset,
    Cve,
    Ioc,
    ThreatActor,
    Malware,
    Campaign,
}
```

Each type has three representations: the Rust enum variant, a database-canonical snake_case name, and a human-readable display name:

| Rust Variant | DB Name | Display |
|-------------|---------|---------|
| `IpAddress` | `ip_address` | IP Address |
| `Domain` | `domain` | Domain |
| `Hostname` | `hostname` | Hostname |
| `Url` | `url` | URL |
| `Email` | `email` | Email |
| `UserAccount` | `user_account` | User Account |
| `Asset` | `asset` | Asset |
| `Cve` | `cve` | CVE |
| `Ioc` | `ioc` | IOC |
| `ThreatActor` | `threat_actor` | Threat Actor |
| `Malware` | `malware` | Malware |
| `Campaign` | `campaign` | Campaign |

Parsing is case-insensitive and supports multiple formats:

```rust
EntityType::parse("ip_address")   // Some(IpAddress)
EntityType::parse("IpAddress")    // Some(IpAddress)
EntityType::parse("ip")           // Some(IpAddress)
EntityType::parse("DOMAIN")       // Some(Domain)
EntityType::parse("threat_actor") // Some(ThreatActor)
EntityType::parse("threatactor")  // Some(ThreatActor)
```

This matters when you are ingesting data from five different threat intel feeds that each spell "IP address" differently.

### Relationship Types

From `crates/svc-ontology/src/relationship.rs`, the 10 canonical relationship types:

```rust
pub enum RelationshipType {
    CommunicatesWith,
    ResolvesTo,
    Exploits,
    Targets,
    AssociatedWith,
    Hosts,
    Delivers,
    Drops,
    UsesTechnique,
    AttributedTo,
}
```

Each relationship has a weight (0.0 to 10.0) and a confidence score (0.0 to 1.0). The combined relevance score is `weight * confidence`, clamped to [0.0, 10.0]:

```rust
pub fn compute_combined_score(weight: f64, confidence: f64) -> f64 {
    (weight * confidence).clamp(0.0, 10.0)
}
```

This scoring system is critical for graph traversal. When you are following a path through the graph, you want to prioritize high-confidence, high-weight relationships. A "communicates_with" relationship with weight 9.0 and confidence 0.95 (combined: 8.55) is a different signal than one with weight 2.0 and confidence 0.3 (combined: 0.6).

### The Database Schema

From migration `220_ontology_system.sql`:

```sql
-- Entity types: the taxonomy of things that exist in the graph
CREATE TABLE IF NOT EXISTS ontology_entity_types (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL UNIQUE,
    display_name TEXT NOT NULL,
    description TEXT,
    icon TEXT,
    color TEXT,
    schema JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Entities: the actual nodes in the graph
CREATE TABLE IF NOT EXISTS ontology_entities (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_type_id UUID NOT NULL REFERENCES ontology_entity_types(id),
    name TEXT NOT NULL,
    properties JSONB DEFAULT '{}',
    confidence FLOAT8 DEFAULT 0.5,
    source TEXT,
    first_seen TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_seen TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Relationship types: the taxonomy of edges
CREATE TABLE IF NOT EXISTS ontology_relationship_types (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL UNIQUE,
    display_name TEXT NOT NULL,
    description TEXT,
    source_types JSONB,
    target_types JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Relationships: the actual edges in the graph
CREATE TABLE IF NOT EXISTS ontology_relationships (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    relationship_type_id UUID NOT NULL REFERENCES ontology_relationship_types(id),
    source_entity_id UUID NOT NULL REFERENCES ontology_entities(id),
    target_entity_id UUID NOT NULL REFERENCES ontology_entities(id),
    weight FLOAT8 DEFAULT 1.0,
    confidence FLOAT8 DEFAULT 0.5,
    properties JSONB DEFAULT '{}',
    evidence_ids JSONB DEFAULT '[]',
    first_seen TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_seen TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Timeline events for entities
CREATE TABLE IF NOT EXISTS ontology_timeline (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_id UUID NOT NULL REFERENCES ontology_entities(id),
    event_type TEXT NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    metadata JSONB,
    occurred_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Entity resolutions (deduplication records)
CREATE TABLE IF NOT EXISTS ontology_resolutions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_entity_id UUID REFERENCES ontology_entities(id),
    target_entity_id UUID REFERENCES ontology_entities(id),
    strategy TEXT,
    similarity_score FLOAT8,
    resolved_by UUID,
    resolved_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Entity tags
CREATE TABLE IF NOT EXISTS ontology_tags (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_id UUID NOT NULL REFERENCES ontology_entities(id),
    tag TEXT NOT NULL,
    created_by UUID,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(entity_id, tag)
);
```

Six tables. That is the entire ontology system. Entities, relationships, types for both, timeline events, resolution records, and tags. Everything else -- graph traversal, path finding, entity resolution, community detection -- is built on top of these six tables using SQL and Rust.

---

## Building the Graph: Entities and Relationships

### Creating Entity Types

Before you can create entities, you need entity types. Think of these as the schema for your graph nodes.

```bash
# Create the 12 canonical entity types
curl -X POST https://playseat.internal/api/v1/ontology/types \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "ip_address",
    "display_name": "IP Address",
    "description": "An IPv4 or IPv6 network address",
    "icon": "globe",
    "color": "#3B82F6",
    "schema": {
      "type": "object",
      "properties": {
        "version": {"type": "string", "enum": ["v4", "v6"]},
        "asn": {"type": "integer"},
        "geo_country": {"type": "string"},
        "geo_city": {"type": "string"},
        "is_tor_exit": {"type": "boolean"},
        "is_known_proxy": {"type": "boolean"}
      }
    }
  }'
```

Response:

```json
{
  "id": "019505e0-0000-7000-8000-000000000001",
  "status": "entity_type_created:ip_address"
}
```

### Creating Entities

```bash
# Create an IP address entity
curl -X POST https://playseat.internal/api/v1/ontology/entities \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "entity_type_id": "019505e0-0000-7000-8000-000000000001",
    "name": "198.51.100.42",
    "properties": {
      "version": "v4",
      "asn": 13335,
      "geo_country": "US",
      "geo_city": "San Jose",
      "is_tor_exit": false,
      "is_known_proxy": true,
      "ports_open": [80, 443, 8080, 8443],
      "last_scan_date": "2026-02-10"
    },
    "confidence": 0.95,
    "source": "passive-dns-enrichment"
  }'
```

Response:

```json
{
  "id": "019505e0-1000-7000-8000-000000000001",
  "status": "entity_created:198.51.100.42"
}
```

Entity validation is strict. Names cannot be empty or exceed 500 characters. Confidence must be between 0.0 and 1.0:

```rust
pub fn validate_entity_name(name: &str) -> Result<(), String> {
    let trimmed = name.trim();
    if trimmed.is_empty() {
        return Err("Entity name must not be empty".to_string());
    }
    if trimmed.len() > MAX_ENTITY_NAME_LEN {
        return Err(format!(
            "Entity name exceeds maximum length of {} characters (got {})",
            MAX_ENTITY_NAME_LEN, trimmed.len()
        ));
    }
    Ok(())
}

pub fn validate_confidence(confidence: f64) -> Result<(), String> {
    if confidence < 0.0 || confidence > 1.0 {
        return Err(format!(
            "Confidence must be between 0.0 and 1.0 (got {})", confidence
        ));
    }
    Ok(())
}
```

### Creating Relationships

Once you have entities, connect them:

```bash
# 198.51.100.42 communicates_with evil-c2.example.com
curl -X POST https://playseat.internal/api/v1/ontology/relationships \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "relationship_type_id": "019505e0-0000-7100-8000-000000000001",
    "source_entity_id": "019505e0-1000-7000-8000-000000000001",
    "target_entity_id": "019505e0-1000-7000-8000-000000000002",
    "weight": 8.5,
    "confidence": 0.92,
    "properties": {
      "protocol": "https",
      "port": 443,
      "frequency": "every_4_hours",
      "first_observed": "2026-01-15T03:22:00Z",
      "last_observed": "2026-02-17T22:45:00Z",
      "bytes_transferred": 4521890
    },
    "evidence_ids": [
      "019505e0-2000-7000-8000-000000000001",
      "019505e0-2000-7000-8000-000000000002"
    ]
  }'
```

Response:

```json
{
  "id": "019505e0-3000-7000-8000-000000000001",
  "status": "relationship_created:019505e0-1000-7000-8000-000000000001->019505e0-1000-7000-8000-000000000002"
}
```

Every relationship links back to evidence IDs. This is not optional decoration -- this is what makes the graph defensible in an intelligence review. When someone asks "why do you think this IP communicates with this domain?", you point to evidence record `019505e0-2000-7000-8000-000000000001` which contains the packet capture that proves it.

---

## Graph Traversal: Following the Thread

### The WITH RECURSIVE Engine

Playseat's graph traversal is powered by PostgreSQL's `WITH RECURSIVE` CTEs. This is not a toy implementation -- it handles graphs with tens of thousands of nodes and hundreds of thousands of edges.

The traverse endpoint supports three directions:

```bash
# Outbound traversal: "What does this entity connect TO?"
curl -X POST https://playseat.internal/api/v1/ontology/traverse \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "entity_id": "019505e0-1000-7000-8000-000000000001",
    "depth": 3,
    "direction": "outbound"
  }'
```

The outbound traversal SQL:

```sql
WITH RECURSIVE graph_walk AS (
    -- Base case: direct outbound neighbors
    SELECT target_entity_id AS entity_id, 1 AS depth
    FROM ontology_relationships
    WHERE source_entity_id = $1

    UNION

    -- Recursive case: follow outbound edges deeper
    SELECT r.target_entity_id, gw.depth + 1
    FROM graph_walk gw
    JOIN ontology_relationships r ON r.source_entity_id = gw.entity_id
    WHERE gw.depth < $2
)
SELECT DISTINCT e.id, e.entity_type_id, e.name, e.properties,
       e.confidence, e.source, e.first_seen, e.last_seen,
       e.created_at, e.updated_at
FROM graph_walk gw
JOIN ontology_entities e ON e.id = gw.entity_id;
```

Response for a depth-3 outbound traversal from a suspicious IP:

```json
{
  "entities": [
    {
      "id": "019505e0-1000-7000-8000-000000000002",
      "entity_type_id": "019505e0-0000-7000-8000-000000000002",
      "name": "evil-c2.example.com",
      "properties": {"registrar": "NameCheap", "registered": "2025-11-03"},
      "confidence": 0.88,
      "source": "passive-dns"
    },
    {
      "id": "019505e0-1000-7000-8000-000000000003",
      "entity_type_id": "019505e0-0000-7000-8000-000000000011",
      "name": "SYNTHETIC-BEAR Loader v2.1",
      "properties": {"sha256": "a1b2c3d4...", "file_type": "PE32+"},
      "confidence": 0.91,
      "source": "sandbox-analysis"
    },
    {
      "id": "019505e0-1000-7000-8000-000000000004",
      "entity_type_id": "019505e0-0000-7000-8000-000000000008",
      "name": "CVE-2025-12345",
      "properties": {"cvss": 9.1, "vector": "NETWORK"},
      "confidence": 0.95,
      "source": "nvd-enrichment"
    },
    {
      "id": "019505e0-1000-7000-8000-000000000005",
      "entity_type_id": "019505e0-0000-7000-8000-000000000007",
      "name": "web-server-prod-07",
      "properties": {"os": "Ubuntu 22.04", "role": "web-frontend"},
      "confidence": 0.99,
      "source": "asset-inventory"
    },
    {
      "id": "019505e0-1000-7000-8000-000000000006",
      "entity_type_id": "019505e0-0000-7000-8000-000000000010",
      "name": "APT-SYNTHETIC-BEAR",
      "properties": {"origin": "Eastern Europe", "motivation": "espionage"},
      "confidence": 0.72,
      "source": "threat-intel-feed"
    }
  ],
  "total": 5,
  "depth": 3,
  "direction": "outbound",
  "root_entity_id": "019505e0-1000-7000-8000-000000000001"
}
```

One IP address. Three hops. Five connected entities spanning domains, malware, CVEs, assets, and threat actors. This is the power of a connected graph.

### Bidirectional Traversal

The `both` direction follows edges in either direction, treating the graph as undirected:

```bash
# Bidirectional: "What is connected to this entity in ANY direction?"
curl -X POST https://playseat.internal/api/v1/ontology/traverse \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "entity_id": "019505e0-1000-7000-8000-000000000003",
    "depth": 2,
    "direction": "both"
  }'
```

The bidirectional CTE is more complex because it follows edges in both directions:

```sql
WITH RECURSIVE graph_walk AS (
    SELECT CASE WHEN source_entity_id = $1 THEN target_entity_id
                ELSE source_entity_id END AS entity_id, 1 AS depth
    FROM ontology_relationships
    WHERE source_entity_id = $1 OR target_entity_id = $1

    UNION

    SELECT CASE WHEN r.source_entity_id = gw.entity_id THEN r.target_entity_id
                ELSE r.source_entity_id END, gw.depth + 1
    FROM graph_walk gw
    JOIN ontology_relationships r
      ON r.source_entity_id = gw.entity_id OR r.target_entity_id = gw.entity_id
    WHERE gw.depth < $2
)
SELECT DISTINCT e.id, e.entity_type_id, e.name, e.properties,
       e.confidence, e.source, e.first_seen, e.last_seen,
       e.created_at, e.updated_at
FROM graph_walk gw
JOIN ontology_entities e ON e.id = gw.entity_id
WHERE e.id != $1;
```

### Inbound Traversal

Sometimes you want to ask the inverse question: "What points TO this entity?"

```bash
# Inbound: "What entities have relationships pointing TO this domain?"
curl -X POST https://playseat.internal/api/v1/ontology/traverse \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "entity_id": "019505e0-1000-7000-8000-000000000002",
    "depth": 2,
    "direction": "inbound"
  }'
```

Inbound traversals answer questions like: "How many internal IPs are communicating with this C2 domain?" or "Which assets are affected by this CVE?"

### Depth Limits

Depth is validated strictly. Minimum 1, maximum 10:

```rust
pub const MIN_DEPTH: u32 = 1;
pub const MAX_DEPTH: u32 = 10;

pub fn validate_depth(depth: u32) -> Result<(), String> {
    if depth < MIN_DEPTH || depth > MAX_DEPTH {
        return Err(format!(
            "Traversal depth must be between {} and {} (got {})",
            MIN_DEPTH, MAX_DEPTH, depth
        ));
    }
    Ok(())
}
```

The max depth of 10 is a deliberate design decision. In a graph with 50,000 entities, a depth-10 traversal could theoretically touch every node. In practice, most useful intelligence questions are answered within 3-4 hops. If you need depth 10, you are either doing community detection (use the dedicated query for that) or you have lost the thread.

---

## Shortest Path: Connecting Two Points

### Finding the Path

The shortest path algorithm uses a recursive CTE with cycle detection:

```bash
# Find the shortest path between an IP and a threat actor
curl -X POST https://playseat.internal/api/v1/ontology/path \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "source_id": "019505e0-1000-7000-8000-000000000001",
    "target_id": "019505e0-1000-7000-8000-000000000006",
    "max_depth": 6
  }'
```

The SQL:

```sql
WITH RECURSIVE path_search AS (
    -- Base case: all direct outbound edges from source
    SELECT source_entity_id, target_entity_id,
           ARRAY[source_entity_id, target_entity_id] AS path, 1 AS depth
    FROM ontology_relationships
    WHERE source_entity_id = $1

    UNION ALL

    -- Recursive case: extend path by one edge
    SELECT ps.source_entity_id, r.target_entity_id,
           ps.path || r.target_entity_id, ps.depth + 1
    FROM path_search ps
    JOIN ontology_relationships r ON r.source_entity_id = ps.target_entity_id
    WHERE NOT r.target_entity_id = ANY(ps.path)  -- cycle detection
      AND ps.depth < $3
)
SELECT path FROM path_search
WHERE target_entity_id = $2
ORDER BY depth
LIMIT 1;
```

Response:

```json
{
  "path": [
    "019505e0-1000-7000-8000-000000000001",
    "019505e0-1000-7000-8000-000000000002",
    "019505e0-1000-7000-8000-000000000003",
    "019505e0-1000-7000-8000-000000000006"
  ],
  "hops": 3,
  "found": true
}
```

Translation: IP `198.51.100.42` -> communicates_with -> domain `evil-c2.example.com` -> hosts -> malware `SYNTHETIC-BEAR Loader v2.1` -> attributed_to -> threat actor `APT-SYNTHETIC-BEAR`. Three hops from an IP address to a named threat actor.

### The In-Memory BFS Alternative

For smaller graphs or when you need to run many path queries quickly, there is an in-memory BFS implementation:

```rust
pub fn bfs_shortest_path(
    adj: &AdjacencyList,
    start: Uuid,
    goal: Uuid,
    max_depth: u32,
) -> PathResult {
    if start == goal {
        return PathResult::from_path(vec![start]);
    }

    let mut visited: HashSet<Uuid> = HashSet::new();
    let mut queue: VecDeque<(Uuid, Vec<Uuid>)> = VecDeque::new();

    visited.insert(start);
    queue.push_back((start, vec![start]));

    while let Some((current, path)) = queue.pop_front() {
        if path.len() > max_depth as usize {
            continue;
        }
        if let Some(neighbors) = adj.get(&current) {
            for (neighbor, _weight) in neighbors {
                if *neighbor == goal {
                    let mut full_path = path.clone();
                    full_path.push(*neighbor);
                    return PathResult::from_path(full_path);
                }
                if !visited.contains(neighbor) {
                    visited.insert(*neighbor);
                    let mut new_path = path.clone();
                    new_path.push(*neighbor);
                    queue.push_back((*neighbor, new_path));
                }
            }
        }
    }

    PathResult::not_found()
}
```

The adjacency list is built from a single SQL query and cached. This lets you run hundreds of path queries per second without hitting the database for each one.

### Enriching Paths with Entity Details

A path of UUIDs is not very useful to an analyst. Here is the SQL to enrich a path with entity names and types:

```sql
-- Given a path array, enrich it with entity details
WITH path_nodes AS (
    SELECT ordinality, entity_id
    FROM unnest(ARRAY[
        '019505e0-1000-7000-8000-000000000001'::UUID,
        '019505e0-1000-7000-8000-000000000002'::UUID,
        '019505e0-1000-7000-8000-000000000003'::UUID,
        '019505e0-1000-7000-8000-000000000006'::UUID
    ]) WITH ORDINALITY AS t(entity_id, ordinality)
),
enriched AS (
    SELECT
        pn.ordinality AS step,
        e.name AS entity_name,
        et.display_name AS entity_type,
        e.confidence,
        e.source,
        e.properties
    FROM path_nodes pn
    JOIN ontology_entities e ON e.id = pn.entity_id
    JOIN ontology_entity_types et ON et.id = e.entity_type_id
),
edges AS (
    SELECT
        pn1.ordinality AS from_step,
        pn2.ordinality AS to_step,
        rt.display_name AS relationship,
        r.weight,
        r.confidence AS edge_confidence
    FROM path_nodes pn1
    JOIN path_nodes pn2 ON pn2.ordinality = pn1.ordinality + 1
    JOIN ontology_relationships r
      ON r.source_entity_id = pn1.entity_id
     AND r.target_entity_id = pn2.entity_id
    JOIN ontology_relationship_types rt ON rt.id = r.relationship_type_id
)
SELECT
    en.step,
    en.entity_name,
    en.entity_type,
    en.confidence AS node_confidence,
    ed.relationship AS edge_to_next,
    ed.weight AS edge_weight,
    ed.edge_confidence
FROM enriched en
LEFT JOIN edges ed ON ed.from_step = en.step
ORDER BY en.step;
```

Result:

| step | entity_name | entity_type | node_confidence | edge_to_next | edge_weight | edge_confidence |
|------|-------------|-------------|-----------------|--------------|-------------|-----------------|
| 1 | 198.51.100.42 | IP Address | 0.95 | Communicates With | 8.5 | 0.92 |
| 2 | evil-c2.example.com | Domain | 0.88 | Hosts | 7.0 | 0.85 |
| 3 | SYNTHETIC-BEAR Loader v2.1 | Malware | 0.91 | Attributed To | 6.5 | 0.72 |
| 4 | APT-SYNTHETIC-BEAR | Threat Actor | 0.72 | | | |

That table is the executive briefing. Four rows that tell the story of an entire attack chain.

---

## Entity Resolution: Merging Duplicates

### The Duplicate Problem

In any intelligence platform that ingests from multiple sources, duplicates are inevitable. VirusTotal calls it `198.51.100.42`. Your SIEM calls it `198.51.100.042`. Your threat intel feed calls it `198.51.100.42/32`. They are all the same entity, but they are three different rows in your database with three different sets of relationships.

Entity resolution is the process of identifying and merging these duplicates. Playseat implements three strategies:

```rust
pub enum ResolutionStrategy {
    NameMatch,         // Exact or near-exact name match
    PropertyOverlap,   // Entities share significant property overlap
    ManualMerge,       // Analyst manually identifies duplicates
}
```

### Levenshtein Distance

At the core of automatic entity resolution is the Levenshtein distance algorithm. This pure Rust implementation uses dynamic programming with O(min(m,n)) space:

```rust
pub fn levenshtein_distance(a: &str, b: &str) -> usize {
    let a_chars: Vec<char> = a.chars().collect();
    let b_chars: Vec<char> = b.chars().collect();
    let a_len = a_chars.len();
    let b_len = b_chars.len();

    if a_len == 0 { return b_len; }
    if b_len == 0 { return a_len; }

    let (shorter, longer, s_len, l_len) = if a_len <= b_len {
        (&a_chars, &b_chars, a_len, b_len)
    } else {
        (&b_chars, &a_chars, b_len, a_len)
    };

    let mut prev_row: Vec<usize> = (0..=s_len).collect();
    let mut curr_row: Vec<usize> = vec![0; s_len + 1];

    for i in 1..=l_len {
        curr_row[0] = i;
        for j in 1..=s_len {
            let cost = if longer[i - 1] == shorter[j - 1] { 0 } else { 1 };
            curr_row[j] = (prev_row[j] + 1)
                .min(curr_row[j - 1] + 1)
                .min(prev_row[j - 1] + cost);
        }
        std::mem::swap(&mut prev_row, &mut curr_row);
    }

    prev_row[s_len]
}
```

The similarity score normalizes the distance to [0.0, 1.0]:

```rust
pub fn similarity_score(a: &str, b: &str) -> f64 {
    let max_len = a.chars().count().max(b.chars().count());
    if max_len == 0 { return 1.0; }
    let dist = levenshtein_distance(a, b) as f64;
    1.0 - (dist / max_len as f64)
}
```

Some examples:
- `similarity_score("198.51.100.42", "198.51.100.42")` = 1.0 (identical)
- `similarity_score("198.51.100.42", "198.51.100.042")` = 0.93 (leading zero)
- `similarity_score("evil-c2.example.com", "evil-c2.example.net")` = 0.89 (TLD difference)
- `similarity_score("kitten", "sitting")` = 0.57 (classic example)

### Resolving Entities via API

```bash
# Resolve two entities that are duplicates
curl -X POST https://playseat.internal/api/v1/ontology/resolve \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "source_entity_id": "019505e0-1000-7000-8000-000000000010",
    "target_entity_id": "019505e0-1000-7000-8000-000000000011",
    "strategy": "fuzzy"
  }'
```

Response:

```json
{
  "id": "019505e0-4000-7000-8000-000000000001",
  "status": "entities_resolved:019505e0-1000-7000-8000-000000000010->019505e0-1000-7000-8000-000000000011:fuzzy"
}
```

### Finding Duplicates: The SQL Query

This is the query I run every morning to find potential duplicate entities. It uses the pg_trgm extension for trigram similarity (faster than computing Levenshtein for every pair):

```sql
-- Find potential duplicate entities within the same type
WITH entity_pairs AS (
    SELECT
        e1.id AS entity_a_id,
        e1.name AS entity_a_name,
        e2.id AS entity_b_id,
        e2.name AS entity_b_name,
        et.display_name AS entity_type,
        similarity(e1.name, e2.name) AS name_similarity,
        -- Compare property overlap
        (SELECT COUNT(*)
         FROM jsonb_object_keys(COALESCE(e1.properties, '{}')) k1
         WHERE e2.properties ? k1.key
        ) AS shared_property_keys
    FROM ontology_entities e1
    JOIN ontology_entities e2
      ON e1.entity_type_id = e2.entity_type_id
     AND e1.id < e2.id  -- avoid self-pairs and duplicates
    JOIN ontology_entity_types et ON et.id = e1.entity_type_id
    WHERE similarity(e1.name, e2.name) > 0.7
)
SELECT
    entity_type,
    entity_a_name,
    entity_b_name,
    ROUND(name_similarity::NUMERIC, 3) AS similarity,
    shared_property_keys,
    CASE
        WHEN name_similarity > 0.95 THEN 'HIGH: near-exact match -- auto-resolve recommended'
        WHEN name_similarity > 0.85 THEN 'MEDIUM: likely duplicate -- analyst review'
        WHEN name_similarity > 0.70 THEN 'LOW: possible duplicate -- investigate'
    END AS recommendation
FROM entity_pairs
WHERE name_similarity > 0.7
ORDER BY name_similarity DESC
LIMIT 50;
```

Result:

| entity_type | entity_a_name | entity_b_name | similarity | shared_keys | recommendation |
|-------------|---------------|---------------|------------|-------------|----------------|
| IP Address | 198.51.100.42 | 198.51.100.042 | 0.929 | 4 | HIGH: near-exact match |
| Domain | evil-c2.example.com | evil-c2.example.net | 0.895 | 3 | MEDIUM: likely duplicate |
| Malware | SYNTHETIC-BEAR Loader | SYNTHETIC-BEAR Loader v2 | 0.870 | 5 | MEDIUM: likely duplicate |
| Threat Actor | APT-SYNTHETIC-BEAR | APT SYNTHETIC BEAR | 0.857 | 2 | MEDIUM: likely duplicate |

### Listing Resolution History

```bash
# View all resolution records
curl -X GET https://playseat.internal/api/v1/ontology/resolutions \
  -H "Authorization: Bearer ${TOKEN}"
```

Response:

```json
{
  "resolutions": [
    {
      "id": "019505e0-4000-7000-8000-000000000001",
      "source_entity_id": "019505e0-1000-7000-8000-000000000010",
      "target_entity_id": "019505e0-1000-7000-8000-000000000011",
      "strategy": "fuzzy",
      "similarity_score": 0.8,
      "resolved_by": "019505e0-5000-7000-8000-000000000001",
      "resolved_at": "2026-02-17T14:30:00Z",
      "created_at": "2026-02-17T14:30:00Z"
    }
  ],
  "total": 1
}
```

---

## Timeline Analysis: The Temporal Dimension

### Why Timelines Matter

A knowledge graph tells you what is connected. A timeline tells you when things happened. Together they answer the most important question in intelligence: "What is the story?"

From `crates/svc-ontology/src/timeline.rs`, the six event types:

```rust
pub enum TimelineEventType {
    Created,    // Entity was created (weight: 50)
    Modified,   // Entity properties were modified (weight: 30)
    Observed,   // Entity was observed in the wild (weight: 40)
    Linked,     // Entity was linked to another entity (weight: 60)
    Resolved,   // Entity was resolved/merged with another (weight: 70)
    Tagged,     // Entity was tagged (weight: 10)
}
```

Each event type has a priority weight for sorting. Resolved events (weight 70) are more significant than Tagged events (weight 10). This weighting drives the default sort order when analysts are reviewing entity timelines.

### Querying Entity Timelines

```bash
# Get the timeline for a suspicious domain
curl -X GET https://playseat.internal/api/v1/ontology/entities/${ENTITY_ID}/timeline \
  -H "Authorization: Bearer ${TOKEN}"
```

Response:

```json
{
  "timeline": [
    {
      "id": "019505e0-6000-7000-8000-000000000001",
      "entity_id": "019505e0-1000-7000-8000-000000000002",
      "event_type": "created",
      "title": "Domain entity created from passive DNS",
      "description": "evil-c2.example.com first observed in passive DNS feed",
      "metadata": {"feed": "passive-dns-alpha", "confidence": 0.88},
      "occurred_at": "2026-01-15T03:22:00Z"
    },
    {
      "id": "019505e0-6000-7000-8000-000000000002",
      "entity_id": "019505e0-1000-7000-8000-000000000002",
      "event_type": "linked",
      "title": "Linked to IP 198.51.100.42 (communicates_with)",
      "description": "DNS resolution observed: evil-c2.example.com -> 198.51.100.42",
      "metadata": {"relationship_type": "communicates_with", "weight": 8.5},
      "occurred_at": "2026-01-15T03:25:00Z"
    },
    {
      "id": "019505e0-6000-7000-8000-000000000003",
      "entity_id": "019505e0-1000-7000-8000-000000000002",
      "event_type": "linked",
      "title": "Linked to malware SYNTHETIC-BEAR Loader v2.1 (hosts)",
      "description": "Sandbox analysis confirmed domain hosts malware binary",
      "metadata": {"relationship_type": "hosts", "sha256": "a1b2c3d4..."},
      "occurred_at": "2026-01-18T11:45:00Z"
    },
    {
      "id": "019505e0-6000-7000-8000-000000000004",
      "entity_id": "019505e0-1000-7000-8000-000000000002",
      "event_type": "tagged",
      "title": "Tagged as 'apt-c2-infrastructure'",
      "description": null,
      "metadata": {"tag": "apt-c2-infrastructure", "tagged_by": "auto-classifier"},
      "occurred_at": "2026-01-18T11:50:00Z"
    },
    {
      "id": "019505e0-6000-7000-8000-000000000005",
      "entity_id": "019505e0-1000-7000-8000-000000000002",
      "event_type": "observed",
      "title": "Domain still active in DNS (302 days since registration)",
      "description": "Daily DNS check confirms domain is still resolving",
      "metadata": {"resolved_ip": "198.51.100.42", "ttl": 300},
      "occurred_at": "2026-02-17T06:00:00Z"
    }
  ],
  "total": 5
}
```

### Timeline Correlation SQL

This query finds entities that had significant activity during a specific time window -- useful for incident correlation:

```sql
-- Find all entities with activity during a specific incident window
WITH incident_window AS (
    SELECT
        '2026-01-15T00:00:00Z'::TIMESTAMPTZ AS window_start,
        '2026-01-20T23:59:59Z'::TIMESTAMPTZ AS window_end
),
active_entities AS (
    SELECT
        t.entity_id,
        e.name AS entity_name,
        et.display_name AS entity_type,
        COUNT(*) AS event_count,
        ARRAY_AGG(DISTINCT t.event_type ORDER BY t.event_type) AS event_types,
        MIN(t.occurred_at) AS first_activity,
        MAX(t.occurred_at) AS last_activity,
        SUM(CASE t.event_type
            WHEN 'created' THEN 50
            WHEN 'modified' THEN 30
            WHEN 'observed' THEN 40
            WHEN 'linked' THEN 60
            WHEN 'resolved' THEN 70
            WHEN 'tagged' THEN 10
            ELSE 0
        END) AS activity_score
    FROM ontology_timeline t
    JOIN ontology_entities e ON e.id = t.entity_id
    JOIN ontology_entity_types et ON et.id = e.entity_type_id
    CROSS JOIN incident_window iw
    WHERE t.occurred_at BETWEEN iw.window_start AND iw.window_end
    GROUP BY t.entity_id, e.name, et.display_name
)
SELECT *
FROM active_entities
ORDER BY activity_score DESC, event_count DESC
LIMIT 25;
```

---

## Real Scenario: From One IOC to a Nine-Month Campaign

### The Starting Point

February 12, 2026. 2:47 AM. An alert fires on our SIEM. Nothing dramatic -- a medium-confidence alert about DNS traffic to an unusual domain from an internal web server. The kind of alert that gets ignored in most SOCs.

I did not ignore it.

The domain was `cdn-assets-static.example.com`. It had been registered 302 days earlier. It resolved to `198.51.100.42`. Our passive DNS enrichment had tagged the IP as a "known proxy" but had not flagged it as malicious.

I started with the ontology search:

```bash
# Search for the suspicious domain
curl -X POST https://playseat.internal/api/v1/ontology/entities/search \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "cdn-assets-static.example.com"
  }'
```

It was already in the graph. Created 47 days ago by our passive DNS feed. Two relationships: resolves_to the IP, and communicates_with our web server. Low weight, moderate confidence. Nobody had looked at it.

### Pulling the Thread

I ran a depth-3 bidirectional traversal from the domain:

```bash
curl -X POST https://playseat.internal/api/v1/ontology/traverse \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "entity_id": "019505e0-1000-7000-8000-000000000042",
    "depth": 3,
    "direction": "both"
  }'
```

The traversal returned 23 entities. I expected 3 or 4. Twenty-three.

The graph revealed a network:
- The domain resolved to **3 different IP addresses** over its 302-day lifetime
- Those IPs hosted **4 other domains** with similar naming patterns (`cdn-static-assets.example.net`, `assets-cdn-global.example.org`, etc.)
- One of those domains was linked to **malware** identified by our sandbox 3 months ago -- an alert that had been closed as a false positive
- The malware was attributed to a threat actor profile that had been created from a CISA advisory
- **7 internal assets** had communication relationships with various nodes in this network
- The communication patterns showed **regular 4-hour beaconing intervals**

### The Path That Mattered

```bash
# Find the path from our web server to the threat actor
curl -X POST https://playseat.internal/api/v1/ontology/path \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "source_id": "019505e0-1000-7000-8000-000000000099",
    "target_id": "019505e0-1000-7000-8000-000000000200",
    "max_depth": 6
  }'
```

Five hops: `web-server-prod-07` -> communicates_with -> `cdn-assets-static.example.com` -> resolves_to -> `198.51.100.42` -> hosts -> `loader-variant-alpha.exe` -> attributed_to -> `APT-SYNTHETIC-BEAR`.

From a single DNS alert to a named APT group in five hops.

### The Community Detection Query

I needed to understand the full scope. This SQL identifies clusters of connected entities -- what graph theorists call "communities":

```sql
-- Community detection: find clusters of interconnected entities
WITH RECURSIVE entity_cluster AS (
    -- Start from the suspicious domain
    SELECT
        '019505e0-1000-7000-8000-000000000042'::UUID AS entity_id,
        1 AS cluster_id,
        0 AS depth
    UNION
    SELECT
        CASE
            WHEN r.source_entity_id = ec.entity_id THEN r.target_entity_id
            ELSE r.source_entity_id
        END,
        ec.cluster_id,
        ec.depth + 1
    FROM entity_cluster ec
    JOIN ontology_relationships r
      ON r.source_entity_id = ec.entity_id
      OR r.target_entity_id = ec.entity_id
    WHERE ec.depth < 4
      AND r.confidence >= 0.5  -- only follow high-confidence edges
),
cluster_summary AS (
    SELECT DISTINCT
        ec.entity_id,
        e.name,
        et.display_name AS entity_type,
        e.confidence,
        e.first_seen,
        ec.depth AS distance_from_seed,
        (SELECT COUNT(*) FROM ontology_relationships r2
         WHERE r2.source_entity_id = ec.entity_id
            OR r2.target_entity_id = ec.entity_id
        ) AS connection_count
    FROM entity_cluster ec
    JOIN ontology_entities e ON e.id = ec.entity_id
    JOIN ontology_entity_types et ON et.id = e.entity_type_id
)
SELECT
    entity_type,
    COUNT(*) AS entity_count,
    ARRAY_AGG(name ORDER BY distance_from_seed, confidence DESC) AS entities,
    ROUND(AVG(confidence)::NUMERIC, 2) AS avg_confidence,
    MIN(first_seen) AS earliest_activity,
    SUM(connection_count) AS total_connections
FROM cluster_summary
GROUP BY entity_type
ORDER BY entity_count DESC;
```

Result:

| entity_type | count | entities | avg_confidence | earliest_activity | total_connections |
|-------------|-------|----------|----------------|-------------------|-------------------|
| IP Address | 5 | [198.51.100.42, 198.51.100.43, 203.0.113.10, ...] | 0.87 | 2025-05-12 | 34 |
| Domain | 6 | [cdn-assets-static.example.com, cdn-static-assets.example.net, ...] | 0.82 | 2025-05-10 | 28 |
| Asset | 7 | [web-server-prod-07, app-server-03, ...] | 0.95 | 2025-06-15 | 21 |
| Malware | 3 | [loader-variant-alpha.exe, loader-variant-beta.dll, ...] | 0.89 | 2025-07-22 | 15 |
| Threat Actor | 1 | [APT-SYNTHETIC-BEAR] | 0.72 | 2025-04-30 | 8 |
| CVE | 2 | [CVE-2025-12345, CVE-2025-12346] | 0.94 | 2025-05-01 | 6 |

Twenty-four entities. The earliest activity was May 2025 -- nine months before our alert. The threat actor had been in the network since June, communicating through a rotating set of domains and IPs that had been individually flagged and individually dismissed.

No single alert told this story. Only the graph did.

### The Timeline Reconstruction

```sql
-- Reconstruct the campaign timeline across all connected entities
SELECT
    t.occurred_at,
    t.event_type,
    e.name AS entity,
    et.display_name AS type,
    t.title,
    t.description
FROM ontology_timeline t
JOIN ontology_entities e ON e.id = t.entity_id
JOIN ontology_entity_types et ON et.id = e.entity_type_id
WHERE t.entity_id IN (
    -- All entities in the cluster
    SELECT DISTINCT entity_id FROM entity_cluster
)
ORDER BY t.occurred_at ASC
LIMIT 100;
```

The timeline showed:
- **May 2025**: First domain registered, first IP resolved
- **June 2025**: First internal asset contacted the C2 (initial compromise)
- **July 2025**: Malware variants deployed, lateral movement to additional servers
- **August-December 2025**: Steady beaconing at 4-hour intervals, data exfiltration via DNS tunneling
- **January 2026**: New domain added to rotation (dns-analytics-global.example.net)
- **February 2026**: Our SIEM alert fires on the newest domain

The campaign had been operating for nine months. We found it because the ontology connected what 47 individual, low-confidence alerts could not.

---

## Tags: Annotating the Graph

### Adding Tags

Tags are the analyst's shorthand for marking entities with operational context:

```bash
# Tag the domain as C2 infrastructure
curl -X POST https://playseat.internal/api/v1/ontology/tags/019505e0-1000-7000-8000-000000000042 \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{"tag": "confirmed-c2"}'

# Tag all entities in the campaign cluster
for ENTITY_ID in $(echo "$CLUSTER_ENTITY_IDS"); do
  curl -X POST "https://playseat.internal/api/v1/ontology/tags/${ENTITY_ID}" \
    -H "Authorization: Bearer ${TOKEN}" \
    -H "Content-Type: application/json" \
    -d '{"tag": "campaign-synthetic-bear-2025"}'
done
```

### Querying by Tags

```bash
# Get all tags for an entity
curl -X GET https://playseat.internal/api/v1/ontology/tags/019505e0-1000-7000-8000-000000000042 \
  -H "Authorization: Bearer ${TOKEN}"
```

Response:

```json
{
  "tags": [
    {
      "id": "019505e0-7000-7000-8000-000000000001",
      "entity_id": "019505e0-1000-7000-8000-000000000042",
      "tag": "confirmed-c2",
      "created_by": "019505e0-5000-7000-8000-000000000001",
      "created_at": "2026-02-12T03:30:00Z"
    },
    {
      "id": "019505e0-7000-7000-8000-000000000002",
      "entity_id": "019505e0-1000-7000-8000-000000000042",
      "tag": "campaign-synthetic-bear-2025",
      "created_by": "019505e0-5000-7000-8000-000000000001",
      "created_at": "2026-02-12T04:15:00Z"
    }
  ],
  "total": 2
}
```

Tags have a unique constraint on `(entity_id, tag)` -- you cannot tag the same entity with the same tag twice. The `ON CONFLICT DO NOTHING` clause means the API is idempotent.

### Tag-Based Graph Queries

Find all entities with a specific tag and their immediate neighbors:

```sql
-- Find all confirmed C2 infrastructure and what internal assets talk to it
WITH tagged_c2 AS (
    SELECT e.id, e.name, et.display_name AS entity_type
    FROM ontology_tags t
    JOIN ontology_entities e ON e.id = t.entity_id
    JOIN ontology_entity_types et ON et.id = e.entity_type_id
    WHERE t.tag = 'confirmed-c2'
),
internal_connections AS (
    SELECT
        tc.name AS c2_entity,
        tc.entity_type AS c2_type,
        asset.name AS internal_asset,
        asset_type.display_name AS asset_type,
        rt.display_name AS relationship,
        r.weight,
        r.confidence,
        r.first_seen,
        r.last_seen
    FROM tagged_c2 tc
    JOIN ontology_relationships r
      ON r.source_entity_id = tc.id OR r.target_entity_id = tc.id
    JOIN ontology_entities asset
      ON asset.id = CASE
          WHEN r.source_entity_id = tc.id THEN r.target_entity_id
          ELSE r.source_entity_id
      END
    JOIN ontology_entity_types asset_type ON asset_type.id = asset.entity_type_id
    JOIN ontology_relationship_types rt ON rt.id = r.relationship_type_id
    WHERE asset_type.name = 'asset'  -- only internal assets
)
SELECT * FROM internal_connections
ORDER BY last_seen DESC, confidence DESC;
```

---

## Ontology Statistics

### The Stats Endpoint

```bash
curl -X GET https://playseat.internal/api/v1/ontology/stats \
  -H "Authorization: Bearer ${TOKEN}"
```

Response:

```json
{
  "total_entities": 47231,
  "total_relationships": 128947,
  "total_entity_types": 12,
  "type_distribution": [
    {"type_name": "ip_address", "count": 18420},
    {"type_name": "domain", "count": 12305},
    {"type_name": "ioc", "count": 8742},
    {"type_name": "asset", "count": 3215},
    {"type_name": "url", "count": 1847},
    {"type_name": "email", "count": 1024},
    {"type_name": "cve", "count": 687},
    {"type_name": "malware", "count": 512},
    {"type_name": "hostname", "count": 289},
    {"type_name": "user_account", "count": 98},
    {"type_name": "threat_actor", "count": 57},
    {"type_name": "campaign", "count": 35}
  ]
}
```

47,000 entities. 129,000 relationships. 12 types. That is a real intelligence graph, not a demo.

### Graph Health Metrics

This query identifies orphaned entities (nodes with no relationships) and over-connected entities (potential data quality issues):

```sql
-- Graph health metrics
WITH entity_connections AS (
    SELECT
        e.id,
        e.name,
        et.display_name AS entity_type,
        COUNT(DISTINCT r.id) AS connection_count
    FROM ontology_entities e
    JOIN ontology_entity_types et ON et.id = e.entity_type_id
    LEFT JOIN ontology_relationships r
      ON r.source_entity_id = e.id OR r.target_entity_id = e.id
    GROUP BY e.id, e.name, et.display_name
),
health_summary AS (
    SELECT
        entity_type,
        COUNT(*) AS total_entities,
        COUNT(*) FILTER (WHERE connection_count = 0) AS orphaned,
        COUNT(*) FILTER (WHERE connection_count > 100) AS over_connected,
        ROUND(AVG(connection_count)::NUMERIC, 1) AS avg_connections,
        MAX(connection_count) AS max_connections,
        ROUND(100.0 * COUNT(*) FILTER (WHERE connection_count = 0) / GREATEST(COUNT(*), 1), 1) AS orphan_pct
    FROM entity_connections
    GROUP BY entity_type
)
SELECT *
FROM health_summary
ORDER BY orphan_pct DESC;
```

Result:

| entity_type | total | orphaned | over_connected | avg_connections | max_connections | orphan_pct |
|-------------|-------|----------|----------------|-----------------|-----------------|------------|
| IOC | 8742 | 2104 | 3 | 2.8 | 247 | 24.1 |
| URL | 1847 | 312 | 0 | 1.9 | 45 | 16.9 |
| IP Address | 18420 | 1847 | 12 | 4.2 | 1203 | 10.0 |
| Domain | 12305 | 847 | 8 | 3.7 | 892 | 6.9 |
| Asset | 3215 | 42 | 5 | 8.4 | 312 | 1.3 |
| Threat Actor | 57 | 0 | 2 | 47.3 | 523 | 0.0 |

IOCs have the highest orphan rate (24.1%) because threat feeds dump indicators without relationships. This is expected -- the ontology enrichment pipeline will connect them over time. Threat actors have zero orphans because every threat actor entry was manually verified by an analyst before creation.

---

## Neighbor Discovery

### Getting Entity Neighbors

The neighbor endpoint returns all entities directly connected to a given entity, regardless of direction:

```bash
# Get neighbors of a malware entity
curl -X GET https://playseat.internal/api/v1/ontology/entities/019505e0-1000-7000-8000-000000000003/neighbors \
  -H "Authorization: Bearer ${TOKEN}"
```

Response:

```json
{
  "neighbors": [
    {
      "id": "019505e0-1000-7000-8000-000000000002",
      "entity_type_id": "019505e0-0000-7000-8000-000000000002",
      "name": "evil-c2.example.com",
      "properties": {"registrar": "NameCheap"},
      "confidence": 0.88,
      "source": "passive-dns"
    },
    {
      "id": "019505e0-1000-7000-8000-000000000004",
      "entity_type_id": "019505e0-0000-7000-8000-000000000008",
      "name": "CVE-2025-12345",
      "properties": {"cvss": 9.1},
      "confidence": 0.95,
      "source": "nvd-enrichment"
    },
    {
      "id": "019505e0-1000-7000-8000-000000000006",
      "entity_type_id": "019505e0-0000-7000-8000-000000000010",
      "name": "APT-SYNTHETIC-BEAR",
      "properties": {"origin": "Eastern Europe"},
      "confidence": 0.72,
      "source": "threat-intel-feed"
    }
  ],
  "total": 3
}
```

The SQL behind this is a straightforward JOIN on the relationships table in both directions:

```sql
SELECT DISTINCT e.id, e.entity_type_id, e.name, e.properties,
       e.confidence, e.source, e.first_seen, e.last_seen,
       e.created_at, e.updated_at
FROM ontology_entities e
JOIN ontology_relationships r
  ON (r.target_entity_id = e.id OR r.source_entity_id = e.id)
WHERE (r.source_entity_id = $1 OR r.target_entity_id = $1)
  AND e.id != $1
LIMIT 50;
```

---

## Operational Lessons Learned

1. **The graph is only as good as the edges.** I have seen organizations spend months ingesting 100,000 IP addresses and domains with zero relationships. That is a list, not a graph. The value is in the connections. Every entity ingestion pipeline must also create relationships, even if the initial confidence is low.

2. **Recursive CTEs scale better than you think.** I was skeptical about building graph traversal on PostgreSQL instead of Neo4j. After benchmarking, depth-4 traversals on our 47,000-node graph complete in 12ms. Depth-6 traversals complete in 85ms. Depth-10 (which I have never needed in practice) completes in 340ms. PostgreSQL's query planner handles recursive CTEs remarkably well when the underlying tables are properly indexed.

3. **Entity resolution is a daily task, not a one-time setup.** New data arrives constantly from multiple feeds. Duplicates accumulate. I run the duplicate detection query every morning and resolve 5-15 entity pairs per day. It takes 10 minutes. If you skip it for a week, you get 70-100 unresolved duplicates, and your graph starts lying to you because the same IP has two nodes with different relationship sets.

4. **Confidence scores decay.** An IOC observed yesterday has high confidence. The same IOC last observed six months ago has questionable confidence. We run a nightly job that decays confidence scores by 2% per week for entities not recently observed. This means old, stale intelligence naturally falls out of graph traversal results because low-confidence edges get filtered.

5. **Start with depth 2, not depth 5.** New analysts always set traversal depth to maximum. They get back a forest of 500 entities and cannot see the trees. Start with depth 2 (direct connections). If the answer is not there, go to depth 3. I have found 90% of actionable intelligence within 3 hops.

6. **Tags are your operational memory.** Six months from now, you will not remember why you marked that IP as suspicious. Tags like `confirmed-c2`, `campaign-synthetic-bear-2025`, `analyst-reviewed-2026-02-12` are the breadcrumbs that let future analysts understand the decisions that were made.

7. **The timeline is the narrative.** When you brief leadership on a threat, they do not want to see a graph. They want to hear a story with a beginning, middle, and end. The timeline feature gives you that story, ordered chronologically, with every event that touched every entity in the campaign. I generate the timeline, paste it into a document, and the executive briefing writes itself.

8. **The first indicator is never the interesting one.** In the nine-month campaign case, the DNS alert on `cdn-assets-static.example.com` was the 47th alert generated by entities in that cluster. The first 46 had been individually triaged and individually dismissed. The graph was the only system that showed they were all connected. This is why you build a knowledge graph -- not for the alerts that are obviously bad, but for the campaigns that are designed to look like 47 individual nothings.

---

*This is the foundation. Every chapter before this one produced data. This chapter showed how to connect it all. The ontology is the connective tissue of the platform -- the system that turns isolated facts into connected intelligence.*

---

(c) 2026 Playseat -- All Rights Reserved | Proprietary and Confidential
