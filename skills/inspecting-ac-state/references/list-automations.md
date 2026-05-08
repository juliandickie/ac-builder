# list-automations

Lists every automation in the configured AC account. No filter flags - the full set is paginated and printed.

## Invocation

```bash
uv run --directory ${CLAUDE_PLUGIN_ROOT}/scripts/python ac-builder list-automations
```

## Flags

None. The command takes no arguments.

For client-side filtering, pipe through `grep`:

```bash
uv run --directory ${CLAUDE_PLUGIN_ROOT}/scripts/python ac-builder list-automations | grep "LAUNCH:"
```

## Output format

Three pieces per row, right-aligned ID, name, then a `status=N` suffix:

```
       1  ARCHIVE: PURCHASE: Intro to CADCAM July 2018  status=2
       3  LEAD: Things Sales Reps Don't Explain Deliver plus Campaign  status=2
       6  Course Interest - All - EDIT - CREATE NEW THEN DELETE  status=1
       7  LEAD: Titans of CAD CAM  status=2
      25  INDUSTRY: 3Shape  status=1
      26  INDUSTRY: Align  status=1
```

### Status codes

| Status | Meaning |
|---|---|
| `1` | Active - automation is running and can fire on triggers |
| `2` | Inactive or draft - automation exists but won't fire |

## Common patterns

### List active launch automations

```bash
uv run --directory ${CLAUDE_PLUGIN_ROOT}/scripts/python ac-builder list-automations | grep "LAUNCH:" | grep "status=1"
```

### Find the ID of a specific iDD automation

```bash
uv run --directory ${CLAUDE_PLUGIN_ROOT}/scripts/python ac-builder list-automations | grep "LAUNCH: LPIS 2026 - Main AU-NZ"
```

### Audit which automations are inactive

```bash
uv run --directory ${CLAUDE_PLUGIN_ROOT}/scripts/python ac-builder list-automations | grep "status=2" | head -30
```

### Count automations in account

```bash
uv run --directory ${CLAUDE_PLUGIN_ROOT}/scripts/python ac-builder list-automations | wc -l
```

## Limitations

- No `--name`, `--status`, or `--limit` flag. All filtering is client-side via shell tools.
- Triggers and actions are not listed - only the automation name and overall status. To inspect actions inside an automation, use the separate `capturing-automations` skill.
- No `--json` output.
- The full list can be long on accounts with historical automations. The CLI walks all pages with no client-side cap.

## Underlying API

`GET /api/3/automations` with `limit=100&offset=...` walking pages. Implemented in `ac_builder.api.automations_v3.list_automations`. The function does accept `**filters` kwargs that map to `filters[X]=Y` query params, but the CLI does not surface any of those flags - to use server-side filtering you'd need to call from Python directly.

## See also

- `references/pagination.md`
- iDD automation naming standard: project root `CLAUDE.md` (CATEGORY: Product [Year[-Month]] - Variant)
