"""게시 관문 — 모든 게시 경로(예약 · 직접 명령 · 댓글)가 외부로 쓰기 전에 지나는 한 곳 (2026-11-19).

계획 docs/plans/2026-11-19-integrated-ops-marketing-plan.md §4.1 P0 중 저장소에서 확인한 것만 반영했다:
  ① 승인 지문(APPROVED.json)이 지금 파일과 같다
  ② 실제로 올라갈 미디어 파일이 하나도 빠짐없이 승인 목록에 있다(빠진 파일 · 기본 카드 경로로 새는 것 차단)
  ③ 지금 시점의 게시물 검사(check_post.mjs)가 FAIL 이 아니다(비공개로 돌린 사건 · 바뀐 용하네 정책 · 금지 표현)
  ④ 그 날짜의 사용자 확인 기록(CONFIRMED.jsonl — 날짜 · 지문 · 사용자 말)이 있다 — 직접 명령도 예외가 아니다
  ⑤ 같은 글 · 같은 플랫폼을 다른 실행이 동시에 올리고 있지 않다(잠금 파일)
하나라도 어긋나면 SystemExit — 외부 API 를 부르기 전에 멈춘다.

확인 기록의 유효 시간(예: 슬롯 전 120분 안)은 사용자 결정 전이라 걸지 않는다. 확인한 시각은 기록에 남고 대기 시작 로그에 보인다.
"""
import contextlib
import datetime
import json
import os
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
KST = datetime.timezone(datetime.timedelta(hours=9))
LOCKS = ROOT / "logs" / "locks"


def today():
    return f"{datetime.datetime.now(KST):%Y-%m-%d}"


def approved_item(pid):
    import threads_api
    rec = json.loads((threads_api.post_dir(pid) / "APPROVED.json").read_text(encoding="utf-8"))
    return next(x for x in rec["items"] if x["id"] == pid)


def approved_files(pid):
    import threads_api
    threads_api.verify(pid)  # 지문이 승인과 다르면 여기서 멈춘다
    return approved_item(pid)["files"]


def confirmations(pid, date):
    """그 날짜 · 그 글 · 지금 지문과 같은 확인 기록들(오래된 것부터)."""
    import threads_api
    f = threads_api.post_dir(pid) / "CONFIRMED.jsonl"
    if not f.exists():
        return []
    files = approved_files(pid)
    out = []
    for line in f.read_text(encoding="utf-8").splitlines():
        if line.strip():
            r = json.loads(line)
            if r["id"] == pid and r["date"] == date and r["files"] == files:
                out.append(r)
    return out


def confirmed(pid, date):
    return bool(confirmations(pid, date))


def media_unapproved(pid, post):
    """올라갈 미디어 중 승인 목록에 없는 파일(상대 경로)."""
    import threads_api
    if post.get("text_only"):
        return []
    _, files = threads_api.media_of(post)
    listed = set(approved_item(pid)["files"])
    return [str(f.relative_to(ROOT)).replace("\\", "/") for f in files
            if str(f.relative_to(ROOT)).replace("\\", "/") not in listed]


def check_post(pid):
    """지금 시점의 게시물 검사. FAIL 이면 그 줄들을, 통과(PASS · HOLD)면 빈 목록. 검사를 못 돌리면 FAIL 로 친다."""
    import threads_api
    f = threads_api.post_dir(pid) / f"{pid}.json"
    try:
        r = subprocess.run(["node", str(ROOT / "tools/check_post.mjs"), str(f)], capture_output=True,
                           text=True, encoding="utf-8", errors="replace", timeout=120, cwd=ROOT)
    except (OSError, subprocess.TimeoutExpired) as e:
        return [f"게시물 검사를 돌리지 못했다: {e}"]
    if r.returncode == 0:
        return []
    lines = [l.strip() for l in (r.stdout + r.stderr).splitlines() if l.strip().startswith("-")]
    return lines or [f"게시물 검사 종료 코드 {r.returncode}"]


def gate(pid, date=None, need_confirm=True):
    """①~④ 를 확인하고 게시물(JSON)을 돌려준다. 외부로 쓰기 전에 부른다."""
    import threads_api
    post = threads_api.verify(pid)  # ①
    miss = media_unapproved(pid, post)  # ②
    if miss:
        raise SystemExit(f"{pid} 올라갈 미디어가 승인 목록에 없다: {miss} — 게시하지 않음")
    bad = check_post(pid)  # ③
    if bad:
        raise SystemExit(f"{pid} 게시물 검사 FAIL: {' / '.join(bad)[:300]} — 게시하지 않음")
    date = date or today()
    if need_confirm and not confirmed(pid, date):  # ④
        raise SystemExit(f"{pid} {date} 사용자 확인 기록 없음(run_schedule.py --show 로 전문을 보이고 --confirm) — 게시하지 않음")
    return post


@contextlib.contextmanager
def lock(pid, platform):
    """⑤ 같은 글 · 같은 플랫폼 동시 게시 막기. 실행이 죽어 잠금이 남으면 파일을 확인하고 지운다."""
    LOCKS.mkdir(parents=True, exist_ok=True)
    p = LOCKS / f"{pid}-{platform}.lock"
    try:
        fd = os.open(p, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError:
        raise SystemExit(f"{pid} {platform} 다른 실행이 게시 중(잠금 {p.relative_to(ROOT)}) — 겹쳐 올리지 않음. "
                         f"남은 잠금이면 게시 기록을 확인한 뒤 지운다")
    try:
        os.write(fd, f"{os.getpid()} {datetime.datetime.now(KST):%Y-%m-%d %H:%M:%S}".encode())
        os.close(fd)
        yield
    finally:
        with contextlib.suppress(OSError):
            p.unlink()
