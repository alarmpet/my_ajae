#!/usr/bin/env node
/**
 * 게시물 검사 — 올리기 전에 막는다 (AGENTS.md §2).
 *
 * 게시물 파일(JSON): { "id": "P0001", "app": "yonghane", "ledger": ["E004"], "text": "…", "card": "…(카드 글자, 선택)" }
 * 실패: 금지 표현 · 본문 주소 · 장부에 없는 ID · 장부 근거에 없는 숫자 · 장부 ID 없음.
 * 판단 못 한 것은 통과가 아니라 보류(경고)로 낸다.
 *
 *   node tools/check_post.mjs posts/P0001.json [더 많은 파일…]
 */
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import path from 'node:path';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');

/** 금지 표현 — 이유를 같이 적는다. 늘릴 때는 이 표만 고친다. */
export const BANNED = [
  [/완전\s*무료|100%\s*무료|평생\s*무료/, '「완전 무료」 — 용하네에는 용한패스가 있다'],
  [/AI\s*사주|AI\s*가\s*(사주|풀이|운세)를?\s*(봐|풀|알려)/, '「AI 사주」 — 용하네는 AI 초안을 사람이 검수 · 승인한 문장만 낸다(앱이 실시간으로 AI 문장을 만들지 않는다)'],
  [/적중/, '「적중」 — 효과 단정'],
  [/용하(다|대요|더라|네요|죠)(?!네)/, '효능을 뜻하는 「용하다」(이름 「용하네」는 괜찮다)'],
  [/반드시\s*(맞|이루|됩|생깁)|틀림없이|무조건\s*(맞|됩)/, '확정 예언'],
  [/큰일\s*(납|나요|난다)|액운|불운이\s*온/, '공포 문구'],
  [/(국내|업계|한국)\s*1위|최초|유일한/, '근거 없는 비교(1위 · 최초 · 유일)'],
  // 의료 · 투자 조언(AGENTS §2-3) — 2026-11-14 추가. 「코인으로 잃었다」 같은 경험담은 막지 않고, 권유 · 효과 단정만 막는다.
  [/(병|질병|질환|우울증|불면증|통증)(이|을|를|도)?\s*(낫|나아|고쳐|고칩|치료)|치료\s*효과|약\s*대신|병원\s*(안\s*가도|갈\s*필요\s*없)/, '의료 조언 · 치료 효과 단정'],
  [/(주식|코인|종목|부동산|비트코인)(을|를|은|는)?\s*(사세요|사라|사야|추천|오릅니다|오른다|오를\s*(겁|거))|(매수|매도)\s*(하세요|추천|타이밍)|(수익|원금)\s*보장|투자\s*(하세요|추천|하면\s*(법니다|벌어요))/, '투자 조언 · 수익 단정'],
  [/어린이\s*(전용|용\s*게임)|아이들\s*전용/, '보카라이더는 전 연령 · 아동 전용 아님'],
  [/사람\s*시험\s*(완료|마쳤|끝냈)/, '와일드 크라운은 사람 시험 전'],
  [/(하루|한\s*시간|몇\s*(분|시간))\s*만에\s*(앱|게임|서비스)|(지시|프롬프트|말)\s*한\s*(줄|마디)(이면|로|만으로)\s*(앱|게임|뚝딱)/, '만능론(「지시 한 줄이면 앱」 · 「하루 만에 앱」) — docs/plan.md §3 · brand/brand.md 말투'],
];

/**
 * 보류(경고) 표현 — 실패는 아니지만 사람이 한 번 본다.
 * 출처: ECC(affaan-m/ECC, MIT) skills/crosspost · skills/brand-voice 의 금지 목록을 한국어 글에 맞게 옮김.
 * 검토 기록: docs/reference/2026-11-12-ecc-review.md
 */
// 말투 · 과장 · 댓글 유도는 막지도 경고하지도 않는다 — 사용자 지시 2026-11-13 「제발 빡빡하게 하지마, 재미없으면 아무도 안 본다」.
// (예전 보류 목록: 미끼 질문 · 판에 박힌 발표 문구 · 교훈 틀 · 「꿀팁 · 대박」 — ECC 에서 옮겼던 것, 걷음)
export const HOLD = [];

const URL_RE = /https?:\/\/|www\.|\b[a-z0-9-]+\.(com|net|io|app|dev|kr|co)\b/i;

/** 글의 숫자 — 쉼표를 뗀 정수 · 소수. 날짜처럼 보이는 1~2자리 단독 숫자도 센다(근거에 있어야 한다). */
export function numbersIn(text) {
  // 줄 첫머리의 목록 번호(「1. 」 「2) 」)는 사실 숫자가 아니다 — 목록형 글(2026-11-13)을 위해 뺀다.
  text = String(text).replace(/^([ \t]*)\d{1,2}[.)](?=[ \t])/gm, '$1');
  // 「1단계 · 5단계 중」 같은 순서 낱말도 사실 숫자가 아니다(2026-11-13).
  text = text.replace(/\d{1,2}(?=\s*단계)/g, '');
  // 「3D · 2D」는 숫자가 아니라 낱말이다 — 뒤에 D 가 붙은 한 자리 숫자는 뺀다.
  return [...String(text).matchAll(/\d[\d,]*(?:\.\d+)?(?![\dD])/g)]
    .filter((m) => !/^\d[Dd]$/.test(String(text).slice(m.index, m.index + 2)))
    .map((m) => m[0].replace(/,/g, ''));
}

export function loadLedger(file = path.join(ROOT, 'ledger', 'events.jsonl')) {
  const map = new Map();
  for (const line of readFileSync(file, 'utf8').split('\n')) {
    if (!line.trim()) continue;
    const e = JSON.parse(line);
    map.set(e.id, e);
  }
  return map;
}

/** @returns {{ fail: string[], hold: string[] }} */
export function checkPost(post, ledger) {
  const fail = [];
  const hold = [];
  // 플랫폼별 글(variants: { instagram, x, … })도 같은 규칙으로 검사한다
  const variants = post.variants && typeof post.variants === 'object' ? Object.values(post.variants) : [];
  const body = [post.text ?? '', post.card ?? '', ...variants].join('\n');
  if (!post.text || !String(post.text).trim()) fail.push('본문이 비었다');
  for (const [re, why] of BANNED) if (re.test(body)) fail.push(`금지 표현: ${why}`);
  if (URL_RE.test(body)) fail.push('본문에 주소가 있다 — 주소는 프로필 링크 하나에만');
  const ids = Array.isArray(post.ledger) ? post.ledger : [];
  if (ids.length === 0) fail.push('장부 ID 가 없다 — 사실은 장부에 있는 것만 쓴다');
  const entries = [];
  for (const id of ids) {
    const e = ledger.get(id);
    if (!e) fail.push(`장부에 없는 ID: ${id}`);
    else {
      entries.push(e);
      if (e.public === false) fail.push(`공개하지 않기로 한 사건: ${id}`);
    }
  }
  if (post.app && entries.length && !entries.some((e) => e.app === post.app || e.app === 'maker')) {
    fail.push(`앱(${post.app})과 장부 사건의 앱이 다르다`);
  }
  const known = new Set(entries.flatMap((e) => numbersIn((e.facts ?? []).join(' ') + ' ' + (e.title ?? ''))));
  // allow_numbers: 사용자가 보고 「그냥 가」로 넘긴 숫자(게시물에 이유와 함께 적는다)
  for (const n of post.allow_numbers ?? []) known.add(String(n));
  for (const n of new Set(numbersIn(body))) if (!known.has(n)) fail.push(`장부 근거에 없는 숫자: ${n}`);
  for (const [re, why] of HOLD) if (re.test(body)) hold.push(`보류 표현: ${why}`);
  if ([...String(post.text ?? '')].length > 500) hold.push('본문 500자 초과 — 스레드에는 이어지는 답글로 나눠 올린다(threads_api.split_text)');
  return { fail, hold };
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const files = process.argv.slice(2);
  if (files.length === 0) { console.error('사용법: node tools/check_post.mjs posts/<파일>.json …'); process.exit(2); }
  const ledger = loadLedger();
  let bad = 0;
  for (const f of files) {
    const post = JSON.parse(readFileSync(f, 'utf8'));
    const { fail, hold } = checkPost(post, ledger);
    if (fail.length) { bad++; console.log(`FAIL ${f}\n  - ${fail.join('\n  - ')}`); }
    else console.log(`${hold.length ? 'HOLD' : 'PASS'} ${f}${hold.length ? `\n  - ${hold.join('\n  - ')}` : ''}`);
  }
  process.exit(bad ? 1 : 0);
}
