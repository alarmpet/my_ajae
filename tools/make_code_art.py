"""실제 코드 줄을 그대로 옮겨 그린 「편집기 화면」 그림(1080x1080 PNG) — 목록형 글의 카드 배경 (2026-11-13).

글자는 지어내지 않는다: 원본 파일의 지정한 줄을 그 자리에서 읽어 그린다. 줄이 길면 끝을 「…」로 자른다.
출생 정보 · 토큰 · 계정 값이 든 줄은 고르지 않는다(AGENTS §2-7 · §4).

  python tools/make_code_art.py <원본파일> <줄범위,...> "<제목줄>" <out.png>
  예) python tools/make_code_art.py D:/auto-cf/bin/script.py 31,265-268,103-104 "auto-cf/bin/script.py" out/art/list/L0001.png

그 뒤 tools/make_card.py 로 카드 글자를 얹는다.
"""
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

W = H = 1080
MONO = ImageFont.truetype('C:/Windows/Fonts/consola.ttf', 30)
KO = ImageFont.truetype('C:/Windows/Fonts/malgun.ttf', 28)
TITLE = ImageFont.truetype('C:/Windows/Fonts/malgunbd.ttf', 28)
BG, PANEL, FG, DIM, CMT, ACC = (24, 25, 30), (32, 34, 40), (225, 228, 235), (110, 115, 128), (120, 190, 120), (255, 140, 50)


def ranges(spec):
    out = []
    for part in spec.split(','):
        a, _, b = part.partition('-')
        out.append((int(a), int(b or a)))
    return out


def draw_mixed(d, xy, text, fill, max_x, wrap_x=None, max_rows=3, row_h=46):
    """ASCII 는 Consolas, 나머지(한글)는 맑은 고딕. 넘치면 다음 줄로 접고(최대 max_rows), 그래도 넘치면 「…」. 쓴 줄 수를 돌려준다."""
    x, y = xy
    wrap_x = wrap_x or x
    rows = 1
    for ch in text:
        if 0x2600 <= ord(ch) < 0x2C00 or ord(ch) >= 0x1F000 or ord(ch) == 0xFE0F:
            continue  # 그림 문자(⚠️ 🧭 등)는 글꼴에 없어 네모로 나온다 — 건너뛴다
        f = MONO if ord(ch) < 128 else KO
        w = d.textlength(ch, font=f)
        if x + w > max_x - 20:
            if rows >= max_rows:
                d.text((x, y), '…', font=KO, fill=DIM)
                return rows
            rows += 1
            x, y = wrap_x, y + row_h
            if ch == ' ':
                continue
        d.text((x, y + (2 if f is KO else 0)), ch, font=f, fill=fill)
        x += w
    return rows


def make(src, spec, title, out):
    lines = Path(src).read_text(encoding='utf-8').splitlines()
    img = Image.new('RGB', (W, H), BG)
    d = ImageDraw.Draw(img)
    top, bottom = 130, 950  # make_card 가 가운데 860px 띠만 쓴다
    d.rounded_rectangle((40, top, W - 40, bottom), 18, fill=PANEL)
    for i, c in enumerate([(255, 95, 86), (255, 189, 46), (39, 201, 63)]):
        d.ellipse((70 + i * 34, top + 26, 90 + i * 34, top + 46), fill=c)
    d.text((190, top + 18), title, font=TITLE, fill=ACC)
    rs = ranges(spec)
    probe = ImageDraw.Draw(Image.new('RGB', (W, H)))  # 접힌 줄 수를 먼저 재서 가운데에 놓는다
    rows = (len(rs) - 1) * 40
    for a, b in rs:
        for ln in range(a, b + 1):
            t = lines[ln - 1].rstrip()
            rows += 46 * draw_mixed(probe, (130, 0), t, FG, W - 40,
                                    wrap_x=130 + probe.textlength(t[:len(t) - len(t.lstrip())], font=MONO) + 24)
    y = max(top + 90, top + 70 + ((bottom - top - 70) - rows) // 2)  # 줄 묶음을 판 가운데로
    for n, (a, b) in enumerate(rs):
        if n:
            d.text((66, y), '· · ·', font=MONO, fill=DIM)
            y += 40
        for ln in range(a, b + 1):
            text = lines[ln - 1].rstrip()
            d.text((60, y), f'{ln:>3}', font=MONO, fill=DIM)
            stripped = text.lstrip()
            col = CMT if stripped.startswith('#') or stripped.startswith('//') else FG
            indent = 130 + d.textlength(text[:len(text) - len(stripped)], font=MONO)
            y += 46 * draw_mixed(d, (130, y), text, col, W - 40, wrap_x=indent + 24)
            if y > bottom - 40:
                break
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    img.save(out)
    print(out)


if __name__ == '__main__':
    if len(sys.argv) != 5:
        sys.exit(__doc__)
    make(*sys.argv[1:])
