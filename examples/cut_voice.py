# 예시: 한 번에 읽은 목소리 녹음(assets/audio_raw/full_take1.m4a, 98초) → 줄마다 자르기. LINES의 구간은 이 녹음 전용 — 자기 녹음에 맞게 바꿔야 함.
# 구간 = 쉼(−42 dB 아래 0.35초+) 사이 말소리. 6번 줄 첫 시도(34.87~38.39 "지도 API 키와…")는 버리고 다시 읽은 것만 씀.
# 조각 사이 쉼은 원래 길이와 0.30초 중 짧은 쪽, 1.05배속(1·2라운드와 같음) → hf/assets/audio/<id>.wav
import json, subprocess
from pathlib import Path
EP = Path(__file__).resolve().parent
SRC = EP / "assets/audio_raw/full_take1.m4a"
LINES = {
    "N01": [(4.60, 6.58), (7.38, 9.49)], "N02": [(9.98, 12.91), (15.48, 16.84)], "N03": [(18.55, 20.09), (20.63, 21.95)],
    "N04": [(22.63, 24.48), (25.09, 26.90)], "N05": [(27.94, 29.21), (29.67, 32.05), (32.70, 33.84)],
    "N06": [(38.87, 41.74), (42.12, 43.64), (44.32, 45.92), (46.46, 48.71)], "N07": [(49.47, 52.03), (52.69, 54.34)],
    "N08": [(55.55, 56.85), (57.25, 60.73)], "N09": [(61.36, 62.78), (63.31, 66.21)],
    "N10": [(66.70, 68.58), (68.98, 70.38), (71.21, 73.23)], "N11": [(73.71, 77.18)],
    "N12": [(77.81, 78.76), (79.27, 80.38), (80.95, 84.55)], "N13": [(85.16, 86.71), (87.25, 89.25)], "N14": [(90.53, 92.80), (93.55, 96.19)],
}
SPEED = 1.05
(EP / "hf/assets/audio").mkdir(parents=True, exist_ok=True)
D = {}
for sid, rng in LINES.items():
    fc, n = [], 0
    for i, (s, e) in enumerate(rng):
        a, b = s - 0.06, e + (0.12 if i == len(rng) - 1 else 0.06)
        fc.append(f"[0:a]atrim={a:.3f}:{b:.3f},asetpts=PTS-STARTPTS,afade=t=in:d=0.012,afade=t=out:st={b - a - 0.02:.3f}:d=0.02[p{n}]"); n += 1
        if i < len(rng) - 1:
            gap = max(min(rng[i + 1][0] - e, 0.30) - 0.12, 0.05)
            fc.append(f"anullsrc=r=24000:cl=mono,atrim=0:{gap:.3f}[p{n}]"); n += 1
    fc.append("".join(f"[p{k}]" for k in range(n)) + f"concat=n={n}:v=0:a=1,atempo={SPEED}[o]")
    out = EP / f"hf/assets/audio/{sid}.wav"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(SRC), "-filter_complex", ";".join(fc), "-map", "[o]", "-ar", "48000", "-ac", "1", "-c:a", "pcm_s16le", str(out)], check=True)
    D[sid] = round(float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(out)], capture_output=True, text=True).stdout), 2)
    print(sid, D[sid])
(EP / "hf/assets/audio/durations.json").write_text(json.dumps(D))
(EP / "hf/assets/audio/lines.json").write_text(json.dumps(LINES))
print("total", round(sum(D.values()), 1))
