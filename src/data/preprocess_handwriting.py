from __future__ import annotations

"""
Preprocess handwriting images:
- load grayscale
- trim to content bounding box
- resize with aspect ratio to target size
- pad to square canvas
- normalize to [0, 1]
"""

import argparse
from pathlib import Path
from typing import Iterable, Tuple

import numpy as np
from PIL import Image


def load_image(path: Path) -> np.ndarray:
    """Load an image as grayscale uint8 array."""
    with Image.open(path) as img:
        img = img.convert("L")
        return np.array(img, dtype=np.uint8)


def trim_to_content(img: np.ndarray, threshold: int = 250) -> np.ndarray:
    """Crop to bounding box of non-background pixels."""
    mask = img < threshold
    if not np.any(mask):
        return img
    coords = np.argwhere(mask)
    y0, x0 = coords.min(axis=0)
    y1, x1 = coords.max(axis=0)
    return img[y0 : y1 + 1, x0 : x1 + 1]


def resize_and_pad(img: np.ndarray, target_size: int = 256) -> np.ndarray:
    """Resize keeping aspect ratio, then pad to a square canvas."""
    h, w = img.shape[:2]
    if h == 0 or w == 0:
        return np.full((target_size, target_size), 255, dtype=np.uint8)
    scale = target_size / max(h, w)
    new_w = max(1, int(round(w * scale)))
    new_h = max(1, int(round(h * scale)))
    pil_img = Image.fromarray(img, mode="L")
    resized = pil_img.resize((new_w, new_h), resample=Image.LANCZOS)
    canvas = np.full((target_size, target_size), 255, dtype=np.uint8)
    top = (target_size - new_h) // 2
    left = (target_size - new_w) // 2
    canvas[top : top + new_h, left : left + new_w] = np.array(resized, dtype=np.uint8)
    return canvas


def normalize(img: np.ndarray) -> np.ndarray:
    """Normalize to float32 [0, 1]."""
    return img.astype(np.float32) / 255.0


def preprocess_single_image(input_path: Path, output_path: Path, target_size: int = 256) -> None:
    """Full preprocessing pipeline for one image."""
    img = load_image(input_path)
    cropped = trim_to_content(img)
    padded = resize_and_pad(cropped, target_size=target_size)
    normalized = normalize(padded)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray((normalized * 255).astype(np.uint8), mode="L").save(output_path)


def iter_image_files(directory: Path) -> Iterable[Path]:
    """Yield image files in directory (simple glob-based)."""
    patterns = ("*.png", "*.jpg", "*.jpeg", "*.bmp")
    for pattern in patterns:
        for path in sorted(directory.glob(pattern)):
            yield path


def batch_preprocess(input_dir: Path, output_dir: Path, target_size: int = 256) -> None:
    """Preprocess all images in input_dir and write to output_dir."""
    input_dir.mkdir(parents=True, exist_ok=True)
    output_dir.mkdir(parents=True, exist_ok=True)
    for img_path in iter_image_files(input_dir):
        out_path = output_dir / img_path.name
        preprocess_single_image(img_path, out_path, target_size=target_size)
        print(f"Processed {img_path.name} -> {out_path}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Preprocess handwriting images.")
    parser.add_argument(
        "--input-dir",
        type=Path,
        default=Path("data/handwriting_raw"),
        help="Directory containing raw handwriting images.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("data/handwriting_processed"),
        help="Directory to save processed images.",
    )
    parser.add_argument(
        "--target-size",
        type=int,
        default=256,
        help="Target square size for output images.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    batch_preprocess(args.input_dir, args.output_dir, target_size=args.target_size)


if __name__ == "__main__":
    main()
