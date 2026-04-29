#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path


VI_SENTENCES = [
    "Việt Nam đang phát triển các hệ thống tìm kiếm ngữ nghĩa cho dữ liệu tiếng Việt.",
    "Mô hình nhúng cần phản hồi nhanh, ổn định và giữ chất lượng truy hồi trong môi trường sản xuất.",
    "Người dùng gửi câu truy vấn ngắn để tìm tài liệu liên quan trong kho tri thức doanh nghiệp.",
    "Dịch vụ cần từ chối văn bản quá dài thay vì tự động cắt bớt nội dung đầu vào.",
]


def load_tokenizer(tokenizer_path: str | None):
    if not tokenizer_path:
        return None
    try:
        from tokenizers import Tokenizer

        path = Path(tokenizer_path)
        if path.exists():
            return Tokenizer.from_file(str(path))
    except Exception:
        return None
    return None


def count_tokens(text: str, tokenizer) -> int:
    if tokenizer is None:
        return max(1, len(text.split()))
    return len(tokenizer.encode(text).ids)


def build_text(target_tokens: int, tokenizer) -> str:
    parts: list[str] = []
    idx = 0
    while count_tokens(" ".join(parts), tokenizer) < target_tokens:
        parts.append(VI_SENTENCES[idx % len(VI_SENTENCES)])
        idx += 1
    text = " ".join(parts)

    if tokenizer is None:
        return " ".join(text.split()[:target_tokens])

    # Benchmark payloads should not exceed their named token bucket.
    encoded = tokenizer.encode(text)
    if len(encoded.ids) <= target_tokens:
        return text

    special_count = sum(encoded.special_tokens_mask)
    content_ids = [
        token_id
        for token_id, is_special in zip(encoded.ids, encoded.special_tokens_mask)
        if not is_special
    ]
    content_limit = max(1, target_tokens - special_count)

    for limit in range(min(content_limit, len(content_ids)), 0, -1):
        candidate = tokenizer.decode(content_ids[:limit], skip_special_tokens=True).strip()
        if candidate and count_tokens(candidate, tokenizer) <= target_tokens:
            return candidate

    return tokenizer.decode(content_ids[:1], skip_special_tokens=True).strip()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", default="benchmarks/payloads")
    parser.add_argument("--model", default="bge-m3-vi-vists")
    parser.add_argument(
        "--tokenizer-path",
        default="/models/bge-m3-vi-vists-best-eval/tokenizer.json",
    )
    parser.add_argument("--lengths", default="32,64,128,256,512")
    args = parser.parse_args()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    tokenizer = load_tokenizer(args.tokenizer_path)

    for length in [int(item) for item in args.lengths.split(",") if item.strip()]:
        text = build_text(length, tokenizer)
        actual_tokens = count_tokens(text, tokenizer)
        payload = {
            "model": args.model,
            "input": text,
            "encoding_format": "float",
        }
        (out_dir / f"payload_{length}.json").write_text(
            json.dumps(payload, ensure_ascii=False),
            encoding="utf-8",
        )
        (out_dir / f"input_{length}.jsonl").write_text(
            json.dumps({"text": text}, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        print(f"wrote target={length} actual_tokens={actual_tokens}")


if __name__ == "__main__":
    main()
