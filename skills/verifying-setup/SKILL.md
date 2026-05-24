---
name: verifying-setup
description: Use when the user wants to confirm the ac-builder pipeline is healthy, troubleshoot install issues, or audit recent builds. Checks AC API credentials, MJML binary version, theme JSON validation, and lists recent build manifests. Read-only and safe to run anytime. Should be the first skill run after installing ac-builder for the first time.
allowed-tools: Bash
argument-hint: "[--themes-only] [--since 7d] [--theme <name>]"
---

# Verifying ac-builder setup

Confirm the ac-builder Python tool can authenticate with ActiveCampaign, the MJML renderer is installed, and themes load successfully. Also lists recent build manifests for auditing what was built when.

## When to use

- First run after installing the plugin (guides you through any missing prerequisites)
- Anytime AC builds start failing and you want to isolate whether it's auth, rendering, or theme issues
- Periodically to audit which sequences ran and when (`list-builds`)

## Workflow

### Quick verify

```bash
uv run --directory ${CLAUDE_PLUGIN_ROOT}/scripts/python ac-builder verify
```

Output looks like:

```
ac-builder 0.5.1
mjml: 4.15.3
theme corporate-blue: OK
theme friendly-startup: OK
theme lpis: OK
... (all bundled themes)
AC API: OK (https://your-account.api-us1.com/api/3)
```

If any line shows FAIL or an error, see `references/troubleshooting.md`.

### Themes-only check (CI mode)

```bash
uv run --directory ${CLAUDE_PLUGIN_ROOT}/scripts/python ac-builder verify --themes-only
```

Skips AC API and MJML checks; validates theme JSONs only. Used by CI pipelines that don't have AC credentials.

### Audit recent builds

```bash
uv run --directory ${CLAUDE_PLUGIN_ROOT}/scripts/python ac-builder list-builds [--since 7d] [--theme lpis]
```

Lists all `.build-manifests/YYYY-MM-DD/*.json` records the tool wrote when running `build-sequence --apply`. See `references/list-builds-filters.md` for filter flags.

## First-run setup walkthrough

When `verify` fails, follow this sequence:

1. **`uv` not found** -> install: `curl -LsSf https://astral.sh/uv/install.sh | sh`
2. **Node 20+ not found** -> install via nvm: `nvm install 20 && nvm use 20`
3. **AC credentials missing** -> create `~/.config/ac-builder/config.env`:
   ```
   AC_API_URL=https://your-account.api-us1.com
   AC_API_KEY=your-api-key
   AC_DEFAULT_LIST_ID=1
   AC_DEFAULT_FROM_NAME=Your Name | Your Brand
   AC_DEFAULT_FROM_EMAIL=hello@yourdomain.com
   ```
   AC API credentials are at AC > Settings > Developer.
4. **MJML missing** -> run once: `cd ${CLAUDE_PLUGIN_ROOT}/scripts/python && npm install`
5. **Theme load failures** -> see `references/troubleshooting.md`

## Output interpretation

See `references/verify-output.md` for line-by-line meaning of each check.

## Recovery from failures

See `references/troubleshooting.md` for common failure modes and fixes.
