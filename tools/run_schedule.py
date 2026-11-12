"""오늘 날짜의 승인된 글을 스레드 · 인스타에 올린다 — 윈도우 작업 스케줄러가 매일 부른다 (2026-11-12).

    python tools/run_schedule.py            # 오늘(KST) 슬롯 게시
    python tools/run_schedule.py --dry      # 오늘 슬롯과 지문만 확인(게시 안 함)
    python tools/run_schedule.py --date 2026-11-13 --dry

일정은 posts/2026-W46/SCHEDULE.json. 각 게시 도구가 승인 지문 · 계정 · 중복(posts/published.jsonl)을 다시 확인한다.
한 곳이 실패해도 다른 곳은 시도한다. 결과는 logs/schedule.log 에 한 줄씩(토큰 없음).
"""
import datetime
import json
import sys
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
SCHED = ROOT / "posts/2026-W46/SCHEDULE.json"
LOGF = ROOT / "logs/schedule.log"
KST = datetime.timezone(datetime.timedelta(hours=9))


def log(msg):
    LOGF.parent.mkdir(exist_ok=True)
    line = f"{datetime.datetime.now(KST):%Y-%m-%d %H:%M:%S} {msg}"
    print(line)
    with LOGF.open("a", encoding="utf-8", newline="\n") as fh:
        fh.write(line + "\n")


def main():
    dry = "--dry" in sys.argv
    day = sys.argv[sys.argv.index("--date") + 1] if "--date" in sys.argv else f"{datetime.datetime.now(KST):%Y-%m-%d}"
    s = json.loads(SCHED.read_text(encoding="utf-8"))
    todo = [x for x in s["slots"] if x["date"] == day]
    if not todo:
        log(f"{day} 슬롯 없음")
        return 0
    import ig_api
    import threads_api
    tools = {"threads": threads_api.publish, "instagram": ig_api.publish}
    fails = 0
    for slot in todo:
        pid = slot["id"]
        threads_api.verify(pid)  # 지문이 다르면 여기서 멈춘다
        for plat in s["platforms"]:
            if dry:
                log(f"[dry] {day} {pid} {plat} 지문 일치 — 게시 안 함")
                continue
            try:
                rec = tools[plat](pid)
                log(f"OK {pid} {plat} {rec.get('permalink')}")
            except SystemExit as e:
                fails += 1
                log(f"FAIL {pid} {plat} {e}")
            except Exception:
                fails += 1
                log(f"FAIL {pid} {plat} {traceback.format_exc(limit=2)[-300:]}")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
