"""
using fastapi and postman and swagger ui
"""
import os
from fastapi import FastAPI, UploadFile, File, HTTPException
from pypdf import PdfReader
from docx import Document
from dotenv import load_dotenv

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from gen_ai_hub.proxy.langchain.openai import ChatOpenAI

# =========================================================
# ENV
# =========================================================

load_dotenv()
AICORE_CLIENT_ID = os.getenv("AICORE_CLIENT_ID")
AICORE_CLIENT_SECRET = os.getenv("AICORE_CLIENT_SECRET")
AICORE_AUTH_URL = os.getenv("AICORE_AUTH_URL")
AICORE_BASE_URL = os.getenv("AICORE_BASE_URL")
LLM_DEPLOYMENT_ID = os.getenv("LLM_DEPLOYMENT_ID")

if not LLM_DEPLOYMENT_ID:
    raise RuntimeError("LLM_DEPLOYMENT_ID is not set in environment variables")

# =========================================================
# FASTAPI INIT
# =========================================================

app = FastAPI(title="SAP CPI iFlow HITL Prompt Generator")

# =========================================================
# LLM SETUP (SAP AI Core)
# =========================================================

llm = ChatOpenAI(
    deployment_id=LLM_DEPLOYMENT_ID,
    temperature=0
)

# =========================================================
# PROMPTS
# =========================================================

IFLOW_UNDERSTANDING_PROMPT = ChatPromptTemplate.from_template("""
You are an SAP Integration Suite expert.

Read the following document describing an SAP CPI iFlow.

Your task:
1. Understand the iFlow design intent
2. Extract and normalize the details
3. Do NOT create code
4. Do NOT generate a final execution command

Return a clear, structured explanation covering:
- iFlow name
- Package name
- Sender adapter
- Processing steps in order
- Message mappings (names)
- Receiver adapter and receiver name
- Exception subprocess (if any)

Document:
{document_text}
""")

CANONICAL_IFLOW_PROMPT = ChatPromptTemplate.from_template("""
You are generating a final execution prompt for an automated SAP CPI iFlow creation system.

Based ONLY on the approved design below, generate a concise 2–4 line instruction.

Rules:
- Use imperative form ("create", "update")
- Preserve names exactly
- Do not add explanations
- Do not invent steps
- Output ONLY the final prompt

Approved design:
{approved_design}
""")

# =========================================================
# LLM CHAINS
# =========================================================

def generate_iflow_understanding(document_text: str) -> str:
    chain = IFLOW_UNDERSTANDING_PROMPT | llm | StrOutputParser()
    return chain.invoke({"document_text": document_text})


def generate_canonical_iflow_prompt(approved_design: str) -> str:
    chain = CANONICAL_IFLOW_PROMPT | llm | StrOutputParser()
    return chain.invoke({"approved_design": approved_design})

# =========================================================
# FILE TEXT EXTRACTION
# =========================================================

def extract_text_from_file(file: UploadFile) -> str:
    if file.filename.lower().endswith(".pdf"):
        reader = PdfReader(file.file)
        return "\n".join(page.extract_text() or "" for page in reader.pages)

    elif file.filename.lower().endswith(".docx"):
        doc = Document(file.file)
        return "\n".join(p.text for p in doc.paragraphs)

    else:
        raise HTTPException(
            status_code=400,
            detail="Unsupported file type. Only PDF and DOCX are allowed."
        )

# =========================================================
# API ENDPOINTS
# =========================================================

@app.post("/iflow/understand")
async def understand_iflow(file: UploadFile = File(...)):
    """
    Step 1: Upload document → Extract text → LLM understanding
    """
    document_text = extract_text_from_file(file)
    understanding = generate_iflow_understanding(document_text)

    return {
        "filename": file.filename,
        "iflow_understanding": understanding
    }


@app.post("/iflow/final-prompt")
async def generate_final_prompt(approved_design: str):
    """
    Step 2: Approved design → Final canonical prompt
    """
    final_prompt = generate_canonical_iflow_prompt(approved_design)

    return {
        "final_prompt": final_prompt
    }
