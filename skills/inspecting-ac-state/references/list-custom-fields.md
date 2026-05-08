# list-custom-fields (no CLI subcommand in v0.5)

**Status: not implemented as a CLI subcommand.** The v0.5 ac-builder CLI has no `list-custom-fields`, `list-fields`, or equivalent. Custom field inspection requires a workaround.

The plan that drove this skill assumed a `list-custom-fields` subcommand existed; it does not. This page documents both the gap and the workaround.

## Verifying the gap

```bash
uv run --directory ${CLAUDE_PLUGIN_ROOT}/scripts/python ac-builder --help
```

Subcommands listed:

```
{render,check,build-sequence,capture-automation,list-builds,send-test,verify,
 list-campaigns,get-campaign,delete-campaign,list-tags,list-automations,list-addresses}
```

No `list-custom-fields` or `list-fields`. Confirmed against `scripts/python/ac_builder/cli.py` - only the 12 subcommands above register parsers.

## Workaround 1: known field IDs from the project CLAUDE.md

The iDD launch project records its custom field IDs in the project root `CLAUDE.md`:

| Field perstag (used as merge field) | AC ID |
|---|---|
| `LPIS_PURCHASE_DATE` | 293 |
| `ASIMR_PURCHASE_DATE` | 294 |
| `IIDF_PURCHASE_DATE` | 295 |
| `LPIS_COHORT` | 296 (options: 6=June 2026, 7=October 2026) |

If you only need an ID for a known field, prefer this lookup.

## Workaround 2: hit `/fields` directly via Python

Open a shell into the ac-builder Python environment and call the v3 client:

```bash
cd ${CLAUDE_PLUGIN_ROOT}/scripts/python
uv run python -c "
from ac_builder.api.v3_client import ACClient
client = ACClient()
for f in client.paginate('fields', 'fields'):
    print(f\"{f['id']:>4}  {f['perstag']:<30}  {f['title']}\")
"
```

Output looks like:

```
 293  LPIS_PURCHASE_DATE              LPIS Purchase Date
 294  ASIMR_PURCHASE_DATE             ASIMR Purchase Date
 295  IIDF_PURCHASE_DATE              IIDF Purchase Date
 296  LPIS_COHORT                     LPIS Cohort
```

This uses the same `ACClient.paginate` helper that the existing `list-tags` and `list-campaigns` commands rely on.

## Workaround 3: use the AC UI

ActiveCampaign > Contacts > Manage Fields shows every custom field with its perstag. Copy the perstag - you can then derive the ID via Workaround 2 if needed, or just use the perstag in merge fields directly (e.g. `%LPIS_PURCHASE_DATE%`).

## Why the gap exists

ac-builder v0.5 focuses on email rendering, sequence building, and campaign send/list. Custom fields are read by the merge-field renderer (which substitutes `%PERSTAG%` server-side) but never enumerated by the CLI. Adding a `list-fields` subcommand is straightforward (the wiring already exists in `client.paginate`) and would be a useful follow-up.

## Underlying API

`GET /api/3/fields` - returns one row per custom field with `id`, `title`, `perstag`, `type` (text, dropdown, date, etc.), and `options` for dropdown/radio fields.

## See also

- `references/list-tags.md` - for tag IDs (separate concept from custom fields)
- `references/pagination.md`
