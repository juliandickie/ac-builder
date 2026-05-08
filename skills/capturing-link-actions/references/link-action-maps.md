# link-action-maps (future state)

> **Status: NOT IMPLEMENTED in v0.5.** This document describes the eventual flow for forward planning. The current `build-sequence` CLI does NOT accept a `--link-actions` flag. Click actions are wired manually in AC UI per campaign.

The eventual goal is to extend `ac-builder build-sequence` with a `--link-actions <map.json>` flag. The map file would tell the builder, per email code, which URL patterns in the rendered HTML map to which captured automation template, so the builder could auto-create the matching click-action automations after creating the campaigns.

Even once the flag is implemented, AC's current API constraint (no `POST /automations` on this account) means the auto-create step would need a workaround, e.g. duplicating an existing automation through a different endpoint, or using V3 PUT to mutate a stub automation into the desired shape. The investigation is in `${CLAUDE_PLUGIN_ROOT}/scripts/python/ac_builder/fixtures/automations/_AC_API_LIMITATIONS.md`.

## Proposed schema

A link-action map is a JSON object keyed by email code (the values used in MD source headings, e.g. `E1`, `E2`, `WL1`, `C1`, `G1`). Each value is a sub-object mapping URL patterns to template names.

```json
{
  "E1": {
    "https://instituteofdigitaldentistry.com/live-courses/live-patient-implant-surgery-course-wellington-new-zealand/?cid=%CONTACTID%": "interest-tag-click",
    "https://instituteofdigitaldentistry.com/not-interested/?cid=%CONTACTID%": "not-interested-click"
  },
  "E2": {
    "https://instituteofdigitaldentistry.com/live-courses/live-patient-implant-surgery-course-wellington-new-zealand/?cid=%CONTACTID%": "interest-tag-click",
    "https://instituteofdigitaldentistry.com/not-interested/?cid=%CONTACTID%": "not-interested-click"
  },
  "WL1": {
    "https://instituteofdigitaldentistry.com/live-courses/live-patient-implant-surgery-course-wellington-new-zealand/waitlist/?cid=%CONTACTID%": "waitlist-tag-click"
  }
}
```

The template names are the basenames (without `.json`) of fixtures in `fixtures/automations/`, e.g. `interest-tag-click` resolves to `fixtures/automations/interest-tag-click.json`.

## URL matching

Exact-match by default. Merge-field placeholders like `%CONTACTID%` would match the as-rendered URL in the campaign HTML, so the map file should include the placeholder verbatim as it appears in source MD.

If glob or regex matching is needed later, a future schema version could accept wildcards or a `match_type` field per pattern.

## Per-email vs per-product context

Per email, the same URL might map to different template instances depending on the *product* the email targets:

- `E1` (LPIS launch) clicks on the sales URL → `interest-tag-click` with the LPIS-specific tag (`INTEREST: LPIS 2026 - Engaged`).
- `G1` (ASIMR launch) clicks on the sales URL → `interest-tag-click` with the ASIMR-specific tag (`INTEREST: ASIMR - Engaged`).

The map file would need to either:

- Specify the tag ID per entry (e.g. `{"template": "interest-tag-click", "tag": "INTEREST: LPIS 2026 - Engaged"}`).
- Or rely on a separate `--theme` argument that already encodes the product context.

The second option is cleaner because it keeps the map file declarative and reuses the theme system already in place for content rendering.

## Eventual flow

When implemented, the build-sequence call would be:

```bash
uv run --directory ${CLAUDE_PLUGIN_ROOT}/scripts/python ac-builder build-sequence \
  --source path/to/source.md \
  --theme lpis \
  --list-id 22 \
  --from-address 5 \
  --link-actions path/to/link-actions.json \
  --apply
```

After creating each campaign, the builder would:

1. Match the campaign's URLs against the map.
2. For each match, load the corresponding template fixture.
3. Substitute `__CAMPAIGN_ID__` (just-created campaign), `__LINK_ID__` (looked up via campaign's links), `__TAG_ID__` (resolved by tag name), `__AUTOMATION_ID__` (resolved by name for start-automation blocks).
4. Either `POST /automations` with the assembled JSON (currently blocked by AC) or apply the workaround.
5. Activate the automation.

For now (v0.5), steps 4-5 are manual UI work, with the captured fixtures serving as a reference for what to wire up.

## Until then

Manual workflow per campaign:

1. After `build-sequence --apply` creates a campaign, open it in AC UI.
2. For each link in the campaign that needs an action (typically two: the primary CTA and the not-interested footer link), build a matching automation in AC UI using the captured fixture as a checklist.
3. Activate the automation.

For the iDD launch (67 emails, 9 sequences, three to four click-action patterns each) this is roughly 3-5 hours of UI work total. Documenting the patterns in fixtures means the wiring is deterministic and reviewable.

## See also

- `capture-automation-output.md` - schema of the captured fixtures
- `automation-recipes.md` - which AC actions belong to each click-action pattern
- `_AC_API_LIMITATIONS.md` (in the python package fixtures dir) - why the auto-create step is blocked on this account
