import os
import json
from tqdm import tqdm

JSON_ROOT = "data/handwriting_json/json_data"

OUTPUT_CHAR_VOCAB = "data/handwriting_processed/char_vocab.json"
OUTPUT_WRITER_VOCAB = "data/handwriting_processed/writer_vocab.json"


def collect_chars_and_writers(json_root):
    chars = set()
    writers = set()

    for writer_folder in sorted(os.listdir(json_root)):
        writer_path = os.path.join(json_root, writer_folder)
        if not os.path.isdir(writer_path):
            continue

        json_files = [f for f in os.listdir(writer_path) if f.lower().endswith(".json")]

        for jf in tqdm(json_files, desc=f"Parsing writer {writer_folder}", leave=False):
            json_path = os.path.join(writer_path, jf)

            try:
                with open(json_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except Exception as e:
                print(f"[WARN] Failed to read JSON {json_path}: {e}")
                continue

            # Extract character
            try:
                char = data["text"]["letter"]["value"]
                chars.add(char)
            except:
                print(f"[WARN] JSON missing char field: {json_path}")
                continue

            # Extract writer number
            try:
                writer_no = data["license"]["writer_no"]  # e.g. "001"
                writers.add(writer_no)
            except:
                print(f"[WARN] JSON missing writer_no: {json_path}")
                continue

    return sorted(chars), sorted(writers)


def build_mapping_list(items):
    """
    items: sorted list of chars or writer IDs.
    Returns mapping dicts.
    """
    item_to_id = {item: idx for idx, item in enumerate(items)}
    id_to_item = {idx: item for idx, item in enumerate(items)}
    return item_to_id, id_to_item


def save_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"[SAVE] {path}")


def main():
    print("=== Step 1: Collecting characters and writers ===")
    chars, writers = collect_chars_and_writers(JSON_ROOT)

    print(f"Found {len(chars)} unique characters")
    print(f"Found {len(writers)} unique writers")

    # Build mappings
    print("=== Step 2: Building vocab mappings ===")
    char_to_id, id_to_char = build_mapping_list(chars)
    writer_to_id, id_to_writer = build_mapping_list(writers)

    # Save vocab files
    print("=== Step 3: Saving vocab files ===")
    save_json(
        OUTPUT_CHAR_VOCAB,
        {"char_to_id": char_to_id, "id_to_char": id_to_char},
    )
    save_json(
        OUTPUT_WRITER_VOCAB,
        {"writer_to_id": writer_to_id, "id_to_writer": id_to_writer},
    )

    print("=== DONE ===")
    print(f"char_vocab.json saved to: {OUTPUT_CHAR_VOCAB}")
    print(f"writer_vocab.json saved to: {OUTPUT_WRITER_VOCAB}")


if __name__ == "__main__":
    main()
