# The ed_version gotcha

This is the shared cross-skill caveat referenced from `building-sequences/SKILL.md` and `editing-campaigns/SKILL.md`. If you only read one thing about ActiveCampaign before driving its API, read this.

## The behaviour

When AC's modern editor (`ed_version=3`) opens a message, it regenerates the `html` and `text` fields from its internal block tree. Any `html` or `text` we set via `PUT /messages/{id}` gets silently overwritten the next time the message is opened or saved in the AC UI. The API call succeeds. The data is recorded. Then it disappears.

This is not a bug from AC's perspective - the modern editor treats the block tree as the source of truth and the html/text fields as a render. But for anyone driving the API, it is the single most painful surprise in the platform.

## What persists in modern editor

These are stored at the message level, not in the block tree, so they stick regardless of `ed_version`:

- `subject`
- `preheader_text`
- `fromname`
- `fromemail`
- `reply2`

If your edit is a subject typo or a preview text tweak, you can ignore everything else in this document.

## What gets reverted in modern editor

These are regenerated from the block tree on every editor open or save:

- `html`
- `text`

Updating either of these via API on an `ed_version=3` message is a no-op as soon as the message is touched in the UI.

## The fix: target classic editor (`ed_version=1`)

Messages we create via V1 `message_add` start at `ed_version=None`; once linked to a campaign they show as `ed_version=1` (classic). The classic editor reads `html` directly with no block-tree fight - API updates persist permanently.

This is why ac-builder's `building-sequences` skill builds via V1: it produces `ed_version=1` campaigns by construction, and any subsequent V3 PUT to update html/text on those campaigns sticks.

## How to tell which version a message is on

Run `get-message` via Python (the CLI does not expose a dedicated subcommand for this in v0.5):

```bash
uv run --directory ${CLAUDE_PLUGIN_ROOT}/scripts/python python -c "
from ac_builder.api.messages_v3 import get_message
from ac_builder.api.v3_client import ACClient
m = get_message(ACClient(), 123)['message']
print(f\"ed_version={m.get('ed_version')} subject={m.get('subject')!r}\")
"
```

Or check the message detail view in the AC UI - the editor type is shown in the breadcrumb / template info.

## The 1-click escape hatch

If you have a message stuck on `ed_version=3`, opening it in AC's UI and choosing "switch to classic designer" downgrades it to `ed_version=1`. After the switch, future API updates to html/text persist.

The block tree gets discarded as part of the switch, so the current rendered html becomes the canonical content. This is fine if your last UI save reflects the state you want to preserve; just be aware that any structural editing you'd do via the modern designer is gone.

## What ac-builder does automatically

- The V1 build path (used by `building-sequences`) always produces `ed_version=1` messages. **Safe by default.**
- For ad-hoc edits via the `editing-campaigns` skill, the SKILL doc and `references/ed-version-quirks.md` instruct you to call `get_message` first to inspect `ed_version` before any html/text update.
- `messages_v3.update_message()` itself does **not** pre-check `ed_version`. It will happily PUT html updates to an `ed_version=3` message and AC will accept the call. The bug surfaces later when the editor next renders. This is by design - many edits target only subject/preheader (which are safe regardless), and a forced pre-check would be a wasteful round-trip.

In practice this means: when you write code on top of `update_message`, *you* are the one responsible for the `ed_version` pre-check if you're touching html or text. The skill prompts and reference docs walk you through this; the API helper does not enforce it.

## Why this matters for stranger users

This gotcha was discovered late in Phase 1-3 testing (April 27-28, 2026) and is the reason ac-builder uses V1 for creation rather than the V3 master-and-edit pattern that earlier prototypes relied on. Before the V1 path was added, every `ed_version=3` message required manual UI intervention to downgrade before API updates would persist.

If you're migrating from manual AC UI workflows where the modern designer is the default, expect to either:

1. **Switch your team to using ac-builder's V1 path (recommended).** Build campaigns from MD source via `building-sequences`. Edit via `editing-campaigns`. You never see `ed_version=3` because nothing you create lands there.
2. **Manually downgrade existing `ed_version=3` campaigns before API updates.** One-click switch to classic designer in the AC UI, then API updates work normally.

If you're forking ac-builder for a non-AC platform, this whole document is moot - it's specific to ActiveCampaign's two-editor architecture. The takeaway is the general principle: when an API field has a "rendered from a hidden source of truth" relationship with another representation, treat it as read-mostly.

## See also

- `skills/editing-campaigns/references/ed-version-quirks.md` - tactical guide for ad-hoc editing, including step-by-step downgrade instructions
- `skills/building-sequences/SKILL.md` - the skill that builds via V1 (safe path)
- `skills/editing-campaigns/SKILL.md` - the skill that wraps V3 PUT operations
- `docs/architecture.md` - V1 vs V3 split rationale and how it ties into the rest of the build pipeline