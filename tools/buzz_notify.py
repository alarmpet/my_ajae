"""Buzz(로컬 중계 서버) 채널로 짧은 알림을 보낸다 (2026-11-18 사용자 「시험해 봐」).

    python tools/buzz_notify.py whoami                  # 키의 신원 · 채널 목록
    python tools/buzz_notify.py send "메시지"            # BUZZ_CHANNEL(.env) 또는 --channel <UUID> 로
    python tools/buzz_notify.py send "메시지" --channel <UUID>

키는 자격 증명 관리자 `my_ajae/buzz-key` 에서만 읽어 환경 변수로 buzz.exe 에 넘긴다(출력 · 파일에 남기지 않는다).
중계 서버는 도커(D:/tools/buzz/src/deploy/compose)로 돈다 — 꺼져 있으면 알림은 실패만 기록하고 게시는 막지 않는다.
"""
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from secret_store import get  # noqa: E402

BUZZ = r"D:\tools\buzz\app\buzz.exe"
RELAY = os.environ.get("BUZZ_RELAY_URL", "http://192.168.45.80:3300")


def env_value(name):
    f = ROOT / ".env"
    if f.exists():
        for line in f.read_text(encoding="utf-8").splitlines():
            if line.startswith(name + "="):
                return line.split("=", 1)[1].strip()
    return os.environ.get(name)


def run(*args, timeout=30):
    key = get("buzz-key")
    if not key:
        raise SystemExit("키 없음(자격 증명 관리자 my_ajae/buzz-key)")
    env = dict(os.environ, BUZZ_RELAY_URL=RELAY, BUZZ_PRIVATE_KEY=key)
    r = subprocess.run([BUZZ, *args], env=env, capture_output=True, text=True, encoding="utf-8", timeout=timeout)
    out, err = r.stdout.replace(key, "[키]"), r.stderr.replace(key, "[키]")
    if r.returncode:
        raise SystemExit(f"buzz {args[0]} 실패({r.returncode}): {err.strip()[:300]}")
    return out


def send(text, channel=None):
    channel = channel or env_value("BUZZ_CHANNEL")
    if not channel:
        raise SystemExit("채널 없음 — .env 에 BUZZ_CHANNEL=<UUID> 를 넣거나 --channel 로 준다")
    return json.loads(run("messages", "send", "--channel", channel, "--content", text))


def notify(text):
    """게시 흐름에서 부르는 판 — 실패해도 예외를 내지 않는다(알림 때문에 게시가 멈추면 안 된다)."""
    try:
        send(text)
        return True
    except (SystemExit, Exception) as e:  # noqa: BLE001
        print(f"Buzz 알림 실패: {str(e)[:200]}", flush=True)
        return False


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    ch = sys.argv[sys.argv.index("--channel") + 1] if "--channel" in sys.argv else None
    if cmd == "whoami":
        print(run("--format", "compact", "channels", "list"))
    elif cmd == "send":
        print(json.dumps(send(sys.argv[2], ch), ensure_ascii=False))
    else:
        print(__doc__)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
