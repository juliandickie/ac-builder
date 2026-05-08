# list-campaigns

Lists campaigns in the configured AC account. Server-side filtering by name substring and campaign type, client-side cap via `--limit`.

## Invocation

```bash
uv run --directory ${CLAUDE_PLUGIN_ROOT}/scripts/python ac-builder list-campaigns [--name TEXT] [--type TYPE] [--limit N]
```

## Flags

| Flag | Type | Default | Notes |
|---|---|---|---|
| `--name` | string | (none) | Substring match against the campaign name. Server-side filter (`filters[name]=...`). Case-insensitive. |
| `--type` | string | (none) | Campaign type filter. Common values: `single`, `recurring`, `text`, `responder`, `reminder`, `split`, `auto`, `activerss`, `date`. Server-side (`filters[type]=...`). |
| `--limit` | int | 50 | Number of rows to print after pagination. Set to a large value (e.g. `9999`) to see everything. |

## Output format

Two-column plain text, right-aligned ID followed by the campaign name:

```
       1  Welcome to Intro to CADCAM
       2  Opt In Email
       4  Delivery
       5  Gain
       6  Logic
```

When filtered by name:

```
    3427  E11 - Mid-Cart Bonus Reveal (ASIMR) + Case Study #2 (Nidhi)
    3462  LPIS-OB-2 - ASIMR Access Walkthrough + Pre-Course Reading (Day 3)
    3465  ASIMR-OB-1 - Welcome + First Module Prompt (Day 0)
    3466  ASIMR-OB-2 - First Mentoring Call Preview (Day 10)
    3467  ASIMR-OB-3 - Month 3 Check-In (Day 90)
```

## Common patterns

### Find a campaign by partial name

```bash
uv run --directory ${CLAUDE_PLUGIN_ROOT}/scripts/python ac-builder list-campaigns --name "ASIMR-OB-1"
```

### List all single-send campaigns

```bash
uv run --directory ${CLAUDE_PLUGIN_ROOT}/scripts/python ac-builder list-campaigns --type single --limit 200
```

### Audit launch-sequence builds

```bash
uv run --directory ${CLAUDE_PLUGIN_ROOT}/scripts/python ac-builder list-campaigns --name "AUNZ" --limit 50
```

### Count total campaigns in account

```bash
uv run --directory ${CLAUDE_PLUGIN_ROOT}/scripts/python ac-builder list-campaigns --limit 9999 | wc -l
```

## Limitations

- The `--limit` flag caps printed rows, but pagination through AC continues internally for the matched filter set. On a large account, raising `--limit` increases AC API calls.
- Multi-filter logic uses AND. There is no OR or NOT support.
- No date range filter at the CLI level. To filter by date, fetch via `get-campaign` and inspect `cdate` / `sdate` / `ldate`.
- No `--json` output. For machine-readable results, parse the two-column output with `awk '{print $1}'` to extract IDs.

## Underlying API

Hits `GET /api/3/campaigns?filters[name]=...&filters[type]=...` with `limit=100&offset=...` walking pages. Documented in `ac_builder.api.campaigns_v3.list_campaigns`.

## See also

- `references/get-campaign.md` - to inspect a single campaign in full
- `references/pagination.md` - for how the CLI walks AC's pagination
