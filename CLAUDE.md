# ac-builder - agent and contributor guide

ac-builder builds ActiveCampaign email sequences from markdown via MJML, packaged as a Claude Code plugin. The bundled Python tool lives under `scripts/python` and is invoked through `uv run` from inside the skills.

## Layout - where things live

- Python package - `scripts/python/ac_builder/`

- Tests - `scripts/python/tests/` (pytest; run from `scripts/python`)

- Themes - repo root `themes/`, with the JSON schema at `themes/_schema.json` and the shipped themes in `themes/examples/*.json`

- Skills - repo root `skills/<name>/SKILL.md`

- Skill frontmatter linter - repo root `tools/lint-skills.py`

- CI - `.github/workflows/ci.yml`

Note that `themes/`, `skills/`, and `tools/` sit at the REPO ROOT, not under `scripts/python/`. Code (and tests) that need the themes directory should resolve it via `ac_builder.render.theme_loader.THEMES_DIR`, not by walking up from `__file__` (the test files are several levels below the repo root, so `Path(__file__).parent.parent` does not reach it).

## Verify before you push - mirrors CI one for one

CI is the source of truth. Run these from the repo root before pushing to avoid red-build round trips. Each line maps to a CI step.

```
cd scripts/python && uv run ruff check
cd scripts/python && uv run pytest -q
uv run --project scripts/python python tools/lint-skills.py .
cd scripts/python && uv run ac-builder verify --themes-only
cd scripts/python && uv run ac-builder render ../../fixtures/sample.md --email E1 --theme corporate-blue --out /tmp/x.html && test -s /tmp/x.html
cd scripts/python && uv run ac-builder render ../../fixtures/sample.md --email E1 --theme lpis --out /tmp/x.html && test -s /tmp/x.html
```

Use the exact `uv run ...` form, not `.venv/bin/python` shortcuts. Invocation details (working directory, `--project` vs `--directory`) change path resolution and are the usual cause of local-passes-but-CI-fails.

## CI gotchas - learned the hard way

- The ruff step is the real gate. The pytest step ends in `|| echo ...`, so test failures do NOT fail the build. A green check does not mean tests passed - read the pytest log, do not trust the step status.

- ruff is configured in `scripts/python/pyproject.toml` (`select = ["E","F","I","B","UP"]`). Import order (I001) and unused imports (F401) are enforced. Run `ruff check --fix` after editing Python to keep lint debt from accumulating into a red build.

- lint-skills must run from the repo root, because both the script and the `skills/` tree are there. Use `uv run --project scripts/python python tools/lint-skills.py .` (sets the venv without changing directory). Do NOT use `--directory scripts/python` - that cd's away from the script.

- Failures cascade. Steps run in order and some are independent pre-existing issues, so fixing the first red step can reveal the next. After any fix, re-run ALL the verify commands above, not just the one you changed.

## Releasing - the version lives in six places

Bump all of these together, or the release ships inconsistent metadata:

- `.claude-plugin/plugin.json`

- `scripts/python/pyproject.toml`

- `scripts/python/ac_builder/__init__.py` (the `__version__` line)

- `scripts/python/package.json`

- `scripts/python/package-lock.json` (two `version` fields - the root one and `packages.""`)

- `scripts/python/uv.lock` (the `[[package]] name = "ac-builder"` entry)

Then add a `CHANGELOG.md` entry, commit, `git tag vX.Y.Z`, push the tag, and `gh release create vX.Y.Z`.

## Email source format and the truncation guard

Launch email bodies in the source markdown end with the `/not-interested/` opt-out link as their final element. An in-body `### ` heading BEFORE that link silently truncates the rendered body, because body extraction stops at the first in-body H3. Post-link `### CTA` and `### Technique Notes` headings are intentional authoring notes that the parser strips on purpose.

Two guards enforce this (see `ac_builder/parser.py` and `ac_builder/validate/_checks_compliance.py`): a pre-send ERROR when a launch body is missing the opt-out link, and a parser WARNING when an in-body `### ` heading appears before it. Do not use `### ` for content inside an email body - use bold instead.
