import sys
import unittest
from unittest.mock import MagicMock, patch
from datetime import datetime
import os

# Set dummy env vars to prevent warnings in supabase_client.py
os.environ["SUPABASE_URL"] = "http://test"
os.environ["SUPABASE_KEY"] = "test"

# Adjust path to include project root
sys.path.append(".")

# Mock missing dependencies
sys.modules['dotenv'] = MagicMock()
sys.modules['langgraph'] = MagicMock()
sys.modules['langgraph.graph'] = MagicMock()
sys.modules['openai'] = MagicMock()
sys.modules['supabase'] = MagicMock()

from brain.graph import SilverAgentGraph

def mock_llm_response(prompt, **kwargs):
    """Return specific mock responses based on the prompt content."""
    # Price Analysis Mock
    if "Analyze the following silver price data" in prompt or "Analyze the following silver price data" in str(kwargs.get("messages", "")):
        return "Silver is showing a strong uptrend with support at $30.00."
    
    # News Analysis Mock
    if "Analyze the following news headlines" in prompt or "Analyze the following news headlines" in str(kwargs.get("messages", "")):
        return '''{
            "overall_sentiment": "positive",
            "sentiment_score": 0.8,
            "summary": "Market sentiment is bullish due to industrial demand.",
            "key_headlines": ["Silver demand rises in Asia"],
            "potential_impact": "high"
        }'''
    
    # Prediction Mock
    if "make a silver price prediction" in prompt or "make a silver price prediction" in str(kwargs.get("messages", "")):
        return '''{
            "decision": "bullish",
            "price_target": 32.50,
            "price_range": {"low": 31.00, "high": 33.00},
            "confidence_score": 0.9,
            "reasoning_chain": "Strong technicals matched with positive news flow.",
            "key_factors": ["Industrial demand", "Technical breakout"],
            "risks": ["Fed policy"]
        }'''
        
    return "{}"

class TestSilverAgent(unittest.IsolatedAsyncioTestCase):
    
    async def test_full_agent_flow(self):
        print("\n STARTING AGENT FLOW TEST")
        print("="*60)
        
        # 1. Setup Mock DB Client
        mock_db = MagicMock()
        mock_db.log_agent_action = MagicMock()
        
        # Mock Supabase Query Builders
        mock_price_query = MagicMock()
        mock_price_query.select.return_value.order.return_value.limit.return_value.execute.return_value.data = [{
            "price": 31.50,
            "currency": "USD",
            "fetched_at": datetime.utcnow().isoformat()
        }]
        
        mock_news_query = MagicMock()
        mock_news_query.select.return_value.order.return_value.limit.return_value.execute.return_value.data = [{
            "title": "Industrial demand spikes",
            "source_url": "example.com",
            "fetched_at": datetime.utcnow().isoformat()
        }]
        
        # 2. Setup Mock LLM Client
        mock_llm = MagicMock()
        mock_llm.chat_completion.side_effect = lambda messages, **kwargs: mock_llm_response(str(messages), **kwargs)
        
        # 3. Patch dependencies
        with patch('database.price_data', return_value=mock_price_query), \
             patch('database.news_data', return_value=mock_news_query), \
             patch('brain.llm_client.get_llm_client', return_value=mock_llm):
            
            # Initialize Agent
            agent = SilverAgentGraph(db_client=mock_db, llm_client=mock_llm)
            
            # Run Agent
            final_state = await agent.run(session_id="test-session-001")
            
            # 4. Verifications
            print("\n VERIFYING OUTPUTS")
            print("-" * 30)
            
            # Check Prediction
            pred = final_state.get("prediction", {})
            print(f"Prediction Decision: {pred.get('decision')}")
            self.assertEqual(pred.get("decision"), "bullish")
            self.assertEqual(pred.get("confidence_score"), 0.9)
            
            # Check DB Logging
            mock_db.log_agent_action.assert_called_once()
            call_args = mock_db.log_agent_action.call_args[0][0]
            
            print(f"Logged to DB:")
            print(f"- Session ID: {call_args['session_id']}")
            print(f"- Decision: {call_args['decision']}")
            print(f"- Reasoning: {call_args['reasoning_chain'][:50]}...")
            
            self.assertEqual(call_args['session_id'], "test-session-001")
            self.assertEqual(call_args['decision'], "bullish")
            self.assertIn("reasoning_chain", call_args)
            
            print("\n TEST PASSED: Agent successfully collected, analyzed, predicted, and logged.")

if __name__ == "__main__":
    unittest.main()
