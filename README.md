# youtube-editing-skills

Claude Code로 유튜브 영상을 만들 때 실제로 쓰는 스킬과 검사 도구입니다. 편집 프로그램 없이 코드로 자르고, 자막을 말에 맞추고, 다 만든 뒤 스스로 검사합니다.

유튜브 [원장코딩](https://www.youtube.com/channel/UChisjP6QUB8c1tDV_uOK4Uw)에서 쓰는 것들이고, 만든 것들은 [여기](https://wonjangcloud9.github.io/ai-game-battle/)에서 볼 수 있어요.

## 들어 있는 것

**스킬** — `skills/` 폴더를 내 프로젝트의 `.claude/skills/`에 복사하면 Claude Code가 씁니다.

| 스킬 | 하는 일 |
|---|---|
| `clip-to-short` | 긴 발표·인터뷰에서 한 생각(20~25초)만 잘라 세로 쇼츠로. 원본 목소리 + 말에 맞춘 번역 자막 |
| `voice-cut` | 대충 한 번 읽은 녹음을 줄마다 자르고, 다시 읽은 줄은 마지막 것만, 속도·크기 맞춤 |
| `video-preflight` | 다 구운 영상에 돌리는 검사: 자막이 쇼츠 버튼에 가리는지, 한 화면이 너무 오래 서 있는지, 확대가 떨리는지, 소리 크기 |
| `research-loop` | 30분마다 혼자 도는 조사 한 바퀴: 근거 찾기 → 후보를 표에 쌓기 |

**검사 도구** — `scripts/`

| 파일 | 하는 일 |
|---|---|
| `safe_zone_check.py` | 쇼츠 화면에서 제목·버튼에 가리는 자리에 글씨가 있으면 경고 + 빨갛게 칠한 장면 모음 |
| `hold_check.py` | 한 그림이 N초 넘게 안 바뀌는 구간 찾기 |
| `zoom_jitter_check.py` | 사진 확대 장면이 1px씩 튀는지 숫자로 |
| `kenburns.py` | 안 튀는 확대·이동 (ffmpeg zoompan 대신) |
| `ff_candidates.py` | 원본 영상에서 첫 화면으로 쓸 만한 순간 찾기 |
| `align_words.py` | 단어마다 몇 초에 나오는지 (Whisper) |
| `tighten_audio.py` | 녹음의 쉼 줄이기 + 속도 |

**예시** — `examples/`: 실제로 영상을 만든 빌더 두 개(발표 → 쇼츠, 녹음 → 줄별 음성). 경로는 자기 프로젝트에 맞게 고쳐야 돌아갑니다.

## 필요한 것
- [Claude Code](https://claude.com/claude-code)
- `ffmpeg`, [`uv`](https://docs.astral.sh/uv/), `yt-dlp`
- [HyperFrames](https://www.npmjs.com/package/hyperframes) — HTML로 짠 화면을 영상으로 굽는 도구 (`npm i hyperframes`)
- (선택) 그림이 필요할 때 Higgsfield 같은 이미지 생성 도구

## 쓰는 법
```bash
git clone https://github.com/wonjangcloud9/youtube-editing-skills
cp -r youtube-editing-skills/skills/* 내프로젝트/.claude/skills/
cp -r youtube-editing-skills/scripts 내프로젝트/scripts
```
그다음 Claude Code에서 "이 발표에서 쇼츠 하나 만들어 줘"처럼 말하면 됩니다.

## 알아 둘 것
- 남의 영상은 짧게, 출처를 밝히고, 번역 자막을 붙여 씁니다. 권리자가 싫어하면 내립니다.
- 영상을 한꺼번에 많이 받지 마세요. 필요한 구간만, 천천히.
- 검사 기준(쇼츠 가림 자리 등)은 공식 규격이 아니라 실제 화면을 보고 잡은 값입니다.

MIT License
