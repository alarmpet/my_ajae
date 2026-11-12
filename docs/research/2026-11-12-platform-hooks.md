# 플랫폼별 첫 줄 · 첫 3초 · 배포 — 조사 (2026-11-12)

하위 에이전트가 웹에서 조사했다. [공식] 플랫폼 원문 · [데이터] 표본 있는 업체 조사 · [2차] 기사 · **미확인** = 원문 못 찾음. 업체 시간대 조사는 전 세계 집계라 한국 시간에 쓰지 않는다.

## 사용자 질문 「스레드는 첫 줄 후킹이 가장 중요하다는데?」
- **메타 원문에 그런 말은 없다(미확인).** 원문이 말하는 것:
  - Threads 피드 AI 는 좋아요 · 글/프로필 누르기 · 답글 · **스크롤로 지나치기** · 머문 시간을 예측한다. 최근 15분 좋아요, 답글의 답글(2단계 대화)을 신호로 쓴다 — https://transparency.meta.com/features/explaining-ranking/ig-threads-feed/ (2025-03-07)
  - **답글이 전체 조회의 거의 절반.** Threads 전용 오리지널 글, 주 2~5회 이상, 사진 · 영상에 글을 같이 넣은 글이 조회가 많다 — https://about.fb.com/news/2024/10/find-your-community-with-new-threads-educational-insights/
  - 남의 글에 답글 다는 것이 글 쓰는 것만큼 중요, 주제 태그는 관심사 사용자에게 닿게 함(글 하나에 1개) — https://creators.instagram.com/threads
  - 모세리(2024-10): 낚시성 참여 유도를 통제하려 한다 — https://www.engadget.com/social-media/meta-is-working-to-fix-threads-engagement-bait-problem-173135011.html
- 그래서 **첫 줄은 「지나치지 않게」(사건 + 결과), 끝 줄은 진짜 질문(답글)** 이 원문에 맞는 해석이다. 「답글이 좋아요의 3배」 같은 가중치는 근거 없음.
- [데이터] Buffer 2026(45M+ 게시물) Threads 참여율 중앙값: 영상 5.55% · 이미지 4.55% · 텍스트 2.79% · 링크 2.34% — https://buffer.com/resources/data-best-content-format-social-media/

## Instagram
- [공식] 피드는 머묾 · 댓글 · 좋아요 · 공유 · 프로필 누르기 예측, 릴스는 **다시 공유 · 끝까지 시청 · 좋아요 · 오디오 페이지** 순. 릴스 덜 추천: **저해상도 · 워터마크 · 무음 · 테두리 · 글자뿐인 영상 · 이미 올라간 영상** — https://about.instagram.com/blog/announcements/instagram-ranking-explained (2023-05-31)
- [2차] 모세리 2025-01: 시청 시간 · 좋아요 · 보내기(sends)가 핵심, 보내기는 비팔로워 도달에 더 중요 — https://www.socialmediatoday.com/news/instagram-shares-algorithm-insights-2025/738034/
- [공식] 2026-04-30 오리지널 보호를 사진 · 캐러셀로 확대 — 남의 것에 테두리 · 워터마크 · 자막만 더하면 비오리지널 — https://creators.instagram.com/blog/rewarding-original-creators-on-instagram
- 캐러셀 앱 최대 20장(2024-08), API 10장 상한은 미확인 → **10장 이내**로. [데이터] Buffer 2026: 캐러셀 6.9% · 이미지 4.4% · 릴스 3.3%(참여율), 도달은 릴스가 캐러셀의 1.36배.

## YouTube Shorts
- [공식] 최대 3분 · 세로 · 1080p — https://support.google.com/youtube/answer/10059070 · 분석에 「시청함 vs 스와이프」 지표 — https://support.google.com/youtube/answer/12220281 (순위 기준이라는 공식 진술은 미확인)
- [공식 정책] 2025-07-15 반복 · 대량 생산 콘텐츠를 「진정성 없는 콘텐츠」로 — https://support.google.com/youtube/answer/1311392

## TikTok
- [공식] 끝까지 시청 같은 상호작용이 가장 강한 신호, **팔로워 수 · 과거 히트는 직접 요인 아님**, 중복 · 스팸 비추천 — https://newsroom.tiktok.com/en-us/how-tiktok-recommends-videos-for-you
- [공식] 2026-09-24 시행: 새것 없는 재사용 · 참여 조작은 추천 피드 제외, **사실적 AI 생성물 표시 의무** — https://www.tiktok.com/community-guidelines/en/integrity-authenticity

## X
- [공식 코드] xai-org/x-algorithm README: 행동 확률 × 가중치 합, 차단 · 뮤트 · 신고는 음수, **같은 작성자 두 번째 글부터 감쇠**, 신규 작성자 끌어올림, 48시간 넘은 글 · 중복 제외 — https://github.com/xai-org/x-algorithm
- [2차] 가중치(원파일 미확인): 링크 복사 공유 20 · 답글 5 · 인용 5 · DM 공유 5 · 좋아요 0.5 — https://ppc.land/x-gives-copy-link-shares-a-feed-weight-of-20-against-0-5-for-likes/
- 링크 강등 없다는 회사 진술(독립 측정 아님) — https://ppc.land/x-drops-year-old-link-penalty-musk-tells-zuckerberg-on-platform/

## 우리 계정 규칙 (이 조사에서)
1. 첫 줄 · 첫 장면 · 표지 = **장부의 사건 하나와 그 실제 결과.** 장부 밖 숫자로 궁금증을 만들지 않는다.
2. Threads 끝 줄은 **답을 듣고 싶은 진짜 질문.** 「댓글 달면 ○○」 금지.
3. 플랫폼마다 따로 내보낸다. 다른 앱 워터마크 · 테두리 · 무음 · 저해상도 금지.
4. 남의 화면 · 글은 쓰지 않는다. 우리 앱 화면 + 맥락을 더하는 글 = 오리지널.
5. 릴스 · 쇼츠 · 틱톡: 9:16, 화면 자막, 소리 없이도 이해되게, 15~40초에서 시험(우리 가정).
6. 캐러셀: 표지에 결과 + 실제 화면, 10장 이내.
7. Threads 주 2~5회 이상, 남의 글에 **사람이 직접** 답글. 주제 태그 1개.
8. X 는 몰아 올리지 않는다(작성자 감쇠).
9. TTS · 사실적 생성 영상 → 틱톡 · 인스타 · 유튜브 AI 표시를 켠다.
10. 게시 시각은 우리 인사이트 데이터로 4주마다 정한다.

**미확인:** Threads 첫 줄 훅 공식 근거 · 답글/보내기 배수 · 쇼츠 시청함 비율의 순위 사용 · TikTok Academy 첫 3초 원문 · X param.rs 원파일 · 인스타 API 캐러셀 10장 공식 문서 · 한국 시간대 데이터.
