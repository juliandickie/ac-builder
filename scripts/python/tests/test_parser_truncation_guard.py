"""Tests for the in-body heading truncation guard.

Regression cover for the E6/E7 silent truncation: an in-body '### ' heading
(e.g. '### The investment') terminates body extraction in _find_next_real_h3,
dropping everything from that heading to the next section out of the rendered
email. find_in_body_section_headings surfaces such headings so the build can warn.
"""
import logging

from ac_builder.parser import find_in_body_section_headings, parse_md_text


def _section(body: str) -> str:
    return (
        "## E6 — The Investment Email\n\n"
        "**Send date:** Mon May 4, 2026\n\n"
        "### Subject Line Options\n\n"
        "1. **First option** (rationale)\n\n"
        "### Preview Text\n\n"
        '"A preview."\n\n'
        "### Email Body\n\n"
        f"{body}\n"
    )


def test_in_body_heading_is_detected():
    section = _section(
        "Here is the opening of the body.\n\n"
        "### The investment\n\n"
        "This paragraph and the closing opt-out link get silently dropped.\n\n"
        "Not the right fit? [Click here](https://instituteofdigitaldentistry.com/not-interested/?cid=%CONTACTID%) to opt out."
    )
    assert find_in_body_section_headings(section) == ["The investment"]


def test_clean_body_has_no_findings():
    section = _section(
        "A complete body with no stray in-body headings.\n\n"
        "Not the right fit? [Click here](https://instituteofdigitaldentistry.com/not-interested/?cid=%CONTACTID%) to opt out."
    )
    assert find_in_body_section_headings(section) == []


def test_multiple_in_body_headings_all_detected():
    section = _section(
        "Opening.\n\n"
        "### The investment\n\n"
        "Cut here.\n\n"
        "### What you get\n\n"
        "Also cut."
    )
    assert find_in_body_section_headings(section) == ["The investment", "What you get"]


def test_heading_after_opt_out_link_is_ignored():
    # Post-body authoring notes (### CTA, ### Technique Notes) sit AFTER the
    # opt-out link, which is the true end of a launch body. The parser strips
    # them intentionally, so they must not warn (avoids alarm fatigue: the real
    # waitlist/branch-C/global sources do this on nearly every email).
    section = _section(
        "Full body content.\n\n"
        "Not the right fit? [Click here](https://instituteofdigitaldentistry.com/not-interested/?cid=%CONTACTID%) to opt out.\n\n"
        "### CTA\n\n"
        "Hold my seat.\n\n"
        "### Technique Notes\n\n"
        "Authoring scaffolding, never sent."
    )
    assert find_in_body_section_headings(section) == []


def test_heading_before_link_caught_even_with_notes_after():
    # A heading before the opt-out link drops real content (E6/E7); trailing
    # post-link notes are still benign. Only the dangerous one is flagged.
    section = _section(
        "Opening that survives.\n\n"
        "### The investment\n\n"
        "Real content that would be silently dropped.\n\n"
        "Not the right fit? [Click here](https://instituteofdigitaldentistry.com/not-interested/?cid=%CONTACTID%) to opt out.\n\n"
        "### CTA\n\n"
        "Post-link authoring note."
    )
    assert find_in_body_section_headings(section) == ["The investment"]


def test_heading_inside_fence_is_ignored():
    # H3s inside ::: fenced blocks are body content, not a section boundary.
    section = _section(
        "Intro paragraph.\n\n"
        ":::pillars\n"
        "### Pillar One\n"
        "Fenced content stays in the body.\n"
        ":::\n\n"
        "Closing opt-out link."
    )
    assert find_in_body_section_headings(section) == []


def test_split_send_email_body_headings_are_not_flagged():
    # '### Email Body (Morning Send)' / '(Evening Send)' are recognized sections.
    section = (
        "## G12 — Split Send\n\n"
        "### Email Body (Morning Send — ~8am EST)\n\n"
        "Morning body.\n\n"
        "### Email Body (Evening Send — ~6pm EST)\n\n"
        "Evening body."
    )
    assert find_in_body_section_headings(section) == []


def test_section_without_email_body_returns_empty():
    # Non-email sections (e.g. planning blocks) should never trigger the guard.
    section = (
        "## Planning Notes\n\n"
        "### Diagnostic Statements\n\n"
        "Just notes, no email body here."
    )
    assert find_in_body_section_headings(section) == []


def test_parser_logs_warning_for_in_body_heading(caplog):
    # The guard must actually surface during a real parse, not just as a helper.
    text = (
        "# Sequence\n\n"
        "## E6 — The Investment Email\n\n"
        "### Subject Line Options\n\n"
        "1. **An option** (rationale)\n\n"
        "### Preview Text\n\n"
        '"A preview."\n\n'
        "### Email Body\n\n"
        "Opening that survives.\n\n"
        "### The investment\n\n"
        "Content that would be silently dropped."
    )
    with caplog.at_level(logging.WARNING, logger="ac_builder.parser"):
        parse_md_text(text)
    assert "The investment" in caplog.text


def test_parser_no_warning_for_clean_section(caplog):
    text = (
        "# Sequence\n\n"
        "## E6 — Clean Email\n\n"
        "### Subject Line Options\n\n"
        "1. **An option** (rationale)\n\n"
        "### Preview Text\n\n"
        '"A preview."\n\n'
        "### Email Body\n\n"
        "A complete body with no stray in-body headings."
    )
    with caplog.at_level(logging.WARNING, logger="ac_builder.parser"):
        parse_md_text(text)
    assert caplog.text == ""
