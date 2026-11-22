#!/usr/bin/env python3
"""
Test Live Gemini Connection & Structured Extraction
Loads .env, tests the Gemini API key, sends a real sample report,
and prints live token counts, latency, and estimated cost in INR.
"""

import os
import sys
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from dotenv import load_dotenv
load_dotenv()

from backend.app.config import settings
from backend.app.services.report_service import ReportAnalysisService

def test_live_llm():
    api_key = os.getenv("GEMINI_API_KEY", "")
    print("=" * 60)
    print("TESTING LIVE GEMINI LLM CONNECTION VIA GOOGLE ADK / GENAI")
    print("=" * 60)
    
    if not api_key or api_key == "your_gemini_api_key_here":
        print("[!] No GEMINI_API_KEY found in .env (or it is still a placeholder).")
        print("    Add your real Gemini API key to .env:")
        print("    GEMINI_API_KEY=AIzaSy...")
        return
        
    masked_key = api_key[:6] + "..." + api_key[-4:]
    print(f"[✓] Found API Key: {masked_key}")
    print(f"[✓] Configured Model: {settings.gemini_model}")
    print("[*] Sending LAB-001.pdf through live Gemini analysis pipeline...")
    
    pdf_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../data/synthetic_reports/LAB-001.pdf"))
    with open(pdf_path, "rb") as f:
        pdf_bytes = f.read()
        
    service = ReportAnalysisService(api_key=api_key)
    
    start_time = time.perf_counter()
    result = service.analyze_pdf_bytes(pdf_bytes, "LAB-001.pdf")
    total_time = time.perf_counter() - start_time
    
    print("\n" + "=" * 60)
    print("LIVE GEMINI LLM EXECUTION RESULTS")
    print("=" * 60)
    print(f"Report ID:          {result.report_id}")
    print(f"Panel:              {result.panel_name}")
    print(f"Biomarkers count:   {len(result.biomarkers)}")
    print(f"Model Used:         {result.processing_metadata.model_used}")
    print(f"Total Tokens:       {result.processing_metadata.input_tokens + result.processing_metadata.output_tokens} (In: {result.processing_metadata.input_tokens}, Out: {result.processing_metadata.output_tokens})")
    print(f"Total Cost:         ₹{result.processing_metadata.estimated_cost_inr:.4f} INR")
    print(f"Total Pipeline Time:{total_time:.3f} s")
    print(f"Critical Triggered: {result.critical_alert.triggered}")
    print(f"Next Action:        {result.next_step.action.value}")
    
    print("\n--- SAMPLE LIVE ENGLISH EXPLANATION ---")
    if result.explanations_en:
        print(result.explanations_en[0].text)
        print(f"Cited Evidence: {result.explanations_en[0].evidence_item_ids}")
        
    print("\n--- SAMPLE LIVE HINDI EXPLANATION ---")
    if result.explanations_hi:
        print(result.explanations_hi[0].text)
        print(f"Cited Evidence: {result.explanations_hi[0].evidence_item_ids}")
        
    print("\n[✓] LIVE GEMINI INTEGRATION VERIFIED SUCCESSFULLY!")

if __name__ == "__main__":
    test_live_llm()
