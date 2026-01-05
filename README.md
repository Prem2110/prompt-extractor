# SAP CPI iFlow Prompt Generator  
**Human-in-the-Loop | SAP AI Core | CLI + API**

## Overview

This project converts **SAP Integration Suite (CPI) iFlow design documents** (PDF or DOCX) into a **short, deterministic execution prompt** that can be directly consumed by an **existing iFlow creation automation** (MCP / SAP AI Core–based).

It supports **two execution modes**:

1. **Terminal (CLI) execution** – ideal for local testing and Human-in-the-Loop workflows  
2. **API execution (FastAPI)** – usable via **Postman** or **Swagger UI**

Both modes implement the same **Human-in-the-Loop (HITL)** pipeline:

1. Extract document text  
2. LLM interprets iFlow intent  
3. Human reviews and approves  
4. LLM generates a **2–4 line canonical execution prompt**

## Key Features

- SAP AI Core + LangChain integration
- Deterministic output (`temperature = 0`)
- Human-in-the-Loop approval
- Supports **PDF** and **DOCX**
- Produces MCP / tool-friendly prompts
- No CPI APIs are executed by this tool
- Works via **terminal** or **REST API**

## Project Structure

```
Prompt_extractor/
│
├── hil.py     # Terminal (CLI) execution
├── app.py                  # FastAPI application (Postman / Swagger)
├── .env                    # SAP AI Core credentials
├── README.md               # This file
└── sample.docx             # Example SAP CPI document
```

## Prerequisites

- Python **3.10+**
- SAP BTP account with **AI Core**
- An active **LLM deployment** in SAP AI Core
- Deployment ID of the LLM (not model name)

## Dependencies

Install once for **both CLI and API modes**:

```bash
pip install pypdf python-docx python-dotenv langchain langchain-core gen-ai-hub-sdk fastapi uvicorn
```

## Environment Configuration

Create a `.env` file in the project root.

### Example `.env`

```env
AICORE_CLIENT_ID=xxxxxxxx
AICORE_CLIENT_SECRET=xxxxxxxx
AICORE_AUTH_URL=https://gen-ai.authentication.<region>.hana.ondemand.com
AICORE_RESOURCE_GROUP=default
AICORE_BASE_URL=https://api.ai.prod.<region>.aws.ml.hana.ondemand.com/v2

LLM_DEPLOYMENT_ID=your_deployment_id_here
```

### Important Rules

- ❌ No spaces around `=`
- ❌ No inline comments
- ✅ `LLM_DEPLOYMENT_ID` must be the **deployment ID**
- 🔄 Restart the terminal after changing `.env`

## Execution Mode 1: Terminal (CLI)

### Run the CLI Tool

```bash
python hil.py "<path-to-pdf-or-docx>"
```

## Execution Mode 2: API (Postman / Swagger UI)

### Start the API Server

```bash
uvicorn app:app --host 127.0.0.1 --port 8000
```

Swagger UI:
```
http://127.0.0.1:8000/docs
```

## Security Notes

- Never commit `.env` to version control
- Rotate credentials if exposed
- Treat generated prompts as operational artifacts

## Summary

This project provides a **dual-mode (CLI + API)** Human-in-the-Loop system that bridges **human integration design documents** and **machine-executable SAP CPI automation**, using SAP AI Core responsibly and deterministically.
