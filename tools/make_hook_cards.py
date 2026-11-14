"""훅 카드 — 불만을 첫 줄에 놓은 글(L0021~L0026)의 그림. 1080x1350 JPEG.

글자는 게시물 JSON 의 `card_tag` · `card`(줄바꿈으로 나눔, `*` 로 시작하는 줄은 강조색) · `card_sub` 를 그대로 쓴다 — 여기서 짓지 않는다.
가운데 그림은 불만의 모양을 단순한 도형으로 그린 것이다. 어느 앱의 실제 화면도 아니고 용하네 화면도 아니다(AGENTS §2-7 — 앱 화면의 값은 지어내지 않는다).

  python tools/make_hook_cards.py            # L0021~L0026 전부
  python tools/make_hook_cards.py L0022
"""
import json
import math
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
W, H = 1080, 1350
NOTO = 'C:/Windows/Fonts/NotoSansKR-VF.ttf'
BG, INK, GOLD, HOT, DIM = (10, 12, 22), (255, 255, 255), (226, 190, 120), (255, 214, 92), (150, 156, 178)
RED = (235, 78, 70)


def font(size, weight='Black'):
    f = ImageFont.truetype(NOTO, size)
    try:
        f.set_variation_by_name(weight)
    except Exception:
        pass
    return f


def center(d, text, y, f, fill):
    w = d.textlength(text, font=f)
    d.text(((W - w) / 2, y), text, font=f, fill=fill)


def fit(d, text, size, max_w):
    while size > 60 and d.textlength(text, font=font(size)) > max_w:
        size -= 4
    return size


def star(d, cx, cy, r, fill, outline=None):
    pts = []
    for i in range(10):
        a = -math.pi / 2 + i * math.pi / 5
        rr = r if i % 2 == 0 else r * 0.42
        pts.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
    d.polygon(pts, fill=fill, outline=outline)


# ---- 가운데 그림(도형) : 영역 y 790~1090 ----
def m_ad(d):
    for i, (x, y) in enumerate([(170, 800), (250, 850), (330, 900)]):
        d.rounded_rectangle((x, y, x + 580, y + 190), 26, fill=(236, 238, 244) if i == 2 else (90, 96, 120))
        if i == 2:
            d.text((x + 36, y + 30), '광고', font=font(40, 'Bold'), fill=(120, 124, 140))
            d.rounded_rectangle((x + 36, y + 100, x + 400, y + 124), 12, fill=(200, 204, 214))
            d.rounded_rectangle((x + 36, y + 140, x + 300, y + 160), 10, fill=(214, 218, 226))
            cx, cy = x + 580 - 54, y + 54
            d.ellipse((cx - 40, cy - 40, cx + 40, cy + 40), fill=RED)
            d.line((cx - 16, cy - 16, cx + 16, cy + 16), fill=INK, width=9)
            d.line((cx - 16, cy + 16, cx + 16, cy - 16), fill=INK, width=9)


def bubble(d, x, y, w, h, text, fill, ink, right=False):
    d.rounded_rectangle((x, y, x + w, y + h), 40, fill=fill)
    tip = [(x + w - 70, y + h - 4), (x + w - 30, y + h + 34), (x + w - 110, y + h - 4)] if right else [(x + 70, y + h - 4), (x + 30, y + h + 34), (x + 110, y + h - 4)]
    d.polygon(tip, fill=fill)
    f = font(44, 'Bold')
    d.text((x + (w - d.textlength(text, font=f)) / 2, y + (h - 62) / 2), text, font=f, fill=ink)


def m_chat(d):
    bubble(d, 420, 800, 520, 100, '그 일주 아닌데요?', HOT, BG, right=True)
    bubble(d, 140, 950, 600, 100, '죄송합니다. 다시 볼게요.', (236, 238, 244), (40, 44, 60))


def m_diff(d):
    for k, (x, label) in enumerate([(130, 'A 앱'), (590, 'B 앱')]):
        d.rounded_rectangle((x, 800, x + 360, 1080), 28, fill=(28, 32, 54), outline=(70, 76, 104), width=3)
        d.text((x + 28, 818), label, font=font(36, 'Bold'), fill=DIM)
        for i in range(4):
            bx = x + 28 + i * 80
            hot = i == 0
            d.rounded_rectangle((bx, 890, bx + 66, 1040), 14, fill=(HOT if k else GOLD) if hot else (60, 66, 92))
            if hot:
                ch = '?' if k else '!'
                f = font(64)
                d.text((bx + (66 - d.textlength(ch, font=f)) / 2, 918), ch, font=f, fill=BG)
    f = font(96)
    center(d, '≠', 880, f, RED)


def m_login(d):
    for i, (label, fill, ink) in enumerate([('카카오로 로그인', (254, 229, 0), (40, 36, 20)), ('구글로 로그인', (245, 245, 248), (50, 54, 70)), ('네이버로 로그인', (3, 199, 90), INK)]):
        y = 800 + i * 100
        d.rounded_rectangle((210, y, 870, y + 80), 20, fill=fill)
        f = font(40, 'Bold')
        d.text((210 + (660 - d.textlength(label, font=f)) / 2, y + 12), label, font=f, fill=ink)
    f = font(150)
    d.text((880, 830), '?', font=f, fill=RED)


def m_bell(d):
    for i in range(5):
        y = 790 + i * 62
        x = 150 + (i % 2) * 24
        d.rounded_rectangle((x, y, x + 760, y + 86), 22, fill=(236, 238, 244), outline=(190, 194, 206), width=2)
        d.ellipse((x + 20, y + 18, x + 70, y + 68), fill=RED)
        d.text((x + 92, y + 14), '알림', font=font(38, 'Bold'), fill=(40, 44, 60))
        d.rounded_rectangle((x + 200, y + 34, x + 560, y + 52), 9, fill=(196, 200, 212))
        d.text((x + 640, y + 22), '방금', font=font(30, 'Medium'), fill=(130, 134, 150))


def m_star(d):
    d.rounded_rectangle((170, 800, 910, 1080), 30, fill=(28, 32, 54), outline=(70, 76, 104), width=3)
    d.text((210, 826), '오늘의 운세', font=font(42, 'Bold'), fill=DIM)
    for i in range(5):
        star(d, 290 + i * 125, 965, 54, HOT if i == 0 else (58, 64, 92))


MOTIF = {'L0021': m_ad, 'L0022': m_chat, 'L0023': m_diff, 'L0024': m_login, 'L0025': m_bell, 'L0026': m_star}


def make(pid):
    post = json.loads((ROOT / f'posts/list/{pid}.json').read_text(encoding='utf-8'))
    im = Image.new('RGB', (W, H), BG)
    d = ImageDraw.Draw(im)
    d.rectangle((0, 0, W, 14), fill=GOLD)
    # 꼬리표
    f_tag = font(46, 'Bold')
    tw = d.textlength(post['card_tag'], font=f_tag)
    d.rounded_rectangle(((W - tw) / 2 - 36, 96, (W + tw) / 2 + 36, 182), 43, outline=GOLD, width=3)
    center(d, post['card_tag'], 106, f_tag, GOLD)
    # 큰 글자
    lines = post['card'].split('\n')
    size = min(fit(d, ln.lstrip('*'), 150, W - 110) for ln in lines)
    y = 250 if len(lines) == 2 else 230
    for ln in lines:
        hot = ln.startswith('*')
        center(d, ln.lstrip('*'), y, font(size), HOT if hot else INK)
        y += int(size * 1.36)
    MOTIF[pid](d)
    # 아래
    center(d, post['card_sub'], 1140, font(46, 'Bold'), INK)
    d.line((390, 1232, 690, 1232), fill=(60, 66, 92), width=2)
    center(d, '용하네  ·  @my_ajae', 1254, font(34, 'Medium'), GOLD)
    out = ROOT / f'out/cards/list/{pid}.jpg'
    im.save(out, quality=94)
    return out


if __name__ == '__main__':
    ids = sys.argv[1:] or list(MOTIF)
    for pid in ids:
        print(make(pid))
