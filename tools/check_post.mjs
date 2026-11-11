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
  [/AI\s*사주|AI\s*가\s*(사주|풀이|운세)를?\s*(봐|풀|알려)/, '「AI 사주」 — 용하네의 풀이 문장은 사람이 쓴다'],
  [/적중/, '「적중」 — 효과 단정'],
  [/용하(다|대요|더라|네요|죠)(?!네)/, '효능을 뜻하는 「용하다」(이름 「용하네」는 괜찮다)'],
  [/반드시\s*(맞|이루|됩|생깁)|틀림없이|무조건\s*(맞|됩)/, '확정 예언'],
  [/큰일\s*(납|나요|난다)|액운|불운이\s*온/, '공포 문구'],
  [/(국내|업계|한국)\s*1위|최초|유일한/, '근거 없는 비교(1위 · 최초 · 유일)'],
  [/어린이\s*(전용|용\s*게임)|아이들\s*전용/, '보카라이더는 전 연령 · 아동 전용 아님'],
  [/사람\s*시험\s*(완료|마쳤|끝냈)/, '와일드 크라운은 사람 시험 전'],
];

const URL_RE = /https?:\/\/|www\.|\b[a-z0-9-]+\.(com|net|io|app|dev|kr|co)\b/i;

/** 글의 숫자 — 쉼표를 뗀 정수 · 소수. 날짜처럼 보이는 1~2자리 단독 숫자도 센다(근거에 있어야 한다). */
export function numbersIn(text) {
  return [...String(text).matchAll(/\d[\d,]*(?:\.\d+)?/g)].map((m) => m[0].replace(/,/g, ''));
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
  const body = [post.text ?? '', post.card ?? ''].join('\n');
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
  for (const n of new Set(numbersIn(body))) if (!known.has(n)) fail.push(`장부 근거에 없는 숫자: ${n}`);
  if ([...String(post.text ?? '')].length > 500) hold.push('본문 500자 초과 — 스레드 글자 한도(미대조)');
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
