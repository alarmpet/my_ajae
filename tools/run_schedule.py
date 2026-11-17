"""승인된 글을 일정대로 스레드 · 인스타에 올린다 (2026-11-12, 시각별 슬롯 · 대기 모드 2026-11-13).

    python tools/run_schedule.py                                   # 오늘(KST) 슬롯 게시(W46 일정)
    python tools/run_schedule.py --dry                             # 오늘 슬롯과 지문만 확인(게시 안 함)
    python tools/run_schedule.py --date 2026-11-13 --dry
    python tools/run_schedule.py --sched posts/list/SCHEDULE.json --wait   # 앞으로 올 슬롯마다 그 시각까지 기다렸다가 게시
    python tools/run_schedule.py --sched posts/list/SCHEDULE.json --wait --dry

일정 파일: {"platforms": [...], "slots": [{"date": "YYYY-MM-DD", "time": "HH:MM"(선택 — 없으면 파일의 time), "id": ...}]}
각 게시 도구가 승인 지문 · 계정 · 중복(posts/published.jsonl)을 다시 확인한다. 한 곳이 실패해도 다른 곳은 시도한다.
게시물에 first_comment 가 있으면 본글 다음에 우리 계정의 첫 답글로 단다(「예시:」로 밝힌 문구).
--wait 는 이 컴퓨터가 켜져 있고 이 프로세스가 살아 있어야 한다(작업 스케줄러 등록은 사용자 몫 — tools/register_schedule.ps1).
결과는 logs/schedule.log 에 한 줄씩(토큰 없음).

게시 직전 확인(사용자 지시 2026-11-13 「글 올리기 전에 나한테 먼저 출력해서 컨펌받게 해」):
승인(APPROVED.json)과 별도로, 슬롯마다 그날의 확인 기록(같은 폴더 CONFIRMED.jsonl — 날짜 · 지문 · 사용자 말)이 있어야 올린다.
    python tools/run_schedule.py --show L0002                       # 올라갈 그대로 전문 출력(스레드 나눔 · 첫 댓글 · 카드)
    python tools/run_schedule.py --confirm L0002 --date 2026-11-13 --by "사용자 채팅 「올려」"
--wait 는 확인 기록이 없는 슬롯이 LEAD_MIN 분 안으로 다가오면 전문을 출력하고 코드 3 으로 끝난다
(에이전트가 그 출력을 사용자에게 보여 주고 확인을 받아 기록한 뒤 다시 건다). 확인이 없으면 올리지 않는다.
"""
import datetime
import json
import sys
import time
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
LOGF = ROOT / "logs/schedule.log"
KST = datetime.timezone(datetime.timedelta(hours=9))
LEAD_MIN = 120  # 확인 없는 슬롯을 이만큼 앞두고 알린다


def log(msg):
    LOGF.parent.mkdir(exist_ok=True)
    line = f"{datetime.datetime.now(KST):%Y-%m-%d %H:%M:%S} {msg}"
    print(line, flush=True)
    with LOGF.open("a", encoding="utf-8", newline="\n") as fh:
        fh.write(line + "\n")
    # 2026-11-18 — 확인 필요 · 실패 · 보류 · 게시 완료는 알림으로도 보낸다. 알림 실패는 게시를 막지 않는다.
    # 슬랙(폰 알림 · 사용자 「슬랙으로 가자」)만. Buzz 는 쓰지 않는다(사용자 2026-11-18 「이건 사용 안 할 거야」).
    if msg.startswith(("OK ", "FAIL ", "HOLD ", "확인 필요 ")) and "--dry" not in sys.argv:
        icon = {"OK": "✅", "FAIL": "❌", "HOLD": "⏸️", "확인": "🙋"}[msg.split()[0]]
        for mod in ("slack_notify",):
            try:
                __import__(mod).notify(f"{icon} {msg}")
            except Exception as e:  # noqa: BLE001
                print(f"{mod} 건너뜀: {e}", flush=True)


def arg(name, default=None):
    return sys.argv[sys.argv.index(name) + 1] if name in sys.argv else default


def approved_files(pid):
    import threads_api
    threads_api.verify(pid)  # 지문이 승인과 다르면 여기서 멈춘다
    rec = json.loads((threads_api.post_dir(pid) / "APPROVED.json").read_text(encoding="utf-8"))
    return next(x for x in rec["items"] if x["id"] == pid)["files"]


def confirmed(pid, date):
    """그날 그 글에 대한 사용자 확인이 있고, 확인한 지문이 지금 파일과 같은지."""
    import threads_api
    f = threads_api.post_dir(pid) / "CONFIRMED.jsonl"
    if not f.exists():
        return False
    files = approved_files(pid)
    for line in f.read_text(encoding="utf-8").splitlines():
        if line.strip():
            r = json.loads(line)
            if r["id"] == pid and r["date"] == date and r["files"] == files:
                return True
    return False


def show(pid):
    """올라갈 그대로 출력한다 — 스레드는 500자 넘으면 나눠 올리는 조각까지."""
    import threads_api
    post = threads_api.verify(pid)
    parts = threads_api.split_text(post["text"])
    out = [f"===== {pid} ({post.get('app')}) — 승인 지문 일치 ====="]
    for i, t in enumerate(parts):
        out.append(f"--- 본글{'' if i == 0 else f' 이어지는 답글 {i}'} ({len(t)}자) ---")
        out.append(t)
    if post.get("first_comment"):
        out += ["--- 첫 댓글 ---", post["first_comment"]]
    if post.get("topic_tag"):
        out.append(f"--- 스레드 주제 태그: {post['topic_tag']} ---")
    if post.get("hashtags"):
        out.append("--- 인스타 해시태그(캡션 끝): " + " ".join("#" + h.lstrip("#") for h in post["hashtags"]) + " ---")
    out += [f"--- 카드: {post.get('image') or post.get('video') or '(없음)'} ---", "=" * 40]
    return "\n".join(out)


def run_slot(s, pid, dry, date):
    import ig_api
    import threads_api
    if not dry and not confirmed(pid, date):
        log(f"HOLD {pid} {date} 사용자 확인 기록 없음 — 게시 안 함")
        return 1
    tools = {"threads": (threads_api.publish, threads_api.first_comment),
             "instagram": (ig_api.publish, ig_api.first_comment)}
    post = threads_api.verify(pid)  # 지문이 다르면 여기서 멈춘다
    fails = 0
    for plat in post.get("platforms") or s["platforms"]:  # 게시물이 정하면 그곳에만(2026-11-17 — 짧은 글은 스레드만)
        if dry:
            log(f"[dry] {pid} {plat} 지문 일치 — 게시 안 함")
            continue
        pub, com = tools[plat]
        try:
            rec = pub(pid)
            log(f"OK {pid} {plat} {rec.get('permalink')}")
        except SystemExit as e:
            fails += 1
            log(f"FAIL {pid} {plat} {e}")
            continue
        except Exception:
            fails += 1
            log(f"FAIL {pid} {plat} {traceback.format_exc(limit=2)[-300:]}")
            continue
        if post.get("first_comment"):
            try:
                c = com(pid)
                log(f"OK {pid} {plat}-comment {c.get('permalink') or c.get('post_id')}")
            except (SystemExit, Exception) as e:  # 댓글 실패는 본글 실패로 세지 않는다
                log(f"FAIL {pid} {plat}-comment {str(e)[-300:]}")
    return fails


def main():
    dry = "--dry" in sys.argv
    if "--show" in sys.argv:
        print(show(arg("--show")))
        return 0
    if "--confirm" in sys.argv:
        pid, date, by = arg("--confirm"), arg("--date"), arg("--by")
        if not (date and by):
            raise SystemExit("--confirm 에는 --date 와 --by(사용자 말 그대로)가 필요하다")
        import threads_api
        rec = {"id": pid, "date": date, "files": approved_files(pid), "by": by,
               "at": f"{datetime.datetime.now(KST):%Y-%m-%d %H:%M:%S}"}
        with (threads_api.post_dir(pid) / "CONFIRMED.jsonl").open("a", encoding="utf-8", newline="\n") as fh:
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
        log(f"확인 기록 {pid} {date} — {by}")
        return 0
    sched = ROOT / arg("--sched", "posts/2026-W46/SCHEDULE.json")
    s = json.loads(sched.read_text(encoding="utf-8"))
    fails = 0
    if "--wait" in sys.argv:
        now = datetime.datetime.now(KST)
        todo = []
        for x in s["slots"]:
            at = datetime.datetime.strptime(f"{x['date']} {x.get('time') or s['time']}", "%Y-%m-%d %H:%M").replace(tzinfo=KST)
            if at > now:
                todo.append((at, x["id"], x["date"]))
        log(f"대기 시작 {sched.name}: " + ", ".join(f"{a:%m-%d %H:%M} {p}{'' if dry or confirmed(p, d) else '(확인 전)'}" for a, p, d in sorted(todo)) if todo else "앞으로 올 슬롯 없음")
        for at, pid, date in sorted(todo):
            if not dry:
                while (left := (at - datetime.datetime.now(KST)).total_seconds()) > 0:
                    if not confirmed(pid, date) and left <= LEAD_MIN * 60:
                        log(f"확인 필요 {pid} {at:%m-%d %H:%M} — 전문을 출력하고 멈춘다")
                        print(show(pid), flush=True)
                        return 3
                    time.sleep(min(left, 300, max(left - LEAD_MIN * 60, 1)) if not confirmed(pid, date) else min(left, 300))
            fails += run_slot(s, pid, dry, date)
        return 1 if fails else 0
    day = arg("--date", f"{datetime.datetime.now(KST):%Y-%m-%d}")
    todo = [x for x in s["slots"] if x["date"] == day]
    if not todo:
        log(f"{day} 슬롯 없음")
        return 0
    for slot in todo:
        if dry:
            log(f"[dry] {slot['id']} 확인 {'있음' if confirmed(slot['id'], day) else '없음 — 실제로는 올리지 않는다'}")
        fails += run_slot(s, slot["id"], dry, day)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
