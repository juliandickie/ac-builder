---
name: wiring-automations
description: Use when the user wants to wire or finish an ActiveCampaign automation canvas - triggers, waits, Send Email steps from existing drafts, goal islands, and the per-copy settings pass (sender, GA campaign name, Predictive Send). Automation flows cannot be created via the public API; the canvas is driven through the browser on the user's AC login, then copy settings are fixed and verified via the V3 API. Battle-tested on the iDD ASDE launch builds (July 2026).
allowed-tools: Bash, Read
argument-hint: "<automation-id or 'new'> plus the flow spec (trigger, emails in order, waits, goals)"
---

# Wiring an ActiveCampaign automation canvas

Campaigns, tags, and messages are API territory. Automation FLOWS are not - the canvas is UI-only, driven through a browser session on the user's AC login (claude-in-chrome or equivalent). This skill is the field-tested recipe for doing that without losing work, plus the API pass that fixes what the UI silently breaks.

Sequence of a full build:

1. Build the email drafts first with the `building-sequences` skill (`--apply`). Note each campaign id and message id from the build manifest.
2. Wire the canvas in the browser - trigger, actions, Send Email steps, waits, goals. See `references/canvas-recipe.md` for the exact mechanics and footguns.
3. Run the per-copy settings pass - AC copies reset the sender and drop the GA campaign name. Fix and VERIFY via the API. See `references/copy-settings-api.md`.
4. Toggle Predictive Send per copy in the UI (API cannot do this).
5. Leave the automation INACTIVE until the owner's explicit activation go.

## The five rules that prevent rework

1. **Copy each email into the automation exactly once.** The first placement uses "Start from an existing email" (creates the one copy). Every later placement of the same email - other branches, goal paths - uses "Select an email in this automation". Duplicate copies fork sender and GA edits across versions and the automation reports misleading per-email stats.

2. **Never focus text inputs with a click.** Password-manager extensions (1Password) steal the tab on input focus and every subsequent browser action errors with "Cannot access a chrome-extension:// URL". Set values by DOM query plus the native setter instead, and recover from a steal by navigating the tab back to the builder URL. Details in `references/canvas-recipe.md`.

3. **Re-screenshot before every + click.** The canvas recenters after every save, so coordinates from the previous screenshot are stale. A + click that lands on empty canvas silently desyncs the whole following panel sequence - the node is never created and later clicks hit random UI. If a JS probe reports the expected input "not found", the panel never opened; return to the canvas and redo from the +.

4. **Send-mode conventions.** The first email of a sequence (entry or purchase confirmation) sends Immediately. Every later email sends with Predictive Send. Exception - date-anchored urgency emails in the final day or two of a promotion send Immediately (Predictive spreads sends across 24 hours, which breaks deadline mechanics). Scheduled one-off closers are separate campaigns, not automation steps.

5. **One GA campaign name per reporting surface.** The GA field on each copy auto-fills with the email name, which fragments analytics. Set the shared slug (for example `asde-launch` for a launch automation, `asde-onboarding` for onboarding) on every copy - via the API, which is faster and verifiable.

## Goals in the current builder

The action panel has no "Goal" and no "End this automation" action. Both live inside **Jump To (formerly Goal)** under the Workflow tab: condition (for example Tag Exists X), "And when this action is" set to **Anywhere**, and "If the contact does not meet the conditions" set to **End this automation**. Chain goal islands after the last email - each not-met End stops pass-through contacts, so only true goal-jumpers reach the follow-up actions. Full pattern with a worked example in `references/canvas-recipe.md`.

## Verification is not optional

After wiring: re-open each goal panel and confirm condition, Anywhere, and the not-met behaviour on screen; confirm each email card shows or omits the "This email will send using Predictive Send" line per the plan; and GET every copy's campaign and message via the API to confirm GA name and sender stuck. The automation blocks endpoint returns nothing for new-builder canvases - structure is verified on screen, settings via the API.
