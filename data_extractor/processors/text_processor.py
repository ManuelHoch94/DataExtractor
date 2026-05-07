from __future__ import annotations

import re

from data_extractor.processors.base import BaseProcessor

_MULTI_WHITESPACE = re.compile(r"[ \t]+")
_MULTI_NEWLINE = re.compile(r"\n{3,}")
_LIGATURES: dict[str, str] = {
    "ﬀ": "ff",
    "ﬁ": "fi",
    "ﬂ": "fl",
    "ﬃ": "ffi",
    "ﬄ": "ffl",
    "­": "",  # soft-hyphen
}
_LIGATURE_PATTERN = re.compile("|".join(re.escape(k) for k in _LIGATURES))


class TextProcessor(BaseProcessor):
    """Cleans and normalises raw text extracted from PDF pages.

    Operations applied (in order):
    1. Replace common PDF ligatures with ASCII equivalents.
    2. Collapse repeated whitespace within lines.
    3. Collapse excessive blank lines (> 2 consecutive newlines → 2).
    4. Strip leading/trailing whitespace from every line.
    5. Strip the entire string.
    """

    def process(self, text: str) -> str:
        text = _LIGATURE_PATTERN.sub(lambda m: _LIGATURES[m.group()], text)
        lines = text.split("\n")
        lines = [_MULTI_WHITESPACE.sub(" ", line).strip() for line in lines]
        text = "\n".join(lines)
        text = _MULTI_NEWLINE.sub("\n\n", text)
        return text.strip()
