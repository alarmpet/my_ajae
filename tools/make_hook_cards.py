"""훅 카드 2판 — 불만 글(L0021~L0026)마다 네 장 묶음. 1080x1350 JPEG.

왜 이 모양인가(2026-11-15 조사 `docs/research/2026-11-15-hook-cards.md`):
  사주 광고 그림 72장은 거의 전부 「사람 얼굴이 나오는 손그림 만화 + 말풍선 + 한 줄 사연 + 밝은 바탕 + 여러 장」이었다.
  스레드 인기 글 670개에서는 그림 네 장 이상이 한 장보다 반응이 좋았다(좋아요 중앙 84.5 대 44.5).
  1판(어두운 바탕 + 도형)은 사람 · 표정 · 사연이 없어 약했다(사용자 「너무 약해」).

네 장: ① 훅(표정 + 말풍선 + 사연 한 줄) ② 리뷰에서 본 불만의 모양 ③ 용하네는 이렇게 ④ 묻는 말.
글자는 게시물 JSON 의 `cards` 에서만 가져온다 — 여기서 짓지 않는다. 사람 그림은 단순한 낙서 캐릭터이고 실제 인물 · 실제 앱 화면이 아니다.

  python tools/make_hook_cards.py            # L0021~L0026
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
PAPER, INK, MARK = (253, 250, 243), (24, 24, 28), (255, 226, 92)
SKIN, BLUSH, RED = (255, 224, 196), (255, 160, 150), (232, 64, 56)
PASTEL = {'pink': (255, 214, 220), 'sky': (206, 230, 255), 'lilac': (226, 214, 250), 'yellow': (255, 238, 178), 'mint': (204, 240, 222), 'peach': (255, 222, 196)}
SHIRT = {'pink': (240, 110, 130), 'sky': (84, 140, 220), 'lilac': (140, 110, 210), 'yellow': (236, 170, 40), 'mint': (60, 170, 120), 'peach': (236, 130, 80)}


def font(size, weight='Black'):
    f = ImageFont.truetype(NOTO, size)
    try:
        f.set_variation_by_name(weight)
    except Exception:
        pass
    return f


def tw(d, t, f):
    return d.textlength(t, font=f)


def blob(d, cx, cy, rx, ry, fill):
    pts = []
    for i in range(72):
        a = i * math.pi / 36
        k = 1 + 0.06 * math.sin(3 * a + 0.7) + 0.04 * math.cos(5 * a)
        pts.append((cx + rx * k * math.cos(a), cy + ry * k * math.sin(a)))
    d.polygon(pts, fill=fill)


def marker_text(d, text, y, size, mark=True):
    """가운데 정렬 큰 글자. mark 면 글자 뒤에 형광펜."""
    f = font(size)
    w = tw(d, text, f)
    x = (W - w) / 2
    if mark:
        d.rounded_rectangle((x - 18, y + size * 0.62, x + w + 18, y + size * 1.22), 10, fill=MARK)
    d.text((x, y), text, font=f, fill=INK)


def person(d, cx, cy, s, shirt, mood='annoyed', hair='bob', phone=True):
    """낙서 캐릭터. (cx, cy) = 얼굴 가운데, s = 얼굴 반지름."""
    lw = max(5, int(s * 0.055))
    # 몸
    d.rounded_rectangle((cx - s * 1.25, cy + s * 0.85, cx + s * 1.25, cy + s * 3.4), int(s * 0.6), fill=shirt, outline=INK, width=lw)
    # 목
    d.rectangle((cx - s * 0.22, cy + s * 0.75, cx + s * 0.22, cy + s * 1.0), fill=SKIN)
    # 뒷머리
    if hair == 'bob':
        d.ellipse((cx - s * 1.22, cy - s * 1.25, cx + s * 1.22, cy + s * 1.35), fill=INK)
    # 얼굴
    d.ellipse((cx - s, cy - s, cx + s, cy + s), fill=SKIN, outline=INK, width=lw)
    # 앞머리
    if hair == 'bob':
        d.pieslice((cx - s * 1.08, cy - s * 1.2, cx + s * 1.08, cy + s * 0.5), 180, 360, fill=INK)
    else:
        d.pieslice((cx - s * 1.05, cy - s * 1.22, cx + s * 1.05, cy + s * 0.2), 180, 360, fill=INK)
    ey = cy + s * 0.12
    ex = s * 0.42
    # 눈 · 눈썹 · 입
    if mood == 'dizzy':
        for sx in (-1, 1):
            x0 = cx + sx * ex
            d.line((x0 - s * 0.14, ey - s * 0.14, x0 + s * 0.14, ey + s * 0.14), fill=INK, width=lw)
            d.line((x0 - s * 0.14, ey + s * 0.14, x0 + s * 0.14, ey - s * 0.14), fill=INK, width=lw)
    elif mood == 'tired':
        for sx in (-1, 1):
            x0 = cx + sx * ex
            d.line((x0 - s * 0.16, ey, x0 + s * 0.16, ey), fill=INK, width=lw + 2)
    else:
        for sx in (-1, 1):
            x0 = cx + sx * ex
            r = s * (0.13 if mood == 'shock' else 0.09)
            d.ellipse((x0 - r, ey - r, x0 + r, ey + r), fill=INK)
    if mood in ('annoyed', 'angry'):
        for sx in (-1, 1):
            x0 = cx + sx * ex
            d.line((x0 - sx * s * 0.2, ey - s * 0.36, x0 + sx * s * 0.16, ey - s * 0.22), fill=INK, width=lw)
    my = cy + s * 0.52
    if mood == 'shock':
        d.ellipse((cx - s * 0.14, my - s * 0.12, cx + s * 0.14, my + s * 0.2), fill=INK)
    elif mood in ('annoyed', 'angry', 'tired'):
        d.arc((cx - s * 0.22, my - s * 0.02, cx + s * 0.22, my + s * 0.3), 200, 340, fill=INK, width=lw)
    elif mood == 'dizzy':
        d.line((cx - s * 0.2, my + s * 0.06, cx - s * 0.07, my - s * 0.02, cx + s * 0.07, my + s * 0.1, cx + s * 0.2, my + s * 0.02), fill=INK, width=lw)
    else:
        d.line((cx - s * 0.16, my + s * 0.06, cx + s * 0.16, my + s * 0.06), fill=INK, width=lw)
    # 볼
    for sx in (-1, 1):
        d.ellipse((cx + sx * s * 0.66 - s * 0.13, cy + s * 0.34, cx + sx * s * 0.66 + s * 0.13, cy + s * 0.5), fill=BLUSH)
    # 땀 · 화남 표시
    if mood in ('annoyed', 'tired', 'dizzy', 'shock'):
        x0, y0 = cx + s * 0.92, cy - s * 0.55
        d.polygon([(x0, y0 - s * 0.26), (x0 - s * 0.12, y0), (x0 + s * 0.12, y0)], fill=(120, 190, 255))
        d.ellipse((x0 - s * 0.12, y0 - s * 0.1, x0 + s * 0.12, y0 + s * 0.14), fill=(120, 190, 255))
    if mood == 'angry':
        x0, y0 = cx + s * 0.78, cy - s * 0.78
        for a, b in (((-1, -0.3), (-0.3, -0.3)), ((-0.3, -0.3), (-0.3, -1)), ((0.3, -1), (0.3, -0.3)), ((0.3, -0.3), (1, -0.3)), ((1, 0.3), (0.3, 0.3)), ((0.3, 0.3), (0.3, 1)), ((-0.3, 1), (-0.3, 0.3)), ((-0.3, 0.3), (-1, 0.3))):
            d.line((x0 + a[0] * s * 0.16, y0 + a[1] * s * 0.16, x0 + b[0] * s * 0.16, y0 + b[1] * s * 0.16), fill=RED, width=lw)
    # 폰
    if phone:
        px, py = cx - s * 0.2, cy + s * 1.75
        d.rounded_rectangle((px, py, px + s * 0.95, py + s * 1.5), int(s * 0.14), fill=(40, 42, 52), outline=INK, width=lw)
        d.rounded_rectangle((px + s * 0.09, py + s * 0.12, px + s * 0.86, py + s * 1.32), int(s * 0.08), fill=(236, 240, 250))
        d.ellipse((px + s * 0.7, py + s * 1.2, px + s * 1.25, py + s * 1.72), fill=SKIN, outline=INK, width=lw)


def bubble(d, x, y, text, size=54, tail='left', fill=(255, 255, 255)):
    f = font(size, 'Bold')
    lines = text.split('\n')
    w = max(tw(d, ln, f) for ln in lines) + 80
    h = len(lines) * int(size * 1.4) + 52
    d.rounded_rectangle((x, y, x + w, y + h), 46, fill=fill, outline=INK, width=6)
    tx = x + 70 if tail == 'left' else x + w - 70
    d.polygon([(tx - 26, y + h - 4), (tx + 26, y + h - 4), (tx - 34 if tail == 'left' else tx + 34, y + h + 44)], fill=fill, outline=INK, width=6)
    d.line((tx - 21, y + h - 3, tx + 21, y + h - 3), fill=fill, width=8)
    ty = y + 24
    for ln in lines:
        d.text((x + (w - tw(d, ln, f)) / 2, ty), ln, font=f, fill=INK)
        ty += int(size * 1.4)
    return w, h


def foot(d, n, total, hint):
    f = font(34, 'Bold')
    d.text((70, 1272), '용하네 · @my_ajae', font=f, fill=(120, 116, 108))
    for i in range(total):
        x = W / 2 - (total - 1) * 16 + i * 32
        d.ellipse((x - 8, 1286, x + 8, 1302), fill=INK if i == n else (206, 200, 190))
    if hint:
        d.text((W - 70 - tw(d, hint, f), 1272), hint, font=f, fill=INK)


ART = {'L0021': 'c1-ad', 'L0022': 'c2-wrong', 'L0023': 'c3-differ', 'L0024': 'c4-login', 'L0025': 'c5-alarm', 'L0026': 'c6-star'}


def art_of(pid, c=None):
    """Google Flow(Nano Banana)로 그린 캐릭터 그림(글자 없음). 없으면 None — 그때는 낙서 캐릭터로 그린다.

    찾는 순서: 게시물 `cards.art`(저장소 기준 경로) → `out/art/hook/<글 번호>.jpg` → 아래 ART 표(첫 여섯 글).
    """
    cands = []
    if c and c.get('art'):
        cands.append(ROOT / c['art'])
    cands += [ROOT / f'out/art/hook/{pid}.jpg', ROOT / f'out/art/hook/{ART.get(pid, "_")}.jpg']
    for f in cands:
        if f.exists():
            return Image.open(f).convert('RGB')
    return None


def card_hook_art(c, art):
    bg = art.getpixel((12, 12))
    im = Image.new('RGB', (W, H), bg)
    im.paste(art.resize((W, W), Image.LANCZOS), (0, H - W))
    d = ImageDraw.Draw(im)
    f = font(46, 'Bold')
    d.text(((W - tw(d, c['tag'], f)) / 2, 70), c['tag'], font=f, fill=(90, 84, 80))
    lines = c['hook']
    size = 128
    while max(tw(d, ln, font(size)) for ln in lines) > W - 120:
        size -= 4
    y = 146
    for i, ln in enumerate(lines):
        marker_text(d, ln, y, size, mark=(i == len(lines) - 1))
        y += int(size * 1.28)
    bubble(d, 60, 640, c['bubble'], size=56, tail='right')
    d.rectangle((0, 1240, W, H), fill=PAPER)
    d.line((0, 1240, W, 1240), fill=INK, width=5)
    foot(d, 0, 4, '넘겨 보기 →')
    return im


def card_ask_art(c, art):
    bg = art.getpixel((12, 12))
    im = Image.new('RGB', (W, H), bg)
    k = 760
    im.paste(art.resize((k, k), Image.LANCZOS), (W - k, 1240 - k))
    d = ImageDraw.Draw(im)
    lines = c['ask']
    size = 100
    while max(tw(d, ln, font(size)) for ln in lines) > W - 120:
        size -= 4
    y = 150
    for i, ln in enumerate(lines):
        marker_text(d, ln, y, size, mark=(i == len(lines) - 1))
        y += int(size * 1.34)
    bubble(d, 70, 640, c.get('ask_bubble', '댓글로 알려 주세요'), size=50, tail='right')
    d.rectangle((0, 1240, W, H), fill=PAPER)
    d.line((0, 1240, W, 1240), fill=INK, width=5)
    foot(d, 3, 4, '')
    return im


def card_hook(c, color):
    im = Image.new('RGB', (W, H), PAPER)
    d = ImageDraw.Draw(im)
    f = font(46, 'Bold')
    d.text(((W - tw(d, c['tag'], f)) / 2, 78), c['tag'], font=f, fill=(110, 104, 96))
    lines = c['hook']
    size = 132
    while max(tw(d, ln, font(size)) for ln in lines) > W - 120:
        size -= 4
    y = 160
    for i, ln in enumerate(lines):
        marker_text(d, ln, y, size, mark=(i == len(lines) - 1))
        y += int(size * 1.3)
    blob(d, 560, 1010, 430, 300, PASTEL[color])
    person(d, 700, 900, 150, SHIRT[color], mood=c.get('mood', 'annoyed'), hair=c.get('hair', 'bob'))
    bubble(d, 90, 690, c['bubble'], size=56, tail='right')
    d.rectangle((0, 1240, W, H), fill=PAPER)
    d.line((0, 1240, W, 1240), fill=INK, width=5)
    foot(d, 0, 4, '넘겨 보기 →')
    return im


def card_list(c, color, n, title, items, numbered=True, hint='넘겨 보기 →', big=None):
    im = Image.new('RGB', (W, H), PAPER)
    d = ImageDraw.Draw(im)
    blob(d, 930, 170, 220, 170, PASTEL[color])
    f_t = font(70)
    y = 130
    for ln in title.split('\n'):
        w = tw(d, ln, f_t)
        d.rounded_rectangle((70 - 14, y + 46, 70 + w + 14, y + 92), 8, fill=MARK)
        d.text((70, y), ln, font=f_t, fill=INK)
        y += 100
    y += 50
    f = font(56, 'Bold')
    for i, it in enumerate(items):
        lines = it.split('\n')
        bh = len(lines) * 78 + 56
        d.rounded_rectangle((70, y, W - 70, y + bh), 34, fill=(255, 255, 255), outline=INK, width=5)
        if numbered:
            d.ellipse((100, y + bh / 2 - 38, 176, y + bh / 2 + 38), fill=SHIRT[color])
            num = str(i + 1)
            fn = font(46)
            d.text((138 - tw(d, num, fn) / 2, y + bh / 2 - 34), num, font=fn, fill=(255, 255, 255))
        ty = y + 26
        for ln in lines:
            d.text((206 if numbered else 110, ty), ln, font=f, fill=INK)
            ty += 78
        y += bh + 28
    if big:
        fb = font(50, 'Bold')
        d.text(((W - tw(d, big, fb)) / 2, min(y + 20, 1170)), big, font=fb, fill=(110, 104, 96))
    foot(d, n, 4, hint)
    return im


def card_ask(c, color):
    im = Image.new('RGB', (W, H), PASTEL[color])
    d = ImageDraw.Draw(im)
    lines = c['ask']
    size = 104
    while max(tw(d, ln, font(size)) for ln in lines) > W - 140:
        size -= 4
    y = 250
    for i, ln in enumerate(lines):
        marker_text(d, ln, y, size, mark=(i == len(lines) - 1))
        y += int(size * 1.34)
    person(d, 540, 900, 120, SHIRT[color], mood='plain', hair=c.get('hair', 'bob'), phone=False)
    bubble(d, 610, 700, c.get('ask_bubble', '댓글로\n알려 주세요'), size=46, tail='left')
    foot(d, 3, 4, '')
    return im


def make(pid):
    post = json.loads((ROOT / f'posts/list/{pid}.json').read_text(encoding='utf-8'))
    c = post['cards']
    color = c['color']
    art = art_of(pid, c)
    ims = [card_hook_art(c, art) if art else card_hook(c, color),
           card_list(c, color, 1, c['pain_title'], c['pain']),
           card_list(c, color, 2, c['answer_title'], c['answer'], numbered=c.get('answer_numbered', True), big=c.get('answer_note')),
           card_ask_art(c, art) if art else card_ask(c, color)]
    outs = []
    for i, im in enumerate(ims, 1):
        out = ROOT / f'out/cards/list/{pid}-{i}.jpg'
        im.save(out, quality=94)
        outs.append(out)
    return outs


if __name__ == '__main__':
    ids = sys.argv[1:] or ['L0021', 'L0022', 'L0023', 'L0024', 'L0025', 'L0026']
    for pid in ids:
        print(pid, len(make(pid)))
