# Idempotency reference

How `build-sequence` decides whether to create a new campaign or update an existing one, and what that means for re-runs, manual edits, and renames.

## Match key: campaign name

The orchestrator matches existing AC campaigns by exact name. The campaign name is composed from:

1. The sequence-level title (from the MD H1 or campaign-name field)
2. The email code (E1, E2, ...)
3. The email title (from the H2 line)

Resulting in something like:

```
implant-pathway-2026-iidf-branch-c - C1 - IIDF Course Introduction
```

This name is set on the AC campaign at create time and used as the lookup key on every subsequent run.

## Decision tree per email

For each email in the source MD, the orchestrator runs:

```
GET /campaigns?filters[name]=<computed_name>
```

Then branches:

- **Existing match found** -> route to V3 PUT update path
  - V3 PUT to `/messages/{id}` updates subject, preheader, html, text
  - V3 PUT to `/campaigns/{id}` updates name, list scope, sender details
  - The action column shows `updated`
- **No match** -> route to V1 from-scratch create path
  - V1 `POST /admin/api.php?api_action=message_add` creates the message
  - V1 `POST /admin/api.php?api_action=campaign_create` creates the campaign and links it to the message
  - The action column shows `created`

## Re-runs are safe

Edit the source MD, re-run with `--apply`, and existing campaigns get the new content via the PUT path. No duplicate explosion, no "01" / "02" suffixes appearing in AC, no orphaned messages.

```bash
# First apply: 5 emails, all create
ac-builder build-sequence sequence.md --list-id 1 --from-name "..." --from-email "..." --apply

# Edit E2 in the MD, re-run
ac-builder build-sequence sequence.md --list-id 1 --from-name "..." --from-email "..." --apply

# Output:
# E1: updated (no change but PUT runs)
# E2: updated (new content)
# E3-E5: updated (no change)
```

## Manual edits get clobbered

This is the main consequence to keep in mind. If you build E1 via API, then open it in the AC editor and tweak the subject, then re-run `--apply`, the API run overwrites your manual edit.

**Recommendation:** build via API first, polish in the UI last. If you must hand-edit a campaign in AC after building, freeze the source MD (don't re-run for that email) or use `--emails` to filter that email out of subsequent runs:

```bash
ac-builder build-sequence sequence.md --list-id 1 --from-name "..." --from-email "..." --emails E2,E3,E4,E5 --apply
```

This builds E2-E5 and leaves E1 untouched, preserving any UI edits.

## Renames in AC break the match

If you rename a campaign in the AC UI from `... - C1 - IIDF Course Introduction` to `... - C1 - Renamed`, the orchestrator can no longer find it on the next run (since it searches by the old name). The next `--apply` for that email creates a NEW campaign with the original name, leaving the renamed one in place.

To clean up:

1. Either rename the AC campaign back to the original computed name
2. Or delete the renamed campaign from AC
3. Or delete the new fresh-create from AC and rename the original back

If you need to permanently change the campaign-display-name in AC, edit the source MD's H2 line so the computed name matches your desired AC name. Then the next `--apply` updates the matched-by-old-name campaign in place. (You'll need to manually rename the existing AC campaign to the new name first; otherwise the orchestrator creates a new one.)

## Inspecting the manifest

Each `--apply` writes a JSON manifest to `.build-manifests/YYYY-MM-DD/`. The manifest records:

- Source MD path
- Theme name and resolution path
- Per-email rows: code, action, campaign_id, message_id, validation summary, timestamps

To inspect:

```bash
uv run --directory ${CLAUDE_PLUGIN_ROOT}/scripts/python ac-builder list-builds --since 7d
```

Or filter by theme:

```bash
ac-builder list-builds --since 30d --theme lpis
```

The manifest lets you reconstruct exactly what was built, when, and which campaign IDs were touched. Useful for audit and debugging. See the `verifying-setup` skill for more.

## Edge cases

- **Two emails with the same H2 title in one MD** -> they collide on the computed name. The first one is created; the second updates the first instead of creating a separate campaign. Make H2 titles unique.
- **Same campaign name across different MD files** -> the orchestrator can't tell them apart. Two source MDs with the same `Campaign name:` and overlapping email codes will overwrite each other's campaigns. Keep `Campaign name:` values unique per sequence.
- **Soft-deleted AC campaigns** -> AC's "delete" usually moves to a trash list, not a hard delete. If a campaign was deleted in AC and the orchestrator's search returns the deleted campaign, the V3 PUT may fail. Workaround: use `--emails <code>` to skip the offending email, or hard-delete the campaign in AC first.
- **Campaign name truncation** -> AC truncates long campaign names. If two computed names share a prefix and exceed AC's limit, they may collide post-truncation. Keep H2 titles concise (<60 chars after the email code).
