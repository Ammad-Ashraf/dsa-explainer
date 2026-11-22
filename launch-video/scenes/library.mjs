// Scene: the library of ready-made lessons, then Dijkstra's page with its pseudocode lighting up per operation.
import { Rig, encode } from "../rig.mjs";

const rig = new Rig("library");
await rig.open("/library");
await rig.page.addStyleTag({ content: ".provider-pill { visibility: hidden; }" });
rig.cursor = { x: 1180, y: 700, visible: true };
await rig.hold(1000);
rig.mark("grid");
const graphs = await rig.page.evaluate(() => {
  const h = [...document.querySelectorAll(".category-group")].find((g) => /graph/i.test(g.querySelector("h2")?.textContent ?? ""));
  return h ? h.getBoundingClientRect().top + scrollY - 110 : 1400;
});
await rig.scrollTo(graphs, 2600);
await rig.hold(500);
rig.mark("open");
await rig.click('a.algo-card[href="/library/dijkstra"]', { moveMs: 900, after: 150 });
await rig.page.waitForSelector(".algo-head");
await rig.hold(1400);
rig.mark("ops");
await rig.scrollTo(".code", 1600);
await rig.hold(300);
const ops = rig.page.locator(".ops button");
const count = await ops.count();
for (let i = 0; i < Math.min(2, count); i++) {
  await rig.click(ops.nth(i), { moveMs: 800, after: 1300 });
}
await rig.hold(600);
await rig.close();
console.log("library:", rig.n, encode("library"));
