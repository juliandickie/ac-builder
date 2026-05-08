# capture-automation output schema

Reference for the JSON fixture shape produced by `ac-builder capture-automation`. The captured file is a sanitized snapshot of an AC automation's V3 GET response, with specific IDs replaced by placeholder strings.

Verified 2026-04-28 against AC automations 2935 (NOT INTERESTED test) and 2936 (INTEREST test).

## Top-level structure

A captured fixture is a JSON object with these top-level keys:

- `automation` - the automation metadata block (name, status, exit-on-unsubscribe flags, etc.)
- `triggers` - an array of trigger objects (entry conditions: link clicks, tag adds, list subscribes, etc.)
- `blocks` - an array of action blocks (the steps that fire in sequence: addtag, end, etc.)

The capture helper also strips the volatile fields `id`, `userid`, `cdate`, `mdate`, `rev_count` from the top-level object. Inner blocks retain their own `cdate`/`mdate` because they are tied to the captured AC blocks; only the top-level wrapper is cleaned. See `_capture_helper.py` for the exact implementation.

## triggers[]

Each trigger has:

- `type` - the trigger kind. For click-action automations this is `"click"`.
- `relid` - the campaign ID the trigger watches. For `click` triggers this becomes `__CAMPAIGN_ID__` after sanitization.
- `params.linkid` - the link ID within the campaign. Becomes `__LINK_ID__`.
- `params.listid` - the list ID (often `0` meaning all lists). Not sanitized.
- `seriesid` - back-reference to the parent automation's ID. Not sanitized; usually irrelevant for replay.

For a NOT INTERESTED click trigger the captured params look like:

```json
{
  "type": "click",
  "relid": "__CAMPAIGN_ID__",
  "params": {
    "listid": 0,
    "linkid": "__LINK_ID__"
  }
}
```

## blocks[]

Each block represents one step in the automation graph:

- `type` - the action kind. Common ones for click-action templates: `"addtag"`, `"start"`, `"end"`.
- `params` - type-specific parameters. For `addtag` it is `{"tagIds": ["__TAG_ID__"]}`. For `start` it is `{"starts": ["<trigger-id>"]}`.
- `parent` - the upstream block ID. The `start` block has `parent: null`.
- `ordernum` - position within siblings.

For `addtag`, the `tagIds` array is sanitized: each entry becomes `__TAG_ID__`. If the original automation added two tags, both get the same placeholder, which means the fixture loses the distinction. In practice click-action templates only add one tag, so this is not a problem; if a template needs to add multiple distinct tags, sanitize manually.

## Portable vs automation-specific

What is portable across automations (re-usable as a literal template):

- The block `type` values (`addtag`, `start`, `end`, etc.).
- The trigger `type` (`click`, `subscribe`, etc.).
- The block ordering and `parent` relationships.
- The general shape of `params` (what keys exist for each type).

What is automation-specific and must be rewritten if you adapt the fixture:

- `relid` on the trigger - the specific campaign ID the trigger watches.
- `linkid` - the specific link in the campaign.
- `tagIds` - the specific tag the addtag block applies.
- `automation` referenced in a `start-automation` block - the specific downstream automation to launch.
- All the `id`, `automation`, `parent` block-level identifiers that AC assigns. For replay these would need to be regenerated, which is one reason `POST /automations` is unavailable on this account.

## Use as reference

When manually wiring a click action in AC UI for a new campaign:

1. Open the matching fixture (e.g. `not-interested-click.json`).
2. Read the `triggers[0]` block to confirm the trigger type and the placeholder positions.
3. Read the `blocks[]` array in order (sorted by `parent`/`ordernum` if you want strict order) to see which actions to add and their sequence.
4. In the AC UI, replicate that structure, substituting the real campaign+link+tag+automation IDs for the current context.

The captured JSON is not meant to be edited and re-uploaded; it is a documentation artefact for human-driven wiring.

## Re-capture if AC schema drifts

If AC silently changes the JSON shape (e.g. renames a field, adds a new required key for a block type), existing fixtures will go stale. To detect drift:

1. Build a fresh test automation matching one of the existing template patterns.
2. Capture it into a temp file: `ac-builder capture-automation <id> --out /tmp/test.json`.
3. Diff against the existing fixture: `diff <(jq . /tmp/test.json) <(jq . path/to/existing.json)`.

If the diff is empty (modulo placeholder-eligible fields), the schema is stable. If new fields appear, update the fixtures and the placeholder map in `_capture_helper.py`.

## See also

- `automation-recipes.md` - which AC UI actions to add for each click-action pattern
- `link-action-maps.md` - future-state docs for the unbuilt `--link-actions` flag
- `_capture_helper.py` (in the python package) - the actual sanitizer code
