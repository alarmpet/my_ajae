"""승인된 글을 일정대로 스레드 · 인스타에 올린다 (2026-11-12, 시각별 슬롯 · 대기 모드 2026-11-13).

    python tools/run_schedule.py                                   # 오늘(KST) 슬롯 게시(기본 일정 posts/list/SCHEDULE.json)
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
--wait 는 확인 기록이 없는 슬롯이 LEAD_MIN 분 안으로 다가오면 「확인 필요」 알림(슬랙)과 전문을 내고 슬롯 시각까지 확인을
다시 본다. 그때도 없으면 그 슬롯만 보류하고 다음 슬롯을 기다린다(2026-11-19 — 예전에는 코드 3 으로 끝나 이후 슬롯이 모두 빠졌다).
확인이 없으면 올리지 않는다. 일정 파일은 슬롯마다 새로 읽는다.
모든 게시 경로(예약 · threads_api / ig_api 직접 명령 · 댓글)는 tools/post_gate.py 의 같은 관문을 지난다 —
승인 지문 · 미디어 승인 · 지금 시점 게시물 검사 · 그날 확인 기록 · 동시 실행 잠금.
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


from post_gate import approved_files, confirmations, confirmed  # noqa: E402,F401 — 확인 규칙은 게시 관문 한 곳에


def show(pid, platforms=None):
    """올라갈 그대로 출력한다 — 게시 도구와 같은 함수로 만든 글자(스레드 조각 · 인스타 캡션) · 미디어 순서 · 지문."""
    import hashlib

    import ig_api
    import post_gate
    import threads_api
    post = threads_api.verify(pid)
    plats = post.get("platforms") or platforms or ["threads", "instagram"]
    out = [f"===== {pid} ({post.get('app')}) — 승인 지문 일치 · 올라갈 곳: {', '.join(plats)} ====="]
    if "threads" in plats:
        parts = threads_api.split_text(post["text"].strip())
        for i, t in enumerate(parts):
            out.append(f"--- 스레드 본글{'' if i == 0 else f' 이어지는 답글 {i}'} ({len(t)}자) ---")
            out.append(t)
        if post.get("topic_tag"):
            out.append(f"--- 스레드 주제 태그: {post['topic_tag']} (거절되면 태그 없이 올라간다) ---")
    if "instagram" in plats:
        cap = ig_api.caption_of(post)
        out += [f"--- 인스타 캡션({len(cap)}자{', variants.instagram' if (post.get('variants') or {}).get('instagram') else ''}) ---", cap]
    if post.get("first_comment"):
        out += ["--- 첫 댓글(우리 계정) ---", post["first_comment"]]
    if post.get("text_only"):
        out.append("--- 미디어: 없음(글만) ---")
    else:
        kind, files = threads_api.media_of(post)
        out.append(f"--- 미디어: {kind} {len(files)}개(이 순서로) ---")
        for i, f in enumerate(files, 1):
            h = hashlib.sha256(f.read_bytes()).hexdigest()[:12] if f.exists() else "파일 없음"
            out.append(f"  {i}. {f.relative_to(ROOT)}  sha256 {h}")
        miss = post_gate.media_unapproved(pid, post)
        if miss:
            out.append(f"  !! 승인 목록에 없는 미디어: {miss} — 이대로면 게시 관문에서 멈춘다")
    out.append(f"--- AI 표시(인스타): {'붙임' if post.get('ai_label') else '안 붙임'} ---")
    bad = post_gate.check_post(pid)
    out.append("--- 게시물 검사: " + ("FAIL " + " / ".join(bad) if bad else "통과") + " ---")
    out.append("=" * 40)
    return "\n".join(out)


def run_slot(s, pid, dry, date):
    import ig_api
    import post_gate
    import threads_api
    try:  # 지문 · 미디어 승인 · 검사 · 확인 — 하나라도 어긋나면 이 슬롯은 보류(외부 호출 없음)
        post = post_gate.gate(pid, date, need_confirm=not dry)
    except SystemExit as e:
        log(f"HOLD {pid} {date} {e}")
        return 1
    tools = {"threads": (threads_api.publish, threads_api.first_comment),
             "instagram": (ig_api.publish, ig_api.first_comment)}
    fails = 0
    for plat in post.get("platforms") or s["platforms"]:  # 게시물이 정하면 그곳에만(2026-11-17 — 짧은 글은 스레드만)
        if dry:
            log(f"[dry] {pid} {plat} 관문 통과 — 게시 안 함")
            continue
        pub, com = tools[plat]
        try:
            rec = pub(pid, date)
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
                c = com(pid, date)
                log(f"OK {pid} {plat}-comment {c.get('permalink') or c.get('post_id')}")
            except (SystemExit, Exception) as e:  # 댓글 실패는 본글 실패로 세지 않는다
                log(f"FAIL {pid} {plat}-comment {str(e)[-300:]}")
    return fails


def future_slots(sched, after):
    """일정 파일을 새로 읽어 after 보다 뒤의 슬롯을 시각순으로(대기 중에 일정을 고쳐도 다음 슬롯부터 반영)."""
    s = json.loads(sched.read_text(encoding="utf-8"))
    todo = []
    for x in s["slots"]:
        at = datetime.datetime.strptime(f"{x['date']} {x.get('time') or s['time']}", "%Y-%m-%d %H:%M").replace(tzinfo=KST)
        if at > after:
            todo.append((at, x["id"], x["date"]))
    return s, sorted(todo)


def confirm_note(pid, date):
    c = confirmations(pid, date)
    return f"(확인 {c[-1]['at'][5:16]})" if c else "(확인 전)"


def wait_loop(sched, dry):
    """앞으로 올 슬롯마다 그 시각까지 기다렸다가 게시한다.
    확인 기록이 없는 슬롯은 LEAD_MIN 분 전에 「확인 필요」 알림(슬랙)과 전문을 내고, 슬롯 시각까지 확인을 다시 본다.
    그때도 없으면 그 슬롯만 보류하고 다음 슬롯으로 간다 — 예전처럼 멈추지 않는다(2026-11-19: 작업 스케줄러로 돌면
    멈춘 뒤 다음 로그인까지 이후 슬롯이 모두 빠졌다)."""
    s, todo = future_slots(sched, datetime.datetime.now(KST))
    log(f"대기 시작 {sched.name}: " + ", ".join(f"{a:%m-%d %H:%M} {p}{'' if dry else confirm_note(p, d)}" for a, p, d in todo) if todo else "앞으로 올 슬롯 없음")
    fails, last = 0, datetime.datetime.now(KST)
    while todo:
        at, pid, date = todo[0]
        if not dry:
            asked = False
            while (left := (at - datetime.datetime.now(KST)).total_seconds()) > 0:
                if not asked and left <= LEAD_MIN * 60 and not confirmed(pid, date):
                    log(f"확인 필요 {pid} {at:%m-%d %H:%M} — 채팅에서 전문을 보고 「올려」 하면 그 시각에 올린다(없으면 이 슬롯만 보류)")
                    print(show(pid, s.get("platforms")), flush=True)
                    asked = True
                time.sleep(max(1, min(left, 300, left - LEAD_MIN * 60 if left > LEAD_MIN * 60 else 300)))
        # 올리기 직전에 일정을 다시 읽는다 — 기다리는 동안 이 슬롯을 일정에서 빼면 올리지 않는다(사용자 보류)
        s, still = future_slots(sched, at - datetime.timedelta(seconds=1))
        if (at, pid, date) not in still:
            log(f"HOLD {pid} {at:%m-%d %H:%M} 일정에서 빠짐 — 올리지 않음")
            s, todo = future_slots(sched, at)
            continue
        fails += run_slot(s, pid, dry, date)
        last = at
        s, todo = future_slots(sched, last)
    return 1 if fails else 0


def main():
    dry = "--dry" in sys.argv
    if "--show" in sys.argv:
        print(show(arg("--show"), json.loads((ROOT / arg("--sched", "posts/list/SCHEDULE.json")).read_text(encoding="utf-8")).get("platforms")))
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
    sched = ROOT / arg("--sched", "posts/list/SCHEDULE.json")
    s = json.loads(sched.read_text(encoding="utf-8"))
    fails = 0
    if "--wait" in sys.argv:
        return wait_loop(sched, dry)
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
