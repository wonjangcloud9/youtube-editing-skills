---
name: voice-cut
description: Turn one rough voice recording (the creator reads a numbered script once, re-reading lines they fluff) into clean per-line audio files with tightened pauses, a slight speed-up and even loudness. Use when the user hands over a narration recording ("녹음본", "목소리 녹음했어").
---

# voice-cut

1. **Transcribe with word times** (`scripts/align_words.py`) and map each script line to the words that were actually said. If a line was read twice, keep the **last** take. If the speaker changed the wording, captions follow the recording, not the script.
2. **Find speech intervals** with `ffmpeg -af silencedetect=n=-42dB:d=0.35`; cut each line on those boundaries (pad 0.06 s, 0.12 s at the line end), keep in-line pauses at min(original, 0.30 s).
3. **Speed 1.05×** (`atempo`) — tighter without sounding rushed. Do not boost a quiet, echoey recording by 15 dB; that amplifies the room.
4. Write `<line id>.wav` + `durations.json`; the video builder places pictures from those durations. Example: `examples/cut_voice.py`.
5. **Mix**: voice → loudnorm −15 LUFS; music under it with sidechain ducking; check each line's voice-minus-music gap (≥ 10 dB).
6. Verify on the final file: re-transcribe it and confirm every line is present and each first caption starts within ±0.1 s of the voice.
