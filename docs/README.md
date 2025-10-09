# GitHub Pages deployment for the GSEA Enrichment Gallery

This folder now hosts the **full PNG-based** enrichment gallery directly. `create_interactive_gallery.py` writes the optimized HTML into this directory so GitHub Pages can serve it without any extra loader or JavaScript glue. The generated file is ~3.9 MB uncompressed (far below the 100 MB Pages limit), making it safe to publish as-is.

## Files

| File | Purpose |
| --- | --- |
| `index.html` | The complete PNG-embedded gallery served on GitHub Pages. Regenerated automatically by `create_interactive_gallery.py`. |
| `enrichment_plots_gallery_interactive_png.html` | Same gallery HTML kept alongside `index.html` for archival/download purposes. |
| `assets/enrichment-gallery.html.gz` | Optional gzipped copy of the gallery (still produced for offline sharing or scripted downloads). |
| `annotated_enplots_png/` | Published PNG assets copied from the generator (optional for direct download; the gallery inlines Base64 PNGs). |
| `app.js`, `config.json`, `styles.css` | Legacy loader assets kept around in case you need the streaming viewer again. They are no longer referenced by `index.html`.

## Deployment workflow

1. **Regenerate the galleries**
   - Activate the `mus_musculus` conda environment (or any env with CairoSVG installed).
   - Run `python create_interactive_gallery.py` from the repo root. This rebuilds:
     - `enrichment_plots_gallery_interactive.html` (SVG-rich local version)
     - `enrichment_plots_gallery_interactive_png.html` (PNG-embedded web version)
     - `annotated_enplots_png/` and `docs/annotated_enplots_png/` for raw PNG access
     - `docs/index.html` and `docs/enrichment_plots_gallery_interactive_png.html` (Pages-ready copies)
2. **Optional: refresh the compressed payload**
   - `gzip -c docs/index.html > docs/assets/enrichment-gallery.html.gz`
3. **Deploy to GitHub Pages**
   - Push the updated `docs/` folder to the branch that backs GitHub Pages (e.g., `main` with the `/docs` content root).
   - Ensure Pages is enabled in **Settings → Pages** for that branch + `/docs` folder.
4. **Share the Pages URL**
   - Visitors now load the lightweight PNG gallery directly—no streaming or decompression step required. The gzip file remains available for offline archival if desired.

## Device compatibility

- Modern Chromium (Chrome, Edge), WebKit (Safari), and Gecko (Firefox) browsers on desktop/mobile comfortably render the inline PNG gallery.
- The HTML is ~3.9 MB and loads quickly over conference Wi‑Fi. Each image is still encoded inline, so no additional requests are required.
- Keep the legacy viewer assets if you ever want to switch back to streaming from a release asset.
