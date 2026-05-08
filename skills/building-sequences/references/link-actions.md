# Link-action automations reference

How to wire AC click-action automations to specific links in built campaigns. Optional and currently subject to AC API limitations - read this before relying on it.

## Why link-actions matter

ActiveCampaign supports "click action" automations - workflows that fire when a contact clicks a specific link inside an email. Common uses:

- Apply an interest tag when the contact clicks a sales-page CTA (`INTEREST: <Product>`)
- Apply a "not interested" tag when the contact clicks a not-interested link (suppresses future campaigns in that sequence)
- Trigger a follow-up sequence when the contact clicks a high-intent link (e.g. pricing page)

Manually wiring this in the AC UI is tedious. For 20 emails with 3 link types each, that's 60 manual configs. The link-actions feature in ac-builder aims to automate this.

## The capture-then-reference flow

The workflow has two phases:

### Phase 1: Capture template automations

Build a single template automation in the AC UI that does what you want (e.g. applies a tag when a link is clicked). Then capture its JSON via:

```bash
uv run --directory ${CLAUDE_PLUGIN_ROOT}/scripts/python ac-builder capture-automation <automation_id> --out fixtures/automations/<name>.json
```

The captured JSON is a redacted, parameterised version of the automation - tags, link IDs, campaign IDs are replaced with placeholders like `__TAG_ID__`, `__LINK_ID__`, `__CAMPAIGN_ID__`.

You typically capture 2-3 templates: `interest-tag.json`, `not-interested-tag.json`, `purchase-tag.json`.

### Phase 2: Reference templates from a link-actions map

A link-actions map is a JSON file with per-email-code mappings of URL patterns to template names. Sample shape:

```json
{
  "E1": {
    "https://example.com/sales?cid=%CONTACTID%": "interest-tag",
    "https://example.com/not-interested?cid=%CONTACTID%": "not-interested-tag"
  },
  "E2": {
    "https://example.com/sales?cid=%CONTACTID%": "interest-tag"
  }
}
```

Then the orchestrator (when this feature is wired into `build-sequence`) processes each email's rendered HTML, finds the matching link IDs, and creates V3 link-action mappings using the captured automation JSON as the template.

## Current limitations (v0.5)

**Important:** AC's V3 API does NOT support `POST /automations` on most accounts. The captured-template approach can substitute IDs and PUT existing automations, but it cannot programmatically CREATE new ones.

What this means in practice:

- You can capture template automations: works
- Substituting IDs into a captured template and re-PUTing: partial; depends on API permissions
- Wiring up brand-new automations from scratch via the API: not supported on most accounts

For details on what does and doesn't work, see the AC API limitations doc bundled with the orchestrator at `${CLAUDE_PLUGIN_ROOT}/scripts/python/ac_builder/fixtures/automations/_AC_API_LIMITATIONS.md`.

The pragmatic workaround used by most teams is:

1. Build the template automations once in the AC UI
2. After `build-sequence --apply` creates campaigns, manually wire the click actions in the AC UI per campaign

This is documented as the "manual UI wiring" pattern. See your team's specific setup notes (e.g. the iDD project's `manual actions reference`).

## When the feature does work

In environments where the AC API permits `POST /automations` and link-action substitution, the flow looks like:

1. Run `capture-automation` once for each template you need
2. Author a `link-actions-map.json` mapping URL patterns to template names per email code
3. Run `build-sequence` with the map; the orchestrator handles substitution and wiring

Check current ac-builder behaviour by running:

```bash
uv run --directory ${CLAUDE_PLUGIN_ROOT}/scripts/python ac-builder capture-automation --help
```

If the orchestrator's CLI prompts you for `--link-actions <map.json>` on `build-sequence --help`, the feature is wired in. If not (current state in v0.5), use the manual UI wiring fallback.

## Capture command

The capture command is currently the supported piece:

```bash
uv run --directory ${CLAUDE_PLUGIN_ROOT}/scripts/python ac-builder capture-automation <automation_id> --out fixtures/automations/<name>.json
```

Replace `<automation_id>` with the AC automation ID (from the AC UI URL when viewing the automation). The output JSON is parameterised and ready to be referenced from a future map.

For a deeper guide on capturing and parameterising templates, see the companion skill `capturing-link-actions/` (when available in your plugin install).

## Map JSON shape

The intended map format:

```json
{
  "<email-code>": {
    "<URL-pattern>": "<template-name>",
    "<another-URL>": "<another-template>"
  },
  "<another-email-code>": { ... }
}
```

URL patterns are exact URLs as they appear in the rendered HTML (after merge field substitution at AC's send-time). Common pattern: include `%CONTACTID%` in the URL to match how AC's tracker rewrites it.

Template names match the JSON filenames (without `.json`) in `fixtures/automations/`.

## Recommendation

Use the link-actions feature only after:

1. Confirming your AC API permits the relevant V3 endpoints (test with `capture-automation` on a simple template)
2. Reading `_AC_API_LIMITATIONS.md` for the specific endpoints involved
3. Validating the wiring on one email before applying to a full sequence

Otherwise, fall back to manual UI wiring after the campaigns are built. It's tedious but reliable.
