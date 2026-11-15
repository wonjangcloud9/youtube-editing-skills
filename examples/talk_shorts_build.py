#!/usr/bin/env python3
"""ko-code 쇼츠 3개 — AI Engineer Code Summit 2026 (11-11) 발표에서 한 생각씩. 원본 목소리 + 한국어 자막, 내레이션·카드 없음.

    python3 build.py [s1 s2 s3]     # 구간 자르기(ffmpeg) → <id>/hf/index.html → 렌더 → out/<id>.mp4

원본 화면은 왼쪽 아래 발표자 카메라 칸(18,607 402×453) + 오른쪽 슬라이드(442,26 1440×810).
 solo  = 카메라 칸을 2.69배 키워 화면 가운데(머리 y≈700~980), 자막은 가슴 위(아래 끝 1320 — 쇼츠 버튼 줄 위)
 split = 위에 슬라이드(게임 화면) 1080×608, 아래 카메라(머리가 버튼 줄 위로 오게 잘라 올림), 자막은 슬라이드 아래쪽
구간·자막 시간은 source/*.words.json(Whisper large-v3-turbo) + 말소리 쉼(silencedetect)에서 잡음. 선반 규칙: 제목 top 170·92px, 자막 72px.
"""
import json, os, shutil, subprocess, sys
from pathlib import Path

EP = Path(__file__).resolve().parent
SRC = EP / "source"
HF = "hyperframes"
FONTS = Path("./templates/hf-short-ko/assets/fonts")
MUSIC = Path("./episodes/ko-code/2026-11-13-boris-learn-code-short/hf/assets/music/pulse_bed.wav")
EVENT = "AI Engineer Code Summit · 2026.11.11"
SIMON, YEGGE = "사이먼 윌리슨 · Django 공동 창시자", "스티브 예기 · 전 아마존·구글, 40년 차 개발자"

SHORTS = {
    "s1": dict(file="simon_31700", layout="solo", who=SIMON,
               title='AI가 다 해 주는데<br><em>왜 더 힘들까?</em>',
               pieces=[(17.72, 37.94), (42.90, 50.75)],
               subs=[(17.72, 19.50, "왜 제 일은\n더 힘들어졌을까요?", "why does my job feel harder?"),
                     (19.64, 22.30, "왜 더 열심히 일하고\n더 열심히 생각하고", "Why does it feel like I'm working harder, I'm thinking harder,"),
                     (22.30, 26.20, "개발자로 살면서\n지금 제일 몰아붙일까요?", "I'm pushing myself more than I ever have before in my career as a software engineer?"),
                     (26.28, 29.60, "진실은 이거예요\n쉬운 일은 다 처리됐어요", "And I think the truth is that the easy stuff is all handled now."),
                     (29.66, 33.90, "예전엔 한 시간 동안\n느긋하게 테스트를 고쳤죠", "It used to be I could relax and refactor some tests for an hour."),
                     (34.10, 37.94, "이젠 에이전트가 30초에\n저보다 잘하는데 왜 하겠어요", "Why would I do that now when an agent will refactor the test better than me in 30 seconds?"),
                     (42.90, 44.95, "투르 드 프랑스 챔피언\n그렉 르몽드가 말했죠", "This is Greg LeMond, a Tour de France champion. He said,"),
                     (45.05, 47.75, "쉬워지는 게 아니다\n빨라질 뿐이다", "it doesn't get easier, you just get faster."),
                     (47.82, 50.75, "지금 우리 모두에게\n딱 그 일이 벌어지고 있어요", "And I think that's exactly what's happening to all of us right now.")]),
    "s2": dict(file="yegge_29478", layout="solo", who=YEGGE,
               title='밀린 일 100년치<br><em>AI가 넉 달에 60년치</em>',
               pieces=[(14.50, 19.45), (22.85, 43.45)],
               subs=[(14.50, 17.80, "게임 유저들이 찾아와서\n로드맵을 달라고 했어요", "My players came to me asking for a roadmap."),
                     (17.80, 19.45, "제발 좀 천천히 하라고요", "They were like, you've got to slow down. It's too much."),
                     (22.85, 25.60, "제 소프트웨어 공장이", "My software factory, this thing,"),
                     (25.60, 28.60, "하루에 기능 50~100개를\n찍어냈거든요", "had been cranking out like 50 to 100 features a day."),
                     (29.30, 31.90, "시작할 때 밀린 일이\n100년치였는데", "I had 100 years of work in my backlog when I started this"),
                     (31.90, 34.55, "클로드가 넉 달 만에\n60년치를 해치웠어요", "and Claude got through about 60 years of it in about four months."),
                     (34.70, 36.05, "완전 미친 거죠", "It's absolute insanity."),
                     (36.90, 39.62, "하루 100개는\n볼 수도 없어요", "And they can't look at 100 features a day."),
                     (39.64, 43.45, "읽지도 못하는데\n테스트는 어떻게 해요", "They can't even read about 100 features a day, let alone play test them.")]),
    "s3": dict(file="simon_31590", layout="split", who=SIMON,
               title='AI가 만든 게임이 지루해서<br><em>"더 재밌게 만들어" 했더니</em>',
               pieces=[(18.50, 21.30), (25.60, 32.30), (33.50, 41.90), (51.02, 56.80)],
               subs=[(18.50, 21.30, "커맨드 앤 컨커처럼 생겼는데\n진짜 지루했어요", "and it looks like Command & Conquer, and it's really dull."),
                     (25.60, 28.65, "그래서 생각했죠\n오퍼스 5.5한테 이러면 어떨까", "I thought, what happens if I say to Opus 5.5,"),
                     (28.74, 32.30, "\"이 게임 아직 재미없어\n훨씬 재밌게 만들어\"", "this game isn't fun enough yet. Make it a lot more fun."),
                     (33.50, 36.35, "끔찍하게도\n진짜 그렇게 했어요", "And I'm horrified to announce that it just did."),
                     (37.10, 39.05, "클로드가 12시간을 돌았어요", "Claude ran for 12 hours."),
                     (39.15, 41.90, "가상 전투 1,000판을\n직접 시험했고요", "It playtested 1,000 simulated battles."),
                     (51.02, 52.20, "그랬더니 게임이 재밌어졌어요", "the game was fun."),
                     (52.30, 56.80, "아… 재미를 아는 건\n사람만이 아니었네요", "and I'm like, oh, okay… turns out that is not unique to human beings.")]),
    "s4": dict(file="jarred_19790", layout="split", who="재러드 섬너 · Bun 만든 개발자 (Anthropic)", cam_y=612, light=True,
               event="AI Engineer Code Summit · 2026.11.12",
               title='AI가 2배 빠르게 만든 코드<br><em>왜 버렸을까?</em>',
               pieces=[(23.98, 27.08), (31.55, 33.70), (36.00, 37.95), (42.55, 43.85), (45.14, 54.20), (54.86, 58.45)],
               subs=[(23.98, 27.08, "그랬더니 시작 속도가\n2배 빨라졌고", "And then after that, startup time got two times faster"),
                     (31.55, 33.70, "메모리는 3배나\n덜 쓰게 됐어요", "started using about 3x less memory."),
                     (36.00, 37.95, "근데 그 코드가\n엉터리였어요", "But the code was slop."),
                     (42.55, 43.85, "이건 아니다 싶었죠", "this is not good."),
                     (45.14, 49.98, "'archive'라는 이름이\n어디 나오기만 해도", "this meant that any object that accessed a property called archive,"),
                     (49.98, 54.20, "그 기능을 쓰는 걸로\n넘겨짚는 코드였거든요", "it would then assume that the Bun.archive API was potentially used."),
                     (54.86, 57.40, "보자마자 말했어요\n이건 못 내보낸다", "And I looked at this and I was like, we cannot ship this."),
                     (57.40, 58.45, "이건 아니에요", "This is not good.")]),
}

SHORTS["s4_before"] = dict(SHORTS["s4"], light=False)   # 고치기 전 화면(만드는 법 영상용)

CSS = """
@font-face { font-family: "PL"; src: url("assets/fonts/Paperlogy-9Black.woff2") format("woff2"); font-weight: 900; }
@font-face { font-family: "PL"; src: url("assets/fonts/Paperlogy-6SemiBold.woff2") format("woff2"); font-weight: 600; }
* { margin: 0; padding: 0; box-sizing: border-box; }
html, body { width: 1080px; height: 1920px; overflow: hidden; background: #0E0C0B; }
#root { position: relative; width: 1080px; height: 1920px; overflow: hidden; font-family: "PL"; color: #F1ECE4; }
#bg { position: absolute; left: 0; top: 0; width: 1080px; height: 1920px; }
#top { position: absolute; left: 0; top: 0; width: 1080px; height: 520px; background: linear-gradient(180deg, #0E0C0B 0%, #0E0C0B 74%, rgba(14,12,11,0) 100%); }
#title { position: absolute; left: 60px; right: 60px; top: 170px; text-align: center; font-weight: 900; font-size: 92px; line-height: 1.14; letter-spacing: -0.02em; text-shadow: 0 3px 18px rgba(0,0,0,0.7); }
#title.sm { font-size: 78px; }
#title em { font-style: normal; color: #D4502F; }
#who { position: absolute; left: 0; right: 0; text-align: center; font-weight: 600; font-size: 34px; line-height: 1.35; text-shadow: 0 0 3px rgba(0,0,0,0.95), 0 2px 14px rgba(0,0,0,0.9); }
#who small { display: block; font-size: 28px; opacity: 0.78; }
.cap { position: absolute; left: 60px; right: 60px; text-align: center; }
.cap .t { display: inline-block; font-weight: 900; font-size: 72px; line-height: 1.2; letter-spacing: -0.01em; text-shadow: 0 0 4px rgba(0,0,0,0.95), 0 4px 22px rgba(0,0,0,0.9), 0 0 60px rgba(0,0,0,0.6); }
.cap .t.long { font-size: 62px; }
"""


def run(a):
    subprocess.run(a, check=True)


def build(sid):
    S = SHORTS[sid]; d = EP / sid / "hf"
    if not (d / "hyperframes.json").exists():
        d.parent.mkdir(exist_ok=True)
        subprocess.run([HF, "init", str(d), "--example", "blank", "--non-interactive", "--skip-skills", "--resolution", "portrait"], env={**os.environ, "HYPERFRAMES_SKIP_SKILLS": "1"}, capture_output=True)
    a = d / "assets"; (a / "fonts").mkdir(parents=True, exist_ok=True)
    for f in ("Paperlogy-9Black.woff2", "Paperlogy-6SemiBold.woff2"):
        src = FONTS / f
        shutil.copy(src if src.exists() else Path("./channels/ko-code/thumb_mock/fonts") / f, a / "fonts" / f)
    src = SRC / f"{S['file']}.mp4"
    # --- video: each piece → 1080×1920, alternate a slight punch-in so the jump cuts read as cuts
    parts, t0, T = [], 0.0, []
    for i, (s, e) in enumerate(S["pieces"]):
        z = 1.0 if i % 2 == 0 else 1.07
        cw, ch = int(402 / z) // 2 * 2, 0
        if S["layout"] == "solo":
            ch = int(453 / z) // 2 * 2
            cx, cy = 18 + (402 - cw) // 2, 607 + int((453 - ch) * 0.25)
            vf = (f"[0:v]crop={cw}:{ch}:{cx}:{cy},scale=1080:1218:flags=lanczos,unsharp=5:5:0.6[c];"
                  f"[0:v]crop=402:453:18:607,scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,boxblur=24:2,eq=brightness=-0.22:saturation=0.8[b];[b][c]overlay=0:400:shortest=1[v]")
        else:
            ch = int(300 / z) // 2 * 2
            cx, cy = 18 + (402 - cw) // 2, S.get('cam_y', 665) + int((300 - ch) * 0.25)
            vf = (f"[0:v]crop=1440:810:442:26,scale=1080:608:flags=lanczos[s];[0:v]crop={cw}:{ch}:{cx}:{cy},scale=1080:806:flags=lanczos,unsharp=5:5:0.6[c];"
                  f"[0:v]crop=402:453:18:607,scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,boxblur=24:2,eq=brightness=-0.22:saturation=0.8[b];[b][s]overlay=0:400:shortest=1[b2];[b2][c]overlay=0:1008:shortest=1[v]")
        out = a / f"p{i}.mp4"; dur = e - s
        run(["ffmpeg", "-v", "error", "-y", "-ss", f"{s:.3f}", "-t", f"{dur:.3f}", "-i", str(src), "-filter_complex",
             vf + f";[0:a]afade=t=in:d=0.02,afade=t=out:st={dur - 0.03:.3f}:d=0.03[a]", "-map", "[v]", "-map", "[a]", "-r", "30",
             "-c:v", "libx264", "-crf", "16", "-preset", "fast", "-pix_fmt", "yuv420p", "-c:a", "pcm_s16le", "-ar", "48000", "-t", f"{dur:.3f}", str(a / f"p{i}.mov")])
        parts.append(a / f"p{i}.mov"); T.append((s, e, t0)); t0 += dur
    total = round(t0, 3)
    (a / "list.txt").write_text("\n".join(f"file '{p}'" for p in parts))
    run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(a / "list.txt"), "-an", "-c:v", "libx264", "-crf", "16", "-preset", "fast", "-g", "15", "-pix_fmt", "yuv420p", str(a / "track.mp4")])
    run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(a / "list.txt"), "-stream_loop", "-1", "-i", str(MUSIC), "-filter_complex",
         f"[0:a]highpass=f=70,acompressor=threshold=-20dB:ratio=3:attack=8:release=160,loudnorm=I=-15:TP=-1.5:LRA=9[v];[1:a]volume=0.13,atrim=0:{total},afade=t=out:st={total - 0.4:.3f}:d=0.4[m];[v][m]amix=inputs=2:normalize=0,volume=-1.6dB,alimiter=limit=0.84[o]",
         "-map", "[o]", "-t", f"{total}", "-ar", "48000", "-ac", "2", str(a / "mix.wav")])

    def tmap(x):                      # source time → output time
        for s, e, o in T:
            if s - 0.01 <= x <= e + 0.01: return o + min(max(x - s, 0), e - s)
        raise ValueError(f"{sid}: {x} outside the pieces")

    solo = S["layout"] == "solo"
    cap_css = "bottom: 600px;" if solo else "top: 808px;"
    who_css = "top: 404px;"
    body = []
    for i, (s, e, ko, en) in enumerate(S["subs"]):
        st, en_ = tmap(s), tmap(e)
        nxt = tmap(S["subs"][i + 1][0]) if i + 1 < len(S["subs"]) else total
        hold = min(nxt, en_ + 0.35)          # stay up through the short breath, never past the next line
        longc = " long" if max(len(l) for l in ko.split("\n")) > 13 else ""
        body.append(f'<div id="c{i}" class="cap clip" style="{cap_css}" data-start="{st:.3f}" data-duration="{max(hold - st, 0.4):.3f}" data-track-index="2"><div class="t{longc}">{ko.replace(chr(10), "<br />")}</div></div>')
    bands = ('<div style="position:absolute;left:0;top:398px;width:1080px;height:96px;background:linear-gradient(180deg,rgba(14,12,11,0.92) 0%,rgba(14,12,11,0.92) 70%,rgba(14,12,11,0) 100%)"></div>'
             '<div style="position:absolute;left:0;top:740px;width:1080px;height:270px;background:linear-gradient(180deg,rgba(14,12,11,0) 0%,rgba(14,12,11,0.88) 30%,rgba(14,12,11,0.94) 100%)"></div>') if S.get("light") else ""
    tcls = ' class="sm"' if len(S["title"]) > 60 else ""
    html = f"""<!doctype html>
<html lang="ko" data-resolution="portrait"><head><meta charset="UTF-8" /><meta name="viewport" content="width=1080, height=1920" />
<script src="https://cdn.jsdelivr.net/npm/gsap@3.15.0/dist/gsap.min.js"></script><style>{CSS}</style></head>
<body><div id="root" data-composition-id="main" data-start="0" data-duration="{total}" data-width="1080" data-height="1920">
  <video id="bg" class="clip" src="assets/track.mp4" data-start="0" data-duration="{total}" data-track-index="0" muted playsinline></video>
  <div id="top"></div>{bands}
  <div id="title"{tcls}>{S['title']}</div>
  <div id="who" style="{who_css}">{S['who']}<small>{S.get('event', EVENT)}</small></div>
  {chr(10).join('  ' + b for b in body)}
  <audio id="mix" src="assets/mix.wav" data-start="0" data-duration="{total}" data-volume="1"></audio>
</div>
<script>const tl = gsap.timeline({{ paused: true }}); tl.set({{}}, {{}}, {total}); window.__timelines["main"] = tl;</script></body></html>"""
    (d / "index.html").write_text(html)
    (EP / "out").mkdir(exist_ok=True)
    r = subprocess.run([HF, "render", "-o", str(EP / "out" / f"{sid}.mp4")], cwd=d, capture_output=True, text=True)
    print(sid, total, "s", "render ok" if r.returncode == 0 else "RENDER FAIL\n" + r.stdout[-600:] + r.stderr[-600:])


for sid in (sys.argv[1:] or [k for k in SHORTS if k != 's4_before']):
    build(sid)
