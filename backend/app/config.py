import os
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseModel):
    app_name: str = "HeyDoc AI - Lab Report Explainer"
    version: str = "1.0.0"
    gemini_api_key: str = os.getenv("GEMINI_API_KEY", "")
    gemini_model: str = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    fallback_models: list = ["gemini-2.5-flash", "gemini-3.5-flash-lite", "gemini-3.8-flash"]
    max_budget_inr: float = 500.0
    input_cost_per_m_tokens: float = 0.075   # USD
    output_cost_per_m_tokens: float = 0.300  # USD
    usd_to_inr: float = 85.0

settings = Settings()
