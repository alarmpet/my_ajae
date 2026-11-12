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


def log(msg):
    LOGF.parent.mkdir(exist_ok=True)
    line = f"{datetime.datetime.now(KST):%Y-%m-%d %H:%M:%S} {msg}"
    print(line, flush=True)
    with LOGF.open("a", encoding="utf-8", newline="\n") as fh:
        fh.write(line + "\n")


def arg(name, default=None):
    return sys.argv[sys.argv.index(name) + 1] if name in sys.argv else default


def run_slot(s, pid, dry):
    import ig_api
    import threads_api
    tools = {"threads": (threads_api.publish, threads_api.first_comment),
             "instagram": (ig_api.publish, ig_api.first_comment)}
    post = threads_api.verify(pid)  # 지문이 다르면 여기서 멈춘다
    fails = 0
    for plat in s["platforms"]:
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
    sched = ROOT / arg("--sched", "posts/2026-W46/SCHEDULE.json")
    s = json.loads(sched.read_text(encoding="utf-8"))
    fails = 0
    if "--wait" in sys.argv:
        now = datetime.datetime.now(KST)
        todo = []
        for x in s["slots"]:
            at = datetime.datetime.strptime(f"{x['date']} {x.get('time') or s['time']}", "%Y-%m-%d %H:%M").replace(tzinfo=KST)
            if at > now:
                todo.append((at, x["id"]))
        log(f"대기 시작 {sched.name}: " + ", ".join(f"{a:%m-%d %H:%M} {p}" for a, p in sorted(todo)) if todo else "앞으로 올 슬롯 없음")
        for at, pid in sorted(todo):
            if not dry:
                while (left := (at - datetime.datetime.now(KST)).total_seconds()) > 0:
                    time.sleep(min(left, 300))
            fails += run_slot(s, pid, dry)
        return 1 if fails else 0
    day = arg("--date", f"{datetime.datetime.now(KST):%Y-%m-%d}")
    todo = [x for x in s["slots"] if x["date"] == day]
    if not todo:
        log(f"{day} 슬롯 없음")
        return 0
    for slot in todo:
        fails += run_slot(s, slot["id"], dry)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
