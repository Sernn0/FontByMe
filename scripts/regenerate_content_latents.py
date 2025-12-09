"""
Regenerate content latents with unified index ordering.

This ensures content latents match the unified character mapping,
so that JSON text_id and content latent index are consistent.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
from PIL import Image

# Project root
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.data.unified_mapping import build_unified_mapping, load_png_file_mapping


def parse_args():
    parser = argparse.ArgumentParser(description="Regenerate content latents with unified ordering.")
    parser.add_argument(
        "--encoder_path",
        type=Path,
        default=ROOT / "runs/autoenc/encoder.h5",
        help="Path to content encoder model.",
    )
    parser.add_argument(
        "--png_dir",
        type=Path,
        default=ROOT / "data/content_font/NotoSansKR-Regular",
        help="Directory with standard font PNGs.",
    )
    parser.add_argument(
        "--json_path",
        type=Path,
        default=ROOT / "data/handwriting_processed/handwriting_index_train_shared.json",
        help="Path to handwriting JSON for text mapping.",
    )
    parser.add_argument(
        "--output_path",
        type=Path,
        default=ROOT / "runs/autoenc/content_latents_unified.npy",
        help="Output path for unified content latents.",
    )
    return parser.parse_args()


def load_image(path: Path, size: int = 256) -> np.ndarray:
    """Load and preprocess image to 0-1 range."""
    img = Image.open(path).convert("L")
    img = img.resize((size, size), Image.LANCZOS)
    arr = np.array(img, dtype=np.float32) / 255.0
    return np.expand_dims(arr, axis=-1)


def main():
    args = parse_args()

    # Import TensorFlow
    import tensorflow as tf
    from tensorflow import keras

    print(f"[INFO] Loading encoder from {args.encoder_path}")
    encoder = keras.models.load_model(str(args.encoder_path), compile=False, safe_mode=False)

    # Build unified mapping
    print(f"[INFO] Building unified mapping...")
    char_to_unified_idx, sorted_chars = build_unified_mapping(args.json_path, args.png_dir)
    png_mapping = load_png_file_mapping(args.png_dir)

    print(f"[INFO] Unified mapping: {len(char_to_unified_idx)} characters")

    # Get PNG files
    png_files = sorted(args.png_dir.glob("*.png"))

    # Create content latents in unified order
    num_chars = len(sorted_chars)

    # First, get latent dimension by encoding one image
    sample_img = load_image(png_files[0])
    sample_latent = encoder(np.expand_dims(sample_img, 0), training=False).numpy()
    latent_dim = sample_latent.shape[-1]
    print(f"[INFO] Latent dimension: {latent_dim}")

    # Encode all characters
    latents = np.zeros((num_chars, latent_dim), dtype=np.float32)

    for unified_idx, char in enumerate(sorted_chars):
        # Get PNG file for this character
        codepoint = ord(char)
        png_path = args.png_dir / f"U+{codepoint:04X}.png"

        if not png_path.exists():
            print(f"[WARN] Missing PNG for '{char}' (U+{codepoint:04X})")
            continue

        img = load_image(png_path)
        latent = encoder(np.expand_dims(img, 0), training=False).numpy()
        latents[unified_idx] = latent.squeeze()

        if (unified_idx + 1) % 500 == 0:
            print(f"[INFO] Encoded {unified_idx + 1}/{num_chars} characters")

    print(f"[INFO] Encoded {num_chars} characters")

    # Save
    args.output_path.parent.mkdir(parents=True, exist_ok=True)
    np.save(args.output_path, latents)
    print(f"[INFO] Saved unified content latents to {args.output_path}")
    print(f"[INFO] Shape: {latents.shape}")

    # Verification
    print(f"\n[Verification]")
    print(f"  Character '가' (unified_idx=0) -> latent mean: {latents[0].mean():.4f}")
    print(f"  Character '긔' (unified_idx={char_to_unified_idx.get('긔', -1)}) -> latent mean: {latents[char_to_unified_idx.get('긔', 0)].mean():.4f}")


if __name__ == "__main__":
    main()
