# Common click-action automation recipes

Reference for the four click-action patterns used in the iDD launch. Each recipe documents the AC UI steps to build the template automation and the expected captured JSON shape.

For the schema of the captured JSON, see `capture-automation-output.md`. For the (NOT YET IMPLEMENTED) `--link-actions` map file format, see `link-action-maps.md`.

## NOT INTERESTED click

**Trigger:** Subscriber clicks the "Not the right fit?" or equivalent suppression link in the email footer.

**Actions:**

1. Apply tag `NOT INTERESTED: <Product> <Year>` (e.g. `NOT INTERESTED: LPIS 2026`).
2. End this automation.
3. End other automations.

**Why end others:** the contact has explicitly opted out of this product line; let downstream tag-driven automations clean up by removing them from the launch sequence, abandon-cart, etc. Tim's existing tag-triggered cleanup automations handle the cascade once the tag is applied.

**AC UI steps:**

1. Create automation. Name it descriptively, e.g. `LINK ACTION: NOT INTERESTED template`.
2. Trigger: pick "Subscriber clicks a link in an email." Select any campaign + link as a placeholder; the capture step replaces these with `__CAMPAIGN_ID__` / `__LINK_ID__`.
3. First action: "Add a tag" → pick any NOT INTERESTED tag.
4. Second action: "End this automation."
5. Third action: "End other automations."
6. Save. No need to activate; status `2` (paused) is fine for capture.

**Captured JSON shape (after sanitization):**

- `triggers[0]`: `type: "click"`, `relid: "__CAMPAIGN_ID__"`, `params.linkid: "__LINK_ID__"`.
- `blocks[]`: a `start` block, then chained `addtag` (`tagIds: ["__TAG_ID__"]`), `end`, `endautomation` blocks.

Existing fixture: `${CLAUDE_PLUGIN_ROOT}/scripts/python/ac_builder/fixtures/automations/not-interested-click.json`.

## INTEREST click (E2 logic)

**Trigger:** Subscriber clicks the primary CTA in a launch email (sales page or registration page).

**Actions:**

1. Apply tag `INTEREST: <Product> <Year> - Engaged` (e.g. `INTEREST: LPIS 2026 - Engaged`).

**Why nothing else:** the contact stays in the launch sequence. The engagement tag drives downstream segmentation (e.g. E2 fires after E1 click; warm-segment-only emails filter on this tag). Do NOT end the automation.

**AC UI steps:**

1. Create automation. Name it descriptively, e.g. `LINK ACTION: INTEREST template`.
2. Trigger: "Subscriber clicks a link in an email." Pick any campaign + link as placeholder.
3. Action: "Add a tag" → pick any INTEREST tag.
4. Save.

**Captured JSON shape:**

- `triggers[0]`: same `click` shape as above.
- `blocks[]`: just the `start` block and one `addtag` block. No `end` or `endautomation`.

Existing fixture: `${CLAUDE_PLUGIN_ROOT}/scripts/python/ac_builder/fixtures/automations/interest-tag-click.json`.

## PURCHASE click

**Trigger:** Subscriber clicks a post-checkout thank-you page link, or a manual "I purchased" confirmation link in a follow-up email.

**Actions:**

1. Apply tag `PURCHASE: <Product> - <Cohort> - <Date>` (e.g. `PURCHASE: LPIS - Wellington - 2026-06-19`).
2. Start automation `ONBOARDING: <Product> - <Cohort>` (e.g. `ONBOARDING: LPIS - Wellington - 2026-06`).
3. End other automations.

**Why end others:** the contact is now a paying customer for this cohort; suppress them from any active launch, abandon-cart, or transition sequences for the same product.

**AC UI steps:**

1. Create automation. Name it `LINK ACTION: PURCHASE template`.
2. Trigger: "Subscriber clicks a link in an email." Placeholder campaign + link.
3. First action: "Add a tag" → pick any PURCHASE tag.
4. Second action: "Start an automation" → pick any ONBOARDING automation as placeholder. The capture step replaces this with `__AUTOMATION_ID__`.
5. Third action: "End other automations."
6. Save.

**Captured JSON shape:**

- `triggers[0]`: same `click` shape.
- `blocks[]`: `start`, `addtag` (`tagIds: ["__TAG_ID__"]`), a start-automation block (`automation: "__AUTOMATION_ID__"`), and `endautomation`.

Existing fixture: `${CLAUDE_PLUGIN_ROOT}/scripts/python/ac_builder/fixtures/automations/purchase-tag-click.json`.

## WAITLIST click

**Trigger:** Subscriber clicks a "Join the waitlist" link in a launch email after the cohort sells out.

**Actions:**

1. Apply tag `WAITLIST: <Product> <Year>` (e.g. `WAITLIST: LPIS 2026`).
2. Start automation `LAUNCH: <Product> <Year> - Waitlist <Region>` (e.g. `LAUNCH: LPIS 2026 - Waitlist AU-NZ`).

**Why no end:** the waitlist sequence is a parallel track; the contact stays in any other product-line nurture they were on. The waitlist automation itself handles its own lifecycle.

**AC UI steps:**

1. Create automation. Name it `LINK ACTION: WAITLIST template`.
2. Trigger: "Subscriber clicks a link in an email." Placeholder campaign + link.
3. First action: "Add a tag" → pick any WAITLIST tag.
4. Second action: "Start an automation" → pick the waitlist sequence automation.
5. Save.

**Captured JSON shape:**

- `triggers[0]`: same `click` shape.
- `blocks[]`: `start`, `addtag`, start-automation block.

No existing fixture as of D6; capture when the waitlist click pattern is wired for the LPIS waitlist sequence.

## Recipe summary table

| Recipe | Add tag | End this | End other | Start downstream | Existing fixture |
|---|---|---|---|---|---|
| NOT INTERESTED | Yes | Yes | Yes | No | not-interested-click.json |
| INTEREST | Yes | No | No | No | interest-tag-click.json |
| PURCHASE | Yes | No | Yes | Yes (ONBOARDING) | purchase-tag-click.json |
| WAITLIST | Yes | No | No | Yes (waitlist sequence) | (none yet) |

## Naming convention for template automations in AC UI

Use a `LINK ACTION:` prefix in the AC UI name so they are easy to find with `list-automations --search "LINK ACTION"`. Example names:

- `LINK ACTION: NOT INTERESTED template`
- `LINK ACTION: INTEREST template`
- `LINK ACTION: PURCHASE template`
- `LINK ACTION: WAITLIST template`

These template automations live in AC permanently as references; do NOT delete them after capture. If AC ever supports `POST /automations` they become the source-of-truth for replay.

## See also

- `capture-automation-output.md` - schema of the captured fixtures
- `link-action-maps.md` - future-state docs for the planned `--link-actions` flag
- `building-sequences` - the skill that creates the campaigns these automations attach to
