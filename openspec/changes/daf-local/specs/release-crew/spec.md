## ADDED Requirements

### Requirement: Package assembly
The Release Crew SHALL generate a valid `package.json` at the output folder root. The file SHALL include: package name (derived from the brand profile), version (calculated by the Semver Agent), description, `main` entry pointing to the compiled barrel export, `types` entry pointing to the TypeScript types output, `peerDependencies` (React, React-DOM at minimum), `devDependencies` for build and test tooling, and a `files` list excluding internal pipeline artifacts (reports, screenshots, checkpoints).

#### Scenario: Package.json version calculated by Semver Agent
- **WHEN** `package.json` is generated
- **THEN** the `version` field SHALL be calculated by the Semver Agent (Agent 36) based on the token diff and generation scope
- **AND** SHALL conform to semver format (MAJOR.MINOR.PATCH)

#### Scenario: Package files list excludes pipeline artifacts
- **WHEN** `package.json` is generated
- **THEN** the `files` array SHALL NOT include `reports/`, `screenshots/`, checkpoint directories, `openspec/`, or internal pipeline configuration files
- **AND** SHALL include `src/`, `tokens/compiled/`, `docs/`

### Requirement: Barrel export generation
The Release Crew SHALL generate barrel `index.ts` files that export all public API surface: `src/index.ts` (re-exports all primitives and components), `src/primitives/index.ts` (exports all primitives), `src/components/index.ts` (exports all component sub-directories). Generated barrel files SHALL pass `tsc --noEmit`.

#### Scenario: Root barrel exports all primitives and components
- **WHEN** `src/index.ts` is generated
- **THEN** it SHALL re-export everything from `src/primitives/index.ts` and `src/components/index.ts`
- **AND** SHALL compile without TypeScript errors

#### Scenario: Failed components excluded from barrel exports
- **WHEN** a component exhausted its retry limit and is marked `failed`
- **THEN** the barrel `index.ts` files SHALL NOT include an export for that failed component
- **AND** the failure SHALL be noted in `reports/generation-summary.json`

### Requirement: Changelog prose generation
The Release Crew SHALL generate `docs/changelog.md` summarizing the generation run. The changelog SHALL be in Keep a Changelog format and SHALL include: the version generated, date, a summary of what was added (components, tokens, documentation), any components that failed or were excluded, and any retry events from the generation run.

#### Scenario: Changelog entry per generated version
- **WHEN** `docs/changelog.md` is generated
- **THEN** it SHALL contain at least one changelog entry under a version heading (matching `package.json` version)
- **AND** SHALL reference the components and token changes from this generation run (not generic placeholder text)

#### Scenario: Failed components noted in changelog
- **WHEN** at least one component exhausted its retry limit and was marked `failed`
- **THEN** the changelog SHALL include a "Known Issues" or "Excluded" section listing the failed component names and their last-known error

### Requirement: Semantic version calculation
The Semver Agent (Agent 36) SHALL calculate the version for the generated package. The calculation SHALL be based on: whether this is a first-generation run (1.0.0), whether the token diff contains breaking changes (major bump), whether new components or tokens were added (minor bump), or whether only fixes and enhancements were made (patch bump). The calculated version SHALL be entered into `package.json` and `docs/changelog.md`.

#### Scenario: First-generation run produces version 1.0.0
- **WHEN** no prior version exists (first pipeline run, no checkpoint history)
- **THEN** the Semver Agent SHALL set the version to `1.0.0`

#### Scenario: Breaking token change triggers major version bump
- **WHEN** `tokens/diff.json` contains removed tokens or renamed tokens that would break existing consumers
- **THEN** the Semver Agent SHALL calculate a major version bump
- **AND** the breaking change SHALL be noted in the changelog

### Requirement: Test execution and final summary
The Release Crew SHALL execute all Vitest tests (`tests/*.test.ts`, `src/**/*.test.tsx`) via the configured `vitest.config.ts` and record the results. The final test results SHALL be written to `reports/generation-summary.json` under a `testResults` key, updating the generation report produced in Phase 3. The Release Crew SHALL report the number of passing and failing tests. Test failures SHALL be recorded in the generation summary but SHALL NOT block the output — the design system folder SHALL still be written as the pipeline output.

#### Scenario: Test results appended to generation summary
- **WHEN** the Release Crew completes test execution
- **THEN** `reports/generation-summary.json` SHALL be updated with a `testResults` object containing: total tests, passing, failing, and a list of failing test names

#### Scenario: Test failures are non-blocking
- **WHEN** some Vitest tests fail during the Release Crew run
- **THEN** the pipeline SHALL still write all output artifacts to the output folder
- **AND** SHALL mark the generation summary with `hasTestFailures: true`

### Requirement: Pipeline completeness check
The Pipeline Completeness Agent (Agent 34) SHALL verify that all expected output artifacts are present and non-empty before the Release Crew finalizes the generation summary. If any required file from the PRD output structure is missing, the agent SHALL flag it in the generation summary rather than silently omitting it.

#### Scenario: Missing required file flagged
- **WHEN** the Pipeline Completeness Agent checks the output folder
- **AND** `docs/README.md` is missing
- **THEN** `reports/generation-summary.json` SHALL include a `missingArtifacts` list entry for `docs/README.md`
- **AND** the generation run SHALL not be marked as fully complete

#### Scenario: All artifacts present — run marked complete
- **WHEN** all required output files are present and non-empty
- **THEN** `reports/generation-summary.json` SHALL include `"isComplete": true`
- **AND** the CLI SHALL print a success message with the output folder path

### Requirement: Full build validation sequence
The Publish Agent (Agent 37) SHALL run the complete build and test validation sequence before finalizing the generation summary. The sequence SHALL be, in order:
1. `npm install` — install all production and dev dependencies from the generated `package.json`
2. `npm run build` — execute the Vite library build to produce the compiled distribution output in `dist/`
3. `npm test` — run Vitest against all test files; capture pass/fail results

All three steps MUST succeed for the pipeline to mark the generation run as `isComplete: true`. A failure at `npm install` or `npm run build` SHALL be treated as a **fatal build failure** and SHALL set `hasBuildFailure: true` in the generation summary. A failure at `npm test` is non-blocking (sets `hasTestFailures: true`) but does not prevent artifact output. The generated `dist/` output SHALL be included in the `files` list in `package.json`.

#### Scenario: npm install + build + test all pass
- **WHEN** the Publish Agent runs the full validation sequence and all three steps pass
- **THEN** `reports/generation-summary.json` SHALL include `"isComplete": true`, `"hasBuildFailure": false`, `"hasTestFailures": false`
- **AND** the `dist/` directory SHALL exist in the output folder

#### Scenario: Build failure is fatal
- **WHEN** `npm run build` exits with a non-zero error code
- **THEN** `reports/generation-summary.json` SHALL set `"hasBuildFailure": true` and `"isComplete": false`
- **AND** the CLI SHALL print the build error output before presenting the output review

#### Scenario: Test failures non-blocking
- **WHEN** `npm test` reports failing tests after a successful `npm install` and `npm run build`
- **THEN** `reports/generation-summary.json` SHALL set `"hasTestFailures": true` and `"isComplete": true`
- **AND** the failing test names SHALL be included in the `testResults.failing` list

### Requirement: Codemod Agent
The Codemod Agent (Agent 38, Tier 1) SHALL generate adoption codemod scripts that help teams migrate from raw HTML/CSS to the generated design system. The Codemod Agent's output serves both as a practical immediate-use migration tool and as a versioned migration template for future version-to-version codemods. All codemod scripts SHALL be written to `docs/migration/`.

Required outputs:
- `docs/migration/adoption-codemod.ts` — a jscodeshift-compatible codemod that transforms raw HTML elements to design system components: `<button>` → `<Button>`, `<input>` → `<Input>`, `<a>` → `<Link>`, `<div>` (wrapper patterns) → `<Box>` or `<Stack>`
- `docs/migration/token-codemod.ts` — a codemod that replaces hardcoded CSS values with design system token CSS custom properties: `color: #333` → `color: var(--color-text-primary)`, `padding: 16px` → `padding: var(--spacing-4)`
- `docs/migration/MIGRATION.md` — human-readable migration guide explaining how to run the codemods, what they transform, and what they do NOT transform (manual migration items)

The generated codemods SHALL be parameterized by the actual component and token names from this generation run — not generic templates.

#### Scenario: Button codemod transforms raw HTML
- **WHEN** `docs/migration/adoption-codemod.ts` is generated and the design system includes a `Button` component
- **THEN** the codemod SHALL contain a transform that replaces `<button>` elements with `<Button>` from the generated package
- **AND** the import path in the transform SHALL reference the actual package name from `package.json`

#### Scenario: Token codemod covers all semantic tokens
- **WHEN** `docs/migration/token-codemod.ts` is generated
- **THEN** the codemod SHALL include mappings for all color semantic tokens (e.g., all entries from `--color-*` CSS custom properties)
- **AND** SHALL NOT include mappings for global tier tokens (consumers should not use global tokens directly)

#### Scenario: Migration guide lists manual items
- **WHEN** `docs/migration/MIGRATION.md` is generated
- **THEN** it SHALL contain a section "What the codemods do NOT handle" listing transformation patterns that require manual review (e.g., components with complex prop mappings, custom animation styles)

### Requirement: Rollback Agent cross-cutting organizational note
The Rollback Agent (Agent 40) is listed under the Release Crew in the agent census but is a cross-cutting pipeline utility. It is instantiated by the First Publish Agent (Agent 6) at pipeline start — before Phase 1 begins — and persists across all phases. The Rollback Agent does NOT run as a Release Crew sequential step; it is always available for rollback operations throughout the entire pipeline lifecycle. The first checkpoint it writes is before Phase 1 begins (pre-generation baseline). Its placement in the Release Crew section of the codebase is for organizational grouping only.

#### Scenario: Rollback Agent ready before Phase 1
- **WHEN** the pipeline starts (before Phase 1)
- **THEN** the First Publish Agent SHALL instantiate the Rollback Agent
- **AND** the Rollback Agent SHALL write the initial baseline checkpoint before any generation begins

#### Scenario: Rollback Agent callable from any phase
- **WHEN** the Token Engine Crew detects an unrecoverable error in Phase 2
- **THEN** the First Publish Agent SHALL call the Rollback Agent to restore the pre-Phase-2 checkpoint
- **AND** the Rollback Agent SHALL be available immediately (it was instantiated at pipeline start, not at Release Crew start)
