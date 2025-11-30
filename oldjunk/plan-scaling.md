# Slide Deck Scaling Fix: Fixed Resolution + Transform

## Problem

The presentation mixes viewport units (`90vw/90vh` for slides) with fixed pixels (`24px`, `36px`, etc.) causing inconsistent scaling at different window sizes.

## Solution

Design at fixed 1920x1080 resolution, let impress.js scale everything via CSS transforms. This is how PowerPoint/Keynote work.

## Files to Modify

1. `index.html` - Configure impress.js canvas dimensions
2. `styles.css` - Convert viewport units to fixed pixels

## Changes

### 1. index.html (line 21)

```html
<!-- Current -->
<div id="impress" data-transition-duration="50" data-min-scale="1">

<!-- New -->
<div id="impress"
     data-transition-duration="50"
     data-width="1920"
     data-height="1080"
     data-min-scale="0"
     data-max-scale="3">
```

### 2. styles.css

#### CSS Variables (lines 5-17)

| Variable | Current | New |
|----------|---------|-----|
| `--title-font-size` | `5vh` | `54px` |
| `--section-font-size` | `5vw` | `96px` |
| `--body-large-font-size` | `3vh` | `32px` |
| `--code-fullscreen-font-size` | `1.8vh` | `19px` |
| `--title-slide-h1-font-size` | `7vw` | `134px` |
| `--title-slide-subtitle-font-size` | `4vw` | `77px` |
| `--title-slide-link-font-size` | `3vw` | `58px` |

Keep unchanged: `--subtitle-font-size: 36px`, `--body-font-size: 24px`, `--label-font-size: 20px`, `--code-font-size: 18px`, `--code-small-font-size: 14px`

#### Slide Dimensions (lines 51-52)

```css
.step {
    width: 1728px;    /* 1920 * 0.9 */
    height: 972px;    /* 1080 * 0.9 */
}
```

#### Other Viewport Units

| Selector | Property | Current | New |
|----------|----------|---------|-----|
| `.slide-section .section-image` (103) | `max-height` | `50vh` | `540px` |
| `.slide-section .section-image` (104) | `max-width` | `60vw` | `1152px` |
| `.slide-epoch .epoch-content` (398) | `padding-right` | `10vw` | `192px` |
| `.side-by-side figure` (419) | `width` | `35vw` | `672px` |
| `.side-by-side .img-container` (423-424) | `width`, `height` | `35vw` | `672px` |
| `.split-panel img` (596) | `max-height` | `50vh` | `540px` |
| `.step.slide-1000x` (809-810) | `width`, `height` | `100vw`, `100vh` | `1920px`, `1080px` |

#### Delete Mobile Media Query (lines 840-849)

Remove entirely - impress.js transform scaling handles all viewport sizes.

## How It Works

impress.js `computeWindowScale()` calculates `min(window.height/1080, window.width/1920)` and applies a CSS transform to scale the entire canvas. At different aspect ratios, this creates automatic letterboxing (black bars).

## Testing

After implementation, verify at:
- 1920x1080 (native - should be pixel-perfect)
- 1366x768 (smaller 16:9 - scales down)
- 2560x1440 (larger - scales up)
- 1024x768 (4:3 - horizontal letterboxing)
- Mobile portrait (scales way down, letterboxed)
