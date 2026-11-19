"""@my_ajae 인스타그램 공식 API(Instagram 로그인 방식) — 토큰 확인 · 사진/캐러셀/릴스 게시 (2026-11-12).
D:/auto-cf/tools/ig_api_publish.py(@petblossom)와 같은 방식. 토큰은 자격 증명 관리자 `my_ajae/ig-token` 에서만 읽는다.

    python tools/ig_api.py whoami              # 토큰이 어느 계정 것인지(아이디 · 계정 종류만)
    python tools/ig_api.py publish P0008 --yes [--date YYYY-MM-DD]  # 게시 관문(tools/post_gate.py) 통과 때만 — 그날 사용자 확인 필요

캡션은 게시물 JSON 의 variants.instagram, 없으면 text. 영상은 REELS(피드에도 공유).
AI 표시(AGENTS §2-8): 게시물에 ai_label 이 true 면 is_ai_generated=true 를 함께 보낸다.
승인 지문 대조 · R2 임시 업로드 · 게시 기록(posts/published.jsonl)은 threads_api.py 의 것을 같이 쓴다.
"""
import datetime
import hashlib
import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from secret_store import get  # noqa: E402
from threads_api import LOG, already, date_arg, media_of, r2, record, remove, upload  # noqa: E402

API = "https://graph.instagram.com/v25.0"
SECRET = "ig-token"
EXPECT_USER = "my_ajae"
MAX_CAPTION = 2200


def api(method, path, **params):
    tok = get(SECRET)
    if not tok:
        raise SystemExit(f"토큰 없음(자격 증명 관리자 my_ajae/{SECRET})")
    params["access_token"] = tok
    url = f"{API}/{path}"
    data = urllib.parse.urlencode(params).encode()
    req = urllib.request.Request(url + ("?" + data.decode() if method == "GET" else ""),
                                 data=None if method == "GET" else data, method=method)
    try:
        return json.load(urllib.request.urlopen(req, timeout=120))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", "replace").replace(tok, "[토큰]")
        raise SystemExit(f"Instagram API {method} {path}: {e.code} {body[:400]}")


def whoami():
    me = api("GET", "me", fields="user_id,username,account_type")
    return me["user_id"], me["username"], me.get("account_type")


def wait_ready(cid, tries=120):
    for _ in range(tries):
        st = api("GET", cid, fields="status_code,status")
        if st.get("status_code") == "FINISHED":
            return
        if st.get("status_code") in ("ERROR", "EXPIRED"):
            raise SystemExit(f"컨테이너 {cid} {st}")
        time.sleep(5)
    raise SystemExit(f"컨테이너 {cid} 처리 시간 초과")


def caption_of(post):
    """인스타에 실제로 올라갈 캡션 — 예약의 --show 도 이 함수로 보여 준다(미리 보기와 게시가 같은 글자)."""
    cap = ((post.get("variants") or {}).get("instagram") or post["text"]).strip()
    if post.get("hashtags"):  # 2026-11-16 — 인스타는 해시태그가 검색 · 탐색에 걸리는 길. 캡션 끝에 한 줄로.
        cap += "\n\n" + " ".join("#" + h.lstrip("#") for h in post["hashtags"])
    return cap


def publish(pid, date=None):
    import post_gate
    post = post_gate.gate(pid, date)  # 승인 지문 · 미디어 승인 · 검사 · 사용자 확인 — 외부 호출 전에
    with post_gate.lock(pid, "instagram"):
        return _publish(pid, post)


def _publish(pid, post):
    if already(pid, "instagram"):
        raise SystemExit(f"{pid} 는 이미 인스타에 올렸다(posts/published.jsonl) — 두 번 올리지 않음")
    uid, user, kind_acc = whoami()
    if user != EXPECT_USER:
        raise SystemExit(f"토큰 계정이 {user} — {EXPECT_USER} 가 아니라 게시하지 않음")
    cap = caption_of(post)
    if len(cap) > MAX_CAPTION:
        raise SystemExit(f"캡션 {len(cap)}자 > {MAX_CAPTION}")
    extra = {"is_ai_generated": "true"} if post.get("ai_label") else {}
    kind, files = media_of(post)
    s3 = r2()
    stamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    keys, urls = [], []
    try:
        for f in files:
            k = f"my_ajae/ig/{pid}/{stamp}/{f.name}"
            urls.append(upload(s3, f, k))
            keys.append(k)
        if kind == "VIDEO":
            cid = api("POST", f"{uid}/media", media_type="REELS", video_url=urls[0], caption=cap,
                      share_to_feed="true", **extra)["id"]
        elif kind == "IMAGE":
            cid = api("POST", f"{uid}/media", image_url=urls[0], caption=cap, **extra)["id"]
        else:
            kids = []
            for u in urls:
                kid = api("POST", f"{uid}/media", image_url=u, is_carousel_item="true")["id"]
                wait_ready(kid)
                kids.append(kid)
            cid = api("POST", f"{uid}/media", media_type="CAROUSEL", children=",".join(kids), caption=cap, **extra)["id"]
        wait_ready(cid)
        try:
            mid = api("POST", f"{uid}/media_publish", creation_id=cid)["id"]
        except SystemExit:
            recent = api("GET", f"{uid}/media", fields="id,caption", limit="5").get("data", [])
            hit = [m for m in recent if (m.get("caption") or "").strip() == cap]
            if not hit:
                raise
            mid = hit[0]["id"]
        info = api("GET", mid, fields="id,permalink,caption,timestamp,media_type,media_product_type")
    finally:
        remove(s3, keys)  # 게시 성공 · 실패와 상관없이 공개 버킷에서 지운다
    if (info.get("caption") or "").strip() != cap or not info.get("permalink"):
        raise SystemExit(f"게시 확인 실패: {info.get('permalink')}")
    rec = {"id": pid, "platform": "instagram", "media_type": info.get("media_product_type") or kind, "post_id": info["id"],
           "permalink": info["permalink"], "at": info.get("timestamp"), "ai_label": bool(extra),
           "files_sha256": {str(f.relative_to(ROOT)): hashlib.sha256(f.read_bytes()).hexdigest() for f in files}}
    record(rec)
    return rec


def first_comment(pid, date=None):
    """게시물의 first_comment 를 우리 계정의 첫 댓글로(「예시:」로 밝힌 문구). 권한(instagram_business_manage_comments)이 없으면 실패한다."""
    import post_gate
    post = post_gate.gate(pid, date)
    with post_gate.lock(pid, "instagram-comment"):
        return _first_comment(pid, post)


def _first_comment(pid, post):
    msg = (post.get("first_comment") or "").strip()
    if not msg:
        return None
    recs = [json.loads(l) for l in LOG.read_text(encoding="utf-8").splitlines() if l.strip()]
    main_rec = next((r for r in recs if r.get("id") == pid and r.get("platform") == "instagram"), None)
    if not main_rec:
        raise SystemExit(f"{pid} 인스타 본글 기록이 없다")
    if any(r.get("id") == pid and r.get("platform") == "instagram-comment" for r in recs):
        raise SystemExit(f"{pid} 첫 댓글은 이미 달았다")
    _, user, _ = whoami()  # 2026-11-19 — 댓글도 계정을 확인한다
    if user != EXPECT_USER:
        raise SystemExit(f"토큰 계정이 {user} — {EXPECT_USER} 가 아니라 댓글 달지 않음")
    cid = api("POST", f"{main_rec['post_id']}/comments", message=msg)["id"]
    rec = {"id": pid, "platform": "instagram-comment", "post_id": cid, "on": main_rec["post_id"]}
    record(rec)
    return rec


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "whoami":
        uid, user, acc = whoami()
        print(f"토큰 계정: @{user} (id {uid}, {acc})" + ("" if user == EXPECT_USER else f" — 주의: {EXPECT_USER} 아님"))
    elif cmd == "publish":
        if "--yes" not in sys.argv:
            raise SystemExit("실제 게시는 --yes 가 있어야 한다")
        print(json.dumps(publish(sys.argv[2], date_arg()), ensure_ascii=False))
    elif cmd == "comment":
        if "--yes" not in sys.argv:
            raise SystemExit("실제 댓글은 --yes 가 있어야 한다")
        print(json.dumps(first_comment(sys.argv[2], date_arg()), ensure_ascii=False))
    else:
        print(__doc__)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
