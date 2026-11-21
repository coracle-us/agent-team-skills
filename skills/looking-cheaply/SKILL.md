---
name: looking-cheaply
description: Use when about to take screenshots, view rendered images, or visually check UI, charts or video frames, especially more than two or three of them or repeatedly.
---

# Looking cheaply

**Every image you view stays in your context and is re-read on every later turn.** Twelve full-size screenshots per
check, three checks, is 36 images riding along for the rest of the session.

Why: a 12-day agent-team build had more than 6,500 screenshots in context.

## The recipe

1. **Capture** all states to a fresh folder per run (`shots/run1/`). Confirm the count and that none are empty.
2. **Diff first** when you have a previous run or a baseline: compare pixels and list which states changed at all.
   Unchanged states need no look.
   `magick compare -metric AE a.png b.png null: 2>&1` (prints the number of differing pixels)
3. **One contact sheet** of the states to check, labelled, tiles about half size:
   `magick montage -label '%t' shots/run1/*.png -tile 4x -geometry 720x450+4+4 sheet.png`
   (or a few lines of Pillow). View the sheet: one image.
4. **Zoom only where it's needed**: for a tile that looks off, or a change too small to judge at half size, view a crop
   of that state at full size, not the whole screenshot.
5. **Re-checks** repeat steps 1, 2 and 4 against the previous run: view only what changed.
6. For many checks, or a long session, hand the looking to a short-lived reviewer agent: it views the images and
   reports in words, and its context ends with it.

## Common mistakes

| Thought | Reality |
|---|---|
| "A contact sheet will miss 2–4 px shifts" | The pixel diff finds those. Then zoom on that state only |
| "A spacing change can break any screen, so view all 12" | The diff tells you which screens changed |
| "I'll view each one in parallel calls" | Parallel or not, all 12 stay in context |
