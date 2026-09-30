"""Deterministic, side-effect-free material chunking."""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any


class ChunkingError(ValueError):
    pass


@dataclass(frozen=True)
class Chunk:
    index: int
    text: str
    start_offset: int
    end_offset: int


def _windows(text: str, size: int = 800, overlap: int = 80, separator: str = "auto") -> list[tuple[str, int, int]]:
    if not text:
        return []
    result: list[tuple[str, int, int]] = []
    start = 0
    while start < len(text):
        limit = min(len(text), start + size)
        end = limit
        if limit < len(text):
            fragment = text[start:limit]
            groups = {
                "auto": (("\n\n",), ("\n",), ("。", "！", "？", ".", "!", "?")),
                "blank_line": (("\n\n",),),
                "newline": (("\n",),),
                "sentence": (("。", "！", "？", ".", "!", "?"),),
            }[separator]
            threshold = max(size // 2, overlap + 1)
            for tokens in groups:
                candidates = [(fragment.rfind(token), len(token)) for token in tokens]
                boundary, token_length = max(candidates)
                if boundary >= threshold:
                    end = start + boundary + token_length
                    break
        if end <= start:
            end = min(len(text), start + size)
        result.append((text[start:end], start, end))
        if end == len(text):
            break
        start = max(start + 1, end - overlap)
    return result


def _preprocess(text: str, options: dict[str, Any]) -> str:
    if options.get("remove_urls"):
        text = re.sub(r"https?://\S+", "", text)
    if options.get("remove_emails"):
        text = re.sub(r"\b[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}\b", "", text)
    if options.get("collapse_whitespace"):
        text = re.sub(r"\s+", " ", text).strip()
    return text


def _validate_custom(options: dict[str, Any]) -> tuple[int, int]:
    size = options.get("max_length", 800)
    overlap_percent = options.get("overlap_percent", 10)
    if isinstance(size, bool) or not isinstance(size, int) or not 100 <= size <= 2000:
        raise ChunkingError("max_length must be between 100 and 2000")
    if isinstance(overlap_percent, bool) or not isinstance(overlap_percent, int) or not 0 <= overlap_percent <= 50:
        raise ChunkingError("overlap_percent must be between 0 and 50")
    if options.get("separator", "sentence") not in {"newline", "blank_line", "sentence"}:
        raise ChunkingError("unsupported separator")
    for flag in ("remove_urls", "remove_emails", "collapse_whitespace"):
        if flag in options and not isinstance(options[flag], bool):
            raise ChunkingError(f"{flag} must be a boolean")
    return size, size * overlap_percent // 100


def chunk_text(body: str, strategy: str = "auto", options: dict[str, Any] | None = None) -> list[Chunk]:
    """Split text by a documented strategy and return offsets of its actual input."""
    if not isinstance(body, str) or not body:
        raise ChunkingError("body must be non-empty text")
    options = options or {}
    if strategy == "auto":
        pieces = _windows(body)
    elif strategy == "custom":
        size, overlap = _validate_custom(options)
        prepared = _preprocess(body, options)
        pieces = _windows(prepared, size, overlap, options.get("separator", "sentence"))
    elif strategy == "hierarchy":
        starts = [match.start() for match in re.finditer(r"(?m)^#{1,3}\s+.+$", body)]
        if starts and starts[0] != 0:
            starts.insert(0, 0)
        starts.append(len(body))
        if len(starts) == 1:
            pieces = _windows(body)
        else:
            pieces = []
            for start, end in zip(starts, starts[1:]):
                section = body[start:end]
                for text, relative_start, relative_end in _windows(section):
                    pieces.append((text, start + relative_start, start + relative_end))
    else:
        raise ChunkingError("unsupported strategy")
    return [Chunk(index=index, text=text, start_offset=start, end_offset=end) for index, (text, start, end) in enumerate(pieces)]
