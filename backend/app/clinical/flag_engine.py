"""
Deterministic Reference Range & Flag Engine
Compares observed test values against laboratory-specific biological reference intervals.
Zero LLM arithmetic - 100% deterministic code.
"""

from typing import Tuple, Optional
from backend.app.schemas.report_schema import FlagType, ReferenceRange
from backend.app.clinical.critical_values import evaluate_critical_value

def calculate_biomarker_flag(
    test_name: str,
    value: float,
    reference_range: ReferenceRange
) -> Tuple[FlagType, bool, Optional[str]]:
    """
    Returns: (flag, is_critical, clinical_note)
    Priority:
    1. Critical Panic Evaluation
    2. Reference Interval Comparison (low / normal / high)
    3. Unknown if range is missing
    """
    # 1. First check critical panic thresholds
    critical_res = evaluate_critical_value(test_name, value)
    if critical_res and critical_res["is_critical"]:
        flag = FlagType.CRITICAL_LOW if critical_res["direction"] == "low" else FlagType.CRITICAL_HIGH
        return flag, True, critical_res["condition_en"]
        
    # 2. Check reference range if present
    low = reference_range.low
    high = reference_range.high
    
    # If range is explicitly 0.0 - 0.0, it is an uncalibrated / qualitative marker
    if low == 0.0 and high == 0.0:
        return FlagType.NORMAL, False, "Reference range uncalibrated or qualitative"

    if low is not None and high is not None:
        if value < low:
            return FlagType.LOW, False, f"Below standard reference lower limit ({low})"
        elif value > high:
            return FlagType.HIGH, False, f"Above standard reference upper limit ({high})"
        else:
            return FlagType.NORMAL, False, "Within biological reference interval"
            
    elif low is not None and high is None:
        if value < low:
            return FlagType.LOW, False, f"Below reference threshold ({low})"
        return FlagType.NORMAL, False, "Above reference threshold"
        
    elif high is not None and low is None:
        if value > high:
            return FlagType.HIGH, False, f"Above upper limit ({high})"
        return FlagType.NORMAL, False, "Within acceptable limit"
        
    return FlagType.UNKNOWN, False, "Reference range not specified"
