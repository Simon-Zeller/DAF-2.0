## ADDED Requirements

### Requirement: Token schema validation
The Token Validation Agent (Agent 8, Token Ingestion Agent Agent 7) SHALL validate all three token tier files against the W3C DTCG schema. Validation SHALL check: required `$value` and `$type` keys on each token, valid `$type` values (color, dimension, fontFamily, fontWeight, fontStyle, duration, cubicBezier, number, string), valid alias reference syntax, no circular references, and naming convention compliance (kebab-case, namespaced by tier). Any violation SHALL produce a structured rejection with the token name, violated rule, and suggested correction.

#### Scenario: Valid token file passes validation
- **WHEN** all tokens in `tokens/base.tokens.json` conform to W3C DTCG schema with valid types, values, and naming
- **THEN** the Token Validation Agent SHALL mark the file as valid and proceed to compilation

#### Scenario: Circular reference detected
- **WHEN** a semantic token aliases another semantic token that in turn aliases the first token
- **THEN** the Token Validation Agent SHALL flag the circular reference with the full alias chain
- **AND** SHALL produce a structured rejection for the retry protocol

#### Scenario: Naming convention violation
- **WHEN** a global token uses camelCase instead of kebab-case (e.g., `primaryBlue` instead of `primary-blue`)
- **THEN** the Token Validation Agent SHALL produce a structured rejection specifying the token name, the violated rule (kebab-case required), and the suggested corrected name

### Requirement: WCAG contrast checking
The Token Validation Agent SHALL perform WCAG contrast ratio calculations for all semantic color token pairs that represent foreground/background relationships. Color token pairs with a contrast ratio below the configured WCAG level (AA: 4.5:1 for normal text, 3:1 for large text; AAA: 7:1 for normal text) SHALL be flagged as validation failures and trigger the retry protocol.

#### Scenario: Contrast failure triggers retry
- **WHEN** `color.text.default` over `color.background.default` yields a contrast ratio of 3.2:1 (below AA 4.5:1 for normal text)
- **THEN** the Token Validation Agent SHALL produce a structured rejection specifying the token pair, the measured ratio, the required ratio, and a suggested replacement value
- **AND** the rejection SHALL be routed to the Token Foundation Agent for correction

#### Scenario: Contrast check accounts for themes
- **WHEN** a semantic color token resolves to different values per theme
- **THEN** the contrast check SHALL be performed for each theme variant independently
- **AND** a failure in any theme SHALL produce a structured rejection

### Requirement: Token compilation
The Token Compilation Agent (Agent 9, deterministic) SHALL compile validated token files into all configured platform outputs. Token compilation SHALL produce: `tokens/compiled/variables.css` (default theme CSS custom properties), `tokens/compiled/variables-light.css`, `tokens/compiled/variables-dark.css`, `tokens/compiled/variables-high-contrast.css`, `tokens/compiled/variables.scss` (SCSS variables), `tokens/compiled/tokens.ts` (TypeScript constants), and `tokens/compiled/tokens.json` (flat resolved JSON). The agent triggers the compilation tool; the tool executes deterministically.

#### Scenario: CSS custom properties use semantic names
- **WHEN** the token compiler generates `tokens/compiled/variables.css`
- **THEN** all CSS custom property names SHALL map to semantic token names (e.g., `--color-background-default`)
- **AND** SHALL NOT expose global token names as CSS custom properties in the semantic compiled output

#### Scenario: Per-theme CSS files contain the same property names
- **WHEN** the compiler generates `variables-light.css` and `variables-dark.css`
- **THEN** both files SHALL define the same set of CSS custom property names
- **AND** the values SHALL differ according to the per-theme values in `tokens/semantic.tokens.json`

#### Scenario: TypeScript constants are type-safe
- **WHEN** the compiler generates `tokens/compiled/tokens.ts`
- **THEN** the file SHALL export named constants as `const` strings
- **AND** the file SHALL pass `tsc --noEmit` without errors using the project's `tsconfig.json`

### Requirement: Multi-brand compilation
For multi-brand archetypes, the Token Engine Crew SHALL compile brand-specific CSS output for each brand. Each brand's compiled CSS SHALL be placed at `tokens/compiled/brands/<brand-id>/variables.css` (and per-theme variants). The compilation SHALL merge base semantic tokens with the brand override tokens from `tokens/brands/<brand-id>.tokens.json` at compilation time. Brand override files SHALL contain only the tokens that differ from the base.

#### Scenario: Brand override applied at compile time
- **WHEN** `tokens/brands/brand-a.tokens.json` overrides `color.background.default`
- **THEN** `tokens/compiled/brands/brand-a/variables.css` SHALL contain the overridden value for `--color-background-default`
- **AND** tokens NOT overridden by `brand-a` SHALL inherit values from the base `tokens/semantic.tokens.json`

#### Scenario: Missing brand override file
- **WHEN** the brand profile specifies a brand identifier for which no override token file exists
- **THEN** the Token Engine Crew SHALL fail-fast with an error identifying the missing file before compilation begins

### Requirement: Token diff generation
The Token Engine Crew SHALL generate a `tokens/diff.json` file that records all token changes relative to a prior run. If no prior run exists, the diff SHALL record all tokens as `added`. The diff SHALL categorize each change as `added`, `modified`, or `removed` and include the token name, prior value (if any), and new value.

#### Scenario: First-run diff records all tokens as added
- **WHEN** no prior `tokens/diff.json` exists in the output folder
- **THEN** the generated `tokens/diff.json` SHALL list all tokens with status `added`

#### Scenario: Modified token recorded in diff
- **WHEN** a token's `$value` changes between runs (cross-phase retry or resume)
- **THEN** `tokens/diff.json` SHALL record the token with status `modified`, including the prior value and the new value

### Requirement: Token Integrity Agent
The Token Integrity Agent (Agent 10, Tier 2) SHALL enforce tier discipline across all three token tiers and detect structural token defects before compilation. The agent SHALL apply the following rules:

**Tier discipline rules:**
- Component-scoped tokens SHALL reference only semantic tokens (never global tokens directly)
- Semantic tokens SHALL reference only global tokens (never component-scoped tokens)
- No tier skipping is permitted: a component token that references a global token bypassing the semantic tier SHALL be flagged as a tier discipline violation

**Structural integrity rules:**
- **Orphan token detection**: tokens that are defined in any tier file but are never referenced by any higher-tier token or any component source SHALL be flagged as orphans and listed in the integrity report
- **Phantom reference detection**: alias references that point to a token that does not exist in the expected tier (e.g., a semantic token that aliases `{color.brand.foo}` when `color.brand.foo` is not defined in `base.tokens.json`) SHALL be flagged as phantom references

Results SHALL be written to `reports/token-integrity.json`. Any tier discipline violation or phantom reference SHALL be a fatal integrity error that triggers the retry protocol against the Token Foundation Agent. Orphan tokens SHALL be reported as warnings only.

#### Scenario: Component token referencing global tier is rejected
- **WHEN** `tokens/component.tokens.json` contains a token that aliases `{color.blue.500}` (a global tier token, not a semantic tier token)
- **THEN** the Token Integrity Agent SHALL flag this as a tier discipline violation
- **AND** the structured rejection SHALL specify the component token name and the forbidden alias target

#### Scenario: Phantom reference detected
- **WHEN** `tokens/semantic.tokens.json` contains `color.text.muted: { $value: "{color.neutral.450}" }` and `color.neutral.450` does not exist in `tokens/base.tokens.json`
- **THEN** the Token Integrity Agent SHALL flag a phantom reference
- **AND** SHALL include the full attempted alias chain and the missing token name in the rejection

#### Scenario: Orphan token reported as warning
- **WHEN** `tokens/base.tokens.json` defines `color.brand.legacy-teal` but it is not referenced by any semantic token or component source
- **THEN** the Token Integrity Agent SHALL record it in `reports/token-integrity.json` as an orphan warning
- **AND** SHALL NOT trigger the retry protocol for orphan warnings

#### Scenario: Clean token set passes integrity check
- **WHEN** all tokens follow tier discipline, have no phantom references, and all orphan warnings are below the configured threshold
- **THEN** the Token Integrity Agent SHALL mark the token set as integrity-validated and proceed to compilation

### Requirement: Additional platform compilation targets
When the brand profile includes additional platform targets in the `plugins` array, the Token Compilation Agent SHALL produce additional compiled outputs beyond the default CSS/SCSS/TS/JSON set:

- **Tailwind CSS** (`tailwind`): produce `tokens/compiled/tailwind.config.ts` with a tokens-derived `theme.extend` configuration (colors, fontFamily, fontSize, spacing, borderRadius, boxShadow, transitionDuration, transitionTimingFunction)
- **iOS Swift** (`swift`): produce `tokens/compiled/swift/DesignTokens.swift` as a Swift enum with nested namespaces for each token category and `UIColor`/`CGFloat` typed constants
- **Android XML** (`android-xml`): produce `tokens/compiled/android/colors.xml` and `tokens/compiled/android/dimens.xml` in Android resource format
- **Jetpack Compose** (`compose`): produce `tokens/compiled/compose/DesignTokens.kt` as a Kotlin object with `Color`, `Dp`, `Sp`, and `TextStyle` typed constants

All additional platform outputs SHALL be compiled from the same validated W3C DTCG source and SHALL be consistent with the CSS custom properties output.

#### Scenario: Tailwind config generated from tokens
- **WHEN** `tailwind` is listed in the brand profile `plugins` array
- **THEN** `tokens/compiled/tailwind.config.ts` SHALL be generated with all semantic color, spacing, font, and radius tokens mapped into Tailwind's `theme.extend` structure
- **AND** the file SHALL be importable by a `tailwind.config.ts` at the consumer project root without modification

#### Scenario: Swift output uses correct UIColor types
- **WHEN** `swift` is listed in the brand profile `plugins` array
- **THEN** `tokens/compiled/swift/DesignTokens.swift` SHALL define color tokens as `UIColor` constants
- **AND** dimension tokens SHALL be typed as `CGFloat`

### Requirement: Token Engine performance NFRs
- Token compilation for a set of up to 5,000 tokens SHALL complete in under 30 seconds on a standard developer machine
- The full Token Engine Crew run (ingestion → validation → integrity check → compilation → multi-brand compilation → diff generation) SHALL complete in under 90 seconds for a standard design system
- Compilation MAY be parallelized across theme variants (light, dark, high-contrast) and brand variants to meet these targets
