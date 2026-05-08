# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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
