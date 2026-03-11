# DAF Local — DesignOps Agentic Framework

**Agent-Orchestrated Design System Generation → Testable Output on Disk**

| Field | Value |
|---|---|
| Version | 1.0.0 |
| Date | March 2026 |
| Status | DRAFT FOR REVIEW |
| Scope | Local generation. Output is a testable folder on disk. |

---

## 1. Executive Summary

### 1.1 The Problem

Creating a design system from scratch is a months-long manual effort: translating brand intent into token structures, generating consistent components, enforcing accessibility, writing documentation, and wiring up governance. Every step is error-prone, and the result is only as good as the weakest manual link.

### 1.2 The Solution

The **DesignOps Agentic Framework (DAF Local)** is an AI-driven generation pipeline built on **CrewAI multi-agent orchestration**. A CLI interviews you about your brand, then runs **45 specialized agents across 9 crews** to generate a complete, validated, documented design system as a local package — tokens, components, tests, docs, semantic registry, governance config, quality reports — ready to install and use.

Every agent has a distinct domain role. Agents make intelligent decisions (what to generate, how to validate, when to escalate). Deterministic tools execute (compile, lint, test, diff). Humans approve at defined gates.

### 1.3 Key Value Propositions

**Full agentic orchestration.** 9 specialized crews (45 agents) cover the entire generation lifecycle: discovery, token engineering, code generation, composition validation, accessibility enforcement, documentation, governance, analytics, semantic registry, and release assembly.

**Conversation to code.** A structured brand interview produces a complete design system. No manual file creation, no manual configuration, no manual scaffolding.

**Zero-drift token architecture.** A single canonical W3C DTCG token store with three tiers (global, semantic, component-scoped), compiled to every configured platform automatically.

**Self-checking quality.** Validation agents catch what generation agents miss. Token references, composition rules, accessibility, and spec-code-docs consistency are verified automatically.

**AI-consumable from day one.** The semantic registry, composition rules, and compliance rules are immediately usable by AI coding assistants (Cursor, Copilot, Claude).

**Governance-ready.** Ownership maps, quality gate thresholds, deprecation policies, contribution workflows, and RFC templates are generated alongside the code — ready for team adoption.

---

## 2. Product Definition

### 2.1 One-liner

A CLI that interviews you about your brand, then runs 45 specialized agents across 9 crews to generate a complete, validated, documented design system as a local package.

### 2.2 Input

A conversation. The user answers questions about brand identity, colors, typography, spacing, component scope, and accessibility requirements.

### 2.3 Output

```
my-design-system/
├── package.json
├── tsconfig.json
├── vitest.config.ts                      # Test runner configuration
├── vite.config.ts                        # Build configuration (library mode)
├── pipeline-config.json                  # Downstream crew configuration seed
├── tokens/
│   ├── base.tokens.json                  # W3C DTCG — global tier
│   ├── semantic.tokens.json              # W3C DTCG — semantic tier
│   ├── component.tokens.json             # W3C DTCG — component-scoped tier
│   ├── diff.json                         # Structured token diff (added/modified/removed)
│   └── compiled/
│       ├── variables.css                 # CSS custom properties (default theme)
│       ├── variables-light.css           # Light theme overrides
│       ├── variables-dark.css            # Dark theme overrides
│       ├── variables-high-contrast.css   # High-contrast theme overrides
│       ├── variables.scss                # SCSS variables
│       ├── tokens.ts                     # TypeScript constants
│       └── tokens.json                   # Flat resolved JSON
├── specs/
│   ├── Box.spec.yaml                     # Primitive specs
│   ├── Stack.spec.yaml
│   ├── ThemeProvider.spec.yaml
│   ├── ...                               # .spec.yaml per primitive
│   ├── Button.spec.yaml                  # Component specs
│   ├── Input.spec.yaml
│   └── ...
├── src/
│   ├── primitives/
│   │   ├── Box.tsx
│   │   ├── Box.test.tsx
│   │   ├── Box.stories.tsx
│   │   ├── Stack.tsx
│   │   ├── Text.tsx
│   │   ├── Grid.tsx
│   │   ├── Icon.tsx
│   │   ├── Pressable.tsx
│   │   ├── Divider.tsx
│   │   ├── Spacer.tsx
│   │   ├── ThemeProvider.tsx
│   │   ├── ...                           # .test.tsx + .stories.tsx per primitive
│   │   └── index.ts
│   ├── components/
│   │   ├── Button/
│   │   │   ├── Button.tsx
│   │   │   ├── Button.test.tsx
│   │   │   └── Button.stories.tsx
│   │   ├── Input/
│   │   │   └── ...
│   │   └── index.ts
│   └── index.ts
├── docs/
│   ├── README.md
│   ├── tokens.md                         # Token catalog
│   ├── components/
│   │   ├── Button.md
│   │   └── ...
│   ├── decisions/                        # Architecture decision records
│   │   ├── generation-narrative.md       # Why the DS looks the way it does
│   │   ├── ADR-001-archetype-selection.md
│   │   ├── ADR-002-token-scale-rationale.md
│   │   └── ...
│   ├── changelog.md                      # Generation changelog
│   ├── templates/                        # RFC and governance templates
│   │   └── rfc-template.md
│   └── search-index.json                 # Full-text search index
├── governance/
│   ├── ownership.json                    # Component ownership map
│   ├── quality-gates.json                # Gate thresholds config
│   ├── deprecation-policy.json           # Lifecycle rules
│   └── workflow.json                     # Contribution pipeline definition
├── registry/
│   ├── components.json                   # Full component registry (AI-consumable)
│   ├── tokens.json                       # Semantic token graph (AI-consumable)
│   ├── composition-rules.json            # Valid composition trees
│   └── compliance-rules.json             # Code compliance ruleset
├── reports/
│   ├── quality-scorecard.json            # Per-component quality scores
│   ├── a11y-audit.json                   # Accessibility audit results
│   ├── token-compliance.json             # Hardcoded value scan
│   ├── composition-audit.json            # Structural integrity report
│   ├── drift-report.json                 # Spec ↔ code ↔ docs consistency
│   └── generation-summary.json           # Full pipeline execution report
├── tests/
│   ├── tokens.test.ts                    # Token validity + reference tests
│   ├── a11y.test.ts                      # Accessibility tests
│   ├── composition.test.ts               # Structural composition tests
│   └── compliance.test.ts                # Token usage compliance tests
├── screenshots/                          # Render validation baselines
│   ├── Button--primary.png
│   ├── Button--disabled.png
│   └── ...
├── .cursorrules                          # Cursor AI context
├── copilot-instructions.md               # GitHub Copilot context
└── ai-context.json                       # Generic LLM context
```

---

## 3. Architecture

### 3.1 Pipeline

Sequential at the phase level with bounded inter-phase retry loops. Each crew's output is the next crew's input. No event bus, no pub/sub, no external triggers. The pipeline advances phase-by-phase, but the retry protocol (§3.4) allows the First Publish Agent (6) to loop between adjacent phases when a downstream validation rejects upstream output — up to the retry limit. This means the pipeline is *forward-sequential* (Phase 3 never runs before Phase 2) but *not strictly one-shot* (Phase 2 can re-trigger Phase 1 agents before advancing).

```
PHASE 1 — DISCOVERY & FOUNDATION
  DS Bootstrap Crew → Brand Profile + raw token set (3 tiers) + canonical spec YAMLs + pipeline config + project scaffolding (tsconfig, build config)

PHASE 2 — TOKEN VALIDATION & COMPILATION
  Token Engine Crew → Validated tokens, compiled to CSS/SCSS/TS/JSON per theme

PHASE 3 — COMPONENT GENERATION
  Design-to-Code Crew → TSX source + tests + stories from canonical specs
  Component Factory Crew → Validated, accessible, scored components

PHASE 4 — DOCUMENTATION & GOVERNANCE (strictly ordered)
  4a. Documentation Crew → Full docs, catalog, decisions, search index
  4b. Governance Crew → Ownership, quality gates, lifecycle config
       (depends on Documentation Crew output: checks "all components have docs")

PHASE 5 — INTELLIGENCE & QUALITY
  AI Semantic Layer Crew → Component registry, token graph, composition rules
  Analytics Crew → Quality reports, compliance scans, consistency checks

PHASE 6 — RELEASE & ASSEMBLY
  Release Crew → Package assembly, changelog, version tag, test execution
```

**Intra-phase ordering:** Where a phase contains multiple crews, order matters when one crew's checks depend on another crew's output. Phase 4 is strictly ordered: Documentation Crew runs first, then Governance Crew — because the Quality Gate Agent (30) checks "all components have docs," which requires documentation to exist. Phase 3 is also ordered: Design-to-Code before Component Factory. Phase 5 crews (AI Semantic Layer and Analytics) have no mutual dependency and may run in either order.

### 3.2 Architectural Principles

**Agent-first, tool-assisted.** Every workflow is agent-orchestrated. Deterministic tools are invoked by agents, never run standalone.

**Token-first.** Every visual decision originates as a design token. Tokens are the atomic unit of truth.

**Human gates, not human labor.** Agents handle orchestration. Humans review and approve at defined gates.

**Canonical source, compiled tokens.** One authoring format per artifact. Tokens are authored in W3C DTCG and compiled to multiple platform outputs (CSS, SCSS, TS, JSON).

**Sequential crew handoff.** Each crew writes its output to the shared folder structure. The next crew reads from it. The output folder is the shared state.

**Plugin architecture.** Every tool, compiler, and linter is a plugin. The pipeline is extensible without forking core.

### 3.3 Agentic vs. Deterministic — Decision Log

Not everything benefits from agents. Agents decide; deterministic tools execute.

| Capability | Mode | Rationale |
|---|---|---|
| Brand interview / discovery | **Agent** | Conversational reasoning. Translates brand values into token decisions. |
| Token schema validation | **Agent** | Interprets ambiguous naming violations, suggests fixes. |
| Token compilation (JSON → CSS/SCSS/TS) | **Deterministic** | Pure data transformation. Agent triggers, tool executes. |
| WCAG contrast calculation | **Deterministic** | Mathematical formula. Agent invokes and interprets. |
| Code generation from specs | **Agent** | Understanding structural intent, handling ambiguity, pattern memory. |
| Render validation / smoke test | **Hybrid** | Headless rendering is deterministic. Interpreting failures and classifying severity is agent. |
| Semver calculation | **Hybrid** | Parsing is deterministic. Edge cases benefit from agent reasoning. |
| Changelog generation | **Agent** | Synthesizes generation decisions into coherent prose. |
| Codemod generation | **Agent** | Understanding old API, new API, generating AST transformations. |
| A11y audit execution | **Deterministic** | axe-core is deterministic. Agent interprets and decides block/warn. |
| Doc page generation | **Agent** | Synthesizes code, tokens, specs into coherent docs. |
| Ownership assignment | **Agent** | Reasoning about component relationships and domain boundaries. |
| Drift detection (spec ↔ code ↔ docs) | **Hybrid** | Structural comparison is deterministic. Interpreting gaps requires reasoning. |
| Token compliance scan | **Deterministic** | AST-based static analysis. Agent invokes and interprets. |
| Initial token scale generation | **Agent** | Creative reasoning: harmonious palettes, type scales, spacing from brand inputs. |
| Folder scaffolding | **Deterministic** | Template-based file generation. Agent decides what; tool writes. |
| Quality scoring | **Hybrid** | Metrics are deterministic. Weighting and gating decisions are agent. |
| Composition rule validation | **Deterministic** | Rule engine checks. Agent decides escalation. |
| Search index building | **Deterministic** | Text indexing. Agent decides what to index and tag. |
| Component registry assembly | **Agent** | Synthesizing specs, props, variants, tokens, examples into coherent registry. |

**Principle:** When in doubt, make it agentic. An agent invoking a deterministic tool is strictly more capable than the tool alone.

### 3.4 Retry Protocol

The pipeline is not one-shot. When a validation agent rejects output from a generation agent, the pipeline enters a bounded retry loop:

1. The validation agent produces a structured rejection: which checks failed, what the specific errors are, and what a fix would look like.
2. The rejection is fed back to the originating generation agent as additional context appended to the original task.
3. The generation agent produces a corrected output incorporating the feedback.
4. The corrected output is re-validated.
5. This loop runs for a maximum of **3 retry attempts** per component per validation stage.
6. If a component still fails after 3 retries, it is marked as `failed` in the generation report, the Rollback Agent preserves its last best attempt, and the pipeline continues with remaining components.

Retry loops apply at these boundaries:

| Generator | Validator | Retry Trigger |
|---|---|---|
| Token Foundation Agent (2) | Token Validation Agent (8) | Naming violation, contrast failure, broken reference |
| Code Generation Agent (14) | Spec Validation Agent (17) | Missing props, invalid state transitions, broken token refs |
| Code Generation Agent (14) | Render Validation Agent (15) | Render failure, empty output, visual artifact |
| Code Generation Agent (14) | TypeScript Compiler (deterministic) | Type errors, import errors |
| Accessibility Agent (19) | axe-core (deterministic) | Critical a11y violation after patching |
| Accessibility Agent (19) | TypeScript Compiler + Render Validation Agent (15) | A11y patches introduced type errors or render regressions |

**Post-patch re-validation:** The Accessibility Agent (19) modifies component source in place to add ARIA attributes, keyboard handlers, and focus management. Because these patches can introduce TypeScript errors or render regressions, the Component Factory Crew triggers a re-validation pass after a11y patching: the patched source is re-compiled (`tsc --noEmit`) and re-rendered (Render Validation Agent). If this fails, the retry loop feeds the error back to the Accessibility Agent for correction.

The retry context accumulates: attempt 2 sees the original task + attempt 1 rejection. Attempt 3 sees original + rejection 1 + rejection 2. This gives the agent increasing information to correct its approach.

**Cross-phase retry routing:** Some retry boundaries span crew and phase boundaries (e.g., Token Foundation Agent in Phase 1 ↔ Token Validation Agent in Phase 2). The First Publish Agent (6) handles this: when a Phase 2 validation fails, Agent 6 detects the failure, re-invokes the originating Phase 1 agent with the rejection context, then re-runs the Phase 2 crew. This means Phases are not strictly one-shot — Agent 6 can loop between adjacent phases up to the retry limit. The Rollback Agent (40) restores checkpoints before each re-run to prevent artifact corruption.

Components that exhaust retries are not silently dropped. The generation report lists them with full error traces, and the Pipeline Completeness Agent (34) flags them as stuck.

**Rollback cascade policy:** The Component Factory Crew (Phase 3) patches `src/` in place for a11y fixes. If the Rollback Agent restores a pre-Component-Factory checkpoint (because a downstream crew failed catastrophically), all in-place a11y patches are lost. To handle this, rollback always cascades forward: when a checkpoint is restored, all crews after the restored phase are invalidated and must re-run. The First Publish Agent (6) enforces this — it never resumes mid-sequence after a rollback. This means rollback is expensive (it replays subsequent phases) but safe (no crew reads stale artifacts from a previous run).

**Retry protocol for Phases 4–6:** The retry table above covers generator ↔ validator pairs in Phases 1–3. Phases 4–6 (Documentation, Governance, AI Semantic Layer, Analytics, Release) use a simpler model: if a crew fails (e.g., Doc Generation Agent produces invalid Markdown, or Search Index Agent fails to build the index), the First Publish Agent (6) retries the entire crew up to **2 attempts**. No per-agent retry within these crews — they are fast enough to re-run entirely. If a Phase 4–6 crew exhausts retries, it is marked as `failed` in the generation report, and the pipeline continues. Phase 4–6 failures are non-fatal to the core design system (components, tokens, tests are already validated) — they degrade documentation, governance, or analytics quality but do not block the output review gate.

**Resume-on-failure:** The checkpoint system enables resumption after catastrophic failures (process crash, LLM API outage). The Rollback Agent (40) writes checkpoints as timestamped snapshots of the output folder at each phase boundary. To resume, the user re-runs the CLI with a `--resume` flag pointing to the output folder. The First Publish Agent (6) detects the last successful checkpoint, validates its integrity (all expected files present and non-corrupt), and resumes from the next phase. Resume does not retry the failed phase automatically — it re-runs it from scratch with a clean slate. If the checkpoint is corrupt or incomplete, the CLI reports the issue and asks the user whether to restart from Phase 1.

### 3.5 Theming Model

The design system supports multiple themes (light, dark, high-contrast, or custom brand themes) through a token-level architecture. Themes do not affect component code — components are theme-agnostic by design.

**Token structure:** Semantic tokens carry per-theme values. In the W3C DTCG files, each semantic token defines its resolved value per theme:

```json
{
  "color": {
    "background": {
      "surface": {
        "$type": "color",
        "$value": "{color.neutral.100}",
        "$extensions": {
          "com.daf.themes": {
            "light": "{color.neutral.100}",
            "dark": "{color.neutral.900}",
            "high-contrast": "{color.neutral.1000}"
          }
        }
      }
    }
  }
}
```

**Compilation:** The Token Compilation Agent (9) produces a separate CSS file per theme (`variables-light.css`, `variables-dark.css`, `variables-high-contrast.css`). Each file contains the same custom property names with different values. Theme switching is a single CSS file swap or class-based scope.

**ThemeProvider primitive:** A `ThemeProvider` component is generated as part of the primitives set. It handles runtime theme switching via CSS class application on the root element and exposes a `useTheme()` hook for programmatic access. It does not use JavaScript to toggle individual token values — it switches the active CSS scope.

**Component contract:** Components consume only semantic tokens. They never reference global tokens or theme-specific values directly. This means every component works in every theme without modification. The Token Compliance Agent (32) enforces this by flagging any direct global token usage in component source.

**Multi-brand:** For the Multi-Brand archetype, themes extend to brand layers. A base theme defines the structure; brand overrides replace specific semantic token values. The Token Foundation Agent (2) generates the base + override structure from the Brand Profile.

**Multi-brand file structure:** Each brand produces a separate override token file alongside the base tokens:

```
tokens/
├── base.tokens.json              # Global tier (shared across all brands)
├── semantic.tokens.json          # Base semantic tier (default brand)
├── component.tokens.json         # Base component-scoped tier
├── brands/
│   ├── brand-a.tokens.json       # Brand A semantic overrides
│   ├── brand-b.tokens.json       # Brand B semantic overrides
│   └── ...                       # One file per brand
└── compiled/
    ├── variables.css             # Default brand, default theme
    ├── variables-light.css       # Default brand, light theme
    ├── variables-dark.css        # Default brand, dark theme
    ├── brand-a/
    │   ├── variables.css         # Brand A, default theme
    │   ├── variables-light.css   # Brand A, light theme
    │   └── variables-dark.css    # Brand A, dark theme
    └── brand-b/
        └── ...                   # Same structure per brand
```

Brand override files contain only the semantic tokens that differ from the base. They are merged at compilation time: base + brand override → brand-specific compiled output. The ThemeProvider handles brand switching as an additional dimension alongside theme switching — it applies both a theme class and a brand class to the root element (e.g., `class="theme-dark brand-a"`). The `useTheme()` hook exposes both `theme` and `brand` properties. Brand names are defined in the Brand Profile under `themes.brands` (an array of brand identifier strings).

---

### 3.6 Crew I/O Contracts

Each crew reads from and writes to the shared output folder. These contracts define the explicit file-level dependencies between crews. A crew fails-fast if its required inputs are missing.

| Crew | Reads (required) | Reads (optional) | Writes |
|---|---|---|---|
| **DS Bootstrap** | User interview input (raw `brand-profile.json` from CLI) | — | `brand-profile.json` (validated), `specs/*.spec.yaml`, `tokens/base.tokens.json` (raw), `tokens/semantic.tokens.json` (raw), `tokens/component.tokens.json` (raw), `pipeline-config.json`, `tsconfig.json`, `vitest.config.ts`, `vite.config.ts` |
| **Token Engine** | `tokens/base.tokens.json` (raw, from Token Foundation Agent), `tokens/semantic.tokens.json` (raw), `tokens/component.tokens.json` (raw) | `brand-profile.json` | `tokens/base.tokens.json` (validated), `tokens/semantic.tokens.json` (validated), `tokens/component.tokens.json` (validated), `tokens/compiled/*`, `tokens/diff.json` |
| **Design-to-Code** | `specs/*.spec.yaml`, `tokens/compiled/*` | `brand-profile.json` | `src/primitives/*.tsx`, `src/primitives/*.test.tsx`, `src/primitives/*.stories.tsx`, `src/components/**/*.tsx`, `src/components/**/*.test.tsx`, `src/components/**/*.stories.tsx`, `reports/generation-summary.json`, `screenshots/*` |
| **Component Factory** | `specs/*.spec.yaml`, `src/primitives/*.tsx`, `src/components/**/*.tsx`, `tokens/semantic.tokens.json`, `brand-profile.json` | — | `reports/quality-scorecard.json`, `reports/a11y-audit.json`, `reports/composition-audit.json` (patches `src/` in place for a11y fixes) |
| **Documentation** | `specs/*.spec.yaml`, `src/components/**/*.tsx`, `tokens/*.tokens.json`, `reports/generation-summary.json` | `brand-profile.json`, `tokens/diff.json` | `docs/**/*.md`, `docs/search-index.json` |
| **Governance** | `brand-profile.json`, `pipeline-config.json`, `specs/*.spec.yaml`, `reports/quality-scorecard.json` | — | `governance/*.json`, `docs/templates/*`, `tests/tokens.test.ts`, `tests/a11y.test.ts`, `tests/composition.test.ts`, `tests/compliance.test.ts` |
| **Analytics** | `specs/*.spec.yaml`, `src/**/*.tsx`, `docs/components/*.md`, `tokens/*.tokens.json` | — | `reports/token-compliance.json`, `reports/drift-report.json` |
| **AI Semantic Layer** | `specs/*.spec.yaml`, `src/primitives/*.tsx`, `src/components/**/*.tsx`, `tokens/*.tokens.json`, `reports/composition-audit.json` | — | `registry/*.json`, `.cursorrules`, `copilot-instructions.md`, `ai-context.json` |
| **Release** | All of the above (reads entire output folder) | — | `package.json`, `src/index.ts`, `docs/changelog.md`, barrel `index.ts` files, updates `reports/generation-summary.json` with final test results |

**Bootstrap output contract:** The Bootstrap Crew produces five categories of artifacts that feed different downstream crews:
1. **Brand Profile** (`brand-profile.json`) — read by nearly every crew for configuration decisions.
2. **Raw token files** (`tokens/*.tokens.json`) — picked up by Token Engine Crew for validation and compilation. Bootstrap writes raw tokens; Token Engine validates and compiles them.
3. **Canonical spec YAMLs** (`specs/*.spec.yaml`) — picked up by Design-to-Code Crew for code generation. Bootstrap writes specs; Design-to-Code produces TSX/tests/stories from them.
4. **Pipeline config** (`pipeline-config.json`) — picked up by Governance Crew as its input seed. Bootstrap infers governance settings from the Brand Profile; Governance Crew generates the full governance artifacts.
5. **Project scaffolding** (`tsconfig.json`, `vitest.config.ts`, `vite.config.ts`) — generated by the Pipeline Configuration Agent (5) alongside `pipeline-config.json`. These files are required by Phase 2+ crews for TypeScript compilation (`tsc --noEmit`), test execution, and build validation. They are generated in Phase 1 so that all downstream crews can compile and test without waiting for the Release Crew.

No crew produces both specs and code for the same component. No crew produces both raw tokens and compiled tokens.

---

### 3.7 Model Assignment Strategy

Not all agents require the same LLM capability. To balance cost, latency, and quality, agents are assigned to model tiers based on their task complexity. All tiers use **Anthropic models exclusively**.

| Tier | Model | Agents | Rationale |
|---|---|---|---|
| **Tier 1 — Generative** | Claude Opus | Code Generation (14), Accessibility (19), Doc Generation (21), Generation Narrative (23), Registry Maintenance (41) | Produce complex, multi-file code or prose requiring deep reasoning. |
| **Tier 2 — Analytical** | Claude Sonnet | Brand Discovery (1), Token Foundation (2), Intent Extraction (13), Drift Detection (33), Composition Constraint (43) | Analyze structured input, make reasoned decisions, but don't generate large code artifacts. |
| **Tier 3 — Classification** | Claude Haiku | Scope Classification (12), Token Ingestion (7), Semver (36), Pipeline Completeness (34) | Classification, routing, simple structural checks. |
| **Deterministic** | No LLM | Token Compilation (9), Render Validation (15), Quality Scoring (20), Search Index (25) | Pure tool invocation — agent logic is routing only. |

Model assignment is configurable per-run via environment variables (`DAF_TIER1_MODEL`, `DAF_TIER2_MODEL`, `DAF_TIER3_MODEL`). Defaults: `claude-sonnet-4-20250514` (Tier 1), `claude-sonnet-4-20250514` (Tier 2), `claude-haiku-4-20250414` (Tier 3). For maximum quality, set Tier 1 to `claude-opus-4-20250514`.

---

### 3.8 Pipeline Configuration Schema

The `pipeline-config.json` file bridges the Brand Profile (user intent) and the Governance Crew (operational rules). It is generated by the Pipeline Configuration Agent (5) and consumed by the Governance Crew as its input seed.

```json
{
  "qualityGates": {
    "minCompositeScore": "number (0-100, default 70)",
    "minTestCoverage": "number (0-100, percentage, default 80)",
    "a11yLevel": "AA | AAA (from Brand Profile)",
    "blockOnWarnings": "boolean (default false)"
  },
  "lifecycle": {
    "defaultStatus": "stable | beta | experimental",
    "betaComponents": "string[] (component names defaulting to beta, e.g., complex Comprehensive-tier components)",
    "deprecationGracePeriodDays": "number (default 90)"
  },
  "domains": {
    "categories": "string[] (e.g., ['forms', 'navigation', 'feedback', 'layout', 'data-display'])",
    "autoAssign": "boolean (default true, lets Ownership Agent auto-assign)"
  },
  "retry": {
    "maxComponentRetries": "number (default 3)",
    "maxCrewRetries": "number (default 2, for Phases 4-6)"
  },
  "models": {
    "tier1": "string (model identifier)",
    "tier2": "string (model identifier)",
    "tier3": "string (model identifier)"
  },
  "buildConfig": {
    "tsTarget": "string (e.g., 'ES2020')",
    "moduleFormat": "string (e.g., 'ESNext')",
    "cssModules": "boolean (default false)"
  }
}
```

The Governance Crew reads this file and expands it into the full governance artifacts (`ownership.json`, `quality-gates.json`, `deprecation-policy.json`, `workflow.json`). The `pipeline-config.json` is a seed — the Governance Crew adds structure, detail, and operational rules that the Pipeline Configuration Agent cannot infer from the Brand Profile alone.

---

## 4. Crew Specifications

9 crews. 45 agents.

---

### 4.1 DS Bootstrap Crew (6 agents)

**Purpose:** Guide creation of a new design system from zero. The crew operates in two steps: first, a **pre-pipeline interview CLI** collects user input into a raw Brand Profile; then, the crew's agents validate, enrich, and execute generation from that profile. This separation keeps the interactive conversation outside CrewAI's task execution model while preserving the agent intelligence for everything that follows.

**Agent 1: Brand Discovery Agent**
- Role: Brand profile validator and enricher
- Goal: Receive the raw Brand Profile collected by the interview CLI. Validate all fields for completeness and internal consistency (e.g., reject "compact density" paired with "spacious spacing"). Resolve the selected archetype into concrete defaults for any unspecified fields. Detect contradictions and fill sensible defaults. Output the finalized, validated Brand Profile that seeds all downstream crews.
- Tools: Brand Profile Schema Validator, Archetype Resolver, Consistency Checker, Default Filler
- Input: Raw `brand-profile.json` from interview CLI
- Output: Validated, enriched `brand-profile.json`
- ⚠ Human Gate: User must approve the finalized Brand Profile before generation begins.

**Pre-pipeline Interview CLI:** A dedicated CLI tool (outside CrewAI) conducts the structured conversation with the user. It presents archetype options, collects color/typography/spacing preferences, asks about scope, and writes a raw `brand-profile.json`. The CLI is a simple Q&A flow — all intelligence (validation, enrichment, contradiction detection, default resolution) lives in the Brand Discovery Agent. This means the interview can also be bypassed entirely by providing a hand-written `brand-profile.json`.

**Agent 2: Token Foundation Agent**
- Role: Initial token set generator
- Goal: Generate the complete initial token set from the Brand Profile: color palette (primitive + semantic tiers) with automatic contrast-safe pairing, typography scale (modular scale from brand type preferences), spacing scale (4px/8px base grid), elevation/shadow scale, border radius scale, motion/easing curves, breakpoint definitions, opacity scale. All three tiers (global, semantic, component-scoped) in W3C DTCG format. Writes raw token files to `tokens/`. The Token Engine Crew (Phase 2) picks up these files for validation and compilation — this is a file-based handoff between phases, not an inline delegation.
- Tools: Color Palette Generator, Modular Scale Calculator, Contrast-Safe Pairer, W3C DTCG Formatter
- Output: `tokens/base.tokens.json`, `tokens/semantic.tokens.json`, `tokens/component.tokens.json` (all raw, pre-validation)

**Agent 3: Primitive Scaffolding Agent**
- Role: Base component spec author
- Goal: Generate canonical spec YAMLs for the full set of composition primitives: Box, Stack (HStack, VStack), Grid, Text, Icon, Pressable, Divider, Spacer, ThemeProvider. Each spec defines: props, token bindings, allowed children, composition rules, and a11y requirements. Specs reference only tokens from the foundation (no hardcoded values). Writes to `specs/`. The Design-to-Code Crew (Phase 3) produces TSX source from these specs, and the Component Factory Crew validates the output.
- Tools: Primitive Spec Template Library, Token Binding Schema

**Agent 4: Core Component Agent**
- Role: Component spec author
- Goal: Generate canonical spec YAMLs for the component set defined by the Brand Profile's scope tier. Starter: Button, Input, Checkbox, Radio, Select, Card, Badge, Avatar, Alert, Modal. Standard adds: Table, Tabs, Accordion, Tooltip, Toast, Dropdown, Pagination, Breadcrumb, Navigation. Comprehensive adds: DatePicker, DataGrid, TreeView, Drawer, Stepper, FileUpload, RichText. Each spec defines: props with types and defaults, variants, interactive states, token bindings, composition from primitives, slot definitions, and a11y requirements. Writes to `specs/`. Incorporates any `componentOverrides` from the Brand Profile for component-specific design decisions.
- Tools: Component Spec Template Library, Variant Schema Generator, State Machine Definer

**Agent 5: Pipeline Configuration Agent**
- Role: Downstream crew configurator and project scaffolder
- Goal: Generate a `pipeline-config.json` that configures how downstream crews should operate for this specific design system (see §3.8 for schema). Derived from the Brand Profile: which quality gate thresholds to apply (stricter for AAA accessibility), which lifecycle statuses to default to (beta for Comprehensive scope's complex components), which domain categories to use for ownership mapping (inferred from component scope). This file is read by the Governance Crew (Phase 4b) as its input seed — the Governance Crew then generates the full governance artifacts. Agent 5 does NOT write to `governance/` directly. Additionally, generate the project scaffolding files required by downstream crews: `tsconfig.json` (TypeScript compiler configuration), `vitest.config.ts` (test runner configuration), and `vite.config.ts` (library-mode build configuration). These must exist before Phase 2 so that all downstream crews can compile, test, and build.
- Tools: Config Generator, Threshold Calculator, Domain Inferrer, Project Scaffolder
- Output: `pipeline-config.json`, `tsconfig.json`, `vitest.config.ts`, `vite.config.ts`

**Agent 6: First Publish Agent**
- Role: Pipeline orchestrator
- Goal: Orchestrate the full generation pipeline by invoking all downstream crews in sequence: Token Engine Crew → Design-to-Code Crew → Component Factory Crew → Documentation Crew → Governance Crew → AI Semantic Layer Crew → Analytics Crew → Release Crew. Aggregates results and final status.
- Tools: Crew Sequencer, Result Aggregator, Status Reporter
- ⚠ Human Gate: User reviews the final generation report and output folder before the result is considered complete.

**DS Archetypes:**
- Enterprise B2B: Conservative palette, readable type scale, dense layouts, comprehensive scope, AA.
- Consumer B2C: Vibrant palette, expressive type scale, spacious layouts, standard scope, AA.
- Mobile-First: Compact density, touch-optimized spacing, limited breakpoints, starter scope + native, AAA.
- Multi-Brand Platform: Neutral base + brand override layers, standard scope, all themes, AA.
- Custom: Full conversational discovery from scratch.

**Tasks:** T1: Validate/enrich Brand Profile → T2: Generate token foundation → T3: Author primitive specs → T4: Author component specs → T5: Generate pipeline config → T6: Orchestrate full pipeline run.

---

### 4.2 Token Engine Crew (5 agents)

**Purpose:** Validate and compile the token set produced by the Token Foundation Agent (Phase 1). Enforce schema compliance, naming conventions, WCAG contrast, multi-tier reference integrity, and compile to all target platforms. The Token Engine Crew does not create tokens — it ensures the tokens created by Bootstrap are correct and produces the compiled outputs that all downstream crews consume.

**Agent 7: Token Ingestion Agent**
- Role: Canonical token gatekeeper
- Goal: Receive token data from the Token Foundation Agent, normalize to W3C DTCG format, detect duplicates and naming conflicts, stage for validation.
- Tools: DTCG Schema Validator, JSON Normalizer, Duplicate Detector

**Agent 8: Token Validation Agent**
- Role: Token schema and naming enforcer
- Goal: Validate all staged tokens for structural correctness: W3C DTCG schema compliance, naming convention adherence (consistent casing, category prefixes, no abbreviations), and WCAG contrast ratio verification for all declared foreground/background color pairs. Does not check cross-tier reference integrity — that is the Token Integrity Agent's responsibility.
- Tools: WCAG Contrast Calculator, Naming Linter, DTCG Schema Validator

**Agent 9: Token Compilation Agent**
- Role: Multi-platform, multi-theme compiler operator
- Goal: Invoke compiler pipeline for all configured targets: CSS Custom Properties, SCSS variables, TypeScript constants, flat JSON, and any additional targets from Brand Profile (Tailwind, Swift, Android XML, Compose). For CSS output, produce a separate file per theme defined in the Brand Profile (`variables-light.css`, `variables-dark.css`, `variables-high-contrast.css`, etc.) — each file contains the same custom property names with theme-specific resolved values, as defined by the theming model (§3.5). Also produce a default `variables.css` that matches the Brand Profile's default theme.
- Tools: Style Dictionary Compiler, Theme Resolver, Custom Compiler Plugins

**Agent 10: Token Integrity Agent**
- Role: Cross-tier reference graph enforcer
- Goal: Build and validate the full token reference graph across all three tiers. Enforce tier discipline: component tokens must reference semantic tokens, semantic tokens must reference global tokens — no tier skipping. Detect circular references. Flag orphaned tokens (defined but never referenced by any component or semantic token). Flag phantom references (a token references another that does not exist). This is purely structural graph analysis, distinct from the schema and naming checks performed by the Token Validation Agent (8).
- Tools: Reference Graph Walker, Circular Ref Detector, Orphan Scanner, Phantom Ref Scanner

**Agent 11: Token Diff Agent**
- Role: Change documentation feeder
- Goal: Generate structured diffs of the token set: added, modified, removed, deprecated tokens with full context. Feed diff data to Documentation Crew for changelog (via `tokens/diff.json`, read as optional input) and to Analytics Crew for compliance reports. In initial generation (no prior version exists), the diff is a full inventory: all tokens are classified as `added`, with no `modified` or `removed` entries. This ensures a consistent diff format regardless of whether the run is an initial generation or a future re-generation, and provides the Documentation Crew with a structured token inventory for the changelog.
- Tools: JSON Diff Engine, Deprecation Tagger

**Tasks:** T1: Ingest/normalize → T2: Validate schema/naming/contrast → T3: Compile all platforms → T4: Verify reference graph integrity → T5: Generate diff, feed downstream.

**NFRs:** Compilation (5K tokens): <30s. Full pipeline: <90s.

---

### 4.3 Design-to-Code Crew (5 agents)

**Purpose:** Transform canonical component specs (produced by the Bootstrap Crew) into production code. Classify the generation scope, extract structural intent from each spec YAML, generate TypeScript/TSX source + tests + stories, validate render output, and assemble generation results.

**Agent 12: Scope Classification Agent**
- Role: Generation scope classifier
- Goal: Analyze the Brand Profile and component scope to classify the generation workload: which components are token-only (primitives), which require complex state machines, which need multi-variant generation. Prioritize the generation queue (dependencies first: primitives → simple → complex).
- Tools: Scope Analyzer, Dependency Graph Builder, Priority Queue

**Agent 13: Intent Extraction Agent**
- Role: Structural intent analyst
- Goal: For each component spec, extract: layout structure, spacing model, breakpoint behavior, interactive states, slot definitions, a11y attribute requirements. Output a structured intent manifest per component.
- Tools: Spec Parser, Layout Analyzer, A11y Attribute Extractor

**Agent 14: Code Generation Agent**
- Role: Canonical component coder
- Goal: Generate production-quality TypeScript/TSX component source from intent manifests. For each component, produce three files: the component source (`.tsx`), unit tests (`.test.tsx`), and Storybook stories (`.stories.tsx`). Component source must: use only compiled tokens (zero hardcoded values), compose from primitives, support all specified variants, pass lint checks, include `data-testid` attributes. Stories must showcase every variant and interactive state. Uses pattern memory to maintain consistency across components.
- Tools: Code Scaffolder, ESLint Runner, Story Template Generator, Pattern Memory Store

**Agent 15: Render Validation Agent**
- Role: Visual smoke test and baseline capture
- Goal: Render each generated component and every declared variant headlessly. Verify that: every variant produces non-empty visual output, no render errors or React exceptions occur, output dimensions exceed minimum thresholds (no zero-width/zero-height elements), and interactive states (hover, focus, disabled) render distinctly. Capture screenshots of all variants as baseline references (stored in `screenshots/`) for use in future regression diffing. This is a render *validation* — not a regression comparison, since there are no prior baselines to compare against in an initial generation.
- Tools: Playwright Headless Renderer, Screenshot Capture, Render Error Detector, Dimension Validator

**Agent 16: Result Assembly Agent**
- Role: Generation report assembler
- Goal: Assemble the generation output: structured summary per component (what was generated, confidence score, any warnings), visual reference screenshots, mapping of spec → code → test. Write results to `reports/generation-summary.json`.
- Tools: Summary Generator, Confidence Scorer, Report Writer

**Tasks:** T1: Classify scope → T2: Extract intent per component → T3: Generate code + tests + stories → T4: Render validation → T5: Assemble generation report.

**NFRs:** Single component: <5 min. Batch (starter scope, 10 components): <20 min. Batch (comprehensive, 25+ components): <60 min.

---

### 4.4 Component Factory Crew (4 agents)

**Purpose:** Enforce composability, accessibility, and quality through structured validation. Every generated component passes through this crew before being accepted.

**Agent 17: Spec Validation Agent**
- Role: Canonical spec gatekeeper
- Goal: Validate every component spec against JSON Schema: required fields present, all token refs resolve, state transitions are valid (no impossible states), nesting rules respected, prop types complete.
- Tools: JSON Schema Validator, Token Ref Checker, State Machine Validator

**Agent 18: Composition Agent**
- Role: Structural integrity enforcer
- Goal: Verify every component composes from base primitives (Box, Stack, Grid, Text, Icon, Pressable). Check: allowed children constraints, forbidden nesting patterns (e.g., no Pressable inside Pressable), required slots filled, composition depth within limits.
- Tools: Composition Rule Engine, Primitive Registry, Nesting Validator

**Agent 19: Accessibility Agent**
- Role: A11y-first enforcer
- Goal: Review and patch every component for: correct ARIA roles and attributes per state, keyboard navigation handlers (Tab, Enter, Escape, Arrow keys), focus management (trap, restore, programmatic focus), screen-reader announcements for dynamic state changes. Generate component-level a11y test cases as additional test blocks appended to the existing `.test.tsx` files created by the Code Generation Agent (14) — not as separate files. Each appended block is wrapped in a `describe('Accessibility', () => { ... })` suite within the existing test file, ensuring a single test file per component. The Accessibility Agent reads the `brand-profile.json` to determine the target accessibility level (AA or AAA) and adjusts enforcement strictness accordingly: AAA requires stricter contrast ratios, more comprehensive keyboard navigation coverage, and mandatory focus-visible indicators.
- Tools: axe-core Rule Reference, ARIA Generator, Keyboard Nav Scaffolder, Focus Trap Validator

**Agent 20: Quality Scoring Agent**
- Role: Component health assessor
- Goal: Compute a composite quality score (0–100) per component based on what is available at Phase 3. The composite score is a weighted average of five sub-scores: test coverage (25% weight, measured as line coverage percentage), a11y pass rate (25%, percentage of axe-core rules passing), token compliance (20%, percentage of style values sourced from tokens vs hardcoded), composition depth score (15%, primitives-only composition = full marks, direct DOM usage = penalty), and spec completeness (15%, all required fields present in YAML). Gate at **70/100 composite** — components below threshold are flagged in the quality report. Note: the Governance Crew’s Quality Gate Agent (30) enforces a separate **80% minimum test coverage** threshold as an individual gate — a component can pass the 70/100 composite but still fail the 80% coverage gate. Both gates must pass for a component to be fully accepted. Doc completeness is NOT checked here (docs don't exist until Phase 4a) — it is verified later by the Drift Detection Agent (33) in Phase 5.
- Tools: Coverage Reporter, Score Calculator, Threshold Gate

**Tasks:** T1: Validate specs → T2: Verify composition → T3: Scaffold/enforce a11y → T4: Re-validate patched components (compile + render check) → T5: Score and gate.

**NFRs:** Full pipeline: <60s per component.

---

### 4.5 Documentation Crew (5 agents)

**Purpose:** Generate all documentation from code, tokens, and generation metadata. Documentation is a derived artifact — never separately authored.

**Agent 21: Doc Generation Agent**
- Role: Automated documentation writer
- Goal: Generate component docs per component: prop table (types, defaults, required), variant showcase (all variants with descriptions), usage examples (at least 2 per component: basic + advanced), token binding reference (which tokens the component uses). Coherent prose, not just tables. Also generate the project `docs/README.md`: installation instructions (`npm install`), quick start (import and use a component), available components list, available tokens overview, and links to detailed docs.
- Tools: Spec-to-Doc Renderer, Prop Table Generator, Example Code Generator, README Template

**Agent 22: Token Catalog Agent**
- Role: Visual token documentation builder
- Goal: Generate the token catalog: every token with its resolved value, tier (global/semantic/component), usage context description, and visual representation (color swatches as hex + description, type scale as size progression, spacing scale as size values). Organized by category.
- Tools: Token Value Resolver, Scale Visualizer, Usage Context Extractor

**Agent 23: Generation Narrative Agent**
- Role: Design decision narrator
- Goal: Write `docs/decisions/generation-narrative.md`: a human-readable account of *why* the design system looks the way it does. Covers: which archetype was selected and why, which Brand Profile choices drove which token decisions, how the modular scale ratio was chosen, what accessibility tier implications affected the palette, any human gate overrides and their justification. This is the *why* document — it explains design rationale, not release contents (which is the Release Changelog Agent's job).
- Tools: Decision Log Reader, Brand Profile Analyzer, Prose Generator

**Agent 24: Decision Record Agent**
- Role: ADR archivist
- Goal: Generate Architecture Decision Records (ADRs) for every significant generation decision: archetype selection rationale, token scale algorithm choice, composition model decisions, accessibility tier implications. Each ADR follows the standard format: Context → Decision → Consequences.
- Tools: Decision Extractor, ADR Template Generator

**Agent 25: Search Index Agent**
- Role: Discoverability operator
- Goal: Build a full-text search index across all docs, components, tokens, and decisions. Write `search-index.json` with: component names, prop names, token names, doc text — all searchable and filterable by category and status.
- Tools: Search Index Builder, Metadata Tagger

**Tasks:** T1: Generate component docs → T2: Generate token catalog → T3: Write generation narrative → T4: Generate ADRs → T5: Build search index.

**NFRs:** Full doc generation: <5 min. Output: Markdown files + JSON search index.

---

### 4.6 Governance Crew (5 agents)

**Purpose:** Generate a **team adoption kit** — structured configuration artifacts that define how the design system should be operated when adopted by a team. Ownership maps, quality gates, deprecation policies, contribution workflows, and RFC templates are generated alongside the code so that the DS is governance-ready from the moment it is shared. These artifacts define organizational structure and process; they become active when real team members are assigned.

**Agent 26: Ownership Agent**
- Role: Component domain mapper
- Goal: Generate an ownership map (`ownership.json`): assign each component and token category to a logical *domain* (e.g., "forms", "navigation", "feedback", "layout", "data-display") based on component function, relationships, and complexity. Flag components that span multiple domains. Detect orphans (components with no clear domain assignment). Domains serve as organizational blueprints — teams assign real people to domains during adoption.
- Tools: Domain Classifier, Relationship Analyzer, Orphan Detector

**Agent 27: Workflow Agent**
- Role: Contribution pipeline definer
- Goal: Generate workflow definitions for the design system's operation: what pipeline a token change must follow, what pipeline a new component must follow, what quality gates apply at each step. Writes `workflow.json` as a state machine definition.
- Tools: Workflow State Machine Generator, Gate Mapper

**Agent 28: Deprecation Agent**
- Role: Lifecycle policy definer
- Goal: Generate the deprecation policy config: default grace period, warning injection rules, migration guide requirements, removal criteria. Tag any experimental or unstable components with appropriate lifecycle status (stable/beta/experimental).
- Tools: Lifecycle Tagger, Deprecation Policy Generator, Stability Classifier

**Agent 29: RFC Agent**
- Role: Decision process definer
- Goal: Generate RFC templates and process definitions for the design system's governance: when an RFC is required (new primitive, breaking token change), template structure, required sections, approval criteria. Writes templates to `docs/templates/`.
- Tools: RFC Template Generator, Process Definition Builder

**Agent 30: Quality Gate Agent**
- Role: Gate threshold enforcer and test author
- Goal: Define and enforce quality gates as individual pass/fail checks (distinct from the composite score computed by Agent 20): minimum **80% test coverage** per component (line coverage), a11y audit pass (zero critical violations), all token references resolve (no phantom refs), all components have docs (verified after Documentation Crew runs in Phase 4a), all components have at least one usage example. A component must pass both the 70/100 composite score (Agent 20) and all individual quality gates (Agent 30) to be fully accepted. Components that fail individual gates are flagged in the quality report with the specific gate that failed. Additionally, generate the project-level test suites that encode these gates as executable tests: `tests/tokens.test.ts` (token JSON validity, DTCG schema, reference resolution), `tests/a11y.test.ts` (all interactive components have ARIA roles), `tests/composition.test.ts` (all components compose from primitives), `tests/compliance.test.ts` (no hardcoded values). These tests are what `npm test` runs to verify the exit criteria.
- Tools: Gate Evaluator, Threshold Config, Report Writer, Test Suite Generator

**Tasks:** T1: Assign ownership → T2: Define workflows → T3: Set deprecation policy → T4: Generate RFC templates → T5: Evaluate quality gates.

---

### 4.7 Analytics Crew (5 agents)

**Purpose:** Analyze the generated design system for quality, consistency, compliance, and structural health. Produces reports.

**Agent 31: Usage Tracking Agent**
- Role: Internal usage analyzer
- Goal: Scan all generated component source for: which tokens are actually used (vs. defined but unused), which primitives are consumed by which components, cross-component import relationships. Identify unused tokens and unreferenced primitives.
- Tools: AST Import Scanner, Token Usage Mapper, Dependency Graph Builder

**Agent 32: Token Compliance Agent**
- Role: Hardcoded value hunter
- Goal: Static analysis of all generated source code for: hardcoded color values (hex, rgb, hsl), hardcoded spacing values (px, rem, em), hardcoded font sizes, deprecated token references. Report every violation with file, line, and suggested token replacement.
- Tools: AST Analyzer, Token Map, Violation Reporter

**Agent 33: Drift Detection Agent**
- Role: Spec ↔ code ↔ docs consistency checker and fixer
- Goal: Compare three representations of each component: the canonical spec (YAML), the generated code (TSX), and the generated docs (Markdown). Flag any inconsistencies: a prop in the spec not present in code, a variant in code not documented, a token referenced in docs that doesn't exist. For each detected inconsistency, the agent determines the authoritative source (spec is always authoritative over code and docs) and applies automated fixes: update docs to match code, or flag code-vs-spec mismatches for the generation report (code fixes require re-running the Code Generation Agent, which is not possible in Phase 5). Write `drift-report.json` with: all detected inconsistencies, which were auto-fixed, and which require manual attention or a pipeline re-run. Auto-fixable drift (docs missing a prop that exists in code and spec) is corrected in place. Non-fixable drift (code missing a prop from spec) is reported with a recommended action ("re-run Design-to-Code Crew for component X").
- Tools: Structural Comparator, Cross-Reference Checker, Drift Reporter, Doc Patcher

**Agent 34: Pipeline Completeness Agent**
- Role: Pipeline completeness tracker
- Goal: Track each component's completeness through the generation pipeline: created → spec validated → code generated → a11y passed → tests written → docs generated → fully complete. Report components stuck at any stage. Recommend interventions (e.g., "Button has code but no tests — generation may have failed at test stage").
- Tools: Pipeline Stage Tracker, Completeness Calculator, Intervention Recommender

**Agent 35: Breakage Correlation Agent**
- Role: Cross-component failure investigator
- Goal: Analyze all test failures present in the final output — both exhausted-retry failures from Phases 2–3 (components that failed validation after 3 attempts) and any test failures from the Release Crew’s final `npm test` run. For each failure, trace the dependency chain across components. If Button fails, check if Card (which uses Button) also fails. Determine whether a failure is root-cause or downstream (caused by a dependency failure). Report the dependency chain and classify each failure as `root-cause` or `downstream`. This analysis feeds the generation report so the user can prioritize fixes: fixing a root-cause failure may resolve all its downstream failures.
- Tools: Failure Correlator, Dependency Chain Walker, Root Cause Analyzer

**Tasks:** T1: Scan internal usage → T2: Run token compliance scan → T3: Check spec/code/docs consistency → T4: Track pipeline completeness → T5: Correlate failures.

---

### 4.8 Release Crew (5 agents)

**Purpose:** Assemble the final output as a valid, locally installable package with proper versioning, changelog, and migration documentation.

**Agent 36: Semver Agent**
- Role: Version calculator
- Goal: Determine the version number based on scope and completeness. v1.0.0 if all quality gates pass, v0.x.0 if experimental/incomplete. Apply conventional version semantics.
- Tools: Gate Status Reader, Version Calculator

**Agent 37: Release Changelog Agent**
- Role: Release inventory author
- Goal: Write `docs/changelog.md`: a structured account of *what* the release contains. Covers: full component inventory (name, status, quality score), token category summary (count per category, compilation targets), quality gate pass/fail summary, known issues and failed components. This is the *what* document — it inventories release contents, not design rationale (which is the Generation Narrative Agent's job). Written as coherent prose grouped by category.
- Tools: Component Inventory Reader, Quality Report Parser, Prose Generator

**Agent 38: Codemod Agent**
- Role: Adoption helper generator
- Goal: Generate example codemod scripts that demonstrate how consumers would adopt the design system by migrating from common patterns to design system components (e.g., raw `<button>` → `<Button>`, raw `<input>` → `<Input>`, hardcoded `color: #333` → `var(--color-text-primary)`). These are adoption codemods — they help teams replace ad-hoc UI code with design system equivalents. They also serve as templates for future version-to-version migration codemods when the design system evolves.
- Tools: AST Pattern Matcher, Codemod Template Generator, Example Suite Builder

**Agent 39: Publish Agent**
- Role: Package assembler and final validator
- Goal: Assemble the final `package.json` with correct dependencies, peer dependencies, entry points, TypeScript config, and export maps. Then execute the full validation sequence: `npm install` (verify all dependencies resolve), `npm run build` / `tsc --noEmit` (verify TypeScript compiles), and `npm test` (run all project-level and component-level tests). Parse test results. If any step fails, report which step failed and why in `reports/generation-summary.json`. This is the last agent to run before the output review gate — its pass/fail determines the final pipeline status.
- Tools: Package.json Generator, Dependency Resolver, npm CLI, Test Result Parser

**Agent 40: Rollback Agent**
- Role: Generation checkpoint manager (cross-cutting)
- Goal: Maintain checkpoints at each pipeline phase. Although organizationally listed under the Release Crew, the Rollback Agent is **instantiated by the First Publish Agent (6) at pipeline start** — before any crew runs — and invoked at every phase boundary during orchestration. It is not part of the Release Crew’s task sequence and does not depend on the Release Crew being instantiated. Agent 6 holds a direct reference to Agent 40 and calls it as a utility agent outside of any crew’s task flow. Before each crew runs, the Rollback Agent snapshots the current output folder state. If a crew fails catastrophically (exhausts all retries with no recoverable output), the Rollback Agent restores the folder to the last known-good checkpoint and triggers a forward cascade: all subsequent phases must re-run from the restored state (see §3.4, Rollback cascade policy). Report what was rolled back and why.
- Tools: Checkpoint Creator, Restore Executor, Rollback Reporter

**Tasks:** T1: Calculate version → T2: Generate changelog → T3: Generate example codemods → T4: Assemble package → T5: Run `npm install && npm run build && npm test` → T6: Validate final status.

---

### 4.9 AI Semantic Layer Crew (5 agents)

**Purpose:** Expose the design system as a machine-readable knowledge base for AI code generators and coding assistants. Output is a set of static JSON files consumable by Cursor, Copilot, Claude, or any LLM-based tool.

**Agent 41: Registry Maintenance Agent**
- Role: Knowledge graph builder
- Goal: Build the complete component registry (`registry/components.json`): for every component, record: all props with types and defaults, all variants, all states, all slots, all token bindings, all a11y attributes, usage examples. This is the raw structured data that Agent 45 (Context Serializer) then packages into format-specific AI context files.
- Tools: Spec Indexer, Example Generator, Registry Builder

**Agent 42: Token Resolution Agent**
- Role: Semantic intent mapper
- Goal: Build the token resolution graph (`registry/tokens.json`): for every token, record: resolved value per platform, tier, semantic purpose, related tokens (same category), and natural language description. Enable AI assistants to resolve intent ("I need a muted background color") to the correct token.
- Tools: Token Graph Traverser, Semantic Mapper, Natural Language Describer

**Agent 43: Composition Constraint Agent**
- Role: Valid tree definer
- Goal: Build the composition rules file (`registry/composition-rules.json`): for every component, record: allowed children, forbidden nesting, required slots, maximum depth, and example valid/invalid composition trees. Enable AI assistants to generate structurally valid component trees.
- Tools: Composition Rule Extractor, Tree Validator, Example Tree Generator

**Agent 44: Validation Rule Agent**
- Role: Compliance rule exporter
- Goal: Build the compliance rules file (`registry/compliance-rules.json`): exportable rules that an AI assistant or linter can use to check generated code against the design system. Covers: token usage, composition rules, a11y requirements, naming conventions.
- Tools: Rule Compiler, Validation Schema Generator

**Agent 45: Context Serializer Agent**
- Role: AI context packager
- Goal: Package the registry, token graph, composition rules, and compliance rules into optimized context formats for different AI assistants: `.cursorrules` for Cursor, `copilot-instructions.md` for GitHub Copilot, and a unified `ai-context.json` for generic LLM consumption.
- Tools: Context Formatter, Token Budget Optimizer, Multi-Format Serializer

**Tasks:** T1: Build component registry → T2: Build token graph → T3: Build composition rules → T4: Export compliance rules → T5: Package AI context files.

---

## 5. Human Gate Policy

**Philosophy: approve the intent upfront, review the result at the end. Everything in between is autonomous.**

The pipeline has exactly two human gates:

| Gate | When | What the user reviews | What happens next |
|---|---|---|---|
| **Brand Profile Approval** | After the interview CLI runs and Agent 1 validates/enriches the profile. Before any generation begins. | The finalized `brand-profile.json`: colors, typography, spacing, scope, themes, overrides. This is the single moment to course-correct before the pipeline commits. | On approval → full pipeline runs autonomously. On rejection → user edits the profile and re-submits. |
| **Output Review** | After the entire pipeline completes (all 9 crews have finished). | The generation report (`reports/generation-summary.json`): which components passed/failed, quality scores, a11y audit results, test results, token compliance, known issues. Plus the full output folder. | On approval → output is final. On rejection → see granular re-run options below. |

**No mid-pipeline stops.** Once the Brand Profile is approved, the pipeline runs to completion without human intervention. Quality issues during generation are handled by the retry protocol (§3.4): validation agents feed structured rejections back to generation agents for up to 3 attempts per component. Components that exhaust retries are marked as `failed` in the generation report — the user sees them at the output review gate, not during the run.

**Output Review actions:** At the output review gate, the user has four options:
1. **Approve** — output is final, ready to use.
2. **Re-run full pipeline** — adjust the Brand Profile or `componentOverrides` and re-run from Phase 1.
3. **Re-run from phase** — specify a phase number (e.g., `--from-phase 4`) to re-run from that phase onward, using existing artifacts from prior phases. Useful when tokens and components are correct but docs or governance need regeneration.
4. **Re-run specific components** — specify component names (e.g., `--retry-components Button,DatePicker`) to re-run the Design-to-Code → Component Factory pipeline for only those components, then re-run Phases 4–6 to update docs, governance, and reports. Useful when most components passed but a few failed.

**Why this model:** A pipeline that takes 20–60 minutes should not require someone to sit and watch it. Mid-run gates (e.g., "approve this token palette before I generate components") assume the user can meaningfully evaluate intermediate artifacts in isolation. In practice, you can only judge a design system when you see the assembled result — tokens, components, and docs together. The output review gate gives you that complete picture.

---

## 6. Brand Profile Schema

The single data contract between Discovery and all downstream crews:

```json
{
  "name": "string",
  "archetype": "enterprise-b2b | consumer-b2c | mobile-first | multi-brand | custom",
  "colors": {
    "primary": "string (hex or natural language description)",
    "secondary": "string",
    "neutral": "string",
    "semantic": {
      "success": "string",
      "warning": "string",
      "error": "string",
      "info": "string"
    }
  },
  "typography": {
    "fontFamily": "string (primary font stack)",
    "headingFontFamily": "string (optional, heading font)",
    "scaleRatio": "number (modular scale, e.g. 1.25 = major third)",
    "baseSize": "number (px)"
  },
  "spacing": {
    "baseUnit": "number (px, typically 4 or 8)",
    "density": "compact | default | spacious"
  },
  "borderRadius": "none | subtle | moderate | rounded | pill",
  "elevation": "flat | subtle | layered",
  "motion": "none | reduced | standard | expressive",
  "themes": {
    "modes": ["light", "dark", "high-contrast"],
    "default": "light",
    "brandOverrides": "boolean (for multi-brand archetype)",
    "brands": "string[] (optional, brand identifiers for multi-brand archetype, e.g., ['brand-a', 'brand-b'])"
  },
  "accessibility": "AA | AAA",
  "componentScope": "starter | standard | comprehensive",
  "breakpoints": {
    "strategy": "mobile-first | desktop-first",
    "count": "number (typically 3-5)"
  },
  "componentOverrides": {
    "description": "Optional per-component design decisions. Keys are component names. Unspecified components use archetype defaults. The Decision Record Agent (24) documents which defaults were applied and why.",
    "example": {
      "DataGrid": {
        "columnResize": "boolean",
        "virtualization": "boolean",
        "stickyHeader": "boolean"
      },
      "DatePicker": {
        "dateFormat": "string (e.g. 'YYYY-MM-DD')",
        "weekStartsOn": "number (0=Sunday, 1=Monday)",
        "showWeekNumbers": "boolean"
      },
      "Modal": {
        "closeOnOverlayClick": "boolean",
        "trapFocus": "boolean"
      },
      "Button": {
        "variants": ["primary", "secondary", "ghost", "danger"],
        "sizes": ["sm", "md", "lg"]
      }
    }
  }
}
```

---

## 7. Component Scope Tiers

| Tier | Count | Components |
|---|---|---|
| **Starter** | 10 | Button, Input, Checkbox, Radio, Select, Card, Badge, Avatar, Alert, Modal |
| **Standard** | 19 | Starter + Table, Tabs, Accordion, Tooltip, Toast, Dropdown, Pagination, Breadcrumb, Navigation |
| **Comprehensive** | 25+ | Standard + DatePicker, DataGrid, TreeView, Drawer, Stepper, FileUpload, RichText |

All tiers include 9 base primitives (11 exports): Box, Stack (single module exporting both HStack and VStack), Grid, Text, Icon, Pressable, Divider, Spacer, ThemeProvider. "9 primitives" refers to 9 source files and spec YAMLs; `Stack.tsx` exports `HStack` and `VStack` as named exports from a single module.

---

## 8. Exit Criteria — What "Valid" Means

The generated design system **must** pass all of these without manual intervention. 8 Fatal + 7 Warning = 15 total criteria.

| # | Check | Method | Severity |
|---|---|---|---|
| 1 | Token JSON parses without error | JSON.parse | Fatal |
| 2 | Token JSON conforms to W3C DTCG schema | JSON Schema validation | Fatal |
| 3 | All semantic token references resolve to global tokens | Reference graph traversal | Fatal |
| 4 | All component token references resolve to semantic tokens | Reference graph traversal | Fatal |
| 5 | All foreground/background color pairs meet WCAG target | Contrast ratio calculation | Fatal |
| 6 | CSS custom properties have no undefined references | Regex + token map | Fatal |
| 7 | TypeScript compiles with zero errors | `tsc --noEmit` | Fatal |
| 8 | `npm install` and `npm run build` complete without errors | Shell | Fatal |
| 9 | All unit tests pass | Vitest | Warning |
| 10 | No hardcoded color/spacing values in source | AST scan | Warning |
| 11 | All interactive components have ARIA roles | AST scan | Warning |
| 12 | All components score ≥70/100 on quality gate | Quality Scoring Agent | Warning |
| 13 | Spec ↔ code ↔ docs consistency check passes | Drift Detection Agent | Warning |
| 14 | Component registry JSON is valid and complete | Schema validation | Warning |
| 15 | One or more components marked `failed` in generation summary | Generation report | Warning |

Fatal = pipeline reports failure, `isComplete: false`. Warning = flagged in quality report, output still usable, `isComplete: true`.

**Note:** Test failures (criterion 9) are classified as Warning, not Fatal. In an AI-generation pipeline, some generated tests may fail despite correct component output. Test failures are surfaced prominently in the output review but do not block the pipeline from marking `isComplete: true`. Build failures (`npm install` and `npm run build`) remain Fatal.

---

## 9. Tech Stack

| Layer | Choice | Rationale |
|---|---|---|
| Orchestration | **CrewAI** | Agent/crew/task model maps directly to the crew architecture. |
| LLM | **Anthropic (Claude Opus, Sonnet, Haiku)** | All tiers use Anthropic models exclusively (see §3.7). |
| Token format | **W3C DTCG** | Industry standard. Future-proof. |
| Token compilation | **Style Dictionary** | Deterministic. Well-tested. DTCG native. |
| Primary framework | **React + TypeScript** | Always generated. |
| Testing | **Vitest + @testing-library/react** | Fast, modern, standard. |
| A11y | **axe-core** | Industry standard. Rule reference for generation, runtime for tests. |
| Visual regression | **Playwright** | Headless rendering for screenshot baselines. |
| AST analysis | **TypeScript Compiler API** | Static analysis for compliance scans. |
| Package format | **npm local package** | `npm install ../my-design-system`. Registry-ready structure. |

Requirements: `python` + `node` + an LLM API key.

---

## 10. Agent Census

| # | Crew | Agent Count | Agents |
|---|---|---|---|
| 1 | DS Bootstrap | 6 | Brand Discovery, Token Foundation, Primitive Scaffolding, Core Component, Pipeline Configuration, First Publish |
| 2 | Token Engine | 5 | Token Ingestion, Token Validation, Token Compilation, Token Integrity, Token Diff |
| 3 | Design-to-Code | 5 | Scope Classification, Intent Extraction, Code Generation, Render Validation, Result Assembly |
| 4 | Component Factory | 4 | Spec Validation, Composition, Accessibility, Quality Scoring |
| 5 | Documentation | 5 | Doc Generation, Token Catalog, Generation Narrative, Decision Record, Search Index |
| 6 | Governance | 5 | Ownership, Workflow, Deprecation, RFC, Quality Gate |
| 7 | Analytics | 5 | Usage Tracking, Token Compliance, Drift Detection, Pipeline Completeness, Breakage Correlation |
| 8 | Release | 5 | Semver, Release Changelog, Codemod, Publish, Rollback |
| 9 | AI Semantic Layer | 5 | Registry Maintenance, Token Resolution, Composition Constraint, Validation Rule, Context Serializer |
| | **TOTAL** | **45** | |

---

## 11. Risks

| Risk | Prob | Impact | Mitigation |
|---|---|---|---|
| LLM generates components that don't compile | High | High | Retry protocol (§3.4): validation agents feed structured rejections back to generation agents for up to 3 attempts. Components that exhaust retries are flagged in report, not silently dropped. Rollback Agent preserves checkpoints. |
| Generated tests are trivial / meaningless | Med | Med | Code Generation Agent prompt includes test quality rubric. Quality Scoring Agent penalizes low coverage. |
| Token scales produce aesthetically poor results | Med | Low | Archetype defaults are pre-tuned. User reviews full output at the output review gate. Re-run with adjusted Brand Profile if needed. |
| 45 agents introduce excessive LLM cost per run | Med | Med | Tiered model assignment: fast/cheap for classification agents, powerful for generation agents. Cache deterministic tool outputs. |
| Pipeline takes too long for interactive use | Med | Med | Starter scope targets <30 min. Checkpoint system enables resume-on-failure. |
| CrewAI sequential overhead for 9 crews | Low | Low | If overhead is excessive, crew-to-crew handoff can be replaced with direct function calls. Agent logic is portable. |
| Style Dictionary version incompatibility | Low | Med | Pin version. W3C DTCG format is tool-agnostic. |

---

## 12. Glossary

**DAF:** DesignOps Agentic Framework.

**Crew:** A CrewAI Crew — a group of agents operating one pipeline module.

**Agent:** A CrewAI Agent — autonomous AI unit with role, goal, and tools.

**Tool:** Deterministic utility (compiler, linter, CLI) invoked by agents.

**Human Gate:** An approval point where the pipeline pauses for human review. DAF Local has exactly two: Brand Profile approval (before generation) and Output Review (after generation).

**DTCG:** W3C Design Token Community Group specification.

**Brand Profile:** Structured output of the Brand Discovery Agent interview, defining all design decisions that seed generation.

**DS Archetype:** Pre-configured starting template (Enterprise B2B, Consumer B2C, Mobile-First, Multi-Brand) for bootstrapping.

**Canonical Spec:** Framework-agnostic component specification (YAML) used as the single source of truth for code generation.

**Semver:** Semantic Versioning (MAJOR.MINOR.PATCH).

**ADR:** Architecture Decision Record.

---

## 13. Interview CLI Specification

The Interview CLI is the sole user-facing entry point to the DAF pipeline. It is the only interactive component — everything after it is autonomous. Because the entire pipeline depends on it producing a correct `brand-profile.json`, its behavior is specified here.

### 13.1 Invocation

```bash
# Interactive mode (full interview)
daf init

# File mode (skip interview, provide pre-written profile)
daf init --profile ./my-brand-profile.json

# Resume a previous run
daf init --resume ./my-design-system
```

### 13.2 Interview Flow

The CLI presents a structured, sequential interview in the terminal. Each step collects one category of input:

| Step | Question Category | Required | Default if skipped |
|---|---|---|---|
| 1 | **Project name** | Yes | — |
| 2 | **Archetype selection** (Enterprise B2B, Consumer B2C, Mobile-First, Multi-Brand, Custom) | Yes | — |
| 3 | **Colors** — primary, secondary, neutral, semantic (success/warning/error/info) | No | Derived from archetype |
| 4 | **Typography** — font family, heading font, scale ratio, base size | No | Derived from archetype |
| 5 | **Spacing** — base unit, density | No | Derived from archetype |
| 6 | **Visual style** — border radius, elevation, motion | No | Derived from archetype |
| 7 | **Themes** — modes (light/dark/high-contrast), default, brands (if multi-brand) | No | Derived from archetype |
| 8 | **Accessibility** — AA or AAA | No | AA |
| 9 | **Component scope** — starter, standard, comprehensive | No | Derived from archetype |
| 10 | **Breakpoints** — strategy and count | No | Derived from archetype |
| 11 | **Component overrides** — per-component customization (advanced, optional) | No | None |

For each non-required step, the CLI shows the archetype-derived default and allows the user to accept (Enter) or override. Color inputs accept both hex values (`#1a73e8`) and natural language descriptions (`"a professional blue"`).

### 13.3 Validation and Error Handling

The CLI performs basic structural validation before writing the raw `brand-profile.json`:
- Required fields must be non-empty.
- Hex color values must be valid 3- or 6-digit hex.
- Scale ratio must be a positive number between 1.0 and 2.0.
- Base size must be a positive integer between 8 and 24.
- Archetype must be one of the defined values.

All semantic validation (contradiction detection, consistency checking, default enrichment) is deferred to the Brand Discovery Agent (1) — the CLI does not duplicate agent intelligence.

**Partial input / session interruption:** The CLI writes a `.daf-session.json` file to the current directory after each completed step. If the process is interrupted (Ctrl+C, terminal close), re-running `daf init` in the same directory detects the session file and offers to resume from the last completed step. The session file is deleted after the raw `brand-profile.json` is successfully written.

### 13.4 Output

The CLI writes a single file: `brand-profile.json` (raw, pre-validation) conforming to the schema defined in §6. This file is the input to the Brand Discovery Agent (1), which validates, enriches, and finalizes it before the Human Gate.

### 13.5 Non-interactive Mode

For CI/CD or scripted usage, `daf init --profile ./my-brand-profile.json` skips the interview entirely and passes the provided file directly to the Brand Discovery Agent. The file must conform to the §6 schema. The Brand Discovery Agent still validates and enriches it — non-interactive mode skips only the interview, not validation.
