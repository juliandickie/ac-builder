# Theme resolution reference

How ac-builder finds and loads themes, plus the filename inference table.

## Resolution order

When you pass `--theme <name>`, the loader walks a candidate path list and uses the first one that exists.

### Explicit path

If the argument contains a `/` or starts with `.`, it's treated as an explicit file path. No further search.

```bash
--theme ./themes/custom.json
--theme ../shared/brand.json
--theme /absolute/path/to/theme.json
```

### Named theme

If the argument is a bare name (no `/`, no `.`), the loader tries these paths in order:

1. **Project-local:** `./themes/<name>.json` (relative to where you run the CLI)
2. **User-level:** `~/.config/ac-builder/themes/<name>.json` (or `$XDG_CONFIG_HOME/ac-builder/themes/<name>.json` if set)
3. **Plugin examples:** `${CLAUDE_PLUGIN_ROOT}/themes/examples/<name>.json` (or `$AC_BUILDER_THEMES_DIR/examples/<name>.json` if set)

First match wins. If no match, the loader raises a `ThemeNotFoundError` listing every path it tried.

This means you can:

- Bundle themes with a project (commit `./themes/` to the source repo)
- Override or add themes per-user without touching the project (drop a JSON in `~/.config/ac-builder/themes/`)
- Use a plugin-provided example as-is (just pass its name, e.g. `--theme corporate-blue`)

## Filename inference (`--theme auto`)

When `--theme` is not passed, or when explicitly set to `auto`, the loader infers from the source MD filename. The patterns currently recognised (case-sensitive substring match):

| Filename contains | Resolves to |
|---|---|
| `Branch_C` or `IIDF` | `iidf` |
| `ASIMR` or `GLOBAL_Campaign_2` | `asimr` |
| `LPIS` or `Main_Sequence` or `Waitlist` or `October_LPIS` | `lpis` |

If none of the patterns match (e.g. `Abandon_Cart_Sequences_All_Products.md`), inference returns `None`. The orchestrator then falls back to the per-email `**Theme:**` field; if that's missing too, the build fails with a "could not infer theme" error.

The inference list is currently hard-coded for the iDD use-case. **Custom inference rules are not supported in v0.5.** For non-iDD products, always pass `--theme <name>` explicitly.

## Bundled example themes

The plugin ships several example themes in `${CLAUDE_PLUGIN_ROOT}/themes/examples/`:

- `corporate-blue` - conservative blue/grey corporate palette
- `friendly-startup` - warm orange/teal startup palette
- `bold-startup` - high-contrast bold-startup palette
- `minimal-mono` - black-and-white minimalist
- `lpis`, `iidf`, `asimr` - the iDD example themes

These are starting points. Copy one to `~/.config/ac-builder/themes/<your-brand>.json`, edit colours / fonts / banner URLs, and reference it as `--theme <your-brand>`.

## Theme JSON shape

Every theme JSON is validated against `_schema.json` at load time. Required top-level fields:

- `name` - short identifier
- `display_name` - human-readable label
- `colors` - palette (primary, secondary, background, text, etc.)
- `fonts` - typography settings
- `branding` - banner image URL, alt text, link
- `urls` - canonical product/sales URLs the renderer might inject
- `cta_patterns` - regex patterns auto-detected and styled as CTA buttons
- `tags` (optional) - semantic tags applied to the theme for filtering

A bad JSON raises `ThemeValidationError` with a path into the failing field. Use `ac-builder verify --themes-only` (in the verifying-setup skill) to validate every theme on disk in one pass.

## Multi-brand workflow example

Agency managing three clients, each with their own theme:

1. Create `~/.config/ac-builder/themes/clientA.json`, `clientB.json`, `clientC.json`
2. Authoring source MDs for client A: `--theme clientA` explicitly on every build
3. Same for B and C

Filename auto-inference is not used (none of the inference rules match client names). The explicit flag is always passed.

If you want auto-inference for your own brands, the recommended workaround is:

- Use a filename prefix per brand (e.g. `clientA_*.md`, `clientB_*.md`)
- Always pass `--theme <brand>` explicitly on the CLI - it's one extra flag

A future ac-builder version may expose a config-driven inference rules file. For now, keep brand selection explicit.

## Per-email theme override

A single email can override the file-level theme by setting a per-email `**Theme:**` field:

```markdown
## E5 - Cross-product nudge

**Theme:** asimr
**Send date:** Mon Apr 27, 2026

### Subject Line Options
1. **...**
```

Useful when one sequence promotes products with different brand identities (e.g. an LPIS-themed sequence with one ASIMR cross-sell). The override applies to that one email's render only.

## Troubleshooting

- "Theme '<name>' not found" -> the path list at the bottom of the error tells you exactly where it looked. Drop the JSON in one of those paths.
- "Theme '<name>' failed validation" -> the field path identifies what's missing or wrong-shaped. See `_schema.json` next to the theme directory.
- Filename inference gives wrong theme -> pass `--theme <correct>` to override.
- Per-email override isn't being honoured -> the field name is exactly `**Theme:**`. Capitalisation matters (`**theme:**` is not parsed).
