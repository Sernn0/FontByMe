#!/usr/bin/env python3
"""Run the Font UI application."""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
subprocess.run([sys.executable, str(ROOT / "ui" / "font_ui.py")])
