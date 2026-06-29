import os
import io
import json
import re
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

@app.post("/agent/process")
async def process_document(file: UploadFile = File(...)):
    global execution_logs, extracted_tasks
    
    if len(execution_logs) > 20:
        execution_logs = execution_logs[-20:]
        
    print(f"⚡ Brain7 Core Processing Engine triggered for file: {file.filename}")
    execution_logs.append(f"[SYSTEM] Initialized secure processing for: {file.filename}")
    
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
            "You are a strict JSON generator. Your goal is to analyze the document text and return a valid JSON object matching the specifications below.\n\n"
            "Instructions:\n"
            "1. Identify all tasks, utility bill payments, school/college project milestones, or exam deadlines.\n"
            "2. For each milestone, provide a 'title', a clean 'deadline' format (like YYYY-MM-DD or Month DD), and a 'priority' (HIGH, MEDIUM, or LOW).\n"
            "3. FOR UTILITY/ELECTRICITY BILLS: Scan the text for online payment URLs. If no specific payment link is found, generate a general utility fallback portal link (e.g., https://www.amazon.in/bills or a major national payment desk link) where the user can settle that bill online.\n"
            "4. FOR SCHOOL, COLLEGE, OR ACADEMIC PROJECTS: Automatically generate a helpful reference search query link targeting that specific project topic (e.g., 'https://www.google.com/search?q=how+to+build+' appended with relevant search terms for that assignment).\n"
            "5. If a task does not involve a payment bill or an academic project, set the 'link' property to null.\n"
            "6. Provide a concise brief summary of the items extracted.\n\n"
            "Your output must be a single JSON object containing a 'summary' string and a 'tasks' array. Do not wrap it in markdown code blocks or add extra conversational text. Follow this schema exactly:\n"
            "{\n"
            "  \"summary\": \"Brief overview of the items extracted.\",\n"
            "  \"tasks\": [\n"
            "    {\"title\": \"Task Name\", \"deadline\": \"June 26\", \"priority\": \"HIGH\", \"link\": \"https://...\"},\n"
            "    {\"title\": \"Standard Task\", \"deadline\": \"2026-07-01\", \"priority\": \"MEDIUM\", \"link\": null}\n"
            "  ]\n"
            "}"
        )
        
        execution_logs.append("[AGENT SYSTEM] Querying Gemini model for structured JSON generation...")
        
        try:
            response = client.models.generate_content(
                model=MODEL_NAME,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.1
                )
            )
            
            raw_text = response.text.strip()
            
            if raw_text.startswith("```json"):
                raw_text = raw_text.split("```json", 1)[1]
            if raw_text.endswith("```"):
                raw_text = raw_text.rsplit("```", 1)[0]
            raw_text = raw_text.strip()
            
            parsed_data = json.loads(raw_text)
            
            ai_summary = parsed_data.get("summary", "Tasks extracted successfully.")
            ai_tasks = parsed_data.get("tasks", [])
            
            for task in ai_tasks:
                task["status"] = "Ready"
                if "link" not in task:
                    task["link"] = None
                    
                log_msg = f"[AGENT ACTION] Extracted task: '{task.get('title')}' (Due: {task.get('deadline')})"
                if task.get("link"):
                    log_msg += f" | Generated Link: {task.get('link')}"
                execution_logs.append(log_msg)
                
                extracted_tasks.append(task)
            
            return {
                "summary": ai_summary,
                "tasks": ai_tasks,
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