# cleanup-orphans

Reference for handling orphan messages in ActiveCampaign. An orphan is a row in the `/messages` table that has no parent campaign - usually because the campaign was deleted but the message was not, or a legacy build flow created the message standalone before linking it.

Orphans are mostly a Phase 1-3 era concern. The v0.5 V1 `message_add` build path links messages to campaigns at creation time, so the workflow rarely produces them.

## Why orphans happen

### v0.5 (current build path) - rare

The v0.5 pipeline uses V1 `campaign_create` followed by V1 `message_add`, where `message_add` is invoked with the just-created `campaign_id`. The message row is created already linked. Deleting the campaign via `delete-campaign` removes the linked message in the same action (see `delete-campaign.md`). So in normal v0.5 operation, orphans should not accumulate.

The exception is a half-built campaign: if a `build-sequence` run aborts mid-way (network error, rate limit, etc.) after the campaign is created but before message_add completes, you can end up with a campaign that has no message OR with no campaign that references a created message. The CLI's idempotent rebuild typically resolves these by re-running, but a leftover row may remain.

### Phase 1-3 (legacy) - more common

The pre-v0.5 flow used a master-and-edit pattern with V3 endpoints: create a "master" campaign with one boilerplate message, then duplicate the master per email and edit each duplicate's content. The duplicate path created new message rows linked to new campaigns, but if a master campaign was deleted while duplicates still referenced its content, message references could go stale.

Additionally, the V3 `messages` endpoint allows creating standalone messages not linked to any campaign. Some Phase 1-3 experiments used this to seed templates. Those messages are technically orphans by default until manually linked.

## Detection

There is no built-in CLI subcommand in v0.5 for listing orphans. Detection is a manual cross-reference between the `/messages` and `/campaigns` endpoints.

### Manual detection via Python

```bash
uv run --directory ${CLAUDE_PLUGIN_ROOT}/scripts/python python -c "
from ac_builder.api.v3_client import ACClient
client = ACClient()

# Collect all message IDs referenced by campaigns
campaign_msg_ids = set()
for camp in client.paginate('campaigns', 'campaigns'):
    msg_id = camp.get('messageid') or camp.get('message_id')
    if msg_id:
        campaign_msg_ids.add(int(msg_id))

# Walk messages, flag any not referenced
for msg in client.paginate('messages', 'messages'):
    mid = int(msg['id'])
    if mid not in campaign_msg_ids:
        print(f\"orphan message {mid}: {msg.get('subject', '(no subject)')!r}\")
"
```

This prints the ID and subject of any message not currently referenced by a campaign. Review the output before deleting anything - some standalone messages may be intentional (e.g., reusable templates created for Phase 1-3).

## Manual cleanup

### Delete an orphan message via Python

```bash
uv run --directory ${CLAUDE_PLUGIN_ROOT}/scripts/python python -c "
from ac_builder.api.v3_client import ACClient
client = ACClient()
response = client.delete('messages/19234')
print(response)
"
```

`DELETE /messages/{id}` is the REST-standard delete here (not an action endpoint). Verified shape: returns an empty body on success, 404 on already-deleted.

### Confirmation pattern

Before deleting any orphan message, confirm with the user. Pattern:

```
Found orphan message 19234 with subject 'LPIS 2026 master template'.
This is not referenced by any current campaign. Delete?
```

Wait for explicit confirmation. Some "orphans" are deliberate template seeds.

## Notes on the action endpoint

Unlike `delete-campaign` (which uses the action-endpoint pattern `/campaigns/{id}/delete`), message deletion is plain REST `DELETE /messages/{id}`. There is no `/messages/{id}/delete` action variant.

## When NOT to clean up orphans

- **The account has not been migrated from Phase 1-3.** If older builds still need access to legacy template messages, skip orphan cleanup until migration is complete.
- **You are mid-launch.** A scheduled launch may have a campaign in "scheduled" state where the message link looks orphaned to a snapshot but is actually pending wire-up. Wait until launch activity is quiet.
- **The orphan looks like a template seed.** AC supports reusable message templates that are intentionally not bound to a campaign. Subject line containing "template" or "master" is a hint - confirm with the user before deleting.

## CLI subcommand status

Adding a `cleanup-orphans` CLI subcommand is a useful future enhancement but not implemented in v0.5. Currently this is a Python one-liner workflow, documented above.

## See also

- `delete-campaign.md` - the supported delete path for campaigns; deletes their linked messages too
- `send-test.md` - testing campaigns; producing test campaigns is the main path that yields orphans worth cleaning later
