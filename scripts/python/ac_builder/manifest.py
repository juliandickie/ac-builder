"""Build audit log: every --apply run writes a JSON manifest under .build-manifests/.

Schema:
  - Inputs: source MD, theme, template version, mjml version, ac-builder version
  - Outputs: per-email campaign IDs, message IDs, validation findings, created automations
  - Timing: started_at, completed_at

See spec section 8 for the full schema and rationale.
"""
from __future__ import annotations

import dataclasses
import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

DEFAULT_MANIFEST_ROOT = Path(__file__).resolve().parent.parent / ".build-manifests"


@dataclass
class EmailBuildRecord:
    """One email's outcome from a build run."""
    email_code: str
    campaign_name: str
    campaign_id: int | None
    message_id: int | None
    action: str  # "created" | "updated" | "skipped" | "error" | "dry-run"
    html_size_bytes: int = 0
    error: str | None = None
    validation_errors: list[str] = field(default_factory=list)
    validation_warnings: list[str] = field(default_factory=list)
    automations_created: list[dict[str, Any]] = field(default_factory=list)
    tags_created: list[str] = field(default_factory=list)


@dataclass
class BuildManifest:
    """Top-level audit record for one build run."""
    source_md: str
    theme: str
    template_used: str
    template_version: str
    mjml_version: str
    ac_builder_version: str
    footer_mode: str
    command_line: str
    started_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: datetime | None = None
    source_md_sha256: str = ""
    results: list[EmailBuildRecord] = field(default_factory=list)

    def add_result(self, record: EmailBuildRecord) -> None:
        self.results.append(record)

    def fingerprint_source(self, source_path: Path) -> None:
        """Compute and store sha256 of the source MD for traceability."""
        if source_path.exists():
            self.source_md_sha256 = hashlib.sha256(source_path.read_bytes()).hexdigest()

    def to_dict(self) -> dict[str, Any]:
        d = dataclasses.asdict(self)
        d["started_at"] = self.started_at.isoformat()
        if self.completed_at:
            d["completed_at"] = self.completed_at.isoformat()
        return d


class ManifestStore:
    """Reads and writes manifest JSON files under a date-partitioned directory."""

    def __init__(self, root: Path | None = None) -> None:
        self.root = root or DEFAULT_MANIFEST_ROOT

    def write(self, manifest: BuildManifest) -> Path:
        if manifest.completed_at is None:
            manifest.completed_at = datetime.now(timezone.utc)

        date_dir = self.root / manifest.started_at.strftime("%Y-%m-%d")
        date_dir.mkdir(parents=True, exist_ok=True)

        stem = Path(manifest.source_md).stem or "build"
        timestamp = manifest.started_at.strftime("%H%M%S")
        path = date_dir / f"{stem}-{timestamp}.json"

        with path.open("w") as f:
            json.dump(manifest.to_dict(), f, indent=2, default=str)
        return path


def list_manifests(*, root: Path | None = None, since_days: int = 7) -> list[Path]:
    """List manifest files modified within the last N days, newest first."""
    root = root or DEFAULT_MANIFEST_ROOT
    if not root.exists():
        return []
    cutoff = datetime.now() - timedelta(days=since_days)
    matches: list[Path] = []
    for path in root.rglob("*.json"):
        if datetime.fromtimestamp(path.stat().st_mtime) >= cutoff:
            matches.append(path)
    return sorted(matches, key=lambda p: p.stat().st_mtime, reverse=True)
