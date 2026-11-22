"""
Extraction Agent with Google GenAI / ADK 2.0
Extracts structured patient metadata and test biomarkers from lab report text into
schema-validated data models.
Tracks latency, token counts, and cost.
"""

import time
import json
import re
from typing import Tuple, Dict, Any, List
from google import genai
from google.genai import types

from backend.app.config import settings
from backend.app.schemas.report_schema import ExtractedBiomarkerRaw, PatientMetadata

EXTRACTION_SYSTEM_PROMPT = """You are a specialized clinical data extraction agent for diagnostic laboratories.
Your task is to extract all laboratory investigations from the provided report text into a strict JSON object.

Rules:
1. Extract patient details (name, age, gender, patient_id, collection_date, referred_by).
2. Extract the panel name and report type (CBC, LIPID, HBA1C, THYROID, LFT, MULTI).
3. For every single test result, extract:
   - item_id: uppercase short identifier (e.g. CBC_HGB, LIPID_CHOL, LFT_ALT)
   - test_name: full canonical test name
   - value: numeric value (float)
   - unit: string unit of measurement (e.g. g/dL, mg/dL, /uL, uIU/mL)
   - reference_low: numeric lower reference bound if present, else null
   - reference_high: numeric upper reference bound if present, else null
   - reference_text: unparsed reference interval string from report
4. Extract only facts present in the text. Do not invent or fabricate data.

Return ONLY valid JSON matching this structure:
{
  "report_id": "...",
  "report_type": "...",
  "panel_name": "...",
  "patient": {
    "name": "...",
    "age": 30,
    "gender": "...",
    "patient_id": "...",
    "collection_date": "...",
    "referred_by": "..."
  },
  "biomarkers": [
    {
      "item_id": "...",
      "test_name": "...",
      "value": 0.0,
      "unit": "...",
      "reference_low": 0.0,
      "reference_high": 0.0,
      "reference_text": "..."
    }
  ]
}
"""

class ExtractorAgent:
    def __init__(self, api_key: str = None):
        self.api_key = api_key or settings.gemini_api_key
        self.client = genai.Client(api_key=self.api_key) if self.api_key else None

    def extract_from_text(self, report_text: str) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """
        Extracts structured data from report text.
        Returns: (parsed_data, token_and_perf_metadata)
        """
        start_time = time.perf_counter()
        
        # If API key is available, try at most 2 cheap lightweight models (1 attempt each, fast failover)
        if self.client:
            models_to_try = [settings.gemini_model, "gemini-2.0-flash-lite"]
            # Deduplicate preserving order
            unique_models = []
            for m in models_to_try:
                if m and m not in unique_models:
                    unique_models.append(m)
            
            for model_name in unique_models[:2]:
                try:
                    response = self.client.models.generate_content(
                        model=model_name,
                        contents=[
                            EXTRACTION_SYSTEM_PROMPT,
                            f"LAB REPORT TEXT:\n{report_text}"
                        ],
                        config=types.GenerateContentConfig(
                            temperature=0.0,
                            response_mime_type="application/json"
                        )
                    )
                    latency = time.perf_counter() - start_time
                    
                    # Clean markdown code fences if present
                    resp_text = (response.text or "").strip()
                    resp_text = re.sub(r"^```(?:json)?\s*", "", resp_text, flags=re.MULTILINE)
                    resp_text = re.sub(r"\s*```$", "", resp_text, flags=re.MULTILINE)
                    
                    raw_json = json.loads(resp_text)
                    if not raw_json.get("biomarkers"):
                        # If model returned empty biomarker array, fall back
                        continue
                        
                    usage = getattr(response, "usage_metadata", None)
                    in_tokens = getattr(usage, "prompt_token_count", 800) if usage else 800
                    out_tokens = getattr(usage, "candidates_token_count", 350) if usage else 350
                    
                    cost_usd = (in_tokens / 1_000_000 * settings.input_cost_per_m_tokens) + \
                               (out_tokens / 1_000_000 * settings.output_cost_per_m_tokens)
                    cost_inr = cost_usd * settings.usd_to_inr
                    
                    perf_meta = {
                        "latency_seconds": round(latency, 3),
                        "model_used": model_name,
                        "execution_mode": "LIVE_LLM",
                        "is_live_llm": True,
                        "engine_label": f"Live Gemini LLM ({model_name})",
                        "input_tokens": in_tokens,
                        "output_tokens": out_tokens,
                        "estimated_cost_inr": round(cost_inr, 4)
                    }
                    return raw_json, perf_meta
                except Exception as e:
                    print(f"[ExtractorAgent] Lightweight model '{model_name}' failed: {e}. Trying fallback...")
                    continue
            
        # Deterministic regex parser fallback (guarantees zero-network execution, no hanging, and offline evals)
        return self._deterministic_extract(report_text, start_time)

    def _deterministic_extract(self, text: str, start_time: float) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        latency = time.perf_counter() - start_time
        
        # Extract report ID
        rep_id_match = re.search(r"Report ID:\s*([A-Za-z0-9\-]+)", text)
        report_id = rep_id_match.group(1) if rep_id_match else "UNKNOWN_REP"
        
        # Extract patient metadata
        p_name = re.search(r"Patient Name:\s*([^\n\r]+)", text)
        p_age_sex = re.search(r"Age / Sex:\s*(\d+)\s*Yrs\s*/\s*([A-Za-z]+)", text)
        p_id = re.search(r"Patient ID:\s*([A-Za-z0-9\-]+)", text)
        p_ref = re.search(r"Referred By:\s*([^\n\r]+)", text)
        p_date = re.search(r"Sample Date:\s*([0-9\-]+)", text)
        
        patient = {
            "name": p_name.group(1).strip() if p_name else "Unknown",
            "age": int(p_age_sex.group(1)) if p_age_sex else 30,
            "gender": p_age_sex.group(2).strip() if p_age_sex else "Unknown",
            "patient_id": p_id.group(1).strip() if p_id else "UNKNOWN_ID",
            "collection_date": p_date.group(1).strip() if p_date else "2026-11-20",
            "referred_by": p_ref.group(1).strip() if p_ref else "Clinical Review"
        }
        
        # Determine panel
        panel_name = "DIAGNOSTIC LAB INVESTIGATION"
        report_type = "GENERAL"
        if "COMPLETE BLOOD COUNT" in text:
            panel_name = "COMPLETE BLOOD COUNT (CBC)"
            report_type = "CBC"
        elif "LIPID PROFILE" in text:
            panel_name = "LIPID PROFILE"
            report_type = "LIPID"
        elif "HbA1c" in text or "DIABETES" in text:
            panel_name = "DIABETES MONITORING (HbA1c)"
            report_type = "HBA1C"
        elif "THYROID" in text:
            panel_name = "THYROID PROFILE"
            report_type = "THYROID"
        elif "LIVER FUNCTION" in text or "LFT" in text:
            panel_name = "LIVER FUNCTION TEST (LFT)"
            report_type = "LFT"
            
        biomarkers = []
        
        # Regex patterns for tabular rows
        # 1. Single-line row: Name ... Number Unit Low - High
        single_line_pattern = r"([A-Za-z0-9\(\)\/\s\.\-]+?)\s+([\d\.]+)\s+([a-zA-Z\/\%u\u03bcL]+)\s+([\d\.]+)\s*[\-\–]\s*([\d\.]+)"
        
        lines = [l.strip() for l in text.split("\n") if l.strip()]
        item_counter = 1
        
        # Check if table headers exist sequentially
        header_idx = -1
        for i, l in enumerate(lines):
            if "Status Flag" in l or ("Investigation" in l and i + 4 < len(lines)):
                header_idx = i
                break

        # Strategy A: Sequential table cell extraction (common in PDF table streams)
        if header_idx != -1 and header_idx + 1 < len(lines):
            i = header_idx + 1
            while i < len(lines):
                # Stop if end of table / remarks reached
                if "Pathologist Remarks" in lines[i] or "END OF EXAMINATION" in lines[i]:
                    break
                    
                # Look for pattern: Name (line i), Value (line i+1), Unit (line i+2), Range (line i+3), Flag (line i+4)
                if i + 3 < len(lines):
                    name_cand = lines[i]
                    val_cand = lines[i+1]
                    unit_cand = lines[i+2]
                    range_cand = lines[i+3]
                    
                    # Check if val_cand is a float
                    val_match = re.match(r"^([\d\.]+)$", val_cand)
                    range_match = re.match(r"^([\d\.]+)\s*[\-\–]\s*([\d\.]+)$", range_cand)
                    
                    if val_match and range_match:
                        val = float(val_match.group(1))
                        r_low = float(range_match.group(1))
                        r_high = float(range_match.group(2))
                        
                        slug = re.sub(r"[^A-Za-z0-9]", "_", name_cand).upper()[:12]
                        item_id = f"{report_type}_{slug}_{item_counter}"
                        item_counter += 1
                        
                        biomarkers.append({
                            "item_id": item_id,
                            "test_name": name_cand,
                            "value": val,
                            "unit": unit_cand,
                            "reference_low": r_low,
                            "reference_high": r_high,
                            "reference_text": range_cand
                        })
                        # Advance past this row (checking if line i+4 is a flag)
                        if i + 4 < len(lines) and any(f in lines[i+4] for f in ["NORMAL", "HIGH", "LOW", "CRITICAL"]):
                            i += 5
                        else:
                            i += 4
                        continue
                i += 1

        # Strategy B: Fallback to single-line pattern if sequential did not find items
        if not biomarkers:
            for line in lines:
                if "Investigation" in line or "Accredited" in line:
                    continue
                m = re.search(single_line_pattern, line)
                if m:
                    t_name = m.group(1).strip()
                    if len(t_name) < 3 or any(w in t_name for w in ["Page", "Date", "Department"]):
                        continue
                    try:
                        val = float(m.group(2))
                        unit = m.group(3).strip()
                        r_low = float(m.group(4))
                        r_high = float(m.group(5))
                        slug = re.sub(r"[^A-Za-z0-9]", "_", t_name).upper()[:12]
                        item_id = f"{report_type}_{slug}_{item_counter}"
                        item_counter += 1
                        biomarkers.append({
                            "item_id": item_id,
                            "test_name": t_name,
                            "value": val,
                            "unit": unit,
                            "reference_low": r_low,
                            "reference_high": r_high,
                            "reference_text": f"{r_low} - {r_high}"
                        })
                    except ValueError:
                        continue

        parsed = {
            "report_id": report_id,
            "report_type": report_type,
            "panel_name": panel_name,
            "patient": patient,
            "biomarkers": biomarkers
        }
        
        perf = {
            "latency_seconds": round(latency, 4),
            "model_used": "deterministic-clinical-engine",
            "execution_mode": "DETERMINISTIC_FALLBACK",
            "is_live_llm": False,
            "engine_label": "Deterministic Clinical Engine (Safe Offline Mode)",
            "input_tokens": 0,
            "output_tokens": 0,
            "estimated_cost_inr": 0.0
        }
        return parsed, perf
