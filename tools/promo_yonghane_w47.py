"""용하네 소개 영상 약 26초(1080x1920 · 24fps) — 운영 사이트 실제 화면(폰 폭) + 문구 띠 + 끝 화면.

재료: C:/Users/petbl/ego/yonghane-video-20261114-2130/frames/{A,B,C}/*.jpg
  ego-browser 로 www.yonghane.com 을 폰 폭(432x768 · 배율 2.5)으로 열어 한 장씩 찍은 것(round-04 · round-09).
  A = 첫 화면(히어로) → 네 가지 풀이 → 봐주지 않는 이유
  B = 앱이 내는 예시 인물(가상의 인물)의 사주 풀이 · 웹툰 보기. 출생 정보 줄은 화면 밖에서 시작한다.
  C = 이용권 안내가 나오는 자리
문구 출처 — 여기서 짓지 않는다:
  · 「2027 신년운세, 돈 내고 보지 마세요」 — 장부 E044(2027 띠별 한 해 · 토정 내년 괘) · E037(결제 버튼 없음). 2026-11-16 사용자 「무료 사주앱, 신년운세 강조」
  · 「사주 · 토정비결 · 점성술 · 타로」 · 「로그인 없이」 · 끝 화면 두 줄 — 장부 E038
  · 「풀이는 웹툰처럼 넘겨 봅니다」 — 장부 E039
  · 「결제 버튼이 없습니다」 · 「나머지는 1시간 이용권」 — 장부 E037
  · 「출생 정보는 이 기기 안에서만 계산합니다」 — 장부 E014
  · 「광고 없음」은 쓰지 않는다(2026-11-15 사용자 — 광고는 할 계획)
소리: 없음(무음 트랙). 합성 음성 없음. 웹툰 그림은 앱 화면 그대로 — 사실적 생성 영상이 아니다.

  python tools/promo_yonghane_w47.py
"""
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
SRC = Path('C:/Users/petbl/ego/yonghane-video-20261114-2130/frames')
OUT = ROOT / 'out/video/yh-intro-w47'
FB = 'C:/Windows/Fonts/malgunbd.ttf'
W, H, FPS = 1080, 1920, 24
NAVY, GOLD, CREAM = (11, 13, 20), (226, 190, 120), (245, 240, 230)

# (장면, 시작 프레임, 끝 프레임(미포함), 문구 줄들, 오른쪽 위 꼬리표)
CAPS = [
    ('A', 0, 104, ['2027 신년운세', '돈 내고 보지 마세요'], '실제 화면'),
    ('A', 104, 196, ['사주 · 토정비결 · 점성술 · 타로', '로그인 없이'], '실제 화면'),
    ('B', 0, 92, ['풀이는 웹툰처럼', '넘겨 봅니다'], '실제 화면 · 예시 인물(가상의 인물)'),
    ('B', 92, 166, ['결제 버튼이 없습니다'], '실제 화면 · 예시 인물(가상의 인물)'),
    ('B', 166, 266, ['출생 정보는', '이 기기 안에서만 계산합니다'], '실제 화면 · 예시 인물(가상의 인물)'),
    ('C', 0, 80, ['나머지는 1시간 이용권', '돈 주고 사는 게 아닙니다'], '실제 화면 · 예시 인물(가상의 인물)'),
]
END_FRAMES = 78
FADE = 6


def font(size):
    return ImageFont.truetype(FB, size)


def overlay(lines, tag):
    im = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    f_t = font(28)
    tw = d.textlength(tag, font=f_t)
    d.rounded_rectangle((W - tw - 64, 150, W - 24, 202), 14, fill=(0, 0, 0, 165))
    d.text((W - tw - 44, 157), tag, font=f_t, fill=(255, 255, 255, 235))
    f = font(60)
    lh = 84
    bw = max(d.textlength(ln, font=f) for ln in lines) + 96
    bh = lh * len(lines) + 56
    x0, y0 = (W - bw) / 2, 1250 - bh / 2
    d.rounded_rectangle((x0, y0, x0 + bw, y0 + bh), 34, fill=(8, 10, 16, 225), outline=GOLD + (255,), width=3)
    y = y0 + 26
    for ln in lines:
        w = d.textlength(ln, font=f)
        d.text(((W - w) / 2, y), ln, font=f, fill=(255, 255, 255, 255))
        y += lh
    return im


def end_card():
    im = Image.new('RGB', (W, H), NAVY)
    d = ImageDraw.Draw(im)

    def center(text, y, size, fill):
        f = font(size)
        w = d.textlength(text, font=f)
        d.text(((W - w) / 2, y), text, font=f, fill=fill)

    center('용하네', 520, 150, GOLD)
    center('듣기 좋은 말만 하지 않습니다.', 780, 62, CREAM)
    center('계산대로 말합니다.', 870, 62, CREAM)
    d.line((340, 1010, 740, 1010), fill=GOLD, width=3)
    center('프로필 링크에서 바로', 1060, 54, (255, 255, 255))
    center('www.yonghane.com', 1140, 54, GOLD)
    center('화면은 실제 앱 · 풀이는 앱이 내는 예시 인물(가상의 인물) 결과', 1300, 30, (170, 170, 180))
    center('@my_ajae', 1360, 34, (200, 200, 205))
    return im


def main():
    fdir = OUT / 'frames'
    fdir.mkdir(parents=True, exist_ok=True)
    for old in fdir.glob('*.jpg'):
        old.unlink()
    n = 0
    for scene, a, b, lines, tag in CAPS:
        ov = overlay(lines, tag)
        for i in range(a, b):
            base = Image.open(SRC / scene / f'{i:04d}.jpg').convert('RGBA')
            k = min(1.0, (i - a + 1) / FADE, (b - i) / FADE)
            layer = ov.copy()
            layer.putalpha(layer.getchannel('A').point(lambda v, k=k: int(v * k)))
            Image.alpha_composite(base, layer).convert('RGB').save(fdir / f'{n:05d}.jpg', quality=93)
            n += 1
    end = end_card()
    for _ in range(END_FRAMES):
        end.save(fdir / f'{n:05d}.jpg', quality=93)
        n += 1
    dst = OUT / 'yonghane-intro-w47.mp4'
    subprocess.run([
        'ffmpeg', '-y', '-loglevel', 'error', '-framerate', str(FPS), '-i', str(fdir / '%05d.jpg'),
        '-f', 'lavfi', '-i', 'anullsrc=r=48000:cl=stereo',
        '-c:v', 'libx264', '-preset', 'slow', '-crf', '18', '-pix_fmt', 'yuv420p', '-r', str(FPS),
        '-c:a', 'aac', '-b:a', '128k', '-shortest', '-movflags', '+faststart', str(dst)], check=True)
    end.save(OUT / 'end.jpg', quality=93)
    print(dst, f'{n} 장 · {n / FPS:.1f}초')


if __name__ == '__main__':
    main()
