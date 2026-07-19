# AC API capability map - audited 19 July 2026

Empirical audit of the ActiveCampaign V3 API surface on a live account (instituteofdigitaldentistry, US1), run because the plugin's assumptions dated from April 2026. Method: GET sweep with `limit=1` across candidate resources, empty-body POST probes for method existence, and field-writability PUTs against a throwaway PROBE campaign (created and deleted by the audit - drafts never send, and no status field was ever changed).

## Corrections to prior assumptions

| Old assumption | Reality |
|---|---|
| Automation canvas structure is not readable via API | It is - `GET /api/3/automations/{id}/blocks` returns the full canvas. The response key is `automationBlocks`, NOT `blocks`; parsing the wrong key is why it looked empty. |
| Predictive Send state is UI-only to verify | Readable per send block - `params.sendtype` is `"imm"` (Immediately) or `"opt"` (Predictive). Goal blocks expose `position` ("anywhere"), `unmet` ("end"), and `name`. Structural verification of a wired automation is now an API one-liner. |
| GA campaign name and automation rename are UI-only | Both writable - `PUT /api/3/campaigns/{id}` (`analytics_campaign_name`), `PUT /api/3/automations/{id}` (`name`). Proven July 2026. |

## Block schema (from live reads)

`GET /api/3/automations/{id}/blocks` -> `automationBlocks[]`, each with `id`, `ordernum`, `type`, `params`:

- `start` - `{"starts": ["<trigger id>"]}`
- `send` - `{"campaignid": N, "sendtype": "imm"|"opt", "emailname": "..."}`
- `wait` - `{"waittype": "for", "waittime": N, "waitdurt": "hour"|"day", ...}`
- `addtag` / `removetag` - `{"tagIds": ["<tag id>"]}`
- `goal` - `{"name": "...", "position": "anywhere", "unmet": "end", "segmentid": N, ...}`

**Goal conditions are stored as HIDDEN UNNAMED SEGMENTS** - each goal's `segmentid` points to a segment with an empty name. Never bulk-delete unnamed segments; they are load-bearing goal conditions.

## Campaign fields confirmed writable on drafts (PUT /api/3/campaigns/{id})

`name`, `analytics_campaign_name`, `tracklinks`, `embed_images`, and `sdate` (stored ISO in the account timezone). Writing `sdate` on a draft does NOT schedule it - `status` stayed 0 throughout the audit. Whether flipping `status` schedules a send was deliberately NOT probed (a mistake there emails a real list); if API scheduling is ever needed for date-anchored closers, test the status flip on a campaign attached to a verified zero-contact list first.

## Message fields confirmed writable (PUT /api/3/messages/{id})

`fromname`, `fromemail`, `reply2` (proven in production settings passes). Message ids come from `GET /api/3/campaigns/{id}/campaignMessages` (`basemessageid` is 0 for V1-created campaigns).

## Method-existence results

| Probe | Result | Meaning |
|---|---|---|
| POST /api/3/automations | 405 | Automations still cannot be created via API |
| POST /api/3/campaigns | 405 | Campaign creation stays on the V1 API (the plugin's path) |
| POST /api/3/goals | 405 | Goal definitions read-only |
| POST /api/3/segments | **201 on an EMPTY body** | Segments ARE creatable via API - and validation is absent, an empty POST creates a blank segment. Never probe this endpoint with empty bodies (the audit's stray was deleted, id 2377). Serialized segment conditions format still to be mapped before using this for real (read an existing segment built in the UI as the template). |
| POST /api/3/webhooks | 422 field_missing | Webhooks creatable via API with a valid payload |
| PUT/POST /api/3/automationBlocks | 422 "Invalid block" | Routes EXIST (not 405) - canvas blocks may be writable with valid payloads. Unproven. If ever explored, only against a scratch automation created in the UI for that purpose, never a live one. |

## Readable resources confirmed (GET, 200)

campaigns, messages, automations (+ /blocks, /campaigns, /contactAutomations, /goals nested), tags, lists, contacts, segments, contactAutomations, emailActivities, campaignLists, campaignMessages, addresses, users, groups, forms, templates, brandings, configs, siteTrackingDomains, webhooks, goals, automationBlocks, bounceLogs, links, contactGoals, dealGroups.

Not available on this account/plan: schemas (404), customObjects (400), notifications (404), seriesHooks (404), blocks (404 - use automationBlocks).

## Audit hygiene notes

- Empty-body POST is NOT a safe method probe on this API - segments (and possibly others) create objects with zero validation. Probe method existence with PUT against a nonexistent id instead (404/422 = route exists, 405 = method absent).
- Ordering params can be silently ignored (`orders[id]` on segments) - fetch tails via `offset = total - n`, never trust the sort.
- Every write was verified by re-GET; every probe object (segment 2377, campaign 3717 with its message) was deleted and confirmed 404.
