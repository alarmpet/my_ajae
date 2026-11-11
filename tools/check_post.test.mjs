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
