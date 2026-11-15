#!/usr/bin/env python3
"""Where does one picture hold too long? Run on a rendered mp4 (Shorts or long-form).

User feedback 2026-11-04 on a long-form hook: "루즈해서 이탈할 것 같은데" — new picture every 1–3 s, silent number
cards that change on the spoken word. This finds the stretches where the picture barely changes.

    python3 scripts/hold_check.py <video.mp4> [--max 5.0] [--thresh 0.04]

How: ffmpeg scene scores on a 320-px copy (every frame), a "change" = scene score >= --thresh. Default 0.015 was set on
one of our long-form drafts: at 0.04 a number card swapping its big number was missed; at 0.015 card swaps,
punch-ins and b-roll cuts count while a steady talking head does not — so what remains are mostly long one-camera
speaker clips (fix: punch-ins at phrase changes) or cards/stills held under one long narration line.
"""
import argparse
import re
import subprocess

ap = argparse.ArgumentParser()
ap.add_argument("video")
ap.add_argument("--max", type=float, default=5.0, help="report holds longer than this (s)")
ap.add_argument("--thresh", type=float, default=0.015, help="scene score that counts as a picture change")
a = ap.parse_args()

dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", a.video],
                           capture_output=True, text=True, check=True).stdout)
log = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", a.video, "-an", "-vf",
                      f"scale=320:-2,select='gte(scene\\,{a.thresh})',metadata=print", "-f", "null", "-"],
                     capture_output=True, text=True).stderr
cuts = [float(t) for t in re.findall(r"pts_time:([0-9.]+)", log)]
marks = [0.0] + cuts + [dur]
holds = [(s, e) for s, e in zip(marks, marks[1:]) if e - s > a.max]
gaps = [e - s for s, e in zip(marks, marks[1:])]
print(f"{a.video}: {dur:.1f}s · {len(cuts)} picture changes (≥{a.thresh}) · median gap {sorted(gaps)[len(gaps) // 2]:.1f}s")
for s, e in holds:
    print(f"  hold {int(s // 60)}:{s % 60:04.1f} – {int(e // 60)}:{e % 60:04.1f}  ({e - s:.1f}s)")
print(f"{len(holds)} holds over {a.max:.0f}s" if holds else f"OK — no picture holds over {a.max:.0f}s")
