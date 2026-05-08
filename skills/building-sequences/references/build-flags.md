# Build flags reference

Every CLI flag of `ac-builder build-sequence`, with what it does, an example value, when to use it, and what happens if omitted.

## Required-with-defaults

These are technically optional on the CLI because they fall back to env vars from `~/.config/ac-builder/config.env`. If the env var is unset and the flag is omitted, the orchestrator errors at startup.

### `--list-id <int>`

The AC list ID. The campaign's compliance footer is rendered against this list (sender address, unsubscribe handling). Note: the list scope is for footer rendering only - the automation flow that delivers the campaign decides actual recipients.

- Example: `--list-id 1`
- Default: `AC_DEFAULT_LIST_ID` env var
- Multi-list: repeat the flag (`--list-id 1 --list-id 2`)
- When omitted (and no env): error

### `--from-name '...'`

Sender display name in the inbox.

- Example: `--from-name "Your Name | Your Brand"`
- Default: `AC_DEFAULT_FROM_NAME` env var
- When omitted (and no env): error

### `--from-email '...'`

Sender email address. Must be a verified sender in your AC account.

- Example: `--from-email "hello@yourdomain.com"`
- Default: `AC_DEFAULT_FROM_EMAIL` env var
- When omitted (and no env): error

## Theme

### `--theme {auto|<name>|<path.json>}`

How to resolve the theme that controls colours, fonts, banner, and CTA detection patterns.

- Example: `--theme lpis` (named) or `--theme ./themes/custom.json` (path)
- Default: filename inference (see `theme-resolution.md`)
- When omitted: file-level theme is auto-inferred; per-email `**Theme:**` field can override

## Filtering

### `--emails E1,E2,E3`

Build only the listed email codes. Comma-separated, no spaces. Useful for iterating on a single email without re-applying the whole sequence.

- Example: `--emails E1,E2`
- Default: build all emails in the source MD
- When omitted: full sequence is built

## Sender / reply

### `--reply-to <email>`

Reply-To header. When users hit reply, this is the address that receives the reply.

- Example: `--reply-to "support@yourdomain.com"`
- Default: `AC_DEFAULT_REPLY_TO` env var, then falls back to `--from-email`
- When omitted (and no env): replies go to from-email

### `--address-id <int>`

The ID of a saved physical address in your AC account's address library. Renders in the compliance footer (CAN-SPAM requires a postal address).

- Example: `--address-id 5`
- Default: `AC_DEFAULT_ADDRESS_ID` env var, then `0` (account default)
- When omitted: account-default address used

## Tracking

### `--track-link-domain <domain>`

Custom click-tracking domain (sub-domain that you've configured to track at AC). Replaces AC's default tracking domain in tracked links.

- Example: `--track-link-domain links.yourdomain.com`
- Default: AC account default tracking domain
- When omitted: AC default

### `--utm-campaign <slug>`

The campaign-name identifier for tracking purposes. Renders in tracked URLs as a campaign tag. Overrides the `Campaign name:` from the source MD header.

- Example: `--utm-campaign launch-2026-q1`
- Default: `Campaign name:` value parsed from MD header
- When omitted: MD value used; if MD doesn't have one, AC's default scheme

### `--archive {public|private}`

Sets the campaign's archive privacy in AC's web archive feature.

- Example: `--archive private`
- Default: AC account default
- When omitted: account default applies

## Footer

### `--footer-mode {launch|onboarding|transactional|auto}`

Controls which footer template renders at the bottom of the email.

- `launch` - full marketing footer including unsubscribe, preferences, three-action CTA pattern (Interest/Not Interested/Already Bought), sender address
- `onboarding` - reduced footer for paying-customer post-purchase emails. AC's mandatory unsubscribe link still shows; opt-out CTAs do not.
- `transactional` - minimal compliance footer for transactional emails
- `auto` - infer from filename: launch sequences default to `launch`, onboarding files to `onboarding`, etc.

- Example: `--footer-mode onboarding`
- Default: `auto`
- When omitted: auto-inference based on filename

## Header / banner

### `--header-image-url <url>`

Override the banner image URL (otherwise the theme's default banner is used).

- Example: `--header-image-url https://cdn.yourdomain.com/banner.jpg`
- Default: theme banner
- When omitted: theme default

### `--header-image-alt <text>`

Alt text for the banner image. The validator requires non-empty alt text on all images.

- Example: `--header-image-alt "Q1 Launch banner"`
- Default: theme banner alt text
- When omitted: theme default

### `--header-image-link <url>`

Make the banner image clickable to a URL.

- Example: `--header-image-link https://yourdomain.com/landing`
- Default: not clickable, or theme default if set
- When omitted: theme default

## Validation

### `--no-check`

Skip pre-send validation. Use sparingly - the validator catches compliance issues, broken merge fields, missing alt text, non-https image URLs, etc. Reserved for occasions where you've already validated externally and want to push through one known-WARN finding.

- Example: `--no-check`
- Default: validation runs
- When omitted: validation runs

## Apply mode

### `--apply`

Required to commit changes to AC. Without it, the orchestrator runs the entire pipeline including the dry-run validation table, but does NOT call AC's create or update endpoints. Always dry-run first.

- Example: `--apply`
- Default: dry-run mode
- When omitted: dry-run only

## Defaults summary

If you set up `~/.config/ac-builder/config.env` with `AC_DEFAULT_LIST_ID`, `AC_DEFAULT_FROM_NAME`, `AC_DEFAULT_FROM_EMAIL`, the daily command becomes:

```bash
uv run --directory ${CLAUDE_PLUGIN_ROOT}/scripts/python ac-builder build-sequence path/to/sequence.md --apply
```

Themes auto-infer from filename, footer auto-infers from filename, address comes from account default, validation runs by default. Most fine-tuning flags only need to be passed when overriding the defaults.
