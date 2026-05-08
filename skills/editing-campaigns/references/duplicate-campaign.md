# duplicate-campaign

Reference for `ac_builder.api.campaigns_v3.duplicate_campaign`. Two-step copy + rename pattern: AC's copy endpoint ignores the `name` parameter and always returns a campaign called "<original> (Copy)", so the helper follows up with a `PUT /campaigns/{id}` to apply the intended name.

Verified 2026-04-27 against live AC.

## Helper signature

```python
def duplicate_campaign(
    client: ACClient,
    campaign_id: int | str,
    new_name: str,
) -> dict[str, Any]:
```

Returns:

```python
{
    "succeeded": True,
    "message": "...",
    "newCampaignId": 3489,
    "renamed_to": "LAUNCH: LPIS 2026 - E1 - October Cohort",
}
```

`renamed_to` is `None` if the copy step failed (in which case `succeeded` is also `False`).

## Two-step pattern

1. **Copy.** `POST /api/3/campaigns/{id}/copy` with empty body. Returns `{"succeeded", "message", "newCampaignId"}`. The new campaign inherits everything: html template, styling, from-name, from-email, reply-to, message structure, subject, preheader, body content. Its name is "<original> (Copy)" regardless of any name param.
2. **Rename.** `PUT /api/3/campaigns/{newId}` with `{"campaign": {"name": new_name}}`. Updates the name to the intended value.

The helper does both in one call.

## Important restriction

**Campaigns inside an active automation cannot be duplicated.** AC's API returns:

```
HTTP 400
{"errors": [{"detail": "not allowed to copy this campaign", ...}]}
```

For the master-and-edit workflow we use, build masters as standalone drafts (not yet wired into automation Send Email steps) so they can be duplicated. After duplication and content edits, attach duplicates to automation steps via the AC UI.

## Workaround when the source IS in an automation

If the campaign you want to copy is already attached to an automation:

1. Open the automation in the AC UI.
2. Detach the Send Email step that points at the source campaign (or remove the step entirely).
3. Run `duplicate_campaign` against the now-standalone source.
4. Re-attach the source to the automation in the UI.
5. Wire the duplicate into wherever it needs to live (a new automation step, a fresh standalone send, etc.).

## Examples

### Standard duplicate + rename

```bash
uv run --directory ${CLAUDE_PLUGIN_ROOT}/scripts/python python -c "
from ac_builder.api.v3_client import ACClient
from ac_builder.api.campaigns_v3 import duplicate_campaign
client = ACClient()
result = duplicate_campaign(
    client,
    3465,
    new_name='LAUNCH: LPIS 2026 - E1 - Save the Date - October Cohort',
)
print(result)
"
```

### Inspect the duplicate after the copy

```bash
uv run --directory ${CLAUDE_PLUGIN_ROOT}/scripts/python python -c "
from ac_builder.api.v3_client import ACClient
from ac_builder.api.campaigns_v3 import duplicate_campaign, get_campaign
client = ACClient()
result = duplicate_campaign(client, 3465, new_name='New Cohort Variant')
new_id = result['newCampaignId']
campaign = get_campaign(client, new_id)
print('new campaign:', campaign.get('campaign', {}).get('name'))
print('message_id:', campaign.get('campaign', {}).get('message_id'))
"
```

The duplicate has its own campaign ID and its own message ID. You can then call `update_message` against the new message ID to edit subject, preheader, or body html for the duplicate without touching the original.

## After duplication: editing the copy

The new campaign carries a new message ID. To edit content on the duplicate:

1. `get_campaign(client, new_id)` to find the message ID.
2. `update_message(client, message_id, subject=..., preheader_text=...)` for content edits.
3. Watch `ed_version` if you intend to update `html`/`text` - see `ed-version-quirks.md`.

Since duplicates inherit `ed_version` from the source, if the source was created via V1 message_add (ac-builder's path), the duplicate is also `ed_version=1` and content updates persist.

## Underlying API

```
Step 1:
POST /api/3/campaigns/{id}/copy
Content-Type: application/json
Body: {}
Returns: {"succeeded": true, "message": "...", "newCampaignId": N}

Step 2:
PUT /api/3/campaigns/{newId}
Content-Type: application/json
Body: {"campaign": {"name": "<new_name>"}}
Returns: {"campaign": {<full updated record>}, ...}
```

## See also

- `update-campaign-fields.md` - the rename uses update_campaign internally; same field rules apply
- `update-message-fields.md` - editing the duplicate's content
- `ed-version-quirks.md` - inherited ed_version on the duplicate
