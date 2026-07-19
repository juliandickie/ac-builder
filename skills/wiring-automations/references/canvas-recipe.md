# Canvas mechanics - the browser recipe and its footguns

Field-tested July 2026 on instituteofdigitaldentistry.activehosted.com (automations 2964 and 2965), Chrome driven via claude-in-chrome with 1Password installed. Builder URL pattern: `/app/builder/<automation-id>`.

## Text entry - the 1Password problem

Clicking a text input focuses it, which summons the 1Password inline overlay, which steals the tab: every later browser tool call errors "Cannot access a chrome-extension:// URL of different extension". The automation name editor, the GA campaign-name input, and the Jump To name input are confirmed triggers.

**Recovery** - navigate the tab back to the builder URL. Unsaved panel state is lost; redo from the + node.

**Prevention, in order of preference:**

1. Set the value WITHOUT any click - query the input in the DOM and use the native setter:

```js
const el = [...document.querySelectorAll('input')]
  .filter(i => { const r = i.getBoundingClientRect(); return r.x > 640 && r.width > 100; })
  .sort((a, b) => a.getBoundingClientRect().y - b.getBoundingClientRect().y)[0]; // topmost panel input
const set = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
set.call(el, 'THE VALUE');
el.dispatchEvent(new Event('input', { bubbles: true }));
```

2. For searchable dropdowns (condition pickers, tag pickers, the email search), a real click is needed to OPEN them, but the inner search input auto-focuses - so follow the click with a JS set on `document.activeElement` (no second click), then click the exact option text from a fresh screenshot.

3. Buttons are safe to click. Modals' Save/Create/Finish can also be clicked via JS by matching button text when a screenshot is not warranted.

Guard every `document.activeElement` write: if it is not an INPUT, the panel never opened - abort and redo rather than spraying events at a DIV.

## Coordinates go stale after every save

The canvas recenters and rezooms after each node save. Never reuse + coordinates from before a save. Symptom of a stale click: the action panel never opens, the JS probe finds no input, and no node appears (the two lost Wait nodes of 19 July). Re-screenshot, find the current +, redo.

Panning: the mouse wheel does not scroll the canvas - drag on empty canvas space. Zoom controls sit bottom-left.

## Node recipes

**Trigger (tag added)** - "Add a start trigger" -> Tag is added -> click the Tag field, JS-set the tag name fragment, click the exact suggestion, Runs defaults to Once (keep for one-shot sequences) -> Save.

**Send Email from an existing draft** - + -> Send an email -> "Start from an existing email" -> JS-set the search, click the result, Create. The settings panel opens with the copy already placed. Set the Send toggle here (Immediately or Predictive Send - UI-only, no API). Sender and GA can be fixed later via the API (see copy-settings-api.md), which is more reliable than the panel's Edit flows. Finish saves.

For a SECOND placement of the same email use the "Select an email in this automation" dropdown on the Send an email modal instead - never create a second copy.

**Wait** - + -> Workflow tab -> Wait -> "A set period of time" -> JS-set the number (guard for INPUT), unit dropdown needs a real click (minutes / hours / days / weeks) -> Save. Default is 1 day(s), so a plain days wait only needs the number set.

**If/Else date conditions** - the Current date condition supports only Is / Is Not on exact month-day-year with a per-condition timezone. No before/after operators - date ranges are OR-groups of exact dates, which forces branching by entry-date cohort. Verify every date row visually; a search-filter fragment typed into the wrong row silently changes months.

**Jump To goal (formerly Goal)** - + -> Workflow tab -> Jump To. Fill:

- Name (JS-set, no click) - convention "Goal - Purchased" style.
- Condition - click "(Select a condition)", JS-set `tag` on the auto-focused search, click "Tag", operator becomes Exists, click the value field, JS-set the tag fragment, click the suggestion.
- "And when this action is" -> **Anywhere** (real click to open, click the option).
- "If the contact does not meet the conditions" -> **End this automation** (options are Continue anyway / Wait until the conditions are met / End this automation).
- Save.

**Goal islands pattern** (replaces the classic explicit-End-then-goals layout, which this builder cannot express):

```
last email
  -> Goal - Purchased   (tag X, Anywhere, not-met End)
  -> follow-up actions  (for example Remove tag DND)
  -> Goal - Muted       (tag Y, Anywhere, not-met End)
  -> follow-up actions
  -> Goal - Booked      (tag Z, Anywhere, not-met End)
  -> Automation ends
```

Trace each persona to verify: a drip finisher hits the first goal unmatched and Ends; a goal-jumper lands at its goal, runs the actions below it, then Ends at the next goal's not-met check. Order the goals by the spec's priority.

**Remove/Add tag** - + -> Contacts tab -> Remove a tag / Add a tag -> click the field, JS-set, click the suggestion, Save.

**Activation toggle** - Active / Inactive pills top-right of the builder; verify the state visually after clicking (red dot = Inactive). Deactivating an automation is also just this toggle.

## What the API can and cannot do here

Can (see copy-settings-api.md): read the copies in a flow, fix sender and reply-to, fix the GA campaign name, rename the automation, read automation status.

Cannot: create or edit the flow structure (blocks endpoint returns empty for new-builder canvases), toggle Predictive Send, set the trigger. Those are screen work, verified on screen.
