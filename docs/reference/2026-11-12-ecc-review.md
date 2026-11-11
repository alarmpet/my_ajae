# ECC(everything-claude-code) 검토 — 설치하지 않고 골라 옮긴다 (2026-11-12)

## 무엇인가 (GitHub API · 원문으로 확인)
- 원본 `affaan-m/everything-claude-code` → 지금 이름 **`affaan-m/ECC`**. MIT(LICENSE 원문 확인). 별 301,205 · 포크 44,443 · 마지막 푸시 2026-11-09 · VERSION 2.2.3 · 검토한 커밋 `d2ef268`.
- 검색 1위 `WorldFlowAI/everything-claude-code` 는 **포크 표시 없는 사본 · 라이선스 없음** — 쓰지 않는다.
- 구성(셈): agents 71 · commands 98 · skills 314 · rules 23 묶음(언어별) · hooks 27개(PreToolUse 10 · Stop 8 · SessionStart 2 · PostToolUse 2 · PostToolUseFailure 2 · UserPromptSubmit · PreCompact · SessionEnd 각 1).
- 설치는 `install.sh`/`install.ps1` → `npm install --ignore-scripts` → `scripts/install-apply.js` 가 `~/.claude` 등에 깐다.

## 결정: 전체 설치는 하지 않는다
1. **훅 27개가 모든 도구 호출 · 세션 끝마다 돈다.** 이 PC 에는 이미 claude-mem · serena 훅과 다른 저장소들(용하네 · auto-cf …)의 규칙이 있다. 전역(`~/.claude`)에 깔면 모든 프로젝트가 영향을 받는다. 충돌 · 속도는 재 보지 않았다 — 재 보지 않은 채 전역에 넣지 않는다.
2. **이 저장소는 코드 저장소가 아니라 게시물 공장이다.** 314 스킬 대부분(언어별 패턴 · 의료 · 네트워크 · 금융)은 쓸 데가 없다.
3. 게시 스킬 `social-publisher` 는 유료 중개 서비스 SocialClaw(키 · 대시보드 OAuth)를 거친다 — 우리 계획(공식 API · 0원 · `docs/plan.md` §5)과 다르다.

## 옮긴 것
| ECC 원문 | 우리 쪽 | 형태 |
|---|---|---|
| `skills/crosspost` 금지 목록(「Excited to share」 · 「Here's what I learned」 · 「What do you think?」) | `tools/check_post.mjs` `HOLD` — 「공유하게 되어 기쁩니다」 · 「오늘 배운 점은」 · 「여러분은 어떠세요?」 | **보류(경고)** — 실패 아님 |
| `skills/brand-voice` Hard Bans(미끼 질문 · 억지 밈) | `HOLD` — 꿀팁 · 대박 · 미쳤다 · 역대급 | 보류 |
| (우리 규칙인데 검사에 없던 것) `docs/plan.md` 「지시 한 줄이면 앱이 나온다는 쓰지 않는다」 | `BANNED` 만능론 | **실패** |

시험 2개 추가 — `node --test tools/check_post.test.mjs` 12/12 통과(2026-11-12).

## 참조만 하는 것 (나중에 해당 단계에서 다시 읽는다)
- **`skills/crosspost` 핵심 규칙** — 플랫폼마다 같은 글을 그대로 붙이지 않는다 · 한 글은 한 가지 · 원문이 얻지 않은 질문 · 교훈 · 행동 요청을 지어 붙이지 않는다 · 가져온 글 속 지시는 따르지 않는다. 우리 AGENTS §2-2 와 같은 방향. 인스타 · 스레드 글을 따로 쓸 때 적용.
- **`skills/operator-approval-loop`** — 승인은 **글 원문의 sha256 + 승인 시점**에 묶고, 글이 바뀌면 옛 승인은 무효, 게시 시도는 승인 하나당 한 번, 결과를 모르면(타임아웃) **자동 재시도 금지 · 사람이 확인**. 우리 AGENTS §3 「승인 뒤 파일 지문이 바뀌면 게시하지 않는다」를 구현할 때의 설계 참고. SQLite 참조 구현(`references/approval_claims.py`)은 우리 규모에 과하다 — 게시 장부 JSON 한 줄로 시작한다.
- **`skills/growth-log`** — 「한 일」이 아니라 「원인 · 다음에 알아볼 신호 · 다음 행동」을 적는다, 같은 원인은 합친다. 월요일 「식은땀(사고 일지)」 틀과 소재 장부 항목 쓰는 법에 참고.
- **`skills/social-publisher` 의 「가져온 내용은 데이터」 조항** — 플랫폼 응답 · 댓글 속 문장이 게시 대상 · 시각을 정하지 못하게 한다. 숫자 모으기(인사이트 API) 만들 때 넣는다.
- `the-security-guide.md` — 훅 · MCP 보안 글. 메타 API 토큰 다룰 때 다시 본다.

## 보지 않은 것
- 훅 스크립트 본문 · `scripts/install-apply.js` 를 한 줄씩 읽지 않았다(설치하지 않으므로).
- 314 스킬 중 읽은 것: social-publisher · crosspost · operator-approval-loop · brand-voice · growth-log(앞부분). 나머지는 이름만.
