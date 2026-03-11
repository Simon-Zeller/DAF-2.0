## ADDED Requirements

### Requirement: CLI invocation and command structure
The CLI executable SHALL be named `daf` with the subcommand `init` as the primary entry point. The following invocation modes SHALL be supported:

- `daf init <output-path>` — interactive mode: run the full brand interview, then start the pipeline
- `daf init <output-path> --profile <path-to-json>` — file mode: skip the interview and pass the provided `brand-profile.json` directly to the Brand Discovery Agent for validation and enrichment
- `daf init <output-path> --resume` — resume mode: locate the most recent valid checkpoint in the output folder and resume the pipeline
- `daf init <output-path> --from-phase N` — re-entry mode: re-run the pipeline from Phase N onward
- `daf init <output-path> --retry-components Name1,Name2,...` — targeted retry mode: re-run Phase 3 for named components only, then Phase 4–6

#### Scenario: File mode skips interview
- **WHEN** the user runs `daf init ./my-ds --profile ./my-brand-profile.json`
- **THEN** the CLI SHALL skip the brand interview entirely
- **AND** SHALL pass the provided file directly to the Brand Discovery Agent for validation and enrichment
- **AND** the Brand Discovery Agent SHALL still validate and enrich the file — file mode skips only the interview, not validation

#### Scenario: File mode with invalid JSON
- **WHEN** the user provides a `--profile` path that does not exist or contains invalid JSON
- **THEN** the CLI SHALL report the error and exit with a non-zero status code
- **AND** SHALL NOT start the pipeline

### Requirement: Brand interview conversation
The CLI SHALL conduct a structured, conversational brand interview that collects all inputs required to generate a design system. The interview SHALL cover brand identity, primary and secondary colors, typography (font families, scale), spacing scale, component scope, accessibility requirements, theming model (light/dark/high-contrast), and multi-brand configuration. The interview output SHALL produce a validated `brand-profile.json` file in the output folder. The CLI SHALL use plain prose prompts — no form UI, no GUI.

#### Scenario: Full interview completion
- **WHEN** the user runs the CLI without `--resume`
- **THEN** the CLI presents brand interview questions sequentially
- **AND** collects answers for all required fields (brand identity, colors, typography, spacing, component scope, accessibility requirements)
- **AND** writes a validated `brand-profile.json` to the output folder before starting Phase 1

#### Scenario: User provides ambiguous color input
- **WHEN** the user enters a color value that cannot be parsed as a valid hex, RGB, or HSL color
- **THEN** the CLI SHALL re-prompt with a clarifying question and an example of valid input
- **AND** SHALL NOT proceed to the next question until a valid color is entered

#### Scenario: Multi-brand configuration
- **WHEN** the user specifies more than one brand during the interview
- **THEN** the CLI SHALL prompt for per-brand color and identity overrides
- **AND** SHALL record all brand identifiers in `brand-profile.json` under `themes.brands`

### Requirement: Output folder targeting
The CLI SHALL accept an output directory path as a required argument. If the directory does not exist, the CLI SHALL create it. If the directory already contains a partial pipeline run, the CLI SHALL warn the user and require confirmation (or `--force`) before overwriting.

#### Scenario: New output directory
- **WHEN** the user specifies an output path that does not exist
- **THEN** the CLI SHALL create the directory (including parent directories) before starting the pipeline

#### Scenario: Existing non-empty directory without --resume
- **WHEN** the user specifies an output path that already contains files and does not pass `--resume` or `--force`
- **THEN** the CLI SHALL display a warning listing the conflicting path
- **AND** SHALL ask the user to confirm overwrite, exit, or use `--resume`

### Requirement: Resume mode
The CLI SHALL support a `--resume` flag. When provided, the CLI SHALL locate the most recent valid checkpoint in the output folder, validate its integrity (all expected files present and non-corrupt), and restart the pipeline from the next phase after the last successful checkpoint. The CLI SHALL NOT retry the failed phase automatically — it SHALL re-run the failed phase from scratch.

#### Scenario: Valid checkpoint found
- **WHEN** the user runs the CLI with `--resume` pointing to an output folder
- **AND** a valid checkpoint exists for at least one completed phase
- **THEN** the CLI SHALL print the last successful phase name and the next phase to run
- **AND** SHALL re-run from the next phase without re-running previously completed phases

#### Scenario: Corrupt or incomplete checkpoint
- **WHEN** the user runs the CLI with `--resume`
- **AND** the checkpoint is corrupt or missing expected files
- **THEN** the CLI SHALL report the integrity failure with a list of missing or invalid files
- **AND** SHALL ask the user whether to restart from Phase 1 or exit

#### Scenario: No checkpoint found
- **WHEN** the user runs the CLI with `--resume`
- **AND** no checkpoint files exist in the output folder
- **THEN** the CLI SHALL notify the user that no checkpoint was found
- **AND** SHALL exit without starting the pipeline

### Requirement: Model tier configuration
The CLI SHALL respect model tier configuration provided via environment variables. `DAF_TIER1_MODEL` configures Tier 1 (generative agents), `DAF_TIER2_MODEL` configures Tier 2 (analytical agents), `DAF_TIER3_MODEL` configures Tier 3 (classification agents). If an environment variable is not set, the CLI SHALL use the documented defaults: `claude-sonnet-4-20250514` for Tiers 1 and 2, `claude-haiku-4-20250414` for Tier 3.

#### Scenario: Custom tier 1 model set
- **WHEN** `DAF_TIER1_MODEL=claude-opus-4-20250514` is set in the environment
- **THEN** all Tier 1 agents SHALL use `claude-opus-4-20250514` for LLM calls
- **AND** Tier 2 and Tier 3 agents SHALL use their own tier's configured or default model

#### Scenario: No environment variables set
- **WHEN** no `DAF_TIER*_MODEL` environment variables are set
- **THEN** Tiers 1 and 2 SHALL use `claude-sonnet-4-20250514`
- **AND** Tier 3 SHALL use `claude-haiku-4-20250414`

### Requirement: Pipeline progress reporting
The CLI SHALL display real-time progress during pipeline execution. Progress output SHALL include the current phase name, current crew name, current agent name, and a summary of completion status (e.g., "Phase 2 / Token Engine Crew — validating 24 tokens"). Failed components SHALL be reported inline as they occur without halting the progress display.

#### Scenario: Phase transition
- **WHEN** a crew completes and the pipeline advances to the next phase
- **THEN** the CLI SHALL print a phase completion summary including the crew name, artifacts written, and any warnings or failures

#### Scenario: Component retry
- **WHEN** a component fails validation and enters the retry loop
- **THEN** the CLI SHALL indicate the retry attempt number (e.g., "Button — retry 2/3") inline in the progress output

### Requirement: Output review re-entry flags
The CLI SHALL support two re-entry flags that are activated from the Output Review gate:

**`--from-phase N`** (where N is 1–6): Re-run the pipeline from Phase N onward using the existing checkpoint and output folder. The Rollback Agent SHALL restore the checkpoint from the end of Phase N-1 before re-running. Phase 1 re-run is a full restart. This flag SHALL NOT be used for the initial pipeline run.

**`--retry-components Name1,Name2,...`**: Re-run Phase 3 (Design-to-Code + Component Factory) exclusively for the named components. Token generation, documentation, governance, AI semantic layer, and analytics are NOT re-run. After the targeted component retry completes, Phase 4–6 SHALL re-run from the checkpoint before Phase 4 to refresh documentation and governance artifacts for the updated components.

Both flags SHALL be accepted as CLI arguments AND as interactive choices in the Output Review gate. When provided as CLI arguments directly (not from the interactive gate), the CLI SHALL warn if no valid checkpoint is found for the requested re-entry point.

#### Scenario: --from-phase 3 re-entry
- **WHEN** the user runs the CLI with `--from-phase 3` against an existing output folder with a Phase 2 checkpoint
- **THEN** the Rollback Agent SHALL restore the Phase 2 checkpoint
- **AND** the pipeline SHALL execute Phase 3 → Phase 4 → Phase 5 → Phase 6 in sequence

#### Scenario: --retry-components targets specific components
- **WHEN** the user runs with `--retry-components Button,Modal`
- **THEN** the pipeline SHALL generate only `Button` and `Modal` in Phase 3
- **AND** SHALL then re-run Phase 4–6 to update documentation and governance artifacts
- **AND** SHALL NOT regenerate tokens, primitives, or other components

#### Scenario: Flag used without valid checkpoint
- **WHEN** the user runs with `--from-phase 4` but no Phase 3 checkpoint exists in the output folder
- **THEN** the CLI SHALL report the missing checkpoint
- **AND** SHALL ask whether to run from Phase 1 instead (full restart)

### Requirement: Human Gate — Brand Profile Approval
After conducting the brand interview and before Phase 1 begins, the CLI SHALL display a formatted summary of the `brand-profile.json` and require explicit user approval. This gate prevents wasting pipeline time on incorrect brand inputs.

The summary SHALL show: brand name, archetype, component scope tier, color palette preview (color names and hex values), typography choices, accessibility level, theme modes, and multi-brand configuration.

The user SHALL have three choices:
1. **Approve** — proceed to Phase 1 immediately
2. **Re-run interview** — restart the brand interview from the beginning
3. **Provide file** — exit the interview and provide a hand-written `brand-profile.json` at the output folder path (the pipeline will validate and start Phase 1 on next run)

#### Scenario: Summary displayed before Phase 1
- **WHEN** the brand interview completes
- **THEN** the CLI SHALL display the brand profile summary and wait for explicit approval before starting Phase 1
- **AND** SHALL NOT begin Phase 1 automatically

#### Scenario: Re-run interview selected
- **WHEN** the user selects "Re-run interview" at the brand profile approval gate
- **THEN** the CLI SHALL restart the brand interview from the beginning
- **AND** SHALL overwrite the previously generated `brand-profile.json` only after the new interview is complete and approved

#### Scenario: Hand-written brand profile detected and bypasses interview
- **WHEN** a `brand-profile.json` already exists in the output folder when the CLI starts
- **THEN** the CLI SHALL skip the interview, display the file contents as the brand profile summary, and present the approval gate directly
- **AND** SHALL validate the file schema before displaying (fail-fast with field errors if invalid)

### Requirement: Interview session persistence
The CLI SHALL write a `.daf-session.json` file to the output directory after each completed interview step. This enables resumption of interrupted interviews without losing already-collected answers.

#### Scenario: Interview interrupted and resumed
- **WHEN** the user interrupts the interview (Ctrl+C, terminal close) after completing step 5 of 11
- **AND** re-runs `daf init` targeting the same output directory
- **THEN** the CLI SHALL detect `.daf-session.json` in the output directory
- **AND** SHALL offer to resume from step 6 (the last incomplete step)
- **AND** SHALL preserve all answers from steps 1–5 as previously recorded

#### Scenario: Session file deleted after interview completion
- **WHEN** the brand interview completes successfully and the raw `brand-profile.json` is written
- **THEN** the CLI SHALL delete `.daf-session.json` from the output directory
- **AND** the session file SHALL NOT remain as a pipeline artifact

#### Scenario: User declines to resume interrupted session
- **WHEN** the CLI detects a `.daf-session.json` and the user declines to resume
- **THEN** the CLI SHALL delete the session file and restart the interview from the beginning
