"""「아재도 한다」 릴스 — 76만 회 강아지 쇼츠를 만든 이야기 (1080x1920 · 24fps · 약 22초).

재료(우리 채널의 우리 영상 — 남의 화면 없음):
  D:/auto-cf/jobs/20261022-ai-sofa/video/sofa_full_v3.mp4  (유튜브 joTy32Ny8Jk 로 올린 파일)
  D:/auto-cf/jobs/20261022-ai-sofa/sofa_pop_start4.jpg · sofa_pop_end1.jpg  (시작 · 끝 장면)
문구는 장부 E019 · E021 에서만 — 여기서 숫자를 짓지 않는다.
사실적 AI 생성 영상이 들어간다 → 화면에 「AI 생성 영상」 표시 + 플랫폼 AI 표시를 켠다(AGENTS §2-8).
글자 배치: 쇼츠 · 릴스 화면은 위 약 120px · 아래 약 25% · 오른쪽 아이콘 줄을 UI 가 덮는다 → 글자는 위쪽 안전 영역(가로 가운데)에만.

  python tools/promo_maker_76.py
"""
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parents[1]
JOB = Path('D:/auto-cf/jobs/20261022-ai-sofa')
SOFA = JOB / 'video/sofa_full_v3.mp4'
OUT = ROOT / 'out/video/maker-76'
FB = 'C:/Windows/Fonts/malgunbd.ttf'
FR = 'C:/Windows/Fonts/malgun.ttf'
W, H, FPS = 1080, 1920, 24
INK = (22, 22, 26)
WHITE, CREAM, YELLOW, ORANGE, GRAY = (255, 255, 255), (245, 240, 230), (255, 214, 92), (255, 150, 70), (200, 200, 205)


def font(size, bold=True):
    return ImageFont.truetype(FB if bold else FR, size)


def gradient_top(height, alpha_max=200):
    """위에서 아래로 옅어지는 검은 그라데이션(글자 뒤 받침) — 띠보다 화면을 덜 가린다."""
    g = Image.new('L', (1, height))
    for y in range(height):
        t = y / height
        g.putpixel((0, y), int(alpha_max * (1 - t) ** 1.6))
    shade = Image.new('RGBA', (W, height), (0, 0, 0, 255))
    shade.putalpha(g.resize((W, height)))
    return shade


def centered(d, y, text, size, fill, bold=True, shadow=True, layer=None):
    fo = font(size, bold)
    w = d.textlength(text, font=fo)
    x = (W - w) / 2
    if shadow and layer is not None:
        sh = Image.new('RGBA', layer.size, (0, 0, 0, 0))
        ImageDraw.Draw(sh).text((x, y + 4), text, font=fo, fill=(0, 0, 0, 170))
        layer.alpha_composite(sh.filter(ImageFilter.GaussianBlur(6)))
        d = ImageDraw.Draw(layer)
    d.text((x, y), text, font=fo, fill=fill)
    return y + int(size * 1.32)


def ai_pill(layer, text='AI 생성 영상'):
    d = ImageDraw.Draw(layer)
    fo = font(28)
    tw = d.textlength(text, font=fo)
    x1, y1 = (W - tw) / 2 - 22, 150
    d.rounded_rectangle((x1, y1, x1 + tw + 44, y1 + 50), 25, fill=(255, 255, 255, 46), outline=(255, 255, 255, 120), width=2)
    d.text((x1 + 22, y1 + 6), text, font=fo, fill=(255, 255, 255, 235))


def overlay(path, small, big, big_col):
    """작은 줄 + 큰 줄 두 단(가운데 정렬) + 위쪽 그라데이션 + 가운데 AI 표시 알약."""
    layer = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    layer.alpha_composite(gradient_top(720), (0, 0))
    ai_pill(layer)
    d = ImageDraw.Draw(layer)
    y = 250
    for line in small:
        y = centered(d, y, line, 50, CREAM, layer=layer)
        d = ImageDraw.Draw(layer)
    y += 14
    for line in big:
        y = centered(d, y, line, 96, big_col, layer=layer)
        d = ImageDraw.Draw(layer)
    layer.save(path)


def frames_slide(path):
    bg = Image.new('RGB', (W, H), INK)
    d = ImageDraw.Draw(bg)
    a = Image.open(JOB / 'sofa_pop_start4.jpg').convert('RGB')
    b = Image.open(JOB / 'sofa_pop_end1.jpg').convert('RGB')
    tw = 450
    a = a.resize((tw, int(a.height * tw / a.width)))
    b = b.resize((tw, int(b.height * tw / b.width)))
    top = 560
    for img, x in ((a, 60), (b, W - 60 - tw)):
        m = Image.new('L', img.size, 0)
        ImageDraw.Draw(m).rounded_rectangle((0, 0, img.width, img.height), 28, fill=255)
        bg.paste(img, (x, top), m)
    for x, t in ((60, '시작 장면'), (W - 60 - tw, '끝 장면')):
        w = d.textlength(t, font=font(44))
        d.text((x + (tw - w) / 2, top + a.height + 28), t, font=font(44), fill=YELLOW)
    for i, (t, s, c) in enumerate([('이 두 장 사이 10초를', 64, WHITE), ('Google Flow 가 채웠다', 64, WHITE)]):
        w = d.textlength(t, font=font(s))
        d.text(((W - w) / 2, 250 + i * 92), t, font=font(s), fill=c)
    t = '그림 · 영상 모두 AI 생성'
    w = d.textlength(t, font=font(36, False))
    d.text(((W - w) / 2, top + a.height + 110), t, font=font(36, False), fill=GRAY)
    bg.save(path)


def end_slide(path):
    bg = Image.new('RGB', (W, H), INK)
    d = ImageDraw.Draw(bg)
    rows = [('우리 집 강아지가', 72, CREAM), ('내가 없을 때도', 72, CREAM), ('이렇게 즐거웠으면.', 84, YELLOW),
            (None, 60, None), ('그 마음으로 만든 영상입니다.', 46, GRAY), (None, 120, None),
            ('아재도 한다', 92, ORANGE), ('@my_ajae', 40, GRAY)]
    y = 560
    for t, s, c in rows:
        if t:
            w = d.textlength(t, font=font(s))
            d.text(((W - w) / 2, y), t, font=font(s), fill=c)
        y += int(s * 1.4)
    bg.save(path)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    overlay(OUT / 'hook.png', ['코딩 모르는 40대가', 'AI랑 만든 영상 도구로'], ['유튜브 76만 회'], YELLOW)
    overlay(OUT / 'twist.png', ['내가 없을 때'], ['우리 집 강아지도', '이러고 놀면 좋겠다'], WHITE)
    frames_slide(OUT / 'frames.png')
    end_slide(OUT / 'end.png')
    # A 0~5.5 훅 · B 5.5~16 마음 · C 3.5초 시작/끝 장면 · D 3.5초 끝
    fc = (
        f'[0:v]trim=0:5.5,setpts=PTS-STARTPTS,fps={FPS},scale={W}:{H},setsar=1[a0];[a0][1:v]overlay[A];'
        f'[0:v]trim=5.5:16,setpts=PTS-STARTPTS,fps={FPS},scale={W}:{H},setsar=1[b0];[b0][2:v]overlay[B];'
        f'[3:v]fps={FPS},scale={W}:{H},setsar=1[C];[4:v]fps={FPS},scale={W}:{H},setsar=1[D];'
        '[A][B][C][D]concat=n=4:v=1:a=0,format=yuv420p[v];'
        '[0:a]atrim=0:16,asetpts=PTS-STARTPTS[s1];[0:a]atrim=0:7,asetpts=PTS-STARTPTS,volume=0.25,afade=t=out:st=5.6:d=1.4[s2];'
        '[s1][s2]concat=n=2:v=0:a=1,loudnorm=I=-14.5:TP=-1.5:LRA=11,aresample=48000[a]'
    )
    out = OUT / 'maker-76.mp4'
    cmd = ['ffmpeg', '-v', 'error', '-y', '-i', str(SOFA), '-i', str(OUT / 'hook.png'), '-i', str(OUT / 'twist.png'),
           '-loop', '1', '-t', '3.5', '-i', str(OUT / 'frames.png'), '-loop', '1', '-t', '3.5', '-i', str(OUT / 'end.png'),
           '-filter_complex', fc, '-map', '[v]', '-map', '[a]', '-c:v', 'libx264', '-crf', '19', '-r', str(FPS),
           '-c:a', 'aac', '-b:a', '192k', '-movflags', '+faststart', str(out)]
    subprocess.run(cmd, check=True)
    print(out)


if __name__ == '__main__':
    main()
