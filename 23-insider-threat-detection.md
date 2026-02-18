# Chapter 23: Insider Threat — The Mole Inside

> *"We were hunting them. But they were watching us hunt."*

---

**OPERATION STARLIGHT — T-minus 22 hours**
**Playseat Tactical Operations Center, undisclosed NATO facility**
**February 18, 2026 — 06:14 UTC**

---

I hadn't slept in thirty-one hours.

The dark web intelligence from Chapter 22 had confirmed what I'd feared: Clara Dubois was alive, held in the basement level of an abandoned hospital in the industrial quarter of Marseille, and PHANTOM MERCY knew we were coming. That last part was the problem. That last part was why I was staring at a behavioral analytics dashboard at six in the morning instead of finalizing the rescue plan.

Because someone on our team was feeding them information.

Clara had warned me. The last thing she'd said before she went dark — before she deliberately walked into PHANTOM MERCY's trap to access their command server and extract evidence — was: *"Don't trust INTERPOL Station Marseille."*

I'd taken it as operational caution. I was wrong. She'd meant it literally.

---

## The Anomaly That Started Everything

It was Marchetti who noticed it first. Not through intuition, though the man had more of that than anyone I'd worked with. Through Playseat.

At 04:47 UTC, our UEBA module flagged an anomalous access pattern on the investigation case files for PHANTOM MERCY. Someone with legitimate access to the system was doing things that didn't match their behavioral baseline. Small things. The kind of things you'd miss if you weren't running continuous behavioral analytics against every session.

I pulled up the alert.

```bash
# Pull the latest critical anomaly events — last 6 hours
curl -X GET "https://playseat.internal/api/v1/behavioral/anomalies/critical?hours=6" \
  -H "Authorization: Bearer ${TOKEN}"
```

Response:

```json
{
  "critical_anomalies": [
    {
      "id": "01950100-0000-7000-8000-000000000001",
      "entity_id": "01947000-0000-7000-8000-000000000042",
      "category": "data_access",
      "anomaly_score": "critical",
      "deviation": 6.8,
      "details": {
        "anomalies_detected": [
          {
            "factor": "case_file_access_frequency",
            "expected": "2-5 queries per shift",
            "observed": "47 queries in 90 minutes",
            "deviation_sigma": 6.8,
            "points": 35
          },
          {
            "factor": "access_scope",
            "expected": "Liaison-level clearance (summary views only)",
            "observed": "Accessed raw evidence vault, operational planning docs, source identities",
            "deviation_sigma": 8.2,
            "points": 40
          },
          {
            "factor": "export_pattern",
            "expected": "Zero exports in 90-day baseline",
            "observed": "3 PDF exports of operational timeline documents",
            "deviation_sigma": 12.0,
            "points": 25
          }
        ],
        "composite_score": 94,
        "risk_level": "critical"
      },
      "detected_at": "2026-02-18T04:47:00Z"
    }
  ]
}
```

Ninety-four. Out of a hundred.

Forty-seven queries in ninety minutes from an account whose baseline was two to five queries per *shift*. Three PDF exports from a user who had never exported a single document in three months on the system. And the worst part — the access scope. This person had been reading raw evidence vault entries. Operational planning documents. Source identities.

They were reading everything we had on PHANTOM MERCY. And they were copying it.

"Who is entity four-two?" I asked Marchetti. My voice was flat. Controlled. The kind of control you learn when the alternative is putting your fist through a monitor.

Marchetti was already pulling it up.

---

## Understanding UEBA: The System That Caught the Mole

Let me explain how we got here, because the technology matters. Playseat's User and Entity Behavior Analytics module is the reason we caught this at all. Without it, the mole would have continued operating until Clara was dead and the entire PHANTOM MERCY investigation was compromised.

The schema that powers everything. From migration `056_behavioral_analytics.sql`:

```sql
-- Sprint 51: User & Entity Behavior Analytics (UEBA)

CREATE TABLE IF NOT EXISTS behavior_baselines (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_id UUID NOT NULL,
    entity_type VARCHAR(50) NOT NULL,
    category VARCHAR(50) NOT NULL,
    baseline_data JSONB NOT NULL DEFAULT '{}',
    sample_count INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS anomaly_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    baseline_id UUID NOT NULL REFERENCES behavior_baselines(id),
    entity_id UUID NOT NULL,
    category VARCHAR(50) NOT NULL,
    anomaly_score VARCHAR(20) NOT NULL DEFAULT 'normal',
    deviation DOUBLE PRECISION NOT NULL DEFAULT 0.0,
    details JSONB NOT NULL DEFAULT '{}',
    detected_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS insider_threat_assessments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_id UUID NOT NULL,
    threat_level VARCHAR(20) NOT NULL DEFAULT 'none',
    risk_factors JSONB NOT NULL DEFAULT '[]',
    score DOUBLE PRECISION NOT NULL DEFAULT 0.0,
    assessed_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS session_risk_scores (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL,
    entity_id UUID NOT NULL,
    risk_score DOUBLE PRECISION NOT NULL DEFAULT 0.0,
    factors JSONB NOT NULL DEFAULT '[]',
    scored_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_behavior_baselines_entity ON behavior_baselines(entity_id);
CREATE INDEX IF NOT EXISTS idx_anomaly_events_entity ON anomaly_events(entity_id);
CREATE INDEX IF NOT EXISTS idx_anomaly_events_detected ON anomaly_events(detected_at);
CREATE INDEX IF NOT EXISTS idx_insider_threat_entity ON insider_threat_assessments(entity_id);
```

Every person with access to this investigation — every analyst, every liaison officer, every support staffer — has a behavioral baseline. Eight categories of behavior, tracked continuously, compared against ninety days of historical data.

Here's what those baselines look like when you build them:

```sql
-- Build login pattern baseline from 90 days of auth logs
-- This is what "normal" looks like for every user on the system

WITH login_history AS (
    SELECT
        ae.actor_id AS entity_id,
        EXTRACT(DOW FROM ae.created_at) AS day_of_week,
        EXTRACT(HOUR FROM ae.created_at) AS hour_of_day,
        ae.details->>'source_ip' AS source_ip,
        ae.details->>'device_type' AS device_type,
        ae.details->>'geo_country' AS geo_country,
        ae.details->>'auth_method' AS auth_method,
        ae.created_at
    FROM audit_events ae
    WHERE ae.event_type = 'auth_login_success'
      AND ae.created_at > NOW() - INTERVAL '90 days'
),
time_patterns AS (
    SELECT
        entity_id,
        MODE() WITHIN GROUP (ORDER BY hour_of_day) AS typical_login_hour,
        STDDEV(hour_of_day) AS login_hour_stddev,
        ARRAY_AGG(DISTINCT day_of_week ORDER BY day_of_week) AS active_days,
        COUNT(*)::DOUBLE PRECISION /
            EXTRACT(EPOCH FROM (MAX(created_at) - MIN(created_at))) * 86400
            AS avg_logins_per_day
    FROM login_history
    GROUP BY entity_id
),
location_patterns AS (
    SELECT
        entity_id,
        ARRAY_AGG(DISTINCT source_ip) AS known_source_ips,
        ARRAY_AGG(DISTINCT geo_country) AS known_countries,
        ARRAY_AGG(DISTINCT device_type) AS known_devices,
        COUNT(DISTINCT source_ip) AS unique_ip_count
    FROM login_history
    GROUP BY entity_id
)
UPDATE behavior_baselines bb
SET baseline_data = jsonb_build_object(
    'typical_login_hour', tp.typical_login_hour,
    'login_hour_stddev', tp.login_hour_stddev,
    'active_days', tp.active_days,
    'avg_logins_per_day', tp.avg_logins_per_day,
    'known_source_ips', lp.known_source_ips,
    'known_countries', lp.known_countries,
    'known_devices', lp.known_devices,
    'unique_ip_count', lp.unique_ip_count
),
    sample_count = (
        SELECT COUNT(*) FROM login_history lh
        WHERE lh.entity_id = bb.entity_id
    ),
    updated_at = NOW()
FROM time_patterns tp
JOIN location_patterns lp ON tp.entity_id = lp.entity_id
WHERE bb.entity_id = tp.entity_id
  AND bb.category = 'login_patterns';
```

The system doesn't care who you are. It doesn't care about your title or your agency affiliation or the flag on your badge. It cares about deviation from baseline. That's it. And when your deviation hits critical thresholds across multiple categories simultaneously, the system screams.

---

## Session Risk Scoring: How We Caught It in Real Time

**06:22 UTC**

Marchetti had the name. I didn't want to believe it.

"Duval," he said. "Jean-Marc Duval. INTERPOL Liaison, Station Marseille. Seconded to us eight weeks ago when we opened the PHANTOM MERCY case."

Clara's words echoed in my skull like a gunshot in a stairwell. *Don't trust INTERPOL Station Marseille.*

I ran the session risk score on Duval's current session:

```bash
# Score the current session risk for the suspect entity
curl -X POST https://playseat.internal/api/v1/behavioral/sessions/score \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "01950200-0000-7000-8000-000000000001",
    "entity_id": "01947000-0000-7000-8000-000000000042"
  }'
```

Response:

```json
{
  "id": "01950300-0000-7000-8000-000000000001",
  "session_id": "01950200-0000-7000-8000-000000000001",
  "entity_id": "01947000-0000-7000-8000-000000000042",
  "risk_score": 91.7,
  "factors": [
    {
      "factor": "after_hours_access",
      "weight": 2.0,
      "detail": "Active session at 04:30 UTC — outside baseline hours (08:00-18:00 CET)",
      "contribution": 12.3
    },
    {
      "factor": "data_access_velocity",
      "weight": 2.5,
      "detail": "47 case file queries in 90 minutes — baseline is 2-5 per 8-hour shift",
      "contribution": 28.4
    },
    {
      "factor": "access_scope_expansion",
      "weight": 3.0,
      "detail": "Accessed evidence vault (never accessed), ops planning (never accessed), source IDs (never accessed)",
      "contribution": 31.2
    },
    {
      "factor": "export_anomaly",
      "weight": 2.0,
      "detail": "3 PDF exports — zero baseline exports in 90 days",
      "contribution": 14.8
    },
    {
      "factor": "geo_anomaly",
      "weight": 1.5,
      "detail": "Session originating from VPN exit in Bucharest — baseline is Marseille and Lyon only",
      "contribution": 5.0
    }
  ],
  "scored_at": "2026-02-18T06:22:00Z"
}
```

Bucharest. The son of a bitch was logging in from Bucharest and reading everything we had on the operation to rescue Clara.

"He's online right now?" I asked.

"Active session. Started at 04:31." Marchetti's jaw was tight. "He's been in the evidence vault for the last forty minutes."

Forty minutes in the evidence vault. The vault that contained Clara's extraction plan. The vault that contained the coordinates for the rescue entry points. The vault that contained the thermal imaging analysis of the hospital building in Marseille.

If he'd already transmitted that to PHANTOM MERCY, Clara was dead.

---

## The Composite Risk Scoring Formula

Here's the algorithm that flagged Duval. It runs hourly against every monitored user, but for entities already in an active investigation workspace, it runs continuously — every five minutes.

```sql
-- Composite insider threat risk scoring
-- Continuous mode: runs every 5 minutes for active investigation members

WITH user_anomalies AS (
    SELECT
        ae.entity_id,
        ae.category,
        ae.anomaly_score,
        ae.deviation,
        ae.details,
        ae.detected_at,
        -- Recency weight: anomalies from the last hour score much higher
        EXP(-EXTRACT(EPOCH FROM (NOW() - ae.detected_at)) / 604800.0) AS recency_weight
    FROM anomaly_events ae
    WHERE ae.detected_at > NOW() - INTERVAL '90 days'
      AND ae.anomaly_score IN ('medium', 'high', 'critical')
),
category_scores AS (
    SELECT
        entity_id,
        category,
        SUM(
            ae.deviation *
            CASE ae.anomaly_score
                WHEN 'critical' THEN 4.0
                WHEN 'high' THEN 2.5
                WHEN 'medium' THEN 1.0
                ELSE 0.0
            END *
            ae.recency_weight
        ) AS category_score,
        COUNT(*) AS anomaly_count,
        MAX(ae.detected_at) AS last_anomaly
    FROM user_anomalies ae
    GROUP BY entity_id, category
),
composite_scores AS (
    SELECT
        entity_id,
        SUM(
            category_score *
            CASE category
                WHEN 'data_access' THEN 2.5      -- Data exfil weighted highest
                WHEN 'login_patterns' THEN 2.0    -- Unusual access patterns
                WHEN 'network_activity' THEN 1.8  -- Unusual network destinations
                WHEN 'privilege_usage' THEN 1.5   -- Privilege abuse
                WHEN 'email_behavior' THEN 1.3    -- Unusual email patterns
                WHEN 'physical_access' THEN 1.2   -- Physical access anomalies
                WHEN 'application_usage' THEN 1.0 -- App usage changes
                WHEN 'collaboration_patterns' THEN 0.8
                ELSE 1.0
            END
        ) AS raw_composite,
        COUNT(DISTINCT category) AS categories_affected,
        SUM(anomaly_count) AS total_anomalies,
        MAX(last_anomaly) AS most_recent_anomaly
    FROM category_scores
    GROUP BY entity_id
),
normalized AS (
    SELECT
        entity_id,
        raw_composite,
        -- Sigmoid normalization to 0-100
        100.0 / (1.0 + EXP(-(raw_composite - 50.0) / 15.0)) AS normalized_score,
        categories_affected,
        total_anomalies,
        most_recent_anomaly,
        CASE
            WHEN categories_affected >= 5 THEN 'critical'
            WHEN categories_affected >= 3 THEN 'high'
            WHEN categories_affected >= 2 THEN 'medium'
            ELSE 'low'
        END AS multi_category_indicator
    FROM composite_scores
)
SELECT
    n.entity_id,
    u.username,
    u.email,
    u.role,
    ROUND(n.normalized_score::NUMERIC, 1) AS risk_score,
    n.categories_affected,
    n.total_anomalies,
    n.most_recent_anomaly,
    n.multi_category_indicator,
    CASE
        WHEN n.normalized_score >= 85 THEN 'critical'
        WHEN n.normalized_score >= 65 THEN 'high'
        WHEN n.normalized_score >= 40 THEN 'medium'
        WHEN n.normalized_score >= 20 THEN 'low'
        ELSE 'none'
    END AS threat_level
FROM normalized n
JOIN users u ON n.entity_id = u.id
WHERE n.normalized_score >= 20
ORDER BY n.normalized_score DESC;
```

For Duval, the output was damning:

| username | role | risk_score | categories_affected | total_anomalies | threat_level |
|----------|------|-----------|---------------------|-----------------|-------------|
| jm.duval | interpol_liaison | 94.2 | 4 | 23 | critical |

Four categories affected. Twenty-three anomalies. Critical threat level. And here's the part that made my stomach drop — it wasn't just tonight. When I looked at the trend, Duval had been escalating for weeks.

---

## Baseline Deviation Analysis: The Pattern We Should Have Seen

**06:38 UTC**

I pulled the full anomaly timeline. Marchetti stood behind me, arms crossed, watching the screen like he was reading a sentencing document.

```bash
# Get the full insider threat assessment with historical context
curl -X GET "https://playseat.internal/api/v1/behavioral/insider-threats/assess?entity_id=01947000-0000-7000-8000-000000000042" \
  -H "Authorization: Bearer ${TOKEN}"
```

Response:

```json
{
  "id": "01950400-0000-7000-8000-000000000001",
  "entity_id": "01947000-0000-7000-8000-000000000042",
  "threat_level": "critical",
  "risk_factors": [
    {
      "factor": "sustained_scope_creep",
      "weight": 4.0,
      "detail": "Steady expansion of accessed case materials over 6 weeks — from summary views to raw evidence to operational planning",
      "first_observed": "2026-02-03T14:22:00Z"
    },
    {
      "factor": "after_hours_pattern",
      "weight": 3.0,
      "detail": "12 after-hours sessions in last 3 weeks — baseline was zero after-hours sessions in first 5 weeks",
      "first_observed": "2026-02-05T22:17:00Z"
    },
    {
      "factor": "export_escalation",
      "weight": 3.5,
      "detail": "First export Feb 8, then 3 more Feb 12, then 7 on Feb 15 — exponential pattern",
      "first_observed": "2026-02-08T16:40:00Z"
    },
    {
      "factor": "geo_inconsistency",
      "weight": 2.5,
      "detail": "VPN exits from Bucharest (4x), Sofia (2x), Istanbul (1x) — baseline is Marseille/Lyon only",
      "first_observed": "2026-02-10T03:11:00Z"
    },
    {
      "factor": "query_targeting",
      "weight": 4.5,
      "detail": "Search queries specifically targeting: rescue timeline, entry vectors, thermal coverage gaps, Clara Dubois extraction plan",
      "first_observed": "2026-02-17T23:55:00Z"
    }
  ],
  "score": 94.2,
  "assessed_at": "2026-02-18T06:38:00Z"
}
```

There it was. Written in data. The story of a man who'd started with casual access and ended up searching for Clara's extraction plan by name. The deviation was smooth, methodical, patient — exactly how a trained intelligence officer would do it.

I typed the query myself. I needed to see the full timeline with my own eyes.

```sql
-- Reconstruct Duval's complete behavioral timeline
-- Every action, every anomaly, every assessment — chronological

WITH behavioral_events AS (
    SELECT
        'anomaly' AS event_source,
        ae.id,
        ae.category,
        ae.anomaly_score AS severity,
        ae.deviation,
        ae.details,
        ae.detected_at AS event_time
    FROM anomaly_events ae
    WHERE ae.entity_id = '01947000-0000-7000-8000-000000000042'

    UNION ALL

    SELECT
        'assessment' AS event_source,
        ita.id,
        'insider_assessment' AS category,
        ita.threat_level AS severity,
        ita.score AS deviation,
        ita.risk_factors::JSONB AS details,
        ita.assessed_at AS event_time
    FROM insider_threat_assessments ita
    WHERE ita.entity_id = '01947000-0000-7000-8000-000000000042'

    UNION ALL

    SELECT
        'audit' AS event_source,
        ae.id,
        ae.event_type AS category,
        CASE
            WHEN ae.event_type IN ('classified_doc_access', 'evidence_vault_access') THEN 'high'
            WHEN ae.event_type IN ('case_file_export', 'file_download') THEN 'medium'
            ELSE 'info'
        END AS severity,
        0.0 AS deviation,
        ae.details,
        ae.created_at AS event_time
    FROM audit_events ae
    WHERE ae.actor_id = '01947000-0000-7000-8000-000000000042'
      AND ae.event_type IN (
          'auth_login_success', 'auth_login_failure',
          'classified_doc_access', 'evidence_vault_access',
          'case_file_export', 'file_download', 'file_upload',
          'search_query', 'ops_planning_access',
          'email_send_external', 'vpn_connect'
      )
)
SELECT
    event_time,
    event_source,
    category,
    severity,
    ROUND(deviation::NUMERIC, 1) AS deviation_or_score,
    details,
    CASE WHEN event_source = 'assessment'
         THEN deviation
         ELSE NULL
    END AS risk_score_at_time
FROM behavioral_events
WHERE event_time BETWEEN '2026-01-20' AND '2026-02-18'
ORDER BY event_time ASC;
```

The results painted a picture in timestamps. Each row a brushstroke. Each day a shade darker.

**Week 1 (Jan 20-26):** Normal. Duval accesses summary briefings, attends meetings, logs in from Marseille during business hours. Risk score: 8.

**Week 2 (Jan 27 - Feb 2):** First deviation. Duval starts querying case files outside the summary tier. Reads three full investigation reports. Risk score: 14.

**Week 3 (Feb 3-9):** Acceleration. After-hours access begins. First document export. Accesses evidence vault for the first time. Risk score: 31.

**Week 4 (Feb 10-16):** Escalation. VPN exits from Bucharest. Seven document exports. Queries targeting operational planning. Risk score: 67.

**Week 5 (Feb 17-18):** Tonight. Forty-seven queries. Three exports. Searches for "Clara Dubois extraction plan," "thermal coverage hospital sector 4," "entry vector B analysis." Risk score: 94.2.

I sat back in my chair. My hands were shaking.

He'd been watching us build the rescue plan. And transmitting everything to PHANTOM MERCY.

---

## Access Pattern Analysis: What Duval Was Stealing

**06:55 UTC**

I needed to know exactly what he'd taken. Not approximately. Not "several documents." Exactly. Because the answer would determine whether Operation STARLIGHT could still proceed or whether Clara was already dead.

```sql
-- Detailed access pattern analysis for the mole
-- What exactly was accessed, when, and what was exported

WITH current_period AS (
    SELECT
        EXTRACT(DOW FROM created_at) AS day_of_week,
        EXTRACT(HOUR FROM created_at) AS hour_of_day,
        COUNT(*) AS access_count,
        SUM(CASE WHEN details->>'action' = 'file_download' THEN 1 ELSE 0 END) AS downloads,
        SUM(CASE WHEN details->>'action' = 'case_file_export' THEN 1 ELSE 0 END) AS exports,
        SUM(COALESCE((details->>'bytes_transferred')::BIGINT, 0)) AS total_bytes,
        ARRAY_AGG(DISTINCT details->>'document_title') AS documents_accessed
    FROM audit_events
    WHERE actor_id = '01947000-0000-7000-8000-000000000042'
      AND created_at > NOW() - INTERVAL '7 days'
    GROUP BY EXTRACT(DOW FROM created_at), EXTRACT(HOUR FROM created_at)
),
baseline AS (
    SELECT
        (baseline_data->>'typical_login_hour')::INTEGER AS typical_hour,
        (baseline_data->>'login_hour_stddev')::DOUBLE PRECISION AS hour_stddev,
        baseline_data->'active_days' AS active_days,
        (baseline_data->>'avg_logins_per_day')::DOUBLE PRECISION AS avg_daily
    FROM behavior_baselines
    WHERE entity_id = '01947000-0000-7000-8000-000000000042'
      AND category = 'login_patterns'
)
SELECT
    cp.day_of_week,
    cp.hour_of_day,
    cp.access_count,
    cp.downloads,
    cp.exports,
    pg_size_pretty(cp.total_bytes) AS data_transferred,
    CASE
        WHEN cp.hour_of_day < 6 OR cp.hour_of_day > 22 THEN 'AFTER_HOURS'
        WHEN cp.day_of_week IN (0, 6) THEN 'WEEKEND'
        ELSE 'normal'
    END AS time_flag,
    CASE
        WHEN cp.total_bytes > 100 * 1024 * 1024 THEN 'HIGH_VOLUME'
        WHEN cp.exports > 0 THEN 'EXPORT_DETECTED'
        ELSE 'normal'
    END AS volume_flag,
    cp.documents_accessed
FROM current_period cp
CROSS JOIN baseline b
WHERE cp.access_count > 0
ORDER BY cp.day_of_week, cp.hour_of_day;
```

The results were surgical. In the last week alone, Duval had exported:

1. **STARLIGHT operational timeline** — the hour-by-hour rescue plan
2. **Thermal imaging analysis of Hôpital Saint-Lazare** — the abandoned hospital where Clara was held, including thermal coverage gaps
3. **Entry vector assessment** — three possible entry points with risk scoring
4. **Clara Dubois debriefing protocol** — what she would be asked upon extraction, including what evidence she'd gathered
5. **Team composition brief** — names, roles, and positions of the twelve-person rescue team
6. **Communications plan** — frequencies, encryption protocols, callsigns

Everything. He'd taken everything.

---

## Impossible Travel: Proving the VPN Was a Cover

**07:04 UTC**

Marchetti wanted physical proof. The behavioral analytics were damning but circumstantial in a court of law — an INTERPOL officer could claim he was "doing his job" by reviewing case files. We needed something harder.

I ran the impossible travel detection:

```sql
-- Detect impossible travel: Duval's login locations vs physical badge swipes

WITH ordered_logins AS (
    SELECT
        ae.actor_id,
        ae.details->>'source_ip' AS source_ip,
        ae.details->>'geo_country' AS country,
        ae.details->>'geo_city' AS city,
        (ae.details->>'geo_lat')::DOUBLE PRECISION AS lat,
        (ae.details->>'geo_lon')::DOUBLE PRECISION AS lon,
        ae.created_at,
        LAG(ae.details->>'geo_city') OVER (
            PARTITION BY ae.actor_id ORDER BY ae.created_at
        ) AS prev_city,
        LAG((ae.details->>'geo_lat')::DOUBLE PRECISION) OVER (
            PARTITION BY ae.actor_id ORDER BY ae.created_at
        ) AS prev_lat,
        LAG((ae.details->>'geo_lon')::DOUBLE PRECISION) OVER (
            PARTITION BY ae.actor_id ORDER BY ae.created_at
        ) AS prev_lon,
        LAG(ae.created_at) OVER (
            PARTITION BY ae.actor_id ORDER BY ae.created_at
        ) AS prev_login_at
    FROM audit_events ae
    WHERE ae.event_type = 'auth_login_success'
      AND ae.actor_id = '01947000-0000-7000-8000-000000000042'
      AND ae.created_at > NOW() - INTERVAL '30 days'
),
travel_analysis AS (
    SELECT
        actor_id,
        source_ip,
        city,
        country,
        created_at,
        prev_city,
        prev_login_at,
        -- Haversine distance in km
        2 * 6371 * ASIN(SQRT(
            POWER(SIN(RADIANS(lat - prev_lat) / 2), 2) +
            COS(RADIANS(prev_lat)) * COS(RADIANS(lat)) *
            POWER(SIN(RADIANS(lon - prev_lon) / 2), 2)
        )) AS distance_km,
        EXTRACT(EPOCH FROM (created_at - prev_login_at)) / 3600.0 AS hours_between,
        CASE
            WHEN EXTRACT(EPOCH FROM (created_at - prev_login_at)) > 0
            THEN (2 * 6371 * ASIN(SQRT(
                POWER(SIN(RADIANS(lat - prev_lat) / 2), 2) +
                COS(RADIANS(prev_lat)) * COS(RADIANS(lat)) *
                POWER(SIN(RADIANS(lon - prev_lon) / 2), 2)
            ))) / (EXTRACT(EPOCH FROM (created_at - prev_login_at)) / 3600.0)
            ELSE 999999
        END AS required_speed_kmh
    FROM ordered_logins
    WHERE prev_login_at IS NOT NULL
      AND city != prev_city
)
SELECT
    prev_city || ' -> ' || city AS travel_path,
    ROUND(distance_km::NUMERIC, 0) AS distance_km,
    ROUND(hours_between::NUMERIC, 1) AS hours_between_logins,
    ROUND(required_speed_kmh::NUMERIC, 0) AS required_speed_kmh,
    CASE
        WHEN required_speed_kmh > 1000 THEN 'IMPOSSIBLE_TRAVEL'
        WHEN required_speed_kmh > 500 THEN 'UNLIKELY_TRAVEL'
        ELSE 'possible'
    END AS verdict,
    created_at AS anomalous_login_at
FROM travel_analysis
WHERE required_speed_kmh > 500
ORDER BY required_speed_kmh DESC;
```

Three impossible travel events in the last two weeks:

| travel_path | distance_km | hours_between | speed_kmh | verdict |
|---|---|---|---|---|
| Marseille -> Bucharest | 1,528 | 0.3 | 5,093 | IMPOSSIBLE_TRAVEL |
| Lyon -> Sofia | 1,442 | 0.8 | 1,803 | IMPOSSIBLE_TRAVEL |
| Marseille -> Istanbul | 2,214 | 1.1 | 2,013 | IMPOSSIBLE_TRAVEL |

On February 15, Duval badged into the INTERPOL office in Marseille at 14:22 local time. Eighteen minutes later, he logged into Playseat from a VPN exit node in Bucharest. Unless Jean-Marc Duval could teleport, he was using remote VPN infrastructure to mask his connection while still physically present in France.

That wasn't carelessness. That was tradecraft. The VPN exits were in Eastern Europe — outside EU jurisdiction for quick data requests, inside enough infrastructure to have low latency. He'd chosen them deliberately.

"He's trained," Marchetti said, reading over my shoulder. Not a question.

"Or handled by someone who is."

---

## The Decision: Do Not Arrest — Feed False Intelligence

**07:18 UTC**

This was the hardest moment. Every instinct screamed to revoke Duval's access immediately. Lock his account. Have him arrested at his hotel. Hand him to the French DGSI and let them tear his life apart.

But arresting Duval wouldn't save Clara. It would do the opposite.

If PHANTOM MERCY lost their source of real-time intelligence on our investigation, they'd know we'd found the leak. And they'd assume we were about to move. They'd either kill Clara immediately to eliminate the witness, or relocate her to a secondary site we hadn't identified.

We needed Duval operational. But we needed him to operate on our terms.

Marchetti understood it before I finished the sentence. The man had spent twenty years in Italian military intelligence. He'd handled double agents before.

"We feed him," Marchetti said.

"We feed him."

This is how you run a counterintelligence operation through a platform like Playseat. You don't shut down the compromised channel. You control it.

```bash
# Step 1: Create a compartmented investigation workspace
# Only Marchetti and I have access — Duval's session inherits the
# modified case files without knowing the originals have been moved

curl -X POST https://playseat.internal/api/v1/behavioral/config \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "jurisdiction": "nato_counterintel",
    "compliance_framework": "COSMIC_TOP_SECRET",
    "settings": {
      "monitoring_scope": "full_session_recording",
      "session_recording": true,
      "real_time_alerting": true,
      "alert_recipients": ["marchetti", "analyst_primary"],
      "data_retention_days": 3650,
      "evidence_preservation": "continuous",
      "counterintel_mode": true,
      "modified_content_injection": true,
      "approval_authority": "operation_commander",
      "legal_review_required_threshold": "none_during_active_operation"
    }
  }'
```

We created what's called a "wilderness of mirrors." Duval's account remained active, but everything he could see was now a carefully constructed lie.

```bash
# Step 2: Log the counterintel operation in the evidence vault
# Every piece of disinformation we feed is documented for legal proceedings

curl -X POST https://playseat.internal/api/v1/behavioral/insider-threats/assess \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "entity_id": "01947000-0000-7000-8000-000000000042",
    "context": {
      "period": "2026-02-18T07:18:00Z/ongoing",
      "operation": "COUNTERINTEL_STARLIGHT_SHADOW",
      "status": "active_feed_operation",
      "modified_documents": [
        {
          "original": "STARLIGHT_operational_timeline_v3.pdf",
          "modified": "STARLIGHT_operational_timeline_v3_DECOY.pdf",
          "changes": "Entry time shifted from 05:30 to 22:00. Entry point changed from B to A. Thermal gap window inverted."
        },
        {
          "original": "thermal_analysis_saint_lazare.pdf",
          "modified": "thermal_analysis_saint_lazare_DECOY.pdf",
          "changes": "Thermal coverage gaps rotated 180 degrees. South wall shown as unwatched (actually most surveilled)."
        },
        {
          "original": "team_composition_brief.pdf",
          "modified": "team_composition_brief_DECOY.pdf",
          "changes": "Team size inflated from 12 to 24. Fake names added. Approach vector changed from east to west."
        }
      ],
      "objective": "Feed false operational details through compromised liaison to misdirect PHANTOM MERCY defensive posture"
    }
  }'
```

Three documents. Three lies. Each one designed to make PHANTOM MERCY look the wrong way at the wrong time.

The modified thermal analysis was Marchetti's idea. Brilliant in its cruelty. The real thermal imaging showed that the south-facing wall of the hospital had a twelve-minute gap in camera coverage between 05:18 and 05:30, caused by the rotation cycle of two overlapping PTZ cameras. We swapped it — showed the south wall as fully covered and the north wall as the gap.

If PHANTOM MERCY repositioned their guards based on our "leaked" intel, they'd reinforce the north wall. Which would weaken the south wall. Which was exactly where we'd be coming through.

---

## Continuous Monitoring: Watching the Mole Watch Us

**08:45 UTC**

Duval logged back in at 08:32 CET. Right on schedule. His regular morning session, connecting from his usual workstation at INTERPOL Marseille.

Except now everything he saw was our fabrication.

I watched his session in real time through the UEBA dashboard:

```bash
# Pull real-time session activity for the monitored entity
curl -X GET "https://playseat.internal/api/v1/behavioral/sessions/score?entity_id=01947000-0000-7000-8000-000000000042" \
  -H "Authorization: Bearer ${TOKEN}"
```

08:34 — He opened the STARLIGHT operational timeline. The decoy version. He spent eleven minutes reading it.

08:45 — He queried the thermal analysis. The modified one. Four minutes.

08:49 — He opened the team composition brief. The inflated version. Two minutes.

08:51 — He exported all three as PDFs.

```bash
# Real-time anomaly detection flagging the exports
curl -X POST https://playseat.internal/api/v1/behavioral/anomalies/detect \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "baseline_id": "01947100-0000-7000-8000-000000000042",
    "entity_id": "01947000-0000-7000-8000-000000000042",
    "category": "data_access",
    "deviation": 8.1,
    "details": {
      "event_type": "case_file_export",
      "documents_exported": [
        "STARLIGHT_operational_timeline_v3_DECOY.pdf",
        "thermal_analysis_saint_lazare_DECOY.pdf",
        "team_composition_brief_DECOY.pdf"
      ],
      "export_destination": "local_download",
      "total_bytes": 4718592,
      "composite_score": 96,
      "risk_level": "critical",
      "counterintel_note": "DECOY documents exported as planned — disinformation delivery confirmed"
    }
  }'
```

08:53 — He closed the session.

Eleven minutes of access. Three exports. And PHANTOM MERCY just received a rescue plan that would send them looking at the wrong entrance, at the wrong time, with the wrong number of operators to worry about.

I looked at Marchetti. He was almost smiling. Almost.

"He took the bait?"

"All three documents," I said. "He's going to send them. And when PHANTOM MERCY reads that we're coming through the north wall at 22:00 with a twenty-four-person team..."

"They'll put everything on the north side." Marchetti finished the sentence. "And we come through the south at 05:30 with twelve."

---

## The Full Behavioral Stats: What This System Can See

I pulled the system-wide stats. Partly to document the investigation. Partly because I needed to believe that Playseat could see what humans couldn't.

```bash
# Get full behavioral analytics system stats
curl -X GET https://playseat.internal/api/v1/behavioral/stats \
  -H "Authorization: Bearer ${TOKEN}"
```

Response:

```json
{
  "total_monitored_entities": 847,
  "active_baselines": 6776,
  "anomalies_last_24h": 23,
  "critical_anomalies_last_24h": 2,
  "high_risk_entities": 1,
  "threat_assessments_last_30d": 412,
  "categories": {
    "login_patterns": {"anomalies": 7, "avg_deviation": 1.8},
    "data_access": {"anomalies": 5, "avg_deviation": 4.1},
    "network_activity": {"anomalies": 4, "avg_deviation": 2.3},
    "privilege_usage": {"anomalies": 2, "avg_deviation": 1.9},
    "email_behavior": {"anomalies": 2, "avg_deviation": 1.2},
    "physical_access": {"anomalies": 1, "avg_deviation": 1.7},
    "application_usage": {"anomalies": 1, "avg_deviation": 0.8},
    "collaboration_patterns": {"anomalies": 1, "avg_deviation": 0.6}
  },
  "insider_threat_summary": {
    "critical_entities": 1,
    "high_entities": 0,
    "medium_entities": 3,
    "low_entities": 8,
    "counterintel_operations_active": 1
  }
}
```

One critical entity. One counterintel operation active. One mole who thought he was invisible, feeding poison to people who would kill the woman I loved.

---

## Evidence Preservation: Building the Case Against Duval

**09:30 UTC**

Even while we used Duval as a channel for disinformation, we needed to preserve everything for prosecution. When this was over — when Clara was safe — Jean-Marc Duval was going to face a military tribunal, and every piece of evidence needed to be legally airtight.

```sql
-- Preserve the complete insider threat evidence chain
-- BLAKE3 + SHA-256 dual hashing for integrity
-- Append-only — nothing can be deleted or modified

INSERT INTO evidence (
    id, finding_id, evidence_type, file_path,
    hash_blake3, hash_sha256, file_size_bytes,
    collected_by, collected_at, chain_of_custody
)
SELECT
    gen_random_uuid(),
    '01950500-0000-7000-8000-000000000001',
    'insider_threat_behavioral_evidence',
    '/evidence/2026/02/counterintel-starlight-shadow/duval-behavioral-timeline.json',
    encode(digest(details::TEXT, 'sha256'), 'hex'),
    encode(digest(details::TEXT, 'sha256'), 'hex'),
    LENGTH(details::TEXT),
    '01945000-0000-7000-8000-000000000001',
    NOW(),
    jsonb_build_array(
        jsonb_build_object(
            'action', 'automated_collection',
            'by', 'playseat_ueba_counterintel',
            'at', NOW(),
            'scope', 'full_behavioral_timeline_entity_042',
            'classification', 'COSMIC_TOP_SECRET',
            'legal_authority', 'NATO_SOFA_Article_VII'
        ),
        jsonb_build_object(
            'action', 'evidence_preservation',
            'by', 'marchetti_g',
            'at', NOW(),
            'verification', 'dual_hash_verified',
            'witness', 'analyst_primary'
        )
    )
FROM anomaly_events
WHERE entity_id = '01947000-0000-7000-8000-000000000042'
  AND detected_at BETWEEN '2026-01-20' AND '2026-02-18'
LIMIT 1;
```

Every anomaly event. Every session recording. Every document access. Every export. Every VPN connection from Bucharest and Sofia and Istanbul. All of it hashed, timestamped, and preserved in the evidence vault with an unbroken chain of custody.

Duval's defense attorney would argue that he was doing his job, that INTERPOL liaisons are supposed to review case files, that the system was too sensitive, that the after-hours access was just dedication.

The data would tell a different story. The data always tells a different story.

---

## Data Exfiltration Tracking: Where Did It Go?

**10:12 UTC**

The last piece of the puzzle: how was Duval getting the documents to PHANTOM MERCY? He wasn't stupid enough to email them from his INTERPOL account. He wasn't using USB drives — the workstations had USB ports disabled.

I ran the exfiltration detection query:

```sql
-- Track potential exfiltration channels for the mole
WITH user_transfers AS (
    SELECT
        ae.actor_id,
        ae.details->>'destination' AS destination,
        ae.details->>'destination_type' AS dest_type,
        ae.details->>'file_classification' AS classification,
        COALESCE((ae.details->>'bytes_transferred')::BIGINT, 0) AS bytes,
        ae.created_at,
        DATE_TRUNC('hour', ae.created_at) AS hour_bucket
    FROM audit_events ae
    WHERE ae.event_type IN ('file_download', 'file_copy', 'file_upload', 'print_job')
      AND ae.actor_id = '01947000-0000-7000-8000-000000000042'
      AND ae.created_at > NOW() - INTERVAL '30 days'
),
hourly_aggregates AS (
    SELECT
        actor_id,
        hour_bucket,
        dest_type,
        COUNT(*) AS transfer_count,
        SUM(bytes) AS total_bytes,
        COUNT(DISTINCT destination) AS unique_destinations,
        BOOL_OR(classification IN ('secret', 'top_secret', 'cosmic')) AS includes_classified
    FROM user_transfers
    GROUP BY actor_id, hour_bucket, dest_type
),
baseline_comparison AS (
    SELECT
        ha.actor_id,
        ha.hour_bucket,
        ha.dest_type,
        ha.transfer_count,
        ha.total_bytes,
        ha.unique_destinations,
        ha.includes_classified,
        bb.baseline_data,
        COALESCE((bb.baseline_data->>'avg_daily_bytes')::BIGINT, 0) AS baseline_daily_bytes,
        CASE
            WHEN COALESCE((bb.baseline_data->>'avg_daily_bytes')::BIGINT, 1) > 0
            THEN ha.total_bytes::DOUBLE PRECISION /
                 GREATEST((bb.baseline_data->>'avg_daily_bytes')::BIGINT, 1)
            ELSE 999.0
        END AS volume_deviation_factor
    FROM hourly_aggregates ha
    LEFT JOIN behavior_baselines bb ON ha.actor_id = bb.entity_id
        AND bb.category = 'data_access'
)
SELECT
    hour_bucket,
    dest_type,
    transfer_count,
    pg_size_pretty(total_bytes) AS data_volume,
    unique_destinations,
    includes_classified,
    ROUND(volume_deviation_factor::NUMERIC, 1) AS volume_multiplier,
    CASE
        WHEN includes_classified AND dest_type = 'local_download'
        THEN 'CRITICAL: Classified data downloaded locally'
        WHEN volume_deviation_factor > 10
        THEN 'HIGH: 10x+ volume deviation'
        WHEN includes_classified
        THEN 'HIGH: Classified data transfer'
        ELSE 'MEDIUM'
    END AS exfil_risk
FROM baseline_comparison
WHERE volume_deviation_factor > 1
   OR includes_classified
ORDER BY hour_bucket DESC;
```

Local downloads. Every time. He was downloading the PDFs to his local workstation — which meant he was then transferring them to a personal device. Probably a phone. Probably through a messaging app with end-to-end encryption.

We couldn't intercept the final handoff. Not without tipping him off. But it didn't matter. We knew the channel existed, we'd poisoned it with false intelligence, and we had the full behavioral trail for the tribunal.

---

## 11:00 UTC — The Moment of Quiet

Marchetti brought coffee. Real coffee, not the machine swill — he'd smuggled an espresso maker into the TOC on day one, because Italian special forces officers have priorities.

We sat in silence for three minutes. Outside the operations center, the rest of the investigation team was reviewing the (real) rescue plan, unaware that one of their colleagues was a traitor. Unaware that everything they were seeing was the genuine article while Duval saw carefully crafted fiction.

"How long have they had him?" I asked.

"Duval was posted to Marseille in 2024," Marchetti said. "PHANTOM MERCY's financial network runs through Marseille. It's possible he was compromised before the investigation even started."

"Clara knew."

"Clara knew." He took a sip. "She always knows more than she says."

That was true. Clara Dubois, DGSE deep-cover operative, cryptographer, the most infuriatingly brilliant person I'd ever met. She'd warned me about INTERPOL Marseille and I'd filed it as operational paranoia. I'd been wrong. She'd been precise.

She was always precise.

"The rescue still happens at 05:30 tomorrow," I said.

"The rescue still happens at 05:30 tomorrow," Marchetti confirmed. "And thanks to Monsieur Duval, PHANTOM MERCY thinks it's happening at 22:00 tonight through the north wall."

"Which means they'll be exhausted and out of position by the time we actually move."

Marchetti raised his espresso. "To the mole."

I didn't drink to that. I drank to Clara. Silently.

Twenty hours until STARLIGHT. Twenty hours until we'd know if the disinformation worked. Twenty hours until I'd either get her back or lose her forever.

The UEBA dashboard pulsed green. All eight behavioral categories monitored. Eight hundred and forty-seven entities baselined. One mole identified, contained, and weaponized against his own handlers.

We were hunting them. But they'd been watching us hunt. And now we were watching them watch, feeding them lies dressed as truth, and the whole thing had the sickening elegance of a hall of mirrors where nobody could tell which reflection was real.

Playseat could tell. The baselines don't lie. The deviations don't lie. The timestamps don't lie.

People lie. The data doesn't.

---

## What This Chapter Taught Me

1. **Alerts that are not triaged do not exist.** If we'd been running continuous monitoring from day one instead of hourly sweeps, we'd have caught Duval two weeks earlier. The system detected the anomalies. The configuration delayed the response. Build your SLAs tight: critical alerts get immediate human review. No exceptions.

2. **Baselines need time, but they start working faster than you think.** Duval's baseline was only six weeks old. It was enough. His normal behavior was so distinct from his espionage behavior that even a shallow baseline caught the deviation. Thirty days is minimum. But even two weeks of baseline can catch a bad actor who gets greedy.

3. **Multi-category correlation is the kill shot.** Duval didn't just have data access anomalies. He had login pattern anomalies, geo-location anomalies, export anomalies, and access scope anomalies — all simultaneously. Four categories. That's not a false positive. That's not dedication. That's espionage.

4. **Don't arrest the mole — use them.** The counterintelligence value of a known mole is vastly greater than the satisfaction of arresting them. Feed them false intelligence. Control the narrative. Let them think they're winning while you dismantle their operation from the inside.

5. **Legal frameworks must be documented before deployment.** Everything we did to Duval was logged, hashed, timestamped, and preserved. Every decoy document was catalogued. Every counterintelligence decision was recorded with authorization chain. When this goes to tribunal, the evidence will be a fortress.

6. **The human element breaks last and worst.** UEBA catches behavioral deviations. It doesn't catch motivation. Why did Duval turn? Money? Ideology? Coercion? Compromise? That question would be answered later, in an interrogation room. But the system that caught him didn't need to know why. It only needed to know that his behavior had changed. And it did.

---

*Next chapter: We switch sides — war-gaming the rescue operation through Playseat's red team simulation module. Every entry vector. Every risk score. Every second of the plan, tested against PHANTOM MERCY's defenses before a single operator moves.*

---

© 2026 Playseat — All Rights Reserved | Defensive Intelligence Through ADAPT
