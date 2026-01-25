"""
LangGraph State Machine for the Silver Prediction Agent.
Defines the agent workflow and state transitions.
"""

import os
from typing import Any, Dict, List, TypedDict, Annotated
from datetime import datetime
from dotenv import load_dotenv

# Note: Full implementation requires langgraph and langchain
# This is the structure for the state machine

load_dotenv()


class AgentGraphState(TypedDict):
    """State schema for the agent graph."""
    # Session info
    session_id: str
    current_step: str
    
    # Collected data
    price_data: Dict[str, Any]
    news_data: List[Dict[str, Any]]
    
    # Analysis results
    price_analysis: str
    news_sentiment: Dict[str, Any]
    
    # Predictions
    prediction: Dict[str, Any]
    confidence: float
    
    # Execution tracking
    messages: List[Dict[str, str]]
    errors: List[str]
    last_updated: str


class SilverAgentGraph:
    """
    LangGraph-based state machine for autonomous silver prediction.
    
    Workflow:
    1. COLLECT: Gather price data and news
    2. ANALYZE: Process data and extract insights  
    3. PREDICT: Generate price predictions
    4. LOG: Store results and reasoning
    """
    
    def __init__(self, db_client=None, state_manager=None, llm_client=None):
        """
        Initialize the agent graph.
        
        Args:
            db_client: Database client for persistence
            state_manager: State manager for tracking
            llm_client: LLM client for analysis (optional, will create if not provided)
        """
        self.db_client = db_client
        self.state_manager = state_manager
        self.llm_client = llm_client
        self._graph = None
        
    def _build_graph(self):
        """
        Build the LangGraph state machine.
        """
        try:
            from langgraph.graph import StateGraph, END
        except ImportError:
            raise ImportError(
                "langgraph package not installed. Run: pip install langgraph"
            )
        
        # Create state graph
        graph = StateGraph(AgentGraphState)
        
        # Add nodes
        graph.add_node("collect", self._collect_node)
        graph.add_node("analyze", self._analyze_node)
        graph.add_node("predict", self._predict_node)
        graph.add_node("log", self._log_node)
        
        # Define edges
        graph.add_edge("collect", "analyze")
        graph.add_edge("analyze", "predict")
        graph.add_edge("predict", "log")
        graph.add_edge("log", END)
        
        # Set entry point
        graph.set_entry_point("collect")
        
        # Compile the graph
        self._graph = graph.compile()
        
    async def _collect_node(self, state: AgentGraphState) -> AgentGraphState:
        """
        Collection node: Gather price and news data from database.
        """
        from database import price_data, news_data
        
        state["messages"].append({
            "step": "collect",
            "status": "started",
            "timestamp": datetime.utcnow().isoformat()
        })
        
        try:
            # Get latest price data from DB
            print("📊 Fetching silver price data from DB...")
            try:
                # Get latest price record
                response = price_data().select("*").order("fetched_at", desc=True).limit(1).execute()
                latest_price = response.data[0] if response.data else {}
                
                if latest_price:
                    # Get 7-day old price for change calculation if not already present
                    # Note: We are just fetching what's available
                    pass
                
                state["price_data"] = latest_price
            except Exception as e:
                print(f"⚠️  Could not fetch price data: {str(e)}")
                state["errors"].append(f"Price DB error: {str(e)}")
                state["price_data"] = {}
            
            # Get latest news data from DB
            print("📰 Fetching silver news from DB...")
            news_items = []
            try:
                # Fetch recent news
                response = news_data().select("*").order("fetched_at", desc=True).limit(10).execute()
                news_items = response.data if response.data else []
            except Exception as e:
                print(f"⚠️  Could not fetch news data: {str(e)}")
                state["errors"].append(f"News DB error: {str(e)}")
            
            state["news_data"] = news_items
            
            state["current_step"] = "collect_complete"
            state["messages"].append({
                "step": "collect",
                "status": "complete",
                "price_collected": bool(state["price_data"]),
                "news_count": len(news_items),
                "timestamp": datetime.utcnow().isoformat()
            })
            
            print(f"✅ Collection complete: Price=${state['price_data'].get('price', 'N/A')}, News={len(news_items)} items")
            
        except Exception as e:
            error_msg = f"Collection error: {str(e)}"
            state["errors"].append(error_msg)
            print(f"❌ {error_msg}")
        
        state["last_updated"] = datetime.utcnow().isoformat()
        return state
    
    async def _analyze_node(self, state: AgentGraphState) -> AgentGraphState:
        """
        Analysis node: Process collected data using LLM.
        """
        from brain.prompts import SYSTEM_PROMPTS
        from brain.llm_client import get_llm_client 
        
        state["messages"].append({
            "step": "analyze",
            "status": "started",
            "timestamp": datetime.utcnow().isoformat()
        })
        
        try:
            print("🤔 Analyzing market data...")
            
            # Initialize LLM client if not provided
            if not self.llm_client:
                self.llm_client = get_llm_client()
            
            # Get price history from database if available
            price_history = []
            if self.db_client:
                try:
                    price_history = self.db_client.get_price_history(symbol="XAG", days=7)
                except Exception:
                    pass
            
            # Analyze price data
            price_analysis = self.llm_client.analyze_market_data(
                state["price_data"],
                price_history=price_history,
                system_prompt=SYSTEM_PROMPTS["analyst"]
            )
            state["price_analysis"] = price_analysis
            
            # Analyze news sentiment
            news_sentiment = self.llm_client.analyze_news_sentiment(
                state["news_data"],
                system_prompt=SYSTEM_PROMPTS["analyst"]
            )
            state["news_sentiment"] = news_sentiment
            
            state["current_step"] = "analyze_complete"
            state["messages"].append({
                "step": "analyze",
                "status": "complete",
                "sentiment": news_sentiment.get("overall_sentiment"),
                "timestamp": datetime.utcnow().isoformat()
            })
            
            print(f"✅ Analysis complete: Sentiment={news_sentiment.get('overall_sentiment', 'N/A')}")
            
        except Exception as e:
            error_msg = f"Analysis error: {str(e)}"
            state["errors"].append(error_msg)
            state["price_analysis"] = f"Analysis failed: {str(e)}"
            state["news_sentiment"] = {"overall_sentiment": "neutral", "error": str(e)}
            print(f"❌ {error_msg}")
        
        state["last_updated"] = datetime.utcnow().isoformat()
        return state
    
    async def _predict_node(self, state: AgentGraphState) -> AgentGraphState:
        """
        Prediction node: Generate price predictions using LLM.
        """
        from brain.prompts import SYSTEM_PROMPTS
        from brain.llm_client import get_llm_client
        
        state["messages"].append({
            "step": "predict",
            "status": "started",
            "timestamp": datetime.utcnow().isoformat()
        })
        
        try:
            print("🔮 Generating prediction...")
            
            # Initialize LLM client if not provided
            if not self.llm_client:
                self.llm_client = get_llm_client()
            
            # Generate prediction
            prediction = self.llm_client.make_prediction(
                market_data=state["price_data"],
                news_analysis=state["news_sentiment"],
                price_analysis=state["price_analysis"],
                system_prompt=SYSTEM_PROMPTS["predictor"]
            )
            
            state["prediction"] = prediction
            state["confidence"] = prediction.get("confidence_score", 0.0)
            
            state["current_step"] = "predict_complete"
            state["messages"].append({
                "step": "predict",
                "status": "complete",
                "direction": prediction.get("direction"),
                "confidence": state["confidence"],
                "timestamp": datetime.utcnow().isoformat()
            })
            
            print(f"✅ Prediction: {prediction.get('decision', 'N/A').upper()} "
                  f"(confidence: {state['confidence']:.2f})")
            
        except Exception as e:
            error_msg = f"Prediction error: {str(e)}"
            state["errors"].append(error_msg)
            state["prediction"] = {
                "decision": "neutral",
                "direction": "neutral",
                "error": str(e),
                "reasoning_chain": "Prediction failed due to error"
            }
            state["confidence"] = 0.0
            print(f"❌ {error_msg}")
        
        state["last_updated"] = datetime.utcnow().isoformat()
        return state
    
    async def _log_node(self, state: AgentGraphState) -> AgentGraphState:
        """
        Logging node: Persist results to database.
        """
        state["messages"].append({
            "step": "log",
            "status": "started",
            "timestamp": datetime.utcnow().isoformat()
        })
        
        try:
            print("💾 Logging results...")
            
            if self.db_client and state.get("prediction"):
                self.db_client.log_agent_action({
                    "session_id": state["session_id"],
                    "reasoning_chain": state["prediction"].get("reasoning_chain", "") + "\n\nAnalysis: " + str(state.get("price_analysis", "")),
                    "decision": state["prediction"].get("decision"),
                    "prediction_value": state["prediction"],
                    "confidence_score": state["confidence"],
                    "raw_response": {
                        "news_sentiment": state.get("news_sentiment", {}),
                        "price_data": state.get("price_data", {})
                    },
                    "created_at": datetime.utcnow().isoformat()
                })
                
                print("✅ Results logged to database")
            else:
                print("⚠️  Database not available, results not persisted")
            
            state["current_step"] = "complete"
            state["messages"].append({
                "step": "log",
                "status": "complete",
                "timestamp": datetime.utcnow().isoformat()
            })
            
        except Exception as e:
            error_msg = f"Logging error: {str(e)}"
            state["errors"].append(error_msg)
            print(f"❌ {error_msg}")
        
        state["last_updated"] = datetime.utcnow().isoformat()
        return state
    
    def get_initial_state(self, session_id: str = None) -> AgentGraphState:
        """Create initial state for a new run."""
        import uuid
        return AgentGraphState(
            session_id=session_id or str(uuid.uuid4()),
            current_step="initialized",
            price_data={},
            news_data=[],
            price_analysis="",
            news_sentiment={},
            prediction={},
            confidence=0.0,
            messages=[],
            errors=[],
            last_updated=datetime.utcnow().isoformat()
        )
    
    async def run(self, session_id: str = None) -> AgentGraphState:
        """
        Execute the agent workflow.
        
        Args:
            session_id: Optional session ID for tracking
        
        Returns:
            Final agent state after execution
        """
        print("🚀 Starting Silver Prediction Agent...")
        print(f"Session ID: {session_id or 'auto-generated'}")
        print("-" * 60)
        
        state = self.get_initial_state(session_id)
        
        # Build graph if not already built
        if not self._graph:
            try:
                self._build_graph()
                print("✅ LangGraph state machine initialized")
                
                # Execute using LangGraph
                result = await self._graph.ainvoke(state)
                return result
            except ImportError:
                print("⚠️  LangGraph not available, using sequential execution")
        
        # Fallback: Execute nodes sequentially without LangGraph
        state = await self._collect_node(state)
        state = await self._analyze_node(state)
        state = await self._predict_node(state)
        state = await self._log_node(state)
        
        print("-" * 60)
        print("✅ Agent execution complete!")
        
        return state

