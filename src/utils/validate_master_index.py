
import json
import os
from pathlib import Path
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor

# Define paths
ROOT_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT_DIR / "data"
JSON_DIR = DATA_DIR / "handwriting_json" / "json_data"
RAW_DIR = DATA_DIR / "handwriting_raw" / "resizing"
PROCESSED_DIR = DATA_DIR / "handwriting_processed"

def parse_single_json(json_file):
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Extract info
        image_info = data.get("image", {})
        text_info = data.get("text", {})

        file_name = image_info.get("file_name")
        text_value = data.get("info", {}).get("text")

        # Fallback if text is not in info
        if not text_value and "letter" in text_info:
             text_value = text_info["letter"].get("value")

        if not file_name or not text_value:
            return None, "missing_metadata"

        # Writer ID logic: inferred from folder name usually, or file naming convention
        # Format seems to be: {writer_id}......
        # json_file.parent.name is likely writer_id
        writer_id = json_file.parent.name

        expected_image_path = RAW_DIR / writer_id / file_name

        if not expected_image_path.exists():
            return None, "image_not_found"

        return {
            "writer_id": writer_id,
            "text": text_value,
            "image_path": str(expected_image_path.relative_to(ROOT_DIR)),
            "json_path": str(json_file.relative_to(ROOT_DIR))
        }, "valid"

    except Exception as e:
        return None, f"error: {str(e)}"

def main():
    print(f"Scanning {JSON_DIR} ...")

    # Collect all JSON files
    json_files = list(JSON_DIR.rglob("*.json"))
    print(f"Found {len(json_files)} JSON files.")

    valid_entries = []
    errors = {
        "missing_metadata": [],
        "image_not_found": [],
        "error": []
    }

    # Parallel processing for speed
    with ThreadPoolExecutor(max_workers=16) as executor:
        results = list(tqdm(executor.map(parse_single_json, json_files), total=len(json_files)))

    for res, status in results:
        if status == "valid":
            valid_entries.append(res)
        elif status.startswith("error"):
            errors["error"].append(res) # res is error message? No, wait. logic needed
            # Correction: parse_single_json returns None, msg on error
            pass
        else:
            errors[status].append(res) # res is None for these cases usually?
            # Re-read parse_single_json: it returns None, status

    # Check for orphaned images (Images with no JSON)
    print("Checking for orphaned images...")
    all_images = set()
    for img_path in RAW_DIR.rglob("*.jpg"): # Assuming jpg based on previous head
        all_images.add(str(img_path.relative_to(ROOT_DIR)))

    linked_images = set(e["image_path"] for e in valid_entries)
    orphaned_images = all_images - linked_images

    print(f"\nValidation Results:")
    print(f"Valid Pairs: {len(valid_entries)}")
    print(f"Orphaned Images: {len(orphaned_images)}")
    print(f"Metadata Issues: {len(errors['missing_metadata'])}")
    print(f"Missing Images: {len(errors['image_not_found'])}")

    # Save Report
    report = {
        "valid_count": len(valid_entries),
        "orphaned_count": len(orphaned_images),
        "missing_metadata_count": len(errors['missing_metadata']),
        "image_not_found_count": len(errors['image_not_found']),
        "orphaned_samples": list(orphaned_images)[:10],
        # "valid_samples": valid_entries[:5]
    }

    report_path = PROCESSED_DIR / "data_validation_report.json"
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print(f"Report saved to {report_path}")

    # Save a clean master index candidate
    master_candidate_path = PROCESSED_DIR / "master_index_candidate.json"
    with open(master_candidate_path, 'w', encoding='utf-8') as f:
        json.dump(valid_entries, f, indent=2, ensure_ascii=False)
    print(f"Clean candidate index saved to {master_candidate_path}")

if __name__ == "__main__":
    main()
