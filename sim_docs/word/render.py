"""Word document page rendering.

Extracts pages as images via LibreOffice + PyMuPDF.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

from sim_docs.core.soffice import run_soffice


def render_page(
    docx_path: str | Path,
    page: int = 1,
    output: str | Path | None = None,
) -> bytes | str:
    """Render a specific page of a Word document to an image.

    Args:
        docx_path: Path to .docx or .dotm file.
        page: Page number (1-indexed).
        output: Output image path. If None, returns bytes.

    Returns:
        PNG bytes if output is None, otherwise output path.
    """
    resolved_path = str(Path(docx_path).expanduser().resolve())
    output_path = str(output) if output else None

    with tempfile.TemporaryDirectory() as tmpdir:
        pdf_path = convert_to_pdf(resolved_path, tmpdir)

        try:
            import fitz
        except ImportError:
            raise ImportError(
                "PyMuPDF (fitz) is required for page rendering. "
                "Install it with: pip install PyMuPDF"
            )

        doc = fitz.open(pdf_path)

        if page < 1 or page > len(doc):
            raise ValueError(f"Page {page} out of bounds. Document has {len(doc)} pages.")

        page_obj = doc.load_page(page - 1)
        pix = page_obj.get_pixmap(dpi=150)

        if output_path:
            pix.save(output_path)
            return output_path
        else:
            return pix.tobytes("png")


def convert_to_pdf(docx_path: str, outdir: str) -> str:
    """Convert .docx/.dotm to .pdf using LibreOffice."""
    import subprocess

    run_soffice(
        ["--headless", "--convert-to", "pdf", "--outdir", outdir, docx_path],
        check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )
    return str(Path(outdir) / (Path(docx_path).stem + ".pdf"))