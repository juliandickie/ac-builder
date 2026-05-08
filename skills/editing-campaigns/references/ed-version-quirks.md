# ed_version quirks

Every AC Message carries an `ed_version` field that records which editor was used to create or last save it. The value determines whether `PUT /messages/{id}` updates to `html` and `text` survive, or are quietly reverted on the next editor open in the AC UI.

## Summary

| `ed_version` | Editor | What persists via `PUT /messages/{id}` |
|---|---|---|
| `None` (newly created) | not yet bound | All fields persist. Becomes `1` once linked to a campaign. |
| `1` | Classic editor | All fields persist - subject, preheader, html, text, fromname, fromemail, reply2. |
| `3` | Modern designer | Subject, preheader, fromname, fromemail, reply2 persist. **html and text get regenerated from the editor's internal block tree on next save in the UI - your API update is overwritten.** |

The shared cross-skill caveat lives at `${CLAUDE_PLUGIN_ROOT}/docs/ed-version-gotcha.md` (referenced from both `editing-campaigns` and `building-sequences`). This document is the editing-skill-specific tactical guide.

## Why the modern designer reverts

The modern designer (`ed_version=3`) stores email content as a block tree - a structured representation of rows, columns, text blocks, button blocks, image blocks, etc. The `html` field is a *render* of that tree, generated whenever the editor opens or saves. Subject and preheader are not in the tree; they are message-level fields, so they persist independently.

When you `PUT /messages/{id}` with a new html value, the API accepts it. `GET /messages/{id}` immediately afterward shows your html. But the next time anyone opens the message in the modern designer in the AC UI, the editor reads the (unchanged) block tree, regenerates the html from it, and saves the regenerated version back, silently overwriting your update.

If no one opens the editor before the campaign sends, the change persists for that send. But the message is in a fragile state - any future UI inspection erases the API-applied content.

## Tactical guidance

### V1 message_add path (used by build-sequence) is safe

ac-builder's `building-sequences` skill creates messages via the V1 endpoint `POST /admin/api.php?api_action=message_add`. V1 messages do not carry an `ed_version` initially; once linked to a campaign they show as `ed_version=1` (classic). All `PUT /messages/{id}` updates persist on these.

### Modern designer in AC UI is dangerous for API updates

If a master campaign was built using the modern drag-and-drop designer in AC's UI, its messages are `ed_version=3`. API updates to body content will revert. Switch to classic designer first (one click in the AC UI - see "switching" below) or rebuild the master via V1.

### Always check ed_version before updating html or text

Pre-check pattern:

```bash
uv run --directory ${CLAUDE_PLUGIN_ROOT}/scripts/python python -c "
from ac_builder.api.v3_client import ACClient
from ac_builder.api.messages_v3 import get_message
client = ACClient()
msg = get_message(client, 19234)
m = msg.get('message', {})
print(f\"id={m.get('id')} ed_version={m.get('ed_version')} subject={m.get('subject')!r}\")
"
```

If `ed_version` is `1` or `None`: safe to update html/text.
If `ed_version` is `3`: stop. Update only subject/preheader/from-fields, or downgrade the message to classic first.

### Switching from modern to classic in AC UI

The 1-click escape hatch:

1. Open the campaign in the AC UI.
2. Click into the message editor.
3. Look for "switch to classic designer" or "use the legacy editor" - the exact label varies by AC version, usually under a settings or dropdown menu near the editor toolbar.
4. Confirm. AC may show a warning that switching loses the block tree; this is fine because we want the html as source of truth.
5. After switching, `ed_version` becomes `1` and API updates persist permanently.

Note: switching is per-message, not per-campaign. If a campaign has multiple messages (split tests), each must be switched.

### Subject and preheader are always safe

Regardless of `ed_version`, subject and preheader updates persist. These are message-level fields outside the editor's block tree. If you only need to fix a subject typo or update preview text, you do not need to worry about ed_version.

## What the helpers do

- `update_message` will happily update html on an `ed_version=3` message - it does not pre-check. **The caller is responsible for inspecting `ed_version` first.** This is by design: many edits target only subject/preheader, and a forced pre-check would be wasteful round-trips.
- `update_campaign` is unaffected by `ed_version` because it operates on campaign metadata, not message content.
- `duplicate_campaign` produces a duplicate with the same `ed_version` as the source. Duplicating an `ed_version=1` master gives an `ed_version=1` copy.

## See also

- `update-message-fields.md` - which fields persist in which mode
- `${CLAUDE_PLUGIN_ROOT}/docs/ed-version-gotcha.md` - shared cross-skill caveat document
- `${CLAUDE_PLUGIN_ROOT}/docs/superpowers/specs/2026-04-28-ac-api-quirks-and-launch-workflow.md` (in the iDD project repo) - background on the V1 vs V3 path choice and why ac-builder targets `ed_version=1`
