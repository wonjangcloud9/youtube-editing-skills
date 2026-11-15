---
name: clip-to-short
description: Cut one complete thought (20–25 s) out of a long talk or livestream into a 9:16 Short with the speaker's original voice and translated captions timed to the words. Use when asked to make a Short from a talk, interview, keynote or podcast ("쇼츠 만들어", "이 발표에서 쇼츠 뽑아줘").
---

# clip-to-short

Goal: a Short that is one person's whole thought in their own voice, captions that appear the instant the words start, and nothing hidden under the Shorts buttons.

## Steps
1. **Find the passage in text first.** Fetch captions only (`yt-dlp --skip-download --write-auto-subs`), search them for a passage that stands alone: a claim, a number, a turn ("but…"), an ending line. Auto captions are wrong about names and numbers — treat them as a map, not as the quote.
2. **Download only that passage** — `yt-dlp --download-sections "*<start>-<end>" --force-keyframes-at-cuts`, with ~10 s of margin each side. Never bulk-download; pause between requests and stop at the first 429.
3. **Word timestamps** — `scripts/align_words.py` (Whisper large-v3-turbo; usage in its header) → words with start/end seconds. Re-check every name, number and key word against the audio and against what is on the slide.
4. **Pick the pieces.** Keep whole sentences; cut only inside real pauses (`ffmpeg -af silencedetect=n=-32dB:d=0.35`). Drop filler stretches and stretched words. Total 20–25 s. Put the strongest picture/number first.
5. **Captions.** One caption per spoken phrase, start = that phrase's first word (never earlier than 0.15 s before the voice), max 2 lines, ~11 Korean characters per line at 72 px. Translate what was said, not the slide.
6. **Layout (1080×1920).** Title at top 170 px / 92 px type; name + event under it; captions end above y = 1344 and left of x = 888 (Shorts UI). If the slide behind the captions is light, lay a dark gradient band under them.
7. **Build and render** — see `examples/talk_shorts_build.py` (ffmpeg crops per piece, alternate a 1.07 punch-in so jump cuts read as cuts, HyperFrames page for title/captions, voice normalised to −15 LUFS with a quiet music bed).
8. **Look at it.** Extract 6 frames across the render and read every caption on them. Then run the `video-preflight` skill.

## Rules
- Quote only what the audio says; keep the source link, speaker, event and date in the description.
- Short excerpt, credited, transformed with translation. If the rights holder objects, take it down.
- Do not say "done" until you have looked at frames from the rendered file.
