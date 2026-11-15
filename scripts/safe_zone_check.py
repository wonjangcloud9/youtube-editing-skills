#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["numpy", "pillow"]
# ///
"""Shorts safe zone: is any of our text under the YouTube Shorts UI?

Shades the parts of a 1080x1920 frame that the Shorts player covers and writes a contact sheet:
  bottom  y > 1344 (bottom 30%: title, channel + subscribe, sound pill, description when expanded)
  right   x > 888 for 840 < y < 1680 (like / dislike / comment / share / remix column)
  top     y < 230 (search / menu icons, status bar) — lighter: icons sit at the right edge only
Numbers from creator safe-zone guides (they differ: bottom 300-672 px, right 120-192 px; none is an official YouTube
spec) and from a screenshot of our own short in the YouTube player (2026-11-05: the button column touched the right end
of a 66 px caption; the owner saw text cut by the bottom overlay on a phone).

    uv run scripts/safe_zone_check.py <final.mp4>            # frames at caption midpoints (HyperFrames captions.html)
    uv run scripts/safe_zone_check.py <final.mp4> --at 1,5,9
    uv run scripts/safe_zone_check.py frame1.png frame2.png  # e.g. hyperframes snapshot output
Writes <out dir>/safe_zone.jpg and prints frames where bright caption-like text pixels fall inside a shaded zone.
"""
import json
import re
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

W, H = 1080, 1920
BOTTOM, RIGHT, RIGHT_Y, TOP = 1344, 888, (840, 1680), 230


def frame_at(mp4: Path, t: float) -> Image.Image:
    raw = subprocess.run(["ffmpeg", "-loglevel", "error", "-ss", f"{t:.3f}", "-i", str(mp4), "-frames:v", "1", "-vf", f"scale={W}:{H}",
                          "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True).stdout
    return Image.frombytes("RGB", (W, H), raw)


def caption_times(mp4: Path) -> list[float]:
    cap = mp4.parent.parent / "hf/compositions/captions.html"
    if not cap.exists():
        return []
    m = re.search(r"const C = (\[.*?\]);", cap.read_text(), re.S)
    return [round((s + e) / 2, 2) for _, s, e in json.loads(m.group(1))] if m else []


def text_mask(img: Image.Image) -> np.ndarray:
    """Bright white or our yellow (#FFD60A) pixels that sit next to a dark pixel = drawn text with a shadow/plate."""
    a = np.asarray(img).astype(np.int16)
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    bright = ((r > 238) & (g > 238) & (b > 238)) | ((r > 230) & (g > 190) & (b < 80))
    lum = (r * 299 + g * 587 + b * 114) // 1000
    dark = lum < 60
    near_dark = np.zeros_like(dark)
    for dy, dx in [(-3, 0), (3, 0), (0, -3), (0, 3)]:
        near_dark |= np.roll(np.roll(dark, dy, 0), dx, 1)
    return bright & near_dark


def zones() -> np.ndarray:
    z = np.zeros((H, W), bool)
    z[BOTTOM:, :] = True
    z[RIGHT_Y[0]:RIGHT_Y[1], RIGHT:] = True
    return z


def shade(img: Image.Image) -> Image.Image:
    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    d.rectangle([0, BOTTOM, W, H], fill=(255, 0, 0, 80))
    d.rectangle([RIGHT, RIGHT_Y[0], W, RIGHT_Y[1]], fill=(255, 0, 0, 80))
    d.rectangle([0, 0, W, TOP], fill=(255, 150, 0, 50))
    return Image.alpha_composite(img.convert("RGBA"), ov).convert("RGB")


def main() -> None:
    args = sys.argv[1:]
    if not args:
        print(__doc__); sys.exit(1)
    frames: list[tuple[str, Image.Image]] = []
    if args[0].endswith(".mp4"):
        mp4 = Path(args[0])
        ts = [float(x) for x in args[args.index("--at") + 1].split(",")] if "--at" in args else (caption_times(mp4) or list(np.arange(0.5, 60, 3.0)))
        dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(mp4)],
                                   capture_output=True, text=True).stdout)
        frames = [(f"{t:.1f}s", frame_at(mp4, t)) for t in ts if t < dur]
        out = mp4.parent / "safe_zone.jpg"
    else:
        frames = [(Path(a).stem, Image.open(a).convert("RGB").resize((W, H))) for a in args]
        out = Path(args[0]).parent / "safe_zone.jpg"
    z = zones()
    bad = []
    for name, img in frames:
        m = text_mask(img)
        inside = int((m & z).sum())
        if inside > 400:   # a few hundred px = a word or more of caption-weight text
            bad.append((name, inside))
    cols = min(6, len(frames))
    rows = (len(frames) + cols - 1) // cols
    tw, th = 270, 480
    sheet = Image.new("RGB", (cols * tw, rows * th), (20, 20, 20))
    for k, (name, img) in enumerate(frames):
        t = shade(img).resize((tw, th))
        ImageDraw.Draw(t).text((6, 6), name, fill=(255, 255, 0))
        sheet.paste(t, ((k % cols) * tw, (k // cols) * th))
    sheet.save(out, quality=88)
    print(f"{out}  ({len(frames)} frames)")
    if bad:
        print("⚠ text-like pixels inside the Shorts UI zones: " + ", ".join(f"{n} ({c} px)" for n, c in bad) + " — look at the sheet")
    else:
        print("OK — no caption-like text in the bottom 30% or the right button column")


if __name__ == "__main__":
    main()
