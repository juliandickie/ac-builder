# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.6.2] - 2026-08-22

### Fixed

- Dark mode now actually works. The dark-mode CSS was declared (color-scheme metas, prefers-color-scheme media query, data-ogsc hooks) but non-functional - the rules targeted `.body-bg`/`.card-bg`/`.text-dark` classes that almost nothing carried, and the `.text-dark` colour rule on a td could never override the inline colour MJML places on the child div. Dark-mode clients showed a dark rim around an unchanged white card; partially-inverting clients (Gmail iOS, Outlook mobile) produced black-on-black bodies, reported by customers on the August 2026 iDD celebration broadcasts. `head.mjml` dark rules now target descendants (`.text-dark div/p/span/li/ul/ol`), backgrounds cover the section and its inner table, a `body` rule covers the canvas below the card, and Outlook gets `[data-ogsb]` background rules alongside `[data-ogsc]` text rules. `mj-attributes` defaults attach `card-bg` to every section and `text-dark` to every text block, so coverage is automatic. Templates version 1.0.0 to 1.1.0.
- Button labels with apostrophes no longer ship a literal `&#x27;`. The `[[button:]]` sentinel path delivers pre-escaped text to `_emit_button`, which escaped it again; the V1 create path masked the double-escape by decoding one entity level on store, but the V3 update path does not. `_emit_button` now unescapes before escaping both label and href, making escaping idempotent.

### Changed

- Deliberate dark-mode exemptions in the generator: brand strip sections and their white text (`strip-keep`/`text-keep`), coloured h2/h3/h4 headings (`text-keep`), footer muted text (`text-keep`, muted grey reads on both schemes), and callout boxes get their own `callout-bg` dark treatment.

## [0.6.1] - 2026-07-19

### Added

- `docs/api-capability-map.md` - empirical audit of the AC V3 API surface (19 July 2026): full canvas readable via `GET /automations/{id}/blocks` under the `automationBlocks` key (send blocks expose `sendtype` imm/opt, goal blocks expose position/unmet, goal conditions live in hidden unnamed segments - never bulk-delete unnamed segments); campaign drafts accept PUT on `name`, `sdate`, `tracklinks`, `embed_images`, `analytics_campaign_name`; segments and webhooks are POST-creatable (segments with NO validation - an empty body creates a blank segment, so never method-probe that endpoint with empty POSTs); automations/campaigns/goals remain POST 405; automationBlocks PUT/POST routes exist but valid-payload writes are unproven.

### Changed

- `wiring-automations` - corrected the 0.6.0 claim that canvas blocks are not API-readable; verification guidance now uses the one-read `automationBlocks` check for send modes, waits, and goal settings instead of reopening panels.

## [0.6.0] - 2026-07-19

### Added

- New `wiring-automations` skill - the field-tested recipe for driving AC automation canvases through the browser (flows cannot be created via the public API). Covers the copy-once dedup rule ("Start from an existing email" once, then "Select an email in this automation"), the password-manager tab-steal prevention and recovery pattern (never focus text inputs; DOM query + native setter), stale-coordinate discipline (re-screenshot before every + click), the Jump To goal-island pattern for the current builder (no explicit End action - each goal's not-met "End this automation" supplies the ends), node recipes for triggers, waits, tag actions, and exact-date If/Else cohorts, and send-mode conventions (first email Immediately, rest Predictive Send, final-day urgency emails Immediately). Learned on the iDD ASDE launch builds, automations 2964 and 2965, July 2026.
- Documented three proven API write paths for the post-wiring settings pass in `wiring-automations/references/copy-settings-api.md`: `PUT /api/3/messages/{id}` (fromname/fromemail/reply2), `PUT /api/3/campaigns/{id}` (`analytics_campaign_name` - automation copies drop it and the UI auto-fills per-email names that fragment GA), and `PUT /api/3/automations/{id}` (`name` - avoids the tab-steal-prone builder name editor). All verified by re-GET.

### Changed

- `building-sequences` skill - documented `--footer-mode onboarding` for post-purchase sequences (no `/not-interested/` opt-out requirement) and added a handoff section pointing at `wiring-automations` for the automation-copy settings pass.

## [0.5.1] - 2026-05-24

### Fixed

- Guard against silent truncation of launch email bodies. An in-body `### ` heading terminated markdown body extraction, dropping content (and the closing `/not-interested/` opt-out link) from the rendered email with no error. Pre-send validation now raises an ERROR when a launch-mode email's rendered body is missing its `/not-interested/` opt-out link (always the final element of a launch body, so its absence is a strong truncation signal), and the parser emits a WARNING when a non-section `### ` heading appears before that link (where it would drop real content). Post-link authoring notes such as `### CTA` and `### Technique Notes` are unaffected.

## [0.5.0] - 2026-05-08

### Added

- First public release of ac-builder as a standalone Claude Code plugin.
- Seven gerund-named skills covering setup, building, inspecting, editing, cleanup, link-action capture, and theme creation.
- Bundled Python tool in `scripts/python/`, invoked via `uv run` from inside skills.
- Layered credential resolution: process env > `./ac-builder.env` > `~/.config/ac-builder/config.env`.
- Layered theme resolution: explicit path > project `./themes/` > user `~/.config/ac-builder/themes/` > plugin `themes/examples/`.
- Seven example themes: 4 generic starters (corporate-blue, friendly-startup, bold-startup, minimal-mono) + 3 iDD examples (lpis, iidf, asimr).
- `ac-builder verify --themes-only` flag for CI use.
- GitHub Actions CI: ruff, pytest, MJML compile smoke, skill metadata lint.

### Predecessor work (not part of v0.5.0 changelog but for context)

- v0.1.0 (Apr 27, 2026): in-project plugin scaffold at `tools/ac-builder/plugin/` with 16 CLI-passthrough skills.
- v0.4.0 (Apr 28, 2026): Phase 4 MJML pipeline replaced Phase 1-3 V3 master-and-edit. Added themes/ JSON config, V1 API support, link-action templates.
