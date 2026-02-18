# Chapter 22: Into the Dark — Monitoring Underground Markets

> "We found 14,000 employee credentials for sale on a Tor marketplace three hours before the ransomware group that bought them tried to use them. Three hours. That is the margin between a breach notification and a Tuesday."
> — Threat Intel Lead, post-incident debrief, February 2026

---

## Why This Chapter Exists

Let me be direct about something: we do not operate on the dark web. We do not purchase stolen data. We do not interact with threat actors in marketplaces. What we do is monitor — passively, legally, and deliberately — the public-facing indicators that emerge from underground activity. The distinction matters legally and ethically, and if you blur that line, you will create more problems than you solve.

That said, ignoring the dark web is not an option in 2026. In January alone, three major government contractors had employee credentials appear on Genesis Market successor sites. Two ransomware groups — one tracked as SYNTHETIC-LOCKSMITH and another as PHANTOM-WEAVER — posted data from defense-adjacent firms on their leak sites. Our OSINT module picked up all of it before the victims knew they had been compromised.

This chapter covers the monitoring architecture, the correlation engine that links dark web indicators to your assets, and the investigation workflow when you find your organization's data somewhere it should not be.

---

## The Dark Web Monitoring Architecture

### What We Monitor and What We Do Not

Let me be clear about boundaries:

**We monitor (legal, passive):**
- Tor-hosted leak sites (public pages only)
- Paste sites (Pastebin, PrivateBin, Ghostbin successors)
- Dark web forums with public-facing mirrors
- Telegram channels used by ransomware groups
- Genesis Market / Russian Market successor storefronts
- Credential dump aggregators
- Ransomware "name and shame" sites
- Breach notification databases (HIBP, DeHashed)

**We do not do (illegal, active):**
- Purchase stolen credentials or data
- Create accounts on criminal marketplaces
- Interact with or message threat actors
- Download full breach databases
- Access sites that require payment or criminal acts for entry

### Configuring OSINT Dark Web Feeds

The OSINT module in Playseat supports structured feeds from dark web monitoring services. Here is the schema from migration `015_osint_intelligence.sql`:

```sql
CREATE TABLE IF NOT EXISTS osint_profiles (
    id              UUID PRIMARY KEY,
    campaign_id     UUID NOT NULL REFERENCES campaigns(id),
    entity_type     VARCHAR(32) NOT NULL,
    primary_name    VARCHAR(512) NOT NULL,
    aliases         JSONB NOT NULL DEFAULT '[]',
    summary         TEXT NOT NULL,
    exposure_level  VARCHAR(16) NOT NULL DEFAULT 'minimal',
    confidence_score REAL NOT NULL DEFAULT 0.0,
    digital_footprint JSONB NOT NULL DEFAULT '{}',
    social_footprint JSONB NOT NULL DEFAULT '{}',
    corporate_footprint JSONB NOT NULL DEFAULT '{}',
    source_count    INTEGER NOT NULL DEFAULT 0,
    finding_count   INTEGER NOT NULL DEFAULT 0,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS osint_source_results (
    id              UUID PRIMARY KEY,
    profile_id      UUID REFERENCES osint_profiles(id),
    source_type     VARCHAR(32) NOT NULL,
    source_name     VARCHAR(256) NOT NULL,
    source_url      TEXT,
    title           VARCHAR(512) NOT NULL,
    content         TEXT NOT NULL,
    raw_data        JSONB,
    confidence      REAL NOT NULL DEFAULT 0.0,
    metadata        JSONB NOT NULL DEFAULT '{}',
    collected_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

### Setting Up Monitoring Profiles

Create an OSINT profile for your organization. This is the anchor that all dark web monitoring correlates against:

```bash
# Create an OSINT profile for your organization
curl -X POST https://playseat.internal/api/v1/osint/profiles \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "campaign_id": "01945000-0000-7000-8000-000000000100",
    "target_name": "Acme Defense Systems",
    "organization": "Acme Defense",
    "aliases": [
      "acmedefense.gov",
      "acme-defense.com",
      "ADS",
      "Acme Defense Systems LLC"
    ],
    "source_types": [
      "dark_web_leak_sites",
      "paste_sites",
      "credential_dumps",
      "ransomware_leak_sites",
      "telegram_channels",
      "breach_databases"
    ]
  }'
```

Response:

```json
{
  "id": "01946000-0000-7000-8000-000000000001",
  "campaign_id": "01945000-0000-7000-8000-000000000100",
  "entity_type": "organization",
  "primary_name": "Acme Defense Systems",
  "aliases": ["acmedefense.gov", "acme-defense.com", "ADS", "Acme Defense Systems LLC"],
  "summary": "Organization monitoring profile for dark web intelligence",
  "exposure_level": "minimal",
  "confidence_score": 0.0,
  "source_count": 0,
  "finding_count": 0,
  "digital_footprint": {},
  "social_footprint": {},
  "corporate_footprint": {},
  "created_at": "2026-02-18T10:00:00Z",
  "updated_at": "2026-02-18T10:00:00Z"
}
```

### Configuring Feed Sources

Now configure the specific intelligence feeds. Each feed type has different polling intervals and correlation strategies:

```bash
# Configure dark web leak site monitoring
curl -X POST https://playseat.internal/api/v1/threatintel/feeds \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "DarkFeed Leak Site Monitor",
    "feed_type": "dark_web_aggregator",
    "url": "https://darkfeed-api.internal/v2/leaks",
    "format": "json",
    "polling_interval_seconds": 300,
    "auth_type": "api_key",
    "enabled": true,
    "filters": {
      "keywords": ["acmedefense", "acme-defense", "acme defense"],
      "email_domains": ["acmedefense.gov", "acme-defense.com"],
      "sectors": ["defense", "government"],
      "threat_types": ["credential_leak", "data_dump", "ransomware_post"]
    }
  }'

# Configure credential monitoring
curl -X POST https://playseat.internal/api/v1/threatintel/feeds \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Credential Leak Aggregator",
    "feed_type": "credential_monitor",
    "url": "https://cred-monitor.internal/v1/stream",
    "format": "json_stream",
    "polling_interval_seconds": 60,
    "auth_type": "api_key",
    "enabled": true,
    "filters": {
      "email_domains": ["acmedefense.gov", "acme-defense.com"],
      "include_hashed": true,
      "include_cleartext": true,
      "min_confidence": 0.7
    }
  }'

# Configure ransomware group leak site monitoring
curl -X POST https://playseat.internal/api/v1/threatintel/feeds \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Ransomware Leak Site Tracker",
    "feed_type": "ransomware_monitor",
    "url": "https://ransom-tracker.internal/v1/posts",
    "format": "json",
    "polling_interval_seconds": 600,
    "auth_type": "api_key",
    "enabled": true,
    "filters": {
      "keywords": ["acme", "defense", "government"],
      "groups": [
        "SYNTHETIC-LOCKSMITH",
        "PHANTOM-WEAVER",
        "LockBit-4.0",
        "BlackCat-Successor",
        "Cl0p-Revival"
      ]
    }
  }'
```

---

## Credential Leak Monitoring and Correlation

### The Correlation Pipeline

When a credential dump appears on a paste site or dark web marketplace, the raw data looks like this:

```
user@acmedefense.gov:P@ssw0rd123!
j.smith@acme-defense.com:Summer2025!
admin@acmedefense.gov:Changem3Now
svc_backup@acmedefense.gov:B@ckup2024$ecure
```

Playseat's correlation engine matches these against your Active Directory, HR systems, and identity providers to determine:
1. Is the credential still valid?
2. Is the user still employed?
3. What systems does this credential grant access to?
4. Has the password been rotated since the leak date?

### Credential Correlation SQL

```sql
-- Correlate leaked credentials against internal identity store
-- This query runs when new credential dumps are ingested

-- Step 1: Create a temporary table with leaked credentials
CREATE TEMPORARY TABLE temp_leaked_creds (
    email VARCHAR(512) NOT NULL,
    password_hash VARCHAR(256),
    source VARCHAR(256) NOT NULL,
    leak_date TIMESTAMPTZ,
    confidence REAL NOT NULL DEFAULT 0.5
);

-- In production, this is populated by the feed ingestion pipeline
-- Example insert for illustration:
INSERT INTO temp_leaked_creds (email, password_hash, source, leak_date, confidence)
VALUES
    ('user@acmedefense.gov', 'sha256:a7f2e3...', 'paste_site_7831', '2026-01-15', 0.9),
    ('j.smith@acme-defense.com', 'sha256:b3c4d5...', 'dark_market_genesis2', '2026-01-20', 0.85),
    ('admin@acmedefense.gov', 'sha256:c5d6e7...', 'telegram_channel_x', '2026-02-01', 0.95),
    ('svc_backup@acmedefense.gov', 'sha256:d7e8f9...', 'ransomware_leak_lbs4', '2026-02-10', 0.80);

-- Step 2: Correlate against internal user records
WITH leaked AS (
    SELECT * FROM temp_leaked_creds
),
internal_users AS (
    SELECT
        u.id,
        u.email,
        u.username,
        u.role,
        u.last_password_change,
        u.is_active,
        u.created_at
    FROM users u
    WHERE u.email IN (SELECT email FROM leaked)
),
correlation AS (
    SELECT
        l.email,
        l.source,
        l.leak_date,
        l.confidence AS leak_confidence,
        iu.id AS user_id,
        iu.username,
        iu.role,
        iu.is_active,
        iu.last_password_change,
        -- Risk assessment
        CASE
            WHEN iu.id IS NULL THEN 'unknown_user'
            WHEN NOT iu.is_active THEN 'inactive_user'
            WHEN iu.last_password_change > l.leak_date THEN 'password_rotated'
            WHEN iu.role IN ('admin', 'soc_admin', 'ot_admin') THEN 'critical_active'
            ELSE 'active_unrotated'
        END AS risk_status,
        -- Priority score
        CASE
            WHEN iu.role IN ('admin', 'soc_admin', 'ot_admin')
                 AND iu.is_active
                 AND (iu.last_password_change IS NULL OR iu.last_password_change < l.leak_date)
            THEN 10
            WHEN iu.is_active
                 AND (iu.last_password_change IS NULL OR iu.last_password_change < l.leak_date)
            THEN 7
            WHEN iu.is_active AND iu.last_password_change > l.leak_date
            THEN 3
            WHEN NOT iu.is_active
            THEN 2
            ELSE 1
        END AS priority_score
    FROM leaked l
    LEFT JOIN internal_users iu ON LOWER(l.email) = LOWER(iu.email)
)
SELECT
    email,
    source,
    leak_date,
    leak_confidence,
    user_id,
    username,
    role,
    is_active,
    last_password_change,
    risk_status,
    priority_score
FROM correlation
ORDER BY priority_score DESC, leak_confidence DESC;
```

### Automated Alert Generation

When the correlation engine finds active, unrotated credentials, generate an alert immediately:

```bash
# Generate a critical alert for leaked admin credential
curl -X POST https://playseat.internal/api/v1/anomaly/alerts \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "anomaly_id": "01946100-0000-7000-8000-000000000001",
    "severity": "critical",
    "message": "CREDENTIAL LEAK: Active admin account admin@acmedefense.gov found on dark web marketplace (source: telegram_channel_x, leak date: 2026-02-01). Password has NOT been rotated since leak date. Account has admin-level access to 47 systems including OT jump servers. Immediate forced password reset required."
  }'
```

### Enrichment via OSINT Search

Once you have a leaked credential, search for additional exposure:

```bash
# Search for additional exposure of the compromised email
curl -X POST https://playseat.internal/api/v1/osint/search \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "target_name": "admin@acmedefense.gov",
    "organization": "Acme Defense Systems",
    "source_types": [
      "paste_sites",
      "breach_databases",
      "dark_web_forums",
      "social_media",
      "code_repositories"
    ]
  }'
```

Response:

```json
{
  "results": [
    {
      "source_type": "breach_database",
      "source_name": "HIBP Aggregated",
      "title": "admin@acmedefense.gov found in 3 breach databases",
      "content": "Email appeared in: MegaCorpLeak2024, CloudServiceBreach2025, VPNProviderDump2026",
      "confidence": 0.95,
      "metadata": {
        "breach_count": 3,
        "earliest_breach": "2024-03-15",
        "latest_breach": "2026-01-28",
        "password_reuse_detected": true
      }
    },
    {
      "source_type": "paste_sites",
      "source_name": "PasteMonitor",
      "title": "Credential pair found on paste site",
      "content": "Full credential pair (email:password) posted on public paste site",
      "confidence": 0.88,
      "metadata": {
        "paste_url": "https://paste-archive.example/raw/7f3a2b",
        "posted_at": "2026-02-05T14:30:00Z",
        "includes_cleartext": true
      }
    },
    {
      "source_type": "code_repositories",
      "source_name": "GitLeaks Monitor",
      "title": "Email found in public GitHub repository",
      "content": "Email address found in committed .env file in public repository",
      "confidence": 0.72,
      "metadata": {
        "repo": "contractor-tools/deploy-scripts",
        "file": ".env.production",
        "committed_at": "2025-11-10T09:15:00Z"
      }
    }
  ]
}
```

---

## Ransomware Group Communication Monitoring

### Tracking Leak Site Posts

Ransomware groups operate public-facing "name and shame" sites where they post victim data to pressure payment. Monitoring these sites provides early warning when your organization — or your supply chain partners — appear.

```bash
# Query ransomware leak site posts mentioning your sector
curl -X GET "https://playseat.internal/api/v1/threatintel/iocs?type=ransomware_post&sector=defense" \
  -H "Authorization: Bearer ${TOKEN}"
```

Response:

```json
{
  "iocs": [
    {
      "id": "01946200-0000-7000-8000-000000000001",
      "ioc_type": "ransomware_post",
      "value": "SYNTHETIC-LOCKSMITH posted: 'Acme Defense subcontractor data - 2.3TB'",
      "source": "ransomware_leak_monitor",
      "confidence": 0.92,
      "metadata": {
        "group": "SYNTHETIC-LOCKSMITH",
        "victim_claimed": "TechSubCon LLC (Acme Defense Subcontractor)",
        "data_size_tb": 2.3,
        "data_types_claimed": ["contracts", "employee_records", "technical_drawings"],
        "deadline": "2026-02-25T00:00:00Z",
        "post_url_hash": "sha256:abc123...",
        "first_seen": "2026-02-15T08:00:00Z"
      },
      "created_at": "2026-02-15T08:05:00Z"
    }
  ]
}
```

This is a supply chain alert — TechSubCon is a subcontractor. Their breach potentially exposes your data.

### Creating an Investigation from a Leak Post

```bash
# Create an investigation campaign for the supply chain leak
curl -X POST https://playseat.internal/api/v1/campaigns \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "INV-2026-0218: TechSubCon Supply Chain Data Leak",
    "description": "Investigation into SYNTHETIC-LOCKSMITH ransomware group posting claiming 2.3TB of data from TechSubCon LLC, an Acme Defense subcontractor. Priority: determine if Acme Defense data is included in the leak.",
    "scope": "supply_chain_breach",
    "priority": "critical"
  }'
```

---

## Initial Access Broker Tracking

### What Are IABs?

Initial Access Brokers (IABs) are threat actors who specialize in gaining initial access to organizations and then selling that access on underground markets. In February 2026, we tracked a surge in IAB listings targeting the defense sector. One listing read:

> "US defense contractor, VPN + RDP access, domain admin possible, $15,000 starting bid"

### IAB Indicator Tracking

```sql
-- Track Initial Access Broker activity targeting your sector
-- This query correlates IAB listings with your asset inventory

WITH iab_listings AS (
    SELECT
        i.id,
        i.value AS listing_description,
        i.metadata->>'sector' AS target_sector,
        i.metadata->>'access_type' AS access_type,
        i.metadata->>'geography' AS geography,
        i.metadata->>'asking_price' AS asking_price,
        i.metadata->>'broker_alias' AS broker_alias,
        i.metadata->>'listing_platform' AS platform,
        (i.metadata->>'first_seen')::TIMESTAMPTZ AS first_seen_at,
        i.confidence
    FROM threat_intel_iocs i
    WHERE i.ioc_type = 'iab_listing'
      AND i.created_at > NOW() - INTERVAL '30 days'
),
sector_matches AS (
    SELECT *
    FROM iab_listings
    WHERE target_sector IN ('defense', 'government', 'defense_industrial_base')
       OR listing_description ILIKE '%defense%'
       OR listing_description ILIKE '%government%'
       OR listing_description ILIKE '%cleared%'
)
SELECT
    id,
    listing_description,
    target_sector,
    access_type,
    geography,
    asking_price,
    broker_alias,
    platform,
    first_seen_at,
    confidence,
    -- Cross-reference with our own attack surface
    (SELECT COUNT(*) FROM adapt_exposure_events
     WHERE event_type IN ('new_port', 'new_service')
       AND severity IN ('critical', 'high')
       AND detected_at > NOW() - INTERVAL '90 days'
    ) AS our_recent_exposures,
    -- Check if described access method matches our infrastructure
    CASE
        WHEN access_type = 'vpn' AND EXISTS (
            SELECT 1 FROM adapt_exposure_events
            WHERE details->>'service' LIKE '%vpn%'
              AND detected_at > NOW() - INTERVAL '90 days'
        ) THEN 'POSSIBLE_MATCH'
        WHEN access_type = 'rdp' AND EXISTS (
            SELECT 1 FROM adapt_exposure_events
            WHERE details->>'port' = '3389'
              AND detected_at > NOW() - INTERVAL '90 days'
        ) THEN 'POSSIBLE_MATCH'
        ELSE 'no_match'
    END AS infrastructure_correlation
FROM sector_matches
ORDER BY
    CASE WHEN infrastructure_correlation = 'POSSIBLE_MATCH' THEN 0 ELSE 1 END,
    first_seen_at DESC;
```

---

## Real Scenario: Discovering Your Data for Sale

### The Discovery

It is 07:15 on a Tuesday. The credential monitoring feed fires an alert. Not one credential — 14,000 of them. All with your email domain. The source: a Tor-hosted marketplace that sells "combo lists" — username/password pairs organized by domain.

Here is the investigation workflow I have run three times now in production:

### Step 1: Scope the Leak

```bash
# Search OSINT sources for the full scope of the leak
curl -X POST https://playseat.internal/api/v1/osint/search \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "target_name": "acmedefense.gov",
    "organization": "Acme Defense Systems",
    "source_types": ["credential_dumps", "breach_databases", "paste_sites"]
  }'
```

### Step 2: Calculate Exposure

```bash
# Get the organization exposure score
curl -X GET "https://playseat.internal/api/v1/osint/score/${PROFILE_ID}" \
  -H "Authorization: Bearer ${TOKEN}"
```

Response:

```json
{
  "profile_id": "01946000-0000-7000-8000-000000000001",
  "exposure_level": "critical",
  "confidence_score": 0.94,
  "breakdown": {
    "credential_exposure": {
      "total_credentials_found": 14237,
      "unique_emails": 8941,
      "cleartext_passwords": 3102,
      "hashed_passwords": 11135,
      "active_employees_affected": 6723,
      "admin_accounts_affected": 47,
      "service_accounts_affected": 12,
      "most_recent_leak": "2026-02-14T00:00:00Z"
    },
    "data_exposure": {
      "documents_found": 0,
      "code_repositories": 3,
      "internal_urls_leaked": 17
    },
    "risk_score": 9.4
  }
}
```

### Step 3: Correlate and Prioritize

```sql
-- Prioritized credential leak response query
-- Groups leaked credentials by risk tier for response prioritization

WITH leaked_creds AS (
    -- Simulated join against credential leak staging table
    SELECT
        osr.id,
        osr.metadata->>'email' AS email,
        osr.metadata->>'password_type' AS password_type,
        osr.metadata->>'source_breach' AS source_breach,
        (osr.metadata->>'leak_date')::TIMESTAMPTZ AS leak_date,
        osr.confidence
    FROM osint_source_results osr
    WHERE osr.source_type = 'credential_dumps'
      AND osr.profile_id = '01946000-0000-7000-8000-000000000001'
      AND osr.collected_at > NOW() - INTERVAL '24 hours'
),
user_lookup AS (
    SELECT
        lc.*,
        u.id AS user_id,
        u.username,
        u.role,
        u.is_active,
        u.last_login
    FROM leaked_creds lc
    LEFT JOIN users u ON LOWER(lc.email) = LOWER(u.email)
),
risk_tiers AS (
    SELECT
        *,
        CASE
            -- Tier 1: Active admin accounts with cleartext passwords
            WHEN is_active AND role IN ('admin', 'soc_admin')
                 AND password_type = 'cleartext'
            THEN 'TIER_1_CRITICAL'
            -- Tier 2: Active privileged accounts (any password type)
            WHEN is_active AND role IN ('admin', 'soc_admin', 'analyst', 'ot_admin')
            THEN 'TIER_2_HIGH'
            -- Tier 3: Active standard accounts with cleartext
            WHEN is_active AND password_type = 'cleartext'
            THEN 'TIER_3_MEDIUM'
            -- Tier 4: Active standard accounts with hashed passwords
            WHEN is_active
            THEN 'TIER_4_LOW'
            -- Tier 5: Inactive accounts
            ELSE 'TIER_5_INACTIVE'
        END AS risk_tier
    FROM user_lookup
)
SELECT
    risk_tier,
    COUNT(*) AS account_count,
    COUNT(*) FILTER (WHERE password_type = 'cleartext') AS cleartext_count,
    COUNT(*) FILTER (WHERE last_login > NOW() - INTERVAL '7 days') AS recently_active,
    ARRAY_AGG(DISTINCT role) AS roles_affected,
    MIN(leak_date) AS earliest_leak,
    MAX(leak_date) AS latest_leak
FROM risk_tiers
GROUP BY risk_tier
ORDER BY
    CASE risk_tier
        WHEN 'TIER_1_CRITICAL' THEN 1
        WHEN 'TIER_2_HIGH' THEN 2
        WHEN 'TIER_3_MEDIUM' THEN 3
        WHEN 'TIER_4_LOW' THEN 4
        WHEN 'TIER_5_INACTIVE' THEN 5
    END;
```

### Step 4: Automated Response

```bash
# Trigger SOAR playbook for mass credential leak response
curl -X POST https://playseat.internal/api/v1/soar/playbooks/execute \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "playbook_id": "01946300-0000-7000-8000-000000000001",
    "trigger": "credential_leak_mass",
    "context": {
      "leak_source": "dark_web_combo_list",
      "total_credentials": 14237,
      "tier_1_critical": 47,
      "tier_2_high": 312,
      "tier_3_medium": 3102,
      "actions": [
        {
          "tier": "TIER_1_CRITICAL",
          "action": "immediate_password_reset_force",
          "action_detail": "Force reset all 47 admin accounts. Revoke all active sessions. Require MFA re-enrollment. Notify CISO.",
          "sla_minutes": 30
        },
        {
          "tier": "TIER_2_HIGH",
          "action": "urgent_password_reset_notify",
          "action_detail": "Send forced reset notification to 312 privileged accounts. 4-hour compliance window.",
          "sla_minutes": 240
        },
        {
          "tier": "TIER_3_MEDIUM",
          "action": "password_reset_campaign",
          "action_detail": "Email notification to 3,102 users with cleartext exposure. 24-hour compliance window. Block after deadline.",
          "sla_minutes": 1440
        }
      ]
    }
  }'
```

---

## Attribution Challenges in Anonymous Networks

### What Attribution Looks Like in Practice

Attribution on the dark web is probabilistic, never certain. Here is the honest framework we use:

```bash
# Create an attribution analysis
curl -X POST https://playseat.internal/api/v1/threatintel/attribution \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "incident_id": "01946400-0000-7000-8000-000000000001",
    "indicators": [
      {
        "type": "infrastructure",
        "value": "198.51.100.42",
        "confidence": 0.85,
        "note": "C2 server IP, previously attributed to SYNTHETIC-LOCKSMITH infrastructure"
      },
      {
        "type": "ttp",
        "value": "T1486 + T1490 + T1027.005",
        "confidence": 0.70,
        "note": "Ransomware deployment chain matches SYNTHETIC-LOCKSMITH playbook"
      },
      {
        "type": "linguistic",
        "value": "ransom_note_language_analysis",
        "confidence": 0.45,
        "note": "Ransom note contains phrasing consistent with Eastern European origin but could be deliberate misdirection"
      },
      {
        "type": "timing",
        "value": "activity_hours_utc_0600_1800",
        "confidence": 0.30,
        "note": "Activity concentrated in UTC+3 business hours, but could be automated"
      }
    ],
    "assessment": {
      "primary_attribution": "SYNTHETIC-LOCKSMITH",
      "confidence": "moderate",
      "alternative_hypotheses": [
        "PHANTOM-WEAVER using borrowed infrastructure",
        "New group mimicking known TTPs",
        "False flag operation"
      ],
      "analyst_note": "Infrastructure overlap is strong, but TTPs alone are insufficient for high-confidence attribution. Recommend monitoring for additional corroborating indicators."
    }
  }'
```

### Attribution Confidence SQL

```sql
-- Calculate attribution confidence score based on indicator overlap
WITH incident_indicators AS (
    SELECT
        i.id AS indicator_id,
        i.ioc_type,
        i.value,
        i.confidence,
        i.metadata->>'attributed_to' AS known_attribution
    FROM threat_intel_iocs i
    WHERE i.id IN (
        -- Indicators linked to current investigation
        SELECT UNNEST(ARRAY[
            '01946500-0000-7000-8000-000000000001',
            '01946500-0000-7000-8000-000000000002',
            '01946500-0000-7000-8000-000000000003'
        ]::UUID[])
    )
),
historical_overlap AS (
    SELECT
        ii.indicator_id,
        ii.ioc_type,
        ii.value,
        ii.known_attribution,
        COUNT(DISTINCT h.id) AS historical_match_count,
        MAX(h.confidence) AS max_historical_confidence
    FROM incident_indicators ii
    LEFT JOIN threat_intel_iocs h ON (
        h.value = ii.value
        AND h.id != ii.indicator_id
        AND h.metadata->>'attributed_to' IS NOT NULL
    )
    GROUP BY ii.indicator_id, ii.ioc_type, ii.value, ii.known_attribution
)
SELECT
    known_attribution AS attributed_group,
    COUNT(*) AS matching_indicators,
    ROUND(AVG(max_historical_confidence)::NUMERIC, 2) AS avg_confidence,
    ARRAY_AGG(DISTINCT ioc_type) AS indicator_types,
    -- Diamond Model completeness
    (CASE WHEN BOOL_OR(ioc_type = 'ip_address') THEN 1 ELSE 0 END +
     CASE WHEN BOOL_OR(ioc_type = 'domain') THEN 1 ELSE 0 END +
     CASE WHEN BOOL_OR(ioc_type = 'malware_hash') THEN 1 ELSE 0 END +
     CASE WHEN BOOL_OR(ioc_type IN ('ttp', 'technique')) THEN 1 ELSE 0 END
    ) AS diamond_model_coverage
FROM historical_overlap
WHERE known_attribution IS NOT NULL
GROUP BY known_attribution
ORDER BY matching_indicators DESC, avg_confidence DESC;
```

---

## Legal Considerations for Dark Web Intelligence

### What You Can and Cannot Do

This is not legal advice — consult your organization's legal counsel. But here is the framework I use:

**Generally permissible (in most US jurisdictions):**
- Monitoring public-facing pages on Tor (same as monitoring any public website)
- Collecting IOCs from publicly posted breach data
- Searching breach notification databases (HIBP, etc.)
- Monitoring paste sites for your own organization's data
- Subscribing to commercial dark web intelligence feeds

**Gray area (get legal approval first):**
- Creating accounts on forums (even with fake identities)
- Downloading samples of leaked data to verify authenticity
- Taking screenshots of marketplace listings
- Automated scraping of dark web sites

**Do not do this:**
- Purchasing stolen data, credentials, or access
- Interacting with threat actors (even to negotiate)
- Accessing sites that require illegal acts for entry
- Downloading child exploitation material (even as "evidence")
- Hacking back against threat actors

### Documenting Legal Compliance

Every dark web monitoring action should be logged with legal justification:

```bash
# Record a dark web monitoring action with legal compliance metadata
curl -X POST https://playseat.internal/api/v1/audit/events \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "event_type": "dark_web_monitoring",
    "action": "passive_leak_site_check",
    "actor_id": "01945000-0000-7000-8000-000000000010",
    "details": {
      "target": "ransomware_leak_site_synthetic_locksmith",
      "method": "automated_feed_ingestion",
      "data_collected": "listing_metadata_only",
      "no_data_purchased": true,
      "no_account_created": true,
      "no_interaction": true,
      "legal_basis": "Monitoring publicly available information for defensive purposes per 18 USC 1030(f)",
      "approved_by": "legal_counsel_2026-01-15",
      "approval_reference": "LEGAL-2026-0115-DWM"
    }
  }'
```

---

## Integration with OSINT and Threat Intelligence Modules

### Building the Intelligence Graph

When dark web indicators are discovered, they must flow into the broader threat intelligence graph. Here is how a single credential leak connects to the ontology system:

```bash
# Add the credential leak as an entity in the ontology
curl -X POST https://playseat.internal/api/v1/ontology/entities \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "entity_type_id": "01945000-0000-7000-8000-000000000009",
    "name": "CRED-LEAK-2026-0218-ACME-14K",
    "properties": {
      "leak_type": "credential_dump",
      "credential_count": 14237,
      "email_domain": "acmedefense.gov",
      "source_platform": "tor_marketplace",
      "first_seen": "2026-02-14T00:00:00Z",
      "password_types": {"cleartext": 3102, "sha256": 8423, "bcrypt": 2712},
      "admin_accounts_included": 47
    },
    "confidence": 0.94,
    "source": "credential_monitoring_feed"
  }'

# Link the leak to the threat actor
curl -X POST https://playseat.internal/api/v1/ontology/relationships \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "relationship_type_id": "01945100-0000-7000-8000-000000000005",
    "source_entity_id": "01946600-0000-7000-8000-000000000001",
    "target_entity_id": "01945200-0000-7000-8000-000000000005",
    "weight": 0.7,
    "confidence": 0.65,
    "properties": {
      "relationship_basis": "Infrastructure overlap between leak distribution and known APT-SYNTHETIC-BEAR C2",
      "analyst_note": "Moderate confidence - could be coincidental infrastructure sharing"
    }
  }'
```

### Building the OSINT Social Graph

Connect all dark web findings into a relationship graph:

```bash
# Build a relationship graph from all dark web findings
curl -X POST https://playseat.internal/api/v1/osint/graph/build \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "campaign_id": "01945000-0000-7000-8000-000000000100",
    "name": "Dark Web Exposure Graph - Acme Defense - Feb 2026",
    "sources": [
      "credential_monitoring_feed",
      "ransomware_leak_monitor",
      "paste_site_monitor",
      "iab_tracker"
    ],
    "time_range": {
      "start": "2026-01-01T00:00:00Z",
      "end": "2026-02-18T23:59:59Z"
    },
    "correlation_rules": [
      "email_domain_match",
      "infrastructure_overlap",
      "temporal_proximity",
      "shared_breach_source"
    ]
  }'
```

Response:

```json
{
  "id": "01946700-0000-7000-8000-000000000001",
  "campaign_id": "01945000-0000-7000-8000-000000000100",
  "name": "Dark Web Exposure Graph - Acme Defense - Feb 2026",
  "node_count": 47,
  "edge_count": 83,
  "cluster_count": 4,
  "clusters": [
    {
      "id": "cluster_1",
      "name": "Credential Leak Cluster",
      "nodes": 23,
      "description": "14K credential dump, connected paste sites, and associated broker listings"
    },
    {
      "id": "cluster_2",
      "name": "Supply Chain Cluster",
      "nodes": 11,
      "description": "TechSubCon ransomware incident, related infrastructure, shared data exposure"
    },
    {
      "id": "cluster_3",
      "name": "IAB Activity Cluster",
      "nodes": 8,
      "description": "Three IAB listings potentially targeting defense sector VPN infrastructure"
    },
    {
      "id": "cluster_4",
      "name": "Historical Breach Cluster",
      "nodes": 5,
      "description": "Legacy breaches (2024-2025) with credential reuse overlap"
    }
  ]
}
```

---

## Continuous Monitoring Dashboard Queries

### Daily Dark Web Intelligence Summary

```sql
-- Daily dark web intelligence summary for morning SOC briefing
SELECT
    'New credential leaks (24h)' AS metric,
    COUNT(*)::TEXT AS value
FROM osint_source_results
WHERE source_type = 'credential_dumps'
  AND collected_at > NOW() - INTERVAL '24 hours'

UNION ALL

SELECT
    'New ransomware posts mentioning sector',
    COUNT(*)::TEXT
FROM threat_intel_iocs
WHERE ioc_type = 'ransomware_post'
  AND metadata->>'sector' IN ('defense', 'government')
  AND created_at > NOW() - INTERVAL '24 hours'

UNION ALL

SELECT
    'New IAB listings (defense sector)',
    COUNT(*)::TEXT
FROM threat_intel_iocs
WHERE ioc_type = 'iab_listing'
  AND (metadata->>'sector' IN ('defense', 'government')
       OR value ILIKE '%defense%')
  AND created_at > NOW() - INTERVAL '24 hours'

UNION ALL

SELECT
    'Unacknowledged critical alerts',
    COUNT(*)::TEXT
FROM anomaly_events
WHERE anomaly_score = 'critical'
  AND category LIKE 'dark_web%'
  AND detected_at > NOW() - INTERVAL '7 days'
  AND NOT EXISTS (
    SELECT 1 FROM anomaly_events ae2
    WHERE ae2.entity_id = anomaly_events.entity_id
      AND ae2.anomaly_score = 'resolved'
      AND ae2.detected_at > anomaly_events.detected_at
  )

UNION ALL

SELECT
    'Feed health (active/total)',
    COUNT(*) FILTER (WHERE enabled = true)::TEXT || '/' || COUNT(*)::TEXT
FROM threat_intel_feeds;
```

---

## Lessons Learned

After eighteen months of operating dark web monitoring at scale, here is what I know:

1. **Speed is everything.** The window between credentials appearing on a dark web marketplace and someone trying to use them is shrinking. In 2024, the average was 72 hours. In 2026, we have seen it as low as 3 hours. Your monitoring pipeline needs to be faster than the buyers.

2. **Credential reuse is your biggest enemy.** Of the 14,000 credentials in our scenario, 3,847 were reused across personal and work accounts. The breach came from a third-party fitness app. Users reused their work passwords. You cannot monitor the dark web fast enough to compensate for password reuse — you need MFA everywhere.

3. **Supply chain monitoring is non-negotiable.** The ransomware post about TechSubCon contained Acme Defense contract documents, technical specifications, and employee records. Monitor your suppliers, not just yourself.

4. **Legal documentation protects you.** Document every monitoring action with legal basis, approval references, and method constraints. If your dark web monitoring program is ever questioned, the audit trail is your defense.

5. **Do not chase attribution too hard.** Spend your energy on containment, not blame. The attacker's nationality matters far less than whether your admin accounts still have unrotated passwords.

6. **False positives are expensive but necessary.** Our initial credential monitoring generated 340 false positives per week (test accounts, former employees, coincidental email addresses). We tuned it down to 12 per week, but the remaining 12 still require human review. Budget for that analyst time.

---

*Next chapter: The enemy within — when the threat does not come from outside your network but from the person sitting three desks away.*

---

© 2026 Playseat — All Rights Reserved | Proprietary and Confidential
