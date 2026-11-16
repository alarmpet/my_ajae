"""@my_ajae 공식 Threads API — 토큰 확인 · 승인 지문 대조 · 글/사진/캐러셀/영상 게시 (2026-11-12).
D:/auto-cf/tools/threads_api.py(@petblossom)와 같은 방식. 토큰은 자격 증명 관리자 `my_ajae/threads-token` 에서만 읽는다 — 출력 · 파일에 쓰지 않는다.

    python tools/threads_api.py whoami                  # 토큰이 어느 계정 것인지(아이디만)
    python tools/threads_api.py verify P0008            # APPROVED.json 지문과 파일 대조(게시 안 함)
    python tools/threads_api.py r2-test                 # 공개 버킷에 시험 파일 올리고 · 열어 보고 · 지운다(게시 안 함)
    python tools/threads_api.py publish P0008 --yes     # 승인 지문 · 계정 · 글자 수가 맞을 때만 게시
    python tools/threads_api.py comment L0001 --yes     # 게시물의 first_comment 를 본글의 첫 답글로(우리 계정)

게시물의 미디어(게시물 JSON 기준): video 가 있으면 영상, carousel 이면 캐러셀, image 면 그 그림 한 장, 아니면 카드 한 장(out/cards/W46/<id>.jpg). 게시물은 posts/*/<id>.json 어디든(승인 기록은 같은 폴더).
미디어는 auto-cf 의 R2 공개 버킷(petblossom-feed) `my_ajae/` 아래에 잠깐 올리고, 게시를 확인하면 지운다(사용자 결정 2026-11-12).
게시 기록은 posts/published.jsonl 에 한 줄씩 남긴다.
"""
import datetime
import hashlib
import json
import mimetypes
import sys
import time
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
LOG = ROOT / "posts/published.jsonl"
R2 = json.loads(Path("D:/auto-cf/config/ig_api.json").read_text(encoding="utf-8"))["r2"]


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


# ---- 승인 지문 ----
def post_dir(pid):
    """게시물 파일이 있는 폴더(posts/<묶음>/<pid>.json). 승인 기록은 같은 폴더의 APPROVED.json."""
    hits = sorted((ROOT / "posts").glob(f"*/{pid}.json"))
    if len(hits) != 1:
        raise SystemExit(f"{pid} 게시물 파일이 {len(hits)}개 — 게시하지 않음")
    return hits[0].parent


def verify(pid):
    """승인 기록의 sha256 과 지금 파일이 모두 같은지. 다르면 게시하지 않는다(AGENTS §3)."""
    d = post_dir(pid)
    rec = json.loads((d / "APPROVED.json").read_text(encoding="utf-8"))
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
    return json.loads((d / f"{pid}.json").read_text(encoding="utf-8"))


def media_of(post):
    if post.get("video"):
        return "VIDEO", [ROOT / post["video"]]
    if post.get("carousel"):
        return "CAROUSEL", [ROOT / x for x in post["carousel"]]
    if post.get("image"):
        return "IMAGE", [ROOT / post["image"]]
    return "IMAGE", [ROOT / f"out/cards/W46/{post['id']}.jpg"]


# ---- R2 공개 주소 ----
def r2():
    import boto3
    return boto3.client("s3", endpoint_url=R2["s3_endpoint"], region_name="auto",
                        aws_access_key_id=get("r2-access-key-id", prefix="auto-cf/"),
                        aws_secret_access_key=get("r2-secret-access-key", prefix="auto-cf/"))


def upload(s3, path, key):
    ctype = mimetypes.guess_type(str(path))[0] or "application/octet-stream"
    s3.put_object(Bucket=R2["bucket"], Key=key, Body=path.read_bytes(), ContentType=ctype)
    url = f"{R2['public_base_url']}/{key}"
    req = urllib.request.Request(url, method="HEAD", headers={"User-Agent": "Mozilla/5.0"})
    if urllib.request.urlopen(req, timeout=30).status != 200:
        raise SystemExit(f"공개 주소 실패 {url}")
    return url


def remove(s3, keys):
    for k in keys:
        s3.delete_object(Bucket=R2["bucket"], Key=k)


# ---- 게시 ----
def wait_ready(cid, tries=120):
    for _ in range(tries):
        st = api("GET", cid, fields="status,error_message")
        if st.get("status") == "FINISHED":
            return
        if st.get("status") in ("ERROR", "EXPIRED"):
            raise SystemExit(f"컨테이너 {cid} {st}")
        time.sleep(5)
    raise SystemExit(f"컨테이너 {cid} 처리 시간 초과")


def publish_container(uid, cid, text):
    # auto-cf 실측: FINISHED 직후 게시하면 4279009(미디어 없음) — 30초 기다리고, 재시도 전에 이미 올라갔는지 본다
    before = {x["id"] for x in api("GET", f"{uid}/threads", fields="id", limit="5").get("data", [])}
    for i in range(4):
        time.sleep(30)
        try:
            return api("POST", f"{uid}/threads_publish", creation_id=cid)["id"]
        except SystemExit as e:
            if "4279009" not in str(e) or i == 3:
                raise
            new = [x for x in api("GET", f"{uid}/threads", fields="id,text", limit="5").get("data", [])
                   if x["id"] not in before and (x.get("text") or "").strip() == text]
            if new:
                return new[0]["id"]


def publish(pid):
    post = verify(pid)
    uid, user = whoami()
    if user != EXPECT_USER:
        raise SystemExit(f"토큰 계정이 {user} — {EXPECT_USER} 가 아니라 게시하지 않음")
    if LOG.exists() and any(json.loads(l).get("id") == pid and json.loads(l).get("platform") == "threads"
                            for l in LOG.read_text(encoding="utf-8").splitlines() if l.strip()):
        raise SystemExit(f"{pid} 는 이미 스레드에 올렸다(posts/published.jsonl) — 두 번 올리지 않음")
    parts = split_text(post["text"].strip())
    text = parts[0]
    kind, files = media_of(post)
    s3 = r2()
    stamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    keys, urls = [], []
    try:
        for f in files:
            k = f"my_ajae/{pid}/{stamp}/{f.name}"
            urls.append(upload(s3, f, k))
            keys.append(k)
        # 주제 태그(2026-11-16): 공식 문서 topic_tag — 글 하나에 하나, 1~50자, 마침표 · & 금지. 팔로워 없는 계정이 주제 피드 · 검색에 걸리는 길.
        # 컨테이너를 만들 때만 붙는다(아직 올라가지 않은 단계) — 거절되면 태그 없이 한 번 더 만든다. 중복 게시는 생기지 않는다.
        tag = (post.get("topic_tag") or "").strip().lstrip("#")
        def make(**kw):
            if tag:
                try:
                    return api("POST", f"{uid}/threads", topic_tag=tag, **kw)["id"]
                except SystemExit as e:
                    print(f"{pid} 주제 태그 거절 — 태그 없이 만든다: {str(e)[:120]}", flush=True)
            return api("POST", f"{uid}/threads", **kw)["id"]
        if kind == "VIDEO":
            cid = make(media_type="VIDEO", video_url=urls[0], text=text)
        elif kind == "IMAGE":
            cid = make(media_type="IMAGE", image_url=urls[0], text=text)
        else:
            kids = [api("POST", f"{uid}/threads", media_type="IMAGE", image_url=u, is_carousel_item="true")["id"] for u in urls]
            for k in kids:
                wait_ready(k)
            cid = make(media_type="CAROUSEL", children=",".join(kids), text=text)
        wait_ready(cid)
        mid = publish_container(uid, cid, text)
        info = api("GET", mid, fields="id,permalink,timestamp,media_type")
    finally:
        remove(s3, keys)  # 게시 성공 · 실패와 상관없이 공개 버킷에서 지운다
    cont, prev = [], info["id"]
    for part in parts[1:]:  # 500자를 넘는 글은 이어지는 답글로(원문 그대로, 자르지 않음)
        c = api("POST", f"{uid}/threads", media_type="TEXT", text=part, reply_to_id=prev)["id"]
        wait_ready(c)
        prev = publish_container(uid, c, part)
        cont.append(prev)
    rec = {"id": pid, "platform": "threads", "media_type": kind, "post_id": info["id"], "permalink": info.get("permalink"),
           "continued": cont, "at": info.get("timestamp"), "files_sha256": {str(f.relative_to(ROOT)): hashlib.sha256(f.read_bytes()).hexdigest() for f in files}}
    with LOG.open("a", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
    return rec


def split_text(text, limit=MAX_TEXT):
    """스레드 한도(500자)에 맞게 줄 단위로 나눈다 — 빈 줄(문단) 경계를 먼저, 안 되면 줄 경계. 글자는 바꾸지 않는다."""
    if len(text) <= limit:
        return [text]
    NL = chr(10)
    paras = text.split(NL + NL)
    parts, cur = [], ""
    for para in paras:
        cand = (cur + NL + NL + para) if cur else para
        if len(cand) <= limit:
            cur = cand
            continue
        if cur:
            parts.append(cur)
        cur = ""
        for line in para.split(NL):
            cand = (cur + NL + line) if cur else line
            if len(cand) <= limit:
                cur = cand
            else:
                if cur:
                    parts.append(cur)
                if len(line) > limit:
                    raise SystemExit(f"한 줄이 {len(line)}자 — 나눌 수 없다")
                cur = line
    if cur:
        parts.append(cur)
    return parts


def first_comment(pid):
    """게시물의 first_comment 를 우리 계정의 첫 답글로 단다(「예시:」로 밝힌 문구 — 부계정 · 가짜 질문 아님)."""
    post = verify(pid)
    msg = (post.get("first_comment") or "").strip()
    if not msg:
        return None
    recs = [json.loads(l) for l in LOG.read_text(encoding="utf-8").splitlines() if l.strip()]
    main = next((r for r in recs if r.get("id") == pid and r.get("platform") == "threads"), None)
    if not main:
        raise SystemExit(f"{pid} 스레드 본글 기록이 없다")
    if any(r.get("id") == pid and r.get("platform") == "threads-comment" for r in recs):
        raise SystemExit(f"{pid} 첫 답글은 이미 달았다")
    uid, user = whoami()
    if user != EXPECT_USER:
        raise SystemExit(f"토큰 계정이 {user}")
    cid = api("POST", f"{uid}/threads", media_type="TEXT", text=msg, reply_to_id=main["post_id"])["id"]
    wait_ready(cid)
    mid = publish_container(uid, cid, msg)
    info = api("GET", mid, fields="id,permalink,timestamp")
    rec = {"id": pid, "platform": "threads-comment", "post_id": info["id"], "permalink": info.get("permalink"), "at": info.get("timestamp")}
    with LOG.open("a", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
    return rec


def r2_test():
    s3 = r2()
    p = ROOT / "out/cards/W46/P0001.jpg"
    k = f"my_ajae/_test/{datetime.datetime.now():%Y%m%d%H%M%S}.jpg"
    try:
        url = upload(s3, p, k)
        print(f"공개 주소 열림: {url}")
    finally:
        remove(s3, [k])
    print("지움")


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "whoami":
        uid, user = whoami()
        print(f"토큰 계정: @{user} (id {uid})" + ("" if user == EXPECT_USER else f" — 주의: {EXPECT_USER} 아님"))
    elif cmd == "verify":
        post = verify(sys.argv[2])
        kind, files = media_of(post)
        print(f"{sys.argv[2]} 지문 일치 · {kind} {len(files)}개 · 글 {len(post['text'].strip())}자")
    elif cmd == "r2-test":
        r2_test()
    elif cmd == "publish":
        if "--yes" not in sys.argv:
            raise SystemExit("실제 게시는 --yes 가 있어야 한다")
        print(json.dumps(publish(sys.argv[2]), ensure_ascii=False))
    elif cmd == "comment":
        if "--yes" not in sys.argv:
            raise SystemExit("실제 답글은 --yes 가 있어야 한다")
        print(json.dumps(first_comment(sys.argv[2]), ensure_ascii=False))
    else:
        print(__doc__)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
