import sys
import os
import json
from datetime import datetime
from unittest.mock import MagicMock, patch

# Setup mocks to avoid external API calls
sys.modules['dotenv'] = MagicMock()
sys.modules['openai'] = MagicMock()
sys.modules['supabase'] = MagicMock()
sys.modules['langgraph'] = None  # Use sequential fallback

# Set dummy env vars
os.environ["SUPABASE_URL"] = "http://test"
os.environ["SUPABASE_KEY"] = "test"

# Adjust path
sys.path.append(".")

# Import the brain
from brain.graph import SilverAgentGraph

def run_bearish_demo():
    print("="*60)
    print("DEMO: SILVER PREDICTION BRAIN - BEARISH SCENARIO")
    print("="*60)

    # 1. SETUP NEW DEMO DATA (Bearish Scenario)
    scenario_input = {
        "price": {
            "price": 28.50,
            "currency": "USD",
            "raw_data": {"symbol": "XAGUSD", "bid": 28.48, "ask": 28.52, "trend": "down"}
        },
        "news": {
            "title": "US Dollar strengthens significantly",
            "raw_data": {
                "headline": "USD Index hits 1-year high on Fed hawkishness",
                "summary": "The dollar spiked after the Fed hinted at more rate hikes, putting pressure on precious metals.",
                "sentiment_label": "bearish",
                "impact_score": 8.5
            }
        }
    }

    # 2. MOCK LLM RESPONSES
    mock_analysis = {
        "market": "Silver has broken below $29.00 support. The strong dollar is creates heavy headwinds.",
        "sentiment": {
            "overall_sentiment": "negative",
            "sentiment_score": -0.75,
            "summary": "Dollar strength is dominant, driving precious metals lower.",
            "key_headlines": ["USD Index hits 1-year high"],
            "potential_impact": "high"
        }
    }

    mock_prediction = {
        "decision": "bearish",
        "price_target": 27.20,
        "price_range": {"low": 26.50, "high": 28.00},
        "confidence_score": 0.85,
        "reasoning_chain": "Technical breakdown combined with overwhelming macro pressure from a strong USD.",
        "key_factors": ["USD Strength", "Support Breach", "Fed Policy"],
        "risks": ["Unexpected geopolitical tension", "Short covering rally"]
    }

    # 3. CONFIGURE MOCKS
    mock_price_query = MagicMock()
    mock_price_query.select.return_value.order.return_value.limit.return_value.execute.return_value.data = [scenario_input["price"]]
    
    mock_news_query = MagicMock()
    mock_news_query.select.return_value.order.return_value.limit.return_value.execute.return_value.data = [scenario_input["news"]]
    
    mock_db_client = MagicMock()
    # We will capture the call to log_agent_action to show it was successful
    payload_capture = {}
    def capture_log(payload):
        payload_capture.update(payload)
        print("\n[DB LOG] Storing the following in 'agent_logs':")
        print(json.dumps(payload, indent=2))
        return True
    
    mock_db_client.log_agent_action.side_effect = capture_log
    
    mock_llm_client = MagicMock()
    mock_llm_client.analyze_market_data.return_value = mock_analysis["market"]
    mock_llm_client.analyze_news_sentiment.return_value = mock_analysis["sentiment"]
    mock_llm_client.make_prediction.return_value = mock_prediction

    # 4. RUN THE BRAIN
    with patch('database.price_data', return_value=mock_price_query), \
         patch('database.news_data', return_value=mock_news_query), \
         patch('brain.llm_client.get_llm_client', return_value=mock_llm_client):
        
        agent = SilverAgentGraph(db_client=mock_db_client, llm_client=mock_llm_client)
        
        print("\n--- STEP 1: COLLECTION ---")
        print(f"Feeding Price Data: {scenario_input['price']['price']}")
        print(f"Feeding Raw News JSON: {json.dumps(scenario_input['news']['raw_data'])}")
        
        print("\n--- STEP 2: PROCESSING (The Brain at Work) ---")
        async def run_async():
            return await agent.run(session_id="bearish-demo-999")
        
        # In a real script we would use asyncio.run(), but since we are in a demo:
        import asyncio
        final_state = asyncio.run(run_async())

        print("\n" + "="*60)
        print("FINAL BRAIN OUTPUT")
        print("="*60)
        print(f"DECISION:   {final_state['prediction']['decision'].upper()}")
        print(f"TARGET:     ${final_state['prediction']['price_target']}")
        print(f"CONFIDENCE: {final_state['confidence']*100}%")
        print(f"REASONING:  {final_state['prediction']['reasoning_chain']}")
        print("="*60)

if __name__ == "__main__":
    run_bearish_demo()
