import { test } from 'node:test';
import assert from 'node:assert/strict';
import { checkPost, loadLedger, numbersIn } from './check_post.mjs';

const ledger = loadLedger();
const ok = { id: 'T', app: 'yonghane', ledger: ['E004'], text: '근거 줄 1,688개를 모아 보니 86% 에 전문 용어가 있었습니다. 낱말 풀이를 붙였습니다.' };

test('장부 근거 안의 숫자만 쓴 글은 통과한다', () => {
  assert.deepEqual(checkPost(ok, ledger).fail, []);
});

test('장부에 없는 숫자를 쓰면 실패한다 — 사건을 부풀리지 못한다', () => {
  const r = checkPost({ ...ok, text: '근거 줄 1,688개 중 90% 에 전문 용어' }, ledger);
  assert.ok(r.fail.some((f) => f.includes('90')));
});

test('금지 표현은 이유와 함께 실패한다', () => {
  for (const t of ['용하네는 완전 무료입니다', 'AI 사주로 봐 드려요', '적중률이 높아요', '이 앱 정말 용하다', '올해 큰일 납니다', '국내 1위 사주 앱']) {
    const r = checkPost({ ...ok, text: t }, ledger);
    assert.ok(r.fail.some((f) => f.startsWith('금지 표현')), t);
  }
});

test('이름 「용하네」는 금지 표현이 아니다', () => {
  assert.deepEqual(checkPost({ ...ok, text: '용하네에 낱말 풀이를 붙였습니다' }, ledger).fail, []);
});

test('본문에 주소가 있으면 실패한다', () => {
  for (const t of ['자세한 건 https://www.yonghane.com', 'yonghane.com 에서 보세요']) {
    assert.ok(checkPost({ ...ok, text: t }, ledger).fail.some((f) => f.includes('주소')), t);
  }
});

test('장부 ID 가 없거나 장부에 없는 ID 면 실패한다 — 사건을 지어내지 못한다', () => {
  assert.ok(checkPost({ ...ok, ledger: [] }, ledger).fail.some((f) => f.includes('장부 ID 가 없다')));
  assert.ok(checkPost({ ...ok, ledger: ['E999'] }, ledger).fail.some((f) => f.includes('E999')));
});

test('지어낸 사건의 숫자 — 「AI 둘이 1,000판」은 장부(9판)와 달라 실패한다', () => {
  const r = checkPost({ id: 'T', app: 'wildcrown', ledger: ['E009'], text: 'AI 둘이 밤새 1,000판을 두었습니다' }, ledger);
  assert.ok(r.fail.some((f) => f.includes('1000')));
  assert.deepEqual(checkPost({ id: 'T', app: 'wildcrown', ledger: ['E009'], text: 'AI 세 모델이 역할을 나눠 9판을 두고 결함 9건을 찾았습니다. 사람 시험은 아직입니다.' }, ledger).fail, []);
});

test('사람 시험 완료 · 어린이 전용은 실패한다', () => {
  assert.ok(checkPost({ id: 'T', app: 'wildcrown', ledger: ['E009'], text: '사람 시험 완료했습니다' }, ledger).fail.length > 0);
  assert.ok(checkPost({ id: 'T', app: 'vocarider', ledger: ['E008'], text: '어린이 전용 영단어 게임' }, ledger).fail.length > 0);
});

test('의료 · 투자 조언은 실패한다 — 경험담은 통과한다(AGENTS §2-3)', () => {
  for (const t of ['이 운세대로 하면 불면증이 낫습니다', '약 대신 이 앱을 쓰세요', '병원 안 가도 됩니다', '치료 효과가 있어요']) {
    assert.ok(checkPost({ ...ok, text: t }, ledger).fail.some((f) => f.includes('의료 조언')), t);
  }
  for (const t of ['올해는 코인을 사세요', '이 종목 추천합니다', '지금이 매수 타이밍', '수익 보장', '원금 보장됩니다', '투자하세요']) {
    assert.ok(checkPost({ ...ok, text: t }, ledger).fail.some((f) => f.includes('투자 조언')), t);
  }
  for (const t of ['코인 자동 매매를 만들었다가 잃었습니다', '투자 공부는 따로 하세요', '병원 예약 앱이 아닙니다', '낫 놓고 기역 자도 모르던 아재']) {
    assert.deepEqual(checkPost({ ...ok, text: t }, ledger).fail, [], t);
  }
});

test('「AI 사주」 금지 이유는 사실대로 적는다 — 「사람이 쓴다」가 아니라 「AI 초안 → 사람 검수 · 승인」', () => {
  const r = checkPost({ ...ok, text: 'AI 사주로 봐 드려요' }, ledger);
  const why = r.fail.find((f) => f.includes('AI 사주'));
  assert.ok(why.includes('검수'), why);
  assert.ok(!why.includes('사람이 쓴다'), why);
});

test('숫자 뽑기 — 쉼표를 뗀다', () => {
  assert.deepEqual(numbersIn('7,403개와 15,255개 · 5° · 60m'), ['7403', '15255', '5', '60']);
});

test('장부의 모든 항목은 근거 경로와 사실을 가진다', () => {
  for (const e of ledger.values()) {
    assert.ok(e.source && e.source.length > 5, `${e.id} 근거 없음`);
    assert.ok(Array.isArray(e.facts) && e.facts.length > 0, `${e.id} 사실 없음`);
    assert.ok(['yonghane', 'vocarider', 'wildcrown', 'maker'].includes(e.app), `${e.id} 앱`);
  }
});

test('만능론은 실패한다 — 「지시 한 줄이면 앱」 · 「하루 만에 앱」', () => {
  for (const t of ['지시 한 줄이면 앱이 나옵니다', '하루 만에 앱을 만들었어요', '프롬프트 한 줄로 게임 뚝딱']) {
    assert.ok(checkPost({ ...ok, text: t }, ledger).fail.some((f) => f.includes('만능론')), t);
  }
  assert.deepEqual(checkPost({ ...ok, text: '지시에 예외 하나를 적었습니다' }, ledger).fail, []);
});

test('말투 · 과장 · 댓글 유도는 막지도 보류하지도 않는다(2026-11-13 사용자 지시)', () => {
  for (const t of ['여러분은 어떠세요?', '공유하게 되어 기쁩니다', '오늘 배운 점은 이것입니다', '꿀팁 하나', '이거 진짜 미쳤다', 'AI 하나한테만 맡기면 망합니다']) {
    const r = checkPost({ ...ok, text: t }, ledger);
    assert.deepEqual(r.fail, [], t);
    assert.deepEqual(r.hold, [], t);
  }
});

test('「3D · 2D」의 숫자는 세지 않는다 — 다른 숫자는 그대로 센다', () => {
  assert.deepEqual(numbersIn('3D 수식은 직접 못 합니다 · 2D 카드'), []);
  assert.deepEqual(numbersIn('5° 기울였고 3D 화면'), ['5']);
});

test('플랫폼별 글(variants)도 검사한다 — 인스타 글에만 넣은 장부 밖 숫자도 실패', () => {
  const r = checkPost({ ...ok, variants: { instagram: '근거 줄 1,688개 중 99% 에 전문 용어' } }, ledger);
  assert.ok(r.fail.some((f) => f.includes('99')));
  assert.deepEqual(checkPost({ ...ok, variants: { x: '근거 줄 1,688개, 86% 에 전문 용어' } }, ledger).fail, []);
});

test('목록 번호(줄 첫머리 1. 2) )는 숫자로 세지 않는다 — 본문 속 숫자는 센다', () => {
  assert.deepEqual(numbersIn('1. 컷은 2.5초 이하\n2) 첫 2초\n  3. 끝'), ['2.5', '2']);
  assert.deepEqual(numbersIn('10. 열 번째'), []);
  assert.deepEqual(numbersIn('값 1. 끝'), ['1']);
});

test('「N단계」는 숫자로 세지 않고, allow_numbers 는 통과시킨다', () => {
  assert.deepEqual(numbersIn('✔️ 4단계 (첫 장면) · 5단계 중 어디'), []);
  const ledger = loadLedger();
  const p = { id: 'X', app: 'maker', ledger: ['E016'], text: '확률은 0%입니다' };
  assert.ok(checkPost(p, ledger).fail.some((f) => f.includes('숫자: 0')));
  assert.deepEqual(checkPost({ ...p, allow_numbers: ['0'] }, ledger).fail, []);
});
