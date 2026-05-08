# Contributing to ac-builder

Thanks for considering a contribution. This is a small, opinionated tool maintained by Julian Dickie. Most welcome contributions are themes, skill improvements, and bug fixes.

## Dev setup

```bash
git clone https://github.com/juliandickie/ac-builder ~/code/ac-builder
cd ~/code/ac-builder/scripts/python
uv sync --extra dev
npm install
uv run pytest
```

## Adding a theme

The fastest contribution: add a new theme to `themes/examples/`.

1. Copy an existing theme as a starting point: `cp themes/examples/corporate-blue.json themes/examples/<your-theme>.json`
2. Edit the fields (display_name, colors, banner, URLs, cta_patterns)
3. Validate: `uv run --directory scripts/python ac-builder verify --themes-only`
4. Add a one-line description to `themes/examples/README.md` (if it doesn't exist, create it with a heading + bullet list)
5. Open a PR

Theme schema is at `themes/_schema.json`. Human-readable docs: `docs/theme-schema.md`.

## Improving a skill

Each skill lives in `skills/<gerund-name>/`. Includes:

- `SKILL.md` (frontmatter + body)
- `references/` (one file per detail topic, loaded on demand)

Skill frontmatter constraints (enforced by `tools/lint-skills.py` in CI):

- `name`: lowercase + hyphens only, max 64 chars, no `claude` or `anthropic`
- `description`: max 1024 chars, third person, "what + when" pattern, includes search keywords
- `allowed-tools`: minimum tools the skill needs

## Reporting bugs

Open a GitHub issue with:

1. Output of `/ac-builder:verifying-setup`
2. The exact command you ran
3. The full error output
4. Your `ac-builder` version (`uv run --directory scripts/python ac-builder --version` if a `--version` flag exists, otherwise check `scripts/python/pyproject.toml`)
5. AC API region (api-us1, api-us2, etc.)

Don't include credentials in issue text.

## Testing your changes

```bash
# Unit tests
uv run --directory scripts/python pytest -v

# Lint
uv run --directory scripts/python ruff check

# Skill metadata lint
uv run --directory scripts/python python ../../tools/lint-skills.py

# MJML compile smoke test
uv run --directory scripts/python ac-builder render fixtures/sample.md --theme corporate-blue --out /tmp/render.html
```

CI runs all of the above on every push.

## Code style

- Python: ruff defaults, line length 100
- Markdown: hyphens not em dashes (project convention)
- JSON: 2-space indent
- No trailing whitespace; one final newline

## License

By contributing, you agree your contributions will be licensed under the MIT license that covers this project.
