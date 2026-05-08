# Troubleshooting ac-builder install issues

## `uv: command not found`

`uv` is a hard prerequisite (no fallback to plain pip). Install with:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Then restart your shell or `source ~/.bashrc` / `source ~/.zshrc`.

Verify: `uv --version` should print 0.4 or higher.

## `node: command not found` or wrong version

MJML requires Node 20+. Install via nvm:

```bash
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.7/install.sh | bash
nvm install 20
nvm use 20
```

Verify: `node --version` should print v20.x.x or higher.

## `AC API: FAIL: AC_API_URL not set`

The credential file isn't being found. The tool walks this resolution chain:

1. Process env vars (`export AC_API_URL=...`)
2. `./ac-builder.env` in the current working directory
3. `~/.config/ac-builder/config.env` (XDG default)

Most users want option 3. Create the file:

```bash
mkdir -p ~/.config/ac-builder
cat > ~/.config/ac-builder/config.env <<EOF
AC_API_URL=https://your-account.api-us1.com
AC_API_KEY=your-api-key
AC_DEFAULT_LIST_ID=1
AC_DEFAULT_FROM_NAME=Your Name | Your Brand
AC_DEFAULT_FROM_EMAIL=hello@yourdomain.com
AC_DEFAULT_REPLY_TO=hello@yourdomain.com
EOF
```

Get AC_API_URL and AC_API_KEY from AC > Settings > Developer.

## `AC API: FAIL: 401 Unauthorized`

Your API key is invalid or revoked. Regenerate at AC > Settings > Developer > "Generate new API key", then update `~/.config/ac-builder/config.env`.

## `theme <name>: FAIL: ...`

The theme JSON doesn't validate against `themes/_schema.json`. Common issues:

- **Hex colors must be 6 digits.** `#000` is invalid; use `#000000`.
- **`name` field must match filename.** A theme at `themes/examples/lpis.json` must have `"name": "lpis"`.
- **All required `colors` keys present.** Required: `primary`, `cta_bg`, `cta_text`, `body_text`, `body_text_dark`, `bg`, `bg_dark`, `card_bg`, `card_bg_dark`.
- **Banner URL invalid.** Must be a full HTTPS URL (use placehold.co for testing).

To see the specific error, run with verbose:

```bash
uv run --directory ${CLAUDE_PLUGIN_ROOT}/scripts/python ac-builder verify --themes-only
```

The error line shows exactly which field failed.

## `mjml: FAIL: command not found`

Run `npm install` once in the plugin's Python directory:

```bash
cd ${CLAUDE_PLUGIN_ROOT}/scripts/python && npm install
```

Verify: `npx mjml --version` should print `4.15.3`.

## Per-platform gotchas

- **macOS with system Python:** uv strongly recommended; uses its own Python install rather than system Python.
- **Windows:** plugin tested on macOS and Linux. Windows may work via WSL2; plain Windows shells are not supported in v0.5.
- **Linux without sudo:** `uv` install script writes to `~/.cargo/bin/`, no sudo needed.
