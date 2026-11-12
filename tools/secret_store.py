"""비밀값(토큰)을 Windows 자격 증명 관리자에 넣고 꺼낸다 — 저장소 파일 · 로그 · 대화에 값이 남지 않게.
D:/auto-cf/tools/secret_store.py 와 같은 방식(이름 앞머리만 my_ajae/).

    python tools/secret_store.py put-stdin <이름> [--min-len 40]   # 표준 입력의 값을 저장(출력하지 않는다)
    python tools/secret_store.py put-clipboard <이름>              # 클립보드 값을 저장하고 클립보드를 비운다
    python tools/secret_store.py check <이름>                     # 있는지 · 길이만

코드에서: from secret_store import get; tok = get("threads-token")
값은 절대 print 하지 않는다.
"""
import ctypes
import ctypes.wintypes as wt
import sys

CRED_TYPE_GENERIC = 1
CRED_PERSIST_LOCAL_MACHINE = 2
PREFIX = "my_ajae/"


class CREDENTIAL(ctypes.Structure):
    _fields_ = [("Flags", wt.DWORD), ("Type", wt.DWORD), ("TargetName", wt.LPWSTR), ("Comment", wt.LPWSTR),
                ("LastWritten", wt.FILETIME), ("CredentialBlobSize", wt.DWORD), ("CredentialBlob", ctypes.POINTER(ctypes.c_char)),
                ("Persist", wt.DWORD), ("AttributeCount", wt.DWORD), ("Attributes", ctypes.c_void_p),
                ("TargetAlias", wt.LPWSTR), ("UserName", wt.LPWSTR)]


adv = ctypes.WinDLL("advapi32", use_last_error=True)
adv.CredWriteW.argtypes = [ctypes.POINTER(CREDENTIAL), wt.DWORD]
adv.CredReadW.argtypes = [wt.LPCWSTR, wt.DWORD, wt.DWORD, ctypes.POINTER(ctypes.POINTER(CREDENTIAL))]
adv.CredFree.argtypes = [ctypes.c_void_p]


def put(name, value):
    blob = value.encode("utf-8")
    c = CREDENTIAL()
    c.Type = CRED_TYPE_GENERIC
    c.TargetName = PREFIX + name
    c.CredentialBlobSize = len(blob)
    c.CredentialBlob = ctypes.cast(ctypes.create_string_buffer(blob, len(blob)), ctypes.POINTER(ctypes.c_char))
    c.Persist = CRED_PERSIST_LOCAL_MACHINE
    c.UserName = "my_ajae"
    if not adv.CredWriteW(ctypes.byref(c), 0):
        raise OSError(ctypes.get_last_error(), "CredWriteW 실패")


def get(name):
    p = ctypes.POINTER(CREDENTIAL)()
    if not adv.CredReadW(PREFIX + name, CRED_TYPE_GENERIC, 0, ctypes.byref(p)):
        return None
    try:
        return ctypes.string_at(p.contents.CredentialBlob, p.contents.CredentialBlobSize).decode("utf-8")
    finally:
        adv.CredFree(p)


def main():
    cmd, name = sys.argv[1], sys.argv[2]
    if cmd == "put-stdin":
        min_len = int(sys.argv[sys.argv.index("--min-len") + 1]) if "--min-len" in sys.argv else 40
        v = sys.stdin.read().strip()
        if not v or any(ch.isspace() for ch in v) or len(v) < min_len:
            raise SystemExit(f"값이 토큰처럼 보이지 않는다(길이 {len(v)}) — 저장하지 않음")
        put(name, v)
        print(f"저장: {PREFIX}{name} (길이 {len(v)})")
    elif cmd == "put-clipboard":
        import subprocess
        min_len = int(sys.argv[sys.argv.index("--min-len") + 1]) if "--min-len" in sys.argv else 40
        v = subprocess.run(["powershell", "-NoProfile", "-Command", "Get-Clipboard -Raw"], capture_output=True,
                           text=True, encoding="utf-8").stdout.strip()
        if not v or any(ch.isspace() for ch in v) or len(v) < min_len:
            raise SystemExit(f"클립보드 값이 토큰처럼 보이지 않는다(길이 {len(v)}) — 저장하지 않음")
        put(name, v)
        subprocess.run(["powershell", "-NoProfile", "-Command", "Set-Clipboard -Value ' '"], capture_output=True)
        print(f"저장: {PREFIX}{name} (길이 {len(v)}), 클립보드 비움")
    elif cmd == "check":
        v = get(name)
        print(f"{PREFIX}{name}: " + (f"있음 (길이 {len(v)})" if v else "없음"))
    else:
        raise SystemExit(__doc__)


if __name__ == "__main__":
    main()
