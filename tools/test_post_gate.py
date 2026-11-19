"""게시 관문 시험 — 외부 API 를 한 번도 부르지 않는 것을 확인한다 (2026-11-19).

    python -X utf8 -m unittest tools/test_post_gate.py

계획 docs/plans/2026-11-19-integrated-ops-marketing-plan.md §8 P0 「확인 없는 직접/예약 · 변경된 캐러셀 · 누락 지문 ·
검사 FAIL 에서 외부 쓰기 호출 0」을 가짜 API 로 잰다. 실제 게시물(L0024 등)의 파일을 읽기만 한다.
"""
import json
import sys
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import ig_api  # noqa: E402
import post_gate  # noqa: E402
import threads_api  # noqa: E402


def a_confirmed_slot():
    """확인 기록이 있고 지금 지문과 같은 (글, 날짜) 하나."""
    f = ROOT / "posts/list/CONFIRMED.jsonl"
    for line in reversed(f.read_text(encoding="utf-8").splitlines()):
        if line.strip():
            r = json.loads(line)
            try:
                if post_gate.confirmed(r["id"], r["date"]):
                    return r["id"], r["date"]
            except SystemExit:
                continue
    raise unittest.SkipTest("지금 지문과 맞는 확인 기록이 없다")


class NoNetwork(unittest.TestCase):
    def setUp(self):
        # 외부로 나가는 길을 모두 가짜로 — 불리면 그 자체가 실패다
        self.calls = []
        boom = lambda *a, **k: self.calls.append((a, k)) or (_ for _ in ()).throw(AssertionError("외부 호출"))  # noqa: E731
        self.patches = [mock.patch.object(threads_api, "api", boom), mock.patch.object(ig_api, "api", boom),
                        mock.patch.object(threads_api, "r2", boom), mock.patch.object(ig_api, "r2", boom)]
        for p in self.patches:
            p.start()
        self.pid, self.date = a_confirmed_slot()

    def tearDown(self):
        for p in self.patches:
            p.stop()

    def assertBlocked(self, fn, *args, word=""):
        with self.assertRaises(SystemExit) as cm:
            fn(*args)
        self.assertEqual(self.calls, [], "막혀야 하는데 외부 호출이 있었다")
        self.assertIn(word, str(cm.exception))

    def test_직접_명령도_그날_확인이_없으면_막는다(self):
        for fn in (threads_api.publish, ig_api.publish, threads_api.first_comment, ig_api.first_comment):
            self.assertBlocked(fn, self.pid, "2099-01-01", word="사용자 확인 기록 없음")

    def test_날짜를_안_주면_오늘_기준(self):
        with mock.patch.object(post_gate, "today", return_value="2099-01-01"):
            self.assertBlocked(threads_api.publish, self.pid, word="2099-01-01")

    def test_승인_목록에_없는_미디어는_막는다(self):
        # 글만 올리는 게시물이어도 시험이 되도록 — 미디어가 있는 모양으로 바꾸고, 승인 안 된 카드 한 장을 끼운다
        post = dict(threads_api.verify(self.pid), text_only=False)
        extra = lambda p: ("CAROUSEL", [ROOT / "out/cards/W46/P0001.jpg"])  # noqa: E731
        with mock.patch.object(threads_api, "verify", return_value=post), mock.patch.object(threads_api, "media_of", extra):
            self.assertBlocked(threads_api.publish, self.pid, self.date, word="승인 목록에 없다")
            self.assertBlocked(ig_api.publish, self.pid, self.date, word="승인 목록에 없다")

    def test_검사_FAIL_이면_막는다(self):
        with mock.patch.object(post_gate, "check_post", return_value=["- 금지 표현: 시험"]):
            self.assertBlocked(ig_api.publish, self.pid, self.date, word="검사 FAIL")

    def test_지문이_바뀌면_막는다(self):
        with mock.patch.object(threads_api, "verify", side_effect=SystemExit("지문 불일치(시험)")):
            self.assertBlocked(threads_api.publish, self.pid, self.date, word="지문 불일치")

    def test_관문을_통과하면_그다음에야_외부로_간다(self):
        # 관문은 통과하고, 이미 올린 글이면 외부 호출 없이 멈춘다 — 중복 확인이 계정 확인보다 먼저
        with mock.patch.object(threads_api, "already", return_value=True):
            self.assertBlocked(threads_api.publish, self.pid, self.date, word="이미 스레드에 올렸다")
        with mock.patch.object(ig_api, "already", return_value=True):
            self.assertBlocked(ig_api.publish, self.pid, self.date, word="이미 인스타에 올렸다")

    def test_같은_글_같은_플랫폼_동시_실행은_막는다(self):
        with post_gate.lock(self.pid, "threads"):
            self.assertBlocked(threads_api.publish, self.pid, self.date, word="다른 실행이 게시 중")
        self.assertFalse((post_gate.LOCKS / f"{self.pid}-threads.lock").exists(), "잠금이 남았다")


class Preview(unittest.TestCase):
    def test_미리_보기는_인스타_실제_캡션과_미디어_순서를_보인다(self):
        import run_schedule
        pid, _ = a_confirmed_slot()
        post = threads_api.verify(pid)
        out = run_schedule.show(pid, ["threads", "instagram"])
        plats = post.get("platforms") or ["threads", "instagram"]
        if "instagram" in plats:
            self.assertIn(ig_api.caption_of(post), out)
        self.assertIn("게시물 검사:", out)
        if not post.get("text_only"):
            for f in threads_api.media_of(post)[1]:
                self.assertIn(str(f.relative_to(ROOT)), out)


if __name__ == "__main__":
    unittest.main()
