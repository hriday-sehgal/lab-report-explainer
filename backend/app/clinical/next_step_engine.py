"""
Deterministic Next-Step Engine
Selects strictly one action from the closed enum:
- follow_up_test_package
- doctor_consult
- no_action
"""

from typing import List
from backend.app.schemas.report_schema import (
    NextStepType,
    NextStepGuidance,
    LabBiomarker,
    FlagType
)

def determine_next_step(biomarkers: List[LabBiomarker], has_critical: bool) -> NextStepGuidance:
    abnormal_items = [
        b for b in biomarkers 
        if b.flag in (FlagType.LOW, FlagType.HIGH, FlagType.CRITICAL_LOW, FlagType.CRITICAL_HIGH)
    ]
    
    # 1. Critical values override everything -> Doctor Consult (Urgent)
    if has_critical:
        critical_items = [b for b in biomarkers if b.is_critical]
        ev_ids = [b.item_id for b in critical_items]
        return NextStepGuidance(
            action=NextStepType.DOCTOR_CONSULT,
            reason_en="One or more biomarkers exceed critical panic thresholds. Immediate medical consultation is required.",
            reason_hi="एक या अधिक परीक्षण परिणाम गंभीर सीमा पार कर चुके हैं। तत्काल डॉक्टर से परामर्श लेना अनिवार्य है।",
            evidence_item_ids=ev_ids
        )
        
    # 2. No abnormal items -> No action needed
    if not abnormal_items:
        return NextStepGuidance(
            action=NextStepType.NO_ACTION,
            reason_en="All tested biomarkers fall within the laboratory's standard reference intervals. Routine wellness maintenance is advised.",
            reason_hi="सभी जांच परिणाम लैब द्वारा निर्धारित सामान्य सीमा के भीतर हैं। नियमित स्वास्थ्य देखभाल जारी रखें।",
            evidence_item_ids=[b.item_id for b in biomarkers[:3]] if biomarkers else []
        )
        
    # 3. Check for isolated mild abnormalities that suit a follow-up test package
    # (e.g. isolated elevated triglycerides or mild borderline lipid marker)
    if len(abnormal_items) == 1:
        single = abnormal_items[0]
        test_lower = single.test_name.lower()
        if "triglyceride" in test_lower or "cholesterol" in test_lower:
            return NextStepGuidance(
                action=NextStepType.FOLLOW_UP_TEST_PACKAGE,
                reason_en=f"A single isolated elevation was found in {single.test_name} ({single.value} {single.unit}). We suggest scheduling a 3-month follow-up lipid profile recheck.",
                reason_hi=f"केवल {single.test_name} ({single.value} {single.unit}) में असामान्यता पाई गई है। 3 महीने बाद दोबारा जांच (फॉलो-अप टेस्ट) कराने का सुझाव है।",
                evidence_item_ids=[single.item_id]
            )
            
    # 4. Standard abnormal results -> Doctor Consult
    ev_ids = [b.item_id for b in abnormal_items]
    names = ", ".join([b.test_name for b in abnormal_items[:3]])
    return NextStepGuidance(
        action=NextStepType.DOCTOR_CONSULT,
        reason_en=f"Values outside reference intervals were observed for {names}. A consultation with a qualified doctor is recommended for clinical review.",
        reason_hi=f"{names} के परिणाम सामान्य सीमा से बाहर हैं। चिकित्सकीय समीक्षा के लिए योग्य डॉक्टर से परामर्श लें।",
        evidence_item_ids=ev_ids
    )
