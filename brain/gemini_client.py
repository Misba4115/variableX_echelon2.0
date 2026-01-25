"""
Gemini LLM Client for the Silver Prediction Agent.
Handles Google Gemini API interactions for real-time predictions.
"""

import os
import json
import time
from pathlib import Path
from typing import Any, Dict, List, Optional
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from .env file
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

try:
    import google.genai as genai
except ImportError:
    genai = None


class GeminiClient:
    """
    Google Gemini API client for the agent's LLM operations.
    Specialized for real-time silver price predictions.
    """
    
    def __init__(
        self, 
        api_key: Optional[str] = None,
        model: str = "gemini-1.5-flash",  # Fast and efficient for real-time
        max_retries: int = 3
    ):
        """
        Initialize the Gemini client.
        
        Args:
            api_key: Google Gemini API key (or use GEMINI_API_KEY env var)
            model: Model to use (default: gemini-1.5-flash for speed)
            max_retries: Maximum retry attempts for API calls
        """
        if genai is None:
            raise ImportError(
                "google-genai package not installed. "
                "Run: pip install google-genai"
            )
        
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError(
                "Missing GEMINI_API_KEY. Please provide it or set in .env file. "
                "Get your API key from: https://makersuite.google.com/app/apikey"
            )
        
        # Initialize Gemini API client - google-genai uses Client directly
        self.client = genai.Client(api_key=self.api_key)
        self.model = model
        self.max_retries = max_retries
        self.total_requests = 0
    
    def predict_silver_price(
        self,
        current_price: float,
        price_change: float,
        recent_prices: List[Dict[str, Any]],
        news_articles: List[Dict[str, Any]],
        market_context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Generate a silver price prediction based on real database data.
        
        Args:
            current_price: Current silver price in USD
            price_change: 24h price change percentage
            recent_prices: List of recent price data points
            news_articles: List of recent news articles from database
            market_context: Additional market context/indicators
        
        Returns:
            Dict with prediction details
        """
        
        # Format price history
        price_history = ""
        if recent_prices:
            price_history = "Recent Price History:\n"
            for price in recent_prices[-7:]:  # Last 7 data points
                price_val = price.get('price', 0)
                timestamp = price.get('fetched_at', 'N/A')
                price_history += f"- {timestamp[:10]}: ${price_val}\n"
        
        # Format news summary
        news_summary = ""
        if news_articles:
            news_summary = "Recent News Summary:\n"
            for i, article in enumerate(news_articles[:5], 1):  # Top 5 recent articles
                title = article.get('title', 'No title')
                content = article.get('content', 'No content')[:100]
                news_summary += f"{i}. {title}\n   {content}...\n"
        
        # Market context
        context_text = ""
        if market_context:
            context_text = "Market Context:\n"
            for key, value in market_context.items():
                context_text += f"- {key}: {value}\n"
        
        # Build the prompt
        prompt = f"""You are an expert precious metals analyst specializing in silver (XAG) price prediction.

CURRENT MARKET DATA:
- Current Price: ${current_price} USD
- 24h Change: {price_change:+.2f}%
- Timestamp: {datetime.utcnow().isoformat()}

{price_history}

{news_summary}

{context_text}

Based on this real-time data, provide a silver price prediction with:
1. **Decision**: BULLISH, BEARISH, or NEUTRAL
2. **Target Price**: Specific price target in USD
3. **Confidence**: Score from 0.0 to 1.0
4. **Timeframe**: How many hours/days for this prediction
5. **Key Factors**: Why this prediction based on data
6. **Risks**: What could change this prediction

Respond in JSON format:
{{
  "decision": "BULLISH|BEARISH|NEUTRAL",
  "target_price": <number>,
  "confidence_score": <0.0-1.0>,
  "timeframe_hours": <integer>,
  "key_factors": ["<factor1>", "<factor2>", ...],
  "risks": ["<risk1>", "<risk2>", ...],
  "reasoning": "<detailed explanation based on provided data>"
}}

IMPORTANT: Only use the data provided above. Make realistic predictions based on actual market data."""
        
        return self._call_gemini(prompt, is_json=True)
    
    def analyze_market_data(
        self,
        price_data: Dict[str, Any],
        price_history: List[Dict[str, Any]] = None,
    ) -> str:
        """
        Analyze market price data using Gemini.
        
        Args:
            price_data: Current price data from database
            price_history: Historical price data from database
        
        Returns:
            Analysis text
        """
        
        # Format price history
        history_text = "Not available"
        if price_history:
            history_lines = []
            for item in price_history[-10:]:  # Last 10 data points
                price_val = item.get('price', 'N/A')
                timestamp = item.get('fetched_at', 'N/A')
                history_lines.append(f"- {timestamp}: ${price_val}")
            history_text = "\n".join(history_lines)
        
        prompt = f"""Analyze the following silver price data:

Current Price: ${price_data.get('price', 'N/A')} USD
Currency: {price_data.get('currency', 'USD')}
Change: {price_data.get('price_change', 0):+.2f} USD ({price_data.get('price_change_percent', 0):+.2f}%)
High 24h: ${price_data.get('high_24h', 'N/A')}
Low 24h: ${price_data.get('low_24h', 'N/A')}
Timestamp: {price_data.get('fetched_at', 'N/A')}

Recent price points:
{history_text}

Provide a brief technical analysis including:
1. Price movement assessment
2. Support/resistance levels (if identifiable from data)
3. Overall trend direction
4. Key observations"""
        
        return self._call_gemini(prompt)
    
    def analyze_news_sentiment(
        self,
        news_items: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Analyze news sentiment using Gemini.
        
        Args:
            news_items: List of news articles from database
        
        Returns:
            Dict with sentiment analysis
        """
        
        if not news_items:
            return {
                "overall_sentiment": "neutral",
                "sentiment_score": 0.0,
                "summary": "No news data available for analysis"
            }
        
        # Format news items
        news_text = ""
        for i, item in enumerate(news_items[:10], 1):  # Top 10 articles
            title = item.get('title', 'No title')
            content = item.get('content', 'No content')
            news_text += f"{i}. {title}\n   Content: {content}\n\n"
        
        prompt = f"""Analyze the sentiment of these silver market news articles:

{news_text}

Provide sentiment analysis in JSON format:
{{
  "overall_sentiment": "positive|negative|neutral",
  "sentiment_score": <-1.0 to 1.0>,
  "summary": "<brief summary of market sentiment>",
  "bullish_factors": ["<factor1>", "<factor2>"],
  "bearish_factors": ["<factor1>", "<factor2>"],
  "impact_level": "high|medium|low"
}}

Base your analysis only on the news provided above."""
        
        return self._call_gemini(prompt, is_json=True)
    
    def _call_gemini(
        self,
        prompt: str,
        is_json: bool = False,
        temperature: float = 0.7
    ) -> Any:
        """
        Call Gemini API with retry logic.
        
        Args:
            prompt: The prompt to send to Gemini
            is_json: Whether to expect JSON response
            temperature: Temperature for generation (0.0-2.0)
        
        Returns:
            Response from Gemini (parsed as JSON if is_json=True)
        """
        
        for attempt in range(self.max_retries):
            try:
                # Generate response using new google-genai API
                response = self.client.models.generate_content(
                    model=self.model,
                    contents=prompt,
                    config=genai.types.GenerateContentConfig(
                        temperature=temperature,
                        top_p=0.95,
                        top_k=40,
                        max_output_tokens=2048,
                    )
                )
                
                self.total_requests += 1
                response_text = response.text.strip()
                
                # Parse JSON if requested
                if is_json:
                    # Try to extract JSON from response
                    try:
                        # Remove markdown code blocks if present
                        if response_text.startswith("```"):
                            response_text = response_text.split("```")[1]
                            if response_text.startswith("json"):
                                response_text = response_text[4:]
                            response_text = response_text.split("```")[0]
                        
                        return json.loads(response_text)
                    except json.JSONDecodeError:
                        print(f"[GeminiClient] Warning: Failed to parse JSON response")
                        return {
                            "error": "JSON parse failed",
                            "raw_response": response_text
                        }
                
                return response_text
                
            except Exception as e:
                if attempt == self.max_retries - 1:
                    error_msg = f"Gemini API error after {self.max_retries} retries: {str(e)}"
                    print(f"[GeminiClient] {error_msg}")
                    raise Exception(error_msg)
                
                # Exponential backoff
                wait_time = 2 ** attempt
                print(f"[GeminiClient] Error (attempt {attempt + 1}/{self.max_retries}): {str(e)}")
                print(f"[GeminiClient] Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
    
    def get_request_count(self) -> int:
        """Get total requests made to Gemini API."""
        return self.total_requests


def get_gemini_client(model: str = "gemini-1.5-flash") -> GeminiClient:
    """Get a Gemini client instance."""
    return GeminiClient(model=model)
