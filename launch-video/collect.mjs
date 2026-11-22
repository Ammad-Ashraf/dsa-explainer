// Gather every capture's marks into one file the composition can import.
import fs from "node:fs";
const out = {};
for (const name of fs.readdirSync("captures")) {
  const f = `captures/${name}/marks.json`;
  if (fs.existsSync(f)) out[name] = JSON.parse(fs.readFileSync(f, "utf8"));
}
fs.writeFileSync("src/marks.json", JSON.stringify(out, null, 2));
console.log(Object.fromEntries(Object.entries(out).map(([k, v]) => [k, { frames: v.frames, ...v.marks }])));
