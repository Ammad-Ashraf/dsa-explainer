# Launch video

A scripted, minimal launch video of DSA Explainer: kinetic titles, the real app in a browser frame with smooth
camera moves, a real lesson being made, and a synthesized music bed. Nothing here is recorded by hand.

## How it is made

1. **Capture** (`scenes/*.mjs`, using `rig.mjs`). Headless Chrome opens the running app. Every CSS animation,
   transition and SVG animation is paused and stepped by a virtual clock, one 60 fps frame at a time, so scrolling,
   typing and the cursor are perfectly smooth however slow the machine is. Long waits (making a lesson) are sampled
   as a timelapse. Frames go to `captures/<scene>/`, clips to `public/<scene>.mp4`.
2. **Compose** (`src/`, Remotion). `src/shots.ts` is the edit: which capture frames play, how fast, the captions
   and the camera keyframes. `src/Launch.tsx` lays out the title cards, the browser window and the audio.
3. **Music** (`music.py`): soft pads, a plucked arpeggio and a gentle pulse, synthesized with numpy, so there is no
   licence to worry about. It ducks under the lesson's own narration.

## Re-make it

With the app running on http://127.0.0.1:8000 (and a language-model key for the Studio scene):

```bash
npm install
node scenes/home.mjs
node scenes/studio.mjs      # makes a real lesson (uses the language model)
node scenes/lesson.mjs      # needs captures/lesson.json from the Studio scene
node scenes/library.mjs
node scenes/settings.mjs
node grab-art.mjs           # the mascot images
cp ../outputs/<lesson id>/lesson_v1.mp4 public/bst-lesson.mp4
python music.py 125 public/music.wav
node collect.mjs
npx remotion studio src/index.ts         # preview and tweak
npm run render                           # -> out/dsa-explainer-launch.mp4
```

Capture frame numbers in `src/shots.ts` come from `captures/<scene>/marks.json`; adjust them if you re-capture.
