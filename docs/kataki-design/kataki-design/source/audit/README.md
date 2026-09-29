# Contrast audit

Checks every line of text on every board against WCAG 2.2 AA (4.5:1, or 3:1 for 24px+ / 18.66px+ bold), using the real pixels behind it — gradients, photographs and translucent panels included.

1. `preview2.js audit <boards…>` renders each board in headless Chromium with the vendored fonts, records every text run (colour, opacity, size, weight, rectangles, whether it is covered by a modal or inside an `inert`/`aria-hidden` region), then hides all text and screenshots what is behind it.
2. `audit.py <boards…>` composites each run's colour over those pixels and takes the 10th-percentile ratio. Text covered by an overlay or in an inert region is counted and skipped (WCAG 1.4.3 exempts inactive UI).
3. `run_audit.sh` regenerates the boards and runs both. It also writes the totals that `Sky2-Access` displays.

Paths at the top of `preview2.js` (font folder, art uploads) point at the design sandbox; change them to `../../assets/` to run it here. To use it against the real app, point the renderer at the app's routes instead of `.dc.html` boards — the audit logic does not care where the page comes from.

Result for v2.1: **2,354 text runs across 43 boards, 0 below AA** (baseline before the pass: 411 failures in 2,120).
