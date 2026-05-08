# update-message fields

Reference for the `ac_builder.api.messages_v3.update_message` helper. Sends a `PUT /api/3/messages/{id}` with payload `{"message": {<changed-fields>}}`. The Message object owns subject, preheader, body html and text, plus message-level from-address fields.

## Critical: ed_version determines what persists

**`html` and `text` only persist if the message has `ed_version=1` (classic editor) or `ed_version=None`. For `ed_version=3` (modern designer), `html` and `text` revert on next editor open in the AC UI** because the modern designer regenerates body content from its internal block tree. Subject and preheader are not in the block tree and persist in both modes.

Always run `get_message` first to inspect `ed_version` before updating body content. Detail and rationale: `ed-version-quirks.md` and `${CLAUDE_PLUGIN_ROOT}/docs/ed-version-gotcha.md`.

## Helper signature

```python
def update_message(
    client: ACClient,
    message_id: int | str,
    *,
    subject: str | None = None,
    preheader_text: str | None = None,
    html: str | None = None,
    text: str | None = None,
    fromname: str | None = None,
    fromemail: str | None = None,
    reply2: str | None = None,
) -> dict[str, Any]:
```

All fields are keyword-only and optional. At least one must be provided (otherwise `ValueError`).

## Field reference

| Field | Type | Persists if `ed_version=1`? | Persists if `ed_version=3`? | Notes |
|---|---|---|---|---|
| `subject` | string | yes | yes | Subject line. Typically merge fields like `%FIRSTNAME\|TITLECASE%`. |
| `preheader_text` | string | yes | yes | Inbox preview text. Typically 80-120 characters. |
| `html` | string | yes | **no - reverts** | Full HTML body. Includes the AC tracking pixels and unsubscribe footer. |
| `text` | string | yes | **no - reverts** | Plain-text version. AC will auto-generate from html if missing. |
| `fromname` | string | yes | yes | Display name on this message specifically. |
| `fromemail` | string | yes | yes | Sender email on this message specifically. Must be verified. |
| `reply2` | string | yes | yes | Reply-to address on this message. |

Subject and preheader are stored at the message level, outside the editor block tree, so they persist across both editor versions.

## Examples

### Update subject and preheader (always safe)

```bash
uv run --directory ${CLAUDE_PLUGIN_ROOT}/scripts/python python -c "
from ac_builder.api.v3_client import ACClient
from ac_builder.api.messages_v3 import update_message
client = ACClient()
print(update_message(
    client,
    19234,
    subject='Save the date - LPIS 2026 enrolment opens Monday',
    preheader_text='5-day window. Wellington cohort fills first.',
))
"
```

### Update body html (check ed_version first)

```bash
uv run --directory ${CLAUDE_PLUGIN_ROOT}/scripts/python python -c "
from ac_builder.api.v3_client import ACClient
from ac_builder.api.messages_v3 import get_message, update_message
client = ACClient()

# Pre-check
msg = get_message(client, 19234)
ed_version = msg.get('message', {}).get('ed_version')
if ed_version == 3:
    raise SystemExit('Message is on ed_version=3 (modern designer). html will revert. Switch to classic designer first.')

# Update
new_html = open('output/email-1.html').read()
print(update_message(client, 19234, html=new_html))
"
```

### Swap message-level from-address

```bash
uv run --directory ${CLAUDE_PLUGIN_ROOT}/scripts/python python -c "
from ac_builder.api.v3_client import ACClient
from ac_builder.api.messages_v3 import update_message
client = ACClient()
print(update_message(
    client,
    19234,
    fromname='Dr Ahmad Al-Hassiny',
    fromemail='ahmad@instituteofdigitaldentistry.com',
))
"
```

If you also want the campaign-level from-fields to match, run `update_campaign` separately (see `update-campaign-fields.md`).

## What "reverts" actually looks like

For `ed_version=3` messages, the API call to set `html` succeeds. `GET /messages/{id}` immediately afterward shows your new html. **The next time someone opens that message in AC's modern designer, the editor regenerates the html from its block tree and saves the regenerated version, overwriting your update.** If no one opens the editor, the change persists. But sends through that campaign will use whatever the editor most recently regenerated, which can drift silently.

This is why ac-builder targets `ed_version=1` end-to-end via the V1 message_add path (used by `building-sequences`). The classic editor stores html as the source of truth and accepts API updates permanently.

## Constraints and validation

- `fromemail` must reference a verified sender. AC returns 400 for unverified addresses.
- `html` should pass the pre-send validator (`ac-builder check`) before submission - mismatched `<a>` tag counts, missing unsubscribe link, etc., will fail real sends even if the API accepts the update.
- `subject` length is not strictly bounded by AC but inbox previews truncate around 60-80 characters.

## Underlying API

```
PUT /api/3/messages/{id}
Content-Type: application/json
Body: {"message": {<changed-fields>}}

Returns: {"message": {<full updated record>}, ...}
```

## See also

- `update-campaign-fields.md` - campaign-level metadata (name, analytics_campaign_name, addressid)
- `ed-version-quirks.md` - the editor-version reversion caveat in detail
- `${CLAUDE_PLUGIN_ROOT}/docs/ed-version-gotcha.md` - shared cross-skill caveat document
