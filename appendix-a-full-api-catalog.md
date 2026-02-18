# Appendix A -- Full API Catalog

## Complete Endpoint Reference for Playseat

> 212 API routes across 30+ modules. Every endpoint authenticated via JWT (except auth endpoints themselves).
> All requests require `Authorization: Bearer <token>` unless noted otherwise.
> Base URL: `http://localhost:3000` (development) or your deployed instance.

I built this catalog by reading every route file in `crates/svc-api/src/routes/`. If it compiles, it is here.

---

## Authentication

Authentication endpoints issue and refresh JWT tokens. These are the only unauthenticated endpoints in the platform.

### POST /auth/login

Authenticate a user and receive access + refresh tokens.

```bash
curl -X POST http://localhost:3000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "changeme"}'
```

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "expires_in": 900
}
```

### POST /auth/refresh

Exchange a refresh token for a new access token pair.

```bash
curl -X POST http://localhost:3000/auth/refresh \
  -H "Content-Type: application/json" \
  -d '{"refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."}'
```

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "expires_in": 900
}
```

---

## Health

### GET /health

System health check. Returns database connectivity status.

```bash
curl http://localhost:3000/health
```

```json
{
  "status": "healthy",
  "database": "connected",
  "version": "0.2.0",
  "uptime_secs": 3421
}
```

---

## ADAPT Core -- Adaptive Defense & Posture Testing

The ADAPT engine is the heart of Playseat. Five phases: Discover, Correlate, Validate, Fortify, Prove.

### Cycles

#### POST /api/v1/adapt/cycles

Create a new ADAPT cycle for a scope.

```bash
curl -X POST http://localhost:3000/api/v1/adapt/cycles \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"scope_id": "550e8400-e29b-41d4-a716-446655440000"}'
```

```json
{
  "id": "6ba7b810-9dad-11d1-80b4-00c04fd430c8",
  "cycle_number": 1,
  "scope_id": "550e8400-e29b-41d4-a716-446655440000",
  "phase": "discover",
  "status": "running",
  "started_at": "2026-02-17T14:30:00Z"
}
```

#### GET /api/v1/adapt/cycles

List all ADAPT cycles.

```bash
curl http://localhost:3000/api/v1/adapt/cycles \
  -H "Authorization: Bearer $TOKEN"
```

```json
{
  "cycles": [
    {
      "id": "6ba7b810-9dad-11d1-80b4-00c04fd430c8",
      "cycle_number": 1,
      "phase": "validate",
      "status": "running",
      "started_at": "2026-02-17T14:30:00Z"
    }
  ],
  "total": 1
}
```

#### GET /api/v1/adapt/cycles/current

Get the currently running cycle.

```bash
curl http://localhost:3000/api/v1/adapt/cycles/current \
  -H "Authorization: Bearer $TOKEN"
```

#### GET /api/v1/adapt/cycles/{id}

Get a specific cycle by ID.

```bash
curl http://localhost:3000/api/v1/adapt/cycles/6ba7b810-9dad-11d1-80b4-00c04fd430c8 \
  -H "Authorization: Bearer $TOKEN"
```

#### POST /api/v1/adapt/cycles/{id}/advance

Advance a cycle to the next phase.

```bash
curl -X POST http://localhost:3000/api/v1/adapt/cycles/6ba7b810-9dad-11d1-80b4-00c04fd430c8/advance \
  -H "Authorization: Bearer $TOKEN"
```

```json
{
  "id": "6ba7b810-9dad-11d1-80b4-00c04fd430c8",
  "phase": "correlate",
  "status": "running",
  "advanced_at": "2026-02-17T15:00:00Z"
}
```

#### POST /api/v1/adapt/cycles/{id}/pause

Pause a running cycle.

```bash
curl -X POST http://localhost:3000/api/v1/adapt/cycles/6ba7b810-9dad-11d1-80b4-00c04fd430c8/pause \
  -H "Authorization: Bearer $TOKEN"
```

### Discovery Phase -- Events

#### GET /api/v1/adapt/events

List all exposure events across cycles.

```bash
curl http://localhost:3000/api/v1/adapt/events \
  -H "Authorization: Bearer $TOKEN"
```

```json
{
  "events": [
    {
      "id": "...",
      "cycle_id": "...",
      "event_type": "new_port",
      "severity": "high",
      "details": {"port": 3389, "protocol": "tcp", "service": "rdp"},
      "acknowledged": false,
      "detected_at": "2026-02-17T14:35:00Z"
    }
  ],
  "total": 42
}
```

#### GET /api/v1/adapt/events/unacknowledged

List events that have not been acknowledged yet.

```bash
curl http://localhost:3000/api/v1/adapt/events/unacknowledged \
  -H "Authorization: Bearer $TOKEN"
```

#### POST /api/v1/adapt/events/{id}/acknowledge

Acknowledge an exposure event.

```bash
curl -X POST http://localhost:3000/api/v1/adapt/events/EVENT_ID/acknowledge \
  -H "Authorization: Bearer $TOKEN"
```

#### GET /api/v1/adapt/events/by-cycle/{cycle_id}

List events for a specific cycle.

```bash
curl http://localhost:3000/api/v1/adapt/events/by-cycle/CYCLE_ID \
  -H "Authorization: Bearer $TOKEN"
```

### Correlation Phase

#### GET /api/v1/adapt/correlations

List all threat correlations.

```bash
curl http://localhost:3000/api/v1/adapt/correlations \
  -H "Authorization: Bearer $TOKEN"
```

```json
{
  "correlations": [
    {
      "id": "...",
      "asset_id": "...",
      "threat_type": "cve",
      "threat_ref": "CVE-2024-1234",
      "confidence": 0.92,
      "risk_score": 8.7,
      "exploitability": "weaponized"
    }
  ],
  "total": 15
}
```

#### GET /api/v1/adapt/correlations/high-risk

Get correlations with risk_score above threshold.

```bash
curl http://localhost:3000/api/v1/adapt/correlations/high-risk \
  -H "Authorization: Bearer $TOKEN"
```

#### GET /api/v1/adapt/correlations/by-asset/{asset_id}

Get all correlations for a specific asset.

```bash
curl http://localhost:3000/api/v1/adapt/correlations/by-asset/ASSET_ID \
  -H "Authorization: Bearer $TOKEN"
```

### Validation Phase

#### GET /api/v1/adapt/exposures

List validated exposures.

```bash
curl http://localhost:3000/api/v1/adapt/exposures \
  -H "Authorization: Bearer $TOKEN"
```

```json
{
  "exposures": [
    {
      "id": "...",
      "correlation_id": "...",
      "validation_status": "confirmed",
      "tools_used": ["nmap", "nuclei"],
      "evidence_hash": "a3f2b8c...",
      "validated_at": "2026-02-17T15:10:00Z"
    }
  ],
  "total": 8
}
```

#### GET /api/v1/adapt/exposures/confirmed

List only confirmed exposures.

```bash
curl http://localhost:3000/api/v1/adapt/exposures/confirmed \
  -H "Authorization: Bearer $TOKEN"
```

#### POST /api/v1/adapt/exposures/{id}/revalidate

Trigger re-validation of an exposure.

```bash
curl -X POST http://localhost:3000/api/v1/adapt/exposures/EXPOSURE_ID/revalidate \
  -H "Authorization: Bearer $TOKEN"
```

### Fortification Phase

#### GET /api/v1/adapt/actions

List defense actions.

```bash
curl http://localhost:3000/api/v1/adapt/actions \
  -H "Authorization: Bearer $TOKEN"
```

```json
{
  "actions": [
    {
      "id": "...",
      "action_type": "firewall_rule",
      "target": "10.0.1.50",
      "status": "pending",
      "risk_reduction": 3.2
    }
  ],
  "total": 5
}
```

#### GET /api/v1/adapt/actions/pending

List actions awaiting approval.

#### POST /api/v1/adapt/actions/{id}/approve

Approve a defense action.

```bash
curl -X POST http://localhost:3000/api/v1/adapt/actions/ACTION_ID/approve \
  -H "Authorization: Bearer $TOKEN"
```

#### POST /api/v1/adapt/actions/{id}/execute

Execute an approved action.

```bash
curl -X POST http://localhost:3000/api/v1/adapt/actions/ACTION_ID/execute \
  -H "Authorization: Bearer $TOKEN"
```

### Metrics Phase

#### GET /api/v1/adapt/metrics

List all ADAPT metrics.

```bash
curl http://localhost:3000/api/v1/adapt/metrics \
  -H "Authorization: Bearer $TOKEN"
```

```json
{
  "metrics": [
    {
      "id": "...",
      "metric_name": "mean_time_to_detect",
      "value": 14.2,
      "unit": "minutes",
      "scope": "network",
      "recorded_at": "2026-02-17T16:00:00Z"
    }
  ],
  "total": 24
}
```

#### GET /api/v1/adapt/metrics/trends

Get metric trends over time.

```bash
curl http://localhost:3000/api/v1/adapt/metrics/trends \
  -H "Authorization: Bearer $TOKEN"
```

#### GET /api/v1/adapt/metrics/by-scope/{scope}

Get metrics filtered by scope.

```bash
curl http://localhost:3000/api/v1/adapt/metrics/by-scope/network \
  -H "Authorization: Bearer $TOKEN"
```

### Scopes

#### POST /api/v1/adapt/scopes

Create an ADAPT scope.

```bash
curl -X POST http://localhost:3000/api/v1/adapt/scopes \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Production Network",
    "scope_type": "network",
    "target_cidrs": ["10.0.0.0/16"],
    "target_domains": ["prod.example.com"],
    "scan_interval_hours": 12,
    "auto_validate": true,
    "auto_fortify": false
  }'
```

```json
{
  "id": "...",
  "name": "Production Network",
  "scope_type": "network",
  "target_cidrs": ["10.0.0.0/16"],
  "scan_interval_hours": 12,
  "created_at": "2026-02-17T14:00:00Z"
}
```

#### GET /api/v1/adapt/scopes

List all scopes.

#### PUT /api/v1/adapt/scopes/{id}

Update a scope.

#### DELETE /api/v1/adapt/scopes/{id}

Delete a scope.

### Dashboard & Scoring

#### GET /api/v1/adapt/dashboard

Get the ADAPT dashboard summary.

```bash
curl http://localhost:3000/api/v1/adapt/dashboard \
  -H "Authorization: Bearer $TOKEN"
```

```json
{
  "global_score": 72.5,
  "active_cycles": 2,
  "total_events": 156,
  "unacknowledged_events": 23,
  "confirmed_exposures": 12,
  "pending_actions": 4,
  "metric_trends": {
    "mttd_hours": 2.1,
    "mttr_hours": 8.4,
    "coverage_pct": 87.3
  }
}
```

#### GET /api/v1/adapt/score/asset/{id}

Get ADAPT score for a specific asset.

#### GET /api/v1/adapt/score/global

Get the global ADAPT score across all scopes.

---

## ADAPT Extension 1 -- Adversary War Room

### GET /api/v1/adapt/adversaries

List adversary profiles.

```bash
curl http://localhost:3000/api/v1/adapt/adversaries \
  -H "Authorization: Bearer $TOKEN"
```

```json
{
  "adversaries": [
    {
      "id": "...",
      "name": "COBALT SPIDER",
      "motivation": "financial",
      "sophistication": "advanced",
      "active": true,
      "target_sectors": ["finance", "healthcare"]
    }
  ],
  "total": 3
}
```

### GET /api/v1/adapt/adversaries/{id}

Get a specific adversary profile.

### GET /api/v1/adapt/adversaries/{id}/techniques

List techniques associated with an adversary.

### POST /api/v1/adapt/adversaries/{id}/simulate

Run a simulation of an adversary's campaign.

```bash
curl -X POST http://localhost:3000/api/v1/adapt/adversaries/ADV_ID/simulate \
  -H "Authorization: Bearer $TOKEN"
```

```json
{
  "simulation_id": "...",
  "profile_id": "...",
  "resilience_score": 0.73,
  "techniques_tested": 14,
  "techniques_detected": 10,
  "techniques_blocked": 8,
  "gap_count": 4,
  "gaps": [{"technique_id": "T1059.001", "name": "PowerShell", "tactic": "execution"}]
}
```

### GET /api/v1/adapt/coverage

List technique coverage status.

### GET /api/v1/adapt/coverage/{technique_id}

Get coverage for a specific MITRE technique.

### PUT /api/v1/adapt/coverage/{technique_id}

Update coverage status for a technique.

### GET /api/v1/adapt/coverage/matrix

Get the full MITRE ATT&CK coverage matrix.

### GET /api/v1/adapt/coverage/gaps

Get all coverage gaps.

### GET /api/v1/adapt/simulations

List all simulation runs.

### GET /api/v1/adapt/simulations/{id}

Get a specific simulation.

### GET /api/v1/adapt/simulations/latest/{profile_id}

Get the latest simulation for an adversary profile.

### POST /api/v1/adapt/what-if

Run a what-if analysis.

```bash
curl -X POST http://localhost:3000/api/v1/adapt/what-if \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"scenario": "disable_edr", "affected_techniques": ["T1059", "T1055"]}'
```

### GET /api/v1/adapt/war-room/summary

Get the war room summary dashboard.

---

## ADAPT Extension 2 -- Predictive Threat Forecast

### GET /api/v1/adapt/org-profile

Get the organization security profile.

### PUT /api/v1/adapt/org-profile

Update the organization profile.

```bash
curl -X PUT http://localhost:3000/api/v1/adapt/org-profile \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "org_name": "Acme Defense",
    "industry": "defense",
    "sector": "government",
    "employee_count": 5000,
    "tech_stack": ["kubernetes", "aws", "windows"],
    "risk_appetite": "conservative"
  }'
```

### GET /api/v1/adapt/forecasts

List threat forecasts.

### POST /api/v1/adapt/forecasts

Generate new forecasts based on org profile.

### GET /api/v1/adapt/forecasts/{id}

Get a specific forecast.

### POST /api/v1/adapt/forecasts/{id}/materialize

Mark a forecast as having materialized.

### GET /api/v1/adapt/forecasts/accuracy

Get forecast accuracy metrics.

### GET /api/v1/adapt/forecasts/trending

Get currently trending threats.

---

## ADAPT Extension 3 -- Autopilot

### GET /api/v1/adapt/autopilot/config

Get autopilot configuration.

### PUT /api/v1/adapt/autopilot/config

Update autopilot configuration.

### POST /api/v1/adapt/autopilot/enable

Enable autonomous ADAPT cycling.

```bash
curl -X POST http://localhost:3000/api/v1/adapt/autopilot/enable \
  -H "Authorization: Bearer $TOKEN"
```

```json
{
  "status": "enabled",
  "next_cycle_at": "2026-02-17T18:00:00Z",
  "kill_switch_active": false
}
```

### POST /api/v1/adapt/autopilot/disable

Disable autopilot.

### POST /api/v1/adapt/autopilot/kill-switch

Emergency kill switch -- immediately stops all autonomous operations.

### GET /api/v1/adapt/autopilot/heartbeats

List autopilot heartbeats.

### POST /api/v1/adapt/autopilot/heartbeat

Record an autopilot heartbeat.

### GET /api/v1/adapt/autopilot/escalations

List human escalations from autopilot.

### POST /api/v1/adapt/autopilot/escalations/{id}/acknowledge

Acknowledge an autopilot escalation.

### GET /api/v1/adapt/autopilot/status

Get current autopilot status.

### POST /api/v1/adapt/autopilot/force-cycle

Force an immediate ADAPT cycle.

---

## ADAPT Extension 4 -- Executive Briefing Engine

### GET /api/v1/adapt/briefing-templates

List briefing templates.

### GET /api/v1/adapt/briefing-templates/{id}

Get a specific template.

### GET /api/v1/adapt/briefings

List generated briefings.

### POST /api/v1/adapt/briefings

Generate a new briefing.

```bash
curl -X POST http://localhost:3000/api/v1/adapt/briefings \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"template_id": "...", "cycle_id": "..."}'
```

```json
{
  "id": "...",
  "template_id": "...",
  "title": "Weekly Security Briefing",
  "status": "draft",
  "section_count": 5,
  "generated_at": "2026-02-17T22:00:00Z"
}
```

### GET /api/v1/adapt/briefings/{id}

Get a specific briefing.

### DELETE /api/v1/adapt/briefings/{id}

Delete a briefing.

### GET /api/v1/adapt/briefings/{id}/sections

Get briefing sections.

### POST /api/v1/adapt/briefings/{id}/publish

Publish a briefing.

### POST /api/v1/adapt/briefings/{id}/regenerate

Regenerate briefing content.

### GET /api/v1/adapt/briefings/latest

Get the most recent briefing.

---

## ADAPT Extension 5 -- Collab (Collaborative Hunting)

### POST /api/v1/adapt/collab/workspaces

Create a collaborative workspace.

### GET /api/v1/adapt/collab/workspaces

List workspaces.

### GET /api/v1/adapt/collab/workspaces/{id}

Get workspace details.

### PUT /api/v1/adapt/collab/workspaces/{id}

Update a workspace.

### DELETE /api/v1/adapt/collab/workspaces/{id}

Delete a workspace.

### POST /api/v1/adapt/collab/workspaces/{id}/members

Add a member to a workspace.

### GET /api/v1/adapt/collab/workspaces/{id}/members

List workspace members.

### POST /api/v1/adapt/collab/workspaces/{id}/queries

Share a query in a workspace.

### GET /api/v1/adapt/collab/workspaces/{id}/queries

List shared queries.

### POST /api/v1/adapt/collab/workspaces/{id}/findings

Add a finding to a workspace.

### GET /api/v1/adapt/collab/workspaces/{id}/findings

List workspace findings.

### GET /api/v1/adapt/collab/stats

Get collaboration statistics.

---

## ADAPT Extension 6 -- Sentinel (Behavioral Anomaly Detection)

### POST /api/v1/adapt/sentinel/baselines

Create a behavioral baseline.

### GET /api/v1/adapt/sentinel/baselines

List baselines.

### GET /api/v1/adapt/sentinel/baselines/{id}

Get a specific baseline.

### PUT /api/v1/adapt/sentinel/baselines/{id}

Update a baseline.

### POST /api/v1/adapt/sentinel/detect

Run anomaly detection against baselines.

```bash
curl -X POST http://localhost:3000/api/v1/adapt/sentinel/detect \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"baseline_id": "...", "observations": [{"metric": "login_count", "value": 47}]}'
```

```json
{
  "anomalies_detected": 2,
  "anomalies": [
    {
      "metric": "login_count",
      "observed": 47,
      "baseline_mean": 12.3,
      "deviation_sigma": 4.2,
      "severity": "high"
    }
  ]
}
```

### GET /api/v1/adapt/sentinel/anomalies

List detected anomalies.

### GET /api/v1/adapt/sentinel/alerts

List sentinel alerts.

### POST /api/v1/adapt/sentinel/alerts/{id}/acknowledge

Acknowledge an alert.

### POST /api/v1/adapt/sentinel/alerts/{id}/resolve

Resolve an alert.

### POST /api/v1/adapt/sentinel/rules

Create a detection rule.

### GET /api/v1/adapt/sentinel/rules

List detection rules.

### PUT /api/v1/adapt/sentinel/rules/{id}

Update a detection rule.

### GET /api/v1/adapt/sentinel/stats

Get sentinel statistics.

---

## ADAPT Extension 7 -- Mesh (Federated Defense Network)

### POST /api/v1/adapt/mesh/peers

Register a mesh peer.

### GET /api/v1/adapt/mesh/peers

List mesh peers.

### GET /api/v1/adapt/mesh/peers/{id}

Get peer details.

### PUT /api/v1/adapt/mesh/peers/{id}

Update a peer.

### DELETE /api/v1/adapt/mesh/peers/{id}

Remove a peer.

### POST /api/v1/adapt/mesh/share

Share intelligence with the mesh.

```bash
curl -X POST http://localhost:3000/api/v1/adapt/mesh/share \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"peer_id": "...", "intel_type": "ioc", "content": {"type": "ip", "value": "203.0.113.42"}}'
```

### GET /api/v1/adapt/mesh/shared

List shared intelligence items.

### POST /api/v1/adapt/mesh/peers/{id}/trust

Update trust score for a peer.

### GET /api/v1/adapt/mesh/peers/{id}/trust

Get trust score for a peer.

### POST /api/v1/adapt/mesh/sync/{id}

Trigger sync with a peer.

### GET /api/v1/adapt/mesh/sync-log

Get sync history.

### GET /api/v1/adapt/mesh/status

Get mesh network status.

### GET /api/v1/adapt/mesh/capabilities

Get mesh capabilities.

### GET /api/v1/adapt/mesh/stats

Get mesh statistics.

---

## ADAPT Extension 8 -- Genome (Threat DNA Fingerprinting)

### POST /api/v1/adapt/genome/genomes

Create a threat genome.

### GET /api/v1/adapt/genome/genomes

List genomes.

### GET /api/v1/adapt/genome/genomes/{id}

Get a genome.

### POST /api/v1/adapt/genome/genomes/{id}/markers

Add genetic markers to a genome.

### GET /api/v1/adapt/genome/genomes/{id}/markers

List markers for a genome.

### POST /api/v1/adapt/genome/match

Match a sample against the genome database.

```bash
curl -X POST http://localhost:3000/api/v1/adapt/genome/match \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"sample_hash": "a3b2c1...", "markers": ["obfuscation_xor", "c2_dns_tunnel"]}'
```

```json
{
  "matches": [
    {
      "genome_id": "...",
      "genome_name": "APT-LAZARUS-2025",
      "similarity": 0.87,
      "matching_markers": 5,
      "total_markers": 7
    }
  ]
}
```

### GET /api/v1/adapt/genome/matches

List all matches.

### GET /api/v1/adapt/genome/clusters

List genome clusters.

### POST /api/v1/adapt/genome/cluster

Trigger genome clustering analysis.

### GET /api/v1/adapt/genome/stats

Get genome statistics.

---

## ADAPT Extension 9 -- Replay (Incident Time-Travel)

### POST /api/v1/adapt/replay/replays

Create a replay session.

### GET /api/v1/adapt/replay/replays

List replays.

### GET /api/v1/adapt/replay/replays/{id}

Get a specific replay.

### DELETE /api/v1/adapt/replay/replays/{id}

Delete a replay.

### POST /api/v1/adapt/replay/replays/{id}/events

Add an event to a replay.

### GET /api/v1/adapt/replay/replays/{id}/events

List events in a replay.

### POST /api/v1/adapt/replay/replays/{id}/snapshots

Create a replay snapshot.

### GET /api/v1/adapt/replay/replays/{id}/snapshots

List snapshots.

### POST /api/v1/adapt/replay/replays/{id}/play

Start replay playback.

### GET /api/v1/adapt/replay/replays/{id}/timeline

Get the replay timeline view.

### GET /api/v1/adapt/replay/stats

Get replay statistics.

---

## Campaigns

### POST /campaigns

Create a new campaign.

```bash
curl -X POST http://localhost:3000/campaigns \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "Q1 External Pentest", "description": "Quarterly external assessment"}'
```

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "Q1 External Pentest",
  "description": "Quarterly external assessment",
  "status": "draft",
  "created_by": "...",
  "created_at": "2026-02-17T10:00:00Z",
  "updated_at": "2026-02-17T10:00:00Z"
}
```

### GET /campaigns

List all campaigns.

```bash
curl http://localhost:3000/campaigns \
  -H "Authorization: Bearer $TOKEN"
```

### GET /campaigns/{id}

Get a specific campaign.

### PUT /campaigns/{id}/status

Update campaign status.

```bash
curl -X PUT http://localhost:3000/campaigns/CAMPAIGN_ID/status \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"status": "executing"}'
```

---

## Findings

### POST /campaigns/{campaign_id}/ingest

Ingest tool output for a campaign.

```bash
curl -X POST http://localhost:3000/campaigns/CAMPAIGN_ID/ingest \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"raw_output": "<nmap scan output>", "source_tool": "nmap"}'
```

### POST /findings/ingest

Ingest findings as JSON.

```bash
curl -X POST http://localhost:3000/findings/ingest \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "campaign_id": "...",
    "tool_output": "{\"findings\":[{\"title\":\"Open RDP\",\"severity\":\"high\"}]}"
  }'
```

```json
{
  "job_id": "...",
  "source_format": "json",
  "findings_count": 1,
  "findings": [
    {
      "id": "...",
      "title": "Open RDP",
      "severity": "high",
      "confidence": "medium",
      "source_tool": "manual",
      "verified": false
    }
  ]
}
```

### GET /campaigns/{campaign_id}/findings

List findings for a campaign.

```bash
curl "http://localhost:3000/campaigns/CAMPAIGN_ID/findings?severity=high&source_tool=nmap" \
  -H "Authorization: Bearer $TOKEN"
```

### GET /findings/{id}

Get a specific finding.

### PATCH /findings/{id}

Update a finding.

```bash
curl -X PATCH http://localhost:3000/findings/FINDING_ID \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"severity": "critical", "verified": true, "remediation": "Close port 3389"}'
```

---

## Evidence

### POST /campaigns/{campaign_id}/evidence

Upload evidence (multipart form).

```bash
curl -X POST http://localhost:3000/campaigns/CAMPAIGN_ID/evidence \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@screenshot.png" \
  -F "notes=RDP exposure screenshot"
```

```json
{
  "id": "...",
  "campaign_id": "...",
  "filename": "screenshot.png",
  "content_type": "image/png",
  "size_bytes": 245760,
  "hash_blake3": "a3f2b8c1d4e5f6...",
  "hash_sha256": "e3b0c44298fc1c1...",
  "storage_key": "evidence/2026/02/17/...",
  "custody_chain": [
    {
      "action": "collected",
      "hash_blake3": "a3f2b8c1d4e5f6...",
      "hash_sha256": "e3b0c44298fc1c1..."
    }
  ]
}
```

### GET /campaigns/{campaign_id}/evidence

List evidence for a campaign.

### GET /evidence/{id}

Get evidence metadata.

### GET /evidence/{id}/download

Download evidence file.

---

## Incidents

### GET /incident/incidents

List all incidents.

```bash
curl http://localhost:3000/incident/incidents \
  -H "Authorization: Bearer $TOKEN"
```

### POST /incident/incidents

Create an incident.

```bash
curl -X POST http://localhost:3000/incident/incidents \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Ransomware Detected on FileServer01",
    "description": "CryptoLocker variant detected by EDR",
    "priority": "p1",
    "affected_systems": ["fileserver01.corp.local", "dc01.corp.local"]
  }'
```

```json
{
  "id": "...",
  "title": "Ransomware Detected on FileServer01",
  "phase": "detection",
  "priority": "p1",
  "created_at": "2026-02-17T16:30:00Z"
}
```

### GET /incident/incidents/{id}

Get incident details.

### POST /incident/incidents/{id}/advance

Advance incident to next phase.

### GET /incident/playbooks

List incident playbooks.

### POST /incident/playbooks

Create an incident playbook.

### GET /incident/playbooks/{id}

Get a playbook.

### POST /incident/playbooks/{id}/execute

Execute a playbook against an incident.

### POST /incident/contain

Execute containment action.

```bash
curl -X POST http://localhost:3000/incident/contain \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"incident_id": "...", "action_type": "isolate_host", "target": "fileserver01.corp.local"}'
```

### POST /incident/contain/{id}/rollback

Rollback a containment action.

### GET /incident/incidents/{id}/timeline

Get incident timeline.

### POST /incident/incidents/{id}/timeline

Add event to timeline.

### GET /incident/incidents/{id}/lessons

Get lessons learned.

### POST /incident/incidents/{id}/lessons

Create lessons learned entry.

### GET /incident/stats

Get incident statistics.

---

## Threat Intelligence

### GET /threatintel/feeds

List threat feeds.

```bash
curl http://localhost:3000/threatintel/feeds \
  -H "Authorization: Bearer $TOKEN"
```

```json
{
  "feeds": [
    {
      "id": "...",
      "name": "AlienVault OTX",
      "feed_type": "otx",
      "url": "https://otx.alienvault.com/api/v1/pulses/subscribed",
      "enabled": true,
      "poll_interval_secs": 3600,
      "last_poll_at": "2026-02-17T15:00:00Z"
    }
  ],
  "total": 5
}
```

### POST /threatintel/feeds

Create a feed.

### GET /threatintel/feeds/{id}

Get feed details.

### PUT /threatintel/feeds/{id}

Update a feed.

### DELETE /threatintel/feeds/{id}

Delete a feed.

### POST /threatintel/feeds/{id}/poll

Trigger manual feed poll.

### GET /threatintel/iocs

List IOCs.

### POST /threatintel/iocs

Create an IOC.

```bash
curl -X POST http://localhost:3000/threatintel/iocs \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "ioc_type": "ip",
    "value": "203.0.113.42",
    "confidence": "high",
    "threat_actor": "COBALT SPIDER",
    "tags": ["ransomware", "c2"]
  }'
```

### GET /threatintel/iocs/{id}

Get IOC details.

### DELETE /threatintel/iocs/{id}

Expire an IOC.

### POST /threatintel/iocs/search

Search IOCs.

### POST /threatintel/iocs/bulk

Bulk import IOCs.

### GET /threatintel/actors

List threat actors.

### POST /threatintel/actors

Create a threat actor.

### GET /threatintel/actors/{id}

Get actor details.

### PUT /threatintel/actors/{id}

Update a threat actor.

### GET /threatintel/reports

List intel reports.

### POST /threatintel/reports

Create an intel report.

### GET /threatintel/reports/{id}

Get report details.

### GET /threatintel/stats

Get threat intel statistics.

---

## STIX Feed Aggregator

### POST /api/v1/feeds/stix

Create a STIX feed.

```bash
curl -X POST http://localhost:3000/api/v1/feeds/stix \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "CISA Known Exploited", "url": "https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json", "poll_interval_secs": 3600}'
```

### GET /api/v1/feeds/stix

List STIX feeds.

### GET /api/v1/feeds/stix/{id}

Get feed details.

### PUT /api/v1/feeds/stix/{id}

Update a feed.

### DELETE /api/v1/feeds/stix/{id}

Delete a feed.

### POST /api/v1/feeds/stix/{id}/poll

Poll a feed now.

### GET /api/v1/feeds/stix/{id}/objects

List STIX objects from a feed.

### GET /api/v1/feeds/stix/objects/search

Search STIX objects.

### POST /api/v1/feeds/stix/import

Import a STIX bundle.

### GET /api/v1/feeds/stix/{id}/collections

List TAXII collections for a feed.

### GET /api/v1/feeds/stix/{id}/history

Get feed poll history.

### GET /api/v1/feeds/stix/active

List active feeds.

### GET /api/v1/feeds/stix/errors

Get recent feed errors.

### GET /api/v1/feeds/stix/dedup-stats

Get deduplication statistics.

### GET /api/v1/feeds/stix/stats

Get overall STIX statistics.

---

## SIGMA Rule Engine

### POST /api/v1/sigma/rules

Create a SIGMA rule.

```bash
curl -X POST http://localhost:3000/api/v1/sigma/rules \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Suspicious PowerShell Download",
    "level": "high",
    "logsource": {"category": "process_creation", "product": "windows"},
    "detection": {"selection": {"CommandLine|contains": "IEX (New-Object Net.WebClient).DownloadString"}},
    "description": "Detects PowerShell download cradle"
  }'
```

### GET /api/v1/sigma/rules

List SIGMA rules.

### GET /api/v1/sigma/rules/{id}

Get a rule.

### PUT /api/v1/sigma/rules/{id}

Update a rule.

### DELETE /api/v1/sigma/rules/{id}

Delete a rule.

### POST /api/v1/sigma/rules/{id}/deploy

Deploy a rule to detection engines.

### POST /api/v1/sigma/rules/{id}/undeploy

Undeploy a rule.

### GET /api/v1/sigma/rules/{id}/deployments

List deployments for a rule.

### POST /api/v1/sigma/rules/{id}/test

Test a rule against sample data.

### GET /api/v1/sigma/rules/{id}/test-results

Get test results.

### POST /api/v1/sigma/import

Bulk import SIGMA rules.

### GET /api/v1/sigma/export

Export rules.

### GET /api/v1/sigma/search

Search rules.

### GET /api/v1/sigma/stats

Get SIGMA statistics.

---

## SOAR (Security Orchestration, Automation & Response)

### GET /soar/playbooks

List SOAR playbooks.

```bash
curl http://localhost:3000/soar/playbooks \
  -H "Authorization: Bearer $TOKEN"
```

```json
{
  "playbooks": [
    {
      "id": "...",
      "name": "Phishing Response",
      "status": "active",
      "trigger_type": "alert",
      "version": 3,
      "author": "analyst@playseat.internal"
    }
  ],
  "total": 5
}
```

### POST /soar/playbooks

Create a playbook.

### GET /soar/playbooks/{id}

Get playbook details.

### PUT /soar/playbooks/{id}

Update a playbook.

### DELETE /soar/playbooks/{id}

Delete a playbook.

### POST /soar/playbooks/{id}/activate

Activate a playbook.

### POST /soar/playbooks/{id}/suspend

Suspend a playbook.

### GET /soar/playbooks/{id}/steps

List workflow steps.

### POST /soar/playbooks/{id}/steps

Add a step.

### PUT /soar/steps/{id}

Update a step.

### DELETE /soar/steps/{id}

Delete a step.

### GET /soar/executions

List playbook executions.

### POST /soar/playbooks/{id}/trigger

Trigger playbook execution.

### GET /soar/executions/{id}

Get execution details.

### POST /soar/executions/{id}/cancel

Cancel a running execution.

### GET /soar/executions/{id}/steps

Get execution step results.

### POST /soar/executions/{id}/approve

Approve a step requiring approval.

### GET /soar/stats

Get SOAR statistics.

### GET /soar/stats/efficiency

Get automation efficiency metrics.

---

## OSINT

### POST /osint/profiles

Create a target profile.

```bash
curl -X POST http://localhost:3000/osint/profiles \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "campaign_id": "...",
    "target_name": "Example Corp",
    "organization": "example.com",
    "aliases": ["ExCorp", "Example Corporation"]
  }'
```

### GET /osint/profiles

List profiles.

### GET /osint/profiles/{id}

Get a profile.

### GET /osint/sources

List data sources.

### POST /osint/search

Search across sources.

### GET /osint/entities

List discovered entities.

### POST /osint/entities/resolve

Resolve entity duplicates.

### GET /osint/score/{id}

Get exposure score for a target.

### GET /osint/graph/{id}

Get entity relationship graph.

### POST /osint/graph/build

Build a graph for a target.

### GET /osint/reports/{id}

Get an OSINT report.

### POST /osint/reports/generate

Generate a new report.

---

## Forensics

### GET /forensics/cases

List forensic cases.

### POST /forensics/cases

Create a case.

### GET /forensics/cases/{id}

Get case details.

### POST /forensics/cases/{id}/artifacts

Add an artifact.

### POST /forensics/artifacts/{id}/verify

Verify artifact integrity.

### GET /forensics/artifacts/{id}/custody

Get chain of custody.

### POST /forensics/memory/analyze

Start memory analysis.

### GET /forensics/memory/{id}/injection

Detect process injection.

### GET /forensics/memory/{id}/hidden

Detect hidden processes.

### POST /forensics/disk/analyze

Start disk analysis.

### POST /forensics/disk/{id}/recover

Recover deleted files.

### GET /forensics/disk/{id}/encryption

Detect encryption.

### POST /forensics/timeline/build

Build a forensic timeline.

### GET /forensics/timeline/{id}

Get a timeline.

### GET /forensics/timeline/{id}/anomalies

Detect timeline anomalies.

---

## Red Team

### GET /redteam/playbooks

List red team playbooks.

### POST /redteam/playbooks

Create a playbook.

### GET /redteam/playbooks/{id}

Get a playbook.

### POST /redteam/playbooks/{id}/approve

Approve a playbook.

### POST /redteam/playbooks/{id}/activate

Activate a playbook.

### POST /redteam/playbooks/{id}/abort

Abort a playbook.

### GET /redteam/playbooks/{id}/steps

List playbook steps.

### POST /redteam/playbooks/{id}/steps/{step_id}/result

Record a step result.

### GET /redteam/campaigns/{campaign_id}/playbooks

List playbooks for a campaign.

### GET /redteam/techniques

List MITRE ATT&CK techniques.

### GET /redteam/techniques/{mitre_id}

Get a specific technique.

### GET /redteam/techniques/search

Search techniques.

---

## AI Analysis

### POST /ai/triage

AI-powered finding triage.

```bash
curl -X POST http://localhost:3000/ai/triage \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "finding_id": "...",
    "title": "Open RDP Port",
    "description": "Port 3389 open on production server",
    "current_severity": "medium"
  }'
```

```json
{
  "id": "...",
  "finding_id": "...",
  "suggested_severity": "high",
  "confidence": 0.89,
  "false_positive_likelihood": 0.05,
  "reasoning": "RDP exposed to internet is a critical risk...",
  "provider": "openai",
  "model": "gpt-4",
  "tokens_used": 342
}
```

### GET /ai/triage/{id}

Get triage result.

### POST /ai/remediation

Get AI remediation suggestions.

### POST /ai/narrative

Generate executive narrative.

### POST /ai/correlate

Correlate findings using AI.

### GET /ai/prompts

List prompt templates.

### POST /ai/prompts

Create a prompt template.

### GET /ai/usage

Get AI usage statistics.

---

## Natural Language Query

### POST /nlquery/ask

Ask a natural language question.

```bash
curl -X POST http://localhost:3000/nlquery/ask \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query": "how many critical findings were found this week?"}'
```

```json
{
  "id": "...",
  "raw_text": "how many critical findings were found this week?",
  "parsed_intent": "count",
  "generated_sql": "SELECT COUNT(*) FROM findings WHERE severity = '\"critical\"' AND found_at > NOW() - INTERVAL '7 days'",
  "result_count": 1,
  "results": [{"count": 12}],
  "execution_time_ms": 45,
  "success": true
}
```

### GET /nlquery/history

List query history.

### GET /nlquery/history/{id}

Get a specific query.

### GET /nlquery/templates

List NLQ templates.

### POST /nlquery/templates

Create a template.

### GET /nlquery/templates/{id}

Get a template.

### GET /nlquery/favorites

List saved favorites.

### POST /nlquery/favorites

Save a query as favorite.

### DELETE /nlquery/favorites/{id}

Delete a favorite.

### GET /nlquery/aliases

List entity aliases.

### POST /nlquery/aliases

Create an alias.

### GET /nlquery/stats

Get NLQ statistics.

---

## GeoTrack

### POST /geotrack/targets

Create a geo target.

```bash
curl -X POST http://localhost:3000/geotrack/targets \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "Antenna Alpha", "target_type": "infrastructure", "lat": 48.8566, "lon": 2.3522}'
```

### GET /geotrack/targets

List targets.

### GET /geotrack/targets/{id}

Get target.

### PUT /geotrack/targets/{id}

Update target.

### DELETE /geotrack/targets/{id}

Delete target.

### GET /geotrack/targets/{id}/history

Get position history.

### GET /geotrack/targets/{id}/trajectory

Get computed trajectory.

### POST /geotrack/geofences

Create a geofence.

### GET /geotrack/geofences

List geofences.

### GET /geotrack/geofences/{id}

Get geofence.

### DELETE /geotrack/geofences/{id}

Delete geofence.

### GET /geotrack/geofences/{id}/alerts

Get geofence alerts.

### POST /geotrack/geofences/{id}/check

Check a point against a geofence.

### POST /geotrack/feeds

Create a geo data feed.

### GET /geotrack/feeds

List feeds.

### GET /geotrack/feeds/{id}

Get feed.

### DELETE /geotrack/feeds/{id}

Delete feed.

### POST /geotrack/feeds/ingest

Ingest geo data.

### POST /geotrack/analysis/proximity

Proximity search.

### GET /geotrack/analysis/heatmap

Get activity heatmap.

### GET /geotrack/analysis/movement/{id}

Get movement patterns.

### POST /geotrack/analysis/co-travel

Co-travel analysis.

### GET /geotrack/analysis/predict/{id}

Predict next location.

---

## Command Center

### GET /command/widgets

List widgets.

### POST /command/widgets

Create a widget.

### GET /command/widgets/{id}

Get widget.

### PUT /command/widgets/{id}

Update widget.

### DELETE /command/widgets/{id}

Delete widget.

### GET /command/threat-level

Get current threat level.

### POST /command/threat-level

Set threat level.

### GET /command/threat-level/history

Get threat level history.

### POST /command/search

Search across all domains.

### GET /command/search/history

Get search history.

### GET /command/bookmarks

List bookmarks.

### POST /command/bookmarks

Create a bookmark.

### DELETE /command/bookmarks/{id}

Delete a bookmark.

### GET /command/investigations

List investigations.

### POST /command/investigations

Create an investigation.

### GET /command/investigations/{id}

Get investigation.

### PUT /command/investigations/{id}

Update investigation.

### GET /command/briefings

List briefings.

### POST /command/briefings

Create a briefing.

### GET /command/briefings/{id}

Get briefing.

---

## Ontology (Knowledge Graph)

### GET /ontology/types

List entity types.

### POST /ontology/types

Create entity type.

### GET /ontology/entities

List entities.

### POST /ontology/entities

Create entity.

### GET /ontology/entities/{id}

Get entity.

### PUT /ontology/entities/{id}

Update entity.

### DELETE /ontology/entities/{id}

Delete entity.

### POST /ontology/entities/search

Search entities.

### GET /ontology/entities/{id}/timeline

Get entity timeline.

### GET /ontology/entities/{id}/neighbors

Get entity neighbors.

### GET /ontology/relationships

List relationships.

### POST /ontology/relationships

Create relationship.

### DELETE /ontology/relationships/{id}

Delete relationship.

### GET /ontology/relationship-types

List relationship types.

### POST /ontology/traverse

Traverse the knowledge graph.

### POST /ontology/path

Find shortest path between entities.

### POST /ontology/resolve

Resolve duplicate entities.

### GET /ontology/resolutions

List resolution history.

### POST /ontology/tags/{entity_id}

Add tag to entity.

### GET /ontology/tags/{entity_id}

Get entity tags.

### GET /ontology/stats

Get ontology statistics.

---

## Streaming Pipeline

### POST /api/v1/stream/sources

Create a stream source.

```bash
curl -X POST http://localhost:3000/api/v1/stream/sources \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "Syslog Ingestion", "source_type": "syslog", "config": {"port": 514}}'
```

### GET /api/v1/stream/sources

List sources.

### GET /api/v1/stream/sources/{id}

Get source.

### PUT /api/v1/stream/sources/{id}/pause

Pause a source.

### PUT /api/v1/stream/sources/{id}/resume

Resume a source.

### GET /api/v1/stream/sources/stats

Get source statistics.

### POST /api/v1/stream/windows

Create a time window.

### GET /api/v1/stream/windows

List windows.

### GET /api/v1/stream/windows/{id}

Get window.

### POST /api/v1/stream/windows/{id}/flush

Flush a window.

### POST /api/v1/stream/aggregations

Create an aggregation.

### GET /api/v1/stream/aggregations

List aggregations.

### GET /api/v1/stream/aggregations/{id}

Get aggregation.

### GET /api/v1/stream/aggregations/stats

Get aggregation statistics.

### POST /api/v1/stream/sinks

Create a sink.

### GET /api/v1/stream/sinks

List sinks.

### GET /api/v1/stream/sinks/{id}

Get sink.

### GET /api/v1/stream/sinks/stats

Get sink statistics.

---

## Compliance

### GET /compliance/soc2/controls

List SOC 2 controls.

### POST /compliance/soc2/controls/{id}/evidence

Attach evidence to a control.

### GET /compliance/soc2/readiness

Assess SOC 2 readiness.

### GET /compliance/pentest/reports

List pentest reports.

### POST /compliance/pentest/reports

Create a pentest report.

### GET /compliance/pentest/reports/{id}

Get a pentest report.

### GET /compliance/architecture/reviews

List architecture reviews.

### POST /compliance/architecture/reviews

Create an architecture review.

### GET /compliance/architecture/reviews/{id}

Get an architecture review.

### GET /compliance/demo/environments

List demo environments.

### POST /compliance/demo/environments

Provision a demo environment.

### GET /compliance/demo/environments/{id}

Get a demo environment.

### POST /compliance/demo/environments/{id}/teardown

Teardown a demo environment.

### GET /compliance/demo/scenarios

List demo scenarios.

---

## Evidence Court

### GET /api/v1/evidence-lockers

List evidence lockers (legacy).

### POST /api/v1/evidence-lockers/create

Create an evidence locker (legacy).

### POST /api/v1/evidence-court/cases

Create a case.

```bash
curl -X POST http://localhost:3000/api/v1/evidence-court/cases \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"title": "Ransomware Investigation Q1-2026", "classification": "restricted"}'
```

### GET /api/v1/evidence-court/cases

List cases.

### GET /api/v1/evidence-court/cases/{id}

Get a case.

### PUT /api/v1/evidence-court/cases/{id}

Update a case.

### DELETE /api/v1/evidence-court/cases/{id}

Close a case.

### POST /api/v1/evidence-court/cases/{id}/exhibits

Add an exhibit to a case.

### GET /api/v1/evidence-court/cases/{id}/exhibits

List exhibits.

### GET /api/v1/evidence-court/exhibits/{id}

Get an exhibit.

### POST /api/v1/evidence-court/cases/{id}/package

Create an evidence package.

### GET /api/v1/evidence-court/cases/{id}/packages

List packages.

### GET /api/v1/evidence-court/packages/{id}

Get a package.

### POST /api/v1/evidence-court/packages/{id}/verify

Verify package integrity.

### POST /api/v1/evidence-court/exhibits/{id}/transfer

Transfer exhibit custody.

### GET /api/v1/evidence-court/exhibits/{id}/chain

Get chain of custody.

### POST /api/v1/evidence-court/cases/{id}/legal-hold

Create a legal hold.

---

## Malware Analysis (including YARA)

### GET /malware/samples

List malware samples.

### POST /malware/samples

Submit a sample.

### GET /malware/samples/{id}

Get sample details.

### POST /malware/samples/{id}/classify

Classify a sample.

### POST /malware/sandbox/run

Run sample in sandbox.

### GET /malware/sandbox/{id}

Get sandbox run.

### GET /malware/sandbox/{id}/behaviors

Get observed behaviors.

### GET /malware/yara/rules

List YARA rules.

### POST /malware/yara/rules

Create a YARA rule.

### GET /malware/yara/rules/{id}

Get a rule.

### PUT /malware/yara/rules/{id}

Update a rule.

### DELETE /malware/yara/rules/{id}

Delete a rule.

### POST /malware/yara/scan

Start a YARA scan.

### GET /malware/yara/scans

List scans.

### GET /malware/yara/scans/{id}

Get scan results.

---

## Additional Modules

### CSPM -- Cloud Security Posture Management

| Method | Path | Description |
|---|---|---|
| POST | /cspm/accounts | Register a cloud account |
| GET | /cspm/accounts | List accounts |
| GET | /cspm/accounts/{id} | Get account |
| PUT | /cspm/accounts/{id} | Update account |
| DELETE | /cspm/accounts/{id} | Delete account |
| POST | /cspm/policies | Create a policy |
| GET | /cspm/policies | List policies |
| PUT | /cspm/policies/{id} | Update a policy |
| POST | /cspm/scans | Start a scan |
| GET | /cspm/scans | List scans |
| GET | /cspm/scans/{id} | Get scan |
| GET | /cspm/findings | List findings |
| POST | /cspm/findings/{id}/remediate | Remediate a finding |
| GET | /cspm/compliance/{account_id} | Compliance check |
| GET | /cspm/stats | Get statistics |

### Behavioral Analytics

| Method | Path | Description |
|---|---|---|
| GET | /behavioral/baselines | List baselines |
| POST | /behavioral/baselines | Create baseline |
| GET | /behavioral/baselines/{id} | Get baseline |
| POST | /behavioral/baselines/{id}/update | Update baseline |
| GET | /behavioral/anomalies | List anomalies |
| POST | /behavioral/anomalies/detect | Detect anomalies |
| GET | /behavioral/anomalies/critical | Critical anomalies |
| GET | /behavioral/insider-threats | List assessments |
| POST | /behavioral/insider-threats/assess | Assess insider threat |
| GET | /behavioral/insider-threats/high-risk | High risk entities |
| POST | /behavioral/sessions/score | Score a session |
| GET | /behavioral/sessions/{id} | Get session score |
| GET | /behavioral/sessions/high-risk | High risk sessions |
| GET | /behavioral/stats | Get statistics |

### Zero Trust

| Method | Path | Description |
|---|---|---|
| GET | /zerotrust/evaluations | List evaluations |
| POST | /zerotrust/evaluations | Evaluate trust |
| GET | /zerotrust/evaluations/{id} | Get evaluation |
| GET | /zerotrust/evaluations/untrusted | Untrusted subjects |
| GET | /zerotrust/access | List access records |
| POST | /zerotrust/access/decide | Make access decision |
| GET | /zerotrust/access/denied | Denied requests |
| GET | /zerotrust/access/monitored | Monitored requests |
| GET | /zerotrust/segments | List segments |
| POST | /zerotrust/segments | Create segment |
| GET | /zerotrust/segments/{id} | Get segment |
| POST | /zerotrust/segments/{id}/members | Add member |
| POST | /zerotrust/segments/{id}/policy | Set policy |
| GET | /zerotrust/verifications | List verifications |
| POST | /zerotrust/verifications | Verify subject |

### Security Metrics

| Method | Path | Description |
|---|---|---|
| GET | /metrics/security | List metrics |
| POST | /metrics/security | Record metric |
| POST | /metrics/security/query | Query metrics |
| GET | /metrics/security/latest | Latest metrics |
| GET | /metrics/thresholds | List thresholds |
| POST | /metrics/thresholds | Create threshold |
| PUT | /metrics/thresholds/{id} | Update threshold |
| GET | /metrics/thresholds/violations | Get violations |
| GET | /metrics/trends | List trends |
| POST | /metrics/trends/calculate | Calculate trends |
| GET | /metrics/trends/{name} | Get specific trend |
| GET | /metrics/kpis | List KPIs |
| POST | /metrics/kpis | Create KPI |
| GET | /metrics/kpis/{id} | Get KPI |
| PUT | /metrics/kpis/{id} | Update KPI |

### Purple Team

| Method | Path | Description |
|---|---|---|
| GET | /api/v1/purple-team | List exercises |
| POST | /api/v1/purple-team/create | Create exercise |
| GET | /api/v1/purple-team/{id} | Get exercise |
| GET | /api/v1/purple-team/{id}/objectives | List objectives |
| POST | /api/v1/purple-team/{id}/objectives | Create objective |
| GET | /api/v1/purple-team/{id}/findings | List findings |
| POST | /api/v1/purple-team/{id}/findings | Create finding |
| GET | /api/v1/purple-team/{id}/scores | List scores |
| POST | /api/v1/purple-team/{id}/scores | Create score |
| GET | /api/v1/purple-team/stats | Get statistics |

### Breach Simulation (BAS)

| Method | Path | Description |
|---|---|---|
| POST | /breach-sim/scenarios | Create scenario |
| GET | /breach-sim/scenarios | List scenarios |
| GET | /breach-sim/scenarios/{id} | Get scenario |
| PUT | /breach-sim/scenarios/{id} | Update scenario |
| DELETE | /breach-sim/scenarios/{id} | Delete scenario |
| POST | /breach-sim/runs | Start a run |
| GET | /breach-sim/runs | List runs |
| GET | /breach-sim/runs/{id} | Get run |
| GET | /breach-sim/runs/{id}/results | Get results |
| GET | /breach-sim/runs/{id}/controls | List controls tested |
| GET | /breach-sim/runs/{id}/resilience | Get resilience score |

### Cyber Range

| Method | Path | Description |
|---|---|---|
| GET | /cyberrange/scenarios | List scenarios |
| POST | /cyberrange/scenarios | Create scenario |
| GET | /cyberrange/scenarios/{id} | Get scenario |
| POST | /cyberrange/scenarios/{id}/objectives | Add objective |
| GET | /cyberrange/exercises | List exercises |
| POST | /cyberrange/exercises | Create exercise |
| GET | /cyberrange/exercises/{id} | Get exercise |
| POST | /cyberrange/exercises/{id}/transition | Transition state |
| POST | /cyberrange/exercises/{id}/participants | Add participant |
| GET | /cyberrange/exercises/active | Active exercises |
| GET | /cyberrange/assessments | List assessments |

### Reporting

| Method | Path | Description |
|---|---|---|
| POST | /reporting/generate | Generate a report |
| GET | /reporting/reports | List reports |
| GET | /reporting/reports/{id} | Get report |
| GET | /reporting/compliance/frameworks | List frameworks |
| POST | /reporting/compliance/assess | Assess compliance |
| GET | /reporting/evidence-packs | List evidence packs |
| POST | /reporting/evidence-packs/create | Create pack |
| GET | /reporting/evidence-packs/{id} | Get pack |
| GET | /reporting/dashboard | Get dashboard |
| GET | /reporting/dashboard/trends | Get trends |

### Labs

| Method | Path | Description |
|---|---|---|
| GET | /labs | List labs |
| POST | /labs | Provision a lab |
| GET | /labs/{lab_id} | Get lab |
| POST | /labs/{lab_id}/activate | Activate lab |
| POST | /labs/{lab_id}/pause | Pause lab |
| POST | /labs/{lab_id}/teardown | Teardown lab |
| POST | /labs/{lab_id}/emergency-stop | Emergency stop |
| POST | /labs/{lab_id}/sessions | Start session |
| POST | /labs/{lab_id}/sessions/{session_id}/end | End session |
| POST | /labs/{lab_id}/sessions/{session_id}/actions | Record action |
| GET | /campaigns/{campaign_id}/labs | List campaign labs |

### Social Engineering

| Method | Path | Description |
|---|---|---|
| GET | /social-eng/campaigns | List campaigns |
| POST | /social-eng/campaigns | Create campaign |
| GET | /social-eng/campaigns/{id} | Get campaign |
| POST | /social-eng/campaigns/{id}/approve | Approve |
| POST | /social-eng/campaigns/{id}/launch | Launch |
| POST | /social-eng/campaigns/{id}/pause | Pause |
| POST | /social-eng/campaigns/{id}/abort | Abort |
| GET | /social-eng/campaigns/{id}/metrics | Get metrics |
| GET | /social-eng/campaigns/{id}/events | List events |
| POST | /social-eng/campaigns/{id}/targets | Add targets |
| POST | /social-eng/templates | Create template |
| GET | /social-eng/templates | List templates |
| GET | /campaigns/{campaign_id}/social-eng | Campaign social eng |

### Dashboards

| Method | Path | Description |
|---|---|---|
| GET | /dashboards | List dashboards |
| POST | /dashboards | Create dashboard |
| GET | /dashboards/{id} | Get dashboard |
| GET | /dashboards/{id}/widgets | List widgets |
| POST | /dashboards/{id}/widgets | Add widget |
| GET | /dashboards/widgets/{id} | Get widget |
| GET | /dashboards/threatmap | Get threat map |
| POST | /dashboards/threatmap/entries | Add threat entry |
| GET | /dashboards/metrics/stream | Get metric stream |
| POST | /dashboards/metrics/record | Record metric |

---

## Authentication Notes

All endpoints except `/auth/login`, `/auth/refresh`, and `/health` require a valid JWT in the `Authorization` header:

```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

- Access tokens expire after **15 minutes** (900 seconds)
- Refresh tokens expire after **7 days**
- Roles: `admin`, `campaign_lead`, `analyst`, `viewer`, `auditor`
- All operations are logged to the append-only `audit_events` table

## Error Responses

All endpoints return errors in this format:

```json
{
  "error": "description of what went wrong"
}
```

Common HTTP status codes:
- `401 Unauthorized` -- Missing or expired token
- `403 Forbidden` -- Insufficient role permissions
- `404 Not Found` -- Resource does not exist
- `422 Unprocessable Entity` -- Validation error
- `500 Internal Server Error` -- Server-side failure

---

(c) 2026 Playseat -- All Rights Reserved | Proprietary and Confidential
