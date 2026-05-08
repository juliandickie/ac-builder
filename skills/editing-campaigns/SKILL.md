---
name: editing-campaigns
description: Use when the user wants to mutate an existing AC campaign or message - rename, change subject/preheader, swap from-address, update analytics_campaign_name, or duplicate a campaign as a starting point for a new one. Most edits go through V3 PUT endpoints. The modern editor (ed_version=3) reverts html/text changes on save; classic editor (ed_version=1) accepts them. The 'building-sequences' skill is preferred for bulk content updates from MD source; this skill is for ad-hoc tweaks.
allowed-tools: Bash
argument-hint: "<command> <id> [field=value ...]"
---

# Editing campaigns and messages in ActiveCampaign

Ad-hoc mutations to existing campaigns and messages: renames, subject/preheader tweaks, from-address swaps, analytics_campaign_name updates, and campaign duplication. The underlying transport is V3 `PUT` endpoints for both `/campaigns/{id}` and `/messages/{id}`. There is one important quirk that bites every operator at least once - see "ed_version gotcha summary" below.

## When to use this skill vs building-sequences

This skill is for ad-hoc, UI-style edits to campaigns or messages already in AC. Examples:

- "Fix the subject line on campaign 3465 - typo in the date."
- "Rename campaign 3489 to match the new naming convention."
- "Duplicate the LPIS-LAUNCH-1 master campaign as a starting point for a fresh October version."
- "Swap the from-address on these three campaigns to the new sender."

If the goal is bulk-updating content from a refreshed markdown source - rerunning a full sequence after edits to `output/emails-au-nz/AUNZ_Main_Sequence_E1_to_E20.md`, for instance - prefer `building-sequences`. It is idempotent by name: existing campaigns get V3 PUT updates, new ones get V1 creates, and the master-and-edit pattern is built in. This skill skips that orchestration in exchange for one-shot precision.

There is also `inspecting-ac-state` for read-only lookups - find an ID before editing - and `capturing-link-actions` for click-action automation work. None of those overlap with this skill's mutating role.

## ed_version gotcha summary

Messages in AC carry an `ed_version` field that records which editor created them. **`ed_version=1` (classic) accepts API updates to `html` and `text` permanently. `ed_version=3` (modern designer) regenerates `html`/`text` from an internal block tree on next editor open, silently reverting your update.** Subject and preheader stick in both modes; body content does not.

**Before updating `html` or `text` on a message, check `ed_version` first.** The V1 message_add path used by `building-sequences` always produces `ed_version=1`, so any campaign built by ac-builder is safe. Campaigns built through AC's modern designer in the UI default to `ed_version=3` and need either a switch to classic designer (one-click in the AC UI) or to be rebuilt fresh.

Full detail: `references/ed-version-quirks.md`. Cross-skill caveat: `${CLAUDE_PLUGIN_ROOT}/docs/ed-version-gotcha.md` (shared between `editing-campaigns` and `building-sequences`).

## CLI status: not a CLI subcommand in v0.5

**None of `update-campaign`, `update-message`, `duplicate-campaign`, or `get-message` are exposed as `ac-builder` CLI subcommands in v0.5.** Confirmed by:

```bash
uv run --directory ${CLAUDE_PLUGIN_ROOT}/scripts/python ac-builder --help
```

The current subcommand set is `render`, `check`, `build-sequence`, `capture-automation`, `list-builds`, `send-test`, `verify`, `list-campaigns`, `get-campaign`, `delete-campaign`, `list-tags`, `list-automations`, `list-addresses`. No update or duplicate verbs.

The Python helpers exist - `ac_builder.api.campaigns_v3.update_campaign`, `duplicate_campaign`, `ac_builder.api.messages_v3.update_message`, and `get_message` are implemented and verified against live AC. We just call them through `uv run python -c '...'` rather than a dedicated subcommand. Pattern below.

Adding the four subcommands is straightforward and would be a useful follow-up. Until then, the workflows are Python one-liners.

## Per-command workflows

### update-campaign

Updates top-level campaign metadata: name, fromname, fromemail, reply2, analytics_campaign_name, addressid, public, basemessageid. None of these are message-body fields - those are on the Message, not the Campaign.

```bash
uv run --directory ${CLAUDE_PLUGIN_ROOT}/scripts/python python -c "
from ac_builder.api.v3_client import ACClient
from ac_builder.api.campaigns_v3 import update_campaign
client = ACClient()
result = update_campaign(client, 3465, name='LAUNCH: LPIS 2026 - E1 - Save the Date')
print(result)
"
```

Each parameter is keyword-only and optional - send only what you want to change. Full field reference: `references/update-campaign-fields.md`.

### update-message

Updates fields on a Message (the email itself): subject, preheader_text, html, text, fromname, fromemail, reply2. **Check `ed_version` before touching `html` or `text`** (see ed_version gotcha above).

```bash
uv run --directory ${CLAUDE_PLUGIN_ROOT}/scripts/python python -c "
from ac_builder.api.v3_client import ACClient
from ac_builder.api.messages_v3 import get_message, update_message
client = ACClient()

# Step 1: inspect ed_version before editing
msg = get_message(client, 19234)
print('ed_version:', msg.get('message', {}).get('ed_version'))

# Step 2: update if safe (subject and preheader always safe)
result = update_message(client, 19234, subject='Save the date - LPIS 2026 enrolment opens Monday')
print(result)
"
```

Subject and preheader updates are always safe regardless of `ed_version`. Full field reference: `references/update-message-fields.md`.

### duplicate-campaign

Two-step copy + rename. AC's `POST /campaigns/{id}/copy` ignores the `name` field and always returns a campaign called "<original> (Copy)". The helper does the rename in step 2 via `update_campaign`.

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

**Important restriction:** campaigns inside an active automation cannot be duplicated. AC returns 400 "not allowed to copy this campaign". Detach from the automation first, copy, then re-attach. Detail: `references/duplicate-campaign.md`.

### get-message (read-only, used as ed_version pre-check)

Not a mutation but listed here because every `update-message` call should be preceded by a `get_message` to inspect `ed_version`:

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

If `ed_version` is `1` or `None`, `update_message` calls persist. If `3`, only subject / preheader / from-fields persist; `html` and `text` will revert.

## Quick reference

| Operation | Helper function | Underlying endpoint | Reference |
|---|---|---|---|
| Rename or update metadata | `campaigns_v3.update_campaign` | `PUT /campaigns/{id}` | `references/update-campaign-fields.md` |
| Update subject / preheader / body | `messages_v3.update_message` | `PUT /messages/{id}` | `references/update-message-fields.md` |
| Inspect `ed_version` | `messages_v3.get_message` | `GET /messages/{id}` | `references/ed-version-quirks.md` |
| Duplicate a campaign | `campaigns_v3.duplicate_campaign` | `POST /campaigns/{id}/copy` then `PUT` | `references/duplicate-campaign.md` |

## Common gotchas

- **`update_message` on `ed_version=3` reverts body content.** Subject and preheader are safe; html and text will be regenerated from the editor's block tree on next save in the AC UI. Always `get_message` first.
- **Campaigns in automations cannot be duplicated.** AC returns 400. Detach, duplicate, re-attach.
- **`update_campaign` requires at least one field.** Calling it with no keyword arguments raises `ValueError`. Same for `update_message`.
- **`addressid` updates affect CAN-SPAM footer.** When swapping the physical address, confirm `list-addresses` returns the new one before pointing at it.
- **`fromname` / `fromemail` update on the campaign does not propagate to its messages automatically.** If you change the campaign-level from-address, also update the message-level `fromname` and `fromemail` to match.

## See also

- `building-sequences` - the orchestrated path for bulk content updates from MD source
- `inspecting-ac-state` - read-only lookups (find IDs before editing)
- `capturing-link-actions` - capturing automation JSON templates for click-action wiring
