import sys
import unittest
from unittest.mock import MagicMock, patch
from datetime import datetime
import os
import json

# ==============================================================================
# DEMO DATA CONFIGURATION
# Modify these values to test how the Brain reacts to different scenarios!
# ==============================================================================
DEMO_DATA = {
    # 1. INPUT: What the agent "sees" in the database
    "INPUT": {
        "price": {
            "price": 31.50,
            "currency": "USD",
            "raw_data": {"symbol": "XAGUSD", "bid": 31.45, "ask": 31.55}
        },
        "news": {
            "title": "Industrial demand spikes for Silver",
            "source_url": "example.com",
            "raw_data": {
                "headline": "Silver industrial demand hits record high in 2025",
                "summary": "Renewable energy sectors drive unprecedented demand for silver paste in solar panels.",
                "sentiment_label": "bullish",
                "impact_score": 9.2
            }
        }
    },
    
    # 2. ANALYSIS: How the LLM interprets the data (Mocked)
    "ANALYSIS": {
        "market": "Silver is showing a strong uptrend. Key support at $30.00.",
        "sentiment": {
            "overall_sentiment": "positive",
            "sentiment_score": 0.8,
            "summary": "Market sentiment is bullish due to industrial demand.",
            "key_headlines": ["Silver industrial demand hits record high in 2025"],
            "potential_impact": "high"
        }
    },
    
    # 3. OUTPUT: What the LLM decides (Mocked)
    "PREDICTION": {
        "decision": "bullish",
        "price_target": 32.50,
        "price_range": {"low": 31.00, "high": 33.00},
        "confidence_score": 0.9,
        "reasoning_chain": "Strong technicals matched with positive news flow from industrial sectors.",
        "key_factors": ["Solar panel demand", "Technical breakout"],
        "risks": ["Fed interest rate hikes"]
    }
}
# ==============================================================================


# ----------------------------------------------------------------------
# 1. SETUP MOCKS BEFORE IMPORTS
# ----------------------------------------------------------------------
sys.modules['dotenv'] = MagicMock()
sys.modules['openai'] = MagicMock()
sys.modules['supabase'] = MagicMock()
sys.modules['langgraph'] = None  # Force ImportError to test sequential fallback

# Set dummy env vars
os.environ["SUPABASE_URL"] = "http://test"
os.environ["SUPABASE_KEY"] = "test"

# Adjust path to include project root
sys.path.append(".")

# Now import the class under test
from brain.graph import SilverAgentGraph

# ----------------------------------------------------------------------
# 2. HELPER FUNCTIONS
# ----------------------------------------------------------------------
def mock_llm_chain(messages, **kwargs):
    """
    Simulates the LLM's thought process.
    """
    # This function is not used when we mock high-level client methods,
    # but kept here for reference if we switch to lower-level mocking.
    return "{}"

# ----------------------------------------------------------------------
# 3. TEST CLASS
# ----------------------------------------------------------------------
class TestSilverAgent(unittest.IsolatedAsyncioTestCase):
    
    async def test_demo_scenario(self):
        print("\nSTARTING AGENT TEST WITH DEMO DATA")
        print("="*60)
        print(f"Scenario Input: Price=${DEMO_DATA['INPUT']['price']['price']}, Headline='{DEMO_DATA['INPUT']['news']['raw_data']['headline']}'")
        
        # --- A. Mock Database Queries ---
        # 1. Mock Price Response
        mock_price_query = MagicMock()
        mock_price_record = DEMO_DATA["INPUT"]["price"].copy()
        mock_price_record["fetched_at"] = datetime.utcnow().isoformat()
        
        mock_price_query.select.return_value.order.return_value.limit.return_value.execute.return_value.data = [mock_price_record]
        
        # 2. Mock News Response
        mock_news_query = MagicMock()
        mock_news_record = DEMO_DATA["INPUT"]["news"].copy()
        mock_news_record["fetched_at"] = datetime.utcnow().isoformat()
        
        mock_news_query.select.return_value.order.return_value.limit.return_value.execute.return_value.data = [mock_news_record]
        
        # --- B. Mock DB Client (for logging) ---
        mock_db_client = MagicMock()
        mock_db_client.log_agent_action = MagicMock()
        
        # --- C. Mock LLM Client ---
        mock_llm_client = MagicMock()
        
        # Configure LLM to return our DEMO ANALYSIS
        mock_llm_client.analyze_market_data.return_value = DEMO_DATA["ANALYSIS"]["market"]
        mock_llm_client.analyze_news_sentiment.return_value = DEMO_DATA["ANALYSIS"]["sentiment"]
        
        # Configure LLM to return our DEMO PREDICTION
        mock_llm_client.make_prediction.return_value = DEMO_DATA["PREDICTION"]
        
        # --- D. Patch & Run ---
        with patch('database.price_data', return_value=mock_price_query), \
             patch('database.news_data', return_value=mock_news_query), \
             patch('brain.llm_client.get_llm_client', return_value=mock_llm_client):
            
            # Instantiate Agent
            agent = SilverAgentGraph(db_client=mock_db_client, llm_client=mock_llm_client)
            
            # Run Agent Sequence
            print("\n... Agent is running ...")
            final_state = await agent.run(session_id="demo-session-001")
            
            # --- E. Assertions ---
            print("\nVERIFYING RESULTS")
            print("-" * 30)
            
            # 1. Prediction data checks
            pred = final_state.get("prediction", {})
            self.assertEqual(pred.get("decision"), DEMO_DATA["PREDICTION"]["decision"])
            self.assertEqual(pred.get("price_target"), DEMO_DATA["PREDICTION"]["price_target"])
            self.assertEqual(pred.get("confidence_score"), DEMO_DATA["PREDICTION"]["confidence_score"])
            self.assertIn("Solar panel demand", pred.get("key_factors", []))
            
            print(f"PASS: Prediction values verified (Decision: {pred.get('decision')})")

            # 2. DB Capture Matches Schema (Agent Logs)
            mock_db_client.log_agent_action.assert_called_once()
            log_payload = mock_db_client.log_agent_action.call_args[0][0]
            
            self.assertEqual(log_payload['session_id'], "demo-session-001")
            self.assertEqual(log_payload['decision'], DEMO_DATA["PREDICTION"]["decision"])
            self.assertEqual(log_payload['confidence_score'], DEMO_DATA["PREDICTION"]["confidence_score"])
            self.assertIn("Solar panel demand", str(log_payload['prediction_value']))
            self.assertIn(DEMO_DATA["ANALYSIS"]["market"], log_payload['reasoning_chain'])
            
            print(f"PASS: Correctly logged to 'agent_logs':")
            print(f"  -> Session ID: {log_payload['session_id']}")
            print(f"  -> Raw Response Captured: {bool(log_payload['raw_response'])}")
            print(f"  -> Full Reasoning Chain logged: Yes")
            
            # 3. Verify news data was collected
            self.assertEqual(len(final_state["news_data"]), 1)
            self.assertIn("headline", final_state["news_data"][0]["raw_data"])
            print(f"PASS: News 'raw_data' successfully collected and passed to brain")
            
            print("\nDEMO TEST COMPLETED SUCCESSFULLY")

if __name__ == "__main__":
    unittest.main()
