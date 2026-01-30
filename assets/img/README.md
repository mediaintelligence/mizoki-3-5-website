# Meta ReLU LinkedIn Image Kit

Complete image assets for the "Unlocking Meta's Ad Algorithm With the ReLU Lens" LinkedIn content.

---

## Quick Start

### Converting SVG to PNG

The images are in SVG format for maximum quality and scalability. To convert to PNG:

**Option 1: Browser Method (Easiest)**
1. Open any `.svg` file in Chrome/Firefox
2. Right-click → "Save image as..." → Save as PNG
3. Or use browser print/screenshot at desired resolution

**Option 2: Command Line (macOS)**
```bash
# Install rsvg-convert if needed
brew install librsvg

# Convert single file
rsvg-convert -w 1200 -h 675 01_relu_gate.svg -o 01_relu_gate.png

# Convert all article images
for f in relu-article/*.svg; do
  rsvg-convert -w 1200 -h 675 "$f" -o "${f%.svg}.png"
done

# Convert carousel (1080x1350)
for f in relu-carousel/*.svg; do
  rsvg-convert -w 1080 -h 1350 "$f" -o "${f%.svg}.png"
done
```

**Option 3: Online Tools**
- [CloudConvert](https://cloudconvert.com/svg-to-png)
- [Convertio](https://convertio.co/svg-png/)

---

## 1. LinkedIn Article Images

**Location:** `relu-article/`

| File | Dimensions | Use Case |
|------|------------|----------|
| `01_relu_gate.svg` | 1200×675 | Inline after hook |
| `02_nonlinear_activation_curve.svg` | 1200×675 | When explaining "it jumps" |
| `03_learning_50_events.svg` | 1200×675 | Learning phase explanation |
| `04_compounding_feedback_loop.svg` | 1200×675 | Flywheel/momentum section |
| `05_budget_dilution_vs_concentration.svg` | 1200×675 | "Go deep before wide" |

### For 1920×1080 (Article Cover)
Scale the SVGs to 1920×1080 using the conversion methods above, or open in browser and screenshot at higher resolution.

---

## 2. LinkedIn Carousel Slides

**Location:** `relu-carousel/`
**Format:** 1080×1350 (4:5 ratio - optimal for LinkedIn mobile)

| Slide | File | Content |
|-------|------|---------|
| 1 | `slide_01_cover.svg` | Title card - "Unlocking Meta's Algorithm With the ReLU Lens" |
| 2 | `slide_02_problem.svg` | The problem - flatline then breakout |
| 3 | `slide_03_relu_explained.svg` | What is ReLU? The gate concept |
| 4 | `slide_04_50_events.svg` | The magic number: 50 events/week |
| 5 | `slide_05_consolidate.svg` | Budget dilution vs concentration |
| 6 | `slide_06_flywheel.svg` | The compounding feedback loop |
| 7 | `slide_07_checklist.svg` | The 6-move ReLU Playbook |
| 8 | `slide_08_cta.svg` | Closing quote + CTA |

---

## Captions for LinkedIn Article

Copy/paste these when inserting images:

### Figure 1 — ReLU Gate
> The "ReLU-style gate": weak signals get filtered; strong signals get amplified.

### Figure 2 — Nonlinear Activation Curve
> Nonlinear delivery: results often jump once you cross a learning threshold.

### Figure 3 — Learning Phase (~50 Events)
> Learning phase math: aim for ~50 optimization events per ad set per week to stabilize.

### Figure 4 — Compounding Feedback Loop
> Feedback loop: better signals → better delivery → more signals (compounding).

### Figure 5 — Budget Dilution vs Concentration
> Budget dilution vs concentration: fewer ad sets = faster learning.

---

## Alt Text (SEO + Accessibility)

Use these for image alt attributes:

### Figure 1
```
ReLU gate concept for Meta Ads optimization—weak engagement signals filtered, strong signals amplified.
```

### Figure 2
```
Nonlinear activation curve showing threshold effect in Meta Ads learning and performance marketing.
```

### Figure 3
```
Learning phase target of 50 optimization events per week per ad set for Facebook and Instagram ads.
```

### Figure 4
```
Compounding feedback loop in Meta ad auctions—more conversion signals improve delivery and ROAS.
```

### Figure 5
```
Comparison of budget dilution vs budget concentration in Meta media buying and campaign structure.
```

---

## Where to Insert Each Image in the Article

Use them exactly like this:

| Image | Insert After... |
|-------|-----------------|
| **Figure 1** (ReLU Gate) | Hook + "you're invisible below threshold" |
| **Figure 2** (Nonlinear Curve) | "it's not linear… it jumps" explanation |
| **Figure 3** (50 Events) | Learning phase / stabilization section |
| **Figure 4** (Flywheel) | Momentum / compounding effect section |
| **Figure 5** (Dilution vs Concentration) | "go deep before wide" strategy |

---

## LinkedIn Best Practices

### For Articles
- **Cover image:** Use 1920×1080 version of Figure 1 or create a custom cover
- **Inline images:** 1200×675 works perfectly
- **Add captions** below each image for context

### For Carousel Posts
- Upload all 8 slides as a document/carousel
- **Pro tip:** First slide is the "thumbnail" - make it compelling
- Add a hook in your post text, link to full article

### Posting Strategy
1. **Post the carousel first** (gets more reach)
2. **Comment with article link** (drives traffic)
3. Or post article with images inline, share carousel separately

---

## File Structure

```
assets/img/
├── README.md (this file)
├── relu-article/
│   ├── 01_relu_gate.svg
│   ├── 02_nonlinear_activation_curve.svg
│   ├── 03_learning_50_events.svg
│   ├── 04_compounding_feedback_loop.svg
│   └── 05_budget_dilution_vs_concentration.svg
└── relu-carousel/
    ├── slide_01_cover.svg
    ├── slide_02_problem.svg
    ├── slide_03_relu_explained.svg
    ├── slide_04_50_events.svg
    ├── slide_05_consolidate.svg
    ├── slide_06_flywheel.svg
    ├── slide_07_checklist.svg
    └── slide_08_cta.svg
```

---

## Customization

The SVGs are fully editable. To customize:

1. Open in any vector editor (Figma, Illustrator, Inkscape)
2. Or edit the SVG XML directly - colors are CSS variables
3. Brand colors used:
   - Cyan: `#00d4ff`
   - Blue: `#4f8fff`
   - Purple: `#a855f7`
   - Green: `#10b981`
   - Orange: `#f59e0b`
   - Red: `#ef4444`
   - Background: `#0a0a0f` to `#12121a`

---

## Credits

Created for MIZ OKI 3.5
Part of the "ReLU Lens" media buying framework content series.
