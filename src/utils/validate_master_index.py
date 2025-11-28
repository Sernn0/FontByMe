from __future__ import annotations

"""
Validate master handwriting index JSON for required fields and paths.
"""

import argparse
import json
import os
from pathlib import Path
from typing import Dict, List, Optional


REQUIRED_KEYS = ["image_path", "text", "text_id", "writer_id"]
DEFAULT_INPUT = Path("data/handwriting_processed/master_index.json")
DEFAULT_REPORT = Path("data/handwriting_processed/schema_check_report.json")
DEFAULT_ROOT = Path("data/handwriting_raw/resizing")


def resolve_path(path_str: str, root: Optional[Path]) -> str:
    """Resolve image path against optional root, handling leading slash paths."""
    if not root:
        return str(Path(path_str))

    # Strip leading slash to handle paths like "/data/handwriting_raw/resizing/..."
    normalized = Path(path_str.lstrip("/"))
    root_parts = list(root.parts)
    norm_parts = list(normalized.parts)

    # If normalized path already contains the root prefix, drop it.
    if norm_parts[: len(root_parts)] == root_parts:
        remaining = Path(*norm_parts[len(root_parts) :])
        return str(root / remaining)

    # Otherwise, treat as relative to root.
    return str(root / normalized)


def validate_entry(entry: Dict, root: Optional[Path]) -> List[str]:
    """Return a list of problems for a single entry."""
    problems = []
    for key in REQUIRED_KEYS:
        if key not in entry:
            problems.append(f"missing_key:{key}")
    if "image_path" in entry:
        path = entry["image_path"]
        if not isinstance(path, str):
            problems.append("image_path_not_str")
        else:
            resolved = resolve_path(path, root)
            if not os.path.exists(resolved):
                problems.append("image_missing")
                entry["resolved_image_path"] = resolved
    if "text" in entry and not isinstance(entry.get("text"), str):
        problems.append("text_not_str")
    if "text_id" in entry and not isinstance(entry.get("text_id"), int):
        problems.append("text_id_not_int")
    if "writer_id" in entry and not isinstance(entry.get("writer_id"), (int, str)):
        problems.append("writer_id_not_int_or_str")
    return problems


def validate_index(input_path: Path, root: Optional[Path]) -> Dict:
    """Validate the master index and return a report dictionary."""
    if not input_path.is_file():
        return {"status": "error", "message": f"file not found: {input_path}"}

    try:
        entries = json.loads(input_path.read_text(encoding="utf-8"))
    except Exception as exc:
        return {"status": "error", "message": f"failed to read json: {exc}"}

    issues = []
    for idx, entry in enumerate(entries):
        probs = validate_entry(entry, root)
        if probs:
            issues.append({"index": idx, "problems": probs, "entry": entry})

    if issues:
        return {"status": "fail", "issues": issues}
    return {"status": "ok"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate master handwriting index JSON.")
    parser.add_argument(
        "--input",
        type=Path,
        default=DEFAULT_INPUT,
        help="Path to master index JSON (default: data/handwriting_processed/master_index.json)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_REPORT,
        help="Path to write validation report JSON.",
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=DEFAULT_ROOT,
        help="Optional root directory to resolve relative image paths.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    report = validate_index(args.input, args.root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Validation status: {report.get('status')}")
    print(f"Report saved to: {args.output}")


if __name__ == "__main__":
    main()
