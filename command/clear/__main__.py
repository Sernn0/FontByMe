#!/usr/bin/env python3
"""Clear all output files and Python cache."""
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUTPUTS = ROOT / "outputs"

# Directories to clean in outputs/
dirs_to_clean = [
    "tmp_images",
    "pipeline_work",
    "results",
    "test_glyphs",
    "test_glyphs_raw",
    "test_glyphs_enhanced",
    "test_pretrained",
    "test_pretrained_font",
]

# Files to clean (root level in outputs/)
files_to_clean = ["*.png", "*.svg", "*.ttf"]

cleaned = 0

# Clean output directories
for dir_name in dirs_to_clean:
    dir_path = OUTPUTS / dir_name
    if dir_path.exists():
        shutil.rmtree(dir_path)
        print(f"✓ Deleted: outputs/{dir_name}")
        cleaned += 1

# Clean output files
for pattern in files_to_clean:
    for file_path in OUTPUTS.glob(pattern):
        file_path.unlink()
        print(f"✓ Deleted: outputs/{file_path.name}")
        cleaned += 1

# Clean __pycache__ directories
for pycache in ROOT.rglob("__pycache__"):
    shutil.rmtree(pycache)
    print(f"✓ Deleted: {pycache.relative_to(ROOT)}")
    cleaned += 1

# Recreate results folder
(OUTPUTS / "results").mkdir(parents=True, exist_ok=True)

if cleaned == 0:
    print("✓ Already clean!")
else:
    print(f"\n✅ Cleaned {cleaned} items")
