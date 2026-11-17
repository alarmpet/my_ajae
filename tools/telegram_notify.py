"""텔레그램 봇으로 폰 알림을 보낸다 (2026-11-18 사용자 「텔레그램으로도 폰 알림 시험해 봐」).

    python tools/telegram_notify.py check            # 봇 이름만(getMe)
    python tools/telegram_notify.py send "메시지"

토큰은 자격 증명 관리자 `my_ajae/telegram-token` 에서만 읽는다(사용자가 put-clipboard 로 넣는다).
받는 채팅은 `.env` 의 TELEGRAM_CHAT_ID. 알림 실패는 게시를 막지 않는다(notify).
"""
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from secret_store import get  # noqa: E402


def env_value(name):
    f = ROOT / ".env"
    if f.exists():
        for line in f.read_text(encoding="utf-8").splitlines():
            if line.startswith(name + "="):
                return line.split("=", 1)[1].strip()
    return os.environ.get(name)


def api(method, **params):
    tok = get("telegram-token")
    if not tok:
        raise SystemExit("토큰 없음(자격 증명 관리자 my_ajae/telegram-token)")
    req = urllib.request.Request(f"https://api.telegram.org/bot{tok}/{method}",
                                 data=urllib.parse.urlencode(params).encode() if params else None)
    try:
        return json.load(urllib.request.urlopen(req, timeout=20))
    except urllib.error.HTTPError as e:
        raise SystemExit(f"Telegram {method}: {e.code} {e.read().decode('utf-8', 'replace').replace(tok, '[토큰]')[:300]}")


def send(text):
    chat = env_value("TELEGRAM_CHAT_ID")
    if not chat:
        raise SystemExit("받는 채팅 없음 — .env 에 TELEGRAM_CHAT_ID")
    return api("sendMessage", chat_id=chat, text=text)["result"]["message_id"]


def notify(text):
    try:
        send(text)
        return True
    except (SystemExit, Exception) as e:  # noqa: BLE001
        print(f"텔레그램 알림 실패: {str(e)[:200]}", flush=True)
        return False


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "check":
        me = api("getMe")["result"]
        print(f"봇: @{me.get('username')}")
    elif cmd == "send":
        print(f"보냄: message_id {send(sys.argv[2])}")
    else:
        print(__doc__)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
