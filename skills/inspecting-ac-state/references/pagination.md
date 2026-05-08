# Pagination in ac-builder list commands

ActiveCampaign paginates list endpoints with `limit` and `offset` query params. ac-builder's CLI walks pagination internally - users almost never set `limit` or `offset` themselves.

## AC's pagination model

| Param | Meaning | Default | Max |
|---|---|---|---|
| `limit` | Rows per page | 20 | 100 |
| `offset` | Rows to skip | 0 | (unbounded) |

To fetch all rows from a paginated endpoint, increment `offset` by `limit` until the API returns fewer rows than `limit` (or zero rows).

The full set is not delivered in a single response on any endpoint - even on small accounts, you get exactly `limit` rows per call.

## How ac-builder handles it

The Python client `ACClient.paginate(path, key, limit=100, params=None)` yields one row at a time, walking pages transparently:

1. Issue `GET <path>?limit=100&offset=0`
2. Yield each row in `response[key]`
3. If fewer than 100 rows came back, stop
4. Otherwise, set `offset += 100` and repeat

This is hardcoded to `limit=100` (AC's max) for efficiency.

## CLI surface

| Subcommand | User-facing limit flag | Behavior |
|---|---|---|
| `list-campaigns` | `--limit N` (default 50) | Caps printed rows after pagination. Backing pagination is unbounded. |
| `list-tags` | (none) | Prints all matched rows. No client-side cap. |
| `list-automations` | (none) | Prints all rows. No client-side cap. |
| `list-addresses` | (none) | Prints all rows. No client-side cap. |

The `--limit` on `list-campaigns` is a *display* cap, not an API cap. With `--limit 50` on an account of 5000 campaigns, the CLI still iterates the first 50 rows from page 1 and stops - so it does not hammer the API. But with a server-side filter (`--name "ASIMR"`) that matches 200 campaigns, `--limit 50` still walks pages until 50 matches are printed.

## Performance notes

- Each page is one HTTP round-trip. On a 5000-tag account, `list-tags` makes 50 API calls.
- AC has a request-rate limit (default 5 req/sec for most endpoints). Rapid `list-*` runs across multiple skills may hit it.
- For one-off mass exports, prefer running once and caching the result rather than re-listing.

## Widening the cap

The only command with a CLI-facing cap is `list-campaigns`. To see everything:

```bash
uv run --directory ${CLAUDE_PLUGIN_ROOT}/scripts/python ac-builder list-campaigns --limit 9999
```

For scripts that need machine-readable structured output, call `client.paginate` directly from Python. Example pattern in `references/list-custom-fields.md`.

## What "all rows" actually means

`list-tags`, `list-automations`, and `list-addresses` print the full set returned by AC's pagination loop. There is no `--all` flag because there is no opposite mode - the default is to print everything.

## Underlying code

`ac_builder.api.v3_client.ACClient.paginate` - the pagination helper.

## See also

- `references/list-campaigns.md`
- `references/list-tags.md`
- `references/list-automations.md`
