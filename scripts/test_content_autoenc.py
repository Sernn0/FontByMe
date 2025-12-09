#!/usr/bin/env python
"""
Visualize content autoencoder reconstructions from content latents.
Tests if content latents contain enough information for reconstruction.
"""

from __future__ import annotations

import argparse
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
import tensorflow as tf
from tensorflow import keras


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Test content autoencoder reconstruction.")
    parser.add_argument(
        "--content_latents",
        type=Path,
        default=Path("runs/autoenc/content_latents.npy"),
        help="Path to content_latents.npy",
    )
    parser.add_argument(
        "--decoder_path",
        type=Path,
        default=Path("runs/autoenc/decoder.h5"),
        help="Path to content decoder model.",
    )
    parser.add_argument(
        "--num_samples",
        type=int,
        default=16,
        help="Number of samples to visualize.",
    )
    parser.add_argument(
        "--output_path",
        type=Path,
        default=Path("runs/autoenc/content_recon_test.png"),
        help="Output image path.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    # Load content latents
    content_latents = np.load(args.content_latents)
    print(f"Content latents shape: {content_latents.shape}")

    # Load decoder
    decoder = keras.models.load_model(args.decoder_path, compile=False, safe_mode=False)
    print(f"Decoder loaded from {args.decoder_path}")
    decoder.summary()

    # Select samples (evenly spaced through the charset)
    num_chars = content_latents.shape[0]
    indices = np.linspace(0, num_chars - 1, args.num_samples, dtype=int)

    # Decode
    selected_latents = content_latents[indices]
    reconstructions = decoder.predict(selected_latents, verbose=0)
    reconstructions = np.clip(reconstructions, 0.0, 1.0)

    # Plot
    cols = min(8, args.num_samples)
    rows = (args.num_samples + cols - 1) // cols

    fig, axes = plt.subplots(rows, cols, figsize=(cols * 2, rows * 2))
    axes = np.atleast_2d(axes)

    for i, idx in enumerate(indices):
        row, col = i // cols, i % cols
        ax = axes[row, col] if rows > 1 else axes[0, col]
        ax.imshow(reconstructions[i].squeeze(), cmap="gray")
        ax.set_title(f"char {idx}", fontsize=8)
        ax.axis("off")

    # Hide unused subplots
    for i in range(len(indices), rows * cols):
        row, col = i // cols, i % cols
        ax = axes[row, col] if rows > 1 else axes[0, col]
        ax.axis("off")

    args.output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.tight_layout()
    plt.savefig(args.output_path, dpi=150)
    plt.close()
    print(f"Saved reconstruction test to {args.output_path}")


if __name__ == "__main__":
    main()
