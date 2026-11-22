// Scene: the finished lesson. Play two moments of the video, answer the quiz wrongly, look at what was verified,
// then ask for a change ("Slow down step 2") and watch only that scene being drawn again.
import fs from "node:fs";
import { BASE, Rig, encode } from "../rig.mjs";

const { lesson_id: id } = JSON.parse(fs.readFileSync("captures/lesson.json", "utf8"));
const detail = await (await fetch(`${BASE}/api/lessons/${id}?version=1`)).json();
const chapters = Object.fromEntries(detail.version_info.chapters.map((c) => [c.name, c]));

const rig = new Rig("lesson");
rig.meta = { audio: [] };
await rig.open(`/lessons/${id}?version=1`);
await rig.page.addStyleTag({ content: ".provider-pill { visibility: hidden; }" });
await rig.page.waitForSelector(".screen video");
rig.cursor = { x: 1200, y: 700, visible: true };

async function play(name, ms) {
  const c = chapters[name];
  await rig.click(rig.page.locator(".chapters .chapter", { hasText: new RegExp(`^${name}`, "i") }).first(), { moveMs: 800, after: 0 });
  await rig.page.evaluate(() => { const v = document.querySelector(".screen video"); v.controls = false; });
  rig.videoClock = { selector: ".screen video", from: rig.vt, start: c.start + 0.01 };
  const first = rig.n;
  await rig.moveTo({ x: 1380, y: 330 }, 900);
  await rig.hold(ms - 900);
  rig.meta.audio.push({ frame: first, frames: rig.n - first, start: c.start + 0.01 });
  rig.videoClock = null;
}

// a still of the opening, then two moments of the lesson
await rig.page.evaluate(async () => {
  const v = document.querySelector(".screen video");
  await new Promise((r) => { if (v.readyState >= 2) r(); else v.addEventListener("loadeddata", r, { once: true }); });
  v.controls = false;
  v.currentTime = 2;
  await new Promise((r) => v.addEventListener("seeked", r, { once: true }));
});
rig.mark("open");
await rig.hold(900);
rig.mark("play4");
await play("step 4", 7800);
rig.mark("play7");
await play("step 7", 10500);
await rig.page.evaluate(() => { document.querySelector(".screen video").controls = true; });

// quiz: pick a wrong answer to see why it is wrong
rig.mark("quiz");
await rig.scrollTo(".tabs", 1500);
const q = detail.quiz[0];
const wrong = q.options.findIndex((_, k) => k !== q.answer && q.why_wrong?.[k]) >= 0
  ? q.options.findIndex((_, k) => k !== q.answer && q.why_wrong?.[k]) : (q.answer + 1) % q.options.length;
await rig.click(rig.page.locator(".quiz-q").first().locator(".quiz-option").nth(wrong), { moveMs: 900, after: 2600 });

// verified
rig.mark("verified");
await rig.click('.tabs button:has-text("Verified")', { moveMs: 800, after: 1400 });
await rig.scrollTo(".timeline", 1300);
await rig.hold(2200);

// plan
rig.mark("plan");
await rig.scrollTo(".tabs", 1000);
await rig.click('.tabs button:has-text("Plan")', { moveMs: 700, after: 1600 });

// change it
rig.mark("change");
await rig.click('.tabs button:has-text("Change it")', { moveMs: 700, after: 500 });
await rig.click("#change", { moveMs: 700, after: 150 });
await rig.type("Slow down step 2", 55);
await rig.hold(400);
await rig.click('button[type=submit]:has-text("Make version")', { moveMs: 800, after: 100 });
await rig.page.waitForURL(/\/studio\/job\//, { timeout: 30000 });
const jobId = rig.page.url().split("/").pop();
await rig.moveTo({ x: 1300, y: 760 }, 600);
rig.mark("revise");
let job;
rig.meta.reviseReal = await rig.timelapse(async () => {
  job = await (await fetch(`${BASE}/api/jobs/${jobId}`)).json();
  return job.status !== "queued" && job.status !== "running";
}, 250);
rig.mark("revised");
await rig.page.waitForSelector(".tabs", { timeout: 60000 });
await rig.hold(1200);
await rig.click('.tabs button:has-text("Verified")', { moveMs: 800, after: 400 });
await rig.scrollTo(".stats", 1200);
await rig.hold(2600);
rig.meta.revise = job.result;
await rig.close();
console.log("lesson:", rig.n, JSON.stringify(rig.meta), encode("lesson"));
