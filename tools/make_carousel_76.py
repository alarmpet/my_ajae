"""캐러셀 6장(1080x1350 JPEG) — 「76만 회 쇼츠 만든 순서」. 글자는 장부 E019 · E021 에서만.

  python tools/make_carousel_76.py
"""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
JOB = Path('D:/auto-cf/jobs/20261022-ai-sofa')
OUT = ROOT / 'out/cards/W46/carousel-76'
W, H = 1080, 1350
INK, ORANGE, YELLOW, WHITE, GRAY = (24, 24, 28), (255, 140, 50), (255, 214, 64), (250, 247, 240), (190, 190, 195)
FB, FR, FM = 'C:/Windows/Fonts/malgunbd.ttf', 'C:/Windows/Fonts/malgun.ttf', 'C:/Windows/Fonts/consola.ttf'


def f(size, path=FB):
    return ImageFont.truetype(path, size)


def wrap(d, text, font, max_w):
    out = []
    for para in text.split('\n'):
        cur = ''
        for word in para.split(' '):
            t = (cur + ' ' + word).strip()
            if d.textlength(t, font=font) > max_w and cur:
                out.append(cur); cur = word
            else:
                cur = t
        out.append(cur)
    return out


def base(n):
    im = Image.new('RGB', (W, H), INK)
    d = ImageDraw.Draw(im)
    d.rectangle((0, 0, W, 12), fill=ORANGE)
    d.text((70, H - 90), f'{n} / 6', font=f(34, FR), fill=GRAY)
    tag = '@my_ajae'
    d.text((W - 70 - d.textlength(tag, font=f(34, FR)), H - 90), tag, font=f(34, FR), fill=GRAY)
    return im, d


def block(d, y, text, size, col, font=FB, max_w=W - 140, x=70):
    fo = f(size, font)
    for ln in wrap(d, text, fo, max_w):
        d.text((x, y), ln, font=fo, fill=col)
        y += int(size * 1.4)
    return y


def ai_tag(d, text='AI 생성 이미지'):
    fs = f(28)
    tw = d.textlength(text, font=fs)
    d.rounded_rectangle((W - tw - 70, 40, W - 30, 92), 12, fill=(0, 0, 0))
    d.text((W - tw - 50, 46), text, font=fs, fill=WHITE)


def paste_fit(im, src, box):
    x, y, w, h = box
    s = Image.open(src).convert('RGB')
    r = min(w / s.width, h / s.height)
    s = s.resize((int(s.width * r), int(s.height * r)))
    im.paste(s, (x + (w - s.width) // 2, y + (h - s.height) // 2))


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    # 1 표지
    im, d = base(1)
    s = Image.open(JOB / 'sofa_pop_start4.jpg').convert('RGB')
    s = s.resize((W, int(s.height * W / s.width)))
    top = int(s.height * 0.28)  # 강아지가 가운데 오게 위아래를 잘라 가로를 꽉 채운다
    im.paste(s.crop((0, top, W, top + 760)), (0, 12))
    ai_tag(d)
    y = block(d, 820, '코딩 모르는 40대가', 64, WHITE)
    y = block(d, y, '76만 회 쇼츠를 만든 순서', 76, YELLOW)
    block(d, y + 20, '내가 없을 때도 우리 집 강아지가 즐거웠으면 해서', 40, GRAY)
    im.save(OUT / '01.jpg', quality=92)
    # 2 구조
    im, d = base(2)
    y = block(d, 160, '① 구조부터', 80, ORANGE)
    y = block(d, y + 40, '평범한 강아지 영상처럼 시작해', 64, WHITE)
    block(d, y + 10, '마지막에 반전이 온다', 64, YELLOW)
    block(d, 760, '소파에서 간식 먹던 강아지 → 집주인이 오자 자는 척 → 마지막에 꼬리를 흔든다', 46, GRAY)
    im.save(OUT / '02.jpg', quality=92)
    # 3 끝 장면 먼저
    im, d = base(3)
    y = block(d, 120, '② 끝 장면을 먼저 정한다', 66, ORANGE)
    block(d, y + 10, '시작 장면 1장 + 끝 장면 1장을 AI 그림으로', 44, WHITE)
    paste_fit(im, JOB / 'sofa_pop_start4.jpg', (60, 360, 470, 800))
    paste_fit(im, JOB / 'sofa_pop_end1.jpg', (550, 360, 470, 800))
    ai_tag(d)
    im.save(OUT / '03.jpg', quality=92)
    # 4 실제로 쓴 묘사 문장
    im, d = base(4)
    y = block(d, 120, '③ 실제로 쓴 장면 묘사', 66, ORANGE)
    y = block(d, y + 30, '시작 장면', 44, YELLOW)
    y = block(d, y, 'home security camera frame of a small fluffy cream Pomeranian sitting on a sofa like a lazy human at movie night, a red-white striped popcorn bucket of dog biscuits in its lap', 40, WHITE, FM)
    y = block(d, y + 30, '끝 장면', 44, YELLOW)
    y = block(d, y, 'lying curled up on a leather sofa, pretending to sleep but ONE eye slightly open peeking toward the camera', 40, WHITE, FM)
    block(d, y + 30, '영상 생성 프롬프트 원문은 남아 있지 않다', 36, GRAY)
    im.save(OUT / '04.jpg', quality=92)
    # 5 AI 가 AI 를 검사
    im, d = base(5)
    y = block(d, 140, '④ AI 그림은 AI 에게 검사시킨다', 62, ORANGE)
    y = block(d, y + 20, '후보 4장마다 이렇게 묻는다', 44, GRAY)
    for q in ['다리가 몇 개 보이나', '발이 사람 손처럼 생기지 않았나', '진짜 보안카메라처럼 보이나 1~5']:
        y = block(d, y + 30, '· ' + q, 54, WHITE)
    block(d, y + 60, '고르는 건 사람', 60, YELLOW)
    im.save(OUT / '05.jpg', quality=92)
    # 6 마무리
    im, d = base(6)
    y = block(d, 160, '⑤ 사이 10초는 Google Flow', 64, ORANGE)
    y = block(d, y + 30, '두 그림 사이를 프레임 모드로 채운다', 48, WHITE)
    y = block(d, y + 60, '제목은 사람이 정하고', 56, WHITE)
    y = block(d, y, 'AI 표시는 켜고 올린다', 56, YELLOW)
    y = block(d, y + 80, '우리 집 강아지가 내가 없을 때도 이렇게 즐거웠으면 하는 마음으로 만들었다.', 44, GRAY)
    block(d, y + 40, '아재도 한다', 72, ORANGE)
    im.save(OUT / '06.jpg', quality=92)
    sheet = Image.new('RGB', (W // 4 * 6, H // 4), 'white')
    for i in range(6):
        sheet.paste(Image.open(OUT / f'0{i + 1}.jpg').resize((W // 4, H // 4)), (i * (W // 4), 0))
    sheet.save(OUT / 'sheet.png')
    print(OUT)


if __name__ == '__main__':
    main()
