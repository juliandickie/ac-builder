# The per-copy settings pass - what copies break and how the API fixes it

When a draft campaign is added to a Send Email step, AC creates a COPY (name suffixed `- (Copy-<id>)`). The copy keeps subject, preheader, and body but **resets From/reply-to to the account default and drops the Google Analytics campaign name**. Every copy needs a settings pass, and the API path is faster and verifiable versus clicking through six panels.

All calls use the V3 API with the `Api-Token` header (credentials resolve from `~/.config/ac-builder/config.env` - note the env var names are `AC_API_URL` and `AC_API_KEY`, and the file contains unquoted spaces, so parse it with python-dotenv rather than shell `source`).

## 1. Enumerate the copies in a flow

```
GET /api/3/automations/{automation_id}/campaigns
```

Returns each copy's campaign id, name, and current `analytics_campaign_name`. This is also the dedup check - if the same email appears twice, someone copied it twice; delete the extra and reuse via "Select an email in this automation".

## 2. Fix sender and reply-to (messages PUT - proven)

Campaign -> message id first (`basemessageid` is 0 on V1-created campaigns, so always go via campaignMessages):

```
GET /api/3/campaigns/{campaign_id}/campaignMessages   -> messageid
PUT /api/3/messages/{message_id}
{"message": {"fromname": "...", "fromemail": "...", "reply2": "..."}}
```

Best practice - read the sender off the ORIGINAL draft's message (ids in the build manifest under `.build-manifests/`) and copy it onto the automation copy's message, so the spec stays the single source of truth.

## 3. Fix the GA campaign name (campaigns PUT - proven 19 Jul 2026)

```
PUT /api/3/campaigns/{campaign_id}
{"campaign": {"analytics_campaign_name": "asde-launch"}}
```

Returns 200 and persists (the UI's GA Customize modal shows the new value). Use ONE shared slug per reporting surface so sends aggregate in GA - per-email names are the default failure mode because the UI auto-fills the field with the email name.

## 4. Rename the automation (automations PUT - proven 19 Jul 2026)

```
PUT /api/3/automations/{automation_id}
{"automation": {"name": "ONBOARDING: ASDE"}}
```

This avoids the builder's name editor entirely (a confirmed 1Password tab-steal trigger). The GET response's `status` field also confirms activation state (1 active, 2 inactive).

## 5. Verify by GET, always

A 200 on PUT is a status line, not proof. Re-GET the message and campaign and print the resulting fromname / fromemail / reply2 / analytics_campaign_name per copy. The 19 July pattern:

```python
for code, cid in COPIES.items():
    # PUT sender, PUT GA ...
    after_m = requests.get(f"{BASE}/api/3/messages/{mid}", headers=H).json()["message"]
    after_c = requests.get(f"{BASE}/api/3/campaigns/{cid}", headers=H).json()["campaign"]
    print(code, after_m["fromname"], after_m["fromemail"], after_m["reply2"],
          after_c["analytics_campaign_name"])
```

## Still UI-only after this pass

- **Setting Predictive Send vs Immediately** - the Send toggle in each copy's settings panel. Convention: first email Immediately, the rest Predictive, final-day urgency emails Immediately.
- Flow structure, triggers, goals - see canvas-recipe.md.

## Verifying the whole thing in one API read

`GET /api/3/automations/{automation_id}/blocks` (response key `automationBlocks`) exposes every block's params - `send` blocks carry `sendtype` (`"imm"` / `"opt"` = Predictive) and `campaignid`, `wait` blocks the duration, `goal` blocks name/position/unmet, tag blocks their tagIds. One read verifies send modes, wiring order, and goal settings without reopening a single panel. Full schema in `docs/api-capability-map.md`.
