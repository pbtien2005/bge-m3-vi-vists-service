from __future__ import annotations

from pathlib import Path

from tokenizers import Tokenizer


class TokenCounter:
    def __init__(self, tokenizer_path: str) -> None:
        path = Path(tokenizer_path)
        if not path.exists():
            raise FileNotFoundError(f"Tokenizer file not found: {path}")
        self._tokenizer = Tokenizer.from_file(str(path))

    def count(self, text: str) -> int:
        return len(self._tokenizer.encode(text).ids)
