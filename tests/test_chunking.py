import pytest

from campusclaw.chunking import ChunkingError, chunk_text


def test_auto_chunks_with_overlap_and_offsets() -> None:
    chunks = chunk_text("甲" * 900)
    assert len(chunks) == 2
    assert chunks[0].end_offset == 800
    assert chunks[1].start_offset == 720


def test_custom_preprocessing_keeps_offsets_relative_to_prepared_text() -> None:
    chunks = chunk_text("Mail a@b.com  https://x.test  content", "custom", {"max_length": 100, "overlap_percent": 0, "remove_urls": True, "remove_emails": True, "collapse_whitespace": True})
    assert "a@b.com" not in chunks[0].text and "https://" not in chunks[0].text


def test_hierarchy_retains_heading() -> None:
    chunks = chunk_text("# Heading\n" + "x" * 900, "hierarchy")
    assert chunks[0].text.startswith("# Heading")


@pytest.mark.parametrize("options", [{"max_length": 99}, {"overlap_percent": 51}, {"separator": "comma"}])
def test_invalid_custom_options_are_rejected(options) -> None:
    with pytest.raises(ChunkingError):
        chunk_text("content", "custom", options)
