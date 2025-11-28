from __future__ import annotations

"""
Generate vocabularies for characters and writers from handwriting JSON metadata.
"""

import argparse
import json
from pathlib import Path
from typing import Dict, Iterable, Optional, Set, Tuple


def extract_text(data: dict) -> Optional[str]:
    """Extract text value from known JSON structures."""
    if isinstance(data.get("info"), dict):
        if isinstance(data["info"].get("text"), dict):
            return data["info"]["text"].get("value")
        return data["info"].get("text")
    if isinstance(data.get("text"), dict):
        return data["text"].get("value")
    if "text" in data:
        return data.get("text")
    return None


def extract_writer(data: dict, json_path: Path) -> Optional[str]:
    """Extract raw writer id from license or fall back to folder name."""
    if isinstance(data.get("license"), dict):
        writer = data["license"].get("writer_no")
        if writer is not None:
            return str(writer)
    return json_path.parent.name


def collect_vocab(json_files: Iterable[Path]) -> Tuple[Set[str], Set[str]]:
    """Collect unique characters and writer ids from JSON files."""
    chars: Set[str] = set()
    writers: Set[str] = set()
    for path in json_files:
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:
            print(f"Warning: failed to read {path}: {exc}")
            continue
        text = extract_text(data)
        writer = extract_writer(data, path)
        if text:
            for ch in str(text):
                chars.add(ch)
        if writer:
            writers.add(str(writer))
    return chars, writers


def save_vocab(vocab: Iterable[str], path: Path) -> None:
    """Save vocabulary list to JSON file (legacy; not used for final mappings)."""
    vocab_list = sorted(vocab)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(vocab_list, ensure_ascii=False, indent=2), encoding="utf-8")


def build_char_mappings(chars: Iterable[str]) -> Dict[str, Dict[str, str]]:
    """Build char_to_id and id_to_char mappings."""
    sorted_chars = sorted(chars)
    char_to_id = {ch: idx for idx, ch in enumerate(sorted_chars)}
    id_to_char = {str(idx): ch for idx, ch in enumerate(sorted_chars)}
    return {"char_to_id": char_to_id, "id_to_char": id_to_char}


def normalize_writer_name(name: str) -> str:
    """Ensure writer name follows writer_XXXX pattern."""
    if name.startswith("writer_"):
        return name
    if name.isdigit():
        return f"writer_{int(name):04d}"
    return f"writer_{name}"


def build_writer_mappings(writers: Iterable[str]) -> Dict[str, Dict[str, str]]:
    """Build writer_to_id and id_to_writer mappings with writer_XXXX keys."""
    normalized = sorted(normalize_writer_name(w) for w in writers)
    writer_to_id = {w: idx for idx, w in enumerate(normalized)}
    id_to_writer = {str(idx): w for idx, w in enumerate(normalized)}
    return {"writer_to_id": writer_to_id, "id_to_writer": id_to_writer}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate character and writer vocab from handwriting JSON.")
    parser.add_argument(
        "--input-dir",
        type=Path,
        default=Path("data/handwriting_json"),
        help="Directory containing handwriting JSON files.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("data/handwriting_processed"),
        help="Directory to save vocab files.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    json_files = list(args.input_dir.rglob("*.json"))
    if not json_files:
        print(f"No JSON files found in {args.input_dir}")
        return
    print(f"Found {len(json_files)} JSON files.")

    char_set, writer_set = collect_vocab(json_files)
    print(f"Unique characters: {len(char_set)}, writers: {len(writer_set)}")

    char_mappings = build_char_mappings(char_set)
    writer_mappings = build_writer_mappings(writer_set)

    args.output_dir.mkdir(parents=True, exist_ok=True)
    char_vocab_path = args.output_dir / "char_vocab.json"
    writer_vocab_path = args.output_dir / "writer_vocab.json"
    char_vocab_path.write_text(json.dumps(char_mappings, ensure_ascii=False, indent=2), encoding="utf-8")
    writer_vocab_path.write_text(json.dumps(writer_mappings, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"Saved char vocab to {char_vocab_path}")
    print(f"Saved writer vocab to {writer_vocab_path}")


if __name__ == "__main__":
    main()
