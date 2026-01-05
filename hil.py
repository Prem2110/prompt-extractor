import os
import sys
from dotenv import load_dotenv
from pypdf import PdfReader
from docx import Document

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from gen_ai_hub.proxy.langchain.openai import ChatOpenAI

# =========================================================
# ENV
# =========================================================

load_dotenv()

LLM_DEPLOYMENT_ID = os.getenv("LLM_DEPLOYMENT_ID")

if not LLM_DEPLOYMENT_ID:
    print("❌ ERROR: LLM_DEPLOYMENT_ID not set in .env")
    sys.exit(1)

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
# HELPERS
# =========================================================

def extract_text(file_path: str) -> str:
    if file_path.lower().endswith(".pdf"):
        reader = PdfReader(file_path)
        return "\n".join(page.extract_text() or "" for page in reader.pages)

    elif file_path.lower().endswith(".docx"):
        doc = Document(file_path)
        return "\n".join(p.text for p in doc.paragraphs)

    else:
        raise ValueError("Unsupported file type. Use PDF or DOCX.")


def generate_understanding(document_text: str) -> str:
    chain = IFLOW_UNDERSTANDING_PROMPT | llm | StrOutputParser()
    return chain.invoke({"document_text": document_text})


def generate_final_prompt(approved_design: str) -> str:
    chain = CANONICAL_IFLOW_PROMPT | llm | StrOutputParser()
    return chain.invoke({"approved_design": approved_design})

# =========================================================
# MAIN FLOW (TERMINAL HITL)
# =========================================================

def main():
    if len(sys.argv) < 2:
        print("Usage: python cli_iflow_prompt.py <path-to-pdf-or-docx>")
        sys.exit(1)

    file_path = sys.argv[1]

    print("\n📄 Extracting document text...")
    document_text = extract_text(file_path)

    print("\n🧠 Generating iFlow understanding (HITL)...\n")
    understanding = generate_understanding(document_text)

    print("========== IFLOW UNDERSTANDING ==========\n")
    print(understanding)
    print("\n========================================\n")

    print("✋ Review the above understanding.")
    print("You may edit it before continuing.")
    print("When ready, paste the APPROVED DESIGN below.")
    print("End input with a blank line.\n")

    # Read multi-line approved design from terminal
    approved_lines = []
    while True:
        line = input()
        if line.strip() == "":
            break
        approved_lines.append(line)

    approved_design = "\n".join(approved_lines)

    if not approved_design.strip():
        print("❌ No approved design provided. Exiting.")
        sys.exit(1)

    print("\n🎯 Generating final canonical prompt...\n")
    final_prompt = generate_final_prompt(approved_design)

    print("========== FINAL EXECUTION PROMPT ==========\n")
    print(final_prompt)
    print("\n============================================\n")

    print("✅ Copy the above prompt into your existing iFlow creation code.")

# =========================================================

if __name__ == "__main__":
    main()
