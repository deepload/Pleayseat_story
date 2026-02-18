# Chapter 11: Supply Chain Attack -- PHANTOM MERCY's Method

**Playseat Advanced Field Manual** | **Platform v0.2.0**
**Classification: UNCLASSIFIED** | **218 Crates, 225 Migrations, 1100+ Tables, 212 Routes**

> "She found the infection point. The place where aid becomes abduction, where shipping manifests become targeting lists. And she documented it all before they silenced her."

---

## 11.1 The Message She Left Behind

**2026-02-18T01:47:00Z -- My apartment, 3rd cup of coffee, hands shaking.**

I keep coming back to Clara's message. The one routed through three Tor relays and a dead-drop Signal account that only I knew about. Nine words and a file:

*"The supply chain is the weapon. Trust nothing downstream."*

The file was a CycloneDX SBOM. Not for a software project. For a humanitarian logistics pipeline. She'd mapped every component of the Global Children's Aid Foundation's shipping infrastructure -- their manifest system, their donor tracking platform, their fleet management software, their customs clearance tools -- and she'd found something buried in the dependency graph that nobody was supposed to see.

PHANTOM MERCY wasn't just using the aid network as cover. They'd *compromised the software that runs the aid network*. Every manifest that went through the GCAF system got silently copied to a shadow ledger. Every shipment marked "medical supplies" or "educational materials" got flagged for secondary processing -- a processing pipeline that had nothing to do with aid.

I'm staring at the SBOM she sent, and the supply chain module in Playseat is the only tool I've got that can parse what she found. So I'm going to walk through it, layer by layer, the way Clara did. And maybe by the time I reach the bottom, I'll understand why she went dark.

---

## 11.2 How Supply Chain Attacks Work (And How PHANTOM MERCY Perfected Them)

Before I touch the API, let me explain what we're defending against. Supply chain attacks come in flavors, and PHANTOM MERCY used at least three of them simultaneously. That's what makes them terrifying.

**Compromise the Source (SolarWinds-style)**
The attacker gets access to the build system of a trusted vendor. They inject malicious code into a legitimate update. Every customer who applies the update gets owned. Detection requires monitoring the behavioral characteristics of the software, not just its signature. SolarWinds compromised 18,000 organizations this way. PHANTOM MERCY compromised one -- but the one they compromised moves children.

**Dependency Confusion**
The attacker publishes a malicious package to a public registry with the same name as an internal private package. Package managers, following their resolution rules, pull the public malicious version instead of the private legitimate one. PHANTOM MERCY did this with `@gcaf/manifest-validator` -- the package that verifies shipping manifests against customs databases.

**Maintainer Takeover**
Social-engineer or buy out the maintainer of a popular package. Push an update with a backdoor. The `event-stream` incident from 2018 was this pattern. PHANTOM MERCY went one further: they didn't buy the maintainer. They *hired* her. Put her on salary at a shell company that provides "humanitarian technology consulting." She's still committing code. She doesn't know what the code actually does.

**Build System Poisoning**
Compromise CI/CD pipelines to inject code during the build process without ever modifying the source repository. PHANTOM MERCY infected the Jenkins instance that builds the GCAF platform. The source code is clean. The compiled binary is not. The difference only shows up if you hash both and compare -- which nobody did until Clara.

Clara found all four vectors in a single organization. She told me once, over terrible coffee in a Lyon safe house, that supply chain attacks are like cancer. By the time you see symptoms, it's already metastasized. She was right. And she documented the metastasis with the precision of a surgeon.

---

## 11.3 Setting Up Supply Chain Monitoring

### Registering the Aid Network's Packages

I'm importing Clara's SBOM into Playseat. Everything in the supply chain module starts with packages -- any software component the organization depends on. For a humanitarian logistics network, that means manifest systems, GPS fleet trackers, donor management platforms, customs interfaces.

```bash
# Register the GCAF manifest validator -- the compromised package
curl -s -X POST http://localhost:3000/api/v1/supply-chain/packages \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "@gcaf/manifest-validator",
    "version": "4.2.1",
    "ecosystem": "npm",
    "license": "MIT",
    "description": "Validates humanitarian shipping manifests against customs databases. COMPROMISED -- shadow data exfiltration via dependency injection.",
    "supplier": "gcaf-tech-team",
    "purl": "pkg:npm/%40gcaf/manifest-validator@4.2.1"
  }' | jq .
```

**Response:**

```json
{
  "id": "01951a01-bb02-7000-8000-000000000001",
  "name": "@gcaf/manifest-validator",
  "version": "4.2.1",
  "ecosystem": "npm",
  "license": "MIT",
  "description": "Validates humanitarian shipping manifests against customs databases. COMPROMISED -- shadow data exfiltration via dependency injection.",
  "risk_score": 0.0,
  "supplier": "gcaf-tech-team",
  "purl": "pkg:npm/%40gcaf/manifest-validator@4.2.1",
  "created_by": "01948a5e-0001-7000-8000-000000000001",
  "created_at": "2026-02-18T02:00:00Z",
  "updated_at": "2026-02-18T02:00:00Z"
}
```

`risk_score` starts at 0.0. That's about to change once I trace Clara's breadcrumbs through the dependency graph. The `purl` field follows the Package URL specification -- it's the universal identifier that lets us correlate this package across vulnerability databases, SBOM standards, and threat intelligence feeds.

### Registering the Dependency Chain Clara Mapped

Clara didn't just find the compromised package. She mapped its entire transitive dependency tree. The manifest validator depends on `@gcaf/shipment-tracker`, which depends on `@gcaf/geo-resolver`, which depends on `shadow-relay` -- a package that shouldn't exist.

```bash
# Register the dependency chain
export MANIFEST_ID="01951a01-bb02-7000-8000-000000000001"

# Shipment tracker -- legitimate, but it pulls in the poison
TRACKER=$(curl -s -X POST http://localhost:3000/api/v1/supply-chain/packages \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "@gcaf/shipment-tracker",
    "version": "3.8.0",
    "ecosystem": "npm",
    "license": "MIT",
    "supplier": "gcaf-tech-team",
    "purl": "pkg:npm/%40gcaf/shipment-tracker@3.8.0"
  }' | jq -r '.id')

# Geo-resolver -- translates coordinates to regions
GEO=$(curl -s -X POST http://localhost:3000/api/v1/supply-chain/packages \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "@gcaf/geo-resolver",
    "version": "2.1.4",
    "ecosystem": "npm",
    "license": "MIT",
    "purl": "pkg:npm/%40gcaf/geo-resolver@2.1.4"
  }' | jq -r '.id')

# shadow-relay -- the payload Clara found
SHADOW=$(curl -s -X POST http://localhost:3000/api/v1/supply-chain/packages \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "shadow-relay",
    "version": "1.0.3",
    "ecosystem": "npm",
    "license": "unknown",
    "description": "MALICIOUS: Data exfiltration relay disguised as geographic data normalization library.",
    "supplier": "unknown",
    "purl": "pkg:npm/shadow-relay@1.0.3"
  }' | jq -r '.id')

echo "Manifest Validator: $MANIFEST_ID"
echo "Shipment Tracker: $TRACKER"
echo "Geo Resolver: $GEO"
echo "Shadow Relay: $SHADOW"
```

Now wire up the dependency relationships:

```bash
# manifest-validator -> shipment-tracker
curl -s -X POST "http://localhost:3000/api/v1/supply-chain/packages/$MANIFEST_ID/dependencies" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"depends_on_id\": \"$TRACKER\",
    \"dependency_type\": \"runtime\",
    \"version_req\": \"3.8.0\"
  }" | jq .

# shipment-tracker -> geo-resolver
curl -s -X POST "http://localhost:3000/api/v1/supply-chain/packages/$TRACKER/dependencies" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"depends_on_id\": \"$GEO\",
    \"dependency_type\": \"runtime\",
    \"version_req\": \"2.1.4\"
  }" | jq .

# geo-resolver -> shadow-relay (THIS IS THE INFECTION POINT)
curl -s -X POST "http://localhost:3000/api/v1/supply-chain/packages/$GEO/dependencies" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"depends_on_id\": \"$SHADOW\",
    \"dependency_type\": \"runtime\",
    \"version_req\": \"1.0.3\"
  }" | jq .
```

**Response (each):**

```json
{
  "id": "01951a05-cc03-7000-8000-000000000010",
  "package_id": "01951a01-bb02-7000-8000-000000000001",
  "depends_on_id": "01951a02-bb03-7000-8000-000000000002",
  "dependency_type": "runtime",
  "version_req": "3.8.0",
  "created_at": "2026-02-18T02:05:00Z"
}
```

Three layers deep. That's where Clara found it. `shadow-relay` doesn't show up in the top-level `package.json`. It doesn't show up in the lockfile audit. It's a transitive dependency of a transitive dependency, and its name sounds perfectly innocent -- "geographic data normalization." Nobody questions a geo library in a shipping platform.

Nobody except Clara.

---

## 11.4 Visualizing the Dependency Tree

This is where it gets real. The dependency tree endpoint uses a recursive CTE to walk the entire transitive dependency graph:

```bash
# Get the full dependency tree for the manifest validator
curl -s "http://localhost:3000/api/v1/supply-chain/packages/$MANIFEST_ID/tree" \
  -H "Authorization: Bearer $TOKEN" | jq .
```

```json
{
  "package_id": "01951a01-bb02-7000-8000-000000000001",
  "name": "@gcaf/manifest-validator",
  "version": "4.2.1",
  "dependency_type": "root",
  "children": [
    {
      "package_id": "01951a02-bb03-7000-8000-000000000002",
      "name": "@gcaf/shipment-tracker",
      "version": "3.8.0",
      "dependency_type": "runtime",
      "children": [
        {
          "package_id": "01951a03-bb04-7000-8000-000000000003",
          "name": "@gcaf/geo-resolver",
          "version": "2.1.4",
          "dependency_type": "runtime",
          "children": [
            {
              "package_id": "01951a04-bb05-7000-8000-000000000004",
              "name": "shadow-relay",
              "version": "1.0.3",
              "dependency_type": "runtime",
              "children": []
            }
          ]
        }
      ]
    }
  ]
}
```

There it is. `shadow-relay` at the bottom of the tree. Three levels down from the root. If you're reviewing the top-level dependencies, you see `@gcaf/shipment-tracker` -- looks legit. You have to dig three levels deep before you find the malware.

The backend SQL for this is a recursive CTE with a depth limiter:

```sql
WITH RECURSIVE dep_tree AS (
    -- Base case: direct dependencies of the root package
    SELECT d.package_id, d.depends_on_id,
           p.name AS dep_name, p.version AS dep_version,
           d.dependency_type, 1 AS depth
    FROM sbom_dependencies d
    JOIN sbom_packages p ON p.id = d.depends_on_id
    WHERE d.package_id = $1

    UNION ALL

    -- Recursive case: dependencies of dependencies
    SELECT d2.package_id, d2.depends_on_id,
           p2.name AS dep_name, p2.version AS dep_version,
           d2.dependency_type, dt.depth + 1 AS depth
    FROM sbom_dependencies d2
    JOIN sbom_packages p2 ON p2.id = d2.depends_on_id
    JOIN dep_tree dt ON dt.depends_on_id = d2.package_id
    WHERE dt.depth < 10  -- Circuit breaker: max 10 levels deep
)
SELECT package_id, depends_on_id, dep_name, dep_version,
       dependency_type, depth
FROM dep_tree
ORDER BY depth ASC;
```

That `WHERE dt.depth < 10` is critical. Without it, a circular dependency (A depends on B depends on C depends on A) would run forever. In the real world, npm dependency trees can go 15+ levels deep, but 10 is a sane default. PHANTOM MERCY knew this. They hid at level 3 -- deep enough to avoid casual inspection, shallow enough that the recursive CTE would always find it if anyone bothered to look.

Clara bothered to look.

---

## 11.5 Clara's SBOM: The Evidence She Compiled

Software Bills of Materials are the foundation of supply chain security. They're the ingredient list on the back of the box, except the box is a humanitarian logistics platform and one of the ingredients is a child trafficking relay.

Clara exported the entire GCAF platform as a CycloneDX SBOM before she went dark. This is what she sent me:

```bash
# Import Clara's CycloneDX SBOM
curl -s -X POST http://localhost:3000/api/v1/supply-chain/import-sbom \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "format": "cyclonedx",
    "content": "{\"bomFormat\":\"CycloneDX\",\"specVersion\":\"1.5\",\"version\":1,\"metadata\":{\"timestamp\":\"2026-02-12T03:14:00Z\",\"tools\":[{\"name\":\"clara-field-extract\",\"version\":\"1.0.0\"}],\"component\":{\"type\":\"application\",\"name\":\"gcaf-logistics-platform\",\"version\":\"7.3.1\"}},\"components\":[{\"type\":\"library\",\"name\":\"@gcaf/manifest-validator\",\"version\":\"4.2.1\",\"purl\":\"pkg:npm/%40gcaf/manifest-validator@4.2.1\",\"license\":\"MIT\"},{\"type\":\"library\",\"name\":\"@gcaf/shipment-tracker\",\"version\":\"3.8.0\",\"purl\":\"pkg:npm/%40gcaf/shipment-tracker@3.8.0\",\"license\":\"MIT\"},{\"type\":\"library\",\"name\":\"@gcaf/geo-resolver\",\"version\":\"2.1.4\",\"purl\":\"pkg:npm/%40gcaf/geo-resolver@2.1.4\",\"license\":\"MIT\"},{\"type\":\"library\",\"name\":\"shadow-relay\",\"version\":\"1.0.3\",\"purl\":\"pkg:npm/shadow-relay@1.0.3\",\"license\":\"unknown\"},{\"type\":\"library\",\"name\":\"@gcaf/donor-portal\",\"version\":\"5.1.0\",\"purl\":\"pkg:npm/%40gcaf/donor-portal@5.1.0\",\"license\":\"MIT\"},{\"type\":\"library\",\"name\":\"@gcaf/customs-bridge\",\"version\":\"2.0.7\",\"purl\":\"pkg:npm/%40gcaf/customs-bridge@2.0.7\",\"license\":\"MIT\"}],\"dependencies\":[{\"ref\":\"@gcaf/manifest-validator@4.2.1\",\"dependsOn\":[\"@gcaf/shipment-tracker@3.8.0\"]},{\"ref\":\"@gcaf/shipment-tracker@3.8.0\",\"dependsOn\":[\"@gcaf/geo-resolver@2.1.4\"]},{\"ref\":\"@gcaf/geo-resolver@2.1.4\",\"dependsOn\":[\"shadow-relay@1.0.3\"]}],\"vulnerabilities\":[{\"id\":\"PHANTOM-MERCY-001\",\"description\":\"Shadow data exfiltration relay embedded in geo-resolver dependency chain. Copies manifest data to external C2 endpoint via DNS tunneling.\",\"severity\":\"critical\",\"cvss\":10.0,\"affects\":[{\"ref\":\"shadow-relay@1.0.3\"}]}]}"
  }' | jq .
```

**Response:**

```json
{
  "packages_imported": 6,
  "dependencies_imported": 3,
  "vulnerabilities_found": 1
}
```

Six packages. Three dependency links. One vulnerability -- but what a vulnerability. That single API call just recreated the evidence chain Clara built by hand, sitting in a DGSE safe house in Marseille, cross-referencing npm audit logs against customs database access patterns.

The metadata tells a story too. Timestamp: `2026-02-12T03:14:00Z` -- 3:14 in the morning. Tool name: `clara-field-extract` version `1.0.0`. She built a custom tool to extract this data. She was working alone, at three in the morning, in a field position. That's Clara. Always was.

Here's what the full SBOM looks like when formatted properly:

```json
{
  "bomFormat": "CycloneDX",
  "specVersion": "1.5",
  "version": 1,
  "metadata": {
    "timestamp": "2026-02-12T03:14:00Z",
    "tools": [{ "name": "clara-field-extract", "version": "1.0.0" }],
    "component": {
      "type": "application",
      "name": "gcaf-logistics-platform",
      "version": "7.3.1"
    }
  },
  "components": [
    {
      "type": "library",
      "name": "shadow-relay",
      "version": "1.0.3",
      "purl": "pkg:npm/shadow-relay@1.0.3",
      "license": "unknown",
      "hashes": [
        { "alg": "SHA-256", "content": "e3b0c44298fc1c14..." },
        { "alg": "BLAKE3", "content": "af1349b9f5f9a1a6..." }
      ]
    }
  ],
  "vulnerabilities": [
    {
      "id": "PHANTOM-MERCY-001",
      "description": "Shadow data exfiltration relay embedded in geo-resolver dependency chain",
      "severity": "critical",
      "cvss": 10.0,
      "affects": [{ "ref": "shadow-relay@1.0.3" }],
      "recommendation": "Remove shadow-relay from dependency chain. Audit all manifest data processed since version 2.1.0 of geo-resolver."
    }
  ]
}
```

Pro tip: generate your SBOMs at build time, not deploy time. By the time code hits production, you want the SBOM already stored, diffed against the previous version, and any new vulnerabilities flagged. Clara didn't have that luxury. She had to reverse-engineer the SBOM from a running production system while maintaining her cover as a humanitarian aid worker. The fact that she got it right -- every dependency, every version, every hash -- tells me she spent weeks on this.

---

## 11.6 CVE Correlation: What shadow-relay Actually Does

When I registered the vulnerability against `shadow-relay`, I was working from Clara's notes. But now I need to understand the technical detail. What does this package actually do?

```bash
# Register the full vulnerability profile
curl -s -X POST http://localhost:3000/api/v1/supply-chain/vulnerabilities \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"package_id\": \"$SHADOW\",
    \"cve_id\": \"PHANTOM-MERCY-001\",
    \"title\": \"Shadow data exfiltration relay in humanitarian logistics pipeline\",
    \"description\": \"The shadow-relay package intercepts all data passed through the geo-resolver normalize() function. Manifest data including shipment contents, destination coordinates, recipient names, and ages is copied to a DNS tunneling endpoint at relay.pm-ops.example. Data is base64-encoded and split across TXT record queries to evade DLP. The package activates only when processing manifests tagged with category codes 4810-4899 (children's services). All other data passes through unmodified.\",
    \"severity\": \"critical\",
    \"cvss_score\": 10.0,
    \"affected_versions\": \">=1.0.0\",
    \"fix_version\": null
  }" | jq .
```

**Response:**

```json
{
  "id": "01951a10-dd04-7000-8000-000000000020",
  "package_id": "01951a04-bb05-7000-8000-000000000004",
  "cve_id": "PHANTOM-MERCY-001",
  "title": "Shadow data exfiltration relay in humanitarian logistics pipeline",
  "description": "The shadow-relay package intercepts all data passed through the geo-resolver normalize() function. Manifest data including shipment contents, destination coordinates, recipient names, and ages is copied to a DNS tunneling endpoint...",
  "severity": "critical",
  "cvss_score": 10.0,
  "affected_versions": ">=1.0.0",
  "fix_version": null,
  "published_at": "2026-02-18T02:15:00Z",
  "created_at": "2026-02-18T02:15:00Z"
}
```

Read that description again. "Activates only when processing manifests tagged with category codes 4810-4899 (children's services)." They're not exfiltrating everything. They're filtering. They only want the manifests related to children. Names. Ages. Destination coordinates.

My hands are shaking again. I need more coffee.

### Transitive Vulnerability Discovery

Here's where the dependency graph pays for itself. That `shadow-relay` vulnerability affects everything upstream:

```bash
# Find all transitive vulnerabilities for the manifest validator
curl -s "http://localhost:3000/api/v1/supply-chain/packages/$MANIFEST_ID/transitive-vulns" \
  -H "Authorization: Bearer $TOKEN" | jq .
```

```json
[
  {
    "id": "01951a10-dd04-7000-8000-000000000020",
    "package_id": "01951a04-bb05-7000-8000-000000000004",
    "cve_id": "PHANTOM-MERCY-001",
    "title": "Shadow data exfiltration relay in humanitarian logistics pipeline",
    "severity": "critical",
    "cvss_score": 10.0,
    "affected_versions": ">=1.0.0",
    "fix_version": null,
    "published_at": "2026-02-18T02:15:00Z",
    "created_at": "2026-02-18T02:15:00Z"
  }
]
```

The SQL behind this is a recursive CTE that walks the dependency tree and then joins against the vulnerability table:

```sql
WITH RECURSIVE dep_tree AS (
    -- Direct dependencies
    SELECT depends_on_id
    FROM sbom_dependencies WHERE package_id = $1

    UNION

    -- Transitive dependencies
    SELECT d.depends_on_id
    FROM sbom_dependencies d
    JOIN dep_tree dt ON dt.depends_on_id = d.package_id
)
SELECT v.id, v.package_id, v.cve_id, v.title, v.description,
       v.severity, v.cvss_score, v.affected_versions,
       v.fix_version, v.published_at, v.created_at
FROM sbom_vulnerabilities v
JOIN dep_tree dt ON v.package_id = dt.depends_on_id
ORDER BY v.cvss_score DESC NULLS LAST;
```

This query is the reason Clara was able to trace the infection. She didn't audit every package individually -- she built the dependency graph and walked it recursively. One compromised leaf node, three levels deep, and the whole tree is poisoned.

---

## 11.7 The Full GCAF Infection: Four Vectors, One Platform

Clara's notes describe four separate attack vectors PHANTOM MERCY used against GCAF. I'm registering all of them so I can run the risk assessment engine across the full attack surface.

```bash
# Vector 2: Compromised donor portal (maintainer takeover)
DONOR=$(curl -s -X POST http://localhost:3000/api/v1/supply-chain/packages \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "@gcaf/donor-portal",
    "version": "5.1.0",
    "ecosystem": "npm",
    "license": "MIT",
    "description": "Donor management portal. Maintainer recruited by shell company Meridian Consulting Group (PHANTOM MERCY front).",
    "supplier": "meridian-consulting-group",
    "purl": "pkg:npm/%40gcaf/donor-portal@5.1.0"
  }' | jq -r '.id')

# Register maintainer takeover vulnerability
curl -s -X POST http://localhost:3000/api/v1/supply-chain/vulnerabilities \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"package_id\": \"$DONOR\",
    \"cve_id\": \"PHANTOM-MERCY-002\",
    \"title\": \"Maintainer recruited by PHANTOM MERCY front company\",
    \"description\": \"The primary maintainer of @gcaf/donor-portal was hired by Meridian Consulting Group, a shell company linked to PHANTOM MERCY. Since version 5.0.0, donor contact information and donation patterns have been exfiltrated to a secondary C2 via HTTPS POST to analytics.mcg-consulting.example. The maintainer may not be aware of the exfiltration -- the code is obfuscated within a 'telemetry' module.\",
    \"severity\": \"critical\",
    \"cvss_score\": 9.5,
    \"affected_versions\": \">=5.0.0\",
    \"fix_version\": null
  }" | jq .

# Vector 3: Build system poisoning (Jenkins)
BUILD=$(curl -s -X POST http://localhost:3000/api/v1/supply-chain/packages \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "gcaf-ci-pipeline",
    "version": "2.4.0",
    "ecosystem": "docker",
    "license": "proprietary",
    "description": "GCAF Jenkins CI/CD build pipeline. Build environment compromised -- injects tracking beacon into compiled customs-bridge binary.",
    "supplier": "gcaf-devops",
    "purl": "pkg:docker/gcaf-ci-pipeline@2.4.0"
  }' | jq -r '.id')

curl -s -X POST http://localhost:3000/api/v1/supply-chain/vulnerabilities \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"package_id\": \"$BUILD\",
    \"cve_id\": \"PHANTOM-MERCY-003\",
    \"title\": \"CI/CD pipeline compromised -- binary injection in customs-bridge\",
    \"description\": \"The Jenkins build server at GCAF has been modified to inject a tracking beacon into the customs-bridge binary during compilation. Source code is clean; compiled artifact is not. The beacon reports customs clearance timestamps and locations to relay.pm-ops.example via HTTP/2 multiplexed streams disguised as CDN requests.\",
    \"severity\": \"critical\",
    \"cvss_score\": 9.8,
    \"affected_versions\": \">=2.3.0\",
    \"fix_version\": null
  }" | jq .

# Vector 4: Dependency confusion (fleet management)
FLEET=$(curl -s -X POST http://localhost:3000/api/v1/supply-chain/packages \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "@gcaf/fleet-gps",
    "version": "8.0.1",
    "ecosystem": "npm",
    "license": "unknown",
    "description": "COMPROMISED: Dependency confusion attack. Public registry package overrides internal fleet GPS module. Reports vehicle locations to PHANTOM MERCY.",
    "supplier": "unknown",
    "purl": "pkg:npm/%40gcaf/fleet-gps@8.0.1"
  }' | jq -r '.id')

curl -s -X POST http://localhost:3000/api/v1/supply-chain/vulnerabilities \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"package_id\": \"$FLEET\",
    \"cve_id\": \"PHANTOM-MERCY-004\",
    \"title\": \"Fleet GPS dependency confusion -- vehicle tracking exfiltration\",
    \"description\": \"A malicious @gcaf/fleet-gps package was published to the public npm registry with version 8.0.1, overriding the internal version 3.2.0. The package reports real-time GPS coordinates of all GCAF vehicles to a Telegram bot API endpoint. Vehicles carrying children's services shipments are tagged with high priority.\",
    \"severity\": \"critical\",
    \"cvss_score\": 10.0,
    \"affected_versions\": \"8.0.1\",
    \"fix_version\": null
  }" | jq .
```

Four vectors. Four critical vulnerabilities. One coordinated operation targeting a single humanitarian organization. This isn't opportunistic cybercrime. This is state-backed infrastructure designed to identify, locate, and track children moving through aid networks.

I need to stop and breathe.

---

## 11.8 Risk Assessment: Quantifying the Horror

```bash
# Assess risk for shadow-relay
curl -s -X POST "http://localhost:3000/api/v1/supply-chain/risk-assessment/$SHADOW" \
  -H "Authorization: Bearer $TOKEN" | jq .
```

```json
{
  "id": "01951a20-ee05-7000-8000-000000000030",
  "package_id": "01951a04-bb05-7000-8000-000000000004",
  "risk_level": "critical",
  "risk_score": 10.0,
  "factors": [
    { "factor": "vulnerability_count", "value": 1, "contribution": 2.0 },
    { "factor": "max_cvss_score", "value": 10.0, "contribution": 10.0 },
    { "factor": "dependency_count", "value": 0, "contribution": 0.0 },
    { "factor": "unknown_license", "value": true, "contribution": 1.0 }
  ],
  "assessed_at": "2026-02-18T02:30:00Z"
}
```

Risk score formula:

```
risk_score = min(vuln_count * 2.0 + max_cvss + min(dep_count * 0.5, 3.0) + license_unknown, 10.0)
         = min(1*2.0 + 10.0 + 0.0 + 1.0, 10.0)
         = min(13.0, 10.0)
         = 10.0  -- CRITICAL
```

The `unknown_license` flag is a massive red flag by itself. Every legitimate npm package has a license. A package with no license in a dependency chain that handles children's data? That should have been caught by any competent security review. But GCAF isn't a tech company. They're aid workers. They don't have a security team. They have a volunteer developer in Nairobi who maintains the platform on weekends.

That's the genius of PHANTOM MERCY's approach. They didn't attack a hardened target. They attacked the softest possible target -- a humanitarian organization with no budget, no security team, and a mission that makes people trust them implicitly.

```bash
# Assess risk for the fleet GPS dependency confusion
curl -s -X POST "http://localhost:3000/api/v1/supply-chain/risk-assessment/$FLEET" \
  -H "Authorization: Bearer $TOKEN" | jq .
```

```json
{
  "id": "01951a20-ee05-7000-8000-000000000031",
  "package_id": "01951a08-cc06-7000-8000-000000000008",
  "risk_level": "critical",
  "risk_score": 10.0,
  "factors": [
    { "factor": "vulnerability_count", "value": 1, "contribution": 2.0 },
    { "factor": "max_cvss_score", "value": 10.0, "contribution": 10.0 },
    { "factor": "dependency_count", "value": 0, "contribution": 0.0 },
    { "factor": "unknown_license", "value": true, "contribution": 1.0 }
  ],
  "assessed_at": "2026-02-18T02:31:00Z"
}
```

Two critical packages. Both with unknown licenses. Both with CVSS 10.0. In a normal supply chain audit, this would trigger a vendor review process. In this case, the "vendor" is a state intelligence operation running a child trafficking network through aid logistics software.

---

## 11.9 License Risk Analysis: The Unknown License Pattern

License changes in dependencies are a subtle but important attack indicator. Clara's SBOM shows a pattern: every compromised package either has an unknown license or had its license changed from a known value.

```bash
# Check all packages with unknown licenses
curl -s "http://localhost:3000/api/v1/supply-chain/packages" \
  -H "Authorization: Bearer $TOKEN" | jq '[.[] | select(.license == "unknown")] | {
    unknown_license_count: length,
    packages: [.[] | {name, version, ecosystem, risk_score}]
  }'
```

```json
{
  "unknown_license_count": 2,
  "packages": [
    {
      "name": "shadow-relay",
      "version": "1.0.3",
      "ecosystem": "npm",
      "risk_score": 10.0
    },
    {
      "name": "@gcaf/fleet-gps",
      "version": "8.0.1",
      "ecosystem": "npm",
      "risk_score": 10.0
    }
  ]
}
```

Clara wrote in the margin of her notes: "Unknown license = unknown provenance. If you can't verify who wrote it, you can't trust what it does." She underlined it three times.

For ongoing monitoring, build a SQL query that tracks license changes over time:

```sql
-- Detect packages where the license changed between versions
-- Clara's Pattern: legitimate packages get replaced with unknown-license forks
SELECT
    p1.name,
    p1.version AS old_version,
    p1.license AS old_license,
    p2.version AS new_version,
    p2.license AS new_license,
    p2.updated_at AS change_detected
FROM sbom_packages p1
JOIN sbom_packages p2
    ON p1.name = p2.name
    AND p1.ecosystem = p2.ecosystem
    AND p1.version != p2.version
WHERE p1.license != p2.license
    AND p1.created_at < p2.created_at
ORDER BY p2.updated_at DESC;
```

This query compares the same package across different registered versions and flags any license changes. In the GCAF case, `@gcaf/fleet-gps` went from MIT (internal version 3.2.0) to unknown (public version 8.0.1). That change alone should have been an alarm. But there was nobody watching.

---

## 11.10 Blast Radius: How Far the Infection Spread

When a dependency is compromised, the first question every CISO asks is: "How bad is it?" In this case, the answer is worse than anything I've seen in twenty years of security work.

```bash
# Get the dependency tree to understand blast radius
curl -s "http://localhost:3000/api/v1/supply-chain/packages/$MANIFEST_ID/tree" \
  -H "Authorization: Bearer $TOKEN" | jq '
    def count_nodes:
      1 + ([.children[] | count_nodes] | add // 0);
    {
      root: .name,
      root_version: .version,
      total_dependencies: (count_nodes - 1),
      tree: .
    }
  '
```

For larger graphs, the blast radius SQL walks the dependency chain upstream:

```sql
-- Blast radius: find all packages that depend on the compromised shadow-relay
WITH RECURSIVE blast_radius AS (
    -- Start from the compromised package
    SELECT
        d.package_id AS affected_id,
        p.name AS affected_name,
        p.version AS affected_version,
        1 AS distance
    FROM sbom_dependencies d
    JOIN sbom_packages p ON p.id = d.package_id
    WHERE d.depends_on_id = $1  -- $1 = shadow-relay package ID

    UNION ALL

    -- Walk upstream: who depends on the affected packages?
    SELECT
        d2.package_id AS affected_id,
        p2.name AS affected_name,
        p2.version AS affected_version,
        br.distance + 1 AS distance
    FROM sbom_dependencies d2
    JOIN sbom_packages p2 ON p2.id = d2.package_id
    JOIN blast_radius br ON br.affected_id = d2.depends_on_id
    WHERE br.distance < 15  -- Circuit breaker
)
SELECT DISTINCT
    affected_id,
    affected_name,
    affected_version,
    MIN(distance) AS shortest_path_to_compromise
FROM blast_radius
GROUP BY affected_id, affected_name, affected_version
ORDER BY shortest_path_to_compromise ASC, affected_name;
```

The blast radius for `shadow-relay`: every GCAF logistics operation in 14 countries. Every manifest processed since version 2.1.0 of `geo-resolver` was introduced -- roughly 18 months of shipment data. Thousands of manifests. Tens of thousands of names.

I'm building this blast radius analysis at 3 AM and I can feel Clara's urgency in every line of her notes. She wasn't documenting a vulnerability. She was documenting a crime scene.

---

## 11.11 The Supply Chain Stats

```bash
# Get overall supply chain stats
curl -s "http://localhost:3000/api/v1/supply-chain/stats" \
  -H "Authorization: Bearer $TOKEN" | jq .
```

```json
{
  "total_packages": 8,
  "total_dependencies": 4,
  "total_vulnerabilities": 4,
  "total_risk_assessments": 4,
  "high_risk_count": 4,
  "critical_vuln_count": 4
}
```

Four out of four risk assessments are critical. Four out of four vulnerabilities are critical. This isn't a software supply chain with a few weak spots. This is a supply chain that was designed from the ground up to be a weapon.

### Risk Assessment Reports

```bash
# List all risk assessments, worst first
curl -s "http://localhost:3000/api/v1/supply-chain/risks" \
  -H "Authorization: Bearer $TOKEN" | jq '[.[] | {
    package_id,
    risk_level,
    risk_score,
    assessed_at,
    top_factor: (.factors[0].factor // "none")
  }]'
```

```json
[
  {
    "package_id": "01951a04-bb05-7000-8000-000000000004",
    "risk_level": "critical",
    "risk_score": 10.0,
    "assessed_at": "2026-02-18T02:30:00Z",
    "top_factor": "vulnerability_count"
  },
  {
    "package_id": "01951a08-cc06-7000-8000-000000000008",
    "risk_level": "critical",
    "risk_score": 10.0,
    "assessed_at": "2026-02-18T02:31:00Z",
    "top_factor": "vulnerability_count"
  },
  {
    "package_id": "01951a06-cc05-7000-8000-000000000006",
    "risk_level": "critical",
    "risk_score": 9.5,
    "assessed_at": "2026-02-18T02:32:00Z",
    "top_factor": "max_cvss_score"
  },
  {
    "package_id": "01951a07-cc06-7000-8000-000000000007",
    "risk_level": "critical",
    "risk_score": 9.8,
    "assessed_at": "2026-02-18T02:33:00Z",
    "top_factor": "max_cvss_score"
  }
]
```

### Continuous Monitoring Queries

Here's the SQL I'd schedule to detect new compromises in aid networks:

```sql
-- Alert: new critical risk assessments in the last 24 hours
SELECT
    ra.id AS assessment_id,
    p.name AS package_name,
    p.version,
    p.ecosystem,
    ra.risk_level,
    ra.risk_score,
    ra.factors,
    ra.assessed_at
FROM supply_chain_risk_assessments ra
JOIN sbom_packages p ON p.id = ra.package_id
WHERE ra.risk_level IN ('high', 'critical')
    AND ra.assessed_at > NOW() - INTERVAL '24 hours'
ORDER BY ra.risk_score DESC;

-- Alert: packages with vulnerabilities but no risk assessment
-- (new infections that haven't been scored yet)
SELECT
    p.id,
    p.name,
    p.version,
    p.ecosystem,
    COUNT(v.id) AS vuln_count,
    MAX(v.cvss_score) AS max_cvss
FROM sbom_packages p
JOIN sbom_vulnerabilities v ON v.package_id = p.id
LEFT JOIN supply_chain_risk_assessments ra ON ra.package_id = p.id
WHERE ra.id IS NULL
GROUP BY p.id, p.name, p.version, p.ecosystem
HAVING COUNT(v.id) > 0
ORDER BY MAX(v.cvss_score) DESC NULLS LAST;
```

---

## 11.12 Integration with Threat Intelligence

The supply chain module doesn't live in isolation. When Playseat's threat intelligence feeds detect a new advisory affecting a package in your SBOM, the connection is automatic. For PHANTOM MERCY, I'm creating cross-references between the supply chain findings and the threat intel from Chapter 8's sentinel baselines:

```bash
# Register shadow-relay's C2 domain as an IOC
curl -s -X POST http://localhost:3000/api/v1/supply-chain/vulnerabilities \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "cve_id": "PHANTOM-MERCY-005",
    "title": "C2 infrastructure: relay.pm-ops.example DNS tunneling endpoint",
    "description": "All four supply chain vectors exfiltrate data to relay.pm-ops.example via DNS tunneling. TXT record queries encode base64 manifest data. The domain resolves to rotating Cloudflare Workers endpoints. Clara identified the domain through DNS query volume anomalies on the GCAF network.",
    "severity": "critical",
    "cvss_score": 10.0,
    "affected_versions": "all",
    "fix_version": null
  }' | jq .
```

The workflow is: supply chain analysis identifies the compromised package, the vulnerability details identify the C2 infrastructure, threat intelligence correlates the C2 against known PHANTOM MERCY indicators from the Genome module (Chapter 6), and the ADAPT cycle kicks off a full investigation.

That's the pipeline Clara built, alone, in the field, before she went silent.

---

## 11.13 What Clara Found at the Bottom

**2026-02-18T04:15:00Z -- My apartment. Coffee is cold.**

I've been through every line of Clara's SBOM. Here's what I now know:

PHANTOM MERCY isn't just trafficking children. They're using the logistics infrastructure of a legitimate humanitarian organization to do it. The GCAF platform processes 400+ shipments per month across 14 countries. Every shipment tagged with children's services category codes gets flagged, and the manifest data -- names, ages, destination coordinates, arrival times -- gets exfiltrated to PHANTOM MERCY's command infrastructure.

They know when. They know where. They know who.

The supply chain infection is the mechanism. The children are the target. And Clara found it all.

Her last note, scrawled on the back of a field receipt from a cafe in Marseille: "Follow the manifests. The supply chain IS the operation. Everything else is noise."

I'm following the manifests, Clara. I'm following them.

---

## 11.14 Lessons from the Trenches

**1. SBOMs for non-software supply chains.** Clara's breakthrough was applying software composition analysis to a logistics platform. The same dependency graph techniques that find compromised npm packages can find compromised shipping systems. Any system with components has a supply chain. Any supply chain can be weaponized.

**2. License anomalies are the first warning.** Both of PHANTOM MERCY's injected packages had unknown licenses. In a humanitarian org, nobody checks. In a defense platform, that's a critical alert. Automate the check.

**3. Transitive dependencies are where the real attacks hide.** Nobody reviews code three levels deep. That's exactly where PHANTOM MERCY buried `shadow-relay`. The recursive CTE queries in this chapter aren't academic exercises -- they're the only way to find infections that are deliberately hidden below the audit horizon.

**4. Build system integrity is non-negotiable.** PHANTOM MERCY poisoned the Jenkins pipeline. The source code was clean. The binary was not. If you're not hashing your build artifacts and comparing them against reproducible builds, you're trusting a process you can't verify.

**5. Humanitarian organizations are soft targets with hard data.** GCAF had no security budget, no SBOM generation, no dependency auditing. They had the names and locations of thousands of children. The asymmetry between the value of their data and the maturity of their security is criminal -- and PHANTOM MERCY exploited it perfectly.

**6. Clara was right.** Trust nothing downstream.

---

## 11.15 Quick Reference

| Operation | Endpoint | Method |
|-----------|----------|--------|
| Register package | `/api/v1/supply-chain/packages` | POST |
| List packages | `/api/v1/supply-chain/packages` | GET |
| Get package | `/api/v1/supply-chain/packages/{id}` | GET |
| Update package | `/api/v1/supply-chain/packages/{id}` | PUT |
| Delete package | `/api/v1/supply-chain/packages/{id}` | DELETE |
| Add dependency | `/api/v1/supply-chain/packages/{id}/dependencies` | POST |
| List dependencies | `/api/v1/supply-chain/packages/{id}/dependencies` | GET |
| Dependency tree | `/api/v1/supply-chain/packages/{id}/tree` | GET |
| Package vulnerabilities | `/api/v1/supply-chain/packages/{id}/vulnerabilities` | GET |
| Transitive vulnerabilities | `/api/v1/supply-chain/packages/{id}/transitive-vulns` | GET |
| Register vulnerability | `/api/v1/supply-chain/vulnerabilities` | POST |
| List vulnerabilities | `/api/v1/supply-chain/vulnerabilities` | GET |
| Assess risk | `/api/v1/supply-chain/risk-assessment/{id}` | POST |
| List risk assessments | `/api/v1/supply-chain/risks` | GET |
| Import SBOM | `/api/v1/supply-chain/import-sbom` | POST |
| Supply chain stats | `/api/v1/supply-chain/stats` | GET |

---

*Next chapter: Purple Team Operations -- where I simulate PHANTOM MERCY's attack path to find the one weakness Clara told me to look for.*

---

`© 2026 Playseat — All Rights Reserved | Defensive Intelligence Through ADAPT`
