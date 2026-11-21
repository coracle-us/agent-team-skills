# Scenario: looking-cheaply

Prompt: `looking-cheaply.prompt.md`.
Passes when: one contact sheet (or a pixel diff, then zoom on what changed), or a short-lived reviewer; not 12
separate full-size screenshots per check.

## Without
- Fails: "12 Read calls, one image per call... I wouldn't tile them into a contact sheet, because... I'd miss
  2-4px spacing regressions."
- Re-checks: "I'd still view all 12 again." 12 full-size images per pass, every pass.

## With
- Pass. Capture, verify without viewing, pixel-diff, one labelled contact sheet, 0-3 full-size crops: "roughly 1-4
  images instead of 12". Re-checks diff against the previous run and view only changed states; offers a short-lived
  reviewer when checks pile up.
