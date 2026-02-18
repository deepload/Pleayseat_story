# Chapter 42: AI Development Patterns -- What Works and What Doesn't

**Playseat Advanced Field Manual -- Book 2**
**A Practitioner's Field Guide to Building Real Systems with AI**

---

> "In theory, theory and practice are the same. In practice, they are not."
> -- Attributed to various people, all of whom clearly tried to ship AI-generated code on a Friday

---

## 42.1 -- Why This Chapter Exists

Chapter 41 told you the story. This chapter gives you the patterns.

Not theory. Not "best practices" written by someone who read a blog post. These are the specific, battle-tested patterns I discovered while building Playseat -- 218 Rust crates, 225 SQL migrations, 1,100+ database tables, 212 API routes, 40 React pages, and 91 end-to-end tests in seven days. Every pattern in this chapter was learned by doing. Most were learned by failing first.

I am writing this for the developer who has used AI assistants for small tasks and is ready to scale up to entire systems. The cognitive jump from "AI writes a function" to "AI writes 200 crates" is not incremental. It requires a fundamentally different workflow, a different relationship with your tools, and a different set of instincts about what to trust and what to verify.

This chapter covers five patterns that work, four anti-patterns that will burn you, the real cost analysis that no one talks about honestly, and the exact commands and configurations I used. No fluff. No marketing. Just the field manual.

---

## 42.2 -- Pattern 1: Architect Then Implement

### What It Is

The human designs every structural decision before the AI writes a single line of code. Not a sketch on a napkin. A real specification: technology choices with justifications, data model with column types, API surface with exact paths, naming conventions, security model, deployment topology.

### Why It Is Non-Negotiable

I am going to say something that will sound obvious but that I have watched dozens of developers get wrong: AI models do not make decisions. They generate the most probable output given the input. When you ask Claude Code "should I use PostgreSQL or MongoDB?" it produces a thoughtful-sounding comparison and then agrees with whichever option you seem to lean toward.

This agreeableness is not a bug. It is a fundamental characteristic of how large language models work. They are trained to be helpful, not to be opinionated. And architecture requires opinions. Harsh, specific, defended-to-the-death opinions.

"We use UUIDv7 because time-sortable IDs distribute writes evenly across B-tree indexes, eliminate the need for a separate created_at index for ordering queries, and enable rough temporal ordering just by looking at the ID."

"We dual-hash with BLAKE3 and SHA-256 because BLAKE3 gives us 10 GB/s verification speed for real-time operations, but SHA-256 is what courts and ANSSI recognize for legal evidence chains."

"We use Tauri v2 instead of Electron because a 200MB Chromium bundle is unacceptable for air-gapped SCIF deployment, and we are not willing to compromise on that."

These are not analyses. These are assertions born from experience, domain knowledge, and the willingness to be wrong. AI cannot do this. AI generates analyses. Humans make assertions.

### How I Applied It

Before day 1 of the Playseat sprint, I had a mental architecture document that covered:

```
CORE DECISIONS (non-negotiable):
  Language: Rust (memory safety for evidence handling)
  Database: PostgreSQL 16 (JSONB + full-text search + txn integrity)
  Auth: JWT with 15min access / 7d refresh, RBAC with 4 roles
  IDs: UUIDv7 everywhere, no exceptions
  Timestamps: TIMESTAMPTZ always, never TIMESTAMP
  Hashing: BLAKE3 + SHA-256 dual hash on all evidence artifacts
  Audit: append-only, mutation-prevention trigger in PostgreSQL
  API: /api/v1/{domain}/{resource}, REST, JSON
  Desktop: Tauri v2, React 18, TypeScript, Tailwind (slate palette)

NAMING CONVENTIONS:
  Tables: {domain_prefix}_{resource_plural}
  Crates: svc-{module}
  Routes: {module}.rs in svc-api/src/routes/
  Migrations: NNN_{description}.sql
  Indexes: idx_{table}_{column}

PATTERNS:
  Every crate: Cargo.toml + lib.rs + unit tests
  Every route: router() fn returning Router<AppState>
  Every migration: CREATE TABLE IF NOT EXISTS + CREATE INDEX IF NOT EXISTS
  Every handler: async fn, Result<Json<T>, AppError>, auth context extracted
```

This document was not written down formally on day 1. It lived in my head and was reinforced through the first three hand-written crates. That was a mistake. By day 4, when I was launching 6-10 parallel agents, the agents needed this context explicitly. I ended up typing the same conventions into agent prompts repeatedly. If I were starting over, I would write `ARCHITECTURE.md` in the first hour and reference it in every prompt.

### The Cost of Skipping This Pattern

I know exactly what happens when you skip it because I did it once.

On day 3, I gave Claude Code a lazy instruction: "Create a social engineering simulation module." No table schemas. No route definitions. No test scenarios. Just a vague directive.

Claude Code produced a module. It compiled. The tests passed. And it was wrong in every way that mattered:
- 11 database tables where 6 were sufficient (three of them duplicated concepts that already existed in other modules)
- 24 API endpoints where 12 were needed (it invented a "campaign template marketplace" feature I never asked for)
- A custom finite state machine library instead of simple enum transitions (over-engineered to a comic degree)
- A 600-line React page with three nested modals and a drag-and-drop campaign builder

I threw it away. Regenerated from a proper specification. Took 15 minutes to write the spec, 8 minutes for Claude Code to implement it. Total time: 23 minutes for the correct version. Time wasted on the vague version: about 20 minutes of generation plus 15 minutes of review before I realized it was unsalvageable. That is 35 minutes lost because I was too lazy to write a specification.

The lesson is arithmetic: 15 minutes of specification saves 35 minutes of rework. Every time. Without exception. In the entire seven-day sprint, I never once produced a better result by giving the AI vague instructions.

---

## 42.3 -- Pattern 2: Parallel Agent Armies

### What It Is

Decompose work into batches of 4-10 completely independent tasks. Launch one AI agent per task, all running simultaneously. Collect results. Review and fix in batch. Commit. Start the next batch.

### Why It Works

AI agents have zero coordination overhead. There are no standup meetings. No Slack threads debating variable names. No "I am blocked waiting for Sarah to merge her PR." No context-switching tax. An agent starts, works, finishes. Another agent starts, works, finishes. They do not interfere with each other if the tasks are truly independent.

The key word is "truly." Two crates that do not import each other are independent. A crate and its route file are not (the route imports from the crate). Two migration files that create different tables are independent. Two migrations where one creates a foreign key to the other's table are not.

In a Cargo workspace, identifying independence is straightforward. If crate A's `Cargo.toml` does not list crate B as a dependency, and B does not list A, they can be created in parallel. Period.

### The Real Numbers

Here is the actual throughput data from the Playseat sprint. I tracked these times because I wanted to know if parallelism was actually saving time or just creating more chaos.

| Task | Sequential (1 agent) | Parallel (6 agents) | Wall-Clock Speedup |
|------|---------------------|---------------------|-------------------|
| Create 6 Rust crates | ~72 min | ~32 min | 2.25x |
| Create 6 route files | ~60 min | ~28 min | 2.14x |
| Create 6 migrations | ~36 min | ~16 min | 2.25x |
| Write 6 book chapters | ~10 hours | ~2 hours | 5x |

Notice the speedup is not 6x even though there are 6 agents. For code generation, it hovers around 2-2.5x. For text generation (book chapters), it reaches 5x.

Why the difference? Because code generation has a sequential tail: the review, the batch fix, the `cargo build --workspace`, the error investigation. These steps are single-threaded (one human, one compiler). For book chapters, there is no compilation step, so the only sequential part is the review, which can be skimmed much faster than code can be debugged.

The practical implication: parallel agents for code generation give you 2-3x throughput improvement, not 6-10x. That is still enormous (2.5x over seven days is the difference between 7 days and 17.5 days), but it is important to have realistic expectations. You will not 10x your output by launching 10 agents.

### The Batch Workflow

Here is the exact workflow I used on day 4 when scaling from 80 to 205 crates:

```
Phase 1: PLAN (10 min)
  - Define next batch of 6-8 modules
  - For each: name, tables, routes, dependencies
  - Verify: no module in this batch imports another module in this batch

Phase 2: GENERATE (15-25 min)
  - Launch agents in parallel
  - Each agent gets: architecture doc, gold standard reference, specific module spec
  - Wait for completion (agents finish at different times)

Phase 3: BATCH FIX (3 min)
  - find crates/ -name "*.rs" -exec sed -i 's/\\!/!/g' {} +
  - find crates/ -name "*.rs" -exec sed -i 's/shared_types::types::Id/shared_types::Id/g' {} +
  - Check Cargo.toml files for unquoted strings

Phase 4: COMPILE (3-8 min)
  - cargo build --workspace
  - If errors: fix manually or describe to AI
  - Iterate until clean (usually 1-2 rounds)

Phase 5: TEST (3-5 min)
  - cargo test --workspace
  - If failures: fix test expectations or implementation
  - Usually 0-2 failures per batch

Phase 6: COMMIT (2 min)
  - git add + commit with descriptive message
  - Include module names and migration numbers

Total cycle: 35-55 minutes per batch of 6-8 modules
Sustained rate: ~10 modules per hour
```

On day 4, I ran this cycle approximately 12 times over 14 hours. That is how 125 new crates came into existence in a single day: not magic, just a disciplined loop executed at sprint pace.

### The Pitfalls That Cost Me Hours

**Pitfall 1: Shared file contention.** Two agents both tried to modify `svc-api/src/lib.rs` to add their `.merge()` call to the router. The second agent overwrote the first agent's changes. I lost 4 crates worth of router integration and had to re-add them manually. Solution: never let agents modify shared files. Agents output their own files only. The human adds all `.merge()` calls to the central router in a single pass after the batch.

**Pitfall 2: Table name collisions.** Without explicit domain prefixes, agent 3 created a `policies` table and agent 5 created a different `policies` table. PostgreSQL's `CREATE TABLE IF NOT EXISTS` silently accepted the first one and skipped the second. The second module's indexes then failed because they referenced columns that existed in the second schema but not the first. This caused the 33-collision disaster documented in chapter 41. Solution: include the exact table name with domain prefix in every agent's prompt.

**Pitfall 3: Inconsistent shared type usage.** Agents working in parallel independently defined the same enums (`Severity`, `Status`, `Priority`) instead of importing from `shared-types`. Each agent made a locally reasonable decision: "I need a Severity enum, so I will define one." But globally, this created 12 duplicate definitions that Rust's type system treated as incompatible types. Solution: provide every agent with an explicit list of types that must be imported from `shared-types`, never redefined.

**Pitfall 4: Migration ordering conflicts.** Two agents created migration files with sequential numbers (e.g., `078_network_policies.sql` and `079_compliance_rules.sql`) but their tables had foreign key dependencies that required a specific execution order. Since migrations run in numerical order, the FK in migration 079 referenced a table from migration 078 that had not been created yet by the other agent's output. Solution: assign migration numbers before launching agents, and explicitly map foreign key dependencies.

Each of these pitfalls cost me 30-60 minutes the first time I encountered it. After that, I built the mitigation into my batch planning phase. By day 6, the batch workflow was smooth enough that I could process a batch of 6 modules in 35 minutes with zero surprises.

---

## 42.4 -- Pattern 3: Gold Standard Reference

### What It Is

Write one perfect implementation of the most common artifact type. Not "pretty good." Perfect. Then tell every AI agent: "Follow this file exactly. Do not deviate."

### Why This Is the Single Most Important Pattern

I say this with conviction: the gold standard reference is the pattern that made the entire Playseat build possible. Without it, day 4 (scaling from 80 to 205 crates) would have been impossible. With it, day 4 was a mechanical exercise in prompt filling.

Here is why. When you tell an AI "create a route handler," it has to make a hundred micro-decisions: What should the import ordering look like? How should errors be handled? What should the function signature be? How should pagination work? Should the response include metadata? How should the URL be structured?

Each of these decisions has multiple reasonable answers. If the AI makes different decisions for different modules, you get an inconsistent codebase that is hard to maintain and review. You spend your review time on "why is this route using a different error format?" instead of "is the business logic correct?"

When you provide a gold standard file and say "do it exactly like this," all those micro-decisions are resolved. The AI replicates the pattern with mechanical precision. Every route has the same import ordering. Every handler has the same function signature. Every error uses the same format. The variable parts -- table names, column definitions, business logic -- change correctly for each module. The structural parts stay identical.

### The Playseat Gold Standard

I wrote `crates/svc-api/src/routes/threatintel.rs` by hand on day 2. It was 340 lines of carefully structured Axum route handler code. It established ten conventions:

1. **Module doc comment** with `//!` explaining the module's purpose
2. **Import ordering**: axum extractors first, serde second, sqlx third, uuid fourth, local crates last
3. **Query parameter struct** with `Option<>` fields and `.unwrap_or()` defaults
4. **Response struct** with `#[derive(Debug, Serialize)]` and only the fields the client should see
5. **Router function** named `router()` returning `Router<AppState>` with RESTful route definitions
6. **Handler functions**: async, four parameters (State, AuthContext, extractor, optional body), returning `Result<Json<T>, AppError>`
7. **SQL queries** using `sqlx::query_as!` macro with parameterized inputs
8. **Pagination** with page/per_page/offset calculation, max 100 per page
9. **Error handling** with `.map_err(|e| AppError::internal(format!("Database error: {e}")))`
10. **Route paths** under `/api/v1/{module}/{resource}` with `:id` path parameters

With this gold standard in place, my prompt for each subsequent module was short:

```
Create the forensics route handler following the exact pattern
of threatintel.rs.

Module: forensics
Base path: /api/v1/forensics
Resources:
  - cases (CRUD + list)
  - artifacts (CRUD + list, nested under case)
  - timelines (list + append, nested under case)

Tables referenced:
  - forensic_cases (id, title, case_type, status, assignee_id, ...)
  - forensic_artifacts (id, case_id FK, artifact_type, blake3_hash, sha256_hash, ...)
  - forensic_timelines (id, case_id FK, event_type, description, actor_id, ...)
```

That is it. Fifteen lines of prompt for a 300-line route file. The agent knew the rest because the gold standard told it everything about structure, style, error handling, and conventions.

### The 200x Multiplier Effect

I wrote one file by hand: ~340 lines, about 2 hours with testing and refinement.

From that one file, Claude Code generated:
- 211 additional route files (~340 lines each, ~71,000 lines total)
- 217 additional crate files (~200 lines each, ~43,400 lines total)
- 224 additional migration files (~100 lines each, ~22,400 lines total)

Total output derived from the gold standard: approximately 136,000 lines of code that followed a consistent structure.

That is a 400x multiplication from the initial 340-line investment. Even accounting for review and fix time (approximately 1 hour per batch of 6-8 modules), the ROI on writing a careful gold standard is astronomical.

### What Happens Without a Gold Standard

On day 1, before I had established the gold standard, I asked Claude Code to create three route files without a reference example. The results:

- Route file 1: Used `axum::extract::Json` for both request and response, with error handling through `anyhow::Result`
- Route file 2: Used a custom response wrapper struct `ApiResponse<T>` that the AI invented, with error handling through `thiserror` derives
- Route file 3: Used bare `impl IntoResponse` returns with manual `StatusCode` setting, and `Result<(), String>` for error handling

Three files. Three completely different patterns. All valid Rust. All would work. All impossible to maintain as a coherent codebase.

I threw all three away and wrote the gold standard. That was the last time I created anything without a reference pattern.

---

## 42.5 -- Pattern 4: The Fix Loop

### What It Is

Accept that AI-generated code will have errors. Build a systematic, partially automated process for finding and fixing those errors. Measure convergence: a healthy fix loop reaches zero errors in 3-5 iterations.

### Why It Is Faster Than Writing Code From Scratch

This is counterintuitive. If the AI introduces bugs, why not just write the code yourself?

Because the bugs are consistent and the fixes are cheap. Here is the comparison:

```
Writing a crate from scratch:
  - Type 200 lines of Rust: 45 minutes
  - Debug compile errors: 10 minutes
  - Write tests: 20 minutes
  - Debug test failures: 15 minutes
  Total: ~90 minutes per crate

AI generation + fix loop:
  - AI generates 200 lines: 3 minutes
  - Batch fix known patterns (sed): 1 minute
  - First cargo build, fix remaining: 5 minutes
  - cargo test, fix failures: 3 minutes
  Total: ~12 minutes per crate
```

The AI fix loop is 7.5x faster because:
1. Generation is near-instant (3 minutes vs 45 minutes)
2. Known bugs are fixed automatically (the sed commands handle 60-70% of errors)
3. Remaining bugs are described to the AI, which fixes them faster than a human can
4. The whole cycle converges in 3-5 iterations

### The Five Stages

```
Stage 1: GENERATE
  AI writes code
  Time: 3-8 minutes (single agent) or 12-25 minutes (parallel batch)

Stage 2: BATCH FIX
  Apply known fix patterns:
    sed -i 's/\\!/!/g' (escape bug)
    sed -i 's/shared_types::types::Id/shared_types::Id/g' (import path)
    Check Cargo.toml quoting
  Time: 1-3 minutes

Stage 3: COMPILE
  cargo build --workspace (or cargo build -p specific-crate for faster feedback)
  Categorize remaining errors:
    - Known pattern? Apply fix. Recompile.
    - Unknown pattern? Describe to AI. AI proposes fix. Apply. Recompile.
    - Architectural issue? Human fixes. Recompile.
  Time: 3-10 minutes
  Typical iterations: 1-3

Stage 4: TEST
  cargo test --workspace
  Categorize failures:
    - Wrong assertion? AI adjusts test. Retest.
    - Real implementation bug? AI fixes implementation. Back to Stage 3.
    - Missing test fixture? Human adds setup. Retest.
  Time: 2-8 minutes
  Typical iterations: 1-2

Stage 5: COMMIT
  All green. git add. git commit.
  Time: 2 minutes
```

### Convergence Metrics Across the Sprint

I tracked error counts across the entire seven-day build. The data tells a clear story:

| Sprint Day | Avg Errors per Crate (First Build) | Fix Iterations to Clean | Time per Crate |
|------------|----------------------------------|------------------------|---------------|
| Day 1 | 5-8 | 4-5 | ~20 min |
| Day 2 | 3-5 | 3-4 | ~15 min |
| Day 3 | 3-4 | 3 | ~12 min |
| Day 4 (early) | 4-6 | 3-4 | ~10 min |
| Day 4 (late) | 2-3 | 2-3 | ~8 min |
| Day 5 (QA) | 1-2 | 2 | ~10 min |
| Day 6 | 1-2 | 2 | ~10 min |

The improvement from day 1 to day 4 came from three things: better prompts (more precise instructions), the batch fix script (automated known bugs), and my own review speed increasing (I learned what to look for). The slight regression on days 5-6 was because those modules were more complex and had more domain-specific logic that required careful review.

### When the Fix Loop Fails

Twice during the sprint, the fix loop did not converge. Both times, the root cause was an architectural issue that the AI could not resolve by iterating on code.

**Failure case 1: Circular dependency.** Agent A created a crate that imported from Agent B's crate, and Agent B's crate imported from Agent A's crate. The AI's attempt to fix it was to inline the shared type. This "fixed" the compile error but created a maintenance nightmare (the type was now defined in two places). I had to stop, identify the shared type, move it to `shared-types`, and update both crates. Time wasted: 25 minutes.

**Failure case 2: SQL type mismatch cascade.** The AI generated a migration with `REAL` (32-bit float) for a score column, but the Rust struct used `f64` (which maps to `DOUBLE PRECISION`). The AI's first fix: change the Rust type to `f32`. This fixed the decode error but broke a downstream calculation that required `f64` precision. The AI's second fix: change the calculation to use `f32`. This introduced floating-point precision errors that made the test assertions fail with values like `0.7000000029802322` instead of `0.7`. The AI's third fix: change the test to use approximate comparison. At this point, three iterations had made the code worse, not better. I stopped the loop, changed the migration column from `REAL` to `DOUBLE PRECISION`, and everything worked.

The lesson: when the fix loop exceeds 5 iterations without converging, stop. The problem is not code-level. It is architectural. The AI is trying to patch symptoms while the disease is structural. Step back, identify the root cause, fix it at the right level, then let the AI continue.

---

## 42.6 -- Pattern 5: Evidence-Driven QA

### What It Is

AI writes both the implementation and the tests. The human does not review test code line by line. Instead, the human reviews test failures (to find real bugs) and test coverage (to find missing scenarios). Trust the compiler and the test runner to be your first filter. Focus your limited human attention on the questions only a human can answer.

### Why This Works Better Than You Think

AI-generated tests have a subtle but powerful property: they are independently derived from the same specification as the implementation. When one AI pass writes the code and another writes the tests (or even the same pass writes both but tests against the specification rather than the implementation), the tests often catch bugs that the implementer missed.

This happened four times during the Playseat QA phase. The most notable: the threat intel feed parser had an off-by-one error in pagination. When the total record count exactly equaled the page size (e.g., 25 records with page_size=25), the `total_pages` calculation returned 2 instead of 1 because of integer division rounding:

```rust
// Buggy implementation (AI-generated):
let total_pages = (total_count + per_page - 1) / per_page;
// When total_count=25, per_page=25: (25 + 25 - 1) / 25 = 49/25 = 1 (integer division)
// Actually correct! The bug was elsewhere:

let total_pages = total_count / per_page + 1; // WRONG
// When total_count=25, per_page=25: 25/25 + 1 = 2 (should be 1)
```

An AI-generated unit test with the boundary condition `total=25, page_size=25` caught it. The test asserted `total_pages == 1`, the implementation returned 2, the test failed, and I fixed the implementation.

An AI wrote the bug. A test from the same AI session caught the bug. That is a remarkable development workflow.

### The 5% Problem

About 5% of AI-generated tests are what I call "tautological" -- they test something, but not anything meaningful:

```rust
// Tautological (AI-generated):
#[test]
fn test_create_feed() {
    let feed = ThreatFeed {
        id: Uuid::now_v7(),
        name: "Test Feed".to_string(),
        // ... fields ...
    };
    assert!(feed.id != Uuid::nil());  // Always true for any v7 UUID
}
```

This test will never fail. It does not test any behavior. It tests that UUIDv7 generates non-nil UUIDs, which is a property of the UUID library, not of your code.

A better version:

```rust
#[test]
fn test_create_feed_validates_name() {
    let result = ThreatFeed::validate_name("");
    assert!(result.is_err());
    assert!(result.unwrap_err().to_string().contains("name cannot be empty"));
}
```

I found approximately 350 tautological tests across the 7,150+ total. I rewrote the worst 50 and left the remaining 300 in place. They are not harmful -- they do not produce false positives -- but they do create false confidence. Having 7,150 passing tests sounds impressive until you realize 350 of them would pass no matter what the code did.

### The E2E Test Strategy

The 91 Playwright E2E tests were the most effective quality gate, and they were a genuine human-AI collaboration. The pattern:

1. I described the user journey in plain English
2. Claude Code wrote the Playwright test with proper selectors and API mocking
3. I ran the test, tweaked selectors that did not match, and added missing assertions
4. Repeat for each journey

The key technical decisions were:
- **JWT injection into localStorage** to skip the login flow for non-auth tests
- **API mocking with `page.route()`** to isolate frontend tests from backend state
- **Data-testid attributes** on React components for stable selectors

Claude Code nailed all three patterns after I showed it the approach for the first test. 91 tests, all passing, running in under 30 seconds on Chromium.

My one complaint: the AI-generated tests consistently used overly broad selectors like `page.getByText('Submit')` instead of `page.getByTestId('submit-incident')`. In a 40-page app, there might be 15 elements containing the text "Submit." This caused flaky test failures that I had to debug individually. After fixing the first 10, I started specifying "use data-testid selectors, never text selectors" in my prompt. The problem disappeared.

---

## 42.7 -- Anti-Pattern 1: Letting AI Make Architecture Decisions

### The Trap

You ask Claude Code: "Design the database schema for a threat intelligence platform."

It produces a schema. It looks reasonable. It has tables for feeds, IOCs, threat actors, campaigns, and relationships. It even includes junction tables for many-to-many relationships and appropriate indexes.

But the schema is wrong in ways that only domain expertise can catch:
- It stores IOC expiry as a column in the IOC table instead of a separate versioning table (stale IOCs are never deleted, they are superseded)
- It uses integer primary keys instead of UUIDv7 (breaks offline operation and multi-region sync)
- It stores STIX bundles as TEXT instead of JSONB (kills query performance on threat data)
- It does not include confidence scores on feed-IOC relationships (essential for deduplication when the same IOC appears in multiple feeds)
- It creates a `references` column without quoting it (PostgreSQL reserved word)

The AI does not push back on any of these issues. It does not say "are you sure you want integer PKs for a platform that might need offline sync?" It just produces the most probable schema given the phrase "threat intelligence platform" and moves on.

### The Rule

Never ask the AI to design. Always tell the AI what to build.

```
BAD:  "Design the threat intel schema."
GOOD: "Create these exact tables with these exact columns and types: [full spec]"

BAD:  "What framework should I use for the API?"
GOOD: "Implement an Axum 0.7 router with Tower middleware in this exact pattern: [gold standard]"

BAD:  "How should I handle authentication?"
GOOD: "Implement JWT auth using jsonwebtoken 9 with 15-min access tokens,
       7-day refresh tokens, RBAC with Admin/Analyst/Operator/ReadOnly roles,
       and middleware that extracts Bearer tokens and injects AuthContext."
```

The more specific your instruction, the less room there is for the AI to hallucinate architecture decisions. The goal is to reduce AI-generated code to a fill-in-the-blanks exercise, not a design exercise.

---

## 42.8 -- Anti-Pattern 2: Skipping Human Review

### The Trap

The AI generates 50 crates. All compile. All tests pass. You commit without reading the code because the green checkmarks feel like safety.

Two weeks later, you discover:
- Three crates return all database rows when the filter parameter is None instead of returning an empty set (a silent data exposure bug that the compiler cannot catch)
- One crate's RBAC check uses `>=` instead of `==` for role comparison, meaning Analyst can perform Admin-only operations (a privilege escalation bug that tests did not cover because the AI did not write a "wrong role" test for that specific route)
- Five crates have SQL queries that do not limit results when no pagination is specified, enabling denial-of-service via `SELECT * FROM million_row_table`

These are not compile errors. These are logic errors that require a human with security awareness to identify. The compiler sees valid Rust. The tests see correct responses for the tested inputs. But the tested inputs do not include adversarial cases.

### The Fix

Review every handler function. Read every SQL query. Check every RBAC assertion.

For 218 crates, this took approximately 6 hours total (spread across days 5-7). That is about 1.5 minutes per crate. Not a deep security audit -- a focused review with this checklist:

```
For every route handler:
  [ ] Auth middleware applied (check router builder)
  [ ] RBAC check matches endpoint sensitivity
  [ ] SQL uses parameterized inputs (no string interpolation)
  [ ] Pagination has a max per_page limit (I used 100)
  [ ] Error responses do not leak stack traces or internal paths
  [ ] Write operations emit audit events
  [ ] Response structs exclude internal fields (password_hash, internal notes)

For every migration:
  [ ] Table name does not collide with existing tables
  [ ] Column names are not PostgreSQL reserved words (or are quoted)
  [ ] Foreign keys reference correct tables
  [ ] Indexes cover expected query patterns
  [ ] IF NOT EXISTS on all CREATE statements
  [ ] TIMESTAMPTZ, not TIMESTAMP
  [ ] DOUBLE PRECISION, not REAL
```

1.5 minutes per crate. 6 hours total. This caught 8 real issues across 218 crates. A 3.7% defect rate that would have been zero-noticed without review.

---

## 42.9 -- Anti-Pattern 3: AI for Security-Critical Logic Without Deep Understanding

### The Trap

The AI implements JWT validation. It looks correct. The tests pass. You deploy.

Six months later, a security audit discovers:
- The JWT validation does not check the `aud` (audience) claim, meaning tokens from any application using the same signing key can authenticate
- The refresh token rotation does not invalidate the old refresh token, enabling token replay attacks
- The password hashing uses bcrypt with the default cost factor of 10, which was reasonable in 2018 but is too low for 2026 hardware

The code does exactly what it was told to do. The problem is that the specification did not include every security requirement, and the AI did not add them autonomously.

### The Rule

For security-critical code, the human must understand every single line. Not "reviewed." Understood. You should be able to explain every function, every conditional, every error path to a security auditor.

For Playseat, the security-critical components were:

| Component | Lines | Review Passes |
|-----------|-------|--------------|
| `core-auth` (JWT + RBAC) | 380 | 3 passes |
| `core-evidence` (chain of custody) | 290 | 2 passes |
| `core-audit` (append-only trail) | 210 | 2 passes |
| Auth middleware | 150 | 2 passes |
| **Total** | **1,030** | **9 passes** |

1,030 lines out of 82,000. About 1.3% of the codebase. These lines got 3-4x more review attention than everything else. That is the correct prioritization.

---

## 42.10 -- Anti-Pattern 4: Assuming AI Tests Are Comprehensive

### The Trap

7,150+ unit tests pass. 91 E2E tests pass. 100% pass rate. You feel confident.

But 100% pass rate means nothing without knowing what the tests cover. AI-generated tests have a systematic bias toward happy paths:

```
What AI tests reliably:
  - Valid inputs produce expected outputs
  - CRUD operations succeed with correct data
  - State machines transition correctly for valid paths
  - Pagination returns correct page sizes for standard cases

What AI tests poorly:
  - Boundary conditions (empty input, max-length strings, zero, negative numbers)
  - Concurrent access (race conditions, lost updates)
  - Error recovery (what happens after a failed transaction rolls back?)
  - Resource exhaustion (100K concurrent connections, 1GB request body)
  - Adversarial inputs (SQL injection in filter params, XSS in stored fields)
  - Authorization edge cases (user A accessing user B's data)
```

### The Fix

After the AI generates tests, add your own tests for the gaps. I added approximately 20 manual test scenarios during the QA phase. Of those 20, four caught real bugs. That is a 20% hit rate -- far higher than the average unit test -- which tells you exactly where the AI's blind spots are.

The four bugs caught by manual tests:
1. A filter parameter that was `None` causing a `WHERE field = NULL` query (should be `WHERE field IS NULL` or omit the clause entirely)
2. A pagination endpoint that returned HTTP 500 when page=0 instead of page=1
3. An evidence upload endpoint that accepted 0-byte files without error
4. A role check that allowed `Operator` to delete campaigns (should be `Admin` only)

All four were real bugs that would have reached production. None were caught by AI-generated tests. The AI did not think to test page=0. Did not think to upload an empty file. Did not think to try Operator role on a delete endpoint.

Human testers think adversarially. AI testers think probabilistically. Both are needed.

---

## 42.11 -- The Real Cost Analysis

Let me lay out the economics with full honesty, including the costs that AI marketing materials conveniently omit.

### Direct Build Costs

```
Claude Code API usage (7 days of intensive use):     ~$200
  Input tokens: ~50M (prompts, context, file contents)
  Output tokens: ~20M (generated code, explanations, fixes)

Developer time (7 days x 10-14 hours/day):           ~$7,000
  Based on $180K/year senior engineer rate
  Fully loaded: ~$1,000/day

Infrastructure (Docker, CI/CD, hosting):              ~$100

Total:                                                ~$7,300
```

### What Those Numbers Hide

The $200 AI cost sounds impossibly cheap. Here is what it does not include:

- **My 15 years of software engineering experience.** The architecture decisions, the naming conventions, the security model, the technology choices -- none of that came from Claude Code. It came from 15 years of building systems, shipping production code, and debugging other people's mistakes at 3 AM.
- **The 10-14 hour days for seven straight days.** That is 70-98 hours of focused work in a week. That is not sustainable. I was exhausted by day 5 and making worse decisions by day 6. The cost table shows $7,000 for "developer time" but does not show the recovery week afterward.
- **The domain expertise.** Knowing which 218 modules a defensive intelligence platform needs. Knowing that evidence chains require dual hashing. Knowing that `references` is a PostgreSQL reserved word. Knowing that UUIDv7 is better than UUIDv4 for time-series data. This knowledge does not appear on an invoice.

### The Comparison That Matters

A traditional contractor team building a comparable platform:

| Resource | Duration | Rate | Total |
|----------|----------|------|-------|
| 2 senior Rust engineers | 6 months | $25K/mo each | $300,000 |
| 1 senior DBA | 4 months | $20K/mo | $80,000 |
| 2 frontend engineers | 4 months | $22K/mo each | $176,000 |
| 1 QA engineer | 3 months | $18K/mo | $54,000 |
| 1 DevOps engineer | 3 months | $20K/mo | $60,000 |
| 1 technical writer | 2 months | $15K/mo | $30,000 |
| Project management | 6 months | $18K/mo | $108,000 |
| **Total** | | | **~$808,000** |

Cost reduction: **110x**.

Even with aggressive discounting (traditional team produces more polished output, better edge case handling, deeper integration testing), the minimum advantage is 50x.

### The Subscription Math

```
Claude Code: $200/month
Sprint output: 82,000 lines of reviewed production code

Cost per line of production code: $0.0024
Equivalent contractor cost per line: $2-5

AI cost advantage per line: 830-2,080x
```

The per-line cost comparison is so extreme that it barely matters how you measure it. Even if you assume AI-generated code requires 3x more review than human-written code, the economics still favor AI by hundreds of times.

### Who This Actually Benefits

The $200/month AI subscription does not help you if:
- You do not know what to build (AI amplifies direction, not directionlessness)
- You cannot review the output (the compiler catches syntax bugs, not logic bugs)
- You are building something novel that has no pattern to replicate (AI is worst at green-field architecture)
- Your domain is so specialized that the AI has limited training data (bleeding-edge research, classified systems)

It dramatically helps you if:
- You have clear architecture and domain expertise
- Your project involves many similar modules (the gold standard pattern)
- You use a statically typed language with good compiler diagnostics
- You have automated test infrastructure
- You are a force-of-one who needs to produce team-scale output

---

## 42.12 -- The Command Reference

For teams wanting to replicate this workflow, here is the exact toolchain.

### Pre-Sprint Setup

```bash
# Rust toolchain
rustup default stable && rustup update

# Create workspace
cargo init --name playseat-api
# Edit Cargo.toml: [workspace] members = ["crates/*"]

# Desktop app
cd apps/desktop && npm install
npx playwright install chromium

# Infrastructure
docker compose up -d postgres minio

# Verify
cargo build --workspace
cd apps/desktop && npx tsc --noEmit && npm run build
```

### Quality Gates (Before Every Commit)

```bash
# Backend
cargo build --workspace 2>&1 | grep -c "error"     # Must be 0
cargo test --workspace 2>&1 | grep "test result"    # Must be all ok

# Frontend
cd apps/desktop && npx tsc --noEmit                 # Must be 0 errors
cd apps/desktop && npm run build                    # Must succeed

# E2E
cd apps/desktop && npx playwright test              # Must be 91/91
```

### Post-Generation Fix Script

```bash
#!/bin/bash
# fix-ai-output.sh -- Run after every batch of AI-generated code

echo "Fixing escape bugs..."
find crates/ -name "*.rs" -exec sed -i 's/\\!/!/g' {} +

echo "Fixing import paths..."
find crates/ -name "*.rs" -exec sed -i 's/shared_types::types::Id/shared_types::Id/g' {} +

echo "Checking Cargo.toml quoting..."
grep -rn '^name = [^"]' crates/*/Cargo.toml && echo "FIX THESE!" || echo "OK"

echo "Checking for duplicate enums..."
grep -rn "pub enum Severity" crates/ --include="*.rs" | grep -v shared_types | grep -v "// shared"
echo "Review any duplicates above."

echo "Building..."
cargo build --workspace 2>&1 | tail -20
```

---

## 42.13 -- When to Use AI and When to Write By Hand

After 137 commits and 82,000 lines, here is my honest assessment.

### Use AI (90%+ success rate, 10-50x time savings)

- CRUD route handlers with standard patterns
- Database migrations for known table schemas
- React page components following an established design system
- Unit tests for straightforward business logic
- Documentation and book chapters
- Boilerplate files (Cargo.toml, configs, CI definitions)
- Refactoring across many files with a consistent pattern

### Write By Hand (AI produces worse results than a competent human)

- Architecture documents and technology decision records
- Security-critical components (auth, crypto, evidence chains)
- Complex SQL queries with multiple joins and CTEs
- Performance-critical hot paths where every allocation matters
- Build system configuration (Cargo workspace setup, CI pipelines)
- The gold standard reference files
- Error messages and user-facing text (AI writes generic prose)

### The Gray Zone (Use AI but review intensively)

- State machine implementations (AI gets the happy path right, misses edge transitions)
- API client code in TypeScript (AI struggles with proper error typing)
- Migration files with foreign keys to existing tables (AI may reference wrong table names)
- Test fixtures and mock data (AI generates plausible but sometimes inconsistent data)

---

## 42.14 -- The Replication Challenge

You have read the patterns. You have seen the numbers. Here is a concrete two-week plan for replicating this workflow on your own project.

### Week 1: Foundation and Patterns

```
Day 1: Architecture (4 hours)
  - Write your technology decision document
  - Define naming conventions, shared types, API patterns
  - Choose your domain prefixes for database tables
  - Output: ARCHITECTURE.md

Day 2: Gold Standard (6 hours)
  - Write one perfect module by hand (crate + route + migration + tests)
  - This is your reference pattern for everything that follows
  - Output: One complete module, reviewed and tested

Day 3-4: First Batch (8 hours each)
  - Use AI to replicate gold standard for 10-15 modules
  - Practice the fix loop
  - Refine your prompts based on error patterns
  - Output: 10-15 working modules

Day 5-7: Scale (8 hours each)
  - Parallel agents, 6-8 per batch
  - Batch fix workflow
  - Target: 40-60 modules by end of week 1
```

### Week 2: Quality and Polish

```
Day 8-9: QA Pass (8 hours each)
  - Review every module against specification
  - Add missing tests (boundary conditions, auth edge cases)
  - Fix logic errors found during review

Day 10-11: Frontend (8 hours each)
  - Generate pages for every module
  - Wire up API client
  - E2E test generation

Day 12-13: Integration (8 hours each)
  - Docker deployment
  - CI/CD pipeline
  - Demo data seeding
  - Cross-platform verification

Day 14: Documentation (8 hours)
  - API documentation
  - Deployment guide
  - Architecture overview
```

Two weeks. One developer. 60-100 modules. A production-grade platform.

The patterns work. The numbers are real. The only question is what you will build with them.

---

**Chapter 42 Summary**
- Pattern 1: Architect Then Implement -- human designs, AI builds, never the reverse
- Pattern 2: Parallel Agent Armies -- 2-3x throughput for code, 5-6x for documentation
- Pattern 3: Gold Standard Reference -- write one perfect file, get 200 consistent copies
- Pattern 4: The Fix Loop -- accept iteration, converge in 3-5 rounds, stop at 5 if not converging
- Pattern 5: Evidence-Driven QA -- AI writes tests, human reviews failures and coverage gaps
- Anti-Pattern 1: Letting AI design architecture (too agreeable, no opinions)
- Anti-Pattern 2: Skipping review (logic bugs hide behind green checkmarks)
- Anti-Pattern 3: Trusting AI on security code (understands syntax, not threat models)
- Anti-Pattern 4: Assuming AI tests are complete (biased toward happy paths)
- Real cost: ~$200 AI + $7,000 human = $7,300 vs $808,000 traditional (110x reduction)

---

*Playseat Advanced Field Manual -- Book 2*
*Chapter 42 of 43*

---

(c) 2026 Playseat -- All Rights Reserved | Proprietary and Confidential