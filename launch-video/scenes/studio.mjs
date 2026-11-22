// Scene: type a topic in the Studio, start the lesson, and watch the pipeline make it (as a timelapse).
// This makes a real lesson with the configured language model.
import fs from "node:fs";
import { BASE, Rig, encode } from "../rig.mjs";

const TOPIC = "Insert 8, 3, 10, 1, 6, 14 into a BST, then delete 3";
const rig = new Rig("studio");
await rig.open("/studio");
await rig.page.addStyleTag({ content: ".provider-pill { visibility: hidden; }" });
await rig.page.evaluate(() => document.activeElement?.blur());
rig.cursor = { x: 1100, y: 640, visible: true };
await rig.hold(900);
rig.mark("type");
await rig.click("#topic", { moveMs: 800, after: 200 });
await rig.type(TOPIC, 48);
await rig.hold(500);
rig.mark("options");
await rig.click('.options button:has-text("Intermediate")', { moveMs: 750 });
await rig.click('.options button:has-text("720p")', { moveMs: 650 });
await rig.hold(300);
rig.mark("submit");
await rig.click('button[type=submit]:has-text("Make my lesson")', { moveMs: 800, after: 100 });
await rig.page.waitForURL(/\/studio\/job\//, { timeout: 30000 });
const jobId = rig.page.url().split("/").pop();
await rig.moveTo({ x: 1300, y: 760 }, 700);
rig.mark("job");
await rig.hold(1200);

let job = null;
const finished = async () => {
  job = await (await fetch(`${BASE}/api/jobs/${jobId}`)).json();
  return job.status !== "queued" && job.status !== "running";
};
rig.mark("timelapse");
const seconds = await rig.timelapse(finished, 500);
rig.mark("done");
await rig.page.waitForSelector(".tabs, [role=tablist]", { timeout: 60000 }).catch(() => {});
await rig.hold(2500);
rig.meta = { jobId, realSeconds: seconds, status: job.status, result: job.result, error: job.error };
await rig.close();
fs.writeFileSync("captures/lesson.json", JSON.stringify({ jobId, ...job.result, status: job.status, error: job.error }, null, 2));
console.log("studio:", rig.n, "frames,", Math.round(seconds), "s real,", job.status, job.result ?? job.error);
console.log(encode("studio"));
