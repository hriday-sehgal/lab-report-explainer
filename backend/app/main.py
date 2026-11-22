"""
FastAPI Server Entrypoint
Provides REST endpoints:
- POST /api/reports/analyze
- GET  /api/health
- GET  /api/synthetic-reports (list 15 pre-generated test reports)
"""

import os
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles

from backend.app.config import settings
from backend.app.schemas.report_schema import LabReportAnalysis
from backend.app.services.report_service import ReportAnalysisService

app = FastAPI(
    title=settings.app_name,
    version=settings.version,
    description="Enterprise-grade diagnostic report explanation and evaluation system with Google ADK 2.0 and Gemini."
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

service = ReportAnalysisService()

# Static directories
STATIC_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "static"))
DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../data"))
EVALS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../evals"))

if os.path.exists(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

if os.path.exists(DATA_DIR):
    app.mount("/data", StaticFiles(directory=DATA_DIR), name="data")

if os.path.exists(EVALS_DIR):
    app.mount("/evals", StaticFiles(directory=EVALS_DIR), name="evals")

@app.get("/")
def get_dashboard():
    """Serves the interactive clinical explainer dashboard"""
    index_file = os.path.join(STATIC_DIR, "index.html")
    if os.path.exists(index_file):
        return FileResponse(index_file)
    return {"message": "HeyDoc AI Lab Explainer Backend API Active. Visit /docs for Swagger UI."}

@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "service": settings.app_name,
        "version": settings.version,
        "model": settings.gemini_model,
        "budget_limit_inr": settings.max_budget_inr
    }

@app.post("/api/reports/analyze", response_model=LabReportAnalysis)
async def analyze_report(file: UploadFile = File(...)):
    """
    Upload a medical lab report PDF to extract biomarkers, compute clinical flags,
    trigger panic value overrides, and generate grounded bilingual explanations.
    """
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are currently supported.")
        
    try:
        content = await file.read()
        analysis = service.analyze_pdf_bytes(content, filename=file.filename)
        return analysis
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Analysis pipeline error: {str(e)}")

@app.get("/api/synthetic-reports")
def list_synthetic_reports():
    """Lists the 15 synthetic benchmark reports available in the dataset"""
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../data/synthetic_reports"))
    if not os.path.exists(base_dir):
        return {"reports": []}
        
    files = sorted([f for f in os.listdir(base_dir) if f.endswith(".pdf")])
    return {"reports": files, "count": len(files)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app.main:app", host="0.0.0.0", port=8000, reload=True)
