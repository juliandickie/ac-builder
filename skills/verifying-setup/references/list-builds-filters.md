# `ac-builder list-builds` filter flags

Every successful `build-sequence --apply` writes a manifest to `.build-manifests/YYYY-MM-DD/<sequence>-<HHMMSS>.json`. The `list-builds` command queries those manifests.

## Flags

| Flag | Purpose | Example |
|---|---|---|
| `--since <duration>` | Only show builds within the last N units. Accepts `7d`, `24h`, `1w`. Default: all time. | `--since 7d` |
| `--theme <name>` | Filter to builds that used a specific theme. | `--theme lpis` |
| `--status <status>` | Filter by build outcome: `success`, `partial`, `failed`. | `--status failed` |
| `--sequence <name>` | Filter to builds that used a specific source MD filename. | `--sequence AUNZ_Main` |
| `--json` | Output raw JSON instead of the table summary. Useful for piping to `jq`. | `--json` |

## Output format

Default (table):

```
DATE        TIME    SEQUENCE                    THEME    EMAILS  STATUS
2026-04-29  14:30   AUNZ_Main_Sequence          lpis     20      success
2026-04-29  15:12   ASIMR_Onboarding            asimr    4       partial
2026-05-01  09:00   IIDF_Branch_C               iidf     5       success
```

`partial` = some emails created/updated successfully, others errored. Inspect with `--json` to see per-email status.

## Common audit queries

- "What did I build last week?": `--since 7d`
- "What's broken?": `--status failed --since 30d`
- "Which builds used the LPIS theme?": `--theme lpis`
- "Show me the raw record for the last AU/NZ build": `--sequence AUNZ_Main --json | head -1`
