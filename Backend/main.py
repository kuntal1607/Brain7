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
from typing import List, Dict, Any, Optional

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

def schedule_task(task_name: str, deadline: str, priority: str, link: Optional[str] = None) -> str:
    task_item = {
        "title": task_name,
        "deadline": deadline,
        "priority": priority.upper() if priority else "MEDIUM",
        "status": "Ready",
        "link": link if link else None
    }
    extracted_tasks.append(task_item)
    log_msg = f"[AGENT ACTION] Successfully isolated and indexed task: '{task_name}' (Due: {deadline})"
    if link:
        log_msg += f" | Link: {link}"
    execution_logs.append(log_msg)
    return log_msg

def autonomous_drafting(task_name: str, generated_content: str) -> str:
    log_msg = f"[AGENT ACTION] Execution Engine complete: Generated full strategy layout for '{task_name}'."
    execution_logs.append(log_msg)
    return log_msg

@app.post("/agent/process")
async def process_document(file: UploadFile = File(...)):
    global execution_logs, extracted_tasks
    
    previous_tasks_count = len(extracted_tasks)
    
    if len(execution_logs) > 20:
        execution_logs = execution_logs[-20:]
        
    print(f"⚡ Brain7 Core Processing Engine triggered for file: {file.filename}")
    
    try:
        content = await file.read()
        text = ""

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
            "1. Extract every assignment, milestone, utility bill payment, lab report deadline, exam date, or project milestone.\n"
            "2. Execute the 'schedule_task' tool for EACH item found to save it.\n"
            "   CRITICAL DATE SPECIFICATION: For the 'deadline' property, always pass a clean format like 'YYYY-MM-DD' or 'Month DD' (e.g., 'June 26') if discernible so the UI algorithm can order it correctly.\n"
            "3. FOR UTILITY/ELECTRICITY BILLS: Scan the document corpus for dynamic online billing payment urls. If no specific payment link is found within the text, you must provide a general fallback portal utility URL (e.g., https://www.amazon.in/bills or a major national payment desk link) where bill settlement occurs online.\n"
            "4. FOR SCHOOL, COLLEGE, OR ACADEMIC PROJECTS: Automatically generate a helpful reference research search query link targeting that specific project domain assignment (e.g., 'https://www.google.com/search?q=how+to+build+' appended with relevant search terms of that specific assignment name) so that users can open it to read documentation details instantly.\n"
            "5. Pass this URL string into the 'link' parameter inside the 'schedule_task' tool invocation. If an extracted task does not involve a payment bill or technical/academic project, leave the parameter blank.\n"
            "6. Identify the highest priority or nearest chronological objective and call 'autonomous_drafting' to construct an execution blueprint.\n"
            "7. Return a highly professional text summary outlining your agent actions and key insights."
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
            
            newly_discovered_tasks = extracted_tasks[previous_tasks_count:]
            
            return {
                "summary": response.text,
                "tasks": newly_discovered_tasks,
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