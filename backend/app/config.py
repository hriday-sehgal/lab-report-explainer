import os
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseModel):
    app_name: str = "CarePulse OS — Clinical Diagnostics & Agentic Explainer"
    version: str = "1.0.0"
    gemini_api_key: str = os.getenv("GEMINI_API_KEY", "")
    gemini_model: str = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite")
    fallback_models: list = ["gemini-3.5-flash-lite", "gemini-3.5-flash"]
    api_timeout_seconds: float = 5.0
    max_budget_inr: float = 500.0
    input_cost_per_m_tokens: float = 0.075   # USD
    output_cost_per_m_tokens: float = 0.300  # USD
    usd_to_inr: float = 85.0

settings = Settings()
