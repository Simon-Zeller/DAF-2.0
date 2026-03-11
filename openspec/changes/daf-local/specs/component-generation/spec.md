## ADDED Requirements

### Requirement: TSX source generation from spec files
The Code Generation Agent (Agent 14) SHALL generate TSX source files for all components and primitives from their corresponding `*.spec.yaml` files and compiled token outputs. Each primitive SHALL produce a single `src/primitives/<Name>.tsx`. Each component SHALL produce `src/components/<Name>/<Name>.tsx`. All generated TSX SHALL: import tokens only from the compiled `tokens/compiled/tokens.ts`, use semantic token names for all style properties, implement all props, variants, and states defined in the spec, and conform to the project's TypeScript configuration.

#### Scenario: Button TSX generated from spec
- **WHEN** `specs/Button.spec.yaml` defines a `variant` prop with values `primary`, `secondary`, `destructive`
- **THEN** `src/components/Button/Button.tsx` SHALL implement all three variant values
- **AND** each variant SHALL map its visual properties to the appropriate component-scoped token name from the spec

#### Scenario: Component uses only semantic tokens
- **WHEN** a generated component file is scanned for token usage
- **THEN** all token references SHALL resolve to semantic or component-scoped token identifiers
- **AND** no raw hex, RGB, or named CSS color value SHALL appear in the component source

#### Scenario: ThemeProvider primitive generated
- **WHEN** the component scope includes `ThemeProvider`
- **THEN** `src/primitives/ThemeProvider.tsx` SHALL be generated
- **AND** SHALL implement runtime theme switching via CSS class application on the root element
- **AND** SHALL expose a `useTheme()` hook returning both `theme` and `brand` properties

### Requirement: Test file generation
The Code Generation Agent SHALL generate a `*.test.tsx` file alongside each component and primitive TSX file. Test files SHALL cover: rendering without errors for each variant and state, prop contract validation (required props, default values), accessibility smoke test (axe render), and at minimum one scenario from the spec's test scenarios.

#### Scenario: Test file co-located with source
- **WHEN** `src/components/Button/Button.tsx` is generated
- **THEN** `src/components/Button/Button.test.tsx` SHALL also be generated in the same directory

#### Scenario: Tests cover all variants
- **WHEN** the Button spec defines three variants
- **THEN** the test file SHALL include at least one test case per variant rendering

#### Scenario: Tests pass TypeScript compilation
- **WHEN** `tsc --noEmit` is run against the test file
- **THEN** it SHALL produce no type errors

### Requirement: Storybook story generation
The Code Generation Agent SHALL generate a `*.stories.tsx` file alongside each component and primitive. Stories SHALL use Storybook CS Format 3 (CSF3). Each story file SHALL export a default meta object and at minimum one named story per variant and state defined in the spec.

#### Scenario: Story file per component
- **WHEN** `src/components/Input/Input.tsx` is generated
- **THEN** `src/components/Input/Input.stories.tsx` SHALL be generated
- **AND** SHALL export a CSF3 default meta object and named story exports for each Input variant and state

#### Scenario: Stories compile without errors
- **WHEN** `tsc --noEmit` is run against the story file
- **THEN** it SHALL produce no type errors

### Requirement: Render validation
The Render Validation Agent (Agent 15, hybrid) SHALL perform headless rendering of each generated component using a headless browser or virtual DOM renderer. A component SHALL fail render validation if: the rendered output is empty, rendering throws an unhandled exception, or a significant visual artifact is detected (malformed layout, invisible content). Render validation failures SHALL trigger the retry protocol against the Code Generation Agent.

#### Scenario: Empty render output fails validation
- **WHEN** a generated component renders to an empty DOM subtree
- **THEN** the Render Validation Agent SHALL flag a render failure
- **AND** the structured rejection SHALL include the component name and "empty output" as the failure reason

#### Scenario: Render exception fails validation
- **WHEN** rendering a component throws a React error or exception
- **THEN** the Render Validation Agent SHALL capture the error message and stack trace
- **AND** SHALL include them in the structured rejection for the Code Generation Agent

### Requirement: TypeScript compilation validation
After generating each batch of component files, the pipeline SHALL run `tsc --noEmit` using the project's `tsconfig.json`. Any type errors SHALL trigger the retry protocol against the Code Generation Agent. The compilation check SHALL cover source files, test files, and story files.

#### Scenario: Type error triggers retry
- **WHEN** `tsc --noEmit` reports a type error in a generated component file
- **THEN** the error message, file path, and line number SHALL be included in the structured rejection
- **AND** the Code Generation Agent SHALL receive the rejection as additional context for retry

### Requirement: Accessibility enforcement and patching
The Accessibility Agent (Agent 19) SHALL audit each generated component using axe-core and SHALL patch the component source in-place to resolve critical and serious accessibility violations. Patches SHALL add ARIA attributes, keyboard event handlers, and focus management as required. After patching, the pipeline SHALL run a post-patch re-validation pass: `tsc --noEmit` on the patched source AND render validation. Failures in the post-patch pass SHALL trigger the retry protocol against the Accessibility Agent.

#### Scenario: Missing ARIA label patched in-place
- **WHEN** axe-core reports a missing `aria-label` on an interactive element in `Button.tsx`
- **THEN** the Accessibility Agent SHALL patch `Button.tsx` in-place to add the required ARIA attribute
- **AND** the patched file SHALL be re-validated with `tsc --noEmit` before the Component Factory Crew is marked complete

#### Scenario: A11y patch introduces type error
- **WHEN** the Accessibility Agent patches a component and the patched source fails `tsc --noEmit`
- **THEN** the type error SHALL trigger the retry protocol against the Accessibility Agent
- **AND** the Accessibility Agent SHALL produce a corrected patch that resolves both the a11y violation and the type error

#### Scenario: Critical violations only — non-critical are warnings
- **WHEN** axe-core reports a violation with impact `moderate` or lower
- **THEN** the Accessibility Agent SHALL record it in `reports/a11y-audit.json` as a warning
- **AND** SHALL NOT trigger the retry protocol for non-critical violations

### Requirement: Quality scoring
The Quality Scoring tool (deterministic) SHALL compute a per-component quality score and write results to `reports/quality-scorecard.json`. Scores SHALL be calculated from: spec coverage (all props/variants/states implemented), test coverage (test cases per variant), a11y compliance (zero critical violations), token compliance (no hardcoded values), and TypeScript strictness (compiled clean).

#### Scenario: Quality scorecard written per component
- **WHEN** Phase 3 completes
- **THEN** `reports/quality-scorecard.json` SHALL contain an entry for every generated component and primitive
- **AND** each entry SHALL include numeric scores for each scoring dimension and an overall score

#### Scenario: Failed components included in scorecard
- **WHEN** a component exhausts its retry limit and is marked `failed`
- **THEN** the quality scorecard SHALL include the failed component with a score of 0 and a `failed: true` flag

### Requirement: Screenshot capture for render baselines
The Render Validation Agent SHALL capture a screenshot of each component variant and state after successful render validation. Screenshots SHALL be written to `screenshots/<ComponentName>--<variant>.png`. Screenshots serve as render validation baselines.

#### Scenario: Screenshot per variant
- **WHEN** the Button component has variants `primary`, `secondary`, `destructive` and state `disabled`
- **THEN** the screenshots directory SHALL contain: `Button--primary.png`, `Button--secondary.png`, `Button--destructive.png`, `Button--disabled.png`

### Requirement: Generation priority order
The Code Generation Agent SHALL generate components in the following priority order: (1) core primitives (`Box`, `Stack`, `Text`, `Grid`, `Icon`, `Pressable`, `Divider`, `Spacer`, `ThemeProvider`), (2) simple leaf components (no composition children, e.g., `Badge`, `Spinner`, `Divider`), (3) complex composite components (components that compose other components, e.g., `Modal`, `Table`, `DataGrid`). Within each tier, components SHALL be generated in alphabetical order to ensure deterministic output.

#### Scenario: Primitives generated before simple components
- **WHEN** the Code Generation Agent begins component generation
- **THEN** all 9 core primitives SHALL be written to `src/primitives/` before any component in `src/components/` is generated

#### Scenario: Composite components generated last
- **WHEN** the Code Generation Agent processes the component list
- **THEN** components classified as composites (referencing other generated components in their spec's composition rules) SHALL be placed in the last generation batch

### Requirement: `data-testid` attribute on all generated components
Every generated TSX component and primitive SHALL include a `data-testid` attribute on its root element. The `data-testid` value SHALL default to the component name in kebab-case (e.g., `data-testid="button"`) and SHALL be passable as a prop so consumers can override it. The `data-testid` prop SHALL be of type `string` and SHALL be optional with the component name as default.

#### Scenario: Button has data-testid on root element
- **WHEN** `src/components/Button/Button.tsx` is generated
- **THEN** the root element SHALL render `data-testid={testId ?? "button"}`
- **AND** the Button props interface SHALL include `testId?: string`

#### Scenario: Primitive has data-testid
- **WHEN** `src/primitives/Stack.tsx` is generated
- **THEN** the root element SHALL render `data-testid={testId ?? "stack"}`

### Requirement: Result Assembly Agent
The Result Assembly Agent (Agent 16, Tier 3) SHALL assemble the Phase 3 generation report from all Design-to-Code Crew outputs after each component batch completes. The agent SHALL compile a structured `reports/generation-summary.json` (Phase 3 section) containing: total components attempted, components succeeded, components failed (with names and last error), overall generation status, and a confidence score per component. The confidence score (0.0–1.0) SHALL reflect how closely the generated TSX matches the spec (based on: all props implemented, all variants present, token compliance, test count vs. spec scenario count).

#### Scenario: Generation summary written after Phase 3
- **WHEN** the Design-to-Code Crew completes all components
- **THEN** `reports/generation-summary.json` SHALL contain a `phase3` section with counts for attempted, succeeded, and failed components
- **AND** each failed entry SHALL include the component name, attempt count, and last structured rejection message

#### Scenario: Confidence score recorded per component
- **WHEN** the Result Assembly Agent processes a completed component
- **THEN** the generation summary SHALL include a `confidence` field (0.0–1.0) for that component
- **AND** components with full spec coverage, passing tests, and no token violations SHALL score 1.0

### Requirement: Composition Agent
The Composition Agent (Agent 18, Tier 1) SHALL compose complex components by nesting primitive and simple components according to spec-defined composition rules. The Composition Agent is distinct from the Code Generation Agent: the Code Generation Agent generates leaf-level implementations, while the Composition Agent assembles composites. The Composition Agent SHALL enforce the following structural rules:

- **Forbidden nesting**: `Pressable` SHALL NOT be placed inside another `Pressable` (direct or indirect)
- **Required slots**: if a spec defines required named slots (e.g., a `Modal` spec requires a `header`, `body`, and `footer` slot), the Composition Agent SHALL implement all required slots
- **Depth limit**: component composition SHALL NOT exceed 4 levels of nesting depth; any spec that would require deeper nesting SHALL be flagged and restructured using extraction

#### Scenario: Modal composed from primitives
- **WHEN** the Composition Agent generates `src/components/Modal/Modal.tsx`
- **THEN** it SHALL be composed from `Box` (container), `Text` (title/body text nodes), and `Pressable` (close button) primitives
- **AND** SHALL implement `header`, `body`, and `footer` slots as required by the Modal spec

#### Scenario: Pressable inside Pressable rejected
- **WHEN** the Composition Agent generates a component that would result in a `Pressable` as a descendant of another `Pressable`
- **THEN** the Composition Agent SHALL restructure the component to eliminate the forbidden nesting
- **AND** SHALL log the restructuring decision to `reports/generation-summary.json`

#### Scenario: Depth limit exceeded — extraction applied
- **WHEN** component composition would exceed 4 nesting levels
- **THEN** the Composition Agent SHALL extract an inner sub-component and reference it by name
- **AND** the extracted sub-component SHALL receive its own spec entry and `src/` file

### Requirement: Quality scoring formula
The Quality Scoring tool SHALL compute the composite quality score using the following weighted dimensions:
- **Test coverage** (25%): percentage of spec-defined scenarios covered by test cases
- **Accessibility pass rate** (25%): percentage of components with zero critical axe-core violations
- **Token compliance** (20%): percentage of style properties using semantic token constants (vs. hardcoded values)
- **Composition depth** (15%): score penalised for nesting depth violations and forbidden composition; 1.0 for clean composition
- **Spec completeness** (15%): percentage of spec-defined props, variants, and states implemented in the TSX

A composite score of **70 or above out of 100** is the minimum passing threshold for the composite quality gate (Agent 20).

In addition to the composite gate, the Component Factory Crew (Agent 30 role at Phase 3 level) SHALL enforce **individual hard gates** that must each independently pass:
- Minimum 80% Vitest test coverage (lines) across all generated components
- Zero critical accessibility violations across all components
- All component-scoped token references resolve (no missing aliases)
- All components have a generated documentation page (`docs/components/<Name>.md`)
- All components have at least one usage example in their docs

A component may pass the 70/100 composite gate but still fail an individual hard gate. Both the composite and all individual hard gates MUST pass for the Governance Crew to mark the pipeline as fully quality-validated.

#### Scenario: Composite score below 70 fails quality gate
- **WHEN** a component's weighted score across all dimensions is 68/100
- **THEN** the quality scorecard SHALL flag the component with `belowCompositThreshold: true`
- **AND** the Governance Crew Quality Gate Agent SHALL report the failure before finalizing governance artifacts

#### Scenario: Individual hard gate fails despite composite passing
- **WHEN** a component's composite score is 75/100 but test coverage is 72% (below 80% hard gate)
- **THEN** the quality scorecard SHALL show `compositePass: true` and `hardGateFail: "testCoverage"` for that component

### Requirement: Accessibility test appending pattern
The Accessibility Agent SHALL NOT generate a separate `*.a11y.test.tsx` file. Instead, it SHALL append an `describe('Accessibility', () => { ... })` block to the component's existing `*.test.tsx` file. The appended block SHALL contain Vitest test cases that call axe-core against each rendered component variant and assert zero critical violations. Post-patch re-validation SHALL run `tsc --noEmit` on the modified test file (not just the source file).

#### Scenario: Accessibility describe block appended to existing test
- **WHEN** the Accessibility Agent processes `src/components/Button/Button.tsx`
- **THEN** it SHALL append a `describe('Accessibility', ...) ` block to `src/components/Button/Button.test.tsx`
- **AND** SHALL NOT create a separate `Button.a11y.test.tsx` file

#### Scenario: AAA level enforces stricter contrast thresholds
- **WHEN** the brand profile specifies `accessibility.level: "AAA"`
- **THEN** the Accessibility Agent SHALL enforce 7:1 contrast ratio for normal text and 4.5:1 for large text (WCAG AAA thresholds)
- **AND** components that pass AA but fail AAA SHALL trigger the retry protocol rather than being recorded as warnings

### Requirement: Component generation performance NFRs (Design-to-Code Crew)
- A single component (primitives excluded) SHALL complete full generation, compilation, render validation, and a11y patching in under 5 minutes
- A full Starter scope (10 primitives + 10 components) SHALL complete Phase 3a in under 20 minutes
- A full Comprehensive scope (9 primitives + 25+ components) SHALL complete Phase 3a in under 60 minutes
- These targets assume a single machine with Anthropic API access; parallel component generation within Phase 3a is permitted to meet these targets

### Requirement: Component Factory Crew performance NFRs
The Component Factory Crew (Phase 3b) — spec validation, composition verification, accessibility enforcement, and quality scoring — SHALL complete its full pipeline in under 60 seconds per component. This target covers: spec validation (Agent 17), composition audit (Agent 18), accessibility patching and post-patch re-validation (Agent 19), and quality scoring (Agent 20).

#### Scenario: Factory pipeline completes within budget
- **WHEN** the Component Factory Crew processes a single component through all four agents
- **THEN** the total elapsed time for that component SHALL be under 60 seconds

#### Scenario: Factory pipeline scales linearly
- **WHEN** the Component Factory Crew processes a Starter scope (10 components + 9 primitives)
- **THEN** total elapsed time SHALL be under 19 minutes (60s × 19 components)
