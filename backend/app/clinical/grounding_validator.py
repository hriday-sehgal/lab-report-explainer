"""
Grounding Verification Engine
Verifies that every explanation statement:
1. Points to one or more valid, present biomarker item_ids.
2. Contains no ungrounded claims or hallucinated evidence.
3. Contains no forbidden diagnostic claims (e.g. 'You have anemia', 'You have diabetes').
"""

import re
from typing import List, Tuple
from backend.app.schemas.report_schema import ExplanationItem, LabBiomarker

FORBIDDEN_DIAGNOSES = [
    r"\byou have (?:diabetes|anemia|cancer|leukemia|liver disease|jaundice|hypothyroidism|hyperthyroidism)\b",
    r"\byou are suffering from\b",
    r"\byou should take (?:medication|tablets|drugs|insulin|metformin|antibiotics|paracetamol)\b",
    r"\bdiagnosis:\b",
    r"\bprescribe\b"
]

def audit_and_filter_explanations(
    explanations: List[ExplanationItem],
    biomarkers: List[LabBiomarker]
) -> Tuple[List[ExplanationItem], float, List[str]]:
    """
    Validates explanations against evidence grounding and safety rules.
    Returns:
    (valid_explanations, grounding_score_percent, audit_log)
    """
    valid_biomarker_ids = {b.item_id for b in biomarkers}
    passed_items: List[ExplanationItem] = []
    audit_logs: List[str] = []
    
    total_count = len(explanations)
    if total_count == 0:
        return [], 100.0, ["No explanations provided"]
        
    grounded_count = 0
    
    for exp in explanations:
        text_lower = exp.text.lower()
        
        # 1. Check for forbidden diagnostic language
        has_unsafe_language = False
        for pattern in FORBIDDEN_DIAGNOSES:
            if re.search(pattern, text_lower):
                has_unsafe_language = True
                audit_logs.append(f"REJECTED sentence '{exp.sentence_id}': Contained forbidden diagnosis/prescription pattern '{pattern}'")
                break
                
        if has_unsafe_language:
            continue
            
        # 2. Check evidence citation validity
        valid_citations = [ev_id for ev_id in exp.evidence_item_ids if ev_id in valid_biomarker_ids]
        if not valid_citations:
            audit_logs.append(f"REJECTED sentence '{exp.sentence_id}': Evidence IDs {exp.evidence_item_ids} not found in extracted biomarkers")
            continue
            
        grounded_count += 1
        exp.evidence_item_ids = valid_citations
        passed_items.append(exp)
        
    grounding_score = (grounded_count / total_count) * 100.0 if total_count > 0 else 100.0
    return passed_items, grounding_score, audit_logs
