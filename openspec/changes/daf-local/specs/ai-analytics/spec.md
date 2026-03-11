## ADDED Requirements

### Requirement: Component registry assembly
The Registry Maintenance Agent (Agent 41) SHALL synthesize `registry/components.json` from spec YAMLs, component source, and composition audit results. The component registry SHALL be AI-consumable and SHALL include for each component: name, description, props schema (names, types, defaults), variant and state inventory, token references, valid composition rules (allowed children and parents), usage examples, accessibility requirements, and file paths. The registry SHALL be formatted as a structured JSON array consumable by AI coding assistants without further transformation.

#### Scenario: Registry includes all components
- **WHEN** `registry/components.json` is generated
- **THEN** every component and primitive in `src/` SHALL have an entry
- **AND** every entry SHALL include all required fields (props, variants, states, tokens, composition, examples)

#### Scenario: Registry composition rules match audit
- **WHEN** `registry/components.json` is generated
- **THEN** composition rules in registry entries SHALL be consistent with `reports/composition-audit.json`
- **AND** SHALL reflect only valid composition combinations from the spec

### Requirement: Semantic token graph
The Registry Maintenance Agent SHALL generate `registry/tokens.json` as a semantic token graph. The graph SHALL represent the resolution chain from component-scoped tokens → semantic tokens → global tokens for every token in the system, with per-theme resolved values. The graph format SHALL be AI-consumable JSON.

#### Scenario: Token graph includes full resolution chain
- **WHEN** `registry/tokens.json` is generated
- **THEN** each entry SHALL include: token name, tier (global/semantic/component), aliases (what it references), and resolved values per configured theme
- **AND** the graph SHALL be queryable by token name to retrieve full context

### Requirement: Composition rules file
The Composition Constraint Agent (Agent 43) SHALL generate `registry/composition-rules.json` defining the valid component composition tree. The file SHALL specify for each component: which components it may contain (children), which components it may be placed inside (parents), and any mutual exclusion rules.

#### Scenario: Composition rules cover all primitives
- **WHEN** `registry/composition-rules.json` is generated
- **THEN** every primitive SHALL have an entry defining its allowed children and parents
- **AND** a composition tree that violates these rules SHALL be detectable programmatically from the file

### Requirement: Compliance rules file
The AI Semantic Layer Crew SHALL generate `registry/compliance-rules.json` defining code compliance rules for the design system. Rules SHALL include: no direct global token usage in components, no hardcoded color values, required import paths for token constants, and component naming conventions. The compliance rules file SHALL be structured so that automated linting tools can load and enforce it.

#### Scenario: Compliance rules cover token usage policy
- **WHEN** `registry/compliance-rules.json` is generated
- **THEN** at least one rule SHALL prohibit direct global token usage in component source
- **AND** at least one rule SHALL prohibit hardcoded color values (hex, RGB, named CSS colors)

### Requirement: AI context file generation
The AI Semantic Layer Crew SHALL generate three AI context files for different coding assistant integrations: `.cursorrules` (Cursor AI context), `copilot-instructions.md` (GitHub Copilot context), and `ai-context.json` (generic LLM context). Each file SHALL include: design system overview, component registry summary, token usage rules, composition rules, and code conventions. These files SHALL be immediately usable by AI coding assistants without modification.

#### Scenario: AI context files summarize design system
- **WHEN** `.cursorrules`, `copilot-instructions.md`, and `ai-context.json` are generated
- **THEN** each SHALL include the component list, token naming conventions, and the rule that components must use semantic tokens only
- **AND** SHALL NOT require manual editing before use in an AI-assisted coding workflow

### Requirement: Quality scorecard reporting
The Analytics Crew SHALL consolidate per-component quality scores from Phase 3 into `reports/quality-scorecard.json`. Each entry SHALL include numeric scores for spec coverage, test coverage, a11y compliance, token compliance, TypeScript strictness, and an overall weighted score. The scorecard SHALL flag components that fall below the configured quality gate thresholds from `pipeline-config.json`.

#### Scenario: Components below threshold are flagged
- **WHEN** a component's overall quality score is below the threshold in `pipeline-config.json`
- **THEN** its scorecard entry SHALL include a `belowThreshold: true` flag
- **AND** SHALL list which scoring dimensions caused the failure

### Requirement: Token compliance scan
The Analytics Crew SHALL perform an AST-based static analysis of all `src/` files to detect hardcoded values. The results SHALL be written to `reports/token-compliance.json`. Every instance of a hardcoded color (hex, RGB, HSL, named CSS color), hardcoded font size, hardcoded spacing value, or hardcoded shadow definition in component source SHALL be reported with the file path, line number, and the suggested token to use instead.

#### Scenario: Hardcoded value detected and reported
- **WHEN** a component source file contains `color: #ffffff`
- **THEN** `reports/token-compliance.json` SHALL include an entry with the file path, line number, the hardcoded value, and the suggested semantic token

#### Scenario: Clean component produces no compliance violations
- **WHEN** a component source file uses only `tokens.ts` constants for all visual properties
- **THEN** the token compliance report SHALL contain no violations for that component

### Requirement: Drift detection
The Drift Detection Agent (Agent 33) SHALL compare spec files, source files, and documentation pages to detect consistency gaps. Results SHALL be written to `reports/drift-report.json`. Drift types SHALL include: spec-to-code drift (a prop defined in spec but not implemented in TSX), code-to-docs drift (a prop implemented in TSX but missing from the doc page), and spec-to-docs drift (spec content not reflected in docs).

#### Scenario: Missing prop implementation detected
- **WHEN** `specs/Input.spec.yaml` defines a `placeholder` prop and `src/components/Input/Input.tsx` does not implement it
- **THEN** `reports/drift-report.json` SHALL include a spec-to-code drift entry for Input with the missing prop name

#### Scenario: No drift in a well-implemented component
- **WHEN** all props, variants, and states in a spec are implemented in TSX and documented in the component's doc page
- **THEN** the drift report SHALL contain no entries for that component

### Requirement: Composition audit
The Analytics Crew SHALL generate `reports/composition-audit.json` by analyzing the structural integrity of all components: checking that components only use allowed children (per spec), checking that token reference chains resolve without broken aliases, and verifying that the component hierarchy matches the spec-defined composition rules.

#### Scenario: Invalid child usage detected
- **WHEN** a component's TSX renders a child component not permitted by the spec's composition rules
- **THEN** `reports/composition-audit.json` SHALL include a structural integrity violation entry for that component

#### Scenario: Broken token alias detected
- **WHEN** a component-scoped token references a semantic token that no longer exists in `tokens/semantic.tokens.json`
- **THEN** the composition audit SHALL flag the broken alias with the full reference chain

### Requirement: Usage Tracking Agent
The Usage Tracking Agent (Agent 31, Tier 2) SHALL generate `reports/usage-report.json` by analyzing the actual usage of tokens and components across all generated source files. The agent SHALL answer:

- **Token usage**: which tokens in `tokens/semantic.tokens.json` and `tokens/component.tokens.json` are actually referenced in `src/` files vs. defined-but-unused (orphaned at the source level)
- **Primitive usage**: which core primitives are imported and used by at least one component vs. primitives that were generated but are never composed
- **Cross-component relationships**: which components import and render which other components, producing a dependency graph

The usage report SHALL flag any token that is defined in the system but referenced by zero components, and SHALL flag any primitive that is never used as a building block. These are informational warnings, not hard gate failures.

#### Scenario: Unused token identified
- **WHEN** `tokens/semantic.tokens.json` defines `color.surface.overlay` but no component in `src/` references its compiled constant
- **THEN** `reports/usage-report.json` SHALL list `color.surface.overlay` as an unused token with status `defined-not-used`

#### Scenario: Component import graph captured
- **WHEN** `src/components/Modal/Modal.tsx` imports and renders `Box`, `Text`, and `Pressable`
- **THEN** the usage report SHALL record Modal's dependencies as `["Box", "Text", "Pressable"]`
- **AND** this graph SHALL be referenced by the registry `components.json` to populate the `usedBy` field

#### Scenario: All primitives used — no orphans
- **WHEN** all 9 generated primitives are imported by at least one component
- **THEN** `reports/usage-report.json` SHALL list zero orphaned primitives

### Requirement: Breakage Correlation Agent
The Breakage Correlation Agent (Agent 35, Tier 2) SHALL analyze all failure events recorded during the pipeline run — both exhausted-retry component failures AND test failures from the final `npm test` execution in the Release Crew — and produce `reports/breakage-correlation.json`. For each failure, the agent SHALL classify it as either:

- **Root-cause failure**: the originating component or token that first failed independent of others
- **Downstream failure**: a component that failed because a dependency (a primitive or component it imports) failed; the failure chain SHALL be traced back to the root cause

The agent SHALL walk the component dependency graph from the Usage Tracking Agent's output to perform this classification. Downstream failures SHALL be resolved simply by fixing the root-cause failure, and the report SHALL make this explicit.

#### Scenario: Downstream failure traced to root cause
- **WHEN** `Modal` fails Vitest tests because `Pressable` (a Modal dependency) failed to generate correctly
- **THEN** `reports/breakage-correlation.json` SHALL classify Modal's test failure as `downstream` with `rootCause: "Pressable"`
- **AND** SHALL include the full dependency chain: `Modal → Pressable`

#### Scenario: Isolated root-cause failure
- **WHEN** `DataGrid` fails generation with no composition dependencies on other failed components
- **THEN** `reports/breakage-correlation.json` SHALL classify it as `root-cause` with no upstream cause

#### Scenario: All components pass — no breakage report entries
- **WHEN** all components generate and pass tests
- **THEN** `reports/breakage-correlation.json` SHALL be an empty array (still written, confirming the check ran)

### Requirement: Drift auto-fix vs manual resolution
The Drift Detection Agent (Agent 33) SHALL distinguish between drift types that can be auto-fixed and those that require manual intervention:

- **Code-to-docs drift** (prop implemented in TSX but missing from doc page): the Drift Detection Agent SHALL auto-fix by appending the missing prop to the documentation page's props table. Auto-fixes SHALL be applied in-place to `docs/components/<Name>.md`.
- **Spec-to-docs drift** (spec content not reflected in docs): the Drift Detection Agent SHALL auto-fix by regenerating the affected section of the documentation page.
- **Spec-to-code drift** (prop defined in spec but not implemented in TSX): the Drift Detection Agent SHALL NOT auto-fix code drift. Code drift requires human review or pipeline re-run and SHALL be marked `requires-manual-fix` in the drift report.

#### Scenario: Code-to-docs drift auto-fixed
- **WHEN** `Input.tsx` implements a `placeholder` prop that is absent from `docs/components/Input.md`
- **THEN** the Drift Detection Agent SHALL append the `placeholder` prop to the props table in `docs/components/Input.md`
- **AND** SHALL record the auto-fix in `reports/drift-report.json` with `autoFixed: true`

#### Scenario: Spec-to-code drift requires manual fix
- **WHEN** `specs/Button.spec.yaml` defines a `loading` state but `src/components/Button/Button.tsx` does not implement it
- **THEN** `reports/drift-report.json` SHALL record the drift entry with `autoFixed: false` and `requires-manual-fix: true`
- **AND** the Drift Detection Agent SHALL NOT modify `Button.tsx`

### Requirement: Token Resolution Agent natural language intent mapping
The Token Resolution Agent (Agent 42, Tier 1) SHALL augment `registry/tokens.json` with **intent mapping** entries. For each semantic token, the agent SHALL generate one or more natural language intent descriptions that describe the token's purpose in plain English. These intent descriptions enable AI coding assistants that receive the registry context to correctly identify the right token when a developer expresses intent rather than a token name.

The intent mapping SHALL be stored in `registry/tokens.json` alongside each token's resolution chain, under an `intents` array.

#### Scenario: Color token intent mapping
- **WHEN** `registry/tokens.json` is generated and includes `color.background.subtle`
- **THEN** the entry SHALL include `intents: ["muted background", "secondary surface", "card background", "subtle container fill"]`
- **AND** an AI assistant receiving this context SHALL be able to resolve "I need a muted background" to `color.background.subtle`

#### Scenario: Token intents are unique across token set
- **WHEN** two tokens have overlapping intent descriptions
- **THEN** the Token Resolution Agent SHALL differentiate the intent descriptions to minimize ambiguity
- **AND** SHALL prefer more specific intent descriptions that distinguish the token's exact use case

### Requirement: Validation Rule Agent
The Validation Rule Agent (Agent 44, Tier 3) is distinct from the Composition Constraint Agent (Agent 43). While the Composition Constraint Agent derives structural composition rules, the Validation Rule Agent derives code compliance rules and writes them to `registry/compliance-rules.json`. The Validation Rule Agent's output is the authoritative source for automated linting and code review enforcement.

The Validation Rule Agent SHALL generate rules covering:
- Direct global token usage in component source (prohibited)
- Hardcoded color values in `src/` (prohibited — hex, RGB, HSL, named CSS colors)
- Hardcoded dimension values not using `tokens.ts` spacing constants (prohibited)
- Required import paths for token constants (must import from `../../tokens/compiled/tokens`)
- Component naming conventions (PascalCase for component names, kebab-case for `data-testid`)
- Composition rules cross-reference (referencing `registry/composition-rules.json` by pointer rather than duplicating them)

Each rule in `registry/compliance-rules.json` SHALL have a unique `ruleId`, a human-readable `description`, and a `severity` (`error` or `warning`).

#### Scenario: Compliance rules file distinct from composition rules
- **WHEN** `registry/compliance-rules.json` and `registry/composition-rules.json` are both generated
- **THEN** `compliance-rules.json` SHALL contain only code compliance rules (no composition structure rules)
- **AND** `composition-rules.json` SHALL contain only structural composition rules (no code compliance rules)

#### Scenario: Compliance rule has required fields
- **WHEN** any rule is written to `registry/compliance-rules.json`
- **THEN** it SHALL contain: `ruleId` (string, unique), `description` (string), `severity` ("error" | "warning"), and `category` (string)

### Requirement: Context Serializer Agent and token budget optimization
The Context Serializer Agent (Agent 45, Tier 2) is distinct from the Registry Maintenance Agent (Agent 41). While the Registry Maintenance Agent assembles the complete component registry, the Context Serializer Agent is responsible for packaging registry data into AI-consumable context files optimized for specific LLM context window constraints.

The Context Serializer Agent SHALL implement **token budget optimization**: because the full registry content may exceed an LLM's context window, the agent SHALL rank registry entries by usage frequency (from `reports/usage-report.json`) and prioritize high-frequency components and tokens. Less-used entries SHALL be truncated or summarized when the serialized output would exceed the target context budget.

Context budget targets:
- `.cursorrules`: 8,000 tokens (Cursor context limit)
- `copilot-instructions.md`: 6,000 tokens (GitHub Copilot context limit)
- `ai-context.json`: no limit, full registry included

#### Scenario: High-usage components prioritized in Cursor context
- **WHEN** generating `.cursorrules` and the full registry exceeds 8,000 tokens
- **THEN** the Context Serializer Agent SHALL include the top-N most-used components (by frequency in `reports/usage-report.json`) within the budget
- **AND** SHALL append a note that the full registry is available in `ai-context.json`

#### Scenario: Full registry in ai-context.json
- **WHEN** generating `ai-context.json`
- **THEN** it SHALL include all components, all token entries, all composition rules, and all intent mappings without truncation
