// Scene: Settings. The providers you can bring, then the local voice and its preview.
import { Rig, encode } from "../rig.mjs";

const rig = new Rig("settings");
await rig.open("/settings");
await rig.page.addStyleTag({ content: ".provider-pill { visibility: hidden; } input[type=password] { color: transparent !important; }" });
// never show any part of a key, not even the hint
await rig.page.evaluate(() => {
  for (const el of document.querySelectorAll(".small, .hint, input")) {
    if (/key is also set|Saved \(/.test(el.textContent + (el.placeholder ?? ""))) el.classList.add("lv-hide");
  }
});
rig.cursor = { x: 1200, y: 700, visible: true };
await rig.hold(900);
rig.mark("providers");
await rig.scrollTo(".provider-list", 1400);
await rig.hold(200);
const cards = rig.page.locator(".provider-card");
const n = await cards.count();
for (const i of [1, 2, 3].filter((i) => i < n)) {
  await rig.moveTo(cards.nth(i), 650);
  await rig.hold(250);
}
await rig.moveTo({ x: 1250, y: 720 }, 700);
rig.mark("voice");
await rig.scrollTo("#voice", 1600);
await rig.hold(500);
await rig.click('button:has-text("Preview voice")', { moveMs: 900, after: 200 });
await rig.timelapse(async () => (await rig.page.locator('button:has-text("Play again")').count()) > 0, 120, 60000);
await rig.hold(1500);
await rig.close();
console.log("settings:", rig.n, encode("settings"));
