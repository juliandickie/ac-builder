---
name: inspecting-ac-state
description: Use when the user wants to look up state in ActiveCampaign without modifying it. Lists or fetches campaigns, tags, automations, and addresses, and explains how to inspect custom fields. Read-only and safe. Useful for finding IDs to pass to other skills, debugging discrepancies between MD source and AC reality, or auditing what is in the account.
allowed-tools: Bash
argument-hint: "<entity> [--name ...] [--search ...] [--type ...] [--limit <n>] [<id>]"
---

# Inspecting AC state

Read-only inspection of ActiveCampaign data via the ac-builder CLI. Wraps `list-campaigns`, `list-tags`, `list-automations`, `list-addresses`, and `get-campaign`. No writes, no deletions, safe to run repeatedly.

## When to use

- **Find an ID to pass to another skill.** For example, looking up the tag ID for `INTEREST: LPIS 2026 - Engaged` before configuring a link-action automation, or grabbing an `addressid` for a campaign send.
- **Debug discrepancies.** A `build-sequence` run shows campaign 3465 in AC but your source MD references "ASIMR-OB-1" - confirm the live state matches what you expect.
- **Audit the account.** Listing all `LAUNCH:` automations or all `LPIS` tags before a launch to confirm nothing is stale or missing.
- **Reality-check before mutations.** Before deleting a campaign or modifying an automation, fetch it once to record what was there.

All commands here are read-only. None of them call AC mutating endpoints. If a write is needed, use the appropriate sequence-building or capture skill instead.

## Quick reference

Each command runs against the AC account configured in `~/.config/ac-builder/config.env` (set up via `verifying-setup`).

| Entity | Command | Reference |
|---|---|---|
| Campaigns (list) | `list-campaigns` | `references/list-campaigns.md` |
| Campaigns (single) | `get-campaign <id>` | `references/get-campaign.md` |
| Tags | `list-tags` | `references/list-tags.md` |
| Custom fields | (no CLI subcommand) | `references/list-custom-fields.md` |
| Automations | `list-automations` | `references/list-automations.md` |
| Addresses (sender) | `list-addresses` | (no separate ref - simple one-shot) |

For pagination semantics across all list commands, see `references/pagination.md`.

## Per-entity workflows

### Campaigns

List with optional filters by name substring or campaign type:

```bash
uv run --directory ${CLAUDE_PLUGIN_ROOT}/scripts/python ac-builder list-campaigns --name "ASIMR" --limit 20
```

Output is two columns: `<id>  <name>`, e.g. `3465  ASIMR-OB-1 - Welcome + First Module Prompt (Day 0)`.

Get full campaign JSON for a specific ID:

```bash
uv run --directory ${CLAUDE_PLUGIN_ROOT}/scripts/python ac-builder get-campaign 3465
```

Returns the full `{"campaign": {...}, ...}` envelope including `message_id`, `addressid`, send statistics, and links. See `references/get-campaign.md` for field interpretation.

### Tags

List with optional substring search (server-side filter on tag name):

```bash
uv run --directory ${CLAUDE_PLUGIN_ROOT}/scripts/python ac-builder list-tags --search "LPIS"
```

Output is `<id>  <tag-name>`. There is no `--limit` flag; tags are paginated transparently and printed all at once. See `references/list-tags.md`.

### Custom fields

There is no `list-custom-fields` (or `list-fields`) subcommand in the v0.5 CLI. To inspect custom fields, hit the `/fields` endpoint directly via the underlying Python client. Workaround pattern documented in `references/list-custom-fields.md`. (Custom field IDs that ac-builder uses are also listed in the project CLAUDE.md - LPIS_PURCHASE_DATE 293, ASIMR_PURCHASE_DATE 294, IIDF_PURCHASE_DATE 295, LPIS_COHORT 296.)

### Automations

List every automation in the account:

```bash
uv run --directory ${CLAUDE_PLUGIN_ROOT}/scripts/python ac-builder list-automations
```

Output is `<id>  <name>  status=<n>` where status `1` is active and `2` is inactive/draft. There is no `--limit` flag - the full set is printed. See `references/list-automations.md`.

To inspect the actions and triggers of a single automation, use the separate `capturing-automations` skill, which writes a structured JSON fixture.

### Addresses

List sender physical addresses (used as `addressid` on campaigns):

```bash
uv run --directory ${CLAUDE_PLUGIN_ROOT}/scripts/python ac-builder list-addresses
```

Output is `<id>  <company> - <address_1>, <city>`. No flags. Addresses are typically a small set per account.

## Pagination

All list commands hit AC paginated endpoints. The CLI handles pagination internally - it fetches up to 100 rows per page and walks forward until the API returns a partial or empty page. The only user-facing limit is the `--limit` flag on `list-campaigns`, which caps the printed rows after pagination.

For details and how to widen the cap, see `references/pagination.md`.

## Output formats

All commands print plain text - two-column tables for list commands, JSON for `get-campaign`. There is no `--json` flag on the list commands; if you need structured output, pipe through `awk` or use the underlying Python `ACClient` directly. The verify skill (`verifying-setup`) shows how to call `client.paginate(...)` from Python.

## Common gotchas

- The `--name` filter on `list-campaigns` is server-side - AC matches as a substring against the campaign name. Filtering by exact ID works only via `get-campaign <id>`.
- `list-tags --search` is server-side too. Search is case-insensitive but only matches the tag name, not internal AC metadata.
- `list-automations` has no filter flags. Combine with `grep` for client-side filtering: `... ac-builder list-automations | grep "LAUNCH:"`.
- The default `--limit 50` on `list-campaigns` is a *display* cap, not an API cap. To see everything, use a high number like `--limit 9999`.
