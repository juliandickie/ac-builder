# list-tags

Lists tags in the configured AC account. Optional server-side substring search.

## Invocation

```bash
uv run --directory ${CLAUDE_PLUGIN_ROOT}/scripts/python ac-builder list-tags [--search TEXT]
```

## Flags

| Flag | Type | Default | Notes |
|---|---|---|---|
| `--search` | string | (none) | Substring match against the tag name. Sent as `?search=...`. Case-insensitive. |

There is no `--limit` flag. The CLI paginates fully and prints every matching tag.

## Output format

Two-column plain text, right-aligned ID followed by the tag name:

```
     977  LPIS: Engaged Lead
    1254  WAITLIST: LPIS 2025
    1286  REGISTERED: LPIS Course
    1547  NOT INTERESTED: LPIS 2025
    1598  WAITLIST: LPIS 2026
    2384  REGISTERED: LPIS 2026
    2447  INTEREST: LPIS 2026 - Engaged
    2448  INTEREST: LPIS 2026 - Ready
    2459  NOT INTERESTED: LPIS 2026 - October
    2461  ACR: LPIS - Wellington - 2026-06-19
```

## Common patterns

### Look up the ID for a specific iDD tag

```bash
uv run --directory ${CLAUDE_PLUGIN_ROOT}/scripts/python ac-builder list-tags --search "INTEREST: LPIS 2026 - Engaged"
```

### Audit all tags in a category

```bash
uv run --directory ${CLAUDE_PLUGIN_ROOT}/scripts/python ac-builder list-tags --search "PURCHASE:"
```

### List every tag in the account

```bash
uv run --directory ${CLAUDE_PLUGIN_ROOT}/scripts/python ac-builder list-tags
```

(Be aware: on a large account this may print thousands of rows.)

### Find the next free tag ID for a pattern

```bash
uv run --directory ${CLAUDE_PLUGIN_ROOT}/scripts/python ac-builder list-tags --search "INTEREST:" | awk '{print $1}' | sort -n | tail
```

## Limitations

- The search is a single substring, no regex, no OR.
- No `--json` output. Pipe through `awk` for IDs.
- Tag descriptions are not shown - only the tag name. To see descriptions, hit `/api/3/tags/<id>` directly via the Python client.
- There is no client-side `--limit` cap, so a wide search may print a long list. Combine with `head` if you only need a few results.

## Underlying API

Hits `GET /api/3/tags?search=...` with `limit=100&offset=...` walking pages. Implemented inline in `cli.py` via `client.paginate("tags", "tags", params={"search": ...})`.

## See also

- `references/list-custom-fields.md` - for inspecting custom fields (note: no CLI subcommand)
- `references/pagination.md`
- iDD tag schema: `plans/activecampaign/ActiveCampaign_Automation_Specs.md` Section 2 (in the project repo, not this plugin)
