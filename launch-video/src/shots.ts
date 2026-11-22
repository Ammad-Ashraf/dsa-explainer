// The edit: which parts of each capture play, how fast, what the caption says and where the camera goes.
// All frame numbers are capture frames (60 fps) from captures/<name>/marks.json.
import type { Cam, Seg } from "./kit";

export type Shot = {
  src: string;
  segs: Seg[];
  captions: { at: number; text: string; hl?: string[] }[];
  cam?: Cam[];
  pills?: { at: number; until: number; text: string }[];
  /** lesson narration to hear: from capture frame `frame`, `frames` long, from `start` seconds into the lesson */
  audio?: { frame: number; frames: number; start: number }[];
};

export const INTRO = [
  { text: "Algorithms are hard to picture.", dur: 150, hl: [] as string[], size: 96 },
  { text: "So we made them move.", dur: 135, hl: ["move"], size: 96 },
];

export const CLOSING = [
  { kind: "card", text: "Every step checked\nbefore anything is drawn.", dur: 170, hl: ["checked"], size: 88 },
  { kind: "stats", dur: 240 },
  { kind: "outro", dur: 330 },
] as { kind: string; text?: string; dur: number; hl?: string[]; size?: number }[];

const SPED = "Sped up";

export const SHOTS: Shot[] = [
  {
    src: "home.mp4",
    segs: [{ from: 0, to: 318 }, { from: 318, to: 1446, rate: 1.5 }],
    captions: [
      { at: 0, text: "Type a topic. Get a narrated lesson.", hl: ["narrated"] },
      { at: 990, text: "Six steps. One honest video.", hl: ["honest"] },
    ],
  },
  {
    src: "studio.mp4",
    segs: [{ from: 20, to: 653 }, { from: 653, to: 1558, rate: 3 }, { from: 1558, to: 1708 }],
    captions: [
      { at: 20, text: "Ask for anything, with your own data.", hl: ["anything"] },
      { at: 653, text: "Each step runs on a real tree. Wrong plans go back.", hl: ["real"] },
    ],
    cam: [
      { f: 60, s: 1 }, { f: 120, s: 1.55, x: 700, y: 396 }, { f: 300, s: 1.55, x: 760, y: 396 },
      { f: 345, s: 1.28, x: 720, y: 650 }, { f: 470, s: 1.28, x: 720, y: 690 }, { f: 545, s: 1 },
      { f: 720, s: 1 }, { f: 800, s: 1.42, x: 300, y: 430 }, { f: 1450, s: 1.42, x: 300, y: 430 }, { f: 1540, s: 1 },
    ],
    pills: [{ at: 680, until: 1550, text: `⏩ ${SPED}` }],
  },
  {
    src: "lesson.mp4",
    segs: [{ from: 30, to: 1266 }],
    captions: [
      { at: 30, text: "Narrated, and drawn only from checked states.", hl: ["checked"] },
      { at: 600, text: "Delete 3: its successor, 6, takes its place.", hl: ["6"] },
    ],
    cam: [
      { f: 80, s: 1 }, { f: 150, s: 1.2, x: 710, y: 520 }, { f: 545, s: 1.2, x: 710, y: 520 }, { f: 600, s: 1 },
      { f: 660, s: 1 }, { f: 760, s: 1.55, x: 1045, y: 590 }, { f: 1150, s: 1.55, x: 1045, y: 590 }, { f: 1240, s: 1 },
    ],
    audio: [{ frame: 111, frames: 468, start: 41.7 }, { frame: 636, frames: 625, start: 71.16 }],
  },
  {
    src: "lesson.mp4",
    segs: [{ from: 1266, to: 1574 }],
    captions: [{ at: 1266, text: "Quiz answers are computed, not guessed.", hl: ["computed"] }],
    cam: [{ f: 1340, s: 1 }, { f: 1420, s: 1.3, x: 710, y: 360 }, { f: 1540, s: 1.3, x: 710, y: 370 }, { f: 1574, s: 1.15, x: 710, y: 370 }],
  },
  {
    src: "lesson.mp4",
    segs: [{ from: 1574, to: 2130, rate: 1.3 }],
    captions: [{ at: 1574, text: "See what was checked, and what was sent back.", hl: ["checked"] }],
  },
  {
    src: "lesson.mp4",
    segs: [{ from: 2130, to: 2446 }, { from: 2446, to: 3237, rate: 4 }, { from: 3237, to: 3330 }],
    captions: [{ at: 2130, text: "Change any part, in plain words.", hl: ["plain"] }],
    pills: [{ at: 2470, until: 3230, text: `⏩ ${SPED}` }],
  },
  {
    src: "library.mp4",
    segs: [{ from: 0, to: 685, rate: 1.2 }],
    captions: [{ at: 0, text: "22 lessons ready to play. No key needed.", hl: ["22"] }],
  },
  {
    src: "settings.mp4",
    segs: [{ from: 0, to: 644, rate: 1.15 }],
    captions: [
      { at: 0, text: "Bring your own model, or run one locally.", hl: ["locally"] },
      { at: 330, text: "The voice lives on your laptop.", hl: ["laptop"] },
    ],
  },
];
