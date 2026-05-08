# get-campaign

Fetches a single campaign in full and prints it as JSON. Useful for inspecting `message_id`, `addressid`, send statistics, schedule, and links.

## Invocation

```bash
uv run --directory ${CLAUDE_PLUGIN_ROOT}/scripts/python ac-builder get-campaign <campaign_id>
```

The campaign ID is a positional argument (integer). No flags.

## Output format

Pretty-printed JSON envelope. Top level keys typically include `campaign`, `links`, `campaignMessage`, plus expansions of related resources (lists, messages, etc.). Truncated example:

```json
{
  "campaign": {
    "type": "single",
    "userid": "1",
    "segmentid": "0",
    "bounceid": "-1",
    "realcid": "0",
    "sendid": "1",
    "threadid": "0",
    "seriesid": "1",
    "formid": "0",
    "basetemplateid": "6f553c5a1d501c4debf58c48d756787bb3ec799c",
    "basemessageid": "0",
    "addressid": "1",
    "source": "web",
    "name": "Welcome to Intro to CADCAM",
    "cdate": "2018-05-09T20:23:15-05:00",
    "mdate": "2018-05-09T20:37:46-05:00",
    "sdate": "2018-05-09T20:37:46-05:00",
    "ldate": "2018-05-09T20:42:09-05:00",
    "send_amt": "1",
    "total_amt": "1",
    "opens": "20",
    "uniqueopens": "1",
    "linkclicks": "2",
    "uniquelinkclicks": "1"
  }
}
```

## Key fields

| Field | Use |
|---|---|
| `name` | Confirms which campaign was returned |
| `type` | `single`, `recurring`, `responder`, etc. |
| `addressid` | The sender physical address - cross-reference with `list-addresses` |
| `seriesid` | Hashed message ID used by V1 send endpoints (`message_id` for `send-test`) |
| `cdate` | Created at |
| `sdate` | Scheduled or sent at |
| `ldate` | Last interaction date |
| `send_amt` / `total_amt` | Number of contacts sent / total set |
| `opens` / `uniqueopens` | Open counts |
| `linkclicks` / `uniquelinkclicks` | Click counts |
| `hardbounces` / `softbounces` | Bounce counts |

## Common patterns

### Pipe through `jq` for a specific field

```bash
uv run --directory ${CLAUDE_PLUGIN_ROOT}/scripts/python ac-builder get-campaign 3465 | jq '.campaign.name'
```

### Extract `message_id` for use with `send-test`

```bash
uv run --directory ${CLAUDE_PLUGIN_ROOT}/scripts/python ac-builder get-campaign 3465 | jq '.campaign.message_id'
```

### Verify a campaign was scheduled correctly

```bash
uv run --directory ${CLAUDE_PLUGIN_ROOT}/scripts/python ac-builder get-campaign 3465 | jq '{name: .campaign.name, sdate: .campaign.sdate, status: .campaign.status}'
```

### Audit address ID across campaigns

Combine with `list-campaigns`:

```bash
for id in $(uv run --directory ${CLAUDE_PLUGIN_ROOT}/scripts/python ac-builder list-campaigns --name "AUNZ" --limit 50 | awk '{print $1}'); do
  uv run --directory ${CLAUDE_PLUGIN_ROOT}/scripts/python ac-builder get-campaign $id | jq -r '"\(.campaign.id) \(.campaign.addressid) \(.campaign.name)"'
done
```

## Limitations

- Returns the V3 raw envelope unchanged - field names match AC's API and many are stringified integers.
- Does not return the rendered HTML body. To get HTML, call `client.get(f"messages/{message_id}")` from Python or look at the AC UI.
- No verbose / quiet modes - the JSON is always full.
- An invalid ID returns a non-zero exit and prints an error from `ACClient.get`.

## Underlying API

`GET /api/3/campaigns/<id>`. Implemented in `ac_builder.api.campaigns_v3.get_campaign`.

## See also

- `references/list-campaigns.md` - to find the ID first
- `references/pagination.md`
