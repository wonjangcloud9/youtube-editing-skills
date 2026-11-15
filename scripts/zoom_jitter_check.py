#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["numpy>=1.26"]
# ///
"""확대·이동 장면이 흔들리는지 숫자로 검사 (사진을 천천히 확대할 때 1px씩 툭툭 튀는 문제).

천천히 확대하는 사진 장면에서 프레임 사이 이동을 위상상관으로 잼. 고르게 움직이면 정수 1px 이동이 거의 없고,
ffmpeg zoompan처럼 정수 픽셀로 반올림하면 "멈췄다 1px 툭"이 반복된다.
  old zoompan: 멈췄다-툭 판정 ✗  →  scripts/kenburns.py: OK (빠른 확대는 1px 이동이 계속돼도 고르면 OK)

    uv run scripts/zoom_jitter_check.py out/draft_long.mp4 --at 22.4 --dur 10   # 사진·지도 장면 구간만
"""
import argparse
import subprocess

import numpy as np

ap = argparse.ArgumentParser()
ap.add_argument("video")
ap.add_argument("--at", type=float, default=0.0)
ap.add_argument("--dur", type=float, default=8.0)
a = ap.parse_args()
raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", str(a.at), "-t", str(a.dur), "-i", a.video,
                      "-vf", "scale=1920:1080,crop=640:360:640:360,format=gray", "-f", "rawvideo", "-"], capture_output=True).stdout
F = np.frombuffer(raw, np.uint8).reshape(-1, 360, 640).astype(np.float32)
sh = []
for x, y in zip(F, F[1:]):
    A, B = np.fft.fft2(x - x.mean()), np.fft.fft2(y - y.mean())
    R = A * np.conj(B); R /= np.abs(R) + 1e-9
    c = np.fft.ifft2(R).real; dy, dx = np.unravel_index(np.argmax(c), c.shape)
    sh.append((dx - 640 if dx > 320 else dx, dy - 360 if dy > 180 else dy))
sh = np.array(sh, float)
moving = np.abs(sh).sum(1) > 0
jump = moving.mean()
stopgo = (moving[1:] != moving[:-1]).mean()  # 멈춤↔1px 이동이 번갈아 나오는 비율 = 흔들림의 모양(고르게 빠른 확대는 계속 1px이라 낮음)
print(f"{a.video} @{a.at}s+{a.dur}s: 멈췄다-툭 {stopgo:.0%} (1px 이동 {jump:.0%}) → {'흔들림 ✗' if stopgo > 0.15 else 'OK'}")
