
import json
import random
from pathlib import Path
from collections import defaultdict
import sys

# Setup path to import from scripts
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.data.unified_mapping import build_unified_mapping

DATA_DIR = ROOT / "data"
PROCESSED_DIR = DATA_DIR / "handwriting_processed"
MASTER_INDEX = PROCESSED_DIR / "master_index_candidate.json"
PNG_DIR = DATA_DIR / "content_font" / "NotoSansKR-Regular"
JSON_PATH = PROCESSED_DIR / "handwriting_index_train_shared.json" # Needed for mapping build?

def main():
    print("Loading master index candidate...")
    with open(MASTER_INDEX, 'r', encoding='utf-8') as f:
        master_data = json.load(f)
    print(f"Loaded {len(master_data)} entries.")

    # Build Unified Mapping
    # note: unified_mapping.py needs a JSON path to scan for characters.
    # We can pass MASTER_INDEX itself if the function supports it, or valid existing json.
    # actually build_unified_mapping takes 'json_path' and reads 'text' fields.
    # master_index_candidate.json has 'text' fields.
    print("Building Unified Character Mapping...")
    char_to_unified_idx, _ = build_unified_mapping(MASTER_INDEX, PNG_DIR)
    print(f"Unified Mapping size: {len(char_to_unified_idx)}")

    # Verify coverage
    data_chars = set(e['text'] for e in master_data)
    mapped_chars = set(char_to_unified_idx.keys())
    missing = data_chars - mapped_chars
    if missing:
        print(f"Warning: {len(missing)} characters in data are not in unified mapping (probably missing in PNGs).")
        # e.g. rare Hanja or symbols not in NotoSansKR-Regular 2350
        # We should filter these out or accept them without ID

    # Group by Writer
    print("Grouping by Writer ID...")
    writers = defaultdict(list)
    for entry in master_data:
        char = entry.get('text')
        # Skip if not in unified mapping?
        # If we train style encoder defined by Writer Classification, character content DOES matter?
        # Actually for style encoder training, we only need writer label.
        # But for the FULL pipeline (Joint Decoder), we need content latent.
        # So entries without a Unified Content Index are useless for Joint Training.
        # They ARE useful for Style Encoder training (pure style learning).
        # We can keep them for Style Encoder, but mark them?
        # For simplicity and consistency, let's keep everything for Style Encoder,
        # but add 'unified_idx' only where available.

        idx = char_to_unified_idx.get(char)
        entry['unified_idx'] = idx # Can be None
        writers[entry['writer_id']].append(entry)

    print(f"Found {len(writers)} writers.")

    train_set = []
    val_set = []
    test_set = []

    # Split
    random.seed(42)
    for wid, entries in writers.items():
        random.shuffle(entries)
        n = len(entries)
        n_train = int(n * 0.8)
        n_val = int(n * 0.1)
        # n_test = rest

        train_set.extend(entries[:n_train])
        val_set.extend(entries[n_train:n_train+n_val])
        test_set.extend(entries[n_train+n_val:])

    print(f"Split results:")
    print(f"  Train: {len(train_set)}")
    print(f"  Val:   {len(val_set)}")
    print(f"  Test:  {len(test_set)}")

    # Save
    def save_json(data, name):
        p = PROCESSED_DIR / name
        with open(p, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False) # minimized json for size
        print(f"Saved {name}")

    save_json(train_set, "handwriting_index_train_new.json")
    save_json(val_set, "handwriting_index_val_new.json")
    save_json(test_set, "handwriting_index_test_new.json")

    # Save Writer Mapping
    sorted_writers = sorted(writers.keys())
    writer_map = {w: i for i, w in enumerate(sorted_writers)}
    with open(PROCESSED_DIR / "writer_vocab_new.json", 'w') as f:
        json.dump(writer_map, f, indent=2)
    print("Saved writer_vocab_new.json")

if __name__ == "__main__":
    main()
