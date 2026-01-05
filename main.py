"""
simple text extraction API using FastAPI
"""

from fastapi import FastAPI, UploadFile, File, HTTPException
from pypdf import PdfReader
from docx import Document
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', filename='app.log', filemode='a')

app = FastAPI(title="File Text Extraction API")

@app.post("/extract-text")
async def extract_text(file: UploadFile = File(...)):
    try:
        extracted_text = ""

        if file.filename.lower().endswith(".pdf"):
            logging.info(f"Processing PDF file: {file.filename}")
            reader = PdfReader(file.file)
            extracted_text = "\n".join(
                page.extract_text() or "" for page in reader.pages
            )
            logging.info(f"Extracted text from PDF file: {file.filename}")
            logging.info(f"Extracted text content: {extracted_text[:]}...")  # Log first 500 characters

        elif file.filename.lower().endswith(".docx"):
            logging.info(f"Processing DOCX file: {file.filename}")
            doc = Document(file.file)
            extracted_text = "\n".join(p.text for p in doc.paragraphs)
            logging.info(f"Extracted text from DOCX file: {file.filename}")
            logging.info(f"Extracted text content: {extracted_text[:]}...")  # Log first 500 characters

        else:
            logging.error(f"Unsupported file type: {file.filename}")
            raise HTTPException(
                status_code=400,
                detail="Unsupported file type. Only PDF and DOCX are allowed."
            )
            
        
        return {
            "filename": file.filename,
            "text": extracted_text
        }
        

    except Exception as e:
        logging.error(f"Error processing file {file.filename}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Text extraction failed: {str(e)}"
        )
