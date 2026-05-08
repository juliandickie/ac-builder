# Template automation JSON fixtures

> ⚠️ **2026-04-28 finding:** AC's V3 API does NOT support `POST /automations` on this account, so the capture-and-replay pattern below cannot actually create automations programmatically. See [_AC_API_LIMITATIONS.md](./_AC_API_LIMITATIONS.md) for the full investigation. The captured fixtures here are kept as **reference documentation** of AC's automation graph shape, not as deployable templates.
>
> **Recommended workflow for the iDD launch:** configure click actions manually per campaign in AC UI after `ac-builder build-sequence --apply`. ~3-5 hours total for 67 emails. Tim's existing tag-triggered automations (NOT INTERESTED + INTEREST × 6 + 4 PURCHASE) handle the cascade once tags are applied.

These are captured AC automation JSON shapes intended as templates for runtime
substitution by `link_actions.py`.

## How to add a new template

1. **Build in AC UI**: create a new automation manually with the desired trigger
   ("Clicks a link in an email") and actions ("Add tag", "End this automation",
   "End other automations", "Start an automation").
2. **Note the automation ID** from the URL: `https://YOURACCOUNT.activehosted.com/app/automations/123/edit`
3. **Capture via CLI**:
   ```bash
   ac-builder capture-automation 123 --out fixtures/automations/your-template-name.json
   ```
4. **Sanitize the captured JSON**: the capture step replaces specific IDs
   (campaignid, linkid, tag IDs, automation IDs) with placeholder strings
   (`__CAMPAIGN_ID__`, `__LINK_ID__`, `__TAG_ID__`, etc.) so `link_actions.py`
   can substitute them at build time.

## Existing templates

- `not-interested-click.json`: NOT INTERESTED click → apply tag → end this
  automation → end other automations
- `interest-tag-click.json`: Interest CTA click → apply tag (no automation
  changes)
- `purchase-tag-click.json`: Purchase confirmation click → apply purchase tag
  + start onboarding automation

## Re-capture if AC schema changes

If AC updates their automation JSON shape and existing builds fail validation,
re-run `capture-automation` against a fresh template and replace the fixture.
