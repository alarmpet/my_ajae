"""보카라이더 홍보 영상 20초(1080x1920 · 24fps) — 실제 게임 녹화 + 문구 띠 + 끝 화면.

입력: out/video/vr-gameplay/gameplay.mp4 · events.json
  (D:/study-game 의 tools/promo/record-gameplay.mjs --sec 30 --wrong 3 --tier fast --boost --step --fps 24 로 녹화)
문구 출처 — 여기서 짓지 않는다:
  · 「단어장 덮고, 핸들 잡으세요.」 사용자 결정(2026-11-12)
  · 「정답 간판으로 들어가면 답」 장부 E018
  · 「달리면서 영단어를 풀어요」 · 「틀린 단어는 바로 다시 나와요」 D:/study-game/.claude/skills/game-cf-video/SKILL.md §0 확정 문구
  · 「가입 없이 바로」 D:/study-game/src/trust.js:6
소리: 게임 자체 음원(D:/study-game/assets/audio) — 같은 게임의 CF 에 쓰던 것. 합성 음성(TTS) 없음 → AI 표시 대상 아님.

  python tools/promo_vocarider_w46.py
"""
import json
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / 'out/video/vr-gameplay'
OUT = ROOT / 'out/video/vr-promo-w46'
GAME_AUDIO = Path('D:/study-game/assets/audio')
FB = 'C:/Windows/Fonts/malgunbd.ttf'
W, H, FPS = 1080, 1920, 24
PURPLE, TEAL = (52, 30, 94), (38, 198, 190)

# (원본 시작, 원본 끝, 문구 띠, 큰 글씨 여부)
SEGS = [
    (0.0, 3.0, '단어장 덮고, 핸들 잡으세요.', True),
    (5.0, 9.5, '정답 간판으로 들어가면 답', False),
    (13.5, 16.5, '달리면서 영단어를 풀어요', False),
    (21.0, 27.5, '틀린 단어는 바로 다시 나와요', False),
]
END_SEC = 3.0


def font(size):
    return ImageFont.truetype(FB, size)


def overlay_png(path, text, big):
    im = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    # 오른쪽 위 「실제 게임 화면」 (game-cf-video §0)
    f_s = font(30)
    tag = '실제 게임 화면'
    tw = d.textlength(tag, font=f_s)
    d.rounded_rectangle((W - tw - 70, 250, W - 30, 305), 14, fill=(0, 0, 0, 150))
    d.text((W - tw - 50, 257), tag, font=f_s, fill=(255, 255, 255, 235))
    if big:
        f = font(92)
        lines = ['단어장 덮고,', '핸들 잡으세요.']
        y = 1000
        for ln in lines:
            w = d.textlength(ln, font=f)
            d.text(((W - w) / 2 + 4, y + 4), ln, font=f, fill=(0, 0, 0, 160))
            d.text(((W - w) / 2, y), ln, font=f, fill=(255, 255, 255, 255))
            y += 120
    else:
        f = font(64)
        w = d.textlength(text, font=f)
        top = H - 430
        d.rounded_rectangle(((W - w) / 2 - 40, top, (W + w) / 2 + 40, top + 120), 28, fill=PURPLE + (225,))
        d.rectangle(((W - w) / 2 - 40, top + 110, (W + w) / 2 + 40, top + 120), fill=TEAL + (255,))
        d.text(((W - w) / 2, top + 22), text, font=f, fill=(255, 255, 255, 255))
    im.save(path)


def end_png(path):
    im = Image.new('RGB', (W, H), PURPLE)
    d = ImageDraw.Draw(im)
    def center(t, f, y, col):
        w = d.textlength(t, font=f)
        d.text(((W - w) / 2, y), t, font=f, fill=col)
    center('단어장 덮고,', font(84), 640, (255, 255, 255))
    center('핸들 잡으세요.', font(84), 750, (255, 255, 255))
    center('보카라이더', font(120), 930, TEAL)
    center('가입 없이 바로', font(54), 1110, (230, 225, 245))
    center('@my_ajae', font(40), 1680, (200, 190, 220))
    im.save(path)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    events = json.loads((SRC / 'events.json').read_text(encoding='utf-8'))
    inputs, filters, labels = [], [], []
    t_out, sfx = 0.0, []
    for i, (a, b, text, big) in enumerate(SEGS):
        ov = OUT / f'ov{i}.png'
        overlay_png(ov, text, big)
        inputs += ['-ss', str(a), '-t', str(b - a), '-i', str(SRC / 'gameplay.mp4'), '-i', str(ov)]
        v, o = 2 * i, 2 * i + 1
        filters.append(f'[{v}:v]fps={FPS},scale={W}:{H},setsar=1[g{i}];[g{i}][{o}:v]overlay=0:0[s{i}]')
        labels.append(f'[s{i}]')
        for e in events:
            if a <= e['t'] < b and e['type'] in ('correct', 'boost', 'wrong'):
                sfx.append((t_out + e['t'] - a, {'correct': 'sfx_correct', 'boost': 'sfx_nitro', 'wrong': 'sfx_wrong'}[e['type']]))
        t_out += b - a
    end = OUT / 'end.png'
    end_png(end)
    n = len(SEGS) * 2
    inputs += ['-loop', '1', '-t', str(END_SEC), '-i', str(end)]
    filters.append(f'[{n}:v]fps={FPS},scale={W}:{H},setsar=1[s_end]')
    labels.append('[s_end]')
    filters.append(''.join(labels) + f'concat=n={len(labels)}:v=1:a=0,format=yuv420p[v]')
    total = t_out + END_SEC
    sfx.append((t_out, 'sfx_finish'))
    # 소리: 배경음악 + 효과음
    a0 = n + 1
    inputs += ['-i', str(GAME_AUDIO / 'bgm/fever.mp3')]
    amix = [f'[{a0}:a]atrim=0:{total},afade=t=out:st={total - 1.2}:d=1.2,volume=0.35[bgm]']
    alabels = ['[bgm]']
    for k, (t, name) in enumerate(sfx):
        inputs += ['-i', str(GAME_AUDIO / f'sfx/{name}.mp3')]
        ms = int(t * 1000)
        amix.append(f'[{a0 + 1 + k}:a]adelay={ms}|{ms},volume=0.9[x{k}]')
        alabels.append(f'[x{k}]')
    amix.append(''.join(alabels) + f'amix=inputs={len(alabels)}:normalize=0,atrim=0:{total},loudnorm=I=-16:TP=-1.5:LRA=11,aresample=48000[a]')
    fc = ';'.join(filters + amix)
    out = OUT / 'vocarider-promo-w46.mp4'
    cmd = ['ffmpeg', '-v', 'error', '-y', *inputs, '-filter_complex', fc, '-map', '[v]', '-map', '[a]',
           '-c:v', 'libx264', '-crf', '19', '-preset', 'medium', '-r', str(FPS), '-c:a', 'aac', '-b:a', '192k', '-ar', '48000',
           '-movflags', '+faststart', '-t', str(total), str(out)]
    subprocess.run(cmd, check=True)
    print(out, f'{total:.1f}s', 'sfx', [(round(t, 2), s) for t, s in sfx])


if __name__ == '__main__':
    main()
