# Appendix B -- Database Schema Reference

## Key Tables Across All Domains

> 225 migrations. 1,100+ tables. PostgreSQL 16. UUIDv7 primary keys. JSONB for flexible data. GIN indexes for full-text and JSON queries.

I am not going to document all 1,100 tables here. That would be a phone book, not a reference. What follows are the ~50 tables you will actually touch daily -- the ones your queries hit, your routes read from, and your forensic reports pull data out of. Organized by domain.

---

## Core Platform

### audit_events

The audit spine. Every operation in the platform logs here. This table is **append-only** -- a PostgreSQL trigger prevents UPDATE and DELETE.

| Column | Type | Notes |
|---|---|---|
| id | UUID | Primary key |
| timestamp | TIMESTAMPTZ | When the event occurred |
| actor_id | UUID | Who performed the action |
| action | TEXT | What they did |
| resource_type | TEXT | What kind of thing was affected |
| resource_id | UUID | Which specific resource |
| outcome | TEXT | `success`, `failure`, or `denied` |
| correlation_id | UUID | Links related events together |
| client_context | TEXT | Client-side context (IP, user-agent) |
| metadata | JSONB | Arbitrary additional data |

**Indexes:** timestamp, actor_id, correlation_id, (resource_type, resource_id)

---

### users

RBAC foundation. Five roles: admin, campaign_lead, analyst, viewer, auditor.

| Column | Type | Notes |
|---|---|---|
| id | UUID | Primary key |
| username | TEXT | Unique login name |
| display_name | TEXT | Human-readable name |
| email | TEXT | Unique email |
| role | TEXT | One of: admin, campaign_lead, analyst, viewer, auditor |
| active | BOOLEAN | Account enabled flag |
| created_at | TIMESTAMPTZ | Account creation time |
| updated_at | TIMESTAMPTZ | Last modification |

**Indexes:** role, active

**Seed data:** System user (admin) at `00000000-0000-0000-0000-000000000001`

---

### campaigns

Campaign state machine. Status transitions enforced in application code.

| Column | Type | Notes |
|---|---|---|
| id | UUID | Primary key |
| name | TEXT | Campaign name |
| description | TEXT | Campaign description |
| status | TEXT | draft, authorized, executing, paused, reporting, closed, cancelled |
| created_by | UUID | FK -> users(id) |
| authorized_by | UUID | FK -> users(id), nullable |
| created_at | TIMESTAMPTZ | Creation time |
| updated_at | TIMESTAMPTZ | Last update |
| authorized_at | TIMESTAMPTZ | Authorization timestamp |
| closed_at | TIMESTAMPTZ | Close timestamp |

**Indexes:** status, created_by, created_at DESC

---

### findings

Normalized vulnerability findings from any security tool.

| Column | Type | Notes |
|---|---|---|
| id | UUID | Primary key |
| campaign_id | UUID | FK -> campaigns(id) ON DELETE CASCADE |
| title | TEXT | Finding title |
| description | TEXT | Full description |
| severity | TEXT | info, low, medium, high, critical |
| confidence | TEXT | low, medium, high, confirmed |
| cwe_id | TEXT | CWE reference, nullable |
| cve_id | TEXT | CVE reference, nullable |
| affected_target | TEXT | What is affected |
| source_tool | TEXT | Which tool found it |
| raw_output | JSONB | Original tool output |
| remediation | TEXT | Remediation guidance |
| found_at | TIMESTAMPTZ | Discovery time |
| verified | BOOLEAN | Manually verified flag |
| verified_by | UUID | FK -> users(id) |
| verified_at | TIMESTAMPTZ | Verification timestamp |

**Indexes:** campaign_id, severity, source_tool, cwe_id (partial), cve_id (partial)

---

### evidence

Evidence records with dual-hash integrity verification.

| Column | Type | Notes |
|---|---|---|
| id | UUID | Primary key |
| campaign_id | UUID | FK -> campaigns(id) ON DELETE CASCADE |
| finding_id | UUID | FK -> findings(id), nullable |
| filename | TEXT | Original filename |
| content_type | TEXT | MIME type |
| size_bytes | BIGINT | File size |
| hash_blake3 | TEXT | BLAKE3 hash of the file |
| hash_sha256 | TEXT | SHA-256 hash of the file |
| storage_key | TEXT | MinIO/S3 object key |
| collected_by | UUID | FK -> users(id) |
| collected_at | TIMESTAMPTZ | Collection timestamp |
| notes | TEXT | Analyst notes |

**Indexes:** campaign_id, finding_id (partial), hash_sha256

---

### evidence_custody

Chain of custody for evidence. Every touch is recorded with re-hashing.

| Column | Type | Notes |
|---|---|---|
| id | UUID | Primary key |
| evidence_id | UUID | FK -> evidence(id) ON DELETE CASCADE |
| actor_id | UUID | FK -> users(id) |
| action | TEXT | collected, transferred, verified, archived, exported |
| hash_blake3 | TEXT | BLAKE3 hash at time of action |
| hash_sha256 | TEXT | SHA-256 hash at time of action |
| notes | TEXT | Action notes |
| created_at | TIMESTAMPTZ | When the action occurred |

**Indexes:** evidence_id, actor_id

---

## ADAPT Engine

### adapt_scopes

Defines what the ADAPT engine monitors.

| Column | Type | Notes |
|---|---|---|
| id | UUID | Primary key |
| name | TEXT | Scope name |
| description | TEXT | Description |
| scope_type | TEXT | network, application, or organization |
| target_cidrs | TEXT[] | CIDR ranges to monitor |
| target_domains | TEXT[] | Domains to monitor |
| scan_interval_hours | INTEGER | How often to scan (default 24) |
| auto_validate | BOOLEAN | Auto-validate exposures (default true) |
| auto_fortify | BOOLEAN | Auto-execute defense actions (default false) |
| created_by | UUID | Who created the scope |
| created_at | TIMESTAMPTZ | Creation time |
| updated_at | TIMESTAMPTZ | Last update |

**Indexes:** scope_type, created_at

---

### adapt_cycles

The ADAPT five-phase cycle: discover, correlate, validate, fortify, prove.

| Column | Type | Notes |
|---|---|---|
| id | UUID | Primary key |
| cycle_number | INTEGER | Sequential cycle number |
| scope_id | UUID | FK -> adapt_scopes(id) |
| phase | TEXT | discover, correlate, validate, fortify, prove |
| status | TEXT | running, completed, failed, paused |
| started_at | TIMESTAMPTZ | Cycle start |
| completed_at | TIMESTAMPTZ | Cycle completion |
| phase_metrics | JSONB | Metrics captured during this phase |
| evidence_hash | TEXT | Hash of cycle evidence |
| created_by | UUID | Who started the cycle |
| created_at | TIMESTAMPTZ | Creation time |

**Indexes:** status, phase, scope_id, cycle_number

---

### adapt_exposure_events

Events detected during the Discovery phase.

| Column | Type | Notes |
|---|---|---|
| id | UUID | Primary key |
| cycle_id | UUID | FK -> adapt_cycles(id) |
| event_type | TEXT | new_host, new_port, new_service, removed_service, cert_expiring, shadow_it, credential_leak |
| asset_id | UUID | Which asset is affected |
| details | JSONB | Event-specific details |
| severity | TEXT | critical, high, medium, low, info |
| detected_at | TIMESTAMPTZ | Detection time |
| acknowledged | BOOLEAN | Has an analyst acknowledged this |
| acknowledged_by | UUID | Who acknowledged |
| acknowledged_at | TIMESTAMPTZ | When acknowledged |

**Indexes:** cycle_id, event_type, severity, acknowledged, asset_id

---

### adapt_threat_correlations

Links between assets and known threats during the Correlation phase.

| Column | Type | Notes |
|---|---|---|
| id | UUID | Primary key |
| cycle_id | UUID | FK -> adapt_cycles(id) |
| asset_id | UUID | The affected asset |
| threat_type | TEXT | cve, ioc, ttp, exploit |
| threat_ref | TEXT | Reference (e.g., CVE-2024-1234) |
| confidence | REAL | Correlation confidence 0.0-1.0 |
| risk_score | REAL | Computed risk score |
| exploitability | TEXT | none, theoretical, poc, weaponized |
| factors | JSONB | Contributing risk factors |
| correlated_at | TIMESTAMPTZ | When correlation was made |

**Indexes:** cycle_id, asset_id, threat_type, risk_score, threat_ref

---

### adapt_validated_exposures

Confirmed exposures from the Validation phase.

| Column | Type | Notes |
|---|---|---|
| id | UUID | Primary key |
| cycle_id | UUID | FK -> adapt_cycles(id) |
| correlation_id | UUID | FK -> adapt_threat_correlations(id) |
| pipeline_run_id | UUID | Validation pipeline run |
| validation_status | TEXT | confirmed, denied, inconclusive |
| tools_used | TEXT[] | Tools used for validation |
| evidence_hash | TEXT | Evidence integrity hash |
| validated_at | TIMESTAMPTZ | When validation completed |

---

### adapt_defense_actions

Actions generated during the Fortification phase.

| Column | Type | Notes |
|---|---|---|
| id | UUID | Primary key |
| cycle_id | UUID | FK -> adapt_cycles(id) |
| exposure_id | UUID | FK -> adapt_validated_exposures(id) |
| action_type | TEXT | firewall_rule, patch, config_change, isolation |
| target | TEXT | What to apply the action to |
| status | TEXT | pending, approved, executed, failed, rolled_back |
| risk_reduction | REAL | Estimated risk reduction |
| approved_by | UUID | Who approved |
| executed_at | TIMESTAMPTZ | When executed |
| created_at | TIMESTAMPTZ | When created |

---

### adapt_metrics

Metrics from the Prove phase.

| Column | Type | Notes |
|---|---|---|
| id | UUID | Primary key |
| cycle_id | UUID | FK -> adapt_cycles(id) |
| metric_name | TEXT | Metric identifier |
| value | REAL | Metric value |
| unit | TEXT | Unit of measurement |
| scope | TEXT | Metric scope |
| recorded_at | TIMESTAMPTZ | When recorded |

---

## ADAPT Pro Extensions

### adapt_adversary_profiles

Adversary profiles for the War Room.

| Column | Type | Notes |
|---|---|---|
| id | UUID | Primary key |
| name | TEXT | Unique adversary name (e.g., COBALT SPIDER) |
| aliases | TEXT[] | Known aliases |
| origin_country | TEXT | Country of origin |
| motivation | TEXT | espionage, financial, disruption, hacktivism, unknown |
| sophistication | TEXT | nation-state, advanced, intermediate, basic |
| target_sectors | TEXT[] | Targeted sectors |
| description | TEXT | Profile description |
| active | BOOLEAN | Currently active flag |
| created_at | TIMESTAMPTZ | Creation time |
| updated_at | TIMESTAMPTZ | Last update |

**Indexes:** name, motivation, active

---

### adapt_adversary_techniques

MITRE ATT&CK techniques associated with adversary profiles.

| Column | Type | Notes |
|---|---|---|
| id | UUID | Primary key |
| profile_id | UUID | FK -> adapt_adversary_profiles(id) |
| technique_id | TEXT | MITRE ATT&CK ID (e.g., T1059.001) |
| technique_name | TEXT | Technique name |
| tactic | TEXT | MITRE tactic (e.g., execution) |
| platform | TEXT | Target platform (default Windows) |
| severity | TEXT | critical, high, medium, low |
| description | TEXT | Technique description |
| created_at | TIMESTAMPTZ | Creation time |

**Indexes:** profile_id, technique_id, tactic

---

### adapt_technique_coverage

Detection coverage status for MITRE techniques.

| Column | Type | Notes |
|---|---|---|
| id | UUID | Primary key |
| technique_id | TEXT | MITRE ATT&CK ID |
| coverage_status | TEXT | covered, partial, gap |
| detection_source | TEXT | What detects this |
| detection_rule_id | UUID | Link to detection rule |
| last_tested | TIMESTAMPTZ | Last test date |
| confidence | REAL | Detection confidence |
| notes | TEXT | Analyst notes |
| created_at | TIMESTAMPTZ | Creation time |
| updated_at | TIMESTAMPTZ | Last update |

**Indexes:** technique_id, coverage_status

---

### adapt_simulation_runs

Results from adversary simulation campaigns.

| Column | Type | Notes |
|---|---|---|
| id | UUID | Primary key |
| profile_id | UUID | FK -> adapt_adversary_profiles(id) |
| resilience_score | REAL | Overall resilience score 0.0-1.0 |
| techniques_tested | INTEGER | Count of techniques tested |
| techniques_detected | INTEGER | Count detected |
| techniques_blocked | INTEGER | Count blocked |
| gap_count | INTEGER | Count of gaps found |
| gaps | JSONB | Detailed gap information |
| recommendations | JSONB | Recommended improvements |
| run_by | UUID | Who ran the simulation |
| started_at | TIMESTAMPTZ | Start time |
| completed_at | TIMESTAMPTZ | Completion time |

**Indexes:** profile_id, resilience_score, started_at

---

### adapt_threat_forecasts

Predictive threat intelligence forecasts.

| Column | Type | Notes |
|---|---|---|
| id | UUID | Primary key |
| org_profile_id | UUID | FK -> adapt_org_profile(id) |
| threat_type | TEXT | Type of predicted threat |
| threat_name | TEXT | Threat name |
| probability | REAL | Probability 0.0-1.0 |
| impact_score | REAL | Estimated impact |
| time_horizon_days | INTEGER | Prediction window |
| rationale | TEXT | Why this is predicted |
| materialized | BOOLEAN | Did it actually happen |
| created_at | TIMESTAMPTZ | Forecast creation time |

---

### adapt_autopilot_config

Autopilot configuration (singleton per deployment).

| Column | Type | Notes |
|---|---|---|
| id | UUID | Primary key |
| enabled | BOOLEAN | Autopilot active |
| max_risk_threshold | REAL | Max risk before human escalation |
| auto_approve_low_risk | BOOLEAN | Auto-approve low-risk actions |
| cycle_interval_hours | INTEGER | Hours between cycles |
| kill_switch_active | BOOLEAN | Emergency stop flag |
| escalation_contacts | JSONB | Who to notify on escalation |
| created_at | TIMESTAMPTZ | Creation time |
| updated_at | TIMESTAMPTZ | Last update |

---

## Ontology & Knowledge Graph

### ontology_entity_types

Registry of entity types in the knowledge graph.

| Column | Type | Notes |
|---|---|---|
| id | UUID | Primary key |
| name | VARCHAR(100) | Unique type name |
| display_name | VARCHAR(200) | Human-readable name |
| description | TEXT | Type description |
| icon | VARCHAR(50) | UI icon name |
| color | VARCHAR(20) | UI color code |
| schema | JSONB | JSON Schema for entity properties |
| created_at | TIMESTAMPTZ | Creation time |

---

### ontology_entities

Universal entity store -- every node in the knowledge graph.

| Column | Type | Notes |
|---|---|---|
| id | UUID | Primary key |
| entity_type_id | UUID | FK -> ontology_entity_types(id) |
| name | VARCHAR(500) | Entity name |
| properties | JSONB | Entity properties (schema-validated) |
| confidence | DOUBLE PRECISION | Entity confidence score |
| source | VARCHAR(200) | Data source |
| first_seen | TIMESTAMPTZ | First observation |
| last_seen | TIMESTAMPTZ | Most recent observation |
| created_at | TIMESTAMPTZ | Creation time |
| updated_at | TIMESTAMPTZ | Last update |

**Indexes:** properties (GIN), entity_type_id, name

---

### ontology_relationships

Edges in the knowledge graph.

| Column | Type | Notes |
|---|---|---|
| id | UUID | Primary key |
| relationship_type_id | UUID | FK -> ontology_relationship_types(id) |
| source_entity_id | UUID | FK -> ontology_entities(id) |
| target_entity_id | UUID | FK -> ontology_entities(id) |
| weight | DOUBLE PRECISION | Relationship strength (default 1.0) |
| confidence | DOUBLE PRECISION | Confidence in this relationship |
| properties | JSONB | Relationship properties |
| evidence_ids | JSONB | Links to supporting evidence |
| first_seen | TIMESTAMPTZ | First observation |
| last_seen | TIMESTAMPTZ | Most recent observation |
| created_at | TIMESTAMPTZ | Creation time |

**Indexes:** source_entity_id, target_entity_id, relationship_type_id

---

### ontology_resolutions

Entity deduplication/resolution log.

| Column | Type | Notes |
|---|---|---|
| id | UUID | Primary key |
| source_entity_id | UUID | Entity being merged |
| target_entity_id | UUID | Entity being kept |
| strategy | VARCHAR(50) | Resolution strategy used |
| similarity_score | DOUBLE PRECISION | How similar the entities were |
| resolved_by | UUID | Who made the decision |
| resolved_at | TIMESTAMPTZ | When resolved |
| created_at | TIMESTAMPTZ | Creation time |

---

## GEOINT

### geo_targets

Tracked geospatial targets.

| Column | Type | Notes |
|---|---|---|
| id | UUID | Primary key |
| name | VARCHAR(300) | Target name |
| target_type | VARCHAR(50) | point, area, infrastructure |
| lat | DOUBLE PRECISION | Latitude |
| lon | DOUBLE PRECISION | Longitude |
| altitude_m | DOUBLE PRECISION | Altitude in meters |
| description | TEXT | Description |
| metadata | JSONB | Flexible metadata |
| status | VARCHAR(30) | active, inactive, archived |
| created_at | TIMESTAMPTZ | Creation time |
| updated_at | TIMESTAMPTZ | Last update |

**Indexes:** status, metadata (GIN)

---

### geo_positions

Position history for tracked targets.

| Column | Type | Notes |
|---|---|---|
| id | UUID | Primary key |
| target_id | UUID | FK -> geo_targets(id) |
| lat | DOUBLE PRECISION | Latitude |
| lon | DOUBLE PRECISION | Longitude |
| altitude_m | DOUBLE PRECISION | Altitude |
| speed_kmh | DOUBLE PRECISION | Speed in km/h |
| bearing_deg | DOUBLE PRECISION | Bearing in degrees |
| accuracy_m | DOUBLE PRECISION | Position accuracy |
| source | VARCHAR(100) | Data source |
| recorded_at | TIMESTAMPTZ | When position was recorded |

**Indexes:** target_id, recorded_at DESC

---

### geo_geofences

Virtual geographic boundaries with alerting.

| Column | Type | Notes |
|---|---|---|
| id | UUID | Primary key |
| name | VARCHAR(200) | Geofence name |
| fence_type | VARCHAR(30) | circle, polygon |
| center_lat | DOUBLE PRECISION | Circle center latitude |
| center_lon | DOUBLE PRECISION | Circle center longitude |
| radius_m | DOUBLE PRECISION | Circle radius in meters |
| polygon | JSONB | Polygon vertices |
| alert_on_enter | BOOLEAN | Alert when target enters |
| alert_on_exit | BOOLEAN | Alert when target exits |
| status | VARCHAR(30) | active, inactive |
| created_at | TIMESTAMPTZ | Creation time |

**Indexes:** polygon (GIN)

---

### geo_geofence_alerts

Alerts generated by geofence violations.

| Column | Type | Notes |
|---|---|---|
| id | UUID | Primary key |
| geofence_id | UUID | FK -> geo_geofences(id) |
| target_id | UUID | FK -> geo_targets(id) |
| alert_type | VARCHAR(20) | enter or exit |
| lat | DOUBLE PRECISION | Position at alert time |
| lon | DOUBLE PRECISION | Position at alert time |
| distance_m | DOUBLE PRECISION | Distance to fence boundary |
| acknowledged | BOOLEAN | Has been acknowledged |
| created_at | TIMESTAMPTZ | Alert time |

**Indexes:** geofence_id, target_id

---

## Mission Boards

### mission_boards

Collaborative analysis boards.

| Column | Type | Notes |
|---|---|---|
| id | UUID | Primary key |
| name | VARCHAR(300) | Board name |
| description | TEXT | Board description |
| status | VARCHAR(30) | active, archived |
| created_by | UUID | Creator |
| created_at | TIMESTAMPTZ | Creation time |
| updated_at | TIMESTAMPTZ | Last update |

---

### mission_hypotheses

Analyst hypotheses with evidence tracking.

| Column | Type | Notes |
|---|---|---|
| id | UUID | Primary key |
| board_id | UUID | FK -> mission_boards(id) |
| title | VARCHAR(300) | Hypothesis title |
| description | TEXT | Hypothesis description |
| status | VARCHAR(30) | proposed, testing, confirmed, rejected |
| confidence | DOUBLE PRECISION | Current confidence level |
| evidence_for | JSONB | Evidence supporting the hypothesis |
| evidence_against | JSONB | Evidence against the hypothesis |
| created_by | UUID | Who proposed it |
| created_at | TIMESTAMPTZ | Creation time |
| updated_at | TIMESTAMPTZ | Last update |

**Indexes:** board_id, evidence_for (GIN), evidence_against (GIN)

---

## NL Query Engine

### nlq_templates

Maps natural language patterns to parameterized SQL.

| Column | Type | Notes |
|---|---|---|
| id | UUID | Primary key |
| name | VARCHAR(200) | Template name |
| pattern | VARCHAR(1000) | Regex pattern to match queries |
| intent | VARCHAR(100) | Intent category (count, list, trend, etc.) |
| sql_template | TEXT | Parameterized SQL query |
| parameters | JSONB | Parameter definitions |
| examples | TEXT[] | Example natural language queries |
| priority | INTEGER | Matching priority (higher = first) |
| enabled | BOOLEAN | Template active |
| created_at | TIMESTAMPTZ | Creation time |

**Indexes:** intent

---

### nlq_queries

Log of every natural language query and its outcome.

| Column | Type | Notes |
|---|---|---|
| id | UUID | Primary key |
| user_id | UUID | Who asked |
| raw_text | TEXT | Original question |
| parsed_intent | VARCHAR(100) | Detected intent |
| generated_sql | TEXT | SQL that was generated |
| template_id | UUID | FK -> nlq_templates(id) |
| result_count | INTEGER | Number of results |
| execution_time_ms | INTEGER | Query execution time |
| success | BOOLEAN | Did it work |
| error_message | TEXT | Error if it failed |
| created_at | TIMESTAMPTZ | Query time |

**Indexes:** user_id, parsed_intent

---

## AI Pipeline

### ai_pipelines

AI model pipeline definitions.

| Column | Type | Notes |
|---|---|---|
| id | UUID | Primary key |
| name | VARCHAR(200) | Pipeline name |
| description | TEXT | Description |
| pipeline_type | VARCHAR(50) | inference, training, evaluation |
| steps | JSONB | Pipeline step definitions |
| schedule | VARCHAR(100) | Cron schedule |
| enabled | BOOLEAN | Pipeline active |
| created_by | UUID | Creator |
| created_at | TIMESTAMPTZ | Creation time |
| updated_at | TIMESTAMPTZ | Last update |

---

## Streaming

### stream_sources

Real-time data ingestion sources.

| Column | Type | Notes |
|---|---|---|
| id | UUID | Primary key |
| name | VARCHAR(200) | Source name |
| source_type | VARCHAR(50) | syslog, kafka, webhook, file |
| config | JSONB | Source configuration |
| status | VARCHAR(30) | active, paused, error |
| events_received | BIGINT | Total events received |
| last_event_at | TIMESTAMPTZ | Last event time |
| created_at | TIMESTAMPTZ | Creation time |

---

## Threat Intelligence

### ti_threat_feeds

Threat intelligence feed configurations.

| Column | Type | Notes |
|---|---|---|
| id | UUID | Primary key |
| name | TEXT | Feed name |
| feed_type | TEXT | otx, misp, stix, csv |
| url | TEXT | Feed URL |
| api_key_ref | TEXT | Reference to stored API key |
| enabled | BOOLEAN | Feed active |
| poll_interval_secs | INTEGER | Poll frequency (default 3600) |
| last_poll_at | TIMESTAMPTZ | Last successful poll |
| created_at | TIMESTAMPTZ | Creation time |

---

### indicators_of_compromise

IOC records with confidence scoring and expiry.

| Column | Type | Notes |
|---|---|---|
| id | UUID | Primary key |
| feed_id | UUID | FK -> ti_threat_feeds(id) |
| ioc_type | TEXT | ip, domain, hash, url, email |
| value | TEXT | The indicator value |
| confidence | TEXT | high, medium, low, unknown |
| threat_actor | TEXT | Associated threat actor |
| first_seen | TIMESTAMPTZ | First observation |
| last_seen | TIMESTAMPTZ | Most recent observation |
| expiry_at | TIMESTAMPTZ | When IOC expires |
| tags | JSONB | Classification tags |
| created_at | TIMESTAMPTZ | Creation time |

**Indexes:** (ioc_type, value), confidence

---

## Incident Response

### ir_incidents

Active incident tracking.

| Column | Type | Notes |
|---|---|---|
| id | UUID | Primary key |
| campaign_id | UUID | FK -> campaigns(id) |
| title | TEXT | Incident title |
| description | TEXT | Full description |
| phase | TEXT | detection, containment, eradication, recovery, lessons_learned |
| priority | TEXT | p1, p2, p3, p4 |
| lead_analyst | TEXT | Assigned analyst |
| affected_systems | JSONB | List of affected systems |
| created_at | TIMESTAMPTZ | Incident creation time |
| resolved_at | TIMESTAMPTZ | Resolution time |

---

### ir_playbooks

Incident response playbook templates.

| Column | Type | Notes |
|---|---|---|
| id | UUID | Primary key |
| name | TEXT | Playbook name |
| incident_type | TEXT | Type of incident this handles |
| steps | JSONB | Ordered step definitions |
| estimated_duration_mins | INTEGER | Expected time to complete |
| auto_actions | JSONB | Automated actions to take |
| created_at | TIMESTAMPTZ | Creation time |

---

### containment_actions

Actions taken to contain incidents.

| Column | Type | Notes |
|---|---|---|
| id | UUID | Primary key |
| incident_id | UUID | FK -> ir_incidents(id) |
| action_type | TEXT | isolate_host, block_ip, disable_account, etc. |
| target | TEXT | What was targeted |
| status | TEXT | pending, executed, rolled_back |
| executed_by | TEXT | Who executed |
| executed_at | TIMESTAMPTZ | Execution time |
| rolled_back | BOOLEAN | Has been rolled back |
| created_at | TIMESTAMPTZ | Creation time |

---

## SOAR

### soar_playbooks

SOAR automation playbooks.

| Column | Type | Notes |
|---|---|---|
| id | UUID | Primary key |
| name | TEXT | Playbook name |
| description | TEXT | Description |
| status | TEXT | draft, active, suspended, archived |
| trigger_type | TEXT | alert, schedule, manual, webhook |
| trigger_config | JSONB | Trigger configuration |
| version | INTEGER | Playbook version |
| author | TEXT | Author |
| approved_by | TEXT | Approver |
| created_at | TIMESTAMPTZ | Creation time |
| updated_at | TIMESTAMPTZ | Last update |

**Indexes:** status

---

### soar_executions

Playbook execution records.

| Column | Type | Notes |
|---|---|---|
| id | UUID | Primary key |
| playbook_id | UUID | FK -> soar_playbooks(id) |
| trigger_event | JSONB | What triggered the execution |
| status | TEXT | running, completed, failed, cancelled |
| started_at | TIMESTAMPTZ | Start time |
| completed_at | TIMESTAMPTZ | Completion time |
| result | JSONB | Execution result |

**Indexes:** status, playbook_id

---

## Workflow Engine

### workflow_templates

Reusable workflow templates.

| Column | Type | Notes |
|---|---|---|
| id | UUID | Primary key |
| name | TEXT | Template name |
| description | TEXT | Description |
| trigger_type | TEXT | manual, event, schedule, webhook |
| steps | JSONB | Ordered step definitions |
| variables | JSONB | Template variables |
| created_by | UUID | Creator |
| is_active | BOOLEAN | Template active |
| version | INT | Template version |
| created_at | TIMESTAMPTZ | Creation time |
| updated_at | TIMESTAMPTZ | Last update |

---

### workflow_runs

Individual workflow executions.

| Column | Type | Notes |
|---|---|---|
| id | UUID | Primary key |
| template_id | UUID | FK -> workflow_templates(id) |
| status | TEXT | pending, running, completed, failed, cancelled |
| started_at | TIMESTAMPTZ | Start time |
| completed_at | TIMESTAMPTZ | Completion time |
| started_by | UUID | Who triggered it |
| variables | JSONB | Runtime variable values |
| error | TEXT | Error message if failed |
| current_step | INT | Current step index |
| created_at | TIMESTAMPTZ | Creation time |
| updated_at | TIMESTAMPTZ | Last update |

---

## Command Center

### command_widgets

Dashboard widgets for the command center.

| Column | Type | Notes |
|---|---|---|
| id | UUID | Primary key |
| name | TEXT | Widget name |
| widget_type | TEXT | chart, table, metric, map |
| config | JSONB | Widget configuration |
| position_x | INT | Grid position X |
| position_y | INT | Grid position Y |
| width | INT | Widget width |
| height | INT | Widget height |
| created_by | UUID | Creator |
| created_at | TIMESTAMPTZ | Creation time |

---

## Schema Design Principles

Throughout all 1,100+ tables, these patterns are consistent:

1. **UUIDv7 primary keys** -- Time-sortable, globally unique, generated with `gen_random_uuid()`
2. **TIMESTAMPTZ for all timestamps** -- Always stored with timezone (UTC)
3. **JSONB for flexible data** -- GIN indexes on all JSONB columns used for querying
4. **Foreign keys with ON DELETE CASCADE** -- Cascading deletes for child records
5. **CHECK constraints** -- Enum values enforced at the database level
6. **IF NOT EXISTS** -- All CREATE TABLE and CREATE INDEX statements are idempotent
7. **Append-only audit** -- audit_events table has trigger preventing mutation
8. **Dual hashing** -- Evidence uses both BLAKE3 (speed) and SHA-256 (compatibility)
9. **Soft deletes** -- Status flags preferred over hard deletes where appropriate
10. **Partial indexes** -- Used on nullable columns (e.g., cwe_id, cve_id) to save space

---

(c) 2026 Playseat -- All Rights Reserved | Proprietary and Confidential
