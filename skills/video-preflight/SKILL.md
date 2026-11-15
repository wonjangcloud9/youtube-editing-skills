---
name: video-preflight
description: Checks to run on a rendered video before calling it finished — captions under the Shorts UI, pictures that sit still too long, shaky zooms, loudness, caption sync — plus actually looking at frames. Use after every render and before telling the user a video is done.
---

# video-preflight

Run on the **rendered file**, not on the project:

| Check | Command | Fails when |
|---|---|---|
| Captions hidden by Shorts UI | `uv run scripts/safe_zone_check.py out/final.mp4` | text below y 1344 or under the right-hand button column |
| Boring holds | `python3 scripts/hold_check.py out/final.mp4 --max 5` | one picture stays > 5 s |
| Shaky zoom | `uv run scripts/zoom_jitter_check.py out/final.mp4 --at <s> --dur <s>` | stop-then-jump ratio > 15 % (ffmpeg `zoompan` does this; use `scripts/kenburns.py`) |
| Loudness | `ffmpeg -i out/final.mp4 -af loudnorm=print_format=summary -f null -` | outside −14…−17 LUFS, true peak above −1 dBTP |
| Opening picture candidates | `uv run scripts/ff_candidates.py <source.mp4>` | (before the edit) pick an opening that is still the same scene 1 s later |

Then **look**: extract frames at 0 s, 1 s and the middle of several captions, tile them, and read them. Typical finds: caption unreadable on a light background, a head cropped, a name tag sitting on top of a slide, a 3-line caption.

A failing check is a finding — fix the video, not the check. Report what you ran with the numbers; anything you could not verify, say so.
