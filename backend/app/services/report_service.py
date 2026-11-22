"""
End-to-End Lab Report Analysis Orchestrator Service
Coordinates:
PDF Text Parsing -> ADK/Gemini Extraction -> Pydantic Schema Validation ->
Deterministic Flag Engine -> Critical Panic Triggers -> Next-Step Router ->
Grounded Bilingual Explanations -> Grounding Audit Layer.
"""

import time
from typing import Dict, Any, List
from backend.app.schemas.report_schema import (
    LabReportAnalysis,
    LabBiomarker,
    ReferenceRange,
    PatientMetadata,
    ProcessingMetadata
)
from backend.app.services.pdf_parser import PDFParserService
from backend.app.agents.extractor_agent import ExtractorAgent
from backend.app.agents.explainer_agent import ExplainerAgent
from backend.app.clinical.flag_engine import calculate_biomarker_flag
from backend.app.clinical.next_step_engine import determine_next_step
from backend.app.clinical.grounding_validator import audit_and_filter_explanations

DISCLAIMER_EN = (
    "NOTICE: This AI-generated report summary is for educational and informational purposes only. "
    "It is NOT a medical diagnosis, clinical prognosis, or treatment prescription. Always consult a "
    "qualified healthcare provider for clinical diagnosis and management."
)

DISCLAIMER_HI = (
    "सूचना: यह AI-निर्मित रिपोर्ट सारांश केवल शैक्षिक और सूचनात्मक उद्देश्यों के लिए है। "
    "यह कोई चिकित्सीय निदान या उपचार सलाह नहीं है। सटीक परामर्श और निदान के लिए हमेशा योग्य डॉक्टर से संपर्क करें।"
)

class ReportAnalysisService:
    def __init__(self, api_key: str = None):
        self.extractor = ExtractorAgent(api_key=api_key)
        self.explainer = ExplainerAgent(api_key=api_key)

    def analyze_pdf_bytes(self, pdf_bytes: bytes, filename: str = "report.pdf") -> LabReportAnalysis:
        pipeline_start = time.perf_counter()
        
        # 1. Parse text from PDF
        text, pdf_meta = PDFParserService.extract_text_from_pdf_bytes(pdf_bytes)
        if not text:
            raise ValueError("Could not extract readable text from the provided PDF.")
            
        # 2. Extract structured data
        raw_data, extract_perf = self.extractor.extract_from_text(text)
        
        # 3. Deterministic Flag and Clinical Evaluation
        validated_biomarkers: List[LabBiomarker] = []
        has_critical = False
        
        raw_biomarkers = raw_data.get("biomarkers", [])
        for item in raw_biomarkers:
            ref_low = item.get("reference_low")
            ref_high = item.get("reference_high")
            ref_text = item.get("reference_text", f"{ref_low} - {ref_high}")
            
            ref_range = ReferenceRange(low=ref_low, high=ref_high, text_range=ref_text)
            flag, is_crit, clinical_note = calculate_biomarker_flag(
                test_name=item["test_name"],
                value=float(item["value"]),
                reference_range=ref_range
            )
            
            if is_crit:
                has_critical = True
                
            validated_biomarkers.append(LabBiomarker(
                item_id=item["item_id"],
                test_name=item["test_name"],
                value=float(item["value"]),
                unit=item.get("unit", ""),
                reference_range=ref_range,
                flag=flag,
                is_critical=is_crit,
                clinical_note=clinical_note
            ))
            
        # 4. Deterministic Next-Step Evaluation
        next_step = determine_next_step(validated_biomarkers, has_critical)
        
        # 5. Grounded Bilingual Explanations
        crit_alert, exp_en, exp_hi, explain_perf = self.explainer.explain_biomarkers(
            biomarkers=validated_biomarkers,
            has_critical=has_critical
        )
        
        # 6. Grounding and Safety Audit
        clean_exp_en, score_en, logs_en = audit_and_filter_explanations(exp_en, validated_biomarkers)
        clean_exp_hi, score_hi, logs_hi = audit_and_filter_explanations(exp_hi, validated_biomarkers)
        
        total_latency = time.perf_counter() - pipeline_start
        total_cost_inr = extract_perf.get("estimated_cost_inr", 0.0) + explain_perf.get("estimated_cost_inr", 0.0)
        total_in_tokens = extract_perf.get("input_tokens", 0) + explain_perf.get("input_tokens", 0)
        total_out_tokens = extract_perf.get("output_tokens", 0) + explain_perf.get("output_tokens", 0)
        
        patient_info = raw_data.get("patient", {})
        patient_meta = PatientMetadata(
            name=patient_info.get("name", "Unknown"),
            age=patient_info.get("age"),
            gender=patient_info.get("gender"),
            patient_id=patient_info.get("patient_id"),
            collection_date=patient_info.get("collection_date"),
            referred_by=patient_info.get("referred_by")
        )
        
        proc_meta = ProcessingMetadata(
            latency_seconds=round(total_latency, 3),
            model_used=f"{extract_perf.get('model_used', 'agent')} + {explain_perf.get('model_used', 'agent')}",
            input_tokens=total_in_tokens,
            output_tokens=total_out_tokens,
            estimated_cost_inr=round(total_cost_inr, 4)
        )
        
        return LabReportAnalysis(
            report_id=raw_data.get("report_id", filename.replace(".pdf", "")),
            report_type=raw_data.get("report_type", "GENERAL"),
            panel_name=raw_data.get("panel_name", "Diagnostic Blood Investigation"),
            patient_metadata=patient_meta,
            biomarkers=validated_biomarkers,
            critical_alert=crit_alert,
            explanations_en=clean_exp_en,
            explanations_hi=clean_exp_hi,
            next_step=next_step,
            disclaimer_en=DISCLAIMER_EN,
            disclaimer_hi=DISCLAIMER_HI,
            processing_metadata=proc_meta
        )
