"""@my_ajae 공식 Threads API — 토큰 확인 · 승인 지문 대조 · 글 게시 (2026-11-12).
D:/auto-cf/tools/threads_api.py(@petblossom)와 같은 방식. 토큰은 자격 증명 관리자 `my_ajae/threads-token` 에서만 읽는다 — 출력 · 파일에 쓰지 않는다.

    python tools/threads_api.py whoami                 # 토큰이 어느 계정 것인지(아이디만)
    python tools/threads_api.py verify P0008           # APPROVED.json 지문과 파일 대조(게시 안 함)
    python tools/threads_api.py publish-text P0001 --yes   # 글만 게시(사진 없이) — 지문이 맞을 때만

사진 · 영상 게시는 공개 주소가 필요하다(auto-cf 는 R2 공개 버킷을 쓴다) — 아직 연결하지 않았다.
"""
import hashlib
import json
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from secret_store import get  # noqa: E402

API = "https://graph.threads.net/v1.0"
SECRET = "threads-token"
EXPECT_USER = "my_ajae"
MAX_TEXT = 500
APPROVED = ROOT / "posts/2026-W46/APPROVED.json"


def api(method, path, **params):
    tok = get(SECRET)
    if not tok:
        raise SystemExit(f"토큰 없음(자격 증명 관리자 my_ajae/{SECRET})")
    params["access_token"] = tok
    url = f"{API}/{path}"
    data = None
    if method == "GET":
        url += "?" + urllib.parse.urlencode(params)
    else:
        data = urllib.parse.urlencode(params).encode()
    try:
        return json.load(urllib.request.urlopen(urllib.request.Request(url, data=data, method=method), timeout=60))
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors="replace").replace(tok, "[토큰]")
        raise SystemExit(f"Threads API {method} {path}: {e.code} {body[:300]}")


def whoami():
    me = api("GET", "me", fields="id,username")
    return me["id"], me["username"]


def verify(pid):
    """승인 기록의 sha256 과 지금 파일이 모두 같은지. 다르면 게시하지 않는다(AGENTS §3)."""
    rec = json.loads(APPROVED.read_text(encoding="utf-8"))
    item = next((x for x in rec["items"] if x["id"] == pid), None)
    if not item:
        raise SystemExit(f"{pid} 는 승인 기록에 없다 — 게시하지 않음")
    bad = []
    for path, want in item["files"].items():
        p = ROOT / path
        got = hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else None
        if got != want:
            bad.append(path)
    if bad:
        raise SystemExit(f"{pid} 지문 불일치(승인 뒤 바뀜): {bad} — 게시하지 않음")
    return json.loads((ROOT / f"posts/2026-W46/{pid}.json").read_text(encoding="utf-8"))


def publish_text(pid):
    post = verify(pid)
    uid, user = whoami()
    if user != EXPECT_USER:
        raise SystemExit(f"토큰 계정이 {user} — {EXPECT_USER} 가 아니라 게시하지 않음")
    text = post["text"].strip()
    if len(text) > MAX_TEXT:
        raise SystemExit(f"글 {len(text)}자 > {MAX_TEXT}")
    cid = api("POST", f"{uid}/threads", media_type="TEXT", text=text)["id"]
    mid = api("POST", f"{uid}/threads_publish", creation_id=cid)["id"]
    return api("GET", mid, fields="id,permalink,timestamp")


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "whoami":
        uid, user = whoami()
        print(f"토큰 계정: @{user} (id {uid})" + ("" if user == EXPECT_USER else f" — 주의: {EXPECT_USER} 아님"))
    elif cmd == "verify":
        verify(sys.argv[2])
        print(f"{sys.argv[2]} 지문 일치")
    elif cmd == "publish-text":
        if "--yes" not in sys.argv:
            raise SystemExit("실제 게시는 --yes 가 있어야 한다")
        print(publish_text(sys.argv[2]))
    else:
        print(__doc__)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
