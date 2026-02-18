# Chapter 15: AI Pipeline -- Teaching Playseat to Think Like Clara

**Playseat Advanced Field Manual -- Book 2**

---

> "She didn't just analyze patterns. She *became* the pattern. And when she
> disappeared, the only way to find her was to teach a machine to think the
> way she thought."

---

## 15.1 -- The Notebook

**2026-02-04, 02:17 UTC. Building 9, Sub-level 2. My desk.**

I haven't slept in thirty-one hours. The coffee's gone cold twice. My eyes are
raw from staring at the same four monitors, the same Playseat dashboards, the
same empty signal space where Clara Dubois used to leave breadcrumbs.

On my desk, next to the cold coffee and the crumpled pack of Gitanes she left
behind six weeks ago: her field notebook. Not the digital one -- the leather-bound
one she carried everywhere, the one she forgot at my apartment the last night
we were together in Paris. 127 pages of her handwriting. Cryptographic shorthand,
analytical frameworks, connection maps drawn in blue ink. Every page a window
into how she thought.

I'd been staring at PHANTOM MERCY data for weeks. The child trafficking network
embedded in humanitarian aid corridors. Clara's investigation. Clara's obsession.
Clara's disappearance. And I kept hitting the same wall: too many data points,
too many false correlations, too many threads that led nowhere. The alert queues
were drowning me -- 10,247 unprocessed signals from the past 48 hours alone. Three
analysts on shift. Average triage time: four minutes per alert. Quick math: 683
hours of work sitting in a queue that would receive another 8,000 before morning.

That's when I looked at her notebook. Really looked at it.

Page 47. She'd drawn a triangle with three words at the vertices: *Frequency.
Proximity. Anomaly.* Underneath, in her precise cursive: *"When everything is
noise, find the thing that doesn't repeat. That's the signal."*

I closed my eyes. I could hear her voice saying it. That night in the
seventh arrondissement, the rain on the window of the restaurant on Rue Cler,
the bottle of Chateauneuf-du-Pape between us. She was explaining how she'd
cracked a DGSE signals case that had stalled for eight months. Pattern
recognition, she said, isn't about finding patterns. It's about finding the
*absence* of patterns.

"The human brain sees faces in clouds," she'd said, twirling her wine glass.
"It *wants* to see patterns. The trick is to teach yourself to see the place
where patterns *should* be but aren't. That's where the truth hides."

I opened my eyes. Stared at the notebook. And I started building the pipeline.

Not because I thought machine learning was a silver bullet -- I've seen too many
"AI-powered" security products that are just regex with a marketing budget. But
because Clara had a method, and methods can be encoded, and if I could teach
Playseat to triage signals the way she triaged them, I could process her
investigation data at scale. I could find what she found. I could follow where
she went.

I could find her.

---

## 15.2 -- Clara's Method, Encoded

The AI subsystem in Playseat isn't a monolith. It's four crates that compose
into a pipeline. But tonight, I wasn't thinking about architecture. I was
thinking about Clara's triangle: Frequency. Proximity. Anomaly.

```
svc-ai          -- Provider abstraction, triage engine, correlation
svc-aiagent     -- Autonomous agent framework (orchestrator, memory, tools)
svc-api/routes  -- HTTP endpoints exposing AI capabilities
migrations/     -- ai_pipelines, ai_pipeline_runs, ai_model_registry, ai_analyses
```

The pipeline follows a three-stage flow. I redesigned it around her analytical
framework:

```
  INGEST              CLASSIFY              PRIORITIZE
  ------              --------              ----------
  Raw signals   ->    Clara's triangle  ->  Priority queue
  PHANTOM data  ->    FP detection      ->  Analyst worklist
  OSINT feeds   ->    Pattern absence   ->  Anomaly detection
  Mesh intel    ->    NLQ enrichment    ->  Investigation leads
```

Each stage is independent. You can run classification without prioritization.
You can feed the prioritizer manually. The pipeline is a suggestion engine,
not a decision engine -- every critical action requires human confirmation.
Clara would've insisted on that. She didn't trust machines to make decisions
about people's lives. Neither do I.

Here's the database schema backing the pipeline:

```sql
-- AI Pipeline definitions
CREATE TABLE IF NOT EXISTS ai_pipelines (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name            TEXT NOT NULL,
    description     TEXT,
    pipeline_type   TEXT NOT NULL DEFAULT 'triage',
    stages          JSONB NOT NULL DEFAULT '[]',
    model_config    JSONB NOT NULL DEFAULT '{}',
    schedule        TEXT,  -- cron expression, NULL = manual only
    enabled         BOOLEAN NOT NULL DEFAULT true,
    created_by      UUID NOT NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Pipeline execution history
CREATE TABLE IF NOT EXISTS ai_pipeline_runs (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    pipeline_id     UUID NOT NULL REFERENCES ai_pipelines(id),
    status          TEXT NOT NULL DEFAULT 'running',
    started_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at    TIMESTAMPTZ,
    items_processed INTEGER NOT NULL DEFAULT 0,
    items_flagged   INTEGER NOT NULL DEFAULT 0,
    items_dismissed INTEGER NOT NULL DEFAULT 0,
    error_count     INTEGER NOT NULL DEFAULT 0,
    tokens_used     INTEGER NOT NULL DEFAULT 0,
    cost_usd        NUMERIC(10,4) NOT NULL DEFAULT 0,
    summary         JSONB,
    created_by      UUID NOT NULL
);

-- Model registry
CREATE TABLE IF NOT EXISTS ai_model_registry (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name            TEXT NOT NULL UNIQUE,
    version         TEXT NOT NULL,
    model_type      TEXT NOT NULL,  -- 'classifier', 'anomaly', 'nlp', 'correlation'
    provider        TEXT NOT NULL,  -- 'claude', 'openai', 'local', 'custom'
    accuracy        NUMERIC(5,4),
    precision_score NUMERIC(5,4),
    recall_score    NUMERIC(5,4),
    f1_score        NUMERIC(5,4),
    training_data   JSONB,
    parameters      JSONB NOT NULL DEFAULT '{}',
    deployed        BOOLEAN NOT NULL DEFAULT false,
    deployed_at     TIMESTAMPTZ,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Individual AI analysis results
CREATE TABLE IF NOT EXISTS ai_analyses (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    campaign_id     UUID,
    finding_id      UUID,
    analysis_type   TEXT NOT NULL,
    provider        TEXT NOT NULL,
    model           TEXT NOT NULL,
    input_context   JSONB,
    result          JSONB,
    status          TEXT NOT NULL DEFAULT 'pending',
    confidence      NUMERIC(5,4),
    tokens_used     INTEGER NOT NULL DEFAULT 0,
    cost_usd        NUMERIC(10,6) NOT NULL DEFAULT 0,
    created_by      UUID NOT NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at    TIMESTAMPTZ
);
```

I stared at those tables for a long time. Cold infrastructure. Columns and
constraints. But somewhere in those rows, I was going to encode the way Clara
Dubois saw the world. And then I was going to point it at every scrap of
PHANTOM MERCY intelligence we had and ask: *Where would she go next?*

---

## 15.3 -- The Provider Abstraction (Or: Building a Brain That Can Switch Bodies)

The first design decision was making the AI provider pluggable. I didn't want
to be locked into any single vendor. Models change, pricing changes, and for
this particular investigation -- tracking a DGSE deep-cover agent through a
trafficking network -- I needed the ability to run inference locally, air-gapped,
no external API calls. If PHANTOM MERCY had compromised cloud providers, I
couldn't have my analysis traffic leaking to them.

The `AiService` trait is the foundation:

```rust
// crates/svc-ai/src/provider.rs

/// Response from an AI provider.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AiResponse {
    pub content: String,
    pub tokens_input: u32,
    pub tokens_output: u32,
    pub model: String,
    pub provider: String,
}

/// Trait for AI model providers.
pub trait AiService: Send + Sync {
    fn analyze(
        &self,
        system_prompt: &str,
        user_prompt: &str,
    ) -> Pin<Box<dyn Future<Output = Result<AiResponse, AppError>> + Send + '_>>;

    fn provider_name(&self) -> &str;
    fn model_name(&self) -> &str;
    fn cost_per_million_tokens(&self) -> (f64, f64);
}
```

Four implementations ship with the platform:

| Provider | Use Case | Cost/1M tokens (in/out) |
|----------|----------|-------------------------|
| `ClaudeProvider` | Production triage, narrative generation | $3 / $15 |
| `OpenAiProvider` | Alternative production, GPT-4o | $5 / $15 |
| `LocalProvider` | Air-gapped deployments (Ollama/vLLM) | $0 / $0 |
| `MockProvider` | Testing, CI pipelines | $0 / $0 |

For the PHANTOM MERCY analysis, I used the local provider exclusively. Every
query about Clara, every inference about trafficking routes, every pattern match
against aid network data -- all of it stayed on my hardware. No cloud. No logs
I didn't control.

The Claude provider, for when you can trust the wire:

```rust
pub struct ClaudeProvider {
    pub api_key: String,
    pub model: String,
    pub endpoint: String,
    client: reqwest::Client,
}

impl ClaudeProvider {
    pub fn new(api_key: String, model: Option<String>, endpoint: Option<String>) -> Self {
        Self {
            api_key,
            model: model.unwrap_or_else(|| "claude-sonnet-4-5-20250929".into()),
            endpoint: endpoint
                .unwrap_or_else(|| "https://api.anthropic.com/v1/messages".into()),
            client: reqwest::Client::new(),
        }
    }
}

impl AiService for ClaudeProvider {
    fn analyze(
        &self,
        system_prompt: &str,
        user_prompt: &str,
    ) -> Pin<Box<dyn Future<Output = Result<AiResponse, AppError>> + Send + '_>> {
        let system = system_prompt.to_string();
        let user = user_prompt.to_string();
        Box::pin(async move {
            let body = ClaudeRequest {
                model: self.model.clone(),
                max_tokens: 4096,
                system,
                messages: vec![ClaudeMessage {
                    role: "user".into(),
                    content: user,
                }],
            };

            let resp = self.client
                .post(&self.endpoint)
                .header("x-api-key", &self.api_key)
                .header("anthropic-version", "2023-06-01")
                .header("content-type", "application/json")
                .json(&body)
                .send()
                .await
                .map_err(|e| AppError::internal(
                    format!("claude API request failed: {e}")
                ))?;

            if !resp.status().is_success() {
                let status = resp.status().as_u16();
                let text = resp.text().await.unwrap_or_default();
                return Err(AppError::internal(
                    format!("claude API returned {status}: {text}")
                ));
            }

            let api_resp: ClaudeApiResponse = resp.json().await
                .map_err(|e| AppError::internal(
                    format!("claude response parse failed: {e}")
                ))?;

            let content = api_resp.content.first()
                .map(|c| c.text.clone())
                .unwrap_or_default();

            Ok(AiResponse {
                content,
                tokens_input: api_resp.usage.input_tokens,
                tokens_output: api_resp.usage.output_tokens,
                model: self.model.clone(),
                provider: "claude".into(),
            })
        })
    }

    fn cost_per_million_tokens(&self) -> (f64, f64) {
        (3.0, 15.0)  // Sonnet 4.5 pricing
    }
}
```

And the local provider -- the one I actually used that night:

```rust
impl AiService for LocalProvider {
    fn analyze(&self, system_prompt: &str, user_prompt: &str)
        -> Pin<Box<dyn Future<Output = Result<AiResponse, AppError>> + Send + '_>>
    {
        let system = system_prompt.to_string();
        let user = user_prompt.to_string();
        Box::pin(async move {
            let body = serde_json::json!({
                "model": self.model,
                "messages": [
                    { "role": "system", "content": system },
                    { "role": "user", "content": user }
                ],
                "stream": false
            });

            let resp = self.client
                .post(format!("{}/api/chat", self.endpoint))
                .json(&body)
                .send()
                .await
                .map_err(|e| AppError::internal(
                    format!("local model request failed: {e}")
                ))?;

            let json: serde_json::Value = resp.json().await
                .map_err(|e| AppError::internal(
                    format!("local model parse failed: {e}")
                ))?;

            let content = json["message"]["content"]
                .as_str()
                .unwrap_or("")
                .to_string();

            Ok(AiResponse {
                content,
                tokens_input: json["prompt_eval_count"].as_u64().unwrap_or(0) as u32,
                tokens_output: json["eval_count"].as_u64().unwrap_or(0) as u32,
                model: self.model.clone(),
                provider: "local".into(),
            })
        })
    }

    fn cost_per_million_tokens(&self) -> (f64, f64) {
        (0.0, 0.0)  // local = free, and private
    }
}
```

Air-gapped. Private. No one could see what I was searching for. Not PHANTOM
MERCY. Not whoever took Clara. Not even my own chain of command -- not yet.

---

## 15.4 -- The Triage Engine (Teaching Playseat Clara's Instincts)

**02:48 UTC.**

The triage engine is where the rubber meets the road. It takes a raw finding
and produces a structured assessment: suggested severity, confidence score,
false positive likelihood, and reasoning. But I'd been running it stock for
months, and stock wasn't good enough. Not for this.

I needed to teach it Clara's instincts.

I started with her notebook. Page 23: her criteria for evaluating trafficking
signals. She had a scoring system -- elegant, ruthless in its efficiency:

1. **Is there a child involved?** If yes, severity is always critical. No
   exceptions. No "medium."
2. **Does the financial trail touch a legitimate aid organization?** If yes,
   confidence increases -- it means the network is sophisticated enough to
   embed itself in real operations.
3. **Is the geographic pattern consistent with known routes?** If yes, lower
   false-positive likelihood.
4. **Is there a timing correlation with aid shipments?** If yes, this isn't
   noise. This is operational tempo.

I encoded all of it:

```rust
// crates/svc-ai/src/triage.rs

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TriageResult {
    pub suggested_severity: Severity,
    pub confidence: f64,
    pub false_positive_likelihood: f64,
    pub reasoning: String,
    pub tokens_used: u32,
}

pub struct TriageEngine<'a> {
    provider: &'a dyn AiService,
}

impl<'a> TriageEngine<'a> {
    pub async fn triage_finding(
        &self,
        title: &str,
        description: &str,
        source_tool: &str,
        current_severity: Severity,
    ) -> Result<TriageResult, AppError> {
        let system_prompt = "You are a security analyst performing finding triage. \
            Analyze the finding and respond with ONLY a JSON object \
            (no markdown, no explanation) with these fields: \
            severity (one of: info, low, medium, high, critical), \
            confidence (0.0-1.0), \
            false_positive_likelihood (0.0-1.0), \
            reasoning (brief explanation).";

        let user_prompt = format!(
            "Finding: {title}\nDescription: {description}\n\
             Source: {source_tool}\nCurrent severity: {current_severity:?}"
        );

        let response = self.provider.analyze(system_prompt, &user_prompt).await?;
        parse_triage_response(&response)
    }

    pub async fn suggest_remediation(
        &self,
        title: &str,
        description: &str,
        cwe_id: Option<&str>,
    ) -> Result<RemediationSuggestion, AppError> {
        let system_prompt = "You are a security engineer generating remediation steps. \
            Respond with ONLY a JSON object (no markdown) with these fields: \
            steps (array of strings, ordered remediation steps), \
            priority (one of: immediate, high, medium, low), \
            effort (one of: minimal, moderate, significant, major), \
            reasoning (brief explanation).";

        let cwe_str = cwe_id.map(|c| format!("\nCWE: {c}")).unwrap_or_default();
        let user_prompt = format!(
            "Finding: {title}\nDescription: {description}{cwe_str}"
        );

        let response = self.provider.analyze(system_prompt, &user_prompt).await?;
        parse_remediation_response(&response)
    }
}
```

The system prompt is carefully tuned. I spent two weeks testing different prompts
against a corpus of 5,000 labeled findings from Clara's historical casework.
Key learnings:

1. **"ONLY a JSON object"** prevents markdown wrapping that breaks parsing
2. Including the **source tool** improves accuracy by 12% -- the model learns
   that OSINT feeds tend to over-report while Clara's manual notes are surgical
3. Including the **current severity** prevents the model from ignoring analyst
   context
4. The **confidence field** is essential -- it tells us when the model is unsure

I fed the first PHANTOM MERCY signal through:

```bash
# Triage a PHANTOM MERCY finding
curl -s -X POST http://localhost:3000/ai/triage \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "finding_id": "019505e0-0000-7000-8000-000000000042",
    "title": "Financial anomaly in Marseille aid corridor",
    "description": "Wire transfers totaling EUR 847,000 routed through Fondation Lumiere (registered Marseille charity) to shell accounts in Nicosia. Timing correlates with three UNHCR shipments to Lebanon. Clara Dubois flagged this entity 6 weeks ago.",
    "source_tool": "mesh_intel",
    "current_severity": "medium"
  }' | jq .
```

Response:

```json
{
  "id": "01950a3f-8e21-7d4a-b012-3456789abcde",
  "finding_id": "019505e0-0000-7000-8000-000000000042",
  "suggested_severity": "critical",
  "confidence": 0.95,
  "false_positive_likelihood": 0.05,
  "reasoning": "Financial trail touching legitimate aid organization with timing correlation to humanitarian shipments. Pattern consistent with known trafficking-embedded logistics. Previous analyst flagging (Clara Dubois) adds strong corroboration. Escalating from medium to critical.",
  "provider": "local",
  "model": "mixtral-8x22b",
  "tokens_used": 287
}
```

The model upgraded this from medium to critical. Clara's name in the context --
the fact that she'd flagged this entity before vanishing -- pushed the confidence
to 0.95. The machine was starting to see what she saw.

My hands were shaking. Not from caffeine. From the realization that the AI had
just confirmed what I'd been afraid to believe: Clara hadn't been investigating
a cold case. She'd found an active, well-funded trafficking pipeline hiding
inside humanitarian operations. And someone had noticed.

---

## 15.5 -- The Model Registry (Cataloging Clara's Ghosts)

Every model used in the pipeline is registered and versioned. That night I
registered three new models, each trained on a different slice of Clara's
analytical legacy:

```sql
-- Query the model registry
SELECT name, version, model_type, provider,
       accuracy, precision_score, recall_score, f1_score,
       deployed, deployed_at
FROM ai_model_registry
WHERE deployed = true
ORDER BY name;
```

Expected output:

```
 name                    | version | model_type   | provider | accuracy | precision | recall | f1     | deployed_at
-------------------------+---------+--------------+----------+----------+-----------+--------+--------+------------------------
 anomaly_detector        | 1.4.0   | anomaly      | local    | 0.8901   | 0.8567    | 0.9234 | 0.8888 | 2026-02-14 12:00:00+00
 dubois_pattern_matcher  | 0.1.0   | classifier   | local    | 0.8734   | 0.9102    | 0.8412 | 0.8744 | 2026-02-04 02:48:00+00
 nlp_extractor           | 1.2.0   | nlp          | claude   | 0.9156   | 0.8978    | 0.9334 | 0.9153 | 2026-02-16 10:00:00+00
 phantom_route_predictor | 0.1.0   | correlation  | local    | 0.7823   | 0.8245    | 0.7401 | 0.7801 | 2026-02-04 03:15:00+00
 threat_classifier       | 2.1.0   | classifier   | claude   | 0.9412   | 0.9234    | 0.9587 | 0.9407 | 2026-02-15 08:00:00+00
```

`dubois_pattern_matcher`. I stared at the name I'd given it. Her name in a
database column. It felt like a violation. It felt like the only thing I could do.

Key metrics for the models I was using on PHANTOM MERCY:

| Model | Accuracy | Precision | Recall | F1 | Provider |
|-------|----------|-----------|--------|-----|----------|
| `dubois_pattern_matcher` | 87.34% | 91.02% | 84.12% | 87.44% | Local |
| `phantom_route_predictor` | 78.23% | 82.45% | 74.01% | 78.01% | Local |
| `threat_classifier` | 94.12% | 92.34% | 95.87% | 94.07% | Claude |
| `anomaly_detector` | 89.01% | 85.67% | 92.34% | 88.88% | Local |
| `nlp_extractor` | 91.56% | 89.78% | 93.34% | 91.53% | Claude |

The Dubois pattern matcher had high precision (91%) but lower recall (84%). It
was picky, like her. It didn't flag things unless it was sure. The phantom
route predictor was rougher -- 78% accuracy -- because predicting trafficking
route evolution is genuinely harder than classifying known threat patterns.

Both ran locally. Both stayed on my hardware. Both used training data derived
from her investigation notes.

Model performance over time:

```sql
-- Model accuracy trend over last 30 days
SELECT
    DATE_TRUNC('day', completed_at) AS day,
    model,
    COUNT(*) AS total_analyses,
    AVG(confidence) AS avg_confidence,
    SUM(tokens_used) AS daily_tokens,
    SUM(cost_usd) AS daily_cost
FROM ai_analyses
WHERE completed_at > NOW() - INTERVAL '30 days'
  AND status = '"completed"'
GROUP BY DATE_TRUNC('day', completed_at), model
ORDER BY day DESC, model;
```

---

## 15.6 -- Training Jobs (Feeding the Machine Her Mind)

**03:22 UTC.**

Model performance degrades over time as patterns evolve. But I had a unique
problem: I wasn't tracking a threat actor that changed tactics quarterly. I
was trying to predict the behavior of a specific human being. Clara. And Clara
didn't degrade -- she adapted. She improvised. She was smarter than any model
I could build.

So I kept feeding it fresh data. Every scrap of her casework I could find.

```bash
# Create a training job using Clara's verified findings
curl -s -X POST http://localhost:3000/ai/training \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "model_name": "dubois_pattern_matcher",
    "training_data_query": "SELECT title, description, severity, source_tool FROM findings WHERE verified = true AND created_by = '\''019505e0-clara-dubois-analyst-id'\'' AND found_at > NOW() - INTERVAL '\''180 days'\''",
    "parameters": {
      "epochs": 10,
      "learning_rate": 0.001,
      "batch_size": 32,
      "validation_split": 0.2
    }
  }' | jq .
```

```json
{
  "job_id": "01950a3f-4444-7000-8000-000000000004",
  "model_name": "dubois_pattern_matcher",
  "status": "queued",
  "estimated_duration_mins": 45,
  "training_samples": 1847,
  "validation_samples": 462
}
```

1,847 training samples. Every finding Clara had verified in the past six months.
Every signal she'd personally confirmed. Every pattern she'd marked as real.
Her analytical judgment, crystallized into training data.

The training pipeline pulls verified findings as ground truth. Only findings
that analysts have manually confirmed (verified = true) feed into training data.
This creates a virtuous cycle: analysts verify findings, which improve the model,
which produces better triage, which means fewer findings need manual verification.

But in this case, there was no cycle. There was just me, feeding Clara's ghost
into a machine, hoping the machine would tell me where she'd gone.

---

## 15.7 -- The 10,000-to-47 Scenario (Finding Clara's Needles)

Let me walk through what happened when I pointed the Clara-trained pipeline at
the full PHANTOM MERCY dataset.

### Phase 1: Ingest

I loaded everything. Six weeks of accumulated intelligence from every source
we had on PHANTOM MERCY. The numbers were staggering:

```sql
-- What the ingest stage received
SELECT source_tool, COUNT(*) as alert_count,
       AVG(CASE WHEN severity = '"critical"' THEN 4
                WHEN severity = '"high"' THEN 3
                WHEN severity = '"medium"' THEN 2
                WHEN severity = '"low"' THEN 1
                ELSE 0 END) AS avg_severity_score
FROM findings
WHERE found_at BETWEEN '2025-12-20' AND '2026-02-04'
  AND campaign_id = '019505e0-phantom-mercy-campaign'
GROUP BY source_tool
ORDER BY alert_count DESC;
```

```
 source_tool    | alert_count | avg_severity_score
----------------+-------------+--------------------
 osint_feeds    |        6842 |               1.2
 mesh_intel     |        2156 |               2.1
 financial_mon  |         891 |               1.8
 clara_notes    |         358 |               2.9
```

Clara's notes. 358 entries. Average severity 2.9 -- the highest of any source.
She wasn't generating noise. Every signal she'd recorded meant something.

### Phase 2: Classify

I ran the Dubois-trained pipeline against all 10,247 findings:

```bash
# Trigger pipeline run
curl -s -X POST http://localhost:3000/ai/pipelines/run \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "pipeline_id": "01950a3f-5555-7000-8000-000000000005",
    "scope": {
      "time_range": {
        "start": "2025-12-20T00:00:00Z",
        "end": "2026-02-04T03:00:00Z"
      },
      "source_tools": ["osint_feeds", "mesh_intel", "financial_mon", "clara_notes"],
      "model_override": "dubois_pattern_matcher"
    }
  }' | jq .
```

The run completed in 8 minutes 42 seconds. I watched every second tick by.

```json
{
  "run_id": "01950a3f-6666-7000-8000-000000000006",
  "pipeline_id": "01950a3f-5555-7000-8000-000000000005",
  "status": "completed",
  "started_at": "2026-02-04T03:30:00Z",
  "completed_at": "2026-02-04T03:38:42Z",
  "items_processed": 10247,
  "items_flagged": 47,
  "items_dismissed": 10200,
  "error_count": 0,
  "tokens_used": 1247832,
  "cost_usd": 0.00,
  "summary": {
    "severity_distribution": {
      "critical": 3,
      "high": 12,
      "medium": 32,
      "dismissed_as_fp": 8914,
      "dismissed_as_info": 1286
    },
    "top_patterns": [
      "Financial routing through Marseille-registered charities",
      "Timing correlation between aid shipments and wire transfers",
      "Encrypted communication bursts preceding cargo movements"
    ]
  }
}
```

10,247 signals became 47 actionable items. Cost: $0.00 -- all local inference.

And those top patterns. Look at them. Marseille charities. Aid shipment timing.
Encrypted comms before cargo movements. Clara's triangle: Frequency. Proximity.
Anomaly. The machine had learned to think like her.

### Phase 3: Prioritize

The 47 flagged items were ranked:

```sql
-- Analyst worklist after pipeline
SELECT
    f.id,
    f.title,
    aa.result->>'suggested_severity' AS ai_severity,
    (aa.result->>'confidence')::float AS confidence,
    (aa.result->>'false_positive_likelihood')::float AS fp_likelihood,
    aa.result->>'reasoning' AS reasoning
FROM findings f
JOIN ai_analyses aa ON aa.finding_id = f.id
WHERE aa.result->>'suggested_severity' IN ('critical', 'high', 'medium')
  AND (aa.result->>'false_positive_likelihood')::float < 0.3
  AND aa.created_at > '2026-02-04T03:30:00Z'
ORDER BY
    CASE aa.result->>'suggested_severity'
        WHEN 'critical' THEN 1
        WHEN 'high' THEN 2
        WHEN 'medium' THEN 3
    END,
    (aa.result->>'confidence')::float DESC
LIMIT 50;
```

The three critical findings made my blood go cold:

1. **Fondation Lumiere wire transfers spiking 400% in January** -- the charity
   Clara had flagged before she disappeared
2. **Encrypted satellite phone traffic from three Marseille locations** --
   burst pattern matching pre-operational staging
3. **Clara's last verified finding: a cargo manifest anomaly on the Marseille-
   Beirut ferry route** -- filed 12 hours before she went dark

Number three. Her last finding. Filed January 15th. The same day she stopped
responding to my messages.

All three were connected. The pipeline saw it because I'd taught it to see it.
Clara had been mapping an active trafficking pipeline moving children through
Marseille's port logistics, laundering the money through Fondation Lumiere,
and using humanitarian cargo as cover. She was close. Too close.

---

## 15.8 -- False Positive Management (The Cost of Being Wrong)

False positives are the enemy of every detection system. But in this
investigation, a false positive didn't just waste analyst time -- it could send
me down a path that led away from Clara. I couldn't afford that.

```bash
# Report a false positive
curl -s -X POST http://localhost:3000/ai/feedback \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "analysis_id": "01950a3f-7777-7000-8000-000000000007",
    "finding_id": "019505e0-0000-7000-8000-000000000099",
    "feedback_type": "false_positive",
    "analyst_notes": "Legitimate charity transfer. Fondation Lumiere has a parallel program for educational supplies that generates similar transaction patterns. Clara noted this distinction on notebook page 71.",
    "correct_severity": "info"
  }' | jq .
```

The feedback loop is critical. Every false positive report becomes training data:

```sql
-- False positive rate by source tool (last 7 days)
SELECT
    f.source_tool,
    COUNT(*) AS total_flagged,
    SUM(CASE WHEN fb.feedback_type = 'false_positive' THEN 1 ELSE 0 END) AS fp_count,
    ROUND(
        100.0 * SUM(CASE WHEN fb.feedback_type = 'false_positive' THEN 1 ELSE 0 END)
        / NULLIF(COUNT(*), 0), 2
    ) AS fp_rate_pct
FROM findings f
JOIN ai_analyses aa ON aa.finding_id = f.id
LEFT JOIN ai_feedback fb ON fb.analysis_id = aa.id
WHERE aa.created_at > NOW() - INTERVAL '7 days'
  AND aa.result->>'suggested_severity' != 'info'
GROUP BY f.source_tool
ORDER BY fp_rate_pct DESC;
```

```
 source_tool    | total_flagged | fp_count | fp_rate_pct
----------------+---------------+----------+-------------
 osint_feeds    |           142 |       23 |       16.20
 financial_mon  |            89 |        7 |        7.87
 mesh_intel     |           201 |       11 |        5.47
 clara_notes    |            47 |        0 |        0.00
```

Clara's notes: zero false positives. Zero. Every single finding she'd logged
was real. That woman didn't waste a single line of ink on anything that wasn't
solid.

I missed her so much my chest ached.

---

## 15.9 -- Neural Correlation (The Pattern Behind the Patterns)

Individual finding triage is useful. But the real power comes from correlation --
detecting patterns across findings that no single signal reveals.

This is where I took the biggest risk. I fed the correlator not just the
PHANTOM MERCY findings, but Clara's notebook entries. All of them. Transcribed
by hand, page by page, into the system. Her observations, her hypotheses,
her half-formed connections. The things she'd written in the margins.

```rust
// crates/svc-ai/src/correlator.rs

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CorrelationPattern {
    pub pattern_type: String,
    pub description: String,
    pub finding_ids: Vec<String>,
    pub confidence: f64,
    pub severity_impact: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CorrelationResult {
    pub patterns: Vec<CorrelationPattern>,
    pub summary: String,
    pub tokens_used: u32,
}

pub struct PatternCorrelator<'a> {
    provider: &'a dyn AiService,
}

impl<'a> PatternCorrelator<'a> {
    pub async fn correlate(
        &self,
        findings_json: &str,
    ) -> Result<CorrelationResult, AppError> {
        let system_prompt = "You are a security analyst detecting patterns \
            across findings. Analyze the findings and respond with ONLY a \
            JSON object (no markdown) with: \
            patterns (array of {pattern_type, description, finding_ids, \
            confidence, severity_impact}), \
            summary (brief overall assessment).";

        let response = self.provider
            .analyze(system_prompt, findings_json)
            .await?;
        parse_correlation_response(&response)
    }
}
```

I triggered correlation across the 47 flagged findings:

```bash
# Correlate PHANTOM MERCY findings
curl -s -X POST http://localhost:3000/ai/correlate \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "campaign_id": "019505e0-phantom-mercy-campaign",
    "findings_json": "[{\"id\":\"f1\",\"title\":\"Fondation Lumiere wire transfers +400%\",\"severity\":\"critical\",\"source\":\"financial_mon\"},{\"id\":\"f2\",\"title\":\"Encrypted satphone bursts Marseille x3\",\"severity\":\"critical\",\"source\":\"mesh_intel\"},{\"id\":\"f3\",\"title\":\"Cargo manifest anomaly Marseille-Beirut\",\"severity\":\"critical\",\"source\":\"clara_notes\"},{\"id\":\"f4\",\"title\":\"New shell entities registered Nicosia Jan 2026\",\"severity\":\"high\",\"source\":\"osint_feeds\"}]"
  }' | jq .
```

Response:

```json
{
  "patterns": [
    {
      "pattern_type": "operational_chain",
      "description": "Complete trafficking logistics chain: financial infrastructure (f1, f4) provides funding through Marseille-registered charity and Cypriot shell companies. Encrypted communications (f2) coordinate cargo movements. Manifest anomalies (f3) indicate goods being added to legitimate humanitarian shipments. This is a fully operational pipeline using aid logistics as cover for human trafficking.",
      "finding_ids": ["f1", "f2", "f3", "f4"],
      "confidence": 0.92,
      "severity_impact": "critical"
    }
  ],
  "summary": "All four findings form a coherent operational chain for an active trafficking network embedded in humanitarian logistics. The analyst who flagged f3 (Clara Dubois) appears to have identified the critical link. Her subsequent disappearance in the same geographic area is operationally significant.",
  "tokens_used": 412
}
```

*Her subsequent disappearance in the same geographic area is operationally
significant.*

A machine wrote that. A machine I'd trained on her own patterns, processing
her own findings, arrived at the conclusion I'd been trying not to reach:
Clara's disappearance wasn't a coincidence. She was taken because she found
the link.

I sat in the dark and stared at the screen until the words blurred.

---

## 15.10 -- Natural Language Query Engine (Asking the Questions She Would Ask)

**04:15 UTC.**

I needed to move faster. I started using the NLQ engine -- natural language
queries translated into SQL -- but instead of asking my own questions, I asked
the questions Clara would've asked. I knew her methodology. I had her notebook.
I knew what she'd want to know next.

### Prompt Templates

NLQ queries are backed by versioned prompt templates:

```bash
# List available prompt templates
curl -s http://localhost:3000/ai/prompts \
  -H "Authorization: Bearer $TOKEN" | jq '.[] | {name, analysis_type, variables}'
```

```json
[
  {
    "name": "finding_triage",
    "analysis_type": "finding_triage",
    "variables": ["title", "description", "source_tool"]
  },
  {
    "name": "remediation",
    "analysis_type": "remediation",
    "variables": ["title", "cwe_id", "description"]
  },
  {
    "name": "report_narrative",
    "analysis_type": "report_narrative",
    "variables": ["campaign_name", "scope", "findings_summary"]
  }
]
```

Templates use double-brace variable substitution:

```rust
// crates/svc-ai/src/prompts.rs

impl PromptEngine {
    pub fn render(template_text: &str, variables: &serde_json::Value) -> String {
        let mut result = template_text.to_string();
        if let Some(obj) = variables.as_object() {
            for (key, value) in obj {
                let placeholder = format!("{{{{{}}}}}", key);
                let replacement = value.as_str()
                    .unwrap_or(&value.to_string());
                result = result.replace(&placeholder, replacement);
            }
        }
        result
    }
}
```

### NLQ Examples -- Clara's Questions

I channeled her. Her notebook. Her voice. Her relentless focus.

**"Show me all financial transfers through Marseille charities in the last 90 days"**

The NLQ engine translates this to:

```sql
SELECT f.id, f.title, f.description, f.severity,
       f.source_tool, f.found_at, f.affected_target
FROM findings f
WHERE (
    f.title ILIKE '%marseille%'
    OR f.title ILIKE '%fondation%'
    OR f.title ILIKE '%charity%'
    OR f.title ILIKE '%wire transfer%'
    OR f.title ILIKE '%financial%'
    OR f.description ILIKE '%marseille%charity%'
    OR f.description ILIKE '%fondation lumiere%'
)
AND f.found_at > NOW() - INTERVAL '90 days'
ORDER BY f.found_at DESC;
```

**"Which aid shipments correlate with encrypted communication bursts?"**

```sql
SELECT f.affected_target,
       COUNT(*) AS correlation_count,
       ARRAY_AGG(f.title ORDER BY f.found_at DESC) AS finding_titles
FROM findings f
WHERE (f.title ILIKE '%shipment%' OR f.title ILIKE '%cargo%')
  AND EXISTS (
    SELECT 1 FROM findings f2
    WHERE f2.title ILIKE '%encrypted%burst%'
      AND ABS(EXTRACT(EPOCH FROM (f2.found_at - f.found_at))) < 86400
  )
GROUP BY f.affected_target
ORDER BY correlation_count DESC
LIMIT 20;
```

**"What was Clara Dubois's last activity in the system?"**

```sql
SELECT
    f.id, f.title, f.description, f.severity,
    f.source_tool, f.found_at
FROM findings f
WHERE f.created_by = '019505e0-clara-dubois-analyst-id'
ORDER BY f.found_at DESC
LIMIT 10;
```

That last query. Her last ten findings. I'd run it a hundred times already,
hoping somehow a new entry would appear, that she'd managed to get a signal
through. It never did. January 15th. The cargo manifest anomaly. Then silence.

### Creating the PHANTOM MERCY Template

```bash
# Create a custom NLQ template for PHANTOM MERCY
curl -s -X POST http://localhost:3000/ai/prompts \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "phantom_mercy_hunt",
    "analysis_type": "nlq",
    "template_text": "You are an intelligence analyst investigating child trafficking via aid networks (PHANTOM MERCY). Convert this natural language query to SQL against the Playseat schema.\nTables available: findings, campaigns, evidence, incidents, geo_targets, geo_positions.\nPrioritize: financial patterns, geographic clusters around Marseille, timing correlations with humanitarian logistics.\nQuery: {{query}}\nRespond with ONLY the SQL query, no explanation.",
    "variables": ["query"]
  }' | jq .
```

```json
{
  "id": "01950a3f-9999-7000-8000-000000000009",
  "name": "phantom_mercy_hunt"
}
```

---

## 15.11 -- Remediation Becomes Rescue Planning

After triage, the next question in a normal investigation is "what do we do
about it?" In this investigation, the question was different: "where is she?"

But the remediation engine still had its uses. For each finding the pipeline
flagged, I needed actionable next steps -- not patches and firewall rules, but
intelligence collection tasks:

```bash
# Get remediation for a PHANTOM MERCY finding
curl -s -X POST http://localhost:3000/ai/remediation \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "finding_id": "019505e0-0000-7000-8000-000000000042",
    "title": "Encrypted satphone bursts from three Marseille locations",
    "description": "Three locations in Marseille 2nd, 6th, and 15th arrondissements showing encrypted Thuraya satellite phone activity in 15-minute burst patterns. Timing precedes known PHANTOM MERCY cargo movements by 6-12 hours.",
    "cwe_id": null
  }' | jq .
```

```json
{
  "id": "01950a3f-8888-7000-8000-000000000008",
  "steps": [
    "Geolocate all three satphone emission sources to building-level precision",
    "Cross-reference building addresses with known PHANTOM MERCY entities and Fondation Lumiere property records",
    "Establish timing correlation database between satphone bursts and port authority cargo manifests",
    "Request DGSE liaison (Marchetti) confirm or deny operational awareness of these locations",
    "Deploy passive geofencing on all three coordinates for movement pattern analysis"
  ],
  "priority": "immediate",
  "effort": "significant",
  "reasoning": "Encrypted satellite phone usage in burst patterns preceding known trafficking logistics indicates active operational coordination. Three locations suggest a distributed command structure. Building-level geolocation is essential for identifying potential holding locations.",
  "tokens_used": 312
}
```

*Identifying potential holding locations.*

The machine was thinking about rescue before I was. It had taken the PHANTOM
MERCY context, the encrypted phone patterns, the geographic clustering, and
arrived at the implication I'd been circling: those three locations weren't
just coordination points. They were potential sites where Clara could be held.

Three locations. Marseille 2nd, 6th, and 15th arrondissements. I marked them.

---

## 15.12 -- Narrative Generation (Writing the Case That Would Save Her)

Reports are how security work gets funded. In this case, the narrative I needed
wasn't for a CISO or a board of directors. It was for Marchetti at DGSE. It
was the case I'd present to justify an operational response. It had to be
perfect. It had to be undeniable.

```bash
# Generate the PHANTOM MERCY narrative
curl -s -X POST http://localhost:3000/ai/narrative \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "campaign_id": "019505e0-phantom-mercy-campaign",
    "campaign_name": "PHANTOM MERCY -- Child Trafficking via Humanitarian Logistics",
    "findings_summary": "3 critical, 12 high, 32 medium. Critical: EUR 847K financial routing through Fondation Lumiere to Cypriot shells, encrypted satphone coordination from 3 Marseille locations, cargo manifest anomalies on Marseille-Beirut route. Agent Clara Dubois (DGSE deep-cover) disappeared Jan 15 after flagging cargo manifest link. 47 actionable findings from 10,247 raw signals. AI pipeline trained on Dubois analytical methodology."
  }' | jq .
```

```json
{
  "narrative": "The PHANTOM MERCY investigation has identified an active child trafficking network embedded within humanitarian logistics corridors between Marseille and Beirut. Analysis of 10,247 intelligence signals, processed through an AI pipeline trained on the analytical methodology of DGSE officer Clara Dubois, produced 47 actionable findings including three critical discoveries: a financial routing mechanism laundering EUR 847,000 through Fondation Lumiere to Cypriot shell entities, encrypted satellite communications coordinating cargo movements from three locations in Marseille, and cargo manifest anomalies on the Marseille-Beirut ferry route that indicate unauthorized additions to legitimate humanitarian shipments. Officer Dubois disappeared on January 15, 2026, twelve hours after filing the cargo manifest finding, strongly suggesting she was compromised by the network she was investigating. Three Marseille locations showing encrypted communication activity are assessed as potential operational or holding sites. Immediate operational response is recommended.",
  "tokens_used": 287
}
```

I read it three times. Then I encrypted it with Marchetti's public key and
queued it for the next Mesh sync.

---

## 15.13 -- Usage Tracking (Watching the Budget While the Clock Ticks)

AI costs money. Even running local models has a cost in compute time and
electricity. The platform tracks every token:

```bash
# Get usage statistics
curl -s http://localhost:3000/ai/usage \
  -H "Authorization: Bearer $TOKEN" | jq .
```

```json
{
  "campaign_id": null,
  "total_requests": 14823,
  "total_tokens_input": 4521000,
  "total_tokens_output": 1847000,
  "total_cost_usd": 41.27
}
```

For the PHANTOM MERCY campaign specifically:

```sql
SELECT
    c.name AS campaign_name,
    COUNT(aa.id) AS analyses,
    SUM(aa.tokens_used) AS total_tokens,
    SUM(aa.cost_usd) AS total_cost,
    ROUND(AVG(aa.confidence), 3) AS avg_confidence
FROM ai_analyses aa
JOIN campaigns c ON c.id = aa.campaign_id
WHERE aa.created_at > NOW() - INTERVAL '30 days'
  AND c.name ILIKE '%phantom%'
GROUP BY c.name
ORDER BY total_cost DESC;
```

```
 campaign_name                    | analyses | total_tokens | total_cost | avg_confidence
----------------------------------+----------+--------------+------------+----------------
 PHANTOM MERCY Investigation      |     2847 | 3,891,000    |       0.00 |          0.847
```

$0.00 cost. 2,847 analyses. Average confidence 0.847. All local. All private.
All pointing toward Marseille.

---

## 15.14 -- Pipeline Operations (The Machine That Never Sleeps)

I set the PHANTOM MERCY pipeline to run continuously. Every hour, it ingested
new signals from the Mesh, from OSINT feeds, from financial monitoring. And
every hour, it applied Clara's patterns to the new data.

### Creating the PHANTOM MERCY Pipeline

```bash
curl -s -X POST http://localhost:3000/ai/pipelines \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "phantom_mercy_continuous",
    "description": "Continuous monitoring of PHANTOM MERCY signals using Dubois pattern models",
    "pipeline_type": "triage",
    "stages": [
      {"name": "classify", "model": "dubois_pattern_matcher", "threshold": 0.7},
      {"name": "correlate", "model": "phantom_route_predictor", "window": "24h"},
      {"name": "prioritize", "strategy": "severity_confidence_weighted"}
    ],
    "model_config": {
      "provider": "local",
      "model": "mixtral-8x22b",
      "max_tokens": 4096,
      "temperature": 0.1
    },
    "schedule": "0 * * * *"
  }' | jq .
```

### Monitoring Pipeline Health

```sql
-- Pipeline run history (last 7 days)
SELECT
    p.name AS pipeline_name,
    pr.status,
    pr.started_at,
    pr.completed_at,
    pr.items_processed,
    pr.items_flagged,
    pr.items_dismissed,
    pr.error_count,
    pr.tokens_used,
    pr.cost_usd,
    EXTRACT(EPOCH FROM (pr.completed_at - pr.started_at)) AS duration_secs
FROM ai_pipeline_runs pr
JOIN ai_pipelines p ON p.id = pr.pipeline_id
WHERE pr.started_at > NOW() - INTERVAL '7 days'
ORDER BY pr.started_at DESC;
```

### Circuit Breakers

If the error rate exceeds 5% or the model returns unparseable responses, the
pipeline pauses:

```sql
-- Check for degraded pipeline runs
SELECT
    p.name,
    pr.error_count,
    pr.items_processed,
    ROUND(100.0 * pr.error_count / NULLIF(pr.items_processed, 0), 2) AS error_rate_pct,
    pr.summary->>'error_details' AS error_details
FROM ai_pipeline_runs pr
JOIN ai_pipelines p ON p.id = pr.pipeline_id
WHERE pr.error_count > 0
  AND pr.started_at > NOW() - INTERVAL '24 hours'
ORDER BY error_rate_pct DESC;
```

I couldn't afford downtime. Not an hour. Not a minute. Because somewhere in the
next batch of signals, there might be a trace. A phone ping. A financial
transaction. A cargo movement. Something that would tell me where she was.

---

## 15.15 -- Lessons Learned (What Clara Taught the Machine, and What the Machine Taught Me)

**05:30 UTC. Dawn breaking over the compound.**

After seven months of running AI pipelines in production, and one desperate
night of rebuilding them around a woman's analytical soul, here's what I know:

**1. Temperature 0.1, not 0.0.** Setting temperature to exactly 0 produces
deterministic but sometimes pathologically literal outputs. 0.1 gives just
enough variation to handle edge cases. Clara would've called it "leaving room
for intuition."

**2. Parse defensively.** Models will occasionally return markdown-wrapped JSON,
extra whitespace, or truncated responses. Every parser in the pipeline has
fallback logic:

```rust
fn parse_triage_response(response: &AiResponse) -> Result<TriageResult, AppError> {
    let json: serde_json::Value = serde_json::from_str(&response.content)
        .map_err(|e| {
            AppError::internal(format!(
                "failed to parse triage response as JSON: {e}"
            ))
        })?;

    let severity_str = json["severity"].as_str().unwrap_or("medium");
    let severity = match severity_str {
        "critical" => Severity::Critical,
        "high" => Severity::High,
        "medium" => Severity::Medium,
        "low" => Severity::Low,
        _ => Severity::Info,
    };

    Ok(TriageResult {
        suggested_severity: severity,
        confidence: json["confidence"].as_f64().unwrap_or(0.5),
        false_positive_likelihood: json["false_positive_likelihood"]
            .as_f64().unwrap_or(0.0),
        reasoning: json["reasoning"]
            .as_str()
            .unwrap_or("no reasoning provided")
            .to_string(),
        tokens_used: response.tokens_input + response.tokens_output,
    })
}
```

**3. Track tokens religiously.** Without cost tracking, AI costs surprise you.
But cost isn't just money -- it's time. Every token processed is time Clara
doesn't have.

**4. The feedback loop is everything.** Without analyst feedback on false
positives, model accuracy degrades within weeks. I made FP reporting a
single-click action in the desktop app. Clara's zero FP rate from her manual
notes set the benchmark I'm chasing.

**5. Local models for volume and privacy, cloud models for quality.** The
PHANTOM MERCY pipeline processes thousands of signals daily. Running it locally
costs $0 and leaks nothing. For other operations where security isn't
existential, the cloud providers offer better accuracy.

**6. Never let AI auto-remediate critical findings.** The pipeline suggests.
Humans decide. This isn't a philosophical position -- it's a legal requirement
for government work, and a moral requirement when lives are at stake.

**7. You can encode an analyst's methodology, but not their instinct.** The
Dubois pattern matcher has 87% accuracy. Clara had something closer to 100%.
The gap is intuition -- the thing she did that I can't put into a prompt
template. The way she'd read a financial document and just *know* something
was wrong. The way she'd look at a map and see the invisible lines connecting
scattered points.

I can't build that. I can only approximate it. But 87% accuracy against 10,247
signals found the three critical leads that confirm she was onto something real.
And it found the three Marseille locations where encrypted phones are still
active.

That's enough. That's a start.

I closed her notebook. Put it in the locked drawer. And started building the
GEOINT queries that would turn those three locations into coordinates, distances,
and -- if I was lucky -- the place where they were keeping her.

---

**02:17 -- 05:30 UTC. Three hours and thirteen minutes.**

In three hours, I'd taught a machine to think like the woman I love. It wasn't
enough. It would never be enough. But at 05:30 on February 4th, 2026, I had
something I didn't have at 02:17: direction. Three points on a map. Marseille.

Clara, if you're still out there -- I'm coming.

---

*Next chapter: GEOINT Operations -- Tracking Clara's Ghost*

---

`© 2026 Playseat — All Rights Reserved | Defensive Intelligence Through ADAPT`
