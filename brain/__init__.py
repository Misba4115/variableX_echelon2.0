"""
Brain module for Autonomous Silver Prediction Agent.
Contains Gemini LLM integration for real-time predictions.
"""

from .agent import SilverPredictionAgent, predict_silver_price, run_prediction_agent
from .gemini_client import GeminiClient, get_gemini_client
from .prompts import SYSTEM_PROMPTS

__all__ = [
    "SilverPredictionAgent",
    "predict_silver_price",
    "run_prediction_agent",
    "GeminiClient",
    "get_gemini_client",
    "SYSTEM_PROMPTS"
]
