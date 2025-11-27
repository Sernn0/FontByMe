from __future__ import annotations

"""Tkinter canvas for drawing a glyph and saving as PNG."""

import os
import tkinter as tk
from pathlib import Path
from typing import Optional

from PIL import Image, ImageDraw

try:
    from utils.preprocess import load_and_preprocess_image
except Exception:  # pragma: no cover
    load_and_preprocess_image = None  # type: ignore


class DrawCanvas(tk.Tk):
    def __init__(self, save_dir: Path = Path("user_drawings"), image_size: int = 256):
        super().__init__()
        self.title("Glyph Canvas")
        self.image_size = image_size
        self.save_dir = save_dir
        self.save_dir.mkdir(parents=True, exist_ok=True)

        self.canvas = tk.Canvas(self, width=image_size, height=image_size, bg="white")
        self.canvas.pack()

        btn_frame = tk.Frame(self)
        btn_frame.pack(fill=tk.X)
        tk.Button(btn_frame, text="Save", command=self.save_image).pack(side=tk.LEFT, expand=True)
        tk.Button(btn_frame, text="Clear", command=self.clear_canvas).pack(
            side=tk.LEFT, expand=True
        )

        self.canvas.bind("<B1-Motion>", self.draw)
        self.canvas.bind("<ButtonPress-1>", self.start_draw)
        self.last_x = None
        self.last_y = None

    def start_draw(self, event):
        self.last_x, self.last_y = event.x, event.y

    def draw(self, event):
        if self.last_x is not None and self.last_y is not None:
            self.canvas.create_line(self.last_x, self.last_y, event.x, event.y, fill="black", width=4)
        self.last_x, self.last_y = event.x, event.y

    def clear_canvas(self):
        self.canvas.delete("all")

    def save_image(self):
        # Save canvas to PNG.
        self.canvas.postscript(file="temp.ps", colormode="color")
        img = Image.open("temp.ps")
        img = img.convert("L").resize((self.image_size, self.image_size))
        self.save_dir.mkdir(parents=True, exist_ok=True)
        save_path = self.save_dir / "canvas.png"
        img.save(save_path)
        os.remove("temp.ps")
        print(f"Saved drawing to {save_path}")
        if load_and_preprocess_image:
            processed = load_and_preprocess_image(save_path)
            print("Processed image shape:", processed.shape)


def main():
    app = DrawCanvas()
    app.mainloop()


if __name__ == "__main__":
    main()
