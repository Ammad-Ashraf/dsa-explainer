// A frame-stepped capture rig: every CSS animation, transition and SVG (SMIL) animation in the page is paused and
// driven from a virtual clock, so each captured frame is exactly 1/FPS apart no matter how slow the screenshot is.
// The result is perfectly smooth scrolling, typing and cursor motion, as if recorded on a very fast machine.
import { chromium } from "playwright-core";
import { execFileSync } from "node:child_process";
import fs from "node:fs";
import path from "node:path";

export const BASE = "http://127.0.0.1:8000";
export const FPS = 60;
export const VIEW = { width: 1440, height: 810 };
export const DPR = 1.5;

const INIT = `
(() => {
  const seen = new WeakMap();
  window.__lv = {
    step(vt) {
      for (const a of document.getAnimations()) {
        if (!seen.has(a)) seen.set(a, vt);
        try { a.pause(); a.currentTime = Math.max(0, vt - seen.get(a)); } catch (e) {}
      }
      for (const svg of document.querySelectorAll("svg")) {
        if (svg.ownerSVGElement) continue;
        if (!seen.has(svg)) seen.set(svg, vt);
        try { svg.pauseAnimations(); svg.setCurrentTime((vt - seen.get(svg)) / 1000); } catch (e) {}
      }
    },
    release() {
      for (const a of document.getAnimations()) { try { a.play(); } catch (e) {} }
      for (const svg of document.querySelectorAll("svg")) { try { svg.unpauseAnimations(); } catch (e) {} }
    },
  };
  const css = document.createElement("style");
  css.textContent = \`
    html { scroll-behavior: auto !important; }
    ::-webkit-scrollbar { display: none; }
    html { scrollbar-width: none; }
    #lv-cursor { position: fixed; left: 0; top: 0; z-index: 2147483647; pointer-events: none; will-change: transform;
      filter: drop-shadow(0 2px 3px rgba(0,0,0,.28)); }
    #lv-ring { position: fixed; z-index: 2147483646; pointer-events: none; width: 44px; height: 44px; margin: -22px 0 0 -22px;
      border-radius: 50%; background: rgba(88, 204, 2, .28); border: 2px solid rgba(88, 204, 2, .8); opacity: 0; }
    .lv-hide { visibility: hidden !important; }
  \`;
  const mount = () => {
    document.head.appendChild(css);
    const c = document.createElement("div");
    c.id = "lv-cursor";
    c.innerHTML = '<svg width="26" height="30" viewBox="0 0 26 30"><path d="M3 2 L3 24 L8.6 18.8 L12.4 27.4 L16.4 25.6 L12.7 17.2 L20.6 17.2 Z" fill="#fff" stroke="#1f2933" stroke-width="1.8" stroke-linejoin="round"/></svg>';
    const r = document.createElement("div");
    r.id = "lv-ring";
    document.body.appendChild(r);
    document.body.appendChild(c);
  };
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", mount); else mount();
})();
`;

const ease = (t) => (t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2); // easeInOutCubic
const easeOut = (t) => 1 - Math.pow(1 - t, 3);

export class Rig {
  constructor(name) {
    this.name = name;
    this.dir = path.join("captures", name);
    fs.rmSync(this.dir, { recursive: true, force: true });
    fs.mkdirSync(this.dir, { recursive: true });
    this.n = 0;
    this.vt = 0;
    this.cursor = { x: VIEW.width * 0.62, y: VIEW.height * 0.72, visible: false };
    this.clickAt = -1e9;
    this.marks = {};
    this.videoClock = null; // { selector, from (vt), start (media seconds) }
    this.hooks = [];
  }

  async open(url = "/") {
    this.browser = await chromium.launch({ executablePath: "C:/Program Files/Google/Chrome/Application/chrome.exe", headless: true,
      args: ["--autoplay-policy=no-user-gesture-required", "--hide-scrollbars"] });
    this.page = await this.browser.newPage({ viewport: VIEW, deviceScaleFactor: DPR });
    await this.page.addInitScript(INIT);
    await this.goto(url);
  }

  async goto(url) {
    await this.page.goto(BASE + url, { waitUntil: "networkidle" });
    await this.page.evaluate(() => document.fonts.ready);
  }

  mark(label) { this.marks[label] = this.n; }

  /** One frame: advance the virtual clock, pose the page, take the picture. */
  async frame() {
    const { x, y, visible } = this.cursor;
    const since = this.vt - this.clickAt;
    const p = Math.min(1, since / 450);
    const ring = since >= 0 && since < 450 ? { s: 0.4 + 0.9 * easeOut(p), o: 1 - p } : { s: 0, o: 0 };
    const clock = this.videoClock;
    await this.page.evaluate(async ({ vt, x, y, visible, ring, clock }) => {
      window.__lv?.step(vt);
      const c = document.getElementById("lv-cursor");
      if (c) { c.style.transform = `translate(${x - 3}px, ${y - 2}px)`; c.style.opacity = visible ? "1" : "0"; }
      const r = document.getElementById("lv-ring");
      if (r) { r.style.left = `${x}px`; r.style.top = `${y}px`; r.style.opacity = String(ring.o); r.style.transform = `scale(${ring.s})`; }
      if (clock) {
        const v = document.querySelector(clock.selector);
        if (v) {
          if (!v.paused) v.pause();
          const t = clock.start + (vt - clock.from) / 1000;
          if (Math.abs(v.currentTime - t) > 0.001) {
            await new Promise((res) => { v.addEventListener("seeked", res, { once: true }); v.currentTime = t; setTimeout(res, 1500); });
          }
          v.dispatchEvent(new Event("timeupdate"));
        }
      }
    }, { vt: this.vt, x, y, visible, ring, clock });
    for (const h of this.hooks) await h(this);
    await this.page.screenshot({ path: path.join(this.dir, `${String(this.n).padStart(5, "0")}.jpg`), quality: 94, type: "jpeg" });
    this.n++;
    this.vt += 1000 / FPS;
  }

  frames(ms) { return Math.max(1, Math.round((ms / 1000) * FPS)); }

  async hold(ms) { for (let i = this.frames(ms); i > 0; i--) await this.frame(); }

  /** Run `fn(t)` for t from 0 to 1 over `ms`, one call per frame, then take that frame. */
  async tween(ms, fn, curve = ease) {
    const k = this.frames(ms);
    for (let i = 1; i <= k; i++) { await fn(curve(i / k)); await this.frame(); }
  }

  async box(selector) {
    const el = this.page.locator(selector).first();
    await el.waitFor({ state: "visible", timeout: 30000 });
    return el.boundingBox();
  }

  async moveTo(target, ms = 700) {
    let to = target;
    if (typeof target === "string") { const b = await this.box(target); to = { x: b.x + b.width / 2, y: b.y + b.height / 2 }; }
    else if (typeof target?.boundingBox === "function") { const b = await target.boundingBox(); to = { x: b.x + b.width / 2, y: b.y + b.height / 2 }; }
    const from = { ...this.cursor };
    this.cursor.visible = true;
    // a gentle arc, like a hand moving a mouse
    const dx = to.x - from.x, dy = to.y - from.y, bend = Math.min(60, Math.hypot(dx, dy) * 0.12);
    await this.tween(ms, async (t) => {
      const arc = Math.sin(Math.PI * t) * bend;
      this.cursor.x = from.x + dx * t - (dy / (Math.hypot(dx, dy) || 1)) * arc;
      this.cursor.y = from.y + dy * t + (dx / (Math.hypot(dx, dy) || 1)) * arc * 0.3;
      await this.page.mouse.move(this.cursor.x, this.cursor.y);
    });
  }

  async click(target, { moveMs = 700, after = 250 } = {}) {
    if (target) await this.moveTo(target, moveMs);
    await this.hold(120);
    this.clickAt = this.vt;
    await this.page.mouse.down();
    await this.frame();
    await this.page.mouse.up();
    await this.hold(after);
  }

  /** Type like a person: a steady rhythm with small pauses after spaces and commas. */
  async type(text, msPerChar = 55) {
    for (const ch of text) {
      await this.page.keyboard.type(ch);
      const pause = msPerChar * (ch === " " ? 1.5 : ch === "," ? 2.2 : 0.8 + 0.4 * ((ch.charCodeAt(0) * 7) % 5) / 5);
      await this.hold(pause);
    }
  }

  async scrollY() { return this.page.evaluate(() => window.scrollY); }

  async scrollTo(y, ms = 1600, curve = ease) {
    const from = await this.scrollY();
    const max = await this.page.evaluate(() => document.documentElement.scrollHeight - innerHeight);
    const to = Math.max(0, Math.min(max, typeof y === "string" ? await this.page.evaluate((s) => {
      const el = document.querySelector(s); return el ? el.getBoundingClientRect().top + scrollY - 90 : scrollY;
    }, y) : y));
    await this.tween(ms, async (t) => { await this.page.evaluate((v) => window.scrollTo(0, v), from + (to - from) * t); }, curve);
  }

  /** Let the page run on its own clock (for long real-time waits). */
  async release() { await this.page.evaluate(() => window.__lv?.release()); }

  /**
   * Timelapse: while `until()` is false, sample one frame every `everyMs` of real time.
   * Animations stay on the virtual clock, so spinners stay smooth while the real work races by.
   */
  async timelapse(until, everyMs = 400, maxMs = 15 * 60 * 1000) {
    const start = Date.now();
    let last = 0;
    while (!(await until()) && Date.now() - start < maxMs) {
      const wait = everyMs - (Date.now() - last);
      if (wait > 0) await new Promise((r) => setTimeout(r, wait));
      last = Date.now();
      await this.frame();
    }
    return (Date.now() - start) / 1000;
  }

  async close() {
    fs.writeFileSync(path.join(this.dir, "marks.json"), JSON.stringify({ frames: this.n, fps: FPS, marks: this.marks, ...(this.meta ?? {}) }, null, 2));
    await this.browser.close();
  }
}

/** Turn a capture folder into a high-quality 60 fps clip for the composition. */
export function encode(name) {
  const out = path.join("public", `${name}.mp4`);
  fs.mkdirSync("public", { recursive: true });
  execFileSync("ffmpeg", ["-y", "-loglevel", "error", "-framerate", String(FPS), "-i", path.join("captures", name, "%05d.jpg"), "-vf", "crop=trunc(iw/2)*2:trunc(ih/2)*2",
    "-c:v", "libx264", "-preset", "slow", "-crf", "14", "-pix_fmt", "yuv420p", "-movflags", "+faststart", out]);
  return out;
}
