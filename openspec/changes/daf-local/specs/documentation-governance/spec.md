## ADDED Requirements

### Requirement: Component documentation pages
The Doc Generation Agent (Agent 21) SHALL generate a Markdown documentation page for every component and primitive at `docs/components/<Name>.md`. Each doc page SHALL include: component description, props table (name, type, required/optional, default, description), variant and state inventory, usage example code, token reference table (which component-scoped tokens the component uses), accessibility notes, and known limitations if any. Doc pages SHALL be generated BEFORE the Governance Crew runs, as the Quality Gate Agent (Agent 30) checks that all components have documentation.

#### Scenario: All components have doc pages
- **WHEN** the Documentation Crew completes
- **THEN** for every file in `src/components/` and `src/primitives/`, a corresponding `docs/components/<Name>.md` SHALL exist
- **AND** each page SHALL contain all required sections

#### Scenario: Doc page includes props table
- **WHEN** generating `docs/components/Button.md`
- **THEN** the props table SHALL list every prop defined in `specs/Button.spec.yaml`
- **AND** SHALL include the prop type, required/optional status, default value, and a description

### Requirement: Token catalog documentation
The Documentation Crew SHALL generate `docs/tokens.md` as a human-readable token catalog. The catalog SHALL list all semantic tokens grouped by category (color, typography, spacing, etc.), include their resolved values per theme, and reference the global tier aliases.

#### Scenario: Semantic tokens cataloged per theme
- **WHEN** `docs/tokens.md` is generated
- **THEN** each semantic token entry SHALL show its resolved value for each configured theme (light, dark, high-contrast)
- **AND** entries SHALL be grouped by semantic category (e.g., Color Tokens → Background, Text, Border)

### Requirement: Architecture Decision Records
The Generation Narrative Agent (Agent 23) SHALL generate Architecture Decision Records (ADRs) and a generation narrative document. Required outputs: `docs/decisions/generation-narrative.md` (why the design system looks the way it does — synthesized from brand profile and generation decisions), `docs/decisions/ADR-001-archetype-selection.md` (why the brand archetype was chosen), `docs/decisions/ADR-002-token-scale-rationale.md` (why the token scales were chosen). Additional ADRs MAY be generated for other significant decisions.

#### Scenario: Generation narrative synthesizes brand and decisions
- **WHEN** `docs/decisions/generation-narrative.md` is generated
- **THEN** it SHALL reference the brand profile (archetype, colors, typography choices) and explain how they translate into token and component decisions
- **AND** SHALL NOT consist of generic placeholder text

#### Scenario: ADR files follow standard format
- **WHEN** any ADR file is generated
- **THEN** it SHALL contain: Status, Context, Decision, Consequences sections
- **AND** SHALL be specific to this design system generation run (not a generic template)

### Requirement: Changelog document
The Documentation Crew SHALL generate `docs/changelog.md` documenting every decision made during the generation pipeline. The changelog SHALL include: phase-by-phase generation events, token changes (from `tokens/diff.json`), components generated or failed, and any retry events.

#### Scenario: Changelog references token diff
- **WHEN** `docs/changelog.md` is generated
- **THEN** token changes from `tokens/diff.json` SHALL be summarized under a dedicated changelog section
- **AND** each changed token SHALL be listed with its prior value and new value

### Requirement: Full-text search index
The Search Index tool (deterministic, Agent 25 triggers) SHALL build `docs/search-index.json` covering all documentation pages, token catalog entries, component names, and spec content. The index SHALL support keyword lookup and SHALL include document title, path, and relevant content excerpt per entry.

#### Scenario: Search index covers all doc pages
- **WHEN** `docs/search-index.json` is generated
- **THEN** every file under `docs/` SHALL have at least one entry in the search index
- **AND** every component name SHALL be findable via keyword search in the index

### Requirement: RFC template generation
The Documentation Crew SHALL generate `docs/templates/rfc-template.md` providing a standard template for proposing future design system changes. The template SHALL include sections for: Motivation, Proposed Changes, Token Impact, Component Impact, Migration Guide, and Rollout Plan.

#### Scenario: RFC template file exists after Phase 4
- **WHEN** the Documentation Crew completes
- **THEN** `docs/templates/rfc-template.md` SHALL exist and SHALL contain all required RFC sections

### Requirement: Governance artifacts
The Governance Crew SHALL generate all governance configuration files seeded from `pipeline-config.json`. Required outputs: `governance/ownership.json` (component ownership map), `governance/quality-gates.json` (quality gate thresholds), `governance/deprecation-policy.json` (lifecycle rules), `governance/workflow.json` (contribution pipeline definition). Governance artifact generation SHALL run AFTER the Documentation Crew completes (the Quality Gate Agent checks for doc completeness).

#### Scenario: Ownership map covers all components
- **WHEN** `governance/ownership.json` is generated
- **THEN** every component and primitive in `src/` SHALL have an ownership entry
- **AND** entries SHALL include domain assignment (derived by the Ownership Assignment Agent by reasoning about component relationships)

#### Scenario: Quality gates derived from pipeline config
- **WHEN** `governance/quality-gates.json` is generated
- **THEN** threshold values (coverage requirements, a11y level, token compliance thresholds) SHALL match the values specified in `pipeline-config.json`
- **AND** SHALL NOT use hardcoded default values that differ from the project's configured thresholds

### Requirement: Test scaffolding
The Governance Crew SHALL generate four test scaffold files under `tests/`: `tests/tokens.test.ts` (token validity and reference tests), `tests/a11y.test.ts` (accessibility tests), `tests/composition.test.ts` (structural composition tests), `tests/compliance.test.ts` (token usage compliance tests). These scaffold files SHALL be runnable with Vitest using the project's `vitest.config.ts`.

#### Scenario: Test scaffold files are runnable
- **WHEN** Vitest is run against `tests/tokens.test.ts`
- **THEN** the test file SHALL load without import errors
- **AND** SHALL execute at least one test assertion

#### Scenario: Compliance test checks for hardcoded values
- **WHEN** `tests/compliance.test.ts` runs
- **THEN** at least one test SHALL verify that no component in `src/` contains hardcoded color values (hex, RGB, named CSS colors)

### Requirement: Token Catalog Agent visual representations
The Token Catalog Agent (Agent 22, Tier 1) is a distinct agent from the Doc Generation Agent (Agent 21). Its sole responsibility is generating the token catalog at `docs/tokens.md`. Beyond listing token names and values, the Token Catalog Agent SHALL produce visual representation sections:

- **Color swatches**: each semantic color token entry SHALL include the hex value, its resolved light/dark contrast counterpart, and a human-readable description of its intended use (e.g., "Primary interactive element background — use for buttons and active states")
- **Typography scale**: the type scale section SHALL present each size step as a proportion progression (e.g., rendered as a visual staircase of text samples from smallest to largest)
- **Spacing scale**: the spacing section SHALL list each step with its pixel value and a visual size representation (e.g., "4px — micro gap", "16px — component padding", "64px — section separation")

Every token entry SHALL also include which components in `registry/components.json` reference it, enabling cross-referenced discoverability.

#### Scenario: Color token entry includes description and usage
- **WHEN** `docs/tokens.md` is generated
- **THEN** each color token entry SHALL include a human-readable usage description
- **AND** SHALL list at least one component that references it (or note it is unreferenced)

#### Scenario: Typography scale shows size progression
- **WHEN** the token catalog documents the typography size scale
- **THEN** the entries SHALL be sequentially ordered from smallest to largest
- **AND** each entry SHALL show its rem value, computed pixel equivalent (at 16px base), and suggested usage context

### Requirement: Decision Record Agent
The Decision Record Agent (Agent 24, Tier 1) is a distinct agent from the Generation Narrative Agent (Agent 23). While the Generation Narrative Agent (Agent 23) synthesizes a prose narrative (`generation-narrative.md`) explaining the overall design philosophy, the Decision Record Agent (Agent 24) is responsible solely for authoring Architecture Decision Records (ADRs) as structured documents.

The Decision Record Agent SHALL produce:
- `docs/decisions/ADR-001-archetype-selection.md` — why the selected archetype was chosen and what alternatives were considered
- `docs/decisions/ADR-002-token-scale-rationale.md` — why the spacing and type scale steps were chosen
- `docs/decisions/ADR-003-component-scope.md` — why the selected scope tier was chosen and what was excluded
- Additional ADRs for any significant generation decision flagged by other agents during the pipeline run

All ADRs SHALL follow the standard format: **Status** (Proposed/Accepted/Deprecated), **Context**, **Decision**, **Consequences**. ADR content SHALL be specific to this generation run — not generic boilerplate.

#### Scenario: ADR-003 documents scope exclusions
- **WHEN** the Design system was generated at Starter scope
- **THEN** `docs/decisions/ADR-003-component-scope.md` SHALL document that Standard and Comprehensive components were excluded
- **AND** SHALL explain the rationale captured during the brand interview (e.g., "Initial launch — expand to Standard in v2")

#### Scenario: Additional ADRs generated for flagged decisions
- **WHEN** a Phase 3 agent logs a significant structural decision (e.g., a composition restructuring due to depth limit)
- **THEN** the Decision Record Agent SHALL produce an additional ADR documenting the decision
- **AND** the ADR index in `docs/decisions/` SHALL reflect all generated ADR files

### Requirement: Workflow Agent
The Workflow Agent (Agent 27, Tier 2) SHALL generate `governance/workflow.json` as a formal contribution pipeline state machine. The state machine SHALL define the contribution lifecycle for teams consuming the generated design system: states (e.g., `rfc-proposed`, `rfc-reviewing`, `token-change`, `component-change`, `approved`, `released`, `deprecated`), valid transitions between states, required approval conditions per transition, and which role triggers each transition. The state machine SHALL be a JSON document directly parseable by automation tools without further transformation.

#### Scenario: Workflow state machine covers RFC lifecycle
- **WHEN** `governance/workflow.json` is generated
- **THEN** it SHALL define transitions from `rfc-proposed` → `rfc-reviewing` → `approved` (or `rejected`)
- **AND** the `approved` → `released` transition SHALL require all quality gates to pass

#### Scenario: Workflow references quality gates
- **WHEN** a transition requires quality gate passage
- **THEN** the `governance/workflow.json` SHALL reference the gate identifiers from `governance/quality-gates.json` by name
- **AND** SHALL NOT hardcode threshold values (they SHALL be derived from `quality-gates.json`)

### Requirement: Deprecation Agent and lifecycle tagging
The Deprecation Agent (Agent 28, Tier 3) SHALL generate `governance/deprecation-policy.json` and SHALL tag every component spec with a lifecycle status. Supported lifecycle statuses are: `stable`, `beta`, and `experimental`.

Assignment rules:
- Components in the Starter or Standard scope tier SHALL default to `stable`
- Components in the Comprehensive scope tier SHALL default to `beta`
- Any custom-added component not in the standard scope list SHALL default to `experimental`
- Components that failed generation (marked `failed` in the summary) SHALL be tagged `experimental` regardless of scope tier

The lifecycle status SHALL also be written into `registry/components.json` entries and SHALL appear as a badge in each component's documentation page.

#### Scenario: Standard component tagged stable
- **WHEN** `governance/deprecation-policy.json` is generated and `Button` is in Starter scope
- **THEN** its lifecycle entry SHALL be `stable`
- **AND** `docs/components/Button.md` SHALL display a stable badge

#### Scenario: Comprehensive component tagged beta
- **WHEN** `DataGrid` is in Comprehensive scope tier
- **THEN** its lifecycle entry SHALL be `beta`
- **AND** `docs/components/DataGrid.md` SHALL display a beta badge indicating it is subject to change

### Requirement: RFC Agent and process definition
The RFC (Request for Comments) Agent (Agent 29, Tier 2) SHALL analyze the generated design system and produce `governance/rfc-process.md` — the human-readable RFC process guide for teams contributing future changes. The RFC Agent SHALL also determine, based on the archetype and scope, which types of changes require a formal RFC vs. those that can be made directly via PR:

- **RFC required**: new component additions, token scale changes, deprecating existing components, changing WCAG compliance level, introducing a new brand, changing archetype
- **RFC optional (PR allowed)**: bug fixes to existing components, new variant additions to existing components, documentation updates, new ADR additions
- **No RFC**: dependency version bumps, build configuration changes, test additions

The RFC gate policy SHALL be written into `governance/rfc-process.md` and SHALL reference the RFC template at `docs/templates/rfc-template.md`.

#### Scenario: RFC process document generated
- **WHEN** the Documentation + Governance phase completes
- **THEN** `governance/rfc-process.md` SHALL exist and SHALL list change types categorized by RFC requirement
- **AND** SHALL reference `docs/templates/rfc-template.md` for the submission format

### Requirement: Quality Gate Agent — individual hard gates vs composite score
The Quality Gate Agent (Agent 30) is the final gate in the Governance Crew. It enforces **individual hard gates** against the output of Phases 3–4. These are distinct from the composite quality score (Agent 20's 70/100 threshold). Both must pass.

Individual hard gates enforced by Agent 30:
1. **Test coverage gate**: aggregate Vitest line coverage ≥ 80% across all generated components
2. **Accessibility gate**: zero critical axe-core violations across all components (from `reports/a11y-audit.json`)
3. **Token reference gate**: all component-scoped token references resolve without broken aliases (from `reports/token-integrity.json`)
4. **Documentation completeness gate**: every component and primitive has a `docs/components/<Name>.md` page (from `docs/components/`)
5. **Usage example gate**: every component documentation page contains at least one usage code example

If any individual hard gate fails, the Quality Gate Agent SHALL mark the governance run as `hardGateFailed` in `governance/quality-gates.json` and SHALL report each failing gate with the required threshold and the actual measured value. Hard gate failures are non-blocking for the pipeline (Phase 5 and 6 still run) but are surfaced prominently in the final output review.

#### Scenario: Test coverage below 80% fails hard gate
- **WHEN** the Quality Gate Agent measures aggregate test coverage at 74%
- **THEN** `governance/quality-gates.json` SHALL record `testCoverageGate: { required: 80, actual: 74, status: "fail" }`

#### Scenario: All hard gates pass
- **WHEN** all 5 individual hard gates pass
- **THEN** `governance/quality-gates.json` SHALL record `hardGatesStatus: "pass"`
- **AND** the generation summary SHALL reflect the quality-validated status

### Requirement: Documentation Crew performance NFRs
The Documentation Crew (Phase 4a) SHALL complete full documentation generation — component doc pages, token catalog, generation narrative, ADRs, changelog, search index, and RFC template — in under 5 minutes. Output format SHALL be Markdown files plus a JSON search index (`docs/search-index.json`).

#### Scenario: Full doc generation completes within budget
- **WHEN** the Documentation Crew runs against a Comprehensive scope design system (25+ components)
- **THEN** all documentation artifacts SHALL be generated in under 5 minutes

#### Scenario: Doc output format is correct
- **WHEN** the Documentation Crew completes
- **THEN** all documentation files SHALL be in Markdown format
- **AND** `docs/search-index.json` SHALL be a valid JSON file covering all generated doc pages
