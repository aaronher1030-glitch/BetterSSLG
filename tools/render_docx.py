"""Render helper for the house-format workflow.

    python -X utf8 tools/render_docx.py <file.docx>              # -> <file>.pdf beside it
    python -X utf8 tools/render_docx.py <file.pdf> --preview DIR  # -> page PNGs for eyeballing

Conversion uses the local Word through COM; page images use PyMuPDF. Nothing is uploaded and
no file other than the stated outputs is written.
"""
import argparse
import sys
from pathlib import Path

PDF_EXPORT = 17
DEFAULT_DPI = 110


def docx_to_pdf(docx_path):
    import win32com.client
    src = Path(docx_path).resolve()
    out = src.with_suffix(".pdf")
    if out.exists():
        out.unlink()
    word = win32com.client.Dispatch("Word.Application")
    word.Visible = False
    try:
        doc = word.Documents.Open(str(src), ReadOnly=True)
        doc.ExportAsFixedFormat(str(out), PDF_EXPORT)
        doc.Close(False)
    finally:
        try:
            word.Quit()
        except Exception:
            pass  # Word sometimes drops the RPC after export; the PDF is already written
    if not out.exists():
        raise RuntimeError(f"Word produced no PDF for {src}")
    return out


def pdf_to_png(pdf_path, preview_dir, dpi=DEFAULT_DPI):
    import pymupdf
    pdf_path, preview_dir = Path(pdf_path), Path(preview_dir)
    preview_dir.mkdir(parents=True, exist_ok=True)
    written = []
    with pymupdf.open(str(pdf_path)) as doc:
        zoom = dpi / 72.0
        for i, page in enumerate(doc, start=1):
            pix = page.get_pixmap(matrix=pymupdf.Matrix(zoom, zoom))
            target = preview_dir / f"{pdf_path.stem}-page-{i}.png"
            pix.save(str(target))
            written.append(target)
    return written


def main(argv=None):
    ap = argparse.ArgumentParser(description="Render SSLG documents for format review.")
    ap.add_argument("path")
    ap.add_argument("--preview", metavar="DIR", help="write page PNGs into DIR")
    ap.add_argument("--dpi", type=int, default=DEFAULT_DPI)
    args = ap.parse_args(argv)

    path = Path(args.path)
    if not path.exists():
        print(f"not found: {path}")
        return 1
    if path.suffix.lower() == ".docx" and not args.preview:
        print("PDF:", docx_to_pdf(path))
    elif args.preview:
        pdf = path if path.suffix.lower() == ".pdf" else docx_to_pdf(path)
        for png in pdf_to_png(pdf, args.preview, args.dpi):
            print("PNG:", png)
    else:
        print("give --preview DIR to render pages, or pass a .docx to convert")
    return 0


if __name__ == "__main__":
    sys.exit(main())
