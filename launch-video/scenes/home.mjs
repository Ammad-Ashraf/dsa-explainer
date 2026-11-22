// Scene: the home page. The hero settles in, then a slow, smooth scroll through the benefits and the pipeline.
import { Rig, encode } from "../rig.mjs";

const rig = new Rig("home");
await rig.open("/");
await rig.page.addStyleTag({ content: ".provider-pill { visibility: hidden; }" });
rig.mark("hero");
await rig.hold(2600);
await rig.moveTo(".hero .btn-primary", 1100);
await rig.hold(700);
await rig.moveTo({ x: 1240, y: 640 }, 900);
rig.mark("scroll");
// one benefit at a time: glide, then let it settle while it fades in
for (const id of ["#checked", "#local", "#quiz", "#change"]) {
  await rig.scrollTo(id, 1500);
  await rig.hold(1300);
}
rig.mark("pipeline");
await rig.scrollTo("#how-it-works", 1700);
await rig.hold(2600);
rig.mark("popular");
await rig.scrollTo(".popular", 1500);
await rig.hold(1800);
await rig.close();
console.log("home:", rig.n, "frames ->", encode("home"));
