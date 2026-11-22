import { encode } from "./rig.mjs";
for (const n of process.argv.slice(2)) console.log(encode(n));
