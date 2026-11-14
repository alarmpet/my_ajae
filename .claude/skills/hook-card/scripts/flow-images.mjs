// Google Flow 로 글자 없는 그림을 한 장씩 만든다 — ego-browser 용 (2026-11-15 실측).
//
// 쓰는 법
//   1) 이 파일과 jobs.json 을 C:/Users/petbl/ego/<목표>-<날짜시각>/ 에 복사한다.
//   2) 아래 D 를 그 폴더로 바꾼다(ego 노드 프로세스에는 환경변수 · 인자가 전달되지 않는다).
//   3) node --check flow-images.mjs   ← 문법 오류가 있으면 ego-browser 가 오류 없이 영원히 멈춘다
//   4) ego-browser nodejs -e 'await import("file:///C:/Users/petbl/ego/<폴더>/flow-images.mjs")'   (백그라운드로)
//   5) 진행은 <폴더>/out/log.txt 를 본다(console.log 는 끝나야 보인다). 끝 줄이 「끝」이면 완료.
//
// 지키는 것
//   · 이미지 모드(Nano Banana) · 지정 비율 · x1 이고 「생성 시 0 크레딧」일 때만 제출한다. 아니면 멈춘다(새 프로젝트는 동영상 모드로 열릴 수 있다).
//   · 한 장씩: 제출 → 진행률이 사라지고 받기 단추가 늘어난 것을 확인 → 받기 → gap_sec 쉼(기본 90초).
//   · 제출 확인(입력칸이 비는 것)이 안 되면 다시 누르지 않고 멈춘다 — 중복 생성 방지.
//   · 「비정상적인 활동」 안내가 보이면 멈춘다. 다른 계정으로 옮겨 잇지 않는다.
//   · 이미 받은 파일은 건너뛴다 → 중간에 끊기면 같은 명령으로 이어 한다.
import fs from "node:fs";

const D = "C:/Users/petbl/ego/REPLACE-ME";          // ← 바꾼다
const cfg = JSON.parse(fs.readFileSync(`${D}/jobs.json`, "utf8"));
const OUT = `${D}/out`;
fs.mkdirSync(OUT, { recursive: true });
const log = (s) => fs.appendFileSync(`${OUT}/log.txt`, `${new Date().toISOString().slice(11, 19)} ${s}\n`);
const statePath = `${D}/state.json`;
const state = fs.existsSync(statePath) ? JSON.parse(fs.readFileSync(statePath, "utf8")) : {};
const RATIO = cfg.ratio || "1:1";
const CHIP = { "1:1": "crop_square", "3:4": "crop_portrait", "4:3": "crop_landscape", "9:16": "crop_9_16", "16:9": "crop_16_9" }[RATIO];
const GAP = (cfg.gap_sec ?? 90) * 1000;

const task = await taskSpace(state.spaceId ?? cfg.space_name ?? "flow-images");
state.spaceId = task.spaceId;
const page = task.page("p1");

// ---- 프로젝트 ----
if (state.project) {
  await page.goto(state.project, { waitUntil: "load", timeout: 60000 });
} else {
  await page.goto("https://labs.google/fx/tools/flow", { waitUntil: "load", timeout: 60000 });
  await page.waitForTimeout(6000);
  const logged = await page.evaluate(() => !!document.querySelector('a[aria-label^="Google 계정"]'));
  if (!logged) { log("멈춤: 로그인돼 있지 않다 — 사용자가 로그인해야 한다"); throw new Error("not logged in"); }
  const ok = await page.evaluate(() => { const e = [...document.querySelectorAll("button,a")].find(e => e.offsetWidth && /새 프로젝트|New project/.test((e.innerText || "") + (e.getAttribute("aria-label") || ""))); if (!e) return false; e.setAttribute("data-ego-new", "1"); e.scrollIntoView({ block: "center", behavior: "instant" }); return true; });
  if (!ok) { log("멈춤: 새 프로젝트 단추 없음"); throw new Error("no new project"); }
  await page.click("[data-ego-new='1']", { label: "새 프로젝트" });
  await page.waitForFunction(() => /\/project\//.test(location.pathname), undefined, { timeout: 30000 });
  state.project = await page.url();
}
await page.waitForTimeout(5000);
fs.writeFileSync(statePath, JSON.stringify(state));
log(`프로젝트 ${state.project} · 공간 ${state.spaceId}`);

// ---- 설정: 이미지 · 비율 · x1 ----
const chip = () => page.evaluate(() => document.querySelector('[aria-label="설정 트리거"]')?.innerText.replace(/\s+/g, " ") || "");
const radios = () => page.evaluate(() => [...document.querySelectorAll("[role=radio],[role=tab]")].filter(e => e.offsetWidth).length);
const good = (c) => /Nano Banana/.test(c) && c.includes(CHIP) && /x1/.test(c);
if (!good(await chip())) {
  if (!(await radios())) { await page.click("[aria-label='설정 트리거']", { label: "설정 열기" }); await page.waitForTimeout(1200); }
  const pick = async (src) => {
    const ok = await page.evaluate((src) => { const re = new RegExp(src); const e = [...document.querySelectorAll("[role=radio],[role=tab]")].find(e => e.offsetWidth && re.test(e.innerText.replace(/\s+/g, " ").trim())); if (!e) return false; document.querySelectorAll("[data-ego-pick]").forEach(x => x.removeAttribute("data-ego-pick")); e.setAttribute("data-ego-pick", "1"); return true; }, src);
    if (ok) { await page.click("[data-ego-pick='1']", { label: "설정 " + src }); await page.waitForTimeout(900); } else log("설정 항목 없음: " + src);
  };
  await pick("^(image )?이미지$");
  await pick(RATIO.replace(":", ":") + "$");
  await pick("^x1$");
  const credit = await page.evaluate(() => (document.body.innerText.match(/생성 시[^\n]{0,30}크레딧[^\n]{0,20}/) || [""])[0]);
  log(`설정 뒤 칩: ${await chip()} · ${credit}`);
  if (credit && !/ 0 크레딧/.test(credit)) { log("멈춤: 0 크레딧이 아니다"); throw new Error("credit"); }
  await page.keyboard.press("Escape").catch(() => {});
}
if (!good(await chip())) { log(`멈춤: 설정이 이미지 ${RATIO} x1 이 아니다 — ${await chip()}`); throw new Error("settings"); }

// ---- 한 장씩 ----
const busy = () => page.evaluate(() => (document.querySelector("main")?.innerText.match(/\n\d+%\n/g) || []).length);
const edLen = () => page.evaluate(() => document.querySelector("[contenteditable=true]")?.textContent.length ?? -1);
const dlCount = () => page.evaluate(() => [...document.querySelectorAll("button")].filter(b => b.textContent.trim() === "download").length);
const jobs = cfg.jobs;
for (let k = 0; k < jobs.length; k++) {
  const [name, scene] = jobs[k];
  if (fs.existsSync(`${OUT}/${name}.jpg`)) { log(`${name} 이미 있음`); continue; }
  if (!good(await chip())) { log(`멈춤: 설정이 바뀌었다 — ${await chip()}`); break; }
  if (/비정상적인 활동/.test(await page.evaluate(() => document.body.innerText))) { log("멈춤: 비정상적인 활동 안내"); break; }
  const before = await dlCount();
  await page.click("[contenteditable=true]", { label: "프롬프트 칸" });
  await page.keyboard.insertText((cfg.base || "") + scene + (cfg.end || ""));
  await page.waitForTimeout(800);
  if ((await edLen()) < 30) { log(`${name} 입력 실패`); break; }
  await page.click("button[type=submit]", { label: "생성 시작" });
  let sent = false;
  for (let i = 0; i < 10; i++) { await page.waitForTimeout(1000); if ((await edLen()) === 0) { sent = true; break; } }
  if (!sent) { log(`${name} 제출 확인 실패 — 다시 누르지 않고 멈춘다`); break; }
  log(`${name} 제출됨`);
  for (let i = 0; i < 20 && (await busy()) === 0; i++) await page.waitForTimeout(1000);
  let done = false;
  for (let i = 0; i < 120; i++) { await page.waitForTimeout(2000); if ((await busy()) === 0 && (await dlCount()) > before) { done = true; break; } }
  if (!done) { log(`${name} 완성 확인 실패`); break; }
  await page.waitForTimeout(3000);
  await page.evaluate(() => { const bs = [...document.querySelectorAll("button")].filter(b => b.textContent.trim() === "download"); document.querySelectorAll("[data-ego-dl]").forEach(x => x.removeAttribute("data-ego-dl")); bs[0].setAttribute("data-ego-dl", "0"); });
  const dl = page.waitForEvent("download", { timeout: 40000 });
  await page.click("[data-ego-dl='0']", { label: "가장 최근 그림 받기" });
  const d = await dl; await d.saveAs(`${OUT}/${name}.jpg`);
  log(`${name} 받음 — ${d.suggestedFilename()}`);
  if (k < jobs.length - 1) { log(`${GAP / 1000}초 쉼`); await page.waitForTimeout(GAP); }
}
log("끝");
