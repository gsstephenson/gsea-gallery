# QR Codes for GSEA Gallery

These QR codes link directly to the published PNG-based gallery hosted on GitHub Pages:

- `gsea-gallery-qr.svg`
- `gsea-gallery-qr.png`

Each code points to <https://gsstephenson.github.io/gsea-gallery/>. Regenerate with:

```bash
conda run -n mus_musculus python -c "import segno, pathlib; out=pathlib.Path('qr_codes'); out.mkdir(exist_ok=True); url='https://gsstephenson.github.io/gsea-gallery/'; qr=segno.make(url, micro=False, error='h'); qr.save(out/'gsea-gallery-qr.svg', scale=10, border=2); qr.save(out/'gsea-gallery-qr.png', scale=10, border=2)"
```
