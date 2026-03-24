"""
File Upload API Route
POST /api/upload/pdf — Extract text from a PDF file
"""

import io
from fastapi import APIRouter, UploadFile, File, HTTPException

router = APIRouter(prefix="/api/upload", tags=["Upload"])


@router.post("/pdf")
async def upload_pdf(file: UploadFile = File(...)):
    """Upload a PDF and extract text content using PyPDF2."""
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    try:
        contents = await file.read()
        pdf_reader = None
        text = ""

        # Try PyPDF2 first
        try:
            from pypdf import PdfReader
            pdf_reader = PdfReader(io.BytesIO(contents))
            for page in pdf_reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
        except ImportError:
            try:
                from PyPDF2 import PdfReader as PdfReader2
                pdf_reader = PdfReader2(io.BytesIO(contents))
                for page in pdf_reader.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
            except ImportError:
                raise HTTPException(
                    status_code=500,
                    detail="No PDF library available. Install pypdf or PyPDF2."
                )

        if not text.strip():
            raise HTTPException(
                status_code=400,
                detail="Could not extract text from PDF. The file may be image-based."
            )

        return {"text": text.strip(), "pages": len(pdf_reader.pages) if pdf_reader else 0}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading PDF: {str(e)}")
