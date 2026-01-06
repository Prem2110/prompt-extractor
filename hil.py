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

# 🔥 NEW: LLM-based editor prompt
IFLOW_EDIT_PROMPT = ChatPromptTemplate.from_template("""
You are an SAP CPI design reviewer.

You are given:
1. The current approved iFlow design
2. A human edit instruction

Apply ONLY the requested change.
Preserve all other content exactly.
Do not summarize.
Do not remove sections unless explicitly instructed.

Current design:
{current_design}

Edit instruction:
{edit_instruction}

Return the FULL updated design.
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


def apply_edit_with_llm(current_design: str, edit_instruction: str) -> str:
    chain = IFLOW_EDIT_PROMPT | llm | StrOutputParser()
    return chain.invoke({
        "current_design": current_design,
        "edit_instruction": edit_instruction
    })


def generate_final_prompt(approved_design: str) -> str:
    chain = CANONICAL_IFLOW_PROMPT | llm | StrOutputParser()
    return chain.invoke({"approved_design": approved_design})

# =========================================================
# HUMAN-IN-THE-LOOP REVIEW LOOP (LLM-ASSISTED)
# =========================================================

def review_loop(initial_understanding: str) -> str:
    current_design = initial_understanding

    while True:
        print("\n========== IFLOW UNDERSTANDING ==========\n")
        print(current_design)
        print("\n========================================\n")

        print("🧑‍💼 Human-in-the-loop decision:")
        print("[Y] Yes   → Approve and continue")
        print("[E] Edit  → Provide edit instruction")
        print("[N] No    → Abort")

        choice = input("\nEnter choice (Y/E/N): ").strip().lower()

        if choice in ("y", "yes"):
            print("\n✅ Design approved.")
            return current_design

        elif choice in ("e", "edit"):
            print("\n✏️ Enter edit instruction (single or multi-line).")
            print("Example: 'Update the package name to mcptest'")
            print("Press ENTER on an empty line to apply.\n")

            lines = []
            while True:
                line = input()
                if line.strip() == "":
                    break
                lines.append(line)

            edit_instruction = "\n".join(lines).strip()

            if not edit_instruction:
                print("⚠️ No edit provided. Skipping.")
                continue

            print("\n🧠 Applying edit using LLM...\n")
            current_design = apply_edit_with_llm(
                current_design=current_design,
                edit_instruction=edit_instruction
            )

            print("🔄 Edit applied successfully.")

        elif choice in ("n", "no"):
            print("\n❌ Aborted by user.")
            sys.exit(0)

        else:
            print("\n⚠️ Invalid choice. Please enter Y, E, or N.")

# =========================================================
# MAIN
# =========================================================

def main():
    if len(sys.argv) < 2:
        print("Usage: python cli_iflow_hitl_llm_edit.py <path-to-pdf-or-docx>")
        sys.exit(1)

    file_path = sys.argv[1]

    print("\n📄 Extracting document text...")
    document_text = extract_text(file_path)

    print("\n🧠 Generating iFlow understanding (HITL)...\n")
    understanding = generate_understanding(document_text)

    approved_design = review_loop(understanding)

    print("\n🎯 Generating final canonical prompt...\n")
    final_prompt = generate_final_prompt(approved_design)

    print("========== FINAL EXECUTION PROMPT ==========\n")
    print(final_prompt)
    print("\n============================================\n")

    print("✅ Ready for MCP / iFlow execution.")

# =========================================================

if __name__ == "__main__":
    main()
