import os
import io
import time
import uvicorn
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pypdf import PdfReader
from docx import Document
from dotenv import load_dotenv
from google import genai
from google.genai import types
from pydantic import BaseModel
from typing import List, Dict, Any

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=API_KEY)

MODEL_NAME = "gemini-2.5-flash-lite"

execution_logs: List[str] = []
extracted_tasks: List[Dict[str, Any]] = []

# --- AGENTIC TOOLS ---
def schedule_task(task_name: str, deadline: str, priority: str) -> str:
    """Saves a discovered milestone task straight into local in-memory states."""
    task_item = {
        "title": task_name,
        "deadline": deadline,
        "priority": priority.upper() if priority else "MEDIUM",
        "status": "Ready"
    }
    extracted_tasks.append(task_item)
    log_msg = f"[AGENT ACTION] Successfully isolated and indexed task: '{task_name}' (Due: {deadline})"
    execution_logs.append(log_msg)
    return log_msg

def autonomous_drafting(task_name: str, generated_content: str) -> str:
    """Drafts study outlines or initial execution approaches for high-priority items."""
    log_msg = f"[AGENT ACTION] Execution Engine complete: Generated full strategy layout for '{task_name}'."
    execution_logs.append(log_msg)
    return log_msg

@app.post("/agent/process")
async def process_document(file: UploadFile = File(...)):
    global execution_logs, extracted_tasks
    
    
    execution_logs = []
    extracted_tasks = []
    
    print(f"⚡ Brain7 Core Processing Engine triggered for file: {file.filename}")
    
    try:
        content = await file.read()
        text = ""

        # Router parsing architecture
        if file.filename.lower().endswith(".pdf"):
            pdf = PdfReader(io.BytesIO(content))
            text = " ".join([page.extract_text() or "" for page in pdf.pages])
        elif file.filename.lower().endswith(".docx"):
            doc = Document(io.BytesIO(content))
            text = " ".join([paragraph.text for paragraph in doc.paragraphs])
        else:
            text = content.decode("utf-8", errors="ignore")

        if not text.strip() or len(text.strip()) < 10:
            return {
                "summary": "The input data source does not contain valid parseable text blocks.",
                "tasks": [],
                "logs": ["[Pipeline Error] File context empty."]
            }

        prompt = (
            f"Analyze the following document corpus completely:\n\n{text[:6000]}\n\n"
            "Execution Instructions:\n"
            "1. Extract every assignment, milestone, lab report deadline, exam date, or project milestone.\n"
            "2. Execute the 'schedule_task' tool for EACH item found to save it.\n"
            "3. Identify the highest priority or nearest chronological objective and call 'autonomous_drafting' to construct an execution blueprint.\n"
            "4. Return a highly professional text summary outlining your agent actions and key insights."
        )
        
        try:
            response = client.models.generate_content(
                model=MODEL_NAME,
                contents=prompt,
                config=types.GenerateContentConfig(
                    tools=[schedule_task, autonomous_drafting],
                    automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=False)
                )
            )
            
            return {
                "summary": response.text,
                "tasks": extracted_tasks,
                "logs": execution_logs
            }
        except Exception as ai_err:
            if "429" in str(ai_err):
                return {
                    "summary": "⚠️ Operational Warning: Standard quota restrictions hit. The engine is cooling down.",
                    "tasks": [],
                    "logs": ["AI API Request Throttled (429). Please try running again in 20 seconds."]
                }
            raise ai_err

    except Exception as e:
        print(f"❌ Critical system failure: {str(e)}")
        return {
            "summary": f"System runtime error encountered during ingestion: {str(e)}",
            "tasks": [],
            "logs": [f"Error: {str(e)}"]
        }

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)