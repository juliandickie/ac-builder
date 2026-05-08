"""Tests for link action wiring (mocked AC clients)."""
from unittest.mock import MagicMock

import pytest

from ac_builder.legacy.link_actions_legacy import (
    LinkActionMap,
    LinkSpec,
    find_matching_link,
    load_link_action_map,
    resolve_tag_id,
)


def test_find_matching_link_exact():
    links = [
        {"id": "1", "link": "https://x.com/a"},
        {"id": "2", "link": "https://x.com/b"},
    ]
    assert find_matching_link(links, "https://x.com/a") == links[0]


def test_find_matching_link_handles_merge_field():
    """Merge fields like %CONTACTID% may be resolved by AC at link-tracking time."""
    links = [
        {"id": "1", "link": "https://x.com/?cid=12345"},
        {"id": "2", "link": "https://x.com/other"},
    ]
    result = find_matching_link(links, "https://x.com/?cid=%CONTACTID%")
    assert result == links[0]


def test_find_matching_link_returns_none_when_no_match():
    links = [{"id": "1", "link": "https://x.com/a"}]
    assert find_matching_link(links, "https://nope.com/x") is None


def test_resolve_tag_id_uses_existing():
    mock_client = MagicMock()
    mock_client.paginate.return_value = iter([
        {"id": "100", "tag": "INTEREST: LPIS 2026 - Engaged"},
        {"id": "200", "tag": "NOT INTERESTED: LPIS 2026"},
    ])

    cache: dict[str, int] = {}
    tag_id = resolve_tag_id(mock_client, "NOT INTERESTED: LPIS 2026", cache)
    assert tag_id == 200
    mock_client.paginate.reset_mock()
    tag_id2 = resolve_tag_id(mock_client, "NOT INTERESTED: LPIS 2026", cache)
    assert tag_id2 == 200
    mock_client.paginate.assert_not_called()


def test_resolve_tag_id_creates_when_missing():
    mock_client = MagicMock()
    mock_client.paginate.return_value = iter([])
    mock_client.post.return_value = {"tag": {"id": "999", "tag": "NEW TAG"}}

    cache: dict[str, int] = {}
    tag_id = resolve_tag_id(mock_client, "NEW TAG", cache)
    assert tag_id == 999
    mock_client.post.assert_called_once()


def test_load_link_action_map(tmp_path):
    map_path = tmp_path / "test-map.json"
    map_path.write_text("""
    {
      "theme": "lpis",
      "links": [
        {
          "label": "Not Interested",
          "match_url": "https://x.com/not-interested",
          "template": "fixtures/automations/not-interested-click.json",
          "tags": ["NOT INTERESTED: TEST"]
        }
      ]
    }
    """)
    m = load_link_action_map(map_path)
    assert isinstance(m, LinkActionMap)
    assert m.theme == "lpis"
    assert len(m.links) == 1
    assert m.links[0].label == "Not Interested"


def test_substitute_placeholders_in_template():
    from ac_builder.legacy.link_actions_legacy import substitute_template_placeholders

    template = {
        "name": "__NAME__",
        "status": "0",
        "triggers": [
            {"type": "click", "params": {"campaignid": "__CAMPAIGN_ID__", "linkid": "__LINK_ID__", "runonce": "1"}}
        ],
        "actions": [
            {"type": "tagAdd", "params": {"tag": "__TAG_ID__"}}
        ],
    }
    result = substitute_template_placeholders(
        template,
        name="My Auto",
        campaign_id=100,
        link_id=88,
        tag_ids=[55],
        end_automation_ids=[],
        start_automation_id=None,
    )
    assert result["name"] == "My Auto"
    assert result["triggers"][0]["params"]["campaignid"] == "100"
    assert result["triggers"][0]["params"]["linkid"] == "88"
    assert result["actions"][0]["params"]["tag"] == "55"


def test_substitute_multiple_tag_actions_for_multiple_tag_ids():
    from ac_builder.legacy.link_actions_legacy import substitute_template_placeholders

    template = {
        "name": "__NAME__",
        "status": "0",
        "triggers": [{"type": "click", "params": {"campaignid": "__CAMPAIGN_ID__", "linkid": "__LINK_ID__"}}],
        "actions": [{"type": "tagAdd", "params": {"tag": "__TAG_ID__"}}],
    }
    result = substitute_template_placeholders(
        template,
        name="x",
        campaign_id=1,
        link_id=2,
        tag_ids=[10, 20, 30],
        end_automation_ids=[],
        start_automation_id=None,
    )
    tag_actions = [a for a in result["actions"] if a["type"] == "tagAdd"]
    assert len(tag_actions) == 3


def test_wire_links_for_campaign_creates_automations():
    from unittest.mock import patch

    from ac_builder.legacy.link_actions_legacy import LinkActionMap, LinkSpec, wire_links_for_campaign

    mock_client = MagicMock()
    mock_client.get.return_value = {"links": [
        {"id": "88", "link": "https://idd.com/not-interested?cid=12345"},
    ]}

    mock_client.paginate.side_effect = [
        iter([{"id": "55", "tag": "NOT INTERESTED: LPIS 2026"}]),
        iter([]),
    ]

    mock_client.post.return_value = {"automation": {"id": "999"}}
    mock_client.patch.return_value = {"automation": {"id": "999", "status": "1"}}

    link_map = LinkActionMap(theme="lpis", links=[
        LinkSpec(
            label="Not Interested",
            match_url="https://idd.com/not-interested?cid=%CONTACTID%",
            template="fixtures/automations/not-interested-click.json",
            tags=["NOT INTERESTED: LPIS 2026"],
        )
    ])

    template_json = {
        "name": "__NAME__",
        "status": "0",
        "triggers": [{"type": "click", "params": {"campaignid": "__CAMPAIGN_ID__", "linkid": "__LINK_ID__", "runonce": "1"}}],
        "actions": [{"type": "tagAdd", "params": {"tag": "__TAG_ID__"}}],
    }
    with patch("ac_builder.legacy.link_actions_legacy.load_template_json", return_value=template_json), \
         patch("ac_builder.legacy.link_actions_legacy.time.sleep"):
        results = wire_links_for_campaign(
            mock_client,
            campaign_id=100,
            campaign_name="Test E1",
            link_action_map=link_map,
        )
    assert len(results) == 1
    assert results[0]["automation_id"] == 999
    assert results[0]["link_id"] == 88
