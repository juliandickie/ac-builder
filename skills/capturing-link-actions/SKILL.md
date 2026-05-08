---
name: capturing-link-actions
description: Use when the user wants to capture an existing AC automation as a reusable JSON template for click-action wiring. Build one template automation per click-action pattern in AC UI (interest-tag, not-interested-tag, purchase-tag, waitlist-tag); this skill captures it via capture-automation to fixtures/automations/<name>.json. The captured templates serve as reference checklists when wiring click actions in AC UI for future sequences. The planned --link-actions flag for build-sequence is NOT implemented in v0.5.
allowed-tools: Bash, Read, Write
argument-hint: "<automation-id> --out fixtures/automations/<name>.json"
---

# Capturing AC link-action automations as templates

A small wrapper around `ac-builder capture-automation` that turns a hand-built AC automation into a sanitized JSON fixture. The use case: when the same click-action pattern (e.g. NOT INTERESTED tag → end automation) is needed across many email sequences, build it once in the AC UI, capture its JSON shape, then use that JSON as a reference when wiring the same pattern in subsequent sequences.

## When to use

- **Multi-sequence link-action wiring.** Across the iDD launch there are 9 sequences (LPIS launch, LPIS waitlist, IIDF Branch C, ASIMR launch, three onboarding, two abandon-cart) all needing the same set of click-action patterns: NOT INTERESTED, INTEREST, PURCHASE, WAITLIST. Build each pattern once, capture its template, then reference the captured JSON when manually configuring click actions for each new campaign.
- **Document the schema.** AC's automation JSON shape is partly undocumented. A captured fixture is the most reliable record of what AC actually emits for a given automation graph (triggers + blocks + parent-child structure).
- **Future-proof against AC schema drift.** If AC silently changes their automation JSON shape, re-capturing reveals the diff. The fixtures act as a regression baseline.

If the goal is to inspect a *single* automation without saving a template, use `inspecting-ac-state` (`list-automations`, `get-automation`) instead.

## v0.5 limitation: capture-only, not replay

> Important: AC's V3 API does not support `POST /automations` on this account, so captured fixtures cannot be turned into deployed automations programmatically. They are reference-only.

The planned `--link-actions <map.json>` flag for `build-sequence` is **NOT** implemented in v0.5. Even if it were, AC's API would reject the create call. The current workflow is:

1. Build template automation in AC UI.
2. Capture its JSON via `capture-automation`.
3. Use the captured JSON as a checklist when manually configuring click actions per campaign in AC UI.

For 67 emails across 9 sequences this is roughly 3-5 hours of manual UI work, but it is unavoidable given the API constraint. Tim's existing tag-triggered automations handle the cascade once tags are applied, so the manual step is only "wire each link to the right tag-add action."

The deeper investigation: `${CLAUDE_PLUGIN_ROOT}/scripts/python/ac_builder/fixtures/automations/_AC_API_LIMITATIONS.md`.

## CLI status

The capture command is wired up in v0.5. Confirm with:

```bash
uv run --directory ${CLAUDE_PLUGIN_ROOT}/scripts/python ac-builder capture-automation --help
```

Signature:

```
ac-builder capture-automation <automation_id> --out <path>
```

Both arguments required. Output path can be relative or absolute.

## Capture flow

### Step 1: Build the template in AC UI

Pick one click-action pattern (e.g. NOT INTERESTED). In the AC UI:

1. Create a new automation.
2. Trigger: "Subscriber clicks a link in an email" → pick any campaign+link as the placeholder (the capture step will sanitize the specific IDs).
3. Add the actions for this pattern. For NOT INTERESTED:
   - Add tag (any tag works as placeholder; the capture sanitizes the ID).
   - End this automation.
   - End other automations.
4. Save the automation.

You do NOT need to activate it. Status `2` (paused) is fine for capture.

### Step 2: Get the automation ID

The ID is in the URL: `https://YOURACCOUNT.activehosted.com/app/automations/2935/edit` → ID is `2935`.

Or use `inspecting-ac-state`:

```bash
uv run --directory ${CLAUDE_PLUGIN_ROOT}/scripts/python ac-builder list-automations --search "test not interested" --limit 5
```

### Step 3: Capture to a fixture file

```bash
uv run --directory ${CLAUDE_PLUGIN_ROOT}/scripts/python ac-builder capture-automation 2935 \
  --out ${CLAUDE_PLUGIN_ROOT}/scripts/python/ac_builder/fixtures/automations/not-interested-click.json
```

The CLI prints `Captured automation 2935 -> <path>` and exits 0.

What capture does:

- Fetches the full automation JSON via `GET /automations/{id}`.
- Walks the triggers and blocks, replacing specific IDs (`campaignid`, `linkid`, `tag`, `automation`) with placeholder strings (`__CAMPAIGN_ID__`, `__LINK_ID__`, `__TAG_ID__`, `__AUTOMATION_ID__`).
- Strips volatile fields (`id`, `userid`, `cdate`, `mdate`, `rev_count`).
- Writes pretty-printed JSON to the output path.

Schema details: `references/capture-automation-output.md`.

### Step 4: Reference the fixture during manual UI wiring

When wiring click actions for a new campaign in AC UI, open the matching fixture (e.g. `not-interested-click.json`) and use it as a checklist:

- Trigger type matches (`click`).
- Action sequence matches (addtag → end → end other).
- Tag and automation references map to the right specific IDs for the current campaign and target tag.

Common recipes (which actions belong to which click pattern): `references/automation-recipes.md`.

## Three example captures

For the iDD launch the canonical templates are interest-tag, not-interested-tag, and purchase-tag. WAITLIST is a fourth used only in the LPIS waitlist parallel sequence.

### interest-tag

Apply an `INTEREST: <Product> <Year> - Engaged` tag when the contact clicks the primary CTA. No automation termination; the contact stays in the launch sequence and the engagement tag drives downstream segmentation.

```bash
uv run --directory ${CLAUDE_PLUGIN_ROOT}/scripts/python ac-builder capture-automation <id> \
  --out ${CLAUDE_PLUGIN_ROOT}/scripts/python/ac_builder/fixtures/automations/interest-tag-click.json
```

### not-interested-tag

Apply a `NOT INTERESTED: <Product> <Year>` tag, end this automation, end other automations. Used for the suppress-me link in every footer.

```bash
uv run --directory ${CLAUDE_PLUGIN_ROOT}/scripts/python ac-builder capture-automation <id> \
  --out ${CLAUDE_PLUGIN_ROOT}/scripts/python/ac_builder/fixtures/automations/not-interested-click.json
```

### purchase-tag

Apply `PURCHASE: <Product> - <Cohort> - <Date>`, kick off the matching ONBOARDING automation, end other automations (so abandon-cart and launch sequences stop). Triggered by clicks on the post-checkout thank-you page or a manual "I purchased" confirmation link.

```bash
uv run --directory ${CLAUDE_PLUGIN_ROOT}/scripts/python ac-builder capture-automation <id> \
  --out ${CLAUDE_PLUGIN_ROOT}/scripts/python/ac_builder/fixtures/automations/purchase-tag-click.json
```

Full recipe details (which AC blocks to add, what order): `references/automation-recipes.md`.

## See also

- `inspecting-ac-state` - find an automation ID before capture
- `building-sequences` - the build path that creates campaigns; the captured templates are referenced when wiring click actions in those campaigns
- `references/capture-automation-output.md` - schema of the captured JSON
- `references/link-action-maps.md` - future-state docs for the planned `--link-actions` flag (NOT implemented in v0.5)
- `references/automation-recipes.md` - recipes for the common click-action patterns
