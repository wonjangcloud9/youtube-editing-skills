#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["pillow>=10"]
# ///
"""흔들림 없는 확대·이동(켄 번스) — 사진·지도용. 프레임을 raw RGB로 stdout에 씀(ffmpeg가 받아서 색·질감 입힘).

왜: ffmpeg zoompan은 확대 창 위치를 매 프레임 정수 픽셀로 반올림해서, 천천히 확대하면 1px씩 툭툭 흔들린다
(ffmpeg zoompan은 확대 창을 정수 픽셀로 반올림해서 흔들림). 여기서는 프레임마다 소수점 위치로 affine 샘플링한다.
zoompan으로 사진을 확대하지 말 것 — 이 스크립트나 HTML(GSAP scale)을 쓴다.

    uv run scripts/kenburns.py SRC --w 1920 --h 1080 --fps 30 --frames 300 --z0 1.0 --z1 1.1 --ox 0.5 --oy 0.45 \
        | ffmpeg -f rawvideo -pix_fmt rgb24 -s 1920x1080 -r 30 -i - ... out.mp4

SRC = 사진 파일(16:9로 꽉 차게 잘라 씀) 또는 번호 붙은 PNG 폴더(지도 선 그리기 프레임: --hold초까지 첫 장, 그다음 한 장씩, 끝은 마지막 장 유지).
--ox/--oy = 확대해 들어가는 점(화면 비율 0~1). 그 점이 화면에서 제자리에 있도록 확대한다.
--ease linear(기본, 같은 사진이 여러 장면에 이어질 때) | inout(한 장면 안에서 부드럽게 출발·도착)
"""
import argparse
import sys
from pathlib import Path

from PIL import Image, ImageOps

ap = argparse.ArgumentParser()
ap.add_argument("src")
ap.add_argument("--w", type=int, default=1920)
ap.add_argument("--h", type=int, default=1080)
ap.add_argument("--fps", type=float, default=30)
ap.add_argument("--frames", type=int, required=True)
ap.add_argument("--z0", type=float, default=1.0)
ap.add_argument("--z1", type=float, default=1.06)
ap.add_argument("--ox", type=float, default=0.5)
ap.add_argument("--oy", type=float, default=0.5)
ap.add_argument("--ease", default="linear", choices=["linear", "inout"])
ap.add_argument("--canvas", type=float, default=1.5, help="사진을 출력의 몇 배 크기로 깔고 샘플링할지(1.5면 확대 1.5배까지 선명)")
ap.add_argument("--hold", type=float, default=0.5, help="폴더 입력: 그리기 시작 전 첫 장을 보여 줄 초")
a = ap.parse_args()

src = Path(a.src)
if src.is_dir():
    seq = sorted(src.glob("*.png"))
    first = Image.open(seq[0]).convert("RGB")
    CW, CH = first.size
    cache = {}

    def frame_at(i):
        k = min(len(seq) - 1, max(0, i - round(a.hold * a.fps)))
        if k not in cache:
            cache.clear()
            cache[k] = Image.open(seq[k]).convert("RGB")
        return cache[k]
else:
    CW, CH = round(a.w * a.canvas), round(a.h * a.canvas)
    still = ImageOps.fit(Image.open(src).convert("RGB"), (CW, CH), Image.LANCZOS, centering=(a.ox, a.oy))

    def frame_at(i):
        return still

out = sys.stdout.buffer
n = max(1, a.frames - 1)
for i in range(a.frames):
    p = i / n
    if a.ease == "inout":
        p = p * p * (3 - 2 * p)
    z = a.z0 + (a.z1 - a.z0) * p
    vw, vh = CW / z, CH / z                      # 보이는 창 크기(원본 픽셀, 소수)
    x0, y0 = a.ox * CW * (1 - 1 / z), a.oy * CH * (1 - 1 / z)
    sx, sy = vw / a.w, vh / a.h
    img = frame_at(i).transform((a.w, a.h), Image.AFFINE, (sx, 0, x0, 0, sy, y0), resample=Image.BICUBIC)
    out.write(img.tobytes())
out.flush()
