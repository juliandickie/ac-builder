"""Tests for build manifest write/read."""
import json
from pathlib import Path

import pytest

from ac_builder.manifest import (
    BuildManifest,
    EmailBuildRecord,
    ManifestStore,
    list_manifests,
)


@pytest.fixture
def tmp_store(tmp_path):
    return ManifestStore(root=tmp_path)


def test_write_manifest_creates_dated_file(tmp_store, tmp_path):
    manifest = BuildManifest(
        source_md="output/sample.md",
        theme="lpis",
        template_used="promo.mjml",
        template_version="1.0.0",
        mjml_version="4.15.3",
        ac_builder_version="0.4.0",
        footer_mode="launch",
        command_line="ac-builder build-sequence sample.md --apply",
    )
    manifest.add_result(EmailBuildRecord(
        email_code="E1",
        campaign_name="E1 - Test",
        campaign_id=100,
        message_id=200,
        action="created",
        html_size_bytes=50000,
    ))
    path = tmp_store.write(manifest)
    assert path.exists()
    assert path.parent.name == manifest.started_at.strftime("%Y-%m-%d")


def test_manifest_round_trip(tmp_store):
    m = BuildManifest(
        source_md="x.md",
        theme="lpis",
        template_used="promo.mjml",
        template_version="1.0.0",
        mjml_version="4.15.3",
        ac_builder_version="0.4.0",
        footer_mode="launch",
        command_line="x",
    )
    m.add_result(EmailBuildRecord(
        email_code="E1", campaign_name="X", campaign_id=1, message_id=2,
        action="created", html_size_bytes=1000,
    ))
    path = tmp_store.write(m)

    with path.open() as f:
        data = json.load(f)
    assert data["source_md"] == "x.md"
    assert data["theme"] == "lpis"
    assert data["results"][0]["email_code"] == "E1"


def test_list_manifests_filters_by_since(tmp_store):
    m1 = BuildManifest(
        source_md="a.md", theme="lpis", template_used="promo.mjml",
        template_version="1.0.0", mjml_version="4.15.3",
        ac_builder_version="0.4.0", footer_mode="launch", command_line="x",
    )
    tmp_store.write(m1)
    found = list_manifests(root=tmp_store.root, since_days=30)
    assert len(found) >= 1


def test_email_build_record_with_validation_warnings():
    rec = EmailBuildRecord(
        email_code="E1",
        campaign_name="X",
        campaign_id=1,
        message_id=2,
        action="created",
        html_size_bytes=1000,
    )
    rec.validation_errors.append("missing-alt-text: foo.jpg")
    rec.validation_warnings.append("subject-mobile-truncation: subject is 38 chars")
    assert rec.validation_errors == ["missing-alt-text: foo.jpg"]


def test_email_build_record_with_automations():
    rec = EmailBuildRecord(
        email_code="E1", campaign_name="X", campaign_id=1, message_id=2,
        action="created", html_size_bytes=1000,
    )
    rec.automations_created.append({
        "automation_id": 5,
        "trigger": "click",
        "link_id": 88,
        "tags_applied": [105],
        "label": "Not Interested",
    })
    assert len(rec.automations_created) == 1
