## Why

Design systems require months of manual work — translating brand intent into tokens, generating components, enforcing accessibility, writing documentation, and wiring governance — with every step error-prone and dependent on the weakest manual link. DAF Local eliminates this by running an AI-orchestrated generation pipeline that turns a brand interview into a complete, validated, testable design system package on disk.

## What Changes

- **New**: CLI that interviews the user about brand identity, colors, typography, spacing, component scope, and accessibility requirements
- **New**: 9-phase sequential pipeline with 45 specialized agents across 9 CrewAI crews that generate all design system artifacts
- **New**: W3C DTCG three-tier token architecture (global → semantic → component-scoped), compiled to CSS/SCSS/TS/JSON per theme
- **New**: Canonical spec YAML format (`*.spec.yaml`) as the source-of-truth for component generation
- **New**: TSX components, tests, and Storybook stories generated from spec files
- **New**: Accessibility enforcement (axe-core) with in-place patching and post-patch re-validation
- **New**: Full documentation suite (README, token catalog, component docs, ADRs, changelog, RFC templates, search index)
- **New**: Governance artifacts (ownership map, quality gates, deprecation policy, contribution workflow)
- **New**: AI semantic registry (component registry, token graph, composition rules, compliance rules, AI context files)
- **New**: Quality analytics (quality scorecard, a11y audit, token compliance, drift report, composition audit)
- **New**: Release assembly (package.json, barrel exports, changelog, test execution)
- **New**: Retry protocol (up to 3 attempts per component per validation stage) with checkpoint/resume support
- **New**: Multi-theme and multi-brand token architecture via ThemeProvider primitive and CSS class scoping

## Capabilities

### New Capabilities

- `cli`: Command-line interface (`daf init`) — brand interview conversation with session persistence (`.daf-session.json`), `--resume` flag, `--profile <path>` flag (skip interview with pre-written brand profile), `--from-phase N` re-entry, `--retry-components` targeted retry, output folder management, model tier configuration via environment variables
- `pipeline-orchestration`: Multi-phase pipeline coordination — phase-sequential execution, First Publish Agent retry routing, checkpoint/restore via Rollback Agent, resume-on-failure, rollback cascade policy
- `ds-bootstrap-crew`: Phase 1 — DS Bootstrap Crew: brand discovery, raw three-tier token file generation, canonical spec YAML authoring, project scaffolding (tsconfig, vite, vitest, pipeline-config.json)
- `token-engine-crew`: Phase 2 — Token Engine Crew: token schema validation, naming enforcement, contrast checking, multi-theme and multi-brand compilation (CSS/SCSS/TS/JSON), diff generation
- `component-generation`: Phase 3 — Design-to-Code Crew and Component Factory Crew: TSX/test/story generation from spec YAMLs, render validation, TypeScript compilation, a11y patching, quality scoring
- `documentation-governance`: Phase 4 — Documentation Crew and Governance Crew: doc page generation, ADRs, generation narrative, search index, ownership map, quality gate config, deprecation policy, test scaffolding
- `ai-analytics`: Phase 5 — AI Semantic Layer Crew and Analytics Crew: component registry, token graph, composition rules, compliance rules, AI context files, quality scorecard, drift detection, token compliance scan
- `release-crew`: Phase 6 — Release Crew: package.json assembly, barrel exports, changelog generation, semantic versioning, test execution, final generation summary

### Modified Capabilities

## Impact

- No prior codebase — this is a greenfield implementation of the full DAF Local framework
- External dependencies: CrewAI (multi-agent orchestration), Anthropic API (Claude models — Opus/Sonnet/Haiku per tier), Style Dictionary or equivalent (token compilation), axe-core (a11y auditing), Vitest (test runner), Vite (build), TypeScript, React, Storybook
- Output is a self-contained folder on disk installable as a package — no runtime server, no cloud deployment, no external state
