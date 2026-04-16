"""
Property-based tests for the chunking engine.
Run: pytest tests/test_chunking.py -v
"""
import pytest
from hypothesis import given, settings, strategies as st
from pathlib import Path
import tempfile
import frontmatter

from link_engine.stages.chunk import (
    _split_into_sections,
    _split_on_paragraphs,
    compute_chunk_hash,
)


# ── Unit Tests ────────────────────────────────────────────────────────────────

def test_simple_heading_split():
    body = """## Introduction

This is the intro section with some text.

## Second Section

This is the second section with more content to fill it out."""

    sections = _split_into_sections(body)
    assert len(sections) >= 2
    headings = [s[0] for s in sections if s[0]]
    assert "Introduction" in headings
    assert "Second Section" in headings


def test_no_headings_returns_single_section():
    body = "Just a plain paragraph without any headings."
    sections = _split_into_sections(body)
    assert len(sections) == 1
    assert sections[0][0] is None
    assert "plain paragraph" in sections[0][1]


def test_chunk_hash_is_deterministic():
    text = "Same text every time"
    assert compute_chunk_hash(text) == compute_chunk_hash(text)


def test_chunk_hash_differs_for_different_text():
    assert compute_chunk_hash("text A") != compute_chunk_hash("text B")


def test_paragraph_split_respects_max_words():
    # Create text with ~500 words
    long_text = " ".join(["word"] * 500)
    chunks = _split_on_paragraphs(long_text, char_offset=0, max_words=500)
    for chunk_text, start, end in chunks:
        word_count = len(chunk_text.split())
        assert word_count <= 500, f"Chunk too large: {word_count} words"


def test_char_start_is_non_negative():
    body = "## Heading\n\nSome content here.\n\n## Another\n\nMore content."
    sections = _split_into_sections(body)
    for _, _, char_start in sections:
        assert char_start >= 0


def test_sections_are_in_order():
    body = """## First

Content A.

## Second

Content B.

## Third

Content C."""
    sections = _split_into_sections(body)
    starts = [s[2] for s in sections]
    assert starts == sorted(starts), "Sections should be in ascending offset order"


# ── Property-Based Tests ──────────────────────────────────────────────────────

heading_strategy = st.text(
    alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd", "Zs")),
    min_size=3,
    max_size=40,
).map(lambda s: s.strip() or "Section")

paragraph_strategy = st.text(
    alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd", "Zs", "Po")),
    min_size=20,
    max_size=200,
)


@given(st.lists(
    st.tuples(heading_strategy, paragraph_strategy),
    min_size=1,
    max_size=5,
))
@settings(max_examples=50)
def test_offsets_never_negative(sections_data):
    """char_start must always be >= 0."""
    body = ""
    for heading, para in sections_data:
        body += f"## {heading}\n\n{para}\n\n"

    sections = _split_into_sections(body)
    for _, _, char_start in sections:
        assert char_start >= 0


@given(st.lists(
    st.tuples(heading_strategy, paragraph_strategy),
    min_size=2,
    max_size=5,
))
@settings(max_examples=50)
def test_offsets_are_sequential(sections_data):
    """Sections should appear in order of their char_start."""
    body = ""
    for heading, para in sections_data:
        body += f"## {heading}\n\n{para}\n\n"

    sections = _split_into_sections(body)
    starts = [s[2] for s in sections]
    assert starts == sorted(starts)


@given(paragraph_strategy)
@settings(max_examples=50)
def test_chunk_text_is_subset_of_body(para_text):
    """Every chunk's text should be found within the original body."""
    body = f"## Test Section\n\n{para_text}"
    sections = _split_into_sections(body)
    for _, text, _ in sections:
        assert text in body or text.strip() in body.replace("\n", " ")