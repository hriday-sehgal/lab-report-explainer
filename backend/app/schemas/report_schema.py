from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class FlagType(str, Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL_LOW = "critical_low"
    CRITICAL_HIGH = "critical_high"
    UNKNOWN = "unknown"

class NextStepType(str, Enum):
    FOLLOW_UP_TEST_PACKAGE = "follow_up_test_package"
    DOCTOR_CONSULT = "doctor_consult"
    NO_ACTION = "no_action"

class ReferenceRange(BaseModel):
    low: Optional[float] = Field(None, description="Lower reference bound")
    high: Optional[float] = Field(None, description="Upper reference bound")
    text_range: Optional[str] = Field(None, description="Original unparsed reference range text")

class ExtractedBiomarkerRaw(BaseModel):
    """Raw extraction from PDF text via LLM"""
    item_id: str
    test_name: str
    value: float
    unit: str
    reference_low: Optional[float] = None
    reference_high: Optional[float] = None
    reference_text: Optional[str] = None

class LabBiomarker(BaseModel):
    """Schema-validated biomarker with deterministically computed flag"""
    item_id: str
    test_name: str
    value: float
    unit: str
    reference_range: ReferenceRange
    flag: FlagType = FlagType.UNKNOWN
    is_critical: bool = False
    clinical_note: Optional[str] = None

class ExplanationItem(BaseModel):
    sentence_id: str
    language: str = Field(..., description="en | hi")
    text: str
    evidence_item_ids: List[str]
    severity: str = "routine"  # routine | attention | urgent

class CriticalAlert(BaseModel):
    triggered: bool = False
    critical_biomarkers: List[str] = []
    message_en: Optional[str] = None
    message_hi: Optional[str] = None
    urgent_action_required: bool = False

class NextStepGuidance(BaseModel):
    action: NextStepType
    reason_en: str
    reason_hi: str
    evidence_item_ids: List[str]

class PatientMetadata(BaseModel):
    name: Optional[str] = "Unknown"
    age: Optional[int] = None
    gender: Optional[str] = None
    patient_id: Optional[str] = None
    collection_date: Optional[str] = None
    referred_by: Optional[str] = None

class ProcessingMetadata(BaseModel):
    latency_seconds: float
    model_used: str
    execution_mode: str = "LIVE_LLM"  # LIVE_LLM | DETERMINISTIC_FALLBACK
    is_live_llm: bool = False
    engine_label: str = "Deterministic Clinical Engine"
    input_tokens: int = 0
    output_tokens: int = 0
    estimated_cost_inr: float = 0.0

class LabReportAnalysis(BaseModel):
    report_id: str
    report_type: str
    panel_name: str
    patient_metadata: PatientMetadata
    biomarkers: List[LabBiomarker]
    critical_alert: CriticalAlert
    explanations_en: List[ExplanationItem]
    explanations_hi: List[ExplanationItem]
    next_step: NextStepGuidance
    disclaimer_en: str
    disclaimer_hi: str
    processing_metadata: ProcessingMetadata
