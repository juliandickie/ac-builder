# Interpreting `ac-builder verify` output

The verify command produces three sections in order: tool version, MJML version, theme statuses, and AC API status.

## ac-builder version line

```
ac-builder 0.5.1
```

The first line is just the installed version. If this is missing entirely, `uv run` failed; the Python tool isn't installed correctly. Re-run `uv sync --directory ${CLAUDE_PLUGIN_ROOT}/scripts/python --extra dev`.

## MJML line

```
mjml: 4.15.3
```

`PASS` (any 4.15.x is acceptable). If missing or shows a different version, `npm install` wasn't run, or `node_modules/` is corrupt.

Recovery: `cd ${CLAUDE_PLUGIN_ROOT}/scripts/python && rm -rf node_modules && npm install`.

## Theme lines

```
theme corporate-blue: OK
theme friendly-startup: OK
theme lpis: OK
theme iidf: OK (banner_url is placeholder - update before --apply)
```

`OK` = passes JSON Schema validation against `themes/_schema.json`.
`OK (warning)` = valid but has known placeholder values that should be replaced before live sends.
`FAIL` = schema validation error; see the next line for the specific field.

Recovery for FAIL: open the theme JSON, fix the offending field per `themes/_schema.json`. Common issues:
- Hex colors must be 6 digits (`#000000`, not `#000`)
- `name` field must match the filename (e.g., `lpis.json` requires `"name": "lpis"`)
- All required colors keys must be present

## AC API line

```
AC API: OK (https://your-account.api-us1.com/api/3)
```

`OK` = `/api/3/users/me` returned 200. The URL shown is what the tool resolved from credentials.

`FAIL: 401` = invalid API key; regenerate at AC > Settings > Developer.
`FAIL: connection error` = wrong AC_API_URL (check spelling: it's typically `https://<account>.api-us1.com` for US-region accounts, `.api-us2.com` for some).
`FAIL: AC_API_URL not set` = config file not loaded; check `~/.config/ac-builder/config.env`.
