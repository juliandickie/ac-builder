# update-campaign fields

Reference for the `ac_builder.api.campaigns_v3.update_campaign` helper. Sends a `PUT /api/3/campaigns/{id}` with payload `{"campaign": {<changed-fields>}}`. Verified 2026-04-27 against live AC.

## Helper signature

```python
def update_campaign(
    client: ACClient,
    campaign_id: int | str,
    *,
    name: str | None = None,
    fromname: str | None = None,
    fromemail: str | None = None,
    reply2: str | None = None,
    analytics_campaign_name: str | None = None,
    addressid: int | str | None = None,
    public: int | bool | None = None,
    basemessageid: int | str | None = None,
) -> dict[str, Any]:
```

All fields are keyword-only and optional. Calling with no fields raises `ValueError`. Only fields that are not `None` are sent in the payload.

## Field reference

| Field | Type | Notes |
|---|---|---|
| `name` | string | Campaign display name. Must be unique within the account or AC will return a duplicate-name error. Used for matching in `building-sequences` idempotency. |
| `fromname` | string | The "From" display name shown in inboxes. Campaign-level setting; messages also have their own `fromname`. |
| `fromemail` | string | The "From" email address. Must be a verified sender or AC rejects it. |
| `reply2` | string | The Reply-To address. Defaults to fromemail if unset. |
| `analytics_campaign_name` | string | Sets the Google Analytics `utm_campaign` value AC injects into tracked links. Per AC Specs, use a slug like `implant-pathway-2026-aunz`. |
| `addressid` | int or string | ID of the physical mailing address shown in the email footer (CAN-SPAM compliance). Use `ac-builder list-addresses` to find IDs. Required by AC; usually set on first send. |
| `public` | int or bool | Campaign archive visibility. `0` (or `False`) = private, `1` (or `True`) = public. The iDD launch keeps this private. |
| `basemessageid` | int or string | Reference to a "starting template" message. Generally set by the AC UI when initializing a campaign; rarely needed via API. |

Boolean coercion: `public=True` is sent as `1`, `public=False` as `0`. AC's API expects the integer form.

## Examples

### Rename a campaign

```bash
uv run --directory ${CLAUDE_PLUGIN_ROOT}/scripts/python python -c "
from ac_builder.api.v3_client import ACClient
from ac_builder.api.campaigns_v3 import update_campaign
client = ACClient()
print(update_campaign(client, 3465, name='LAUNCH: LPIS 2026 - E1 - Save the Date'))
"
```

### Set the analytics campaign name and physical address together

```bash
uv run --directory ${CLAUDE_PLUGIN_ROOT}/scripts/python python -c "
from ac_builder.api.v3_client import ACClient
from ac_builder.api.campaigns_v3 import update_campaign
client = ACClient()
print(update_campaign(
    client,
    3465,
    analytics_campaign_name='implant-pathway-2026-aunz',
    addressid=12,
))
"
```

### Swap the from-address

```bash
uv run --directory ${CLAUDE_PLUGIN_ROOT}/scripts/python python -c "
from ac_builder.api.v3_client import ACClient
from ac_builder.api.campaigns_v3 import update_campaign
client = ACClient()
print(update_campaign(
    client,
    3465,
    fromname='Dr Ahmad Al-Hassiny',
    fromemail='ahmad@instituteofdigitaldentistry.com',
    reply2='ahmad@instituteofdigitaldentistry.com',
))
"
```

If you swap the campaign-level `fromname`/`fromemail`, remember to also update the message-level `fromname`/`fromemail` via `update-message` so the email itself shows the new sender.

## Constraints and validation

- AC validates the from-email against the account's verified senders list. An unverified email returns a 400.
- Names must be non-empty strings.
- `addressid` must reference an existing address in the account; an invalid ID returns a 404 from AC.
- `analytics_campaign_name` is free-form text but should be a URL-safe slug.

## What this endpoint does NOT touch

This is the campaign object - subject lines, preheader text, html body, and plain-text body are all on the Message, not the Campaign. To edit those, use `update_message` (see `update-message-fields.md`).

## Underlying API

```
PUT /api/3/campaigns/{id}
Content-Type: application/json
Body: {"campaign": {<changed-fields>}}

Returns: {"campaign": {<full updated record>}, ...}
```

## See also

- `update-message-fields.md` - body content lives on the Message
- `duplicate-campaign.md` - copy + rename via update_campaign in step 2
- `ed-version-quirks.md` - editor-version caveat for message body updates (does not affect campaign-level fields)
