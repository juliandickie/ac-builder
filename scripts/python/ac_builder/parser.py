"""Parse source markdown files containing email sequences.

The expected MD structure for each email is:

    ## E1 — Title of the Email (Optional Themeplate Code)

    **Send date:** Mon Apr 27, 2026
    **Send to:** Audience description
    **Themeplate:** TP01
    **Job:** One-line job description

    ### Subject Line Options

    1. **First subject line option** (rationale in parens)
    2. **Second subject line option** (rationale)
    3. **Third subject line option** (rationale)

    ### Preview Text

    "Preview text in quotes."

    ### Email Body

    The body content in markdown,
    spanning multiple paragraphs,
    until the next ## heading or `---` divider.

The H2 heading uses an em-dash separator (—, U+2014). The code prefix can
be anything matching `[\\w-]+` (e.g., E1, WL-1, C1, G1, LPIS-OB-1).
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class SequenceMetadata:
    """Document-level fields appearing before the first email H2 section.

    Extracted from the file header (everything between the H1 title and the
    first email's `## CODE — Title` heading). Common fields:

    - `campaign_name`: e.g., "implant-pathway-2026-aunz" (the GA utm_campaign slug)
    - `send_dates`: human-readable date range
    - `voice`: email voice/persona
    - `audience`: who the sequence goes to
    """

    title: str = ""
    """The H1 heading of the file."""

    fields: dict[str, str] = field(default_factory=dict)
    """All `**field:** value` pairs found in the document header."""

    @property
    def campaign_name(self) -> str:
        """The 'Campaign name' field if present (the utm_campaign slug).

        Handles two project conventions in the field key:
        - `Campaign name:` (used in the AU/NZ launch MDs)
        - `AC Campaign name:` (used in onboarding/abandon-cart/transition MDs)
        Backticks (which AC's MD format wraps slugs in) are stripped.
        """
        raw = (
            self.fields.get("campaign_name")
            or self.fields.get("ac_campaign_name")
            or ""
        )
        return raw.strip("`")


@dataclass
class EmailDef:
    """One email parsed from a source MD file."""

    code: str
    """Short code e.g. 'E1', 'WL-1', 'C1', 'G1', 'LPIS-OB-1'."""

    title: str
    """Title after the em-dash, e.g. 'Segmentation Call-Out (TP1 Exclusively Empowered)'."""

    subject_lines: list[str]
    """Subject line options, in order. Usually 3."""

    preview_text: str
    """Preview / preheader text. Quotes stripped."""

    body_md: str
    """Raw markdown body content. Excludes the H3 heading."""

    metadata: dict[str, str] = field(default_factory=dict)
    """Optional fields like send_date, send_to, themeplate, job."""

    @property
    def full_name(self) -> str:
        """Campaign-friendly name: 'E1 - Segmentation Call-Out (TP1 Exclusively Empowered)'."""
        return f"{self.code} - {self.title}"

    @property
    def primary_subject(self) -> str:
        """First subject line option (the recommended one). Empty if none parsed."""
        return self.subject_lines[0] if self.subject_lines else ""


_H1_PATTERN = re.compile(r"^#\s+(?P<title>.+?)\s*$", re.MULTILINE)
_H2_PATTERN = re.compile(
    r"^##\s+(?P<code>[\w-]+)\s+[—-]\s+(?P<title>.+?)\s*$",
    re.MULTILINE,
)
_METADATA_PATTERN = re.compile(
    r"^\*\*(?P<key>[A-Za-z][A-Za-z\s\-]*?):\*\*\s+(?P<value>.+?)\s*$",
    re.MULTILINE,
)
_SUBJECT_LINE_PATTERN = re.compile(
    r"^\d+\.\s+\*\*(?P<subject>.+?)\*\*",
    re.MULTILINE,
)


def parse_md_file(path: str | Path) -> list[EmailDef]:
    """Parse a source MD file into a list of EmailDef objects.

    For document-level metadata (e.g., the sequence's `Campaign name` slug),
    use parse_md_file_with_metadata() instead.

    Args:
        path: Path to the MD file.

    Returns:
        List of EmailDef, one per email section in the file.

    Raises:
        FileNotFoundError if path doesn't exist.
        ValueError if no email sections found (file may not match expected format).
    """
    _, emails = parse_md_file_with_metadata(path)
    return emails


def parse_md_file_with_metadata(
    path: str | Path,
) -> tuple[SequenceMetadata, list[EmailDef]]:
    """Parse a source MD file. Returns sequence-level metadata + emails.

    The sequence metadata is extracted from the file header (the `**field:** value`
    lines appearing between the H1 title and the first email section). Useful
    fields include `campaign_name` (the GA utm_campaign slug).

    Args:
        path: Path to the MD file.

    Returns:
        Tuple of (SequenceMetadata, list[EmailDef]).
    """
    text = Path(path).read_text(encoding="utf-8")
    return parse_md_text_with_metadata(text)


def parse_md_text(text: str) -> list[EmailDef]:
    """Parse markdown text directly into EmailDef objects.

    Splits the text into H2-delimited sections, then parses each one.
    """
    _, emails = parse_md_text_with_metadata(text)
    return emails


def parse_md_text_with_metadata(text: str) -> tuple[SequenceMetadata, list[EmailDef]]:
    """Parse markdown text. Returns sequence-level metadata + emails."""
    # Find all H2 positions to split sections
    h2_positions = [(m.start(), m) for m in _H2_PATTERN.finditer(text)]
    if not h2_positions:
        raise ValueError(
            "No H2 email sections found in the source. Expected format: "
            "'## CODE — Title' (with em-dash separator)."
        )

    # Document header is everything before the first H2
    header_end = h2_positions[0][0]
    header = text[:header_end]
    metadata = _parse_sequence_header(header)

    emails: list[EmailDef] = []
    for i, (start, match) in enumerate(h2_positions):
        end = h2_positions[i + 1][0] if i + 1 < len(h2_positions) else len(text)
        section = text[start:end]
        try:
            # _parse_section returns a list; usually one item, multiple for split-sends.
            for email in _parse_section(section, match.group("code"), match.group("title")):
                emails.append(email)
        except ValueError as exc:
            # Skip sections that don't have all required fields - e.g. summary sections
            # with H2 headings that aren't actual emails.
            code = match.group("code")
            if not _looks_like_email_section(section):
                continue
            raise ValueError(f"Failed to parse section starting with '## {code}': {exc}") from exc

    return metadata, emails


def _parse_sequence_header(header: str) -> SequenceMetadata:
    """Extract document-level metadata from text before the first H2."""
    title_match = _H1_PATTERN.search(header)
    title = title_match.group("title").strip() if title_match else ""

    fields = {
        m.group("key").strip().lower().replace(" ", "_"): m.group("value").strip()
        for m in _METADATA_PATTERN.finditer(header)
    }

    return SequenceMetadata(title=title, fields=fields)


def _looks_like_email_section(section: str) -> bool:
    """Heuristic: a real email section must contain '### Email Body' or '### Subject Line'."""
    return "### Email Body" in section or "### Subject Line" in section


def _parse_section(section: str, code: str, title: str) -> list[EmailDef]:
    """Parse one email H2 section into one or more EmailDef objects.

    Most sections produce one EmailDef. Split-send sections (with multiple
    `### Email Body (...)` blocks) produce one EmailDef per body, with codes
    suffixed by a/b/c and titles annotated with the body's label.

    Args:
        section: Raw section text from the H2 line through to the next H2 or end.
        code: Email code (e.g., 'E1') from the H2 match.
        title: Email title (after the em-dash) from the H2 match.

    Returns:
        List of EmailDef. Length 1 for typical single-body sections, length 2+
        for split-send sections like G12 with morning + evening bodies.

    Raises:
        ValueError if no body sections found or all are empty.
    """
    metadata = _extract_metadata(section)
    subject_lines = _extract_subject_lines(section)
    preview_text = _extract_preview_text(section)

    for heading in find_in_body_section_headings(section):
        logger.warning(
            "Email %s: in-body '### %s' heading after '### Email Body' will silently "
            "truncate the rendered body there. Convert it to bold (**...**) or another "
            "non-H3 style. (Regression guard for the E6/E7 truncation.)",
            code, heading,
        )

    body_blocks = _extract_all_body_blocks(section)

    if not body_blocks:
        raise ValueError("'### Email Body' section not found or empty")

    if len(body_blocks) == 1:
        # Standard single-body case.
        return [
            EmailDef(
                code=code,
                title=title,
                subject_lines=subject_lines,
                preview_text=preview_text,
                body_md=body_blocks[0]["body"],
                metadata=metadata,
            )
        ]

    # Split-send: emit one EmailDef per body block, suffixed a, b, c, ...
    results: list[EmailDef] = []
    for i, block in enumerate(body_blocks):
        suffix = chr(ord("a") + i)
        new_code = f"{code}{suffix}"
        new_title = f"{title} ({block['label']})" if block["label"] else f"{title} (part {suffix})"
        results.append(
            EmailDef(
                code=new_code,
                title=new_title,
                subject_lines=subject_lines,
                preview_text=preview_text,
                body_md=block["body"],
                metadata=metadata,
            )
        )
    return results


def _extract_metadata(section: str) -> dict[str, str]:
    """Extract **key:** value pairs that appear before the first H3."""
    # Stop scanning at the first ### heading
    h3_idx = section.find("\n### ")
    scope = section[:h3_idx] if h3_idx > 0 else section

    return {
        m.group("key").strip().lower().replace(" ", "_"): m.group("value").strip()
        for m in _METADATA_PATTERN.finditer(scope)
    }


def _extract_subject_lines(section: str) -> list[str]:
    """Find '### Subject Line Options' block and extract the bolded subjects."""
    block = _extract_h3_block(section, "Subject Line Options")
    if not block:
        return []
    return [m.group("subject").strip() for m in _SUBJECT_LINE_PATTERN.finditer(block)]


def _extract_preview_text(section: str) -> str:
    """Find '### Preview Text' block and return the text (stripped of surrounding quotes)."""
    block = _extract_h3_block(section, "Preview Text")
    if not block:
        return ""
    # The preview is the first non-empty line
    for line in block.strip().splitlines():
        line = line.strip()
        if line:
            # Strip surrounding double quotes (smart or straight)
            for quote in ('"', "“", "”"):
                if line.startswith(quote):
                    line = line[1:]
                if line.endswith(quote):
                    line = line[:-1]
            return line.strip()
    return ""


def _extract_body(section: str) -> str:
    """Find the (single) '### Email Body' block and return it as raw markdown.

    For split-send sections with multiple bodies, use _extract_all_body_blocks().
    """
    blocks = _extract_all_body_blocks(section)
    return blocks[0]["body"] if blocks else ""


def _extract_all_body_blocks(section: str) -> list[dict[str, str]]:
    """Find every '### Email Body' block in a section, including split-send
    variants like '### Email Body (Morning Send — ~8am EST)'.

    Returns a list of dicts with keys:
      - 'label': the parenthetical annotation if present (e.g., 'Morning Send'),
                 stripped of whitespace. Empty string for plain '### Email Body'.
      - 'body': the markdown body content (trailing whitespace + `---` stripped).
    """
    pattern = re.compile(
        r"^###\s+Email Body(?:\s*\((?P<label>.+?)\))?\s*$",
        re.MULTILINE,
    )
    matches = list(pattern.finditer(section))
    if not matches:
        return []

    results: list[dict[str, str]] = []
    for m in matches:
        body_start = m.end()
        # Body extends until the next H3 (any kind), the next H2, or end of section.
        # H3s inside ::: fenced blocks (e.g. :::pillars ... :::) are part of
        # the body, not a new section boundary - skip past them.
        rest = section[body_start:]
        body_end = _find_next_real_h3(rest)
        body = rest[:body_end].strip()
        if body.endswith("---"):
            body = body[:-3].strip()
        if not body:
            continue
        label = (m.group("label") or "").strip()
        results.append({"label": label, "body": body})
    return results


_FENCE_OPEN_RE = re.compile(r"^[ \t]*:::[a-zA-Z][a-zA-Z0-9_-]*[ \t]*$", re.MULTILINE)
_FENCE_CLOSE_RE = re.compile(r"^[ \t]*:::[ \t]*$", re.MULTILINE)


def _find_next_real_h3(text: str) -> int:
    """Find the byte offset of the next H3 in `text` that is NOT inside a
    ::: fenced block.

    Returns len(text) if no such H3 exists. Used by _extract_all_body_blocks
    to treat `:::pillars ... :::` (and any future fenced-block syntax) as
    opaque to email-section boundary detection.
    """
    h3_re = re.compile(r"^###\s+", re.MULTILINE)
    for match in h3_re.finditer(text):
        if not _is_inside_fence(text, match.start()):
            return match.start()
    return len(text)


def _is_inside_fence(text: str, position: int) -> bool:
    """True if `position` falls between an open ::: fence and its close."""
    before = text[:position]
    open_count = len(_FENCE_OPEN_RE.findall(before))
    close_count = len(_FENCE_CLOSE_RE.findall(before))
    # Each open fence is also matched by close (since both start with :::),
    # so the close pattern counts BOTH opens and closes. Subtract opens to
    # get pure closes.
    pure_closes = close_count - open_count
    return open_count > pure_closes


_ANY_H3_RE = re.compile(r"^###\s+(?P<heading>.+?)\s*$", re.MULTILINE)
_RECOGNIZED_SECTION_PREFIXES = ("Subject Line Options", "Preview Text", "Email Body")
_NOT_INTERESTED_MARKER = "/not-interested/"


def find_in_body_section_headings(section: str) -> list[str]:
    """Return dangerous in-body '### ' headings that truncate real body content.

    An in-body '### ' heading silently terminates body extraction (see
    _find_next_real_h3), dropping everything from it to the next section out of
    the rendered email - the E6/E7 truncation, where an in-body '### The
    investment' ended the body and dropped the closing opt-out link.

    The opt-out link (/not-interested/) is the true end of a launch body, so only
    headings appearing BEFORE that link drop real content; headings AFTER it strip
    post-body authoring notes (### CTA, ### Technique Notes) that are excluded by
    design. We therefore flag a heading only when it falls between '### Email Body'
    and the opt-out link (or, if no link is present in the section, anywhere after
    '### Email Body' - a missing link is itself a truncation signal). Recognized
    section headings (Subject Line Options, Preview Text, Email Body, including
    split-send 'Email Body (Morning Send)' variants) and headings inside ::: fenced
    blocks are never flagged. Returns each offender's heading text (without the
    leading '### '), in document order. Returns [] when there is no '### Email Body'.
    """
    body_match = re.search(r"^###\s+Email Body\b", section, re.MULTILINE)
    if body_match is None:
        return []
    link_pos = section.find(_NOT_INTERESTED_MARKER, body_match.start())
    boundary = link_pos if link_pos != -1 else len(section)
    offenders: list[str] = []
    for m in _ANY_H3_RE.finditer(section):
        if m.start() < body_match.start() or m.start() >= boundary:
            continue
        heading = m.group("heading").strip()
        if heading.startswith(_RECOGNIZED_SECTION_PREFIXES):
            continue
        if _is_inside_fence(section, m.start()):
            continue
        offenders.append(heading)
    return offenders


def _extract_h3_block(section: str, heading: str) -> str:
    """Extract the body following a specific H3 heading, until the next H3 or end.

    Tolerates trailing parenthetical annotations on the heading. Example:
    `### Email Body (Morning Send - ~8am EST)` matches when heading="Email Body".
    For split-send emails with multiple bodies, the FIRST matching block is
    returned. Currently the orchestrator builds one campaign per email section,
    so only one body is used; for split-sends, the user can manually clone the
    duplicate via the AC UI for the second send.
    """
    # Match the H3 line where the heading appears at the start, optionally
    # followed by whitespace + parenthetical content (e.g., "(Morning Send)").
    pattern = re.compile(
        rf"^###\s+{re.escape(heading)}(?:\s*\(.*?\))?\s*$",
        re.MULTILINE,
    )
    match = pattern.search(section)
    if not match:
        return ""

    body_start = match.end()
    # Find the next H3 (or end of section)
    next_h3 = re.search(r"^###\s+", section[body_start:], re.MULTILINE)
    if next_h3:
        return section[body_start : body_start + next_h3.start()]
    return section[body_start:]
