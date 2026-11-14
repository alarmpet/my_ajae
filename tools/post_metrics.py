"""올린 글의 반응을 공식 API 로 읽어 한 표로 모은다 — 읽기만 한다(게시 · 댓글 · 좋아요 없음). 2026-11-14.

    python -X utf8 tools/post_metrics.py            # 표 출력 + ledger/metrics.jsonl 에 오늘 줄 추가
    python -X utf8 tools/post_metrics.py --dry      # 표만 출력

스레드: /{media}/insights (views · likes · replies · reposts · quotes · shares) — 권한 threads_manage_insights.
인스타: /{media}/insights (reach · likes · comments · saved · shares) — 권한 instagram_business_manage_insights.
권한이 없으면 그 칸은 「권한 없음」으로 남긴다 — 숫자를 지어내지 않는다.
metrics.jsonl 에는 우리 글의 숫자만 들어간다(남의 글 · 개인 정보 없음).
"""
import datetime
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import ig_api  # noqa: E402
import threads_api  # noqa: E402

OUT = ROOT / "ledger/metrics.jsonl"
T_METRICS = "views,likes,replies,reposts,quotes,shares"
I_METRICS = "reach,likes,comments,saved,shares"


def insights(mod, post_id, metrics):
    try:
        r = mod.api("GET", f"{post_id}/insights", metric=metrics)
    except SystemExit as e:  # api() 가 오류를 SystemExit 로 올린다
        return {"error": str(e)[:160]}
    out = {}
    for d in r.get("data", []):
        v = d.get("values") or [{}]
        out[d["name"]] = v[0].get("value", d.get("total_value", {}).get("value"))
    return out


def post_meta(pid):
    for f in (ROOT / "posts").glob(f"*/{pid}.json"):
        p = json.loads(f.read_text(encoding="utf-8"))
        return {"app": p.get("app"), "ledger": p.get("ledger"), "pillar": p.get("pillar"), "hook": p.get("hook"),
                "first": str(p.get("text", "")).split("\n")[0][:40]}
    return {}


def main():
    dry = "--dry" in sys.argv
    today = datetime.date.today().isoformat()
    rows = []
    for line in threads_api.LOG.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        d = json.loads(line)
        if d["platform"] == "threads":
            m = insights(threads_api, d["post_id"], T_METRICS)
        elif d["platform"] == "instagram":
            m = insights(ig_api, d["post_id"], I_METRICS)
        else:
            continue
        rows.append({"date": today, "id": d["id"], "platform": d["platform"], "posted_at": d.get("at"), **post_meta(d["id"]), "metrics": m})
    for r in rows:
        m = r["metrics"]
        txt = "권한 없음/오류: " + m["error"] if "error" in m else " ".join(f"{k}={v}" for k, v in m.items())
        print(f"{r['id']:6} {r['platform']:9} {txt}  | {r.get('first', '')}")
    if not dry:
        with OUT.open("a", encoding="utf-8") as f:
            for r in rows:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
        print(f"→ {OUT.relative_to(ROOT)} 에 {len(rows)}줄")


if __name__ == "__main__":
    main()
