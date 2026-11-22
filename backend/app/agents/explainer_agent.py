"""
Grounded Bilingual Explanation Agent
Generates plain-language medical explanations in English and Hindi.
Mandates:
- Every statement must reference one or more extracted biomarker IDs.
- Strict non-diagnostic guardrails (explain biomarkers without diagnosing conditions).
- Critical panic value alert generation.
- Full offline deterministic knowledge fallback for reproducible evaluations and CI.
"""

import time
import json
from typing import List, Tuple, Dict, Any
from google import genai
from google.genai import types

from backend.app.config import settings
from backend.app.schemas.report_schema import (
    LabBiomarker,
    ExplanationItem,
    CriticalAlert,
    FlagType
)

EXPLAINER_SYSTEM_PROMPT = """You are a compassionate, patient-facing healthcare communication assistant for diagnostics labs.
Your objective is to explain blood test results in clear, non-intimidating language in both English and Hindi.

STRICT MEDICAL SAFETY RULES:
1. NO DIAGNOSIS: Never say "You have diabetes", "You have anemia", "You have kidney failure", or "You are suffering from...".
   Always state the biomarker observation: "Your Hemoglobin is lower than the reference interval," or "Your HbA1c is above the standard range."
2. NO PRESCRIPTIONS: Never advise taking medication, dosages, or stopping treatments.
3. GROUNDING MANDATE: Every explanation sentence must cite the exact `evidence_item_ids` that prove it.
4. TONE: Informative, objective, calming, and clinically responsible.

You will receive a list of validated biomarkers with their test names, values, units, reference intervals, and flags.

Return a JSON object with this exact structure:
{
  "critical_alert": {
    "triggered": true/false,
    "message_en": "...",
    "message_hi": "..."
  },
  "explanations_en": [
    {
      "sentence_id": "EXP_EN_1",
      "language": "en",
      "text": "Your Hemoglobin is 14.8 g/dL, which is within the normal reference range of 13.0 to 17.0 g/dL. Hemoglobin is the protein in red blood cells that carries oxygen to your organs.",
      "evidence_item_ids": ["CBC_HGB_1"],
      "severity": "routine"
    }
  ],
  "explanations_hi": [
    {
      "sentence_id": "EXP_HI_1",
      "language": "hi",
      "text": "आपका हीमोग्लोबिन 14.8 g/dL है, जो सामान्य सीमा 13.0 से 17.0 g/dL के बीच है। हीमोग्लोबिन लाल रक्त कोशिकाओं में पाया जाने वाला प्रोटीन है जो शरीर में ऑक्सीजन पहुंचाता है।",
      "evidence_item_ids": ["CBC_HGB_1"],
      "severity": "routine"
    }
  ]
}
"""

# Clinical Biomarker Educational Reference Knowledge Base (Used for offline / guaranteed grounded generation)
BIOMARKER_EDUCATIONAL_KB = {
    "hemoglobin": {
        "role_en": "Hemoglobin is the vital protein in red blood cells responsible for transporting oxygen throughout your body.",
        "role_hi": "हीमोग्लोबिन लाल रक्त कोशिकाओं में मौजूद मुख्य प्रोटीन है जो पूरे शरीर में ऑक्सीजन पहुंचाने का काम करता है।",
        "low_en": "Below the laboratory reference range. Lower levels can indicate reduced oxygen-carrying capacity in the bloodstream.",
        "low_hi": "लैब की सामान्य सीमा से कम है। इसका स्तर कम होने पर शरीर में ऑक्सीजन का प्रवाह धीमा हो सकता है।",
        "high_en": "Above standard reference limits, which may reflect dehydration or increased red blood cell concentration.",
        "high_hi": "सामान्य सीमा से अधिक है, जो शरीर में पानी की कमी या लाल रक्त कोशिकाओं की अधिकता का संकेत हो सकता है।"
    },
    "rbc count": {
        "role_en": "Red Blood Cell count measures the number of oxygen-carrying cells in your blood.",
        "role_hi": "आरबीसी काउंट (RBC) आपके खून में ऑक्सीजन ले जाने वाली लाल रक्त कोशिकाओं की संख्या को दर्शाता है।",
        "low_en": "Lower than expected for standard healthy ranges.",
        "low_hi": "मानक सामान्य स्तर से कम पाया गया है।",
        "high_en": "Higher than reference limits.",
        "high_hi": "मानक सामान्य स्तर से अधिक पाया गया है।"
    },
    "packed cell volume (pcv)": {
        "role_en": "PCV measures the proportion of blood volume made up of red blood cells.",
        "role_hi": "पीसीवी (PCV) खून के कुल आयतन में लाल रक्त कोशिकाओं के प्रतिशत को मापता है।",
        "low_en": "Indicates a lower concentration of circulating red cells.",
        "low_hi": "खून में लाल रक्त कोशिकाओं के कम अनुपात को दर्शाता है।",
        "high_en": "Indicates hemoconcentration or elevated red cell mass.",
        "high_hi": "खून में लाल रक्त कोशिकाओं के अधिक अनुपात को दर्शाता है।"
    },
    "total leukocyte count (wbc)": {
        "role_en": "White blood cells are the core component of your immune system that defend against infections.",
        "role_hi": "सफेद रक्त कोशिकाएं (WBC) रोग प्रतिरोधक क्षमता का मुख्य हिस्सा हैं जो संक्रमण से लड़ती हैं।",
        "low_en": "Lower than standard reference limits.",
        "low_hi": "सामान्य सीमा से कम है, जो कमजोर प्रतिरक्षा प्रतिक्रिया से संबंधित हो सकता है।",
        "high_en": "Elevated above normal limits, frequently observed as an active immune response to inflammation or infection.",
        "high_hi": "सामान्य सीमा से अधिक है, जो अक्सर शरीर में किसी सूजन या संक्रमण से लड़ने की प्रतिक्रिया में बढ़ता है।"
    },
    "platelet count": {
        "role_en": "Platelets are specialized blood cell fragments essential for normal blood clotting and healing.",
        "role_hi": "प्लेटलेट्स खून के थक्के जमाने (रक्त का बहना रोकने) और घाव भरने में महत्वपूर्ण भूमिका निभाते हैं।",
        "low_en": "Reduced platelet count below reference parameters, which can affect clotting efficiency.",
        "low_hi": "सामान्य सीमा से कम है, जिससे रक्त का थक्का बनने की प्रक्रिया प्रभावित हो सकती है।",
        "high_en": "Elevated above standard reference intervals.",
        "high_hi": "सामान्य सीमा से अधिक पाया गया है।"
    },
    "total cholesterol": {
        "role_en": "Total cholesterol measures the cumulative circulating sterols vital for cell membranes and hormone synthesis.",
        "role_hi": "टोटल कोलेस्ट्रॉल शरीर में कोशिकाओं और हार्मोन्स के निर्माण के लिए आवश्यक वसा का स्तर मापता है।",
        "low_en": "Below reference parameters.",
        "low_hi": "सामान्य सीमा से कम है।",
        "high_en": "Elevated above desirable clinical cutoffs, which is an important metric for cardiovascular wellness.",
        "high_hi": "वांछित सामान्य स्तर से अधिक है, जिस पर हृदय के स्वास्थ्य के संदर्भ में ध्यान देने की आवश्यकता है।"
    },
    "hdl cholesterol": {
        "role_en": "HDL is often referred to as good cholesterol as it helps carry excess cholesterol back to the liver for clearance.",
        "role_hi": "एचडीएल (HDL) को 'अच्छा कोलेस्ट्रॉल' कहा जाता है क्योंकि यह नसों से अतिरिक्त वसा को साफ करता है।",
        "low_en": "Below the optimal protective reference threshold.",
        "low_hi": "सुरक्षात्मक सामान्य सीमा से कम है।",
        "high_en": "Within optimal or high protective reference thresholds.",
        "high_hi": "सुरक्षात्मक सामान्य सीमा के अनुकूल है।"
    },
    "ldl cholesterol": {
        "role_en": "LDL carries cholesterol to tissues; managing optimal LDL levels supports healthy vascular flow.",
        "role_hi": "एलडीएल (LDL) को आमतौर पर रक्त वाहिकाओं में वसा जमा करने वाले कोलेस्ट्रॉल के रूप में जाना जाता है।",
        "low_en": "Within safe low bounds.",
        "low_hi": "सामान्य और सुरक्षित स्तर पर है।",
        "high_en": "Above standard clinical cutoffs. Elevated LDL can contribute to arterial lipid accumulation over time.",
        "high_hi": "अनुशंसित सीमा से अधिक है, जो लंबे समय में धमनियों के स्वास्थ्य को प्रभावित कर सकता है।"
    },
    "triglycerides": {
        "role_en": "Triglycerides are the predominant form of dietary and circulating energy storage fats.",
        "role_hi": "ट्राइग्लिसराइड्स शरीर में ऊर्जा के रूप में जमा होने वाली मुख्य वसा (फैट) हैं।",
        "low_en": "Within standard parameters.",
        "low_hi": "सामान्य सीमा के भीतर है।",
        "high_en": "Above standard fasting reference thresholds. Elevated levels warrant dietary and lifestyle review.",
        "high_hi": "फास्टिंग सामान्य सीमा से अधिक है, जिसके लिए खानपान और जीवनशैली पर ध्यान देना आवश्यक है।"
    },
    "hba1c": {
        "role_en": "HbA1c measures the percentage of glycated hemoglobin, reflecting average blood glucose over the preceding 2 to 3 months.",
        "role_hi": "एचबीए1सी (HbA1c) पिछले 2 से 3 महीनों के औसत रक्त शर्करा (ब्लड शुगर) के स्तर को दर्शाता है।",
        "low_en": "Within acceptable normal lower bounds.",
        "low_hi": "स्वीकार्य सामान्य सीमा के भीतर है।",
        "high_en": "Elevated above standard non-diabetic reference thresholds (4.0 - 5.6%), reflecting elevated glycemic exposure.",
        "high_hi": "सामान्य गैर-मधुमेह सीमा (4.0 - 5.6%) से अधिक है, जो पिछले 3 महीनों में शुगर का स्तर अधिक रहने का संकेत है।"
    },
    "tsh": {
        "role_en": "TSH (Thyroid Stimulating Hormone) is secreted by the pituitary to regulate thyroid hormone production and metabolic rate.",
        "role_hi": "टीएसएच (TSH) मस्तिष्क द्वारा उत्पादित हार्मोन है जो थायराइड ग्रंथि और मेटाबॉलिज्म को नियंत्रित करता है।",
        "low_en": "Below reference limits, indicating that the thyroid regulation pathway is suppressed.",
        "low_hi": "सामान्य सीमा से कम है, जो थायराइड ग्रंथि के अधिक सक्रिय होने का संकेत दे सकता है।",
        "high_en": "Elevated above reference limits, signaling that the body is signaling for additional thyroid hormone synthesis.",
        "high_hi": "सामान्य सीमा से अधिक है, जो संकेत देता है कि थायराइड ग्रंथि सुस्त हो सकती है।"
    },
    "alt/sgpt": {
        "role_en": "ALT is an enzyme concentrated within liver cells involved in cellular energy metabolism.",
        "role_hi": "एएलटी (ALT/SGPT) लिवर की कोशिकाओं में पाया जाने वाला एक महत्वपूर्ण एंजाइम है।",
        "low_en": "Within reference parameters.",
        "low_hi": "सामान्य सीमा में है।",
        "high_en": "Elevated above reference intervals, indicating increased leakage of cellular liver enzymes.",
        "high_hi": "सामान्य सीमा से अधिक है, जो लिवर की कोशिकाओं पर तनाव या सूजन की ओर संकेत करता है।"
    },
    "ast/sgot": {
        "role_en": "AST is an enzyme present in hepatic and muscular tissues involved in amino acid processing.",
        "role_hi": "एएसटी (AST/SGOT) लिवर और मांसपेशियों में पाया जाने वाला एंजाइम है।",
        "low_en": "Within standard parameters.",
        "low_hi": "सामान्य सीमा में है।",
        "high_en": "Elevated above standard reference intervals.",
        "high_hi": "सामान्य सीमा से अधिक पाया गया है।"
    },
    "total bilirubin": {
        "role_en": "Total Bilirubin is the pigment produced during normal breakdown of red blood cells, processed by the liver.",
        "role_hi": "बिलीरुबिन लाल रक्त कोशिकाओं के प्राकृतिक टूटने पर बनने वाला पीला पदार्थ है, जिसे लिवर साफ करता है।",
        "low_en": "Within normal physiological range.",
        "low_hi": "सामान्य शारीरिक सीमा के भीतर है।",
        "high_en": "Above standard reference limits, which can be clinically associated with yellowish discoloration (jaundice).",
        "high_hi": "सामान्य सीमा से अधिक है, जो शरीर में पीलापन (पीलिया के लक्षण) का कारण बन सकता है।"
    }
}

class ExplainerAgent:
    def __init__(self, api_key: str = None):
        self.api_key = api_key or settings.gemini_api_key
        self.client = genai.Client(api_key=self.api_key) if self.api_key else None

    def explain_biomarkers(
        self,
        biomarkers: List[LabBiomarker],
        has_critical: bool
    ) -> Tuple[CriticalAlert, List[ExplanationItem], List[ExplanationItem], Dict[str, Any]]:
        """
        Produces bilingual explanations and critical alert status.
        Returns: (critical_alert, explanations_en, explanations_hi, perf_metadata)
        """
        start_time = time.perf_counter()
        
        # 1. Evaluate Critical Alert
        critical_items = [b for b in biomarkers if b.is_critical]
        crit_alert = CriticalAlert()
        if critical_items:
            names_en = ", ".join([f"{b.test_name} ({b.value} {b.unit})" for b in critical_items])
            names_hi = ", ".join([f"{b.test_name}" for b in critical_items])
            crit_alert.triggered = True
            crit_alert.critical_biomarkers = [b.item_id for b in critical_items]
            crit_alert.urgent_action_required = True
            crit_alert.message_en = (
                f"URGENT CLINICAL ATTENTION REQUIRED: Predefined critical panic value(s) detected for {names_en}. "
                "Please contact your attending physician or visit an emergency care facility immediately. Do not delay."
            )
            crit_alert.message_hi = (
                f"तत्काल चिकित्सकीय ध्यान आवश्यक है: {names_hi} में गंभीर आपातकालीन स्तर पाया गया है। "
                "कृपया तुरंत अपने डॉक्टर से संपर्क करें या नजदीकी आपातकालीन चिकित्सा केंद्र जाएं।"
            )

        # 2. Try Gemini LLM if client is available (at most 2 cheap lightweight models, 1 attempt each)
        if self.client:
            models_to_try = [settings.gemini_model, "gemini-2.0-flash-lite"]
            unique_models = []
            for m in models_to_try:
                if m and m not in unique_models:
                    unique_models.append(m)
            
            biomarkers_payload = [
                {
                    "item_id": b.item_id,
                    "test_name": b.test_name,
                    "value": b.value,
                    "unit": b.unit,
                    "reference_low": b.reference_range.low,
                    "reference_high": b.reference_range.high,
                    "flag": b.flag.value,
                    "is_critical": b.is_critical
                }
                for b in biomarkers
            ]
            
            prompt = (
                f"{EXPLAINER_SYSTEM_PROMPT}\n\n"
                f"INPUT BIOMARKERS:\n{json.dumps(biomarkers_payload, indent=2)}"
            )
            
            for model_name in unique_models[:2]:
                try:
                    response = self.client.models.generate_content(
                        model=model_name,
                        contents=prompt,
                        config=types.GenerateContentConfig(
                            temperature=0.2,
                            response_mime_type="application/json"
                        )
                    )
                    latency = time.perf_counter() - start_time
                    
                    # Clean markdown code fences if present
                    resp_text = (response.text or "").strip()
                    resp_text = re.sub(r"^```(?:json)?\s*", "", resp_text, flags=re.MULTILINE)
                    resp_text = re.sub(r"\s*```$", "", resp_text, flags=re.MULTILINE)
                    
                    parsed_res = json.loads(resp_text)
                    
                    raw_en = parsed_res.get("explanations_en", [])
                    raw_hi = parsed_res.get("explanations_hi", [])
                    if not raw_en or not raw_hi:
                        continue
                        
                    exp_en = [ExplanationItem(**item) for item in raw_en]
                    exp_hi = [ExplanationItem(**item) for item in raw_hi]
                    
                    usage = getattr(response, "usage_metadata", None)
                    in_tokens = getattr(usage, "prompt_token_count", 950) if usage else 950
                    out_tokens = getattr(usage, "candidates_token_count", 650) if usage else 650
                    
                    cost_usd = (in_tokens / 1_000_000 * settings.input_cost_per_m_tokens) + \
                               (out_tokens / 1_000_000 * settings.output_cost_per_m_tokens)
                    cost_inr = cost_usd * settings.usd_to_inr
                    
                    perf = {
                        "latency_seconds": round(latency, 3),
                        "model_used": model_name,
                        "execution_mode": "LIVE_LLM",
                        "is_live_llm": True,
                        "engine_label": f"Live Gemini LLM ({model_name})",
                        "input_tokens": in_tokens,
                        "output_tokens": out_tokens,
                        "estimated_cost_inr": round(cost_inr, 4)
                    }
                    return crit_alert, exp_en, exp_hi, perf
                except Exception as e:
                    print(f"[ExplainerAgent] Lightweight model '{model_name}' failed: {e}. Trying fallback...")
                    continue
                
        # 3. Deterministic Grounded Generation Fallback (Zero network latency, 100% grounded)
        exp_en, exp_hi, perf = self._deterministic_explain(biomarkers, start_time)
        return crit_alert, exp_en, exp_hi, perf

    def _deterministic_explain(
        self,
        biomarkers: List[LabBiomarker],
        start_time: float
    ) -> Tuple[List[ExplanationItem], List[ExplanationItem], Dict[str, Any]]:
        latency = time.perf_counter() - start_time
        explanations_en: List[ExplanationItem] = []
        explanations_hi: List[ExplanationItem] = []
        
        for i, b in enumerate(biomarkers, start=1):
            name_lower = b.test_name.lower()
            matched_kb = None
            for k in BIOMARKER_EDUCATIONAL_KB:
                if k in name_lower or name_lower in k:
                    matched_kb = BIOMARKER_EDUCATIONAL_KB[k]
                    break
                    
            role_en = matched_kb["role_en"] if matched_kb else f"{b.test_name} is an important diagnostic biomarker evaluated in laboratory blood panels."
            role_hi = matched_kb["role_hi"] if matched_kb else f"{b.test_name} आपके रक्त की एक महत्वपूर्ण जांच है।"
            
            ref_str = f"{b.reference_range.low} - {b.reference_range.high} {b.unit}" if b.reference_range.low is not None else "specified laboratory reference limits"
            
            if b.flag == FlagType.NORMAL:
                status_desc_en = f"is {b.value} {b.unit}, which falls comfortably within the normal reference range of {ref_str}."
                status_desc_hi = f"{b.value} {b.unit} है, जो सामान्य मानक सीमा ({ref_str}) के बिल्कुल अनुकूल है।"
                severity = "routine"
            elif b.flag in (FlagType.LOW, FlagType.CRITICAL_LOW):
                obs = matched_kb["low_en"] if matched_kb else "is below standard laboratory reference limits."
                obs_hi = matched_kb["low_hi"] if matched_kb else "सामान्य सीमा से कम है।"
                status_desc_en = f"is {b.value} {b.unit}, which is lower than the reference range of {ref_str}. {obs}"
                status_desc_hi = f"{b.value} {b.unit} है, जो सामान्य सीमा ({ref_str}) से कम है। {obs_hi}"
                severity = "urgent" if b.is_critical else "attention"
            elif b.flag in (FlagType.HIGH, FlagType.CRITICAL_HIGH):
                obs = matched_kb["high_en"] if matched_kb else "is above standard laboratory reference limits."
                obs_hi = matched_kb["high_hi"] if matched_kb else "सामान्य सीमा से अधिक है।"
                status_desc_en = f"is {b.value} {b.unit}, which is higher than the reference range of {ref_str}. {obs}"
                status_desc_hi = f"{b.value} {b.unit} है, जो सामान्य सीमा ({ref_str}) से अधिक है। {obs_hi}"
                severity = "urgent" if b.is_critical else "attention"
            else:
                status_desc_en = f"is {b.value} {b.unit}."
                status_desc_hi = f"{b.value} {b.unit} है।"
                severity = "routine"

            # Construct grounded sentences with explicit citation
            text_en = f"Your {b.test_name} {status_desc_en} {role_en}"
            text_hi = f"आपका {b.test_name} {status_desc_hi} {role_hi}"
            
            explanations_en.append(ExplanationItem(
                sentence_id=f"EXP_EN_{i}",
                language="en",
                text=text_en,
                evidence_item_ids=[b.item_id],
                severity=severity
            ))
            explanations_hi.append(ExplanationItem(
                sentence_id=f"EXP_HI_{i}",
                language="hi",
                text=text_hi,
                evidence_item_ids=[b.item_id],
                severity=severity
            ))

        perf = {
            "latency_seconds": round(latency, 4),
            "model_used": "deterministic-clinical-kb",
            "execution_mode": "DETERMINISTIC_FALLBACK",
            "is_live_llm": False,
            "engine_label": "Deterministic Clinical Engine (Safe Offline Mode)",
            "input_tokens": 0,
            "output_tokens": 0,
            "estimated_cost_inr": 0.0
        }
        return explanations_en, explanations_hi, perf
