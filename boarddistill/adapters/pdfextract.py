"""PDF -> text extraction (pypdf) for SR-letter attachments and manual PDFs."""

from __future__ import annotations

import io
import re

from pypdf import PdfReader

_WS = re.compile(r"\s+")


def pdf_to_text(data: bytes) -> str:
    reader = PdfReader(io.BytesIO(data))
    return _WS.sub(" ", " ".join(page.extract_text() for page in reader.pages)).strip()
