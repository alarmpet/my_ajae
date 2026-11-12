"""「아재도 한다」 릴스 — 76만 회 강아지 쇼츠를 만든 과정 (1080x1920 · 24fps · 약 21초).

재료(우리 채널의 우리 영상 — 남의 화면 없음):
  D:/auto-cf/jobs/20261022-ai-sofa/video/sofa_full_v3.mp4  (유튜브 joTy32Ny8Jk 로 올린 파일)
  D:/auto-cf/jobs/20261022-ai-sofa/sofa_pop_start4.jpg · sofa_pop_end1.jpg  (시작 · 끝 장면)
문구는 장부 E019 에서만 — 여기서 숫자를 짓지 않는다.
사실적 AI 생성 영상이 들어간다 → 화면에 「AI 생성 영상」 표시 + 플랫폼 AI 표시를 켠다(AGENTS §2-8).

  python tools/promo_maker_76.py
"""
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
JOB = Path('D:/auto-cf/jobs/20261022-ai-sofa')
SOFA = JOB / 'video/sofa_full_v3.mp4'
OUT = ROOT / 'out/video/maker-76'
FB = 'C:/Windows/Fonts/malgunbd.ttf'
W, H, FPS = 1080, 1920, 24
INK, ORANGE, YELLOW = (24, 24, 28), (255, 140, 50), (255, 214, 64)


def f(size):
    return ImageFont.truetype(FB, size)


def label(d, text):
    fs = f(30)
    tw = d.textlength(text, font=fs)
    d.rounded_rectangle((W - tw - 70, 60, W - 30, 115), 14, fill=(0, 0, 0, 160))
    d.text((W - tw - 50, 66), text, font=fs, fill=(255, 255, 255, 235))


def top_card(path, lines, ai_label):
    im = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rectangle((0, 140, W, 140 + 150 * len(lines) + 40), fill=INK + (215,))
    y = 170
    for text, size, col in lines:
        w = d.textlength(text, font=f(size))
        d.text(((W - w) / 2, y), text, font=f(size), fill=col)
        y += int(size * 1.35)
    label(d, ai_label)
    im.save(path)


def frames_slide(path):
    bg = Image.new('RGB', (W, H), INK)
    d = ImageDraw.Draw(bg)
    a = Image.open(JOB / 'sofa_pop_start4.jpg').convert('RGB')
    b = Image.open(JOB / 'sofa_pop_end1.jpg').convert('RGB')
    tw = 470
    a = a.resize((tw, int(a.height * tw / a.width)))
    b = b.resize((tw, int(b.height * tw / b.width)))
    top = 520
    bg.paste(a, (45, top))
    bg.paste(b, (W - 45 - tw, top))
    for x, t in ((45, '시작 장면 1장'), (W - 45 - tw, '끝 장면 1장')):
        w = d.textlength(t, font=f(44))
        d.text((x + (tw - w) / 2, top + a.height + 30), t, font=f(44), fill=YELLOW)
    for i, t in enumerate(['이 두 장 사이 10초를', 'Google Flow 가 채웠다']):
        w = d.textlength(t, font=f(72))
        d.text(((W - w) / 2, 220 + i * 100), t, font=f(72), fill=(255, 255, 255))
    t = '그림 · 영상 모두 AI 생성'
    w = d.textlength(t, font=f(40))
    d.text(((W - w) / 2, top + a.height + 130), t, font=f(40), fill=(200, 200, 200))
    bg.save(path)


def end_slide(path):
    bg = Image.new('RGB', (W, H), INK)
    d = ImageDraw.Draw(bg)
    rows = [('같은 채널 쇼츠 49개 중', 64, (255, 255, 255)), ('76만 회는 이 하나.', 84, YELLOW),
            ('', 40, None), ('제목은 사람이 정하고', 56, (220, 220, 220)), ('AI 표시는 켜고 올렸다.', 56, (220, 220, 220)),
            ('', 60, None), ('아재도 한다', 96, ORANGE), ('@my_ajae', 44, (180, 180, 180))]
    y = 520
    for t, s, c in rows:
        if t:
            w = d.textlength(t, font=f(s))
            d.text(((W - w) / 2, y), t, font=f(s), fill=c)
        y += int(s * 1.45)
    bg.save(path)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    top_card(OUT / 'hook.png', [('코딩 모르는 40대가 AI랑 만든', 56, (255, 255, 255)),
                                 ('영상 도구로 만든 쇼츠', 56, (255, 255, 255)),
                                 ('유튜브 조회수 76만 회', 84, YELLOW)], 'AI 생성 영상')
    top_card(OUT / 'twist.png', [('평범한 강아지 영상으로 시작해', 54, (255, 255, 255)),
                                  ('집주인이 오자 자는 척', 54, YELLOW)], 'AI 생성 영상')
    frames_slide(OUT / 'frames.png')
    end_slide(OUT / 'end.png')
    # A 0~5.5 훅 · B 5.5~16 반전 · C 3.5초 시작/끝 장면 · D 3초 끝
    fc = (
        f'[0:v]trim=0:5.5,setpts=PTS-STARTPTS,fps={FPS},scale={W}:{H},setsar=1[a0];[a0][1:v]overlay[A];'
        f'[0:v]trim=5.5:16,setpts=PTS-STARTPTS,fps={FPS},scale={W}:{H},setsar=1[b0];[b0][2:v]overlay[B];'
        f'[3:v]fps={FPS},scale={W}:{H},setsar=1[C];[4:v]fps={FPS},scale={W}:{H},setsar=1[D];'
        '[A][B][C][D]concat=n=4:v=1:a=0,format=yuv420p[v];'
        # 소리: 원본 16초 + 뒤 6.5초는 원본 앞부분을 작게(무음 구간을 만들지 않는다)
        '[0:a]atrim=0:16,asetpts=PTS-STARTPTS[s1];[0:a]atrim=0:6.5,asetpts=PTS-STARTPTS,volume=0.25,afade=t=out:st=5.3:d=1.2[s2];'
        '[s1][s2]concat=n=2:v=0:a=1,loudnorm=I=-14.5:TP=-1.5:LRA=11,aresample=48000[a]'
    )
    out = OUT / 'maker-76.mp4'
    cmd = ['ffmpeg', '-v', 'error', '-y', '-i', str(SOFA), '-i', str(OUT / 'hook.png'), '-i', str(OUT / 'twist.png'),
           '-loop', '1', '-t', '3.5', '-i', str(OUT / 'frames.png'), '-loop', '1', '-t', '3', '-i', str(OUT / 'end.png'),
           '-filter_complex', fc, '-map', '[v]', '-map', '[a]', '-c:v', 'libx264', '-crf', '19', '-r', str(FPS),
           '-c:a', 'aac', '-b:a', '192k', '-movflags', '+faststart', str(out)]
    subprocess.run(cmd, check=True)
    print(out)


if __name__ == '__main__':
    main()
