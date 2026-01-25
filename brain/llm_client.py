"""
LLM Client for the Silver Prediction Agent.
Handles OpenAI API interactions with retry logic and structured outputs.
"""

import os
import json
import time
from typing import Any, Dict, List, Optional, Union
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None


class LLMClient:
    """
    OpenAI client wrapper for the agent's LLM operations.
    """
    
    def __init__(
        self, 
        api_key: Optional[str] = None,
        model: str = "gpt-4o-mini",
        max_retries: int = 3
    ):
        """
        Initialize the LLM client.
        
        Args:
            api_key: OpenAI API key (or use OPENAI_API_KEY env var)
            model: Model to use (default: gpt-4o-mini for cost efficiency)
            max_retries: Maximum retry attempts for API calls
        """
        if OpenAI is None:
            raise ImportError(
                "openai package not installed. Run: pip install openai"
            )
        
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError(
                "Missing OPENAI_API_KEY. Please provide it or set in .env file."
            )
        
        self.model = model
        self.max_retries = max_retries
        self.client = OpenAI(api_key=self.api_key)
        self.total_tokens_used = 0
    
    def chat_completion(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        response_format: Optional[str] = None
    ) -> str:
        """
        Send a chat completion request with retry logic.
        
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
                kwargs = {
                    "model": self.model,
                    "messages": messages,
                    "temperature": temperature
                }
                
                if response_format == "json_object":
                    kwargs["response_format"] = {"type": "json_object"}
                
                response = self.client.chat.completions.create(**kwargs)
                
                # Track token usage
                if hasattr(response, 'usage'):
                    self.total_tokens_used += response.usage.total_tokens
                
                return response.choices[0].message.content
                
            except Exception as e:
                if attempt == self.max_retries - 1:
                    raise Exception(f"LLM API error after {self.max_retries} retries: {str(e)}")
                
                # Exponential backoff
                wait_time = 2 ** attempt
                print(f"LLM API error (attempt {attempt + 1}/{self.max_retries}): {str(e)}")
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
        # Format price history
        history_text = "Not available"
        if price_history:
            history_lines = []
            for item in price_history[-10:]:  # Last 10 data points
                history_lines.append(
                    f"- {item.get('collected_at', 'N/A')}: ${item.get('price', 'N/A')}"
                )
            history_text = "\n".join(history_lines)
        
        prompt = f"""
Analyze the following silver price data:

Current Price: ${price_data.get('price', 'N/A')} USD
Timestamp: {price_data.get('timestamp', 'N/A')}

Recent price points:
{history_text}

Provide your analysis of the current price action and trends.
Include:
1. Price movement assessment
2. Support/resistance levels if identifiable
3. Overall trend direction
4. Key observations
"""
        
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
                "summary": "No news data available for analysis"
            }
        
        # Format news items
        news_text = "\n".join([
            f"{i+1}. {item.get('title', 'N/A')}"
            for i, item in enumerate(news_items[:20])  # Limit to 20 items
        ])
        
        prompt = f"""
Analyze the following news headlines related to silver and precious metals:

{news_text}

For each headline, assess the sentiment and potential impact on silver prices.
Then provide an overall sentiment analysis.

Respond in JSON format with:
{{
  "overall_sentiment": "positive|negative|neutral",
  "sentiment_score": <-1.0 to 1.0>,
  "summary": "<brief summary>",
  "key_headlines": ["<headline 1>", "<headline 2>", ...],
  "potential_impact": "high|medium|low"
}}
"""
        
        messages = [{"role": "user", "content": prompt}]
        response = self.chat_completion(
            messages, 
            system_prompt=system_prompt,
            temperature=0.3,
            response_format="json_object"
        )
        
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            return {
                "overall_sentiment": "neutral",
                "sentiment_score": 0.0,
                "summary": response,
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
        Generate a price prediction using LLM.
        
        Args:
            market_data: Current market data
            news_analysis: News sentiment analysis
            price_analysis: Technical price analysis
            system_prompt: System prompt for prediction
        
        Returns:
            Dict with prediction details
        """
        prompt = f"""
Based on the following data, make a silver price prediction:

CURRENT MARKET DATA:
{json.dumps(market_data, indent=2)}

PRICE ANALYSIS:
{price_analysis}

NEWS SENTIMENT:
{json.dumps(news_analysis, indent=2)}

Provide your prediction in JSON format:
{{
  "decision": "bullish|bearish|neutral",
  "price_target": <target price in USD>,
  "price_range": {{"low": <low estimate>, "high": <high estimate>}},
  "confidence_score": <0.0 to 1.0>,
  "reasoning_chain": "<detailed reasoning>",
  "key_factors": ["<factor 1>", "<factor 2>", ...],
  "risks": ["<risk 1>", "<risk 2>", ...]
}}
"""
        
        messages = [{"role": "user", "content": prompt}]
        response = self.chat_completion(
            messages,
            system_prompt=system_prompt,
            temperature=0.4,
            response_format="json_object"
        )
        
        try:
            prediction = json.loads(response)
            # Ensure confidence_score is within bounds
            if "confidence_score" in prediction:
                prediction["confidence_score"] = max(0.0, min(1.0, float(prediction["confidence_score"])))
            elif "confidence" in prediction:
                # Backward compatibility
                prediction["confidence_score"] = max(0.0, min(1.0, float(prediction["confidence"])))
            
            # Map decision to direction for backward compatibility if needed, or vice-versa
            if "decision" in prediction and "direction" not in prediction:
                prediction["direction"] = prediction["decision"]
                
            return prediction
        except (json.JSONDecodeError, ValueError) as e:
            return {
                "decision": "neutral",
                "direction": "neutral",
                "confidence_score": 0.0,
                "reasoning_chain": response,
                "error": f"Failed to parse prediction: {str(e)}"
            }
    
    def get_token_usage(self) -> int:
        """Get total tokens used in this session."""
        return self.total_tokens_used


# Convenience function
def get_llm_client(model: str = "gpt-4o-mini") -> LLMClient:
    """Get an LLM client instance."""
    return LLMClient(model=model)
