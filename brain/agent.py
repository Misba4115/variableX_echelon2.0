"""
LangGraph State Machine for Silver Price Prediction.
Integrates with Gemini API to make real-time predictions based on database data.
"""

import asyncio
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta
from brain.gemini_client import GeminiClient


class SilverPredictionAgent:
    """
    Simplified agent that makes silver price predictions using real database data.
    
    Workflow:
    1. FETCH: Get latest price and news data from database
    2. ANALYZE: Use Gemini to analyze the data
    3. PREDICT: Generate price prediction with confidence
    4. STORE: Save prediction to database
    """
    
    def __init__(self, db_client=None):
        """
        Initialize the prediction agent.
        
        Args:
            db_client: Database client for fetching/storing data
        """
        self.db_client = db_client
        self.gemini_client = None
        self.last_prediction = None
    
    def _init_gemini(self):
        """Initialize Gemini client."""
        if not self.gemini_client:
            try:
                self.gemini_client = GeminiClient()
                print("[Agent] ✅ Gemini client initialized")
            except Exception as e:
                print(f"[Agent] ❌ Failed to initialize Gemini: {e}")
                raise
    
    def _fetch_data(self) -> Dict[str, Any]:
        """
        Fetch latest price and news data from database.
        
        Returns:
            Dict with current_price, price_history, news_articles
        """
        print("[Agent] 📊 Fetching data from database...")
        
        data = {
            "current_price": None,
            "price_change_24h": 0.0,
            "price_history": [],
            "news_articles": [],
            "timestamp": datetime.utcnow().isoformat()
        }
        
        try:
            if not self.db_client:
                print("[Agent] ⚠️  No database client available")
                return data
            
            from database.supabase_client import price_data, news_data
            
            # Fetch latest price
            print("[Agent]   - Fetching price data...")
            try:
                price_response = price_data().select("*").order("fetched_at", desc=True).limit(1).execute()
                if price_response.data:
                    current = price_response.data[0]
                    data["current_price"] = current.get('price', 0)
                    data["price_change_24h"] = current.get('price_change_percent', 0)
                    print(f"[Agent]   ✅ Price: ${data['current_price']} ({data['price_change_24h']:+.2f}%)")
            except Exception as e:
                print(f"[Agent]   ❌ Price fetch error: {e}")
            
            # Fetch price history (last 7 days)
            print("[Agent]   - Fetching price history...")
            try:
                seven_days_ago = (datetime.utcnow() - timedelta(days=7)).isoformat()
                history_response = price_data().select("*").gte("fetched_at", seven_days_ago).order("fetched_at", desc=True).execute()
                if history_response.data:
                    data["price_history"] = history_response.data
                    print(f"[Agent]   ✅ Got {len(data['price_history'])} price points")
            except Exception as e:
                print(f"[Agent]   ⚠️  History fetch error: {e}")
            
            # Fetch recent news
            print("[Agent]   - Fetching recent news...")
            try:
                news_response = news_data().select("*").order("fetched_at", desc=True).limit(10).execute()
                if news_response.data:
                    data["news_articles"] = news_response.data
                    print(f"[Agent]   ✅ Got {len(data['news_articles'])} news articles")
            except Exception as e:
                print(f"[Agent]   ⚠️  News fetch error: {e}")
            
        except Exception as e:
            print(f"[Agent] ❌ Data fetch failed: {e}")
        
        return data
    
    def _analyze_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Use Gemini to analyze collected data.
        
        Args:
            data: Fetched data from database
        
        Returns:
            Dict with analysis results
        """
        print("[Agent] 🧠 Analyzing data with Gemini...")
        
        analysis = {
            "price_analysis": "Analysis pending",
            "sentiment_analysis": {"overall_sentiment": "neutral", "sentiment_score": 0.0}
        }
        
        try:
            self._init_gemini()
            
            if data.get("current_price"):
                # Analyze price data
                print("[Agent]   - Analyzing price trends...")
                price_analysis = self.gemini_client.analyze_market_data(
                    {
                        "price": data["current_price"],
                        "price_change": data.get("price_change_24h", 0),
                        "price_change_percent": data.get("price_change_24h", 0),
                        "fetched_at": data["timestamp"]
                    },
                    price_history=data.get("price_history", [])
                )
                analysis["price_analysis"] = price_analysis
                print("[Agent]   ✅ Price analysis complete")
            
            if data.get("news_articles"):
                # Analyze sentiment
                print("[Agent]   - Analyzing news sentiment...")
                sentiment = self.gemini_client.analyze_news_sentiment(data["news_articles"])
                analysis["sentiment_analysis"] = sentiment
                print(f"[Agent]   ✅ Sentiment: {sentiment.get('overall_sentiment', 'unknown')}")
            
        except Exception as e:
            print(f"[Agent] ❌ Analysis error: {e}")
        
        return analysis
    
    def _make_prediction(self, data: Dict[str, Any], analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Use Gemini to make a price prediction.
        
        Args:
            data: Fetched data from database
            analysis: Analysis results from Gemini
        
        Returns:
            Dict with prediction details
        """
        print("[Agent] 🔮 Making prediction...")
        
        prediction = {
            "decision": "NEUTRAL",
            "target_price": data.get("current_price", 0),
            "confidence_score": 0.0,
            "reasoning": "Prediction pending",
            "timestamp": datetime.utcnow().isoformat(),
            "success": False
        }
        
        try:
            self._init_gemini()
            
            if not data.get("current_price"):
                print("[Agent] ⚠️  No price data available for prediction")
                return prediction
            
            # Make prediction using Gemini
            pred = self.gemini_client.predict_silver_price(
                current_price=data["current_price"],
                price_change=data.get("price_change_24h", 0),
                recent_prices=data.get("price_history", []),
                news_articles=data.get("news_articles", []),
                market_context={
                    "sentiment": analysis.get("sentiment_analysis", {}).get("overall_sentiment", "neutral")
                }
            )
            
            # Extract prediction details
            if isinstance(pred, dict) and "error" not in pred:
                prediction.update({
                    "decision": pred.get("decision", "NEUTRAL").upper(),
                    "target_price": pred.get("target_price", data.get("current_price", 0)),
                    "confidence_score": pred.get("confidence_score", 0.0),
                    "reasoning": pred.get("reasoning", ""),
                    "key_factors": pred.get("key_factors", []),
                    "risks": pred.get("risks", []),
                    "timeframe_hours": pred.get("timeframe_hours", 24),
                    "success": True
                })
                
                print(f"[Agent] ✅ Prediction: {prediction['decision']}")
                print(f"[Agent]    Target: ${prediction['target_price']}")
                print(f"[Agent]    Confidence: {prediction['confidence_score']:.2f}")
            else:
                print(f"[Agent] ⚠️  Invalid prediction response: {pred}")
        
        except Exception as e:
            print(f"[Agent] ❌ Prediction error: {e}")
        
        self.last_prediction = prediction
        return prediction
    
    def _store_prediction(self, prediction: Dict[str, Any]):
        """
        Store prediction to database.
        
        Args:
            prediction: Prediction details to store
        """
        print("[Agent] 💾 Storing prediction...")
        
        try:
            if not self.db_client:
                print("[Agent] ⚠️  No database client, skipping storage")
                return
            
            from database.supabase_client import agent_logs
            import uuid
            
            log_entry = {
                "session_id": str(uuid.uuid4()),
                "reasoning_chain": prediction.get("reasoning", "") + f"\nFactors: {prediction.get('key_factors', [])}",
                "decision": prediction.get("decision", "NEUTRAL"),
                "prediction_value": {
                    "target_price": prediction.get("target_price"),
                    "decision": prediction.get("decision"),
                    "timeframe_hours": prediction.get("timeframe_hours", 24)
                },
                "confidence_score": prediction.get("confidence_score", 0.0),
                "raw_response": {
                    "full_prediction": prediction
                }
            }
            
            response = agent_logs().insert(log_entry).execute()
            print("[Agent] ✅ Prediction stored to database")
            
        except Exception as e:
            print(f"[Agent] ⚠️  Storage error: {e}")
    
    async def run(self) -> Dict[str, Any]:
        """
        Execute the complete prediction workflow.
        
        Returns:
            Final prediction with all analysis
        """
        print("\n" + "="*70)
        print("🚀 SILVER PRICE PREDICTION AGENT")
        print("="*70)
        
        try:
            # Step 1: Fetch data from database
            data = self._fetch_data()
            
            if not data.get("current_price"):
                print("[Agent] ❌ No price data available, aborting")
                return {"success": False, "error": "No price data"}
            
            # Step 2: Analyze data with Gemini
            analysis = self._analyze_data(data)
            
            # Step 3: Make prediction
            prediction = self._make_prediction(data, analysis)
            
            # Step 4: Store prediction
            if prediction.get("success"):
                self._store_prediction(prediction)
            
            print("\n" + "="*70)
            print("✅ PREDICTION COMPLETE")
            print("="*70)
            print(f"Decision: {prediction['decision']}")
            print(f"Target: ${prediction['target_price']}")
            print(f"Confidence: {prediction['confidence_score']:.2%}")
            print(f"Timeframe: {prediction.get('timeframe_hours', 24)} hours")
            print("="*70 + "\n")
            
            return {
                "success": True,
                "prediction": prediction,
                "data_used": {
                    "price_points": len(data.get("price_history", [])),
                    "news_articles": len(data.get("news_articles", []))
                }
            }
            
        except Exception as e:
            print(f"\n[Agent] ❌ Workflow error: {e}")
            import traceback
            traceback.print_exc()
            return {"success": False, "error": str(e)}


async def run_prediction_agent(db_client=None) -> Dict[str, Any]:
    """
    Convenience function to run the prediction agent.
    
    Args:
        db_client: Optional database client
    
    Returns:
        Prediction results
    """
    agent = SilverPredictionAgent(db_client=db_client)
    return await agent.run()


# Synchronous wrapper for convenience
def predict_silver_price(db_client=None) -> Dict[str, Any]:
    """
    Synchronous wrapper to predict silver price.
    
    Args:
        db_client: Optional database client
    
    Returns:
        Prediction results
    """
    return asyncio.run(run_prediction_agent(db_client))
