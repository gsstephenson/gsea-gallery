# GitHub Pages bootstrap for the GSEA Enrichment Gallery

This folder contains a lightweight viewer that streams the large enrichment gallery HTML from a GitHub Release asset. The heavy file is compressed (`.html.gz`) to stay well below GitHub's 100&nbsp;MB per-file limit, while the viewer remains small enough to deploy on GitHub Pages.

## Files

| File | Purpose |
| --- | --- |
| `index.html` | Presentation-friendly bootstrap page with loader UI. |
| `styles.css` | Minimal responsive styling. |
| `app.js` | Loads configuration, fetches the compressed gallery, decompresses it in the browser via [fflate](https://github.com/101arrowz/fflate), and streams it into the iframe. |
| `config.json` | Holds the release asset URL and friendly download name. Update this before publishing. |

## Deployment workflow

1. **Compress the gallery**
   ```bash
   gzip -kc index.html > enrichment-gallery.html.gz
   ```
2. **Stage the compressed asset**
   - Copy `enrichment-gallery.html.gz` into `docs/assets/` (already set up for you).
3. **Configure the viewer**
   - `config.json` points at `assets/enrichment-gallery.html.gz` so the file is served from the same origin, avoiding CORS issues.
4. **Deploy to GitHub Pages**
   - Place the contents of `docs/` in the branch that backs GitHub Pages (e.g., `main` with `/docs`), excluding the 350&nbsp;MB source HTML.
   - Enable Pages in **Settings → Pages**, selecting the branch and `/docs` folder.
5. **Share the Pages URL**
   - During the presentation, users load the Pages site. The viewer streams the compressed gallery, decompresses it client-side, and renders it in an iframe. A direct download link is also provided for offline access.

## Device compatibility

- Modern Chromium (Chrome, Edge), WebKit (Safari), and Gecko (Firefox) browsers on desktop/mobile fully support the streaming + `fflate` decompression approach.
- Memory use is roughly the decompressed size (~350&nbsp;MB). For mobile devices, keep unnecessary tabs closed to free RAM.
- The viewer falls back gracefully; if the fetch fails, attendees can tap **Retry** or use the direct **Download** link.
