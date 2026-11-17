"""슬랙 채널로 게시 알림을 보낸다 — Incoming Webhook (2026-11-18 사용자 「슬랙으로 가자」).

    python tools/slack_notify.py check            # 웹훅이 저장돼 있는지만
    python tools/slack_notify.py send "메시지"

웹훅 주소는 비밀값이다(주소만 알면 누구나 그 채널에 글을 쓴다) — 자격 증명 관리자 `my_ajae/slack-webhook` 에만 둔다.
  python tools/secret_store.py put-clipboard slack-webhook
무료 플랜: 평생 무료 · 기록 90일 · 앱 10개 · 메시지는 채널당 초당 1개(https://slack.com/pricing ·
https://docs.slack.dev/apis/web-api/rate-limits, 2026-11-18 확인). 알림 실패는 게시를 막지 않는다(notify).
"""
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from secret_store import get  # noqa: E402


def send(text):
    url = get("slack-webhook")
    if not url:
        raise SystemExit("웹훅 없음(자격 증명 관리자 my_ajae/slack-webhook)")
    if not url.startswith("https://hooks.slack.com/"):
        raise SystemExit("저장된 값이 슬랙 웹훅 주소 모양이 아니다(https://hooks.slack.com/…)")
    req = urllib.request.Request(url, data=json.dumps({"text": text}).encode(),
                                 headers={"Content-Type": "application/json"})
    try:
        body = urllib.request.urlopen(req, timeout=20).read().decode()
    except urllib.error.HTTPError as e:
        raise SystemExit(f"Slack 웹훅 {e.code} {e.read().decode('utf-8', 'replace')[:200]}")
    if body.strip() != "ok":
        raise SystemExit(f"Slack 응답: {body[:200]}")
    return True


def notify(text):
    try:
        return send(text)
    except (SystemExit, Exception) as e:  # noqa: BLE001
        print(f"슬랙 알림 실패: {str(e)[:200]}", flush=True)
        return False


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "check":
        url = get("slack-webhook")
        print("웹훅: " + ("있음" if url and url.startswith("https://hooks.slack.com/") else "없음"))
    elif cmd == "send":
        send(sys.argv[2])
        print("보냄")
    else:
        print(__doc__)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
