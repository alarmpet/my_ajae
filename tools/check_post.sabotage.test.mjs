// 검사를 일부러 깨 본다 — 규칙을 하나 빼면 그 규칙의 본보기 글이 통과해 버리는지(= 그 규칙이 실제로 막고 있는지).
// 계획 docs/plans/2026-11-18-cross-project-assets-plan.md §3(용하네 tools/sabotage.mjs 의 생각을 가져옴) · §4-2.
//   node --test tools/check_post.sabotage.test.mjs
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { BANNED, YONGHANE_RULES, checkPost, loadLedger, loadYonghanePolicy, parseYonghanePolicy } from './check_post.mjs';

const ledger = loadLedger();
const base = { id: 'T', app: 'yonghane', ledger: ['E004'] };

/** BANNED 와 같은 순서 — 규칙마다 그 규칙에만 걸리는 본보기 글 하나. 규칙을 늘리면 여기도 늘린다. */
const SAMPLES = [
  '이 앱은 완전 무료예요',
  'AI 사주 보러 오세요',
  '적중한 풀이',
  '광고가 없어요',
  '이 집 정말 용하다',
  '무조건 맞아요',
  '올해 액운 조심',
  '업계 1위 앱',
  '불면증이 나아요',
  '코인을 사세요',
  '어린이 전용 게임',
  '사람 시험 완료',
  '지시 한 줄이면 앱이 나와요',
];

test('금지 표현 규칙마다 본보기 글이 있다 — 규칙만 늘리고 시험을 안 늘리면 여기서 걸린다', () => {
  assert.equal(SAMPLES.length, BANNED.length);
});

test('본보기 글은 자기 규칙 하나에만 걸린다', () => {
  SAMPLES.forEach((t, i) => {
    const hit = BANNED.map(([re], k) => (re.test(t) ? k : -1)).filter((k) => k >= 0);
    assert.deepEqual(hit, [i], `「${t}」 → 걸린 규칙 ${hit.join(',')} (기대 ${i})`);
  });
});

test('깨 보기: 규칙 하나를 빼면 그 본보기 글이 금지 표현 없이 지나간다', () => {
  SAMPLES.forEach((t, i) => {
    const before = checkPost({ ...base, text: t }, ledger).fail.filter((f) => f.startsWith('금지 표현'));
    assert.equal(before.length, 1, `「${t}」 는 지금 막혀야 한다`);
    const [removed] = BANNED.splice(i, 1); // 일부러 망가뜨린다
    try {
      const after = checkPost({ ...base, text: t }, ledger).fail.filter((f) => f.startsWith('금지 표현'));
      assert.equal(after.length, 0, `규칙 ${i} 를 뺐는데도 「${t}」 가 막혔다 — 다른 규칙이 가리고 있다`);
    } finally {
      BANNED.splice(i, 0, removed);
    }
  });
});

const fake = parseYonghanePolicy({ rules: [
  { id: 'authenticity-claim', pattern: '정통 (사주|토정)', reason: '정통 표현 금지' },
  { id: 'korean-bracket-particle', pattern: '을\\(를\\)', reason: '코드용' },
  { id: 'brand-new-rule', pattern: '새 규칙', reason: '처음 보는 규칙' },
] });

test('용하네 정책: 고른 규칙만 걸고, 코드용은 빼고, 처음 보는 규칙은 알림으로 돌린다', () => {
  assert.deepEqual(fake.rules.map((r) => r.id), ['authenticity-claim']);
  assert.deepEqual(fake.unknown, ['brand-new-rule']);
});

test('용하네 정책은 용하네 글에만 건다', () => {
  const t = '정통 사주 풀이를 붙였습니다';
  assert.ok(checkPost({ ...base, text: t }, ledger, fake).fail.some((f) => f.includes('용하네 정책 authenticity-claim')));
  assert.deepEqual(checkPost({ ...base, app: 'vocarider', ledger: ['E004'], text: t }, ledger, fake).fail.filter((f) => f.includes('용하네 정책')), []);
  assert.deepEqual(checkPost({ ...base, text: t }, ledger).fail.filter((f) => f.includes('용하네 정책')), []); // 정책을 안 넘기면 예전과 같다
});

test('용하네 정책을 못 읽으면 통과가 아니라 보류로 낸다', () => {
  const r = checkPost({ ...base, text: '낱말 풀이를 붙였습니다' }, ledger, { rules: [], unknown: [], error: '용하네 정책을 읽지 못했다(시험)' });
  assert.ok(r.hold.some((h) => h.includes('검사하지 못했다')));
});

test('운영본 정책에 우리가 고른 규칙이 실제로 있다(이름이 바뀌면 조용히 빠지지 않게)', (t) => {
  const live = loadYonghanePolicy();
  if (live.error) return t.skip(live.error); // 용하네 저장소가 없는 PC
  assert.deepEqual(live.rules.map((r) => r.id).sort(), [...YONGHANE_RULES].sort());
});
