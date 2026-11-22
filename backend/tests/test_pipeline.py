"""
Unit and Integration Tests for Lab Report Explainer Pipeline
Verifies:
1. Pydantic schema validation
2. Deterministic reference range flagging
3. Critical panic value detection and alerts
4. Next-step deterministic routing
5. Grounding verification and anti-diagnosis filtering
6. FastAPI health and analyze endpoints
"""

import os
import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.schemas.report_schema import FlagType, ReferenceRange, NextStepType, LabBiomarker
from backend.app.clinical.flag_engine import calculate_biomarker_flag
from backend.app.clinical.critical_values import evaluate_critical_value
from backend.app.clinical.next_step_engine import determine_next_step
from backend.app.clinical.grounding_validator import audit_and_filter_explanations
from backend.app.schemas.report_schema import ExplanationItem
from backend.app.services.report_service import ReportAnalysisService

client = TestClient(app)

def test_health_endpoint():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "HeyDoc AI" in data["service"]

def test_deterministic_flag_engine_normal():
    ref = ReferenceRange(low=13.0, high=17.0)
    flag, is_crit, note = calculate_biomarker_flag("Hemoglobin", 14.5, ref)
    assert flag == FlagType.NORMAL
    assert not is_crit

def test_deterministic_flag_engine_low_and_high():
    ref = ReferenceRange(low=12.0, high=15.0)
    flag_low, is_crit, _ = calculate_biomarker_flag("Hemoglobin", 10.5, ref)
    assert flag_low == FlagType.LOW
    assert not is_crit
    
    flag_high, is_crit, _ = calculate_biomarker_flag("Hemoglobin", 16.5, ref)
    assert flag_high == FlagType.HIGH
    assert not is_crit

def test_critical_panic_value_trigger():
    # Platelet count < 20,000 /uL
    res = evaluate_critical_value("Platelet Count", 14000.0)
    assert res is not None
    assert res["is_critical"] is True
    assert res["flag"] == "critical_low"

    # Hemoglobin < 7.0 g/dL
    res_hgb = evaluate_critical_value("Hemoglobin", 5.8)
    assert res_hgb is not None
    assert res_hgb["is_critical"] is True
    assert res_hgb["flag"] == "critical_low"

def test_hba1c_false_positive_guard():
    # Ensures HbA1c (e.g. 5.4%) does NOT trigger whole-blood hemoglobin critical low
    res = evaluate_critical_value("HbA1c (Glycated Hemoglobin)", 5.4)
    assert res is None

def test_next_step_routing():
    b_crit = LabBiomarker(
        item_id="CBC_PLT",
        test_name="Platelet Count",
        value=14000.0,
        unit="/uL",
        reference_range=ReferenceRange(low=150000, high=450000),
        flag=FlagType.CRITICAL_LOW,
        is_critical=True
    )
    guidance_crit = determine_next_step([b_crit], has_critical=True)
    assert guidance_crit.action == NextStepType.DOCTOR_CONSULT

    b_norm = LabBiomarker(
        item_id="CBC_HGB",
        test_name="Hemoglobin",
        value=14.0,
        unit="g/dL",
        reference_range=ReferenceRange(low=13.0, high=17.0),
        flag=FlagType.NORMAL,
        is_critical=False
    )
    guidance_norm = determine_next_step([b_norm], has_critical=False)
    assert guidance_norm.action == NextStepType.NO_ACTION

def test_grounding_audit_rejects_hallucinations_and_diagnoses():
    biomarkers = [
        LabBiomarker(
            item_id="BIO_1",
            test_name="Hemoglobin",
            value=9.5,
            unit="g/dL",
            reference_range=ReferenceRange(low=12.0, high=15.0),
            flag=FlagType.LOW,
            is_critical=False
        )
    ]
    
    explanations = [
        # Valid grounded sentence
        ExplanationItem(sentence_id="E1", language="en", text="Hemoglobin is 9.5 g/dL, which is low.", evidence_item_ids=["BIO_1"]),
        # Invalid citation ID
        ExplanationItem(sentence_id="E2", language="en", text="Your WBC count is fine.", evidence_item_ids=["NON_EXISTENT_ID"]),
        # Forbidden diagnosis sentence
        ExplanationItem(sentence_id="E3", language="en", text="You have anemia and should take iron tablets.", evidence_item_ids=["BIO_1"])
    ]
    
    passed, score, logs = audit_and_filter_explanations(explanations, biomarkers)
    assert len(passed) == 1
    assert passed[0].sentence_id == "E1"
    assert any("NON_EXISTENT_ID" in l for l in logs)
    assert any("forbidden" in l for l in logs)

def test_full_pipeline_on_synthetic_report():
    pdf_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../data/synthetic_reports/LAB-001.pdf"))
    assert os.path.exists(pdf_path)
    with open(pdf_path, "rb") as f:
        response = client.post("/api/reports/analyze", files={"file": ("LAB-001.pdf", f, "application/pdf")})
    assert response.status_code == 200
    data = response.json()
    assert data["report_id"] == "LAB-001"
    assert len(data["biomarkers"]) == 5
    assert data["critical_alert"]["triggered"] is False
    assert len(data["explanations_en"]) == 5
    assert len(data["explanations_hi"]) == 5
