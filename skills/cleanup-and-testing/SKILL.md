---
name: cleanup-and-testing
description: Use when the user wants to send a test email of a campaign to themselves, or delete test/probe campaigns from AC. Includes destructive `delete-campaign` which uses the action endpoint pattern `/campaigns/{id}/delete`. Always verify campaign IDs before deleting; the action is not reversible. Send-test uses V1 campaign_send for the cleanest delivery test.
allowed-tools: Bash
argument-hint: "<command> <id> [--to email@example.com]"
---

# Cleanup and testing for ActiveCampaign campaigns

Two destructive-or-delivery operations against existing AC campaigns: `send-test` (one-off test send via V1 `campaign_send`) and `delete-campaign` (V3 action-endpoint delete). Both require an existing campaign ID. Get the ID via the `inspecting-ac-state` skill first; never pass an ID guessed from name alone.

## When to use

- **Test the rendered output before mass send.** After a fresh `build-sequence` run, send the new campaign to your own inbox to confirm subject, preheader, banner, body styling, merge-field substitution, and footer all look right in real email clients (Gmail web, Apple Mail, Outlook desktop). Far more reliable than the AC preview pane.
- **Clean up probe or test campaigns.** When experimenting with the pipeline, theme tweaks, or new MJML blocks, you accumulate disposable campaigns. `delete-campaign` removes them so the live `list-campaigns` view stays focused on real launch material.
- **Remove a campaign that was misnamed or built against the wrong source.** Combined with a fresh `build-sequence` run, this is how you correct a mistake without leaving stale rows.

If the goal is to *modify* a campaign rather than test or remove it, use `editing-campaigns` for ad-hoc updates or `building-sequences` for content refreshes from MD source. Both are non-destructive.

## CLI status

Both `send-test` and `delete-campaign` are wired up as `ac-builder` CLI subcommands in v0.5. Confirmed by:

```bash
uv run --directory ${CLAUDE_PLUGIN_ROOT}/scripts/python ac-builder send-test --help
uv run --directory ${CLAUDE_PLUGIN_ROOT}/scripts/python ac-builder delete-campaign --help
```

Both take a positional `campaign_id` and one required flag (`--to <email>` for send-test, `--yes` for delete-campaign).

## send-test workflow

The send-test command pushes a one-off test send via the V1 `campaign_send` API. The recipient gets the actual rendered email - merge fields populated from their contact record (or fallback placeholders if they're not yet a contact), tracked links rewritten to AC's redirector, full HTML and text parts. Latency is typically under 60s.

### Step 1: Find the campaign ID

Use `inspecting-ac-state` to confirm the campaign exists and grab its ID:

```bash
uv run --directory ${CLAUDE_PLUGIN_ROOT}/scripts/python ac-builder list-campaigns --name "LPIS-LAUNCH-1" --limit 5
```

Output looks like `3465  LAUNCH: LPIS 2026 - E1 - Save the Date`. The first column is the ID.

### Step 2: Send the test

```bash
uv run --directory ${CLAUDE_PLUGIN_ROOT}/scripts/python ac-builder send-test 3465 --to julian@instituteofdigitaldentistry.com
```

The CLI prints `Sent campaign 3465 to julian@instituteofdigitaldentistry.com` and exits 0 on success. Wait roughly 60s, then check the inbox.

### Confirmation pattern

Before running send-test on a campaign you found by name, confirm the match. Example:

```
About to send a test of campaign 3465 'LAUNCH: LPIS 2026 - E1 - Save the Date' to julian@instituteofdigitaldentistry.com. OK?
```

This catches typos and avoids sending an experimental campaign to a real customer's address by accident.

Full V1 semantics, latency, and limitations: `references/send-test.md`.

## delete-campaign workflow

The delete-campaign command is destructive. AC has no trash, no recycle bin, and no undo. Once `succeeded: true` comes back, the campaign and its linked message are gone.

### Step 1: Confirm what you're about to delete

`get-campaign <id>` to print the full record. Verify the name matches your intent:

```bash
uv run --directory ${CLAUDE_PLUGIN_ROOT}/scripts/python ac-builder get-campaign 3489 | head -20
```

### Step 2: Get user confirmation

The skill should always pause and ask the user explicitly before issuing the delete. Pattern:

```
About to delete campaign 3489 'LAUNCH: LPIS 2026 - E1 - PROBE'. This is destructive, AC has no recovery, and the linked message will be removed too. Confirm?
```

Wait for an explicit "yes" or equivalent in the chat. Do not infer consent from a previous conversation turn.

### Step 3: Run the delete

```bash
uv run --directory ${CLAUDE_PLUGIN_ROOT}/scripts/python ac-builder delete-campaign 3489 --yes
```

The `--yes` flag is required by the CLI as a second guard - the parser rejects the call without it. Returns a JSON object with `succeeded: true` on success.

Underlying endpoint detail (action-pattern, not REST-standard `DELETE`): `references/delete-campaign.md`.

## Quick reference

| Operation | CLI subcommand | Underlying endpoint | Reference |
|---|---|---|---|
| Test send to one inbox | `send-test <id> --to <email>` | `POST /admin/api.php?api_action=campaign_send` (V1) | `references/send-test.md` |
| Delete campaign + message | `delete-campaign <id> --yes` | `DELETE /api/3/campaigns/{id}/delete` (action endpoint) | `references/delete-campaign.md` |
| Manual orphan-message cleanup | (no CLI subcommand in v0.5) | `DELETE /api/3/messages/{id}` | `references/cleanup-orphans.md` |

## Common gotchas

- **send-test requires a saved message.** If the campaign has no `message_id` (rare, but possible if a build was interrupted), the CLI prints `Campaign N has no message_id` and exits 2. Run `get-campaign` to confirm; if the message is missing, rebuild via `building-sequences` rather than trying to send.
- **send-test latency is variable.** Typical delivery is under 60s, but AC has been observed to take up to 5 minutes during heavy account-wide send activity. If nothing arrives after 5 minutes, check the AC UI Reports tab for the campaign to confirm the send was queued.
- **delete-campaign uses an action endpoint, not plain REST DELETE.** The path is `/campaigns/{id}/delete`, not `/campaigns/{id}`. Calling plain `DELETE /campaigns/{id}` returns 404. The helper handles this; only relevant if you bypass the CLI.
- **No recovery from delete.** Plan accordingly. If unsure, take a `get-campaign` snapshot to a JSON file first so you have a record of what existed.
- **Orphan messages are rare in v0.5 but possible from older Phase 1-3 data.** The V1 `message_add` path used by `building-sequences` creates messages already linked to a campaign. The legacy V3 master-and-edit pattern occasionally left dangling messages. See `references/cleanup-orphans.md` if migrating older builds.

## See also

- `inspecting-ac-state` - find a campaign ID before testing or deleting
- `building-sequences` - the build path that produces v0.5 campaigns; pair with send-test to verify renders
- `editing-campaigns` - non-destructive mutations (rename, subject tweak) when delete is too aggressive
