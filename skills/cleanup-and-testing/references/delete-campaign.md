# delete-campaign

Reference for the `delete-campaign` CLI subcommand and its underlying V3 action-endpoint API call. Destructive operation - removes a campaign and its linked message permanently. AC has no recovery mechanism, so the workflow includes a confirmation flow.

Verified 2026-04-27 against live AC.

## CLI signature

```
ac-builder delete-campaign <campaign_id> --yes
```

Both arguments required. The `--yes` flag is enforced by `argparse` (`required=True`) so the parser refuses to invoke the command without explicit confirmation. This is the second guard, after the user-confirmation prompt in the skill workflow.

## Underlying transport

The CLI delegates to `ac_builder.api.campaigns_v3.delete_campaign`, which hits:

```
DELETE /api/3/campaigns/{id}/delete
Response: {"succeeded": bool, "message": str}
```

This is an **action-endpoint pattern**, not the REST-standard `DELETE /campaigns/{id}`. Calling plain `DELETE /campaigns/{id}` (without the `/delete` suffix) returns 404. AC's V3 API uses action-endpoint deletes for several resources; this is one of them.

The helper docstring records the verification: "Verified 2026-04-27 against live AC instance."

## Confirmation flow

The skill's documented workflow always includes a user-confirmation step before the actual delete call. Pattern:

```
About to delete campaign 3489 'LAUNCH: LPIS 2026 - E1 - PROBE'.
This is destructive, AC has no recovery, and the linked message will be removed too.
Confirm?
```

Wait for an explicit "yes", "confirm", or equivalent in the chat before running the CLI. Do not infer consent from the original task framing - even if the user said "delete the test campaigns", confirm each campaign individually so you catch any name match that surprises them.

The CLI's `--yes` flag is a separate, second guard. It does not replace the chat-level confirmation; it just makes accidental deletion harder if the command leaks into shell history or a script.

## What gets deleted

- **The campaign record itself** - removed from the `/campaigns` list. Subsequent `get-campaign <id>` returns 404.
- **The campaign's linked message** - the row in `messages` referenced by `campaign.message_id` is also deleted. This is bundled into the same action.
- **Send-event records (reports, opens, clicks, bounces).** AC archives these but they no longer surface against the deleted campaign.
- **Automation links to the campaign.** If the campaign was attached as a Send Email step in an automation, the link breaks. AC handles this by leaving the step orphaned, which can cause silent failures in the automation flow. Best practice: detach the campaign from any automation before deleting.

## What does NOT get deleted

- **Tags applied to contacts** by the campaign's link-action automations. Those persist on contacts.
- **Templates** based on the campaign's HTML are not deleted.
- **The list the campaign was sent to.** Lists are untouched.

## Recovery

**There is no recovery.** AC offers no:

- Trash or recycle bin for campaigns.
- Soft-delete with a restore window.
- Undo button.
- Admin-side recovery option.

If you delete a campaign that turns out to be needed, the only path forward is to rebuild it from the source MD via `building-sequences`. If the source MD is also gone, the content is unrecoverable.

For destructive cleanup of important-looking campaigns: take a `get-campaign <id>` snapshot to a JSON file first as a record of what existed.

## CLI examples

### Standard delete with confirmation

After confirming with the user in chat:

```bash
uv run --directory ${CLAUDE_PLUGIN_ROOT}/scripts/python ac-builder delete-campaign 3489 --yes
```

Returns:

```json
{
  "succeeded": true,
  "message": "Campaign deleted"
}
```

### Snapshot before delete

```bash
uv run --directory ${CLAUDE_PLUGIN_ROOT}/scripts/python ac-builder get-campaign 3489 > /tmp/campaign-3489-backup.json
uv run --directory ${CLAUDE_PLUGIN_ROOT}/scripts/python ac-builder delete-campaign 3489 --yes
```

The JSON snapshot includes name, message_id, html, subject, preheader, from-fields, addressid - enough to reconstruct manually if needed (though not link-action automation wiring, which lives separately).

### Bulk delete pattern (one ID at a time, with confirmation each)

There is no bulk-delete subcommand in v0.5. To remove several test campaigns:

```bash
uv run --directory ${CLAUDE_PLUGIN_ROOT}/scripts/python ac-builder list-campaigns --name "PROBE" --limit 50
# review the list with the user
# for each ID confirmed, run:
uv run --directory ${CLAUDE_PLUGIN_ROOT}/scripts/python ac-builder delete-campaign <id> --yes
```

Loop is intentionally manual - bulk-deleting by name pattern is a foot-gun.

## Behaviour notes

- **Active campaigns can be deleted.** AC does not gate delete-campaign by status (draft, scheduled, sent). This is fine for cleanup of test sends but means a slip-up against a live launch campaign is possible. The confirmation flow exists for this reason.
- **Idempotency.** Re-running delete-campaign against an already-deleted ID returns 404 (campaign not found). The CLI surfaces the error and exits non-zero.
- **No reason field.** Unlike some AC endpoints, delete-campaign does not record a reason or note. The action is invisible after the fact.

## See also

- `send-test.md` - testing campaigns; usually the workflow that produces probe campaigns worth deleting later
- `cleanup-orphans.md` - dealing with messages left behind by old Phase 1-3 builds
