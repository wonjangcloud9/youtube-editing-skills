#!/usr/bin/env python3
"""Real-voice narration -> HyperFrames audio: cut long pauses, then speed up.

    python3 scripts/tighten_audio.py <episode dir> <speed> [id ...]     (default: every assets/audio_raw/*.mp3)

Internal pauses > 0.33 s become 0.28 s, the tail becomes 0.12 s (silencedetect −35 dB / 0.15 s), then atempo=<speed>.
Writes assets/audio/<id>.mp3 (tightened, 1×) and hf/assets/audio/<id>.wav (48 kHz, sped up); creates both folders.
Speeds we use: Shorts ko 1.1 · en 1.05 · long-form 1.05. Then: uv run scripts/align_narration.py <ep> hf/assets/audio
and read every line's transcript against the script (Julian misread '작은' as '자벤' once -> write it '자근').
"""
import re
import subprocess
import sys
from pathlib import Path


def dur(path: Path) -> float:
    return float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)],
                                capture_output=True, text=True, check=True).stdout)


def tighten(ep: Path, sid: str, speed: str) -> None:
    src = ep / f"assets/audio_raw/{sid}.mp3"
    d = dur(src)
    log = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", str(src), "-af", "silencedetect=noise=-35dB:d=0.15", "-f", "null", "-"],
                         capture_output=True, text=True).stderr
    st = [float(x) for x in re.findall(r"silence_start: ([0-9.]+)", log)]
    en = [float(x) for x in re.findall(r"silence_end: ([0-9.]+)", log)]
    keep, cur = [], 0.0
    for a, b in zip(st, en):
        if b >= d - 0.02:
            keep.append((cur, min(d, a + 0.12))); cur = None
            break
        if b - a > 0.33:
            keep.append((cur, a + 0.14)); cur = b - 0.14
    if cur is not None:
        keep.append((cur, d))
    fc = "".join(f"[0:a]atrim={a:.3f}:{b:.3f},asetpts=PTS-STARTPTS[p{i}];" for i, (a, b) in enumerate(keep))
    fc += "".join(f"[p{i}]" for i in range(len(keep))) + f"concat=n={len(keep)}:v=0:a=1,aresample=44100,asetnsamples=n=1152:p=0[o]"  # fixed frame size: libmp3lame rejects odd last frames (11-08 V14)
    mid, out = ep / f"assets/audio/{sid}.mp3", ep / f"hf/assets/audio/{sid}.wav"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(src), "-filter_complex", fc, "-map", "[o]", "-c:a", "libmp3lame", "-b:a", "192k", str(mid)], check=True)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(mid), "-filter:a", f"atempo={speed}", "-ar", "48000", str(out)], check=True)
    print(f"{sid}: {d:.2f}s -> {dur(out):.2f}s at x{speed}")


def main() -> None:
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    ep, speed = Path(sys.argv[1]), sys.argv[2]
    (ep / "assets/audio").mkdir(parents=True, exist_ok=True)
    (ep / "hf/assets/audio").mkdir(parents=True, exist_ok=True)
    ids = sys.argv[3:] or sorted(p.stem for p in (ep / "assets/audio_raw").glob("*.mp3"))
    for sid in ids:
        tighten(ep, sid, speed)


if __name__ == "__main__":
    main()
