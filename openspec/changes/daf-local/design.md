## Context

DAF Local is a greenfield CLI tool and multi-agent pipeline with no prior codebase. The problem domain is design system generation: converting brand intent (expressed in a conversation) into a complete, validated, testable design system package written to a local folder on disk. The pipeline runs locally — no server, no cloud deployment, no external state beyond the output folder.

Key constraints:
- All LLM calls use Anthropic models exclusively (Claude Opus 4, Sonnet 4, Haiku 4)
- Agent orchestration uses CrewAI
- Output is a folder on disk installable as a package
- Human review happens only at defined gates — agents handle orchestration
- The retry protocol permits the pipeline to loop between adjacent phases, but phases are otherwise forward-sequential

## Goals / Non-Goals

**Goals:**
- Implement the full 6-phase, 9-crew, 45-agent pipeline as specified in the PRD
- Produce all output artifacts defined in the PRD output folder structure
- Support multi-theme (light/dark/high-contrast) and multi-brand token compilation
- Enforce a bounded retry protocol (3 attempts per component per validation boundary) with structured rejection feedback
- Enable checkpoint/resume via the `--resume` CLI flag after process crashes or API outages
- Assign agents to model tiers (Opus/Sonnet/Haiku) based on task complexity, configurable via environment variables
- Implement a plugin architecture for tools, compilers, and linters so the pipeline is extensible without forking core

**Non-Goals:**
- Publishing the generated package to npm or any registry
- Cloud deployment, hosted API, or server runtime
- Integration with external design tools (Figma, Sketch, Adobe XD) — input is conversation only
- Real-time collaboration or multi-user authoring
- Visual design editor or GUI — CLI only
- Cross-LLM provider support — Anthropic exclusively for all tiers
- Incremental/partial generation after the initial run — the pipeline regenerates from scratch or resumes from checkpoint

## Decisions

### 1. CrewAI for Agent Orchestration
**Decision:** Use CrewAI as the multi-agent orchestration framework.
**Rationale:** CrewAI provides crew-level composition with defined role/task/tool contracts that map directly to the PRD's crew-and-agent model. Sequential crew handoff with shared state (the output folder) is a first-class pattern in CrewAI.
**Alternatives considered:** LangGraph (too graph-centric; the pipeline is sequential, not a DAG with arbitrary branching), AutoGen (conversation-centric, not crew-centric), custom orchestration (unnecessary complexity).

### 2. Shared Folder as Pipeline State
**Decision:** Each crew reads from and writes to the shared output folder. No event bus, no pub/sub, no in-memory state passed between crews.
**Rationale:** The output folder is both the pipeline's shared state and the deliverable. Filesystem I/O is auditable, resumable, and does not require a message broker. Crew I/O contracts are file-level (§3.6 of the PRD), making dependencies explicit.
**Alternatives considered:** In-memory state object passed through crew chain (not resumable), Redis/message queue (unnecessary infrastructure for a local CLI tool).

### 3. W3C DTCG Three-Tier Token Architecture
**Decision:** Tokens are authored in W3C DTCG format across three tiers: global, semantic, component-scoped. Compilation to CSS/SCSS/TS/JSON is deterministic (tool-executed, not agent-decided).
**Rationale:** W3C DTCG is the emerging standard for design tokens with broad tooling support. Three-tier separation enforces a stable semantic contract — components consume only semantic tokens, never global — which enables theme-agnostic components.
**Alternatives considered:** Single-tier flat token file (no semantic abstraction, components would hardcode theme values), custom JSON schema (no ecosystem tooling).

### 4. Spec YAML as Canonical Source for Component Generation
**Decision:** Every component has a `*.spec.yaml` file written by the Bootstrap Crew. The Design-to-Code Crew generates TSX, tests, and stories exclusively from spec files — it does not infer component intent from brand profile directly.
**Rationale:** Spec files decouple intent (what the component should do) from implementation (how it is coded). This enables the retry protocol to feed structured spec violations back to the Code Generation Agent without re-running discovery.
**Alternatives considered:** Direct brand-to-code generation without specs (no structured rejection feedback possible), JSON schema format (YAML is more readable for spec authoring agents).

### 5. Bounded Retry with Structured Rejection
**Decision:** Each generator/validator pair gets a maximum of 3 retry attempts. Rejections are structured: which checks failed, what the errors are, what a fix would look like. Retry context accumulates across attempts.
**Rationale:** Unbounded retries risk infinite loops and runaway API costs. 3 attempts with accumulating error context gives the agent sufficient signal to correct its approach without excessive cost. Components that exhaust retries are marked `failed` and the pipeline continues.
**Alternatives considered:** Single-attempt pipeline (no self-correction), per-run retry (retry the entire crew, not per-component — too coarse for a11y and TypeScript failures).

### 6. CSS Class-Based Theming
**Decision:** Themes are implemented as separate compiled CSS files with class-based scoping. The ThemeProvider applies a CSS class (`theme-dark`, `brand-a`) to the root element. No JavaScript toggles individual token values.
**Rationale:** CSS class swapping is performant (single class toggle, no layout thrash), SSR-friendly, and does not require a runtime token injection library. Components remain theme-agnostic by consuming only semantic tokens.
**Alternatives considered:** CSS-in-JS runtime theming (adds a runtime dependency, complicates SSR), JavaScript token injection (fragile, requires all consumers to import a JS runtime).

### 7. Model Tier Assignment (Anthropic Exclusive)
**Decision:** Three tiers — Tier 1 (Opus) for generative agents, Tier 2 (Sonnet) for analytical agents, Tier 3 (Haiku) for classification agents. Deterministic tools use no LLM. All tiers use Anthropic models, configurable via `DAF_TIER1_MODEL`, `DAF_TIER2_MODEL`, `DAF_TIER3_MODEL`.
**Rationale:** Not all tasks require maximum capability. Routing simple classification tasks to Haiku and complex code generation to Opus optimises cost-quality tradeoff. Anthropic-only avoids cross-provider prompt engineering divergence.
**Alternatives considered:** Single model for all agents (high cost, overkill for routing), multi-provider (adds per-provider prompt tuning complexity).

### 8. Rollback Cascade Policy
**Decision:** When the Rollback Agent restores a pre-phase checkpoint, all crews after the restored phase are invalidated and must re-run. No mid-sequence resume after rollback.
**Rationale:** A11y patches in `src/` are applied in-place by the Component Factory Crew. If an earlier checkpoint is restored, those patches are lost. Cascading invalidation ensures no crew reads stale artifacts from a previous partial run.
**Alternatives considered:** Selective rollback (restore only failing crew's output) — rejected because crew outputs are interdependent; partial rollback risks artifact corruption.

### 9. Plugin Architecture for Tools
**Decision:** Every tool, compiler, and linter is a plugin. The pipeline loads plugins at startup from the `pipeline-config.json`. Crews invoke plugins via a registered tool interface, never call compilers/linters directly.
**Rationale:** Enables extension (e.g., swapping Style Dictionary for a custom compiler) without forking pipeline core. Also makes tools independently testable.
**Alternatives considered:** Hardcoded tool invocations (inflexible, no extensibility path).

## Risks / Trade-offs

- **[Risk] LLM API cost at scale** — 45 agents with up to 3 retries per component across a large component scope can generate high API costs. → **Mitigation:** Model tier assignment routes classification tasks to Haiku. Retry limit (3) bounds worst-case calls. `DAF_TIER1_MODEL` allows operators to set Tier 1 to Sonnet in cost-sensitive runs.

- **[Risk] Pipeline latency** — Sequential phase execution with retry loops adds cumulative latency, especially for large component scopes. → **Mitigation:** Phase 5 crews (AI Semantic Layer + Analytics) have no mutual dependency and may run in either order. The 3-attempt retry limit bounds per-component latency. Phase 4–6 use crew-level (not per-agent) retries to keep them fast.

- **[Risk] LLM non-determinism on resume** — Resuming from a checkpoint and re-running a phase may produce different output than the first run. → **Mitigation:** Checkpoints capture the full output folder state at each phase boundary. Resume starts from a verified checkpoint (integrity check: expected files present and non-corrupt), not from a partial in-progress state.

- **[Risk] A11y patch regressions** — In-place `src/` patching by the Accessibility Agent can introduce TypeScript errors or render regressions. → **Mitigation:** Post-patch re-validation pass: patched source is re-compiled (`tsc --noEmit`) and re-rendered before the crew is considered complete.

- **[Risk] Component Factory Crew patch loss on rollback** — If rollback restores a pre-Component-Factory checkpoint, all a11y patches applied in-place are lost. → **Mitigation:** Rollback cascade policy: restoring any phase checkpoint invalidates all subsequent phases, so post-rollback the Component Factory Crew (including a11y patching) always re-runs.

- **[Risk] Spec YAML authoring complexity** — Spec files authored by the Bootstrap Crew may be malformed or structurally incomplete, causing Design-to-Code failures downstream. → **Mitigation:** The Spec Validation Agent (17) validates spec structure before code generation begins; failures trigger the retry protocol against the Bootstrap Crew's Spec Generation Agent.

## Open Questions

- Exact plugin interface contract for tool registration in `pipeline-config.json` — to be defined in the `pipeline-orchestration` spec.
- Whether the Resume path should offer the user a diff of what's changed in the output folder since the checkpoint, before re-running — deferred to post-v1.0.
- Exact semver calculation edge cases (pre-release tags, forced major bumps) — to be defined in the `release-crew` spec.
