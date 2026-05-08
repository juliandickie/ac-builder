# send-test

Reference for the `send-test` CLI subcommand and its underlying V1 `campaign_send` API call. One-off test send of a campaign to a single email address. Used after `build-sequence` to verify the rendered output in real email clients before mass send.

Verified 2026-04-27 against live AC.

## CLI signature

```
ac-builder send-test <campaign_id> --to <email>
```

Both arguments required. `campaign_id` is positional, `--to` is the recipient inbox.

## Underlying transport

The CLI delegates to `ac_builder.api.campaigns_v1.campaign_send`, which hits the V1 endpoint:

```
POST /admin/api.php?api_action=campaign_send
Content-Type: application/x-www-form-urlencoded
Body params:
  email=<recipient>
  campaignid=<campaign_id>
  messageid=<message_id>
  type=html
  action=send
```

The CLI first calls V3 `get_campaign(campaign_id)` to look up `message_id` from the campaign record, then passes both IDs to V1 `campaign_send`. This is why send-test cannot be run before content is set - if `get_campaign` returns no `message_id`, the CLI exits 2 with `Campaign N has no message_id`.

## What the recipient sees

The recipient gets the actual rendered email - identical to what a launch send would produce, with one nuance around merge fields:

- **Merge fields populated from the recipient's contact record** when the recipient email matches an existing AC contact. `%FIRSTNAME|TITLECASE%` becomes their actual first name, `%LPIS_PURCHASE_DATE%` becomes their stored value, etc.
- **Merge fields fall back to AC's default placeholders** when the recipient is not yet a contact. `%FIRSTNAME|TITLECASE%` shows as `Friend` (or whatever the field default is), missing custom fields show as blank.
- **Tracked links rewritten through AC's redirector.** Click tracking is live - any clicks on the test fire real events against the campaign. This is fine for one-off internal testing but means: never send test campaigns to a list, only to a single dev/admin inbox.
- **Both HTML and text parts delivered.** The `type=html` parameter does not strip the text alternative; AC always sends multipart.
- **From-name, from-email, reply-to, subject, preheader all reflect the campaign's saved values.** No overrides in send-test.

## Latency

Typical delivery is under 60 seconds from CLI exit to inbox arrival. AC processes the V1 send synchronously - the response confirms the queue, and delivery follows on the regular send infrastructure. Observed range:

- **Best case:** 5-15 seconds (low account-wide send activity).
- **Typical:** 30-60 seconds.
- **Slow:** 2-5 minutes during peak send hours or when the account is mid-launch.

If nothing arrives after 5 minutes, check the AC UI Reports tab for the campaign. A queued-but-not-delivered send shows up there. If the report shows the send was suppressed (e.g., recipient is on the bounce list), no email will ever arrive.

## Limitations

- **Campaign must exist with a saved message.** Cannot test-send a campaign that was created but has no message attached, or one whose message has been deleted.
- **Single recipient only.** The V1 `campaign_send` accepts one email per call. To test against multiple inboxes, run send-test once per address. AC does not throttle test sends aggressively, but pacing them at one or two per minute avoids triggering rate limits.
- **Suppressions still apply.** If the recipient address is on the AC suppression list (bounced, unsubscribed, marked spam), the send will be suppressed silently. Use a fresh internal address if a previous test bounced.
- **No render preview, only delivery.** If you need to preview without sending, use the AC UI's preview pane on the campaign edit page. send-test is for end-to-end delivery testing.

## CLI examples

### Standard test send

```bash
uv run --directory ${CLAUDE_PLUGIN_ROOT}/scripts/python ac-builder send-test 3465 --to julian@instituteofdigitaldentistry.com
```

### Inspect campaign first to confirm name match

```bash
uv run --directory ${CLAUDE_PLUGIN_ROOT}/scripts/python ac-builder get-campaign 3465 | head -10
```

Confirm the printed `name` field matches what you intended, then send.

### Send a test, wait, then inspect via Python

```bash
uv run --directory ${CLAUDE_PLUGIN_ROOT}/scripts/python ac-builder send-test 3465 --to julian@instituteofdigitaldentistry.com
sleep 60
# check inbox in your mail client
```

## Behaviour notes

- **No retries on failure.** If V1 returns an error (network, auth, AC-side), the CLI prints the error and exits non-zero. Re-run the command to retry.
- **Idempotency.** Calling send-test multiple times on the same campaign+email sends multiple emails. There is no dedup. If you trigger it twice by accident, the recipient gets two copies.
- **Tracked clicks count.** Any link clicked in a test fires the same tracking event as a real recipient. For campaigns wired to link-action automations, clicking a tracked link in the test will trigger the automation. This is fine when testing the automation logic itself; surprising when only testing render.

## See also

- `delete-campaign.md` - removing a test campaign after verification
- `cleanup-orphans.md` - dealing with leftover messages from older Phase 1-3 builds
