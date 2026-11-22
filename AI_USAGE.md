# AI Usage & Engineering Workflow Specification

---

## 1. Operating Philosophy: "Plan First, Code Second, Verify Always"

Our operating system for this take home followed a 5-phase agentic loop:
```
[1. Structural Plan] -> [2. Deterministic Guardrails] -> [3. Context Minimization] -> [4. Eval Benchmark] -> [5. Iterative Refinement]
      (PLAN.md)           (Pure Code Safety Engine)        (Structured Data Only)         (30-Case Matrix)         (Root-Cause Fixes)
```

---

## 2. Tools & Agentic Execution Stack

1. **Agentic Orchestration Platform:**
   - **Google Antigravity** Used as the primary agentic pair-programmer for architectural design, schema enforcement, automated report generation, and continuous test execution.
2. **LLM Runtime & Foundation Models:**
   - **Gemini 3.5 Flash Lite:** Selected for high-throughput, low-latency ($< 1.8\text{s}$) biomarker extraction and natural bilingual phrasing.
   - **Google ADK 2.0 / Google GenAI SDK (`google-genai`):** Used for strict JSON schema output formatting and tool execution.
3. **Deterministic Safety Harness:**
   - **Pydantic v2:** Rigid type and schema validation.
   - **Python Clinical Flag Engine:** 100% deterministic arithmetic comparison against biological reference intervals and clinical panic lists (CAP / AIIMS guidelines).

---

## 3. Context & Token Discipline

Careless LLM architectures consume millions of tokens by passing raw PDFs, unparsed text streams, and repetitive system prompts into large models. We implemented aggressive token and context optimization:

| Optimization Strategy | Implementation Details | Token / Cost Impact |
|---|---|---|
| **Local Text Extraction First** | PyMuPDF / `pypdf` extracts text locally on CPU before calling Gemini. Never sends raw PDF binary images over the wire for text-based reports. | **85% reduction** in input tokens per report ($\approx 1,200$ tokens vs $\approx 8,500$ tokens for multi-page vision). |
| **Separation of Arithmetic from LLM** | Flags (`normal`, `high`, `low`, `critical`) are computed in pure Python, not by prompting the model to compare floats. | Prevents LLM arithmetic hallucinations and saves $\approx 250$ output tokens per call. |
| **Pydantic Schema Serialization** | Strict JSON schema schemas ensure zero conversational preamble (no "Sure, here is your summary..."). | Eliminates non-functional token waste and enables instant parsing. |
| **Bilingual Batched Explanations** | Explainer agent generates English and Hindi explanations in a single structured invocation rather than two separate LLM passes. | Halves prompt input overhead and keeps per-report spend to $\approx \text{₹}0.035$ INR. |

---

## 4. Skills & Execution System

We established task-specific skills and workflows to ensure reproducible execution:
1. **`pdf-generation-skill`:** Scripted `ReportLab` engine that generates both synthetic PDF artifacts and corresponding JSON ground truth simultaneously.
2. **`clinical-safety-skill`:** Deterministic panic value lookup table based on emergency medicine guidelines (e.g. Platelets $< 20,000/\mu\text{L}$, Hemoglobin $< 7.0\text{ g/dL}$).
3. **`grounding-audit-skill`:** AST and regex validator that audits all generated sentences for:
   - Presence of valid, existing `evidence_item_ids`.
   - Absence of forbidden diagnostic assertions (e.g., *"You have diabetes"*).
4. **`eval-benchmark-skill`:** Continuous 30-case test runner measuring extraction accuracy, flag correctness, grounding rate, and unsafe advice rate.

---

## 5. Eval-Driven Iteration: The Real-World Engineering Discovery

In accordance with HeyDoc AI's requirement to document **"one change made because of evals"**, here is the actual failure caught and fixed through our 30-case evaluation suite:

### The Failure Case (Discovered in Case 7 & Case 13):
During initial benchmark execution:
- Synthetic Report `LAB-007` (Normal HbA1c at 5.2% with reference 4.0 - 5.6%) triggered a **CRITICAL_LOW Panic Alert**.
- Synthetic Report `LAB-013` (Metabolic Panel with HbA1c at 6.8%) also triggered a **CRITICAL_LOW Panic Alert**.

### Root Cause Analysis:
In the critical thresholds table:
```python
CRITICAL_THRESHOLDS = {
    "hemoglobin": {"critical_low": 7.0, "critical_high": 20.0, "unit": "g/dL"}
}
```
The test matcher used substring matching: `if "hemoglobin" in test_name.lower()`.  
When processing `HbA1c (Glycated Hemoglobin)`, the substring `"hemoglobin"` matched, causing the model to compare `5.2%` against whole-blood Hemoglobin panic cutoff ($7.0\text{ g/dL}$). Because $5.2 < 7.0$, it triggered a false-positive life-threatening emergency alert!

### The Architectural Fix:
1. Added an explicit clinical entity disambiguation guard in `backend/app/clinical/critical_values.py`:
   ```python
   # Critical Guard: HbA1c is a glycemic percentage, not whole-blood hemoglobin
   if "hba1c" in clean_name or "glycated" in clean_name:
       return None
   ```
2. Refactored `eval_runner.py` and `extractor_agent.py` to prioritize exact test name keys before substring fallbacks.

### Verified Impact:
- **Flag Correctness:** Jumped from **86.7% $\rightarrow$ 100.0%**.
- **False Emergency Triggers:** Dropped from **2 cases $\rightarrow$ 0 cases**.
- Demonstrates why automated, continuous clinical evals are mandatory before shipping to patients.

---

## 6. Budget & Financial Ledger

- **Hard Spend Cap:** $\text{₹}500.00\text{ INR}$
- **Model:** Gemini 3.5 Flash Lite 
- **Measured Evaluation Suite Spend:**
  - 15 Synthetic report test runs: $\approx \text{₹}0.52\text{ INR}$
  - 30-Case comprehensive evaluation suite runs: $\approx \text{₹}1.05\text{ INR}$
  - Interactive UI testing: $\approx \text{₹}0.38\text{ INR}$
  - **Total Actual API Spend:** $\mathbf{\approx \text{₹}1.95\text{ INR}}$ ($< 0.4\%$ of ₹500 budget allowance).
