## ADDED Requirements

### Requirement: Brand Profile generation
The DS Bootstrap Crew SHALL conduct a structured brand discovery process using the Brand Discovery Agent (Agent 1) and produce a validated `brand-profile.json` file. The brand profile SHALL include: brand name, brand archetype, primary color palette, secondary/accent colors, neutral scale, typography (font families, weights, size scale), spacing scale, border radius scale, shadow scale, icon set preference, component scope list, accessibility level (WCAG AA or AAA), theming model (light/dark/high-contrast), and multi-brand configuration (brand identifier array under `themes.brands`).

#### Scenario: Brand profile written after interview
- **WHEN** the Brand Discovery Agent completes the interview
- **THEN** the DS Bootstrap Crew SHALL write a validated `brand-profile.json` to the output folder root
- **AND** the file SHALL contain all required fields with no null or empty required values

#### Scenario: Multi-brand archetype recognized
- **WHEN** the brand profile specifies more than one entry in `themes.brands`
- **THEN** the Token Foundation Agent SHALL generate the multi-brand token file structure: `tokens/brands/<brand-id>.tokens.json` per brand alongside the base semantic token file
- **AND** the base `tokens/semantic.tokens.json` SHALL represent the default brand

### Requirement: Raw three-tier token generation
The Token Foundation Agent (Agent 2) SHALL generate three W3C DTCG-format token files from the brand profile: `tokens/base.tokens.json` (global tier), `tokens/semantic.tokens.json` (semantic tier), and `tokens/component.tokens.json` (component-scoped tier). These files are raw outputs — not yet validated or compiled. Token references between tiers SHALL follow the W3C DTCG alias syntax (`{token.path}`). Semantic tokens SHALL define per-theme values for all configured themes.

#### Scenario: Global tier content
- **WHEN** the Token Foundation Agent generates `tokens/base.tokens.json`
- **THEN** the file SHALL contain all primitive values: full color palettes, raw type sizes, raw spacing steps, raw shadow definitions — with no semantic meaning attached
- **AND** tokens SHALL use W3C DTCG `$value` and `$type` keys

#### Scenario: Semantic tier references global tier
- **WHEN** the Token Foundation Agent generates `tokens/semantic.tokens.json`
- **THEN** semantic tokens SHALL reference global tokens using W3C DTCG alias syntax (e.g., `{color.blue.500}`)
- **AND** semantic tokens SHALL carry per-theme values (e.g., `color.background.default` resolves differently in light vs. dark theme)

#### Scenario: Component tier references semantic tier
- **WHEN** the Token Foundation Agent generates `tokens/component.tokens.json`
- **THEN** component-scoped tokens SHALL reference semantic tokens, NEVER global tokens
- **AND** component-scoped tokens SHALL be namespaced by component (e.g., `button.background.default`)

#### Scenario: Multi-brand token file generation
- **WHEN** `themes.brands` in the brand profile contains two or more brand identifiers
- **THEN** for each brand identifier, the Token Foundation Agent SHALL write `tokens/brands/<brand-id>.tokens.json` containing only the semantic token values that differ from the base
- **AND** the merge strategy at compilation time SHALL be: base semantic tokens overridden by brand-specific token values

### Requirement: Canonical spec YAML generation
The Spec Generation Agent (within DS Bootstrap Crew) SHALL generate one `*.spec.yaml` file per component and primitive in the output scope. Spec files SHALL be written to `specs/` in the output folder. Each spec file SHALL define: component name, description, props schema (name, type, required/optional, default), variant list, state list, token references, accessibility requirements, composition rules (allowed children/parents), and test scenarios. The list of components to generate SHALL be determined by the component scope collected during the brand interview.

#### Scenario: Spec file per component
- **WHEN** the component scope includes `Button`, `Input`, and `ThemeProvider`
- **THEN** the DS Bootstrap Crew SHALL write `specs/Button.spec.yaml`, `specs/Input.spec.yaml`, and `specs/ThemeProvider.spec.yaml`
- **AND** each file SHALL be syntactically valid YAML with all required spec keys present

#### Scenario: Spec includes token references
- **WHEN** generating `Button.spec.yaml`
- **THEN** the spec SHALL reference component-scoped token names for all visual properties (e.g., `button.background.default`, `button.text.default`)
- **AND** SHALL NOT embed raw hex color values in the spec

#### Scenario: Primitives always included
- **WHEN** the DS Bootstrap Crew runs
- **THEN** spec files for the core primitive set SHALL ALWAYS be generated regardless of component scope: `Box`, `Stack`, `Text`, `Grid`, `Icon`, `Pressable`, `Divider`, `Spacer`, `ThemeProvider`
- **AND** additional component specs SHALL be generated for all scope items collected in the brand interview

### Requirement: Project scaffolding
The Pipeline Configuration Agent (Agent 5) SHALL generate project configuration files required by all downstream crews for TypeScript compilation, testing, and building. The generated files SHALL be: `tsconfig.json`, `vite.config.ts` (library mode), `vitest.config.ts`, and `pipeline-config.json`. These files SHALL be written in Phase 1 so that all subsequent phases can compile and test without waiting for the Release Crew.

#### Scenario: TypeScript configuration generated
- **WHEN** Phase 1 completes
- **THEN** `tsconfig.json` SHALL exist in the output folder root
- **AND** it SHALL configure `strict: true`, `jsx: react-jsx`, and output paths appropriate for a library package

#### Scenario: Pipeline config seeds governance
- **WHEN** Phase 1 completes
- **THEN** `pipeline-config.json` SHALL contain quality gate thresholds, coverage requirements, a11y level, allowed archetype metadata, and plugin registrations
- **AND** this file SHALL serve as the input seed for the Governance Crew in Phase 4

#### Scenario: Downstream compilation succeeds with Phase 1 scaffolding
- **WHEN** Phase 3 (component generation) runs `tsc --noEmit` on generated TSX files
- **THEN** the compilation SHALL use the `tsconfig.json` written in Phase 1
- **AND** SHALL NOT require any additional TypeScript configuration to be generated later

### Requirement: DS archetype selection
The Brand Discovery Agent SHALL determine the design system archetype based on the brand interview. The five supported archetypes are: **Enterprise B2B** (information-dense, subtle palette, high data-table usage), **Consumer B2C** (expressive, brand-forward, emotion-driven), **Mobile-First** (touch-optimized, large tap targets, minimal nesting), **Multi-Brand Platform** (token abstraction as primary concern, brand-agnostic primitives), and **Custom** (no archetype defaults applied). The selected archetype SHALL be written to `brand-profile.json` under the `archetype` key and SHALL influence default component scope, spacing density, border radius style, and motion defaults.

#### Scenario: Enterprise B2B archetype defaults
- **WHEN** the user selects the Enterprise B2B archetype
- **THEN** the brand profile SHALL default to: Comprehensive component scope, 4px spacing unit, 2px border radius, subtle shadow scale, and AA accessibility level
- **AND** the Spec Generation Agent SHALL prefer table, form, and data-display component specs in its generation order

#### Scenario: Multi-Brand Platform archetype defaults
- **WHEN** the user selects the Multi-Brand Platform archetype
- **THEN** the brand profile SHALL default to Standard component scope
- **AND** the Token Foundation Agent SHALL generate the multi-brand token file structure even if `themes.brands` contains only one identifier

#### Scenario: Custom archetype applies no defaults
- **WHEN** the user selects the Custom archetype
- **THEN** no archetype-based defaults SHALL be applied to component scope, spacing, radius, or motion
- **AND** the brand interview SHALL prompt for each of these fields explicitly

### Requirement: Component scope tiers
The brand profile SHALL record a component scope tier under the `componentScope` key: `starter`, `standard`, or `comprehensive`. The Spec Generation Agent SHALL use the scope tier to determine which component specs to generate, in addition to always generating the 9 core primitives.

- **Starter** (10 components total): `Button`, `Input`, `Checkbox`, `Radio`, `Select`, `Card`, `Badge`, `Avatar`, `Alert`, `Modal`
- **Standard** (19 components = Starter + 9): adds `Table`, `Tabs`, `Accordion`, `Tooltip`, `Toast`, `Dropdown`, `Pagination`, `Breadcrumb`, `Navigation`
- **Comprehensive** (26+ components = Standard + 7 base + any custom): adds `DatePicker`, `DataGrid`, `TreeView`, `Drawer`, `Stepper`, `FileUpload`, `RichText` plus any additional components specified during the brand interview

#### Scenario: Starter scope generates correct component set
- **WHEN** the brand profile specifies `componentScope: "starter"`
- **THEN** the Spec Generation Agent SHALL generate spec files for all 9 core primitives plus the 10 Starter components (19 total spec files)

#### Scenario: Standard scope generates correct component set
- **WHEN** the brand profile specifies `componentScope: "standard"`
- **THEN** the Spec Generation Agent SHALL generate spec files for all 9 core primitives plus the 19 Standard components (28 total spec files)

#### Scenario: Comprehensive scope includes additional custom components
- **WHEN** the brand profile specifies `componentScope: "comprehensive"` and the user named two custom components during the interview
- **THEN** the Spec Generation Agent SHALL generate all 9 core primitives plus the 25+ base Comprehensive components plus the two custom component specs

#### Scenario: Comprehensive-tier components default to beta lifecycle
- **WHEN** a component is part of the Comprehensive scope tier (not Starter or Standard)
- **THEN** its spec SHALL include `lifecycle: "beta"` in the component metadata
- **AND** its generated documentation page SHALL display a beta badge

### Requirement: Complete brand profile schema
The `brand-profile.json` produced by the Brand Discovery Agent SHALL conform to the following full schema. All keys listed as required SHALL be present with non-null values. The Token Foundation Agent SHALL use all schema fields as inputs; fields not provided SHALL receive archetype-appropriate defaults.

Required schema fields:
- `name` (string): brand name
- `archetype` (string): one of `enterprise-b2b`, `consumer-b2c`, `mobile-first`, `multi-brand-platform`, `custom`
- `componentScope` (string): one of `starter`, `standard`, `comprehensive`
- `colors.primary` (object): hex color palette steps (50–950)
- `colors.secondary` (object): hex palette or null
- `colors.neutral` (object): hex palette steps (50–950)
- `colors.semantic` (object): `success`, `warning`, `error`, `info` hex values
- `typography.fontFamilies` (object): `heading`, `body`, `mono` font-family strings
- `typography.fontWeights` (array): numeric weights used (e.g., [400, 500, 700])
- `typography.sizeScale` (array): ordered list of rem size steps
- `spacing.unit` (number): base spacing unit in pixels (e.g., 4 or 8)
- `spacing.scale` (array): ordered multiplier steps (e.g., [0, 0.5, 1, 1.5, 2, 3, 4, 6, 8, 12, 16])
- `borderRadius` (object): named scale — `none`, `sm`, `md`, `lg`, `xl`, `full`
- `elevation` (object): named shadow scale — `none`, `sm`, `md`, `lg`, `xl`
- `motion` (object): `duration` scale (ms steps) and `easing` named curves (`ease-in`, `ease-out`, `ease-in-out`, `spring`)
- `breakpoints` (object): named breakpoints — `xs`, `sm`, `md`, `lg`, `xl`, `2xl` as pixel values
- `accessibility.level` (string): `AA` or `AAA`
- `themes.modes` (array): one or more of `light`, `dark`, `high-contrast`
- `themes.default` (string): the default active theme mode (must be in `themes.modes`)
- `themes.brands` (array): brand identifier strings (minimum one matching `name`)
- `themes.brandOverrides` (object): per-brand token override maps keyed by brand identifier
- `componentOverrides` (object): per-component design decision overrides (e.g., `{"Button": {"borderRadius": "full"}}`)
- `iconSet` (string): preferred icon library name or `custom`
- `plugins` (array): optional tool plugin identifiers

#### Scenario: Full brand profile written after interview
- **WHEN** the brand interview completes
- **THEN** `brand-profile.json` SHALL contain all required schema fields with no null or missing required values
- **AND** the Token Foundation Agent SHALL fail-fast if any required field is absent when it reads the brand profile

#### Scenario: W3C DTCG theme extension format for multi-theme tokens
- **WHEN** the Token Foundation Agent generates `tokens/semantic.tokens.json` for a multi-theme design system
- **THEN** tokens with per-theme values SHALL use the `$extensions.com.daf.themes` W3C DTCG extension key to store per-theme overrides alongside the default `$value`
- **AND** the token compiler SHALL expand these extensions into theme-specific CSS custom property files at compile time

### Requirement: Primitive Scaffolding Agent
The Primitive Scaffolding Agent (Agent 3, Tier 1) SHALL generate spec files exclusively for the 9 core primitives: `Box`, `Stack`, `Text`, `Grid`, `Icon`, `Pressable`, `Divider`, `Spacer`, `ThemeProvider`. These specs SHALL be generated before the Core Component Agent runs, as components depend on primitives as their structural foundation.

The `Stack` primitive spec SHALL define that `Stack.tsx` exports both `HStack` and `VStack` as named exports from a single module (not separate files). The `Pressable` primitive spec SHALL define the forbidden self-nesting rule: a `Pressable` SHALL NOT be a direct or indirect child of another `Pressable`.

#### Scenario: Primitives generated before components
- **WHEN** Phase 1 runs
- **THEN** the Primitive Scaffolding Agent SHALL complete before the Core Component Agent begins
- **AND** all 9 core primitive spec files SHALL be written to `specs/` before any component spec is generated

#### Scenario: Stack exports HStack and VStack
- **WHEN** `specs/Stack.spec.yaml` is generated
- **THEN** it SHALL specify that the implementation exports both `HStack` (horizontal stack) and `VStack` (vertical stack) as named exports from `src/primitives/Stack.tsx`

#### Scenario: Pressable forbidden self-nesting rule
- **WHEN** `specs/Pressable.spec.yaml` is generated
- **THEN** the composition rules section SHALL include a mutual exclusion rule prohibiting `Pressable` as a descendant of another `Pressable`

### Requirement: Core Component Agent
The Core Component Agent (Agent 4, Tier 1) SHALL generate spec files for all non-primitive components determined by the scope tier. The Core Component Agent SHALL run AFTER the Primitive Scaffolding Agent completes (primitive specs must exist before component specs reference them). Component specs SHALL reference primitive component names (e.g., `Box`, `Stack`, `Pressable`) as allowed composition parents and children, not raw HTML elements.

#### Scenario: Component spec references primitives
- **WHEN** `specs/Button.spec.yaml` is generated by the Core Component Agent
- **THEN** its composition rules SHALL reference `Pressable` as its interactive root, not `<button>`
- **AND** its allowed children SHALL be drawn from the generated primitive set

#### Scenario: Component scope respected
- **WHEN** the brand profile specifies `componentScope: "standard"`
- **THEN** the Core Component Agent SHALL generate specs for all Starter (10) plus Standard extension (9) components
- **AND** SHALL NOT generate specs for Comprehensive-only components unless they appear in the explicit component list

### Requirement: Human Gate — Brand Profile Approval
After the brand interview and before Phase 1 begins, the CLI SHALL pause and present a formatted summary of the generated `brand-profile.json` to the user. The user MUST explicitly approve the brand profile before the pipeline proceeds. If the user rejects it, the CLI SHALL allow the user to re-answer specific interview questions or provide a corrected `brand-profile.json` file directly (bypassing the interview entirely).

#### Scenario: Brand profile approved — pipeline starts
- **WHEN** the user reviews the brand profile summary and enters approval
- **THEN** the CLI SHALL immediately begin Phase 1 with the approved `brand-profile.json`

#### Scenario: Brand profile rejected — re-interview
- **WHEN** the user rejects the brand profile during the approval gate
- **THEN** the CLI SHALL either re-run the full interview or allow the user to correct specific fields
- **AND** SHALL re-present the approval summary after re-generation

#### Scenario: Hand-written brand profile bypasses interview
- **WHEN** the user places a valid `brand-profile.json` in the output folder before running the CLI
- **THEN** the CLI SHALL detect the existing file, skip the brand interview, display the file contents for confirmation, and proceed to Phase 1 on approval
- **AND** SHALL validate that all required schema fields are present before accepting the bypass
