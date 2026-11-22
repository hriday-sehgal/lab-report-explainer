"""
Deterministic Clinical Panic / Critical Value Thresholds
Based on standard emergency clinical laboratory guidelines:
- CAP (College of American Pathologists) Panic Value List
- AIIMS Clinical Chemistry Critical Values Protocol
"""

from typing import Dict, Any, Optional

CRITICAL_THRESHOLDS: Dict[str, Dict[str, Any]] = {
    "hemoglobin": {
        "critical_low": 7.0,
        "critical_high": 20.0,
        "unit": "g/dL",
        "condition_en": "Severe life-threatening anemia (low) or polycythemia (high)",
        "condition_hi": "गंभीर जानलेवा एनीमिया (अत्यधिक कमी) या पॉलीसिथीमिया"
    },
    "platelet count": {
        "critical_low": 20000.0,
        "critical_high": 1000000.0,
        "unit": "/uL",
        "condition_en": "Severe thrombocytopenia risk of spontaneous hemorrhage (low) or severe thrombocytosis (high)",
        "condition_hi": "प्लेटलेट्स की अत्यधिक कमी (अचानक रक्तस्राव का जोखिम)"
    },
    "total leukocyte count (wbc)": {
        "critical_low": 2000.0,
        "critical_high": 30000.0,
        "unit": "/uL",
        "condition_en": "Severe neutropenia / immunocompromise (low) or hyperleukocytosis (high)",
        "condition_hi": "सफेद रक्त कोशिकाओं की अत्यधिक कमी या अत्यधिक वृद्धि"
    },
    "total bilirubin": {
        "critical_low": None,
        "critical_high": 15.0,
        "unit": "mg/dL",
        "condition_en": "Critical hyperbilirubinemia with risk of acute encephalopathy / severe hepatic injury",
        "condition_hi": "अत्यधिक उच्च बिलीरुबिन (गंभीर पीलिया एवं यकृत क्षति का जोखिम)"
    },
    "thyroid stimulating hormone (tsh)": {
        "critical_low": 0.05,
        "critical_high": 50.0,
        "unit": "uIU/mL",
        "condition_en": "Thyrotoxic storm risk (low) or myxedema coma risk (high)",
        "condition_hi": "थायराइड की अत्यधिक गंभीर असामान्यता"
    },
    "potassium": {
        "critical_low": 2.8,
        "critical_high": 6.2,
        "unit": "mEq/L",
        "condition_en": "Fatal cardiac arrhythmia risk",
        "condition_hi": "हृदय गति के गंभीर जोखिम (पोटेशियम असंतुलन)"
    }
}

def evaluate_critical_value(test_name: str, value: float) -> Optional[Dict[str, Any]]:
    """
    Check if a test and numeric value match any critical threshold.
    Normalizes test name for robust lookup and guards against false positives
    (e.g., distinguishing blood Hemoglobin from glycated HbA1c).
    """
    clean_name = test_name.lower().strip()
    
    # Critical Guard: HbA1c / Glycated Hemoglobin is a percentage and must NOT
    # match whole-blood Hemoglobin panic rules (< 7.0 g/dL).
    if "hba1c" in clean_name or "glycated" in clean_name:
        return None
    
    # Match alias
    matched_key = None
    for k in CRITICAL_THRESHOLDS:
        if k in clean_name or clean_name in k:
            matched_key = k
            break
            
    if not matched_key:
        return None
        
    rule = CRITICAL_THRESHOLDS[matched_key]
    low_thresh = rule.get("critical_low")
    high_thresh = rule.get("critical_high")
    
    if low_thresh is not None and value < low_thresh:
        return {
            "is_critical": True,
            "flag": "critical_low",
            "threshold": low_thresh,
            "direction": "low",
            "condition_en": rule["condition_en"],
            "condition_hi": rule["condition_hi"]
        }
        
    if high_thresh is not None and value > high_thresh:
        return {
            "is_critical": True,
            "flag": "critical_high",
            "threshold": high_thresh,
            "direction": "high",
            "condition_en": rule["condition_en"],
            "condition_hi": rule["condition_hi"]
        }
        
    return None
