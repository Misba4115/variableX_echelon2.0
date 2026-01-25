"""
LLM Client for the Silver Prediction Agent.
Handles Google Gemini API interactions with retry logic and structured outputs.
"""

import os
import json
import time
from typing import Any, Dict, List, Optional, Union
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=env_path, override=True)

# Import prompts
from brain.prompts import SYSTEM_PROMPTS

try:
    import google.genai as genai
except ImportError:
    genai = None


class LLMClient:
    """
    Google Gemini client wrapper for the agent's LLM operations.
    """
    
    def __init__(
        self, 
        api_key: Optional[str] = None,
        model: str = "gemini-2.5-flash",
        max_retries: int = 3
    ):
        """
        Initialize the Gemini LLM client.
        
        Args:
            api_key: Google Gemini API key (or use GEMINI_API_KEY env var)
            model: Model to use (default: gemini-2.5-flash for speed and cost)
            max_retries: Maximum retry attempts for API calls
        """
        if genai is None:
            raise ImportError(
                "google-genai package not installed. Run: pip install google-genai"
            )
        
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError(
                "Missing GEMINI_API_KEY. Please provide it or set in .env file."
            )
        
        # Normalize model name to include "models/" prefix if needed
        self.model = model if model.startswith("models/") else f"models/{model}"
        self.max_retries = max_retries
        # Initialize Gemini client with API key
        self.client = genai.Client(api_key=self.api_key)
        self.total_tokens_used = 0
    
    def chat_completion(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        response_format: Optional[str] = None
    ) -> str:
        """
        Send a chat completion request with retry logic using Gemini API.
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            system_prompt: Optional system prompt to prepend
            temperature: Sampling temperature (0.0-2.0)
            response_format: Optional 'json_object' for JSON mode
        
        Returns:
            Response text from the model
        """
        # Prepend system prompt if provided
        if system_prompt:
            messages = [{"role": "system", "content": system_prompt}] + messages
        
        for attempt in range(self.max_retries):
            try:
                # Build the complete prompt with system context
                full_prompt = ""
                
                # Add system messages first
                for msg in messages:
                    if msg["role"] == "system":
                        full_prompt += f"{msg['content']}\n\n"
                
                # Add user/assistant messages
                for msg in messages:
                    if msg["role"] != "system":
                        full_prompt += f"{msg['content']}\n\n"
                
                # Use Gemini's API through client.models.generate_content
                response = self.client.models.generate_content(
                    model=self.model,
                    contents=full_prompt.strip(),
                    config=genai.types.GenerateContentConfig(
                        temperature=temperature,
                        max_output_tokens=4096
                    )
                )
                
                if response and response.text:
                    return response.text
                else:
                    raise Exception("Empty response from Gemini API")
                
            except Exception as e:
                if attempt == self.max_retries - 1:
                    raise Exception(f"Gemini API error after {self.max_retries} retries: {str(e)}")
                
                # Exponential backoff
                wait_time = 2 ** attempt
                print(f"Gemini API error (attempt {attempt + 1}/{self.max_retries}): {str(e)}")
                print(f"Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
    
    def analyze_market_data(
        self,
        price_data: Dict[str, Any],
        price_history: List[Dict[str, Any]] = None,
        system_prompt: Optional[str] = None
    ) -> str:
        """
        Analyze market price data using LLM.
        
        Args:
            price_data: Current price data
            price_history: Optional historical price data
            system_prompt: System prompt for analysis
        
        Returns:
            Analysis text
        """
        # Use analyst system prompt if not provided
        if not system_prompt:
            system_prompt = SYSTEM_PROMPTS.get("analyst")
        
        # Format price history
        history_text = "Not available"
        if price_history and len(price_history) > 0:
            history_lines = []
            for item in price_history[-10:]:  # Last 10 data points
                price = item.get('price', 'N/A')
                fetched = item.get('fetched_at', 'N/A')
                change = item.get('price_change', 'N/A')
                history_lines.append(
                    f"- {fetched}: ${price} (Change: {change}%)"
                )
            history_text = "\n".join(history_lines)
        
        current_price = price_data.get('price', 'N/A')
        
        prompt = f"""Analyze the following REAL silver price data and provide technical analysis:

CURRENT PRICE DATA:
- Current Price: ${current_price} USD
- 24h Change: {price_data.get('price_change', 'N/A')}%
- High 24h: ${price_data.get('high_24h', 'N/A')}
- Low 24h: ${price_data.get('low_24h', 'N/A')}
- Trading Volume: {price_data.get('volume', 'N/A')}
- Last Updated: {price_data.get('fetched_at', 'N/A')}

HISTORICAL PRICE POINTS (Last 10):
{history_text}

ANALYSIS REQUIRED:
1. Current Trend Direction (Uptrend/Downtrend/Consolidation)
2. Support and Resistance Levels (based on current data)
3. Momentum Assessment (Strong/Moderate/Weak)
4. Price Volatility Analysis
5. Key Technical Observations
6. Probability of continued trend or reversal (0-100%)
7. Recommended price levels for next 24h

Provide detailed technical analysis for short-term (24h) price prediction."""
        
        messages = [{"role": "user", "content": prompt}]
        return self.chat_completion(messages, system_prompt=system_prompt, temperature=0.5)
    
    def analyze_news_sentiment(
        self,
        news_items: List[Dict[str, Any]],
        system_prompt: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Analyze news sentiment using LLM.
        
        Args:
            news_items: List of news headlines/articles
            system_prompt: System prompt for analysis
        
        Returns:
            Dict with sentiment analysis
        """
        if not news_items:
            return {
                "overall_sentiment": "neutral",
                "sentiment_score": 0.0,
                "summary": "No news data available for analysis",
                "potential_impact": "low"
            }
        
        # Use analyst system prompt if not provided
        if not system_prompt:
            system_prompt = SYSTEM_PROMPTS.get("analyst")
        
        # Format news items
        news_text = "\n".join([
            f"{i+1}. Title: {item.get('title', 'N/A')}\n   Content: {item.get('content', item.get('raw_data', {}))}\n   Source: {item.get('source_url', 'N/A')}\n   Fetched: {item.get('fetched_at', 'N/A')}"
            for i, item in enumerate(news_items[:20])  # Limit to 20 items
        ])
        
        prompt = f"""Analyze the following news headlines related to silver and precious metals:

{news_text}

For each headline, assess:
1. Sentiment impact on silver prices (positive/negative/neutral)
2. Market relevance and credibility
3. Potential price impact magnitude (high/medium/low)

Then provide an overall sentiment analysis in JSON format:
{{
  "overall_sentiment": "positive|negative|neutral",
  "sentiment_score": <-1.0 to 1.0 where -1 is very bearish, 0 is neutral, 1 is very bullish>,
  "summary": "<2-3 sentence market impact summary>",
  "key_themes": ["<theme 1>", "<theme 2>"],
  "potential_impact": "high|medium|low",
  "price_impact_direction": "upward|downward|neutral",
  "bullish_confidence": <0.0-1.0>,
  "bearish_confidence": <0.0-1.0>,
  "neutral_confidence": <0.0-1.0>
}}

Return ONLY valid JSON, no additional text."""
        
        messages = [{"role": "user", "content": prompt}]
        response = self.chat_completion(
            messages, 
            system_prompt=system_prompt,
            temperature=0.3,
            response_format="json_object"
        )
        
        try:
            result = json.loads(response)
            # Ensure all required fields exist
            if "overall_sentiment" not in result:
                result["overall_sentiment"] = "neutral"
            if "sentiment_score" not in result:
                result["sentiment_score"] = 0.0
            if "potential_impact" not in result:
                result["potential_impact"] = "medium"
            return result
        except json.JSONDecodeError:
            return {
                "overall_sentiment": "neutral",
                "sentiment_score": 0.0,
                "summary": response,
                "potential_impact": "medium",
                "error": "Failed to parse JSON response"
            }
    
    def make_prediction(
        self,
        market_data: Dict[str, Any],
        news_analysis: Dict[str, Any],
        price_analysis: str,
        system_prompt: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate a silver price prediction using LLM.
        
        Weighting: 80% price data + 20% news sentiment
        
        Args:
            market_data: Current market data (80% weight)
            news_analysis: News sentiment analysis (20% weight)
            price_analysis: Technical price analysis
            system_prompt: System prompt for prediction
        
        Returns:
            Dict with prediction details
        """
        # Use predictor system prompt if not provided
        if not system_prompt:
            system_prompt = SYSTEM_PROMPTS.get("predictor")
        current_price = float(market_data.get('price', 0))
        
        prompt = f"""You are an expert financial analyst specializing in precious metals trading. 
Generate a precise silver price prediction for the next 24 hours based on the provided data.

WEIGHTING METHODOLOGY (IMPORTANT):
- Price Data: 80% weight (primary factor for short-term prediction)
- News Sentiment: 20% weight (secondary factor for market sentiment)

CURRENT MARKET DATA (80% WEIGHT):
Current Price: ${current_price}
24h Change: {market_data.get('price_change', 0)}% (${market_data.get('price_change', 0)})
High 24h: ${market_data.get('high_24h', 0)}
Low 24h: ${market_data.get('low_24h', 0)}
Volume: {market_data.get('volume', 'N/A')}
Timestamp: {market_data.get('fetched_at', 'N/A')}

TECHNICAL PRICE ANALYSIS:
{price_analysis}

NEWS SENTIMENT (20% WEIGHT):
Overall Sentiment: {news_analysis.get('overall_sentiment', 'neutral')}
Sentiment Score: {news_analysis.get('sentiment_score', 0)} (from -1.0 to 1.0)
Impact: {news_analysis.get('potential_impact', 'medium')}
Summary: {news_analysis.get('summary', 'N/A')}

TASK: Based on 80% weight on price data and 20% weight on news sentiment, generate:

1. A clear decision (BULLISH, BEARISH, or NEUTRAL) 
2. A specific target price for the next 24 hours
3. A price range (low and high estimates)
4. A confidence score (0.0 to 1.0) based on data clarity
5. Detailed reasoning showing the 80/20 weighting calculation
6. Key factors supporting the prediction
7. Potential risks

RESPONSE FORMAT (RETURN ONLY VALID JSON):
{{
  "decision": "BULLISH|BEARISH|NEUTRAL",
  "target_price": <specific numeric target in USD, e.g., 95.50>,
  "price_range": {{"low": <numeric value>, "high": <numeric value>}},
  "confidence_score": <numeric 0.0 to 1.0>,
  "time_horizon": "24 hours",
  "reasoning_chain": "<Step 1: Price analysis (80%)... Step 2: News sentiment (20%)... Combined assessment: ...>",
  "price_factor_analysis": {{
    "trend": "uptrend|downtrend|consolidation",
    "momentum": "strong|moderate|weak",
    "support_level": <numeric>,
    "resistance_level": <numeric>,
    "weight": "80%"
  }},
  "news_factor_analysis": {{
    "sentiment": "{news_analysis.get('overall_sentiment', 'neutral')}",
    "market_impact": "{news_analysis.get('potential_impact', 'medium')}",
    "bullish_weight": <0.0-1.0>,
    "bearish_weight": <0.0-1.0>,
    "weight": "20%"
  }},
  "key_factors": ["<factor 1>", "<factor 2>", "<factor 3>"],
  "risks": ["<risk 1>", "<risk 2>"],
  "probability_up": <0-100>,
  "probability_down": <0-100>
}}

IMPORTANT: 
- Current price is ${current_price}. Predict target price based on technical levels.
- Return ONLY valid JSON, no additional text.
- Confidence should reflect data quality and clarity.
- Decision should be data-driven, not arbitrary.
"""
        
        messages = [{"role": "user", "content": prompt}]
        response = self.chat_completion(
            messages,
            system_prompt=system_prompt,
            temperature=0.3,  # Lower temperature for more consistent predictions
            response_format="json_object"
        )
        
        try:
            # Handle markdown-wrapped JSON responses
            json_str = response.strip()
            if json_str.startswith("```json"):
                json_str = json_str[7:]  # Remove ```json
            if json_str.startswith("```"):
                json_str = json_str[3:]  # Remove ```
            if json_str.endswith("```"):
                json_str = json_str[:-3]  # Remove trailing ```
            json_str = json_str.strip()
            
            # Parse the JSON response
            prediction = json.loads(json_str)
            
            # Validate and normalize required fields
            if not prediction.get("decision"):
                prediction["decision"] = "NEUTRAL"
            
            if prediction.get("decision") in ["bullish", "bearish", "neutral"]:
                prediction["decision"] = prediction["decision"].upper()
            
            # Ensure target_price is numeric
            try:
                if prediction.get("target_price"):
                    prediction["target_price"] = float(prediction["target_price"])
                else:
                    prediction["target_price"] = current_price
            except (ValueError, TypeError):
                prediction["target_price"] = current_price
            
            # Ensure confidence_score is within bounds
            try:
                if "confidence_score" in prediction:
                    prediction["confidence_score"] = max(0.0, min(1.0, float(prediction["confidence_score"])))
                else:
                    prediction["confidence_score"] = 0.5
            except (ValueError, TypeError):
                prediction["confidence_score"] = 0.5
            
            # Map decision to direction for compatibility
            prediction["direction"] = prediction["decision"]
                
            return prediction
            
        except json.JSONDecodeError as e:
            print(f"JSON Parse Error: {e}")
            print(f"Response was: {response[:200]}")
            return {
                "decision": "NEUTRAL",
                "direction": "NEUTRAL",
                "target_price": current_price,
                "confidence_score": 0.0,
                "reasoning_chain": response,
                "error": f"Failed to parse prediction JSON: {str(e)}"
            }
    
    def get_token_usage(self) -> int:
        """Get total tokens used in this session."""
        return self.total_tokens_used


# Convenience function
def get_llm_client(model: str = "gemini-2.5-flash") -> LLMClient:
    """Get an LLM client instance."""
    return LLMClient(model=model)
