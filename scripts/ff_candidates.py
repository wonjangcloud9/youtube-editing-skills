#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["numpy", "pillow"]
# ///
"""Pick the opening shot BEFORE building: score every moment x crop of source footage with the first-frame metric.

The render's first-frame score is the minimum of 0 s and 1 s, so a candidate only counts if the shot still holds
`--hold` seconds later (the Seoul shot in the Hanwha short scored 89 at 38 s but cut away at 38.9 s -> 50 at 1 s).
Scores here are of the bare footage; the title bar and caption gradient on top move the final score a few points.

    uv run scripts/ff_candidates.py <video> [more videos] [--from 0] [--to END] [--step 0.5] [--hold 1.0]
                                    [--crop x,y,w,h ...] [--top 12]

Default crops: landscape -> three full-height 9:16 windows (left, centre, right); portrait -> the whole frame.
Lessons (2026-11-03/04): black-and-white archive tops out ~70 (no colour points); open on a colour, high-detail
real image (US Navy tsunami aerial 86, CES stage screen 89) and cut to archive after. Never grade to raise it.
"""
import importlib.util
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location("ffc", HERE / "first_frame_check.py")
ffc = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(ffc)
DECODE_W = 1280


def probe(video: str) -> tuple[int, int, float]:
    out = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height:format=duration",
                          "-of", "default=nw=1", video], capture_output=True, text=True, check=True).stdout
    kv = dict(line.split("=", 1) for line in out.split() if "=" in line)
    return int(kv["width"]), int(kv["height"]), float(kv["duration"])


def default_crops(w: int, h: int) -> list[tuple[int, int, int, int]]:
    if h >= w:
        return [(0, 0, w, h)]
    cw = int(h * 9 / 16) // 2 * 2
    return [(0, 0, cw, h), ((w - cw) // 2, 0, cw, h), (w - cw, 0, cw, h)]


def scan(video: str, t0: float, t1: float, step: float, crops) -> dict:
    w, h, _ = probe(video)
    dh = round(h * DECODE_W / w / 2) * 2
    k = DECODE_W / w
    raw = subprocess.run(["ffmpeg", "-loglevel", "error", "-ss", f"{t0}", "-t", f"{t1 - t0}", "-i", video,
                          "-vf", f"fps=1/{step},scale={DECODE_W}:{dh}", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                         capture_output=True, check=True).stdout
    n = len(raw) // (DECODE_W * dh * 3)
    frames = np.frombuffer(raw[: n * DECODE_W * dh * 3], np.uint8).reshape(n, dh, DECODE_W, 3)
    res = {}
    for i in range(n):
        t = round(t0 + i * step, 3)
        for c in crops:
            x, y, cw, ch = (int(round(v * k)) for v in c)
            img = Image.fromarray(frames[i, y:y + ch, x:x + cw]).resize((ffc.W, ffc.H), Image.BICUBIC)
            m = ffc.metrics(np.asarray(img).astype(np.float32))
            res[(t, c)] = (ffc.score(m), m)
    return res


def main() -> None:
    a = sys.argv[1:]
    opt = {"--from": "0", "--to": "", "--step": "0.5", "--hold": "1.0", "--top": "12"}
    videos, crops = [], []
    i = 0
    while i < len(a):
        if a[i] == "--crop":
            crops.append(tuple(int(v) for v in a[i + 1].split(","))); i += 2
        elif a[i] in opt:
            opt[a[i]] = a[i + 1]; i += 2
        else:
            videos.append(a[i]); i += 1
    if not videos:
        sys.exit(__doc__)
    step, hold, top = float(opt["--step"]), float(opt["--hold"]), int(opt["--top"])
    hold_steps = max(1, round(hold / step))
    rows = []
    for v in videos:
        w, h, dur = probe(v)
        cs = crops or default_crops(w, h)
        t0, t1 = float(opt["--from"]), float(opt["--to"] or dur)
        res = scan(v, t0, min(t1 + hold, dur), step, cs)
        for (t, c), (s0, m) in res.items():
            later = res.get((round(t + hold_steps * step, 3), c))
            if later is None or t > t1:
                continue
            rows.append((min(s0, later[0]), s0, later[0], m, Path(v).name, t, c))
    rows.sort(key=lambda r: -r[0])
    print(f"{'score':>5} {'@t':>5} {'@t+' + str(hold):>7}  busy dead color  video  t  crop(x,y,w,h)")
    for s, s0, s1, m, name, t, c in rows[:top]:
        print(f"{s:5.1f} {s0:5.1f} {s1:7.1f}  {m['busy']:.2f} {m['dead']:.2f} {m['color']:5.1f}  {name}  {t:g}  {','.join(map(str, c))}")


if __name__ == "__main__":
    main()
