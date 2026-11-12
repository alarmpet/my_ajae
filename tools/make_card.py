"""카드 합성 — 그림(글자 없음) 위에 카드 글자를 얹어 1080x1350 JPEG(인스타 4:5)로 만든다.

글자는 AI 그림에 넣지 않는다(한글이 틀리기 쉽다). 글자는 게시물 JSON 의 `card` 를 그대로 쓴다 — 여기서 짓지 않는다.

  python tools/make_card.py posts/<id>.json <그림.png> out/cards/<id>.jpg
"""
import json
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

W, H = 1080, 1350
FONT_B = 'C:/Windows/Fonts/malgunbd.ttf'
FONT_R = 'C:/Windows/Fonts/malgun.ttf'

# docs/plan.md §3 앱별 색 (만드는 사람 이야기는 숯색 + 주황)
THEME = {
    'yonghane': ((22, 30, 64), (214, 175, 84)),
    'vocarider': ((52, 30, 94), (38, 198, 190)),
    'wildcrown': ((24, 64, 40), (250, 204, 60)),
    'maker': ((34, 34, 38), (255, 140, 50)),
}
APP_NAME = {'yonghane': '용하네', 'vocarider': '보카라이더', 'wildcrown': '와일드 크라운', 'maker': '아재도 한다'}


def wrap(draw, text, font, max_w):
    lines, cur = [], ''
    for ch in text:
        if draw.textlength(cur + ch, font=font) > max_w and cur:
            cut = cur.rfind(' ')
            if cut > 0:
                lines.append(cur[:cut]); cur = cur[cut + 1:] + ch
            else:
                lines.append(cur); cur = ch
        else:
            cur += ch
    if cur:
        lines.append(cur)
    return lines


def make(post, art_path, out_path):
    bg, acc = THEME.get(post.get('app'), THEME['maker'])
    card = Image.new('RGB', (W, H), bg)
    art = Image.open(art_path).convert('RGB')
    s = min(art.size)
    band_top = 860
    art = art.crop(((art.width - s) // 2, (art.height - s) // 2, (art.width + s) // 2, (art.height + s) // 2)).resize((W, W), Image.LANCZOS)
    off = (W - band_top) // 2  # 정사각 그림의 위아래를 같게 잘라 띠 위에 맞춘다
    card.paste(art.crop((0, off, W, off + band_top)), (0, 0))
    d = ImageDraw.Draw(card)
    # 아래 글자 띠
    d.rectangle((0, band_top, W, H), fill=bg)
    d.rectangle((0, band_top, W, band_top + 10), fill=acc)
    text = post['card']
    size = 78
    while size > 44:
        f = ImageFont.truetype(FONT_B, size)
        lines = wrap(d, text, f, W - 140)
        if len(lines) <= 3:
            break
        size -= 4
    y = band_top + 60
    for ln in lines:
        d.text((70, y), ln, font=f, fill=(250, 247, 240))
        y += int(size * 1.3)
    small = ImageFont.truetype(FONT_R, 34)
    d.text((70, H - 80), f"{APP_NAME.get(post.get('app'), '')}", font=small, fill=acc)
    tag = '@my_ajae'
    d.text((W - 70 - d.textlength(tag, font=small), H - 80), tag, font=small, fill=(200, 200, 200))
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    card.save(out_path, 'JPEG', quality=92)


if __name__ == '__main__':
    if len(sys.argv) != 4:
        sys.exit(__doc__)
    make(json.load(open(sys.argv[1], encoding='utf-8')), sys.argv[2], sys.argv[3])
    print(sys.argv[3])
