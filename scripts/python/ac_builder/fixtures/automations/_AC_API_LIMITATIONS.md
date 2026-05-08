# AC API limitations for programmatic automation creation

**Investigation date:** 2026-04-28
**Conclusion:** AC's V3 API does NOT support programmatic automation creation on this account/key. The "link-action workaround" pattern documented in `references/ActiveCampaign-API-HTML-Email-Workflow-Reference.md` Section 7 is partially supported at best.

## What we tried

| Endpoint | Result |
|---|---|
| `POST /api/3/automations` (with metadata) | **405 Method Not Allowed** (no `detail` in body) |
| `POST /api/3/automation` (singular) | 404 No route |
| `POST /api/3/automations/{id}/duplicate` | 405 (Allow: GET) |
| `POST /api/3/automations/{id}/copy` | 405 (Allow: GET) |
| `POST /api/3/automation/{id}/copy` | 404 No route |
| `PATCH /api/3/automations/duplicate` | Route exists but no body shape we tried matched (always returned `"No Result found for Series with id 0"`) |
| `POST /api/3/automationTriggers` | 404 No route |
| `GET /api/3/links/{id}/actions` | "Link has no relationship definition for actions" |
| `GET /api/3/linkActions` | 404 No route |
| `GET /api/3/campaignLinks/{id}/actions` | 404 No route |
| V1 `link_edit` / `link_list` | "You are not authorized to access this file" (admin-only) |

## What DOES work (read-only)

- `GET /api/3/automations` — list all
- `GET /api/3/automations/{id}` — fetch metadata only (NOT triggers/blocks)
- `GET /api/3/automations/{id}/triggers` — fetch trigger nodes
- `GET /api/3/automations/{id}/blocks` — fetch action/block tree
- `GET /api/3/links` — list all tracked links
- `GET /api/3/links/{id}` — fetch a specific link
- `GET /api/3/campaigns/{id}/links` — list links for a campaign
- `PATCH /api/3/automations/{id}` with `{"automation": {"status": "0|1"}}` — toggle automation active/inactive (works for EXISTING automations)

## What this means for ac-builder

The `link_actions.wire_links_for_campaign()` function will fail at the
`POST /automations` step. The build pipeline catches this exception per-email
and continues — campaigns get built and content is correct, but no
click-trigger automations are auto-created.

## Recommended workflow (manual click-action setup)

After `ac-builder build-sequence --apply` creates campaigns:

**Per campaign in AC UI:**
1. Open the campaign in AC
2. For each tracked link the link-action-map specifies (Not Interested, Sales Page CTA), click the link in the campaign editor → "Add Action"
3. Pick "Add tag" → enter the tag name (e.g., `NOT INTERESTED: LPIS 2026`)
4. Save

Tim's existing tag-triggered automations (`NOT INTERESTED: LPIS 2026`, `INTEREST: LPIS 2026 - Engaged`, etc., automation IDs 2926-2934) then fire from the tag application.

Estimated effort: ~3-5 minutes per campaign, ~3-5 hours total for 67 emails. Spread across the launch window this is manageable.

## Captured templates (this directory)

The `not-interested-click.json` and `interest-tag-click.json` files in this
directory ARE captured but cannot be used to recreate automations. They are
**reference documentation** of the trigger + block shape AC uses internally:

- `triggers[0]` shows the `click` trigger with `params.linkid` and `params.listid`
- `blocks[0]` is the `start` block linking the trigger to actions via `params.starts: [trigger_id]`
- `blocks[1]` is the `addtag` block with `params.tagIds: [tag_id]` and `parent: <start_block_id>`

Useful for understanding AC's automation graph if/when AC publishes the
creation API or if you need to escalate to AC support.

## Future investigation

If you need to revisit programmatic automation creation:

1. **Contact AC support** with this finding. The reference doc claims POST works; it doesn't on this account. Possibly a permissions / account-tier issue.
2. **Capture browser network requests** when AC UI duplicates an automation. The undocumented endpoint AC uses internally may be discoverable.
3. **Check if AC has a Node.js SDK** that handles the multi-step creation. The pattern would be: POST /automations → POST trigger → POST start block → POST addtag block → PATCH status. If a client library exists, mirror its call sequence.
4. **Webhook-driven alternative**: configure AC to fire a webhook on link click, hit a self-hosted endpoint that calls `POST /api/3/contactTags` to apply the tag. Adds infrastructure but bypasses the automation-creation issue entirely.
