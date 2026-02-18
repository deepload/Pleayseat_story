# Chapter 16: GEOINT Operations -- Tracking Clara's Ghost

**Playseat Advanced Field Manual -- Book 2**

---

> "Every person on Earth exists in physical space. They consume electricity.
> They emit signals. They leave footprints in the geography of their own
> survival. Find the footprint, and you find the person."

---

## 16.1 -- The Map on My Wall

**2026-02-05, 19:40 UTC. Building 9, Sub-level 2.**

There's a physical map of Marseille pinned to the wall behind my desk. Old
school. Paper. I printed it at 1:25,000 scale across four A0 sheets and
taped them together. Three red pins mark the satellite phone emission sources
the AI pipeline identified last night: Marseille 2nd arrondissement, near the
Vieux-Port. The 6th, up in Castellane. And the 15th, in the northern industrial
sprawl near L'Estaque.

I stare at those pins every time I look up from my monitors.

Somewhere behind one of those pins, Clara Dubois is either alive or dead. And
the only way to find out which is to turn those rough neighborhoods into
precise coordinates, calculate the distances between them, track the movement
patterns between them, and figure out which one is the holding site.

This is what GEOINT was built for.

I remember the exact moment geospatial intelligence clicked for me. It wasn't
a textbook. It was Clara, actually. We were sitting in her apartment in the
Marais, her laptop open to a map of the Aegean, and she was explaining how
she'd tracked a smuggling network by plotting the timing of fishing boat AIS
transponder shutoffs against satellite imagery of coastal transfer points.

"The sea is a map of intention," she said. "People think it's empty, but
every boat has a wake, every wake has a direction, and every direction tells
you what the captain is thinking."

I'd kissed her then, halfway through her explanation. She'd laughed, pushed me
away, and finished her thought. She always finished her thoughts.

Now I needed to use that same methodology -- her methodology -- to find her.

---

## 16.2 -- The Geo Data Model

Before I could start tracking, I needed to understand the data model. Everything
in Playseat's GEOINT module revolves around four core tables:

```sql
-- Core target: anything with a location
CREATE TABLE IF NOT EXISTS geo_targets (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name            TEXT NOT NULL,
    target_type     TEXT NOT NULL DEFAULT 'unknown',
    lat             DOUBLE PRECISION NOT NULL,
    lon             DOUBLE PRECISION NOT NULL,
    altitude_m      DOUBLE PRECISION,
    description     TEXT,
    metadata        JSONB DEFAULT '{}',
    status          TEXT NOT NULL DEFAULT 'active',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Position history: every observed location over time
CREATE TABLE IF NOT EXISTS geo_positions (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    target_id       UUID NOT NULL REFERENCES geo_targets(id),
    lat             DOUBLE PRECISION NOT NULL,
    lon             DOUBLE PRECISION NOT NULL,
    altitude_m      DOUBLE PRECISION,
    speed_kmh       DOUBLE PRECISION,
    bearing_deg     DOUBLE PRECISION,
    accuracy_m      DOUBLE PRECISION,
    source          TEXT,
    recorded_at     TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Geofences: alert perimeters
CREATE TABLE IF NOT EXISTS geo_geofences (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name            TEXT NOT NULL,
    fence_type      TEXT NOT NULL DEFAULT 'circle',
    center_lat      DOUBLE PRECISION NOT NULL,
    center_lon      DOUBLE PRECISION NOT NULL,
    radius_m        DOUBLE PRECISION NOT NULL,
    polygon         JSONB,
    alert_on_enter  BOOLEAN NOT NULL DEFAULT true,
    alert_on_exit   BOOLEAN NOT NULL DEFAULT true,
    status          TEXT NOT NULL DEFAULT 'active',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Geofence alerts: when a target crosses a perimeter
CREATE TABLE IF NOT EXISTS geo_geofence_alerts (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    geofence_id     UUID NOT NULL REFERENCES geo_geofences(id),
    target_id       UUID NOT NULL REFERENCES geo_targets(id),
    alert_type      TEXT NOT NULL,
    lat             DOUBLE PRECISION NOT NULL,
    lon             DOUBLE PRECISION NOT NULL,
    distance_m      DOUBLE PRECISION NOT NULL,
    acknowledged    BOOLEAN NOT NULL DEFAULT false,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

And the supporting tables for feeds and heatmap caching:

```sql
-- Data feeds: satellite, AIS, ADS-B, geolocation APIs
CREATE TABLE IF NOT EXISTS geo_feeds (
    id                   UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name                 TEXT NOT NULL,
    provider             TEXT NOT NULL,
    api_url              TEXT NOT NULL,
    feed_type            TEXT NOT NULL DEFAULT 'generic',
    update_interval_secs INTEGER NOT NULL DEFAULT 300,
    status               TEXT NOT NULL DEFAULT 'active',
    last_poll_at         TIMESTAMPTZ,
    created_at           TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Precomputed heatmap cells for fast rendering
CREATE TABLE IF NOT EXISTS geo_heatmap_cache (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    grid_lat        DOUBLE PRECISION NOT NULL,
    grid_lon        DOUBLE PRECISION NOT NULL,
    cell_size_deg   DOUBLE PRECISION NOT NULL DEFAULT 0.01,
    event_count     INTEGER NOT NULL DEFAULT 0,
    severity_sum    DOUBLE PRECISION NOT NULL DEFAULT 0.0,
    computed_at     TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

Targets are the things you track. Positions are where those things have been.
Geofences are the lines you draw around places you care about. Alerts tell you
when a target crosses a line. Feeds bring in the data. The heatmap cache holds
precomputed density grids for visualization.

Tonight, the targets weren't C2 servers or threat infrastructure. They were
three satellite phones somewhere in Marseille. And somewhere near one of them
was Clara.

---

## 16.3 -- Registering Clara's Ghost

I registered the three satphone emission sources as geo targets. My hands were
steady, but my heart wasn't.

```bash
# Marseille 2nd - Vieux-Port area emission source
curl -s -X POST http://localhost:3000/api/v1/geotrack/targets \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "PHANTOM-SITE-ALPHA",
    "target_type": "satphone_emission",
    "lat": 43.2965,
    "lon": 5.3698,
    "description": "Encrypted Thuraya emission source, Marseille 2nd arr. Near Vieux-Port. Burst pattern: 15-min intervals preceding PHANTOM MERCY cargo movements.",
    "metadata": {
      "emission_type": "thuraya_encrypted",
      "first_detected": "2026-01-22T08:45:00Z",
      "last_detected": "2026-02-05T16:30:00Z",
      "burst_count": 47,
      "confidence": 0.88,
      "association": "PHANTOM MERCY operational coordination"
    }
  }' | jq .
```

```json
{
  "id": "01954a00-bb01-7000-8000-000000000001",
  "name": "PHANTOM-SITE-ALPHA",
  "target_type": "satphone_emission",
  "lat": 43.2965,
  "lon": 5.3698,
  "altitude_m": null,
  "description": "Encrypted Thuraya emission source, Marseille 2nd arr...",
  "metadata": {
    "emission_type": "thuraya_encrypted",
    "first_detected": "2026-01-22T08:45:00Z",
    "last_detected": "2026-02-05T16:30:00Z",
    "burst_count": 47,
    "confidence": 0.88,
    "association": "PHANTOM MERCY operational coordination"
  },
  "status": "active",
  "created_at": "2026-02-05T19:45:22Z",
  "updated_at": "2026-02-05T19:45:22Z"
}
```

The remaining two:

```bash
# Marseille 6th - Castellane area
curl -s -X POST http://localhost:3000/api/v1/geotrack/targets \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "PHANTOM-SITE-BRAVO",
    "target_type": "satphone_emission",
    "lat": 43.2833,
    "lon": 5.3842,
    "description": "Encrypted Thuraya emission source, Marseille 6th arr. Castellane district. Lower burst frequency than ALPHA. Possibly secondary coordination.",
    "metadata": {
      "emission_type": "thuraya_encrypted",
      "first_detected": "2026-01-25T14:20:00Z",
      "last_detected": "2026-02-05T11:15:00Z",
      "burst_count": 23,
      "confidence": 0.76,
      "association": "PHANTOM MERCY secondary node"
    }
  }'

# Marseille 15th - L'Estaque industrial area
curl -s -X POST http://localhost:3000/api/v1/geotrack/targets \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "PHANTOM-SITE-CHARLIE",
    "target_type": "satphone_emission",
    "lat": 43.3614,
    "lon": 5.3147,
    "description": "Encrypted Thuraya emission source, Marseille 15th arr. Industrial zone near port facilities at L Estaque. Highest burst frequency. Likely primary operational hub.",
    "metadata": {
      "emission_type": "thuraya_encrypted",
      "first_detected": "2026-01-18T03:00:00Z",
      "last_detected": "2026-02-05T18:47:00Z",
      "burst_count": 89,
      "confidence": 0.91,
      "association": "PHANTOM MERCY primary operations"
    }
  }'
```

Three targets on the map. Three points in a city of 870,000 people. And
behind one of those points, the woman who'd spent six months unraveling a
trafficking network that was smart enough to use humanitarian aid as cover.

I stared at the metadata. CHARLIE had the most burst activity (89 vs 47 vs 23),
was first detected four days before the others, and had the highest confidence.
It was near port facilities. If PHANTOM MERCY was moving children through
Marseille's port logistics, CHARLIE was the most likely operational center.

But I couldn't afford to guess. I needed math.

---

## 16.4 -- The Haversine Formula: Measuring the Distance Between Hope and Fear

Every distance calculation in GEOINT uses the haversine formula. Standard
great-circle distance accounting for Earth's curvature. Here's the Rust
implementation:

```rust
/// Haversine distance in kilometers between two lat/lon points.
fn haversine_km(lat1: f64, lon1: f64, lat2: f64, lon2: f64) -> f64 {
    let r = 6371.0; // Earth radius in km
    let dlat = (lat2 - lat1).to_radians();
    let dlon = (lon2 - lon1).to_radians();
    let a = (dlat / 2.0).sin().powi(2)
        + lat1.to_radians().cos() * lat2.to_radians().cos()
        * (dlon / 2.0).sin().powi(2);
    let c = 2.0 * a.sqrt().asin();
    r * c
}

/// Haversine distance in meters between two lat/lon points.
fn haversine_m(lat1: f64, lon1: f64, lat2: f64, lon2: f64) -> f64 {
    haversine_km(lat1, lon1, lat2, lon2) * 1000.0
}
```

And the SQL equivalent for proximity queries:

```sql
-- Haversine distance in PostgreSQL
SELECT t.id, t.name, t.target_type, t.lat, t.lon,
  (6371.0 * acos(LEAST(1.0,
    cos(radians($1)) * cos(radians(t.lat)) * cos(radians(t.lon) - radians($2))
    + sin(radians($1)) * sin(radians(t.lat))
  ))) AS distance_km
FROM geo_targets t
WHERE t.status = 'active'
ORDER BY distance_km
LIMIT 50;
```

The `LEAST(1.0, ...)` wrapper prevents NaN from floating-point overshoot on
the `acos` argument. I've seen this bug in production systems -- it manifests
as occasional NULL distance results that corrupt downstream analytics. Clara
would've caught it. She caught everything.

I ran the proximity calculation from ALPHA's position:

```bash
curl -s -X POST http://localhost:3000/api/v1/geotrack/analysis/proximity \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"lat": 43.2965, "lon": 5.3698, "radius_km": 15}' | jq '.[] | {name, distance_km}'
```

```json
{"name": "PHANTOM-SITE-ALPHA", "distance_km": 0.0}
{"name": "PHANTOM-SITE-BRAVO", "distance_km": 1.72}
{"name": "PHANTOM-SITE-CHARLIE", "distance_km": 7.94}
```

ALPHA to BRAVO: 1.72 kilometers. Walking distance. You could move between them
in twenty minutes on foot through the narrow streets of old Marseille.

ALPHA to CHARLIE: 7.94 kilometers. A car ride. Ten minutes if traffic is light,
thirty in Marseille rush hour.

The triangle formed by the three points covered roughly 12 square kilometers
of urban Marseille. Not a huge area, but dense. Thousands of buildings.
Warehouses, apartments, commercial spaces, port facilities. Finding Clara in
that triangle would require more than just knowing the perimeter.

I needed to track how those emission sources moved over time.

---

## 16.5 -- Geofencing: Drawing Lines Around a Woman's Life

Geofences are perimeters that generate alerts when targets cross them. In
defensive intelligence, they're normally used for infrastructure protection
or investigation zone monitoring. Tonight I used them to draw invisible
boundaries around the places where Clara might be.

```bash
# Geofence around PHANTOM-SITE-ALPHA (Vieux-Port area)
curl -s -X POST http://localhost:3000/api/v1/geotrack/geofences \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "PHANTOM ALPHA Perimeter",
    "fence_type": "circle",
    "center_lat": 43.2965,
    "center_lon": 5.3698,
    "radius_m": 500,
    "alert_on_enter": true,
    "alert_on_exit": true
  }' | jq .
```

```json
{
  "id": "01954b00-cc01-7000-8000-000000000001",
  "name": "PHANTOM ALPHA Perimeter",
  "fence_type": "circle",
  "center_lat": 43.2965,
  "center_lon": 5.3698,
  "radius_m": 500.0,
  "polygon": null,
  "alert_on_enter": true,
  "alert_on_exit": true,
  "status": "active",
  "created_at": "2026-02-05T20:15:00Z"
}
```

500 meters. Two blocks in any direction. Tight enough to detect meaningful
movement, wide enough to account for cell tower and satphone geolocation error
margins.

I created fences for all three sites, then added one more: a master fence
encompassing the entire operational triangle.

```bash
# BRAVO perimeter
curl -s -X POST http://localhost:3000/api/v1/geotrack/geofences \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "PHANTOM BRAVO Perimeter",
    "fence_type": "circle",
    "center_lat": 43.2833,
    "center_lon": 5.3842,
    "radius_m": 500,
    "alert_on_enter": true,
    "alert_on_exit": true
  }'

# CHARLIE perimeter (larger -- industrial zone, less precise)
curl -s -X POST http://localhost:3000/api/v1/geotrack/geofences \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "PHANTOM CHARLIE Perimeter",
    "fence_type": "circle",
    "center_lat": 43.3614,
    "center_lon": 5.3147,
    "radius_m": 1000,
    "alert_on_enter": true,
    "alert_on_exit": true
  }'

# Master triangle fence
curl -s -X POST http://localhost:3000/api/v1/geotrack/geofences \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "PHANTOM MERCY Marseille Operations Zone",
    "fence_type": "circle",
    "center_lat": 43.3137,
    "center_lon": 5.3562,
    "radius_m": 8000,
    "alert_on_enter": true,
    "alert_on_exit": false
  }'
```

Four fences. Three tight, one wide. Any new signal source appearing in the
Marseille operations zone triggers an alert. Any emission source moving between
the tight fences triggers alerts at both ends -- exit from one, entry to another.

If they were moving Clara between sites, I'd see it.

---

## 16.6 -- Checking the Fences (Is She Inside?)

The geofence check endpoint evaluates whether a coordinate falls inside or
outside a fence:

```bash
# Check CHARLIE's latest emission against the master zone
curl -s -X POST \
  http://localhost:3000/api/v1/geotrack/geofences/01954b00-cc01-7000-8000-000000000004/check \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "lat": 43.3614,
    "lon": 5.3147,
    "target_id": "01954a00-bb01-7000-8000-000000000003"
  }' | jq .
```

```json
{
  "inside": true,
  "distance_m": 5842.3,
  "geofence_id": "01954b00-cc01-7000-8000-000000000004",
  "geofence_name": "PHANTOM MERCY Marseille Operations Zone"
}
```

Inside. 5.8 km from the zone center. All three sites within the master fence.

I checked for existing alerts:

```bash
# View alerts for the master zone
curl -s http://localhost:3000/api/v1/geotrack/geofences/01954b00-cc01-7000-8000-000000000004/alerts \
  -H "Authorization: Bearer $TOKEN" | jq '.[0]'
```

```json
{
  "id": "01954c00-dd01-7000-8000-000000000001",
  "geofence_id": "01954b00-cc01-7000-8000-000000000004",
  "target_id": "01954a00-bb01-7000-8000-000000000003",
  "alert_type": "enter",
  "lat": 43.3614,
  "lon": 5.3147,
  "distance_m": 5842.3,
  "acknowledged": false,
  "created_at": "2026-02-05T20:25:33Z"
}
```

The fences were alive. Now I needed to feed them position data over time and
watch the patterns emerge.

---

## 16.7 -- Position History: Clara's Phone Is Still Pinging

**21:15 UTC.**

Here's the thing that kept me going. The thing that made me believe she was
still alive.

The Mesh had been collecting emission data from all three sites for two weeks.
When I ingested that data into the GEOINT module, I found something that made
my throat close: one of the emission sources -- ALPHA, the Vieux-Port site --
showed a pattern that didn't match the other two. A secondary signal.
Intermittent. Much weaker. A phone that was being powered on briefly, emitting
for seconds, then killed.

Clara's encrypted phone. Had to be. The emission signature matched a Cryptophone
500 -- the model DGSE issued to deep-cover officers.

I set up a feed to ingest the historical emission data:

```bash
# Set up the SIGINT emission feed
FEED=$(curl -s -X POST http://localhost:3000/api/v1/geotrack/feeds \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Marseille SIGINT Emission Monitor",
    "provider": "Mesh-SIGINT",
    "api_url": "https://mesh.internal/v1/sigint/emissions",
    "feed_type": "sigint_emission",
    "update_interval_secs": 300
  }' | jq -r '.id')

echo "Feed ID: $FEED"

TARGET_ALPHA="01954a00-bb01-7000-8000-000000000001"

# Jan 22: First detection at ALPHA (Vieux-Port)
curl -s -X POST http://localhost:3000/api/v1/geotrack/feeds/ingest \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"feed_id\": \"$FEED\",
    \"target_id\": \"$TARGET_ALPHA\",
    \"lat\": 43.2965, \"lon\": 5.3698,
    \"speed_kmh\": 0, \"bearing_deg\": 0,
    \"accuracy_m\": 200, \"source\": \"sigint_emission\"
  }"

# Jan 26: Signal drifts slightly -- moved within the ALPHA zone
curl -s -X POST http://localhost:3000/api/v1/geotrack/feeds/ingest \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"feed_id\": \"$FEED\",
    \"target_id\": \"$TARGET_ALPHA\",
    \"lat\": 43.2951, \"lon\": 5.3712,
    \"speed_kmh\": 0, \"bearing_deg\": 45,
    \"accuracy_m\": 150, \"source\": \"sigint_emission\"
  }"

# Jan 30: Signal appears near BRAVO (Castellane) -- they moved her
curl -s -X POST http://localhost:3000/api/v1/geotrack/feeds/ingest \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"feed_id\": \"$FEED\",
    \"target_id\": \"$TARGET_ALPHA\",
    \"lat\": 43.2840, \"lon\": 5.3830,
    \"speed_kmh\": 25, \"bearing_deg\": 165,
    \"accuracy_m\": 300, \"source\": \"sigint_emission\"
  }"

# Feb 2: Back at ALPHA zone
curl -s -X POST http://localhost:3000/api/v1/geotrack/feeds/ingest \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"feed_id\": \"$FEED\",
    \"target_id\": \"$TARGET_ALPHA\",
    \"lat\": 43.2958, \"lon\": 5.3705,
    \"speed_kmh\": 0, \"bearing_deg\": 350,
    \"accuracy_m\": 180, \"source\": \"sigint_emission\"
  }"

# Feb 5: Most recent ping -- still at ALPHA, weaker signal
curl -s -X POST http://localhost:3000/api/v1/geotrack/feeds/ingest \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"feed_id\": \"$FEED\",
    \"target_id\": \"$TARGET_ALPHA\",
    \"lat\": 43.2960, \"lon\": 5.3701,
    \"speed_kmh\": 0, \"bearing_deg\": 0,
    \"accuracy_m\": 250, \"source\": \"sigint_emission\"
  }"
```

Each ingest call records the position in `geo_positions`, updates the target's
current lat/lon in `geo_targets`, and timestamps the feed's `last_poll_at`.

Now the trajectory:

```bash
curl -s http://localhost:3000/api/v1/geotrack/targets/$TARGET_ALPHA/trajectory \
  -H "Authorization: Bearer $TOKEN" | jq .
```

```json
[
  {"lat": 43.2965, "lon": 5.3698,  "recorded_at": "2026-01-22T08:45:00Z"},
  {"lat": 43.2951, "lon": 5.3712,  "recorded_at": "2026-01-26T14:20:00Z"},
  {"lat": 43.2840, "lon": 5.3830,  "recorded_at": "2026-01-30T03:10:00Z"},
  {"lat": 43.2958, "lon": 5.3705,  "recorded_at": "2026-02-02T19:45:00Z"},
  {"lat": 43.2960, "lon": 5.3701,  "recorded_at": "2026-02-05T16:30:00Z"}
]
```

I stared at those five points until my vision swam.

January 22 to 26: stationary at ALPHA. Slight drift -- 150 meters, within
one building or block.

January 30: jump to BRAVO. 1.72 kilometers south. They moved her. Middle of
the night -- 03:10 UTC. Under cover of darkness.

February 2: back at ALPHA. Three days at BRAVO, then returned.

February 5: still at ALPHA. Signal weakening.

She wasn't running. She wasn't evading. She was being *moved*. Between sites.
On someone else's schedule. In the middle of the night.

Clara Dubois wasn't hiding. She was being held.

---

## 16.8 -- Movement Pattern Analysis: Reading the Captors' Rhythm

The trajectory gave me raw data. The movement patterns endpoint gave me the
analytics that would break the case open:

```bash
curl -s http://localhost:3000/api/v1/geotrack/analysis/movement/$TARGET_ALPHA \
  -H "Authorization: Bearer $TOKEN" | jq .
```

```json
{
  "positions": [
    {"lat": 43.2960, "lon": 5.3701, "speed_kmh": 0.0,  "bearing_deg": 0.0,   "recorded_at": "2026-02-05T16:30:00Z"},
    {"lat": 43.2958, "lon": 5.3705, "speed_kmh": 0.0,  "bearing_deg": 350.0, "recorded_at": "2026-02-02T19:45:00Z"},
    {"lat": 43.2840, "lon": 5.3830, "speed_kmh": 25.0, "bearing_deg": 165.0, "recorded_at": "2026-01-30T03:10:00Z"},
    {"lat": 43.2951, "lon": 5.3712, "speed_kmh": 0.0,  "bearing_deg": 45.0,  "recorded_at": "2026-01-26T14:20:00Z"},
    {"lat": 43.2965, "lon": 5.3698, "speed_kmh": 0.0,  "bearing_deg": 0.0,   "recorded_at": "2026-01-22T08:45:00Z"}
  ],
  "avg_speed_kmh": 5.0,
  "max_speed_kmh": 25.0,
  "predominant_bearing": 112.0,
  "total_distance_km": 3.58
}
```

Total distance: 3.58 km over two weeks. Not a woman on the run. A woman
confined to a small area with occasional transfers.

Max speed: 25 km/h. Urban vehicle speed. Not highway -- city streets.

Predominant bearing: 112 degrees. Southeast. The direction from ALPHA to BRAVO.

Here's how the server computes it:

```rust
async fn movement_patterns(
    State(state): State<AppState>,
    Extension(_auth): Extension<AuthContext>,
    Path(id): Path<Uuid>,
) -> Result<Json<MovementPattern>, (StatusCode, String)> {
    let rows = sqlx::query_as::<_, MovementRow>(
        "SELECT lat, lon, speed_kmh, bearing_deg, recorded_at \
         FROM geo_positions WHERE target_id = $1 ORDER BY recorded_at DESC LIMIT 50"
    )
    .bind(id)
    .fetch_all(&state.db)
    .await
    .map_err(|e| (StatusCode::INTERNAL_SERVER_ERROR, format!("db error: {e}")))?;

    if rows.is_empty() {
        return Err((StatusCode::NOT_FOUND, "no position data".to_string()));
    }

    let positions: Vec<MovementPoint> = rows.iter().map(|r| MovementPoint {
        lat: r.lat,
        lon: r.lon,
        speed_kmh: r.speed_kmh.unwrap_or(0.0),
        bearing_deg: r.bearing_deg.unwrap_or(0.0),
        recorded_at: r.recorded_at,
    }).collect();

    let speeds: Vec<f64> = positions.iter().map(|p| p.speed_kmh).collect();
    let avg_speed = speeds.iter().sum::<f64>() / speeds.len() as f64;
    let max_speed = speeds.iter().cloned().fold(0.0_f64, f64::max);

    let bearings: Vec<f64> = positions.iter()
        .map(|p| p.bearing_deg)
        .filter(|b| *b > 0.0)
        .collect();
    let predominant_bearing = if bearings.is_empty() {
        0.0
    } else {
        bearings.iter().sum::<f64>() / bearings.len() as f64
    };

    // Total distance by summing haversine between consecutive points
    let mut total_distance_km = 0.0;
    for i in 1..positions.len() {
        total_distance_km += haversine_km(
            positions[i - 1].lat, positions[i - 1].lon,
            positions[i].lat, positions[i].lon,
        );
    }

    Ok(Json(MovementPattern {
        positions, avg_speed_kmh: avg_speed,
        max_speed_kmh: max_speed, predominant_bearing, total_distance_km,
    }))
}
```

The movement pattern told a story. A grim one.

Clara was being held primarily at the ALPHA site near the Vieux-Port. They'd
moved her once to BRAVO -- Castellane -- stayed three days, then brought her
back. The nighttime transfer and the vehicle speed suggested routine
operational security, not a panicked relocation. They had a process. A schedule.

Which meant she was an asset to them, not a liability. They were keeping her
alive because she had something they wanted. Her investigation data. Her
DGSE contacts. Her knowledge of how much the outside world knew about
PHANTOM MERCY.

As long as she was useful, she was alive.

---

## 16.9 -- Co-Travel Analysis: Finding the Captors' Pattern

**22:30 UTC.**

Co-travel analysis is one of the most powerful techniques in GEOINT. If two
targets consistently appear in the same area at the same time, they're likely
related -- even without a direct network connection. I ran co-travel between
all three PHANTOM sites:

```bash
# Co-travel between ALPHA and CHARLIE
curl -s -X POST http://localhost:3000/api/v1/geotrack/analysis/co-travel \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "target_ids": [
      "01954a00-bb01-7000-8000-000000000001",
      "01954a00-bb01-7000-8000-000000000003"
    ],
    "time_window_mins": 10080,
    "distance_threshold_km": 10.0
  }' | jq .
```

```json
[
  {
    "target_a": "01954a00-bb01-7000-8000-000000000001",
    "target_b": "01954a00-bb01-7000-8000-000000000003",
    "proximity_events": 12,
    "avg_distance_km": 7.94
  }
]
```

12 proximity events between ALPHA and CHARLIE. They're consistently within 8
km of each other -- which makes sense, they're both in Marseille. But the
timing was what mattered:

```rust
for pa in &positions_a {
    for pb in &positions_b {
        let time_diff = (pa.recorded_at - pb.recorded_at)
            .num_seconds().unsigned_abs();
        if time_diff <= 300 {  // Within 5 minutes of each other
            let dist = haversine_km(pa.lat, pa.lon, pb.lat, pb.lon);
            if dist <= distance_threshold {
                proximity_events += 1;
                total_distance += dist;
            }
        }
    }
}
```

The co-travel data showed that ALPHA and CHARLIE emitted within 5 minutes of
each other 12 times. ALPHA and BRAVO: 8 times. BRAVO and CHARLIE: only 3 times.

ALPHA and CHARLIE were the most tightly coordinated. The ALPHA site (where
Clara's signal was) and the CHARLIE site (the industrial zone near port
facilities) had the strongest operational relationship.

This meant the people at CHARLIE -- the operational hub -- were in regular
communication with whoever was holding Clara at ALPHA. They were coordinating.
Moving her when they needed to. Checking in regularly.

BRAVO was secondary. A backup location. A safe house, maybe.

---

## 16.10 -- The Heatmap: Where PHANTOM MERCY Breathes

The heatmap shows where activity concentrates over time. I generated one for
the full two-week window:

```bash
curl -s http://localhost:3000/api/v1/geotrack/analysis/heatmap \
  -H "Authorization: Bearer $TOKEN" | jq '.[0:3]'
```

```json
[
  {
    "id": "01955000-ee01-7000-8000-000000000001",
    "grid_lat": 43.36,
    "grid_lon": 5.31,
    "cell_size_deg": 0.01,
    "event_count": 89,
    "severity_sum": 356.0,
    "computed_at": "2026-02-05T22:00:00Z"
  },
  {
    "id": "01955000-ee01-7000-8000-000000000002",
    "grid_lat": 43.30,
    "grid_lon": 5.37,
    "cell_size_deg": 0.01,
    "event_count": 47,
    "severity_sum": 188.0,
    "computed_at": "2026-02-05T22:00:00Z"
  },
  {
    "id": "01955000-ee01-7000-8000-000000000003",
    "grid_lat": 43.28,
    "grid_lon": 5.38,
    "cell_size_deg": 0.01,
    "event_count": 23,
    "severity_sum": 69.0,
    "computed_at": "2026-02-05T22:00:00Z"
  }
]
```

CHARLIE: 89 events, severity sum 356. Burning hot. The industrial zone is the
primary operational hub.

ALPHA: 47 events, severity sum 188. Steady activity. The holding site.

BRAVO: 23 events, severity sum 69. Cooler. The backup.

The heatmap cache is generated by this SQL aggregation:

```sql
-- Regenerate heatmap cache from current position data
INSERT INTO geo_heatmap_cache (id, grid_lat, grid_lon, cell_size_deg, event_count, severity_sum, computed_at)
SELECT
    gen_random_uuid(),
    ROUND(CAST(p.lat AS numeric), 2) AS grid_lat,
    ROUND(CAST(p.lon AS numeric), 2) AS grid_lon,
    0.01 AS cell_size_deg,
    COUNT(*) AS event_count,
    COALESCE(SUM(
        CASE
            WHEN p.speed_kmh > 100 THEN 5.0
            WHEN p.speed_kmh > 50 THEN 3.0
            WHEN p.speed_kmh > 10 THEN 2.0
            ELSE 1.0
        END
    ), 0) AS severity_sum,
    NOW() AS computed_at
FROM geo_positions p
WHERE p.recorded_at >= NOW() - INTERVAL '30 days'
GROUP BY grid_lat, grid_lon
ON CONFLICT DO NOTHING;
```

On my paper map, I updated the red pins. Added heat zones with colored
markers. Red for CHARLIE. Orange for ALPHA. Yellow for BRAVO. The triangle
of PHANTOM MERCY's Marseille operations, rendered in the colors of fire.

Clara's last known position glowed orange in the center of it all.

---

## 16.11 -- Predictive Location: Where They'll Move Her Next

**23:00 UTC.**

The predict endpoint uses linear extrapolation from the most recent positions
to estimate where a target is headed. I wasn't predicting where Clara would
*go* -- she wasn't going anywhere of her own volition. I was predicting where
her captors would *take* her.

```bash
curl -s http://localhost:3000/api/v1/geotrack/analysis/predict/$TARGET_ALPHA \
  -H "Authorization: Bearer $TOKEN" | jq .
```

```json
{
  "target_id": "01954a00-bb01-7000-8000-000000000001",
  "predicted_lat": 43.2962,
  "predicted_lon": 5.3697,
  "confidence": 0.6,
  "based_on_positions": 3,
  "predicted_at": "2026-02-05T23:00:00Z"
}
```

Predicted position: 43.2962, 5.3697. Essentially unchanged from the current
ALPHA location. The model was saying: she's staying put.

The confidence was 0.6 -- moderate. Higher than I expected for a prediction
model, which means the pattern is consistent enough for the algorithm to trust:

```rust
// Linear extrapolation from the most recent two points
let latest = &rows[0];
let prev = &rows[1];

let dt_secs = (latest.recorded_at - prev.recorded_at).num_seconds() as f64;
if dt_secs > 0.0 {
    let dlat = latest.lat - prev.lat;
    let dlon = latest.lon - prev.lon;

    // Extrapolate by the same time delta
    let pred_lat = latest.lat + dlat;
    let pred_lon = latest.lon + dlon;

    // Confidence decreases with fewer data points and larger time gaps
    let base_confidence = if rows.len() >= 3 { 0.7 } else { 0.5 };
    let time_penalty = (dt_secs / 3600.0).min(1.0) * 0.3;
    let conf = (base_confidence - time_penalty).max(0.1);
}
```

Linear extrapolation is a blunt instrument. It works when movement is
consistent. For a captive being held at a primary location with occasional
transfers, the prediction was saying: expect her to remain at ALPHA.

That was good. If she was stationary, we could plan around a fixed target.

But I needed to consider the three scenarios the data supported:

1. **She's at ALPHA.** Most likely. Most recent signals. Highest time-on-station.
2. **She's at BRAVO.** Possible. They moved her there once already. Could do it
   again.
3. **She's at CHARLIE.** Less likely as a holding site -- it's an industrial
   zone near port facilities, more suited to operations than detention. But
   if they needed to move her for interrogation or handoff...

I needed to build a mission plan that covered all three.

---

## 16.12 -- Feed Management: Keeping the Eyes Open

In production, you don't manually ingest position data. You configure feeds
that poll and ingest automatically. I set up everything I could:

```bash
# List active feeds
curl -s http://localhost:3000/api/v1/geotrack/feeds \
  -H "Authorization: Bearer $TOKEN" | jq '.[] | {name, provider, status, last_poll_at}'
```

```json
{"name": "Marseille SIGINT Emission Monitor", "provider": "Mesh-SIGINT", "status": "active", "last_poll_at": "2026-02-05T23:00:00Z"}
```

I added more feeds. Every data source I could tap for Marseille coverage:

```bash
# AIS maritime feed for port activity
curl -s -X POST http://localhost:3000/api/v1/geotrack/feeds \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Marseille AIS Port Monitor",
    "provider": "MarineTraffic",
    "api_url": "https://maritime.internal/v1/positions",
    "feed_type": "ais",
    "update_interval_secs": 120
  }'

# Cell tower geolocation feed
curl -s -X POST http://localhost:3000/api/v1/geotrack/feeds \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Marseille Cell Tower Triangulation",
    "provider": "Mesh-SIGINT",
    "api_url": "https://mesh.internal/v1/celltower/triangulate",
    "feed_type": "celltower_geoloc",
    "update_interval_secs": 300
  }'

# Traffic camera pattern feed (via Mesh partner)
curl -s -X POST http://localhost:3000/api/v1/geotrack/feeds \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Marseille Traffic Pattern Analysis",
    "provider": "DGSE-Liaison",
    "api_url": "https://dgse-mesh.internal/v1/traffic/patterns",
    "feed_type": "traffic_analysis",
    "update_interval_secs": 600
  }'
```

Three new feeds. AIS data would tell me about ship movements at the port near
CHARLIE. Cell tower data would give me additional triangulation on the phone
signals. Traffic camera patterns might catch the vehicle used for nighttime
transfers between ALPHA and BRAVO.

Every feed ran on its own polling interval. Every data point fed into the
position history. Every movement triggered a geofence check. I was building a
surveillance net over Marseille using nothing but signals intelligence and math.

---

## 16.13 -- Integration with the Mission Board

**23:45 UTC.**

GEOINT doesn't exist in isolation. I pinned everything to the mission board
I was building for what was starting to take shape as a rescue operation:

```bash
# Pin the geo analysis to the mission board
curl -s -X POST http://localhost:3000/api/v1/collab/workspaces/$BOARD_ID/pins \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "entity_id": "01954a00-bb01-7000-8000-000000000001",
    "pin_type": "geo_target",
    "title": "Clara Signal: PHANTOM-SITE-ALPHA (Primary Holding)",
    "content": "Encrypted Cryptophone 500 signal intermittently detected at 43.2960, 5.3701 (Marseille 2nd arr, Vieux-Port area). Pattern: ALPHA is primary holding site. One transfer to BRAVO Jan 30, returned Feb 2. Signal weakening but still active as of Feb 5 16:30 UTC. Movement pattern consistent with captive being held and occasionally relocated.",
    "position_x": 400,
    "position_y": 250,
    "color": "#ef4444"
  }'
```

That pin. "Primary Holding." I typed those words and sat with them. This wasn't
an abstract intelligence problem. This was Clara. In a building. In Marseille.
Being held by people who trafficked children.

---

## 16.14 -- The Realization

**2026-02-06, 00:12 UTC.**

I went back to the movement data one more time. Looked at the timing of the
single transfer from ALPHA to BRAVO.

January 30. 03:10 UTC.

I cross-referenced with the AI pipeline findings. January 30 was the date of
a Fondation Lumiere wire transfer -- EUR 127,000 to Nicosia. And the encrypted
satphone burst from CHARLIE at 02:55 UTC -- fifteen minutes before Clara's
signal moved.

The operational chain:

- 02:55 -- CHARLIE (operational hub) sends encrypted coordination signal
- 03:10 -- Clara's phone signal moves from ALPHA to BRAVO
- 03:30 -- Fondation Lumiere initiates wire transfer

They moved Clara to BRAVO, then sent the payment. She was being moved as part
of the financial operation. Her captors were PHANTOM MERCY's logistics team.
The same people moving money and children were moving her.

The realization hit me like a fist in the sternum.

She wasn't just a prisoner. She was *inventory*. An asset to be managed on the
same schedule as the trafficking operations.

I leaned back in my chair and stared at the ceiling for a long time. Then I
leaned forward and started planning.

---

## 16.15 -- Operational Lessons

After using the GEOINT module through this investigation -- through the most
personally devastating investigation of my career -- here are the patterns
that matter:

**Distance thresholds depend on context.** For geolocated IP addresses, 50 km
is "same city." For satphone emissions in an urban area, 500 meters is the
meaningful threshold. Always calibrate geofence radii to the type of data
you're working with.

**Movement speed reveals intent.** A signal that moves at 25 km/h at 03:00
in a city is a car on empty streets. A signal that stays stationary for days
is confinement. Speed isn't just a number -- it's a narrative.

**Heatmaps decay.** Always filter by time window. The last 14 days told me
a different story than the last 30 would. PHANTOM MERCY's operational tempo
was recent and accelerating, and I needed current data, not historical noise.

**Co-travel is operational linkage.** When ALPHA and CHARLIE emit within 5
minutes of each other 12 times, that's not coincidence. That's a communication
protocol. Co-travel in urban SIGINT means coordination.

**The haversine formula assumes a sphere.** Earth is an oblate spheroid. For
distances under 10 km in an urban environment, the error is negligible. For
intercontinental calculations, it can be off by up to 0.3%. For this
investigation, with targets less than 8 km apart, the math was precise enough.

**Prediction models are blunt instruments for captive scenarios.** Linear
extrapolation works for targets making deliberate movement decisions. For
someone being held and moved by captors, the prediction is really predicting
the captor's behavior, which is less linear and more operational. Pair
predictions with timing analysis of the operational chain.

GEOINT is a force multiplier. It doesn't replace SIGINT or financial analysis.
But when you combine geographic awareness with those disciplines, you see
patterns that would remain invisible in any single domain. The timing chain
between CHARLIE's signal, Clara's movement, and the wire transfer? No single
data source revealed that. It took geographic co-location and temporal
correlation working together.

Three points on a map. One woman's life. And a machine that was getting better
every hour at tracking the invisible lines between them.

Tomorrow I'd take the GEOINT data, the AI pipeline results, and the financial
intelligence and turn them into a mission plan. Operation STARLIGHT. The
operation to bring Clara home.

Tonight, I just stared at the three red pins on my wall and tried not to think
about the signal getting weaker.

---

*Next chapter: Mission Planning -- Operation STARLIGHT*

---

`© 2026 Playseat — All Rights Reserved | Defensive Intelligence Through ADAPT`
