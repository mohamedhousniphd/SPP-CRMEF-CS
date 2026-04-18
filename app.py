import os
import json
import uuid
import textwrap
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
from openai import OpenAI

from docx_builder import create_report_docx

app = FastAPI(title="SPP Report Generator")

# Create directories for static files and outputs
Path("static").mkdir(exist_ok=True)
Path("outputs").mkdir(exist_ok=True)

# Serve static files
app.mount("/static", StaticFiles(directory="static"), name="static")

SYSTEM_PROMPT = """\
You are an expert academic writer and educational project consultant specializing
in Moroccan teacher-training programs. You will generate a complete, defense-ready
Supervised Personal Project (المشروع الشخصي المؤطر) final report for a trainee at
the Centre Regional des Metiers de l'Education et de la Formation (CRMEF) —
Casablanca-Settat Region, Computer Science Department.

This project is governed by the Management Guide for Qualifying Training 2025-2026.
It is NOT Action Research — it must focus strictly on practical innovation, renewal,
and the delivery of actionable solutions to real educational/pedagogical problems.

OUTPUT SPECIFICATIONS:
- Maximum 30 pages (excluding cover page, table of contents, references, appendices)
- Professional academic language suitable for a CRMEF defense
- Include tables, figures, and charts where they strengthen the presentation
- Every claim must be grounded in the data provided or properly referenced
- Write in the language specified by the user (Arabic or French ONLY)

MANDATORY REPORT STRUCTURE (exactly in this order):
1. Cover Page
2. Table of Contents
3. General Introduction
4. Topic Definition & Importance
5. Methodology & Implementation Plan
6. Results
7. Analysis & Interpretation
8. Discussion
9. Conclusions & Recommendations
10. Summary & Lessons Learned
11. References
12. Appendices

Generate the COMPLETE report in one pass. Use [DONNÉES À COMPLÉTER: ...] for missing info.
"""

class GenerateRequest(BaseModel):
    provider: str
    model: str
    api_key: str
    data: dict

@app.get("/")
async def read_index():
    return FileResponse('static/index.html')

@app.post("/api/generate")
async def generate_report_api(req: GenerateRequest):
    try:
        # Determine base URL
        base_urls = {
            "openai": "https://api.openai.com/v1",
            "openrouter": "https://openrouter.ai/api/v1",
            "aistudio": "https://generativelanguage.googleapis.com/v1beta/openai/"
        }
        
        base_url = base_urls.get(req.provider, "https://api.openai.com/v1")
        client = OpenAI(base_url=base_url, api_key=req.api_key)
        
        # Build user message (simplified version of generate_report.py logic)
        lang = req.data.get("language", "french").lower()
        lang_instruction = "Write the entire report in FRENCH." if "fr" in lang else "Write the entire report in ARABIC."
        
        user_message = f"{lang_instruction}\n\nPROJECT DATA:\n{json.dumps(req.data, indent=2, ensure_ascii=False)}\n\nNOW GENERATE THE COMPLETE REPORT."
        
        response = client.chat.completions.create(
            model=req.model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_message},
            ],
            temperature=0.4,
            max_tokens=15000,
        )
        
        content = response.choices[0].message.content
        return {"content": content}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class ExportRequest(BaseModel):
    content: str
    filename: Optional[str] = "report.docx"

@app.post("/api/export-docx")
async def export_docx(req: ExportRequest):
    try:
        file_id = str(uuid.uuid4())
        output_path = Path("outputs") / f"{file_id}.docx"
        
        create_report_docx(req.content, str(output_path))
        
        return JSONResponse({
            "file_id": file_id,
            "filename": req.filename
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/download/{file_id}")
async def download_file(file_id: str):
    file_path = Path("outputs") / f"{file_id}.docx"
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    
    return FileResponse(
        path=file_path,
        filename="PPE_Final_Report.docx",
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
