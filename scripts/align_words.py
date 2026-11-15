#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["faster-whisper>=1.0", "numpy"]
# ///
"""Word-level timestamps for ranges of a source video, from the audio itself (Whisper).

YouTube auto-caption word times drift — especially over music, montages and cross-talk — so
subtitles timed from them start early or late. This transcribes each range with
faster-whisper (word_timestamps) and writes absolute start/end times per word.

    uv run scripts/align_words.py <video> <out.json> 0:22.8 1455:1497 …   (seconds, start:end)
"""
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
from faster_whisper import WhisperModel

MARGIN = 1.5  # seconds of context on each side so the first and last words are heard whole


def main() -> None:
    video, out, *ranges = sys.argv[1:]
    model = WhisperModel("small.en", device="cpu", compute_type="int8")
    words = []
    for r in ranges:
        a, b = (float(x) for x in r.split(":"))
        a0 = max(0.0, a - MARGIN)
        # decode with ffmpeg ourselves (16 kHz mono float) — faster-whisper's own PyAV decoding breaks across versions
        pcm = subprocess.run(["ffmpeg", "-loglevel", "error", "-ss", f"{a0}", "-t", f"{b - a0 + MARGIN}", "-i", video,
                              "-ac", "1", "-ar", "16000", "-f", "f32le", "-"], check=True, capture_output=True).stdout
        audio = np.frombuffer(pcm, dtype=np.float32)
        segs, _ = model.transcribe(audio, language="en", word_timestamps=True, beam_size=5,
                                   vad_filter=False, condition_on_previous_text=False)
        n = 0
        for seg in segs:
            for w in seg.words or []:
                s, e = a0 + w.start, a0 + w.end
                if a - 0.5 <= s <= b + 0.5:
                    words.append({"start": round(s, 3), "end": round(e, 3), "word": w.word.strip(), "p": round(w.probability, 3)})
                    n += 1
        print(f"  {a:8.2f}–{b:8.2f}: {n} words", flush=True)
    words.sort(key=lambda w: w["start"])
    Path(out).write_text(json.dumps(words, ensure_ascii=False, indent=0))
    print(f"✓ {out} ({len(words)} words)")


if __name__ == "__main__":
    main()
