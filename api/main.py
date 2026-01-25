"""
FastAPI Application for Silver Prediction Agent
Provides REST API for controller, scraper, and monitoring.

Swagger Documentation: http://localhost:8000/docs
ReDoc Documentation: http://localhost:8000/redoc
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field
import uuid
import json

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Import controller modules
from controller import (
    run_collection_cycle,
    get_all_priorities,
    check_freshness,
    get_fresh_data,
    create_watchdog
)

# Import database and LLM modules
from database.supabase_client import (
    price_data as price_table,
    news_data as news_table,
    agent_logs as logs_table
)
from brain.llm_client import get_llm_client

# ============================================================
# PYDANTIC MODELS (for Swagger documentation)
# ============================================================

class TriggerResponse(BaseModel):
    """Response when triggering collection."""
    success: bool
    message: str
    timestamp: str
    collection_plan: Optional[Dict] = None

class StatusResponse(BaseModel):
    """System status response."""
    status: str = Field(..., description="System status (running, idle, error)")
    watchdog_running: bool = Field(..., description="Is watchdog monitoring active?")
    last_collection: Optional[str] = Field(None, description="Timestamp of last collection")
    uptime_seconds: float

class MetricResponse(BaseModel):
    """Quality metrics response."""
    sources: List[Dict] = Field(..., description="List of sources with quality metrics")
    timestamp: str

class FreshnessResponse(BaseModel):
    """Data freshness response."""
    fresh_prices: int
    fresh_news: int
    stale_prices: int
    stale_news: int
    thresholds: Dict

class CollectionPlanModel(BaseModel):
    """Collection plan structure."""
    should_collect: bool
    total_budget: int
    sources: List[Dict]
    timestamp: str

class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    version: str
    database_connected: bool


class PredictionRequest(BaseModel):
    """Request for real-time prediction."""
    include_history: bool = Field(True, description="Include price history in analysis")


class PredictionResponse(BaseModel):
    """Real-time prediction response."""
    success: bool
    decision: str = Field(..., description="BULLISH, BEARISH, or NEUTRAL")
    target_price: float = Field(..., description="Predicted target price in USD")
    confidence_score: float = Field(..., description="Confidence level (0.0-1.0)")
    time_horizon: str = Field(..., description="Time frame for prediction")
    key_factors: List[str] = Field(..., description="Key factors supporting prediction")
    risks: List[str] = Field(..., description="Potential risks")
    current_price: float = Field(..., description="Current silver price")
    log_id: str = Field(..., description="Agent log ID in database")
    timestamp: str = Field(..., description="Prediction timestamp")


# ============================================================
# FASTAPI APPLICATION
# ============================================================

app = FastAPI(
    title="Silver Prediction Agent API",
    description="""
    ## Autonomous Data Collection Agent for Silver Market Prediction
    
    This API provides endpoints for:
    * **Triggering** data collection cycles
    * **Monitoring** watchdog status
    * **Viewing** quality metrics and priorities
    * **Managing** data freshness
    
    ### Features
    * Event-driven watchdog monitoring
    * Adaptive budget allocation
    * Quality-based prioritization
    * Hybrid freshness tracking
    
    ### Getting Started
    1. Use `POST /api/trigger` to manually trigger collection
    2. Use `POST /api/watchdog/start` to enable automatic monitoring
    3. Check `GET /api/status` for system status
    4. View `GET /api/metrics` for source quality metrics
    """,
    version="1.0.0",
    docs_url="/docs",  # Swagger UI
    redoc_url="/redoc",  # ReDoc UI
    openapi_url="/openapi.json"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include test routes
# from api.test_routes import router as test_router
# app.include_router(test_router)

# Include scraper execution routes
from api.scraper_routes import router as scraper_router
app.include_router(scraper_router)

# Global state
watchdog_instance = None
app_start_time = datetime.now()


# ============================================================
# API ENDPOINTS
# ============================================================

@app.get("/", tags=["General"])
async def root():
    """
    Root endpoint - redirects to documentation.
    """
    return {
        "message": "Silver Prediction Agent API",
        "version": "1.0.0",
        "docs": "/docs",
        "redoc": "/redoc",
        "status": "/api/status"
    }


@app.get("/health", response_model=HealthResponse, tags=["General"])
async def health_check():
    """
    Health check endpoint.
    
    Returns system health status, version, and database connectivity.
    """
    # Simple DB check - try to get sources
    db_connected = False
    try:
        priorities = get_all_priorities()
        db_connected = len(priorities) > 0
    except Exception:
        pass
    
    return {
        "status": "healthy" if db_connected else "degraded",
        "version": "1.0.0",
        "database_connected": db_connected
    }


@app.post("/api/trigger", response_model=TriggerResponse, tags=["Collection"])
async def trigger_collection(budget: int = 10):
    """
    Manually trigger a data collection cycle.
    
    - **budget**: Total number of API calls to allocate (default: 10)
    
    Returns the collection plan with source allocations.
    """
    try:
        plan = run_collection_cycle(total_budget=budget)
        
        return {
            "success": True,
            "message": f"Collection triggered with budget of {budget} calls",
            "timestamp": datetime.now().isoformat(),
            "collection_plan": plan
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/status", response_model=StatusResponse, tags=["Monitoring"])
async def get_status():
    """
    Get current system status.
    
    Returns:
    - System status (running/idle)
    - Watchdog monitoring state
    - Uptime information
    """
    global watchdog_instance, app_start_time
    
    uptime = (datetime.now() - app_start_time).total_seconds()
    
    return {
        "status": "running" if watchdog_instance else "idle",
        "watchdog_running": watchdog_instance is not None and getattr(watchdog_instance, 'is_running', False),
        "last_collection": None,  # TODO: Track this
        "uptime_seconds": uptime
    }


@app.get("/api/metrics", response_model=MetricResponse, tags=["Monitoring"])
async def get_metrics():
    """
    Get quality metrics for all sources.
    
    Returns priority scores, utility, noise, and cost for each source.
    """
    try:
        priorities = get_all_priorities()
        
        return {
            "sources": priorities,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/freshness", response_model=FreshnessResponse, tags=["Data"])
async def get_freshness_status():
    """
    Get data freshness status.
    
    Shows how much data is fresh vs stale based on hybrid thresholds.
    """
    try:
        status = check_freshness()
        
        return {
            "fresh_prices": status['fresh_data']['prices'],
            "fresh_news": status['fresh_data']['news'],
            "stale_prices": status['stale_data']['prices'],
            "stale_news": status['stale_data']['news'],
            "thresholds": status['thresholds']
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/data/fresh", tags=["Data"])
async def get_fresh_data_endpoint():
    """
    Get all fresh data (prices and news).
    
    Returns only data that passes the hybrid freshness criteria.
    """
    try:
        fresh = get_fresh_data()
        
        return {
            "prices": fresh['prices'],
            "news": fresh['news'],
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/predict", response_model=PredictionResponse, tags=["Prediction"])
async def predict_silver_price(request: PredictionRequest = None):
    """
    Generate a real-time silver price prediction.
    
    This endpoint:
    1. Fetches latest price data from price_data table
    2. Fetches latest news from news_data table
    3. Analyzes market data using Gemini LLM
    4. Generates price prediction with 80/20 weighting
    5. Saves prediction to agent_logs table
    
    Returns prediction with decision, target price, and confidence score.
    """
    try:
        # Initialize LLM client
        llm_client = get_llm_client(model="gemini-2.5-flash")
        
        # Fetch latest price data
        price_response = price_table().select("*").order("fetched_at", desc=True).limit(1).execute()
        if not price_response.data or len(price_response.data) == 0:
            raise HTTPException(status_code=400, detail="No price data available in database")
        
        current_price_record = price_response.data[0]
        current_price = float(current_price_record.get('price', 0))
        
        # Fetch price history if requested
        price_history = []
        if request and request.include_history:
            history_response = price_table().select("*").order("fetched_at", desc=True).limit(10).execute()
            price_history = history_response.data if history_response.data else []
        
        # Fetch latest news data
        news_response = news_table().select("*").order("fetched_at", desc=True).limit(5).execute()
        news_items = news_response.data if news_response.data else []
        
        # Analyze market data
        market_analysis = llm_client.analyze_market_data(
            price_data=current_price_record,
            price_history=price_history
        )
        
        # Analyze news sentiment
        news_sentiment = llm_client.analyze_news_sentiment(news_items)
        
        # Generate prediction
        prediction = llm_client.make_prediction(
            market_data=current_price_record,
            news_analysis=news_sentiment,
            price_analysis=market_analysis
        )
        
        # Check if prediction was successful
        if "error" in prediction:
            raise HTTPException(status_code=500, detail=prediction.get("error"))
        
        # Prepare log entry
        session_id = str(uuid.uuid4())
        log_entry = {
            "session_id": session_id,
            "reasoning_chain": prediction.get("reasoning_chain", ""),
            "decision": prediction.get("decision", "NEUTRAL"),
            "prediction_value": json.dumps({
                "target_price": prediction.get("target_price"),
                "price_range": prediction.get("price_range"),
                "time_horizon": prediction.get("time_horizon"),
                "key_factors": prediction.get("key_factors", []),
                "risks": prediction.get("risks", []),
                "probability_up": prediction.get("probability_up"),
                "probability_down": prediction.get("probability_down")
            }),
            "confidence_score": prediction.get("confidence_score", 0.0),
            "raw_response": json.dumps(prediction)
        }
        
        # Save to agent_logs table
        log_response = logs_table().insert(log_entry).execute()
        log_id = log_response.data[0].get("id") if log_response.data else session_id
        
        # Return prediction
        return {
            "success": True,
            "decision": prediction.get("decision", "NEUTRAL"),
            "target_price": prediction.get("target_price", current_price),
            "confidence_score": prediction.get("confidence_score", 0.0),
            "time_horizon": prediction.get("time_horizon", "24 hours"),
            "key_factors": prediction.get("key_factors", []),
            "risks": prediction.get("risks", []),
            "current_price": current_price,
            "log_id": str(log_id),
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")


@app.post("/api/watchdog/start", tags=["Watchdog"])
async def start_watchdog():
    """
    Start the watchdog monitoring service.
    
    The watchdog will automatically trigger collection when:
    - Price changes > 2%
    - New news articles detected
    - Prediction accuracy drops
    """
    global watchdog_instance
    
    if watchdog_instance and getattr(watchdog_instance, 'is_running', False):
        return {
            "success": False,
            "message": "Watchdog is already running",
            "timestamp": datetime.now().isoformat()
        }
    
    try:
        watchdog_instance = create_watchdog()
        watchdog_instance.is_running = True
        
        return {
            "success": True,
            "message": "Watchdog started - monitoring for events",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/watchdog/stop", tags=["Watchdog"])
async def stop_watchdog():
    """
    Stop the watchdog monitoring service.
    """
    global watchdog_instance
    
    if not watchdog_instance:
        return {
            "success": False,
            "message": "Watchdog is not running",
            "timestamp": datetime.now().isoformat()
        }
    
    try:
        watchdog_instance.is_running = False
        watchdog_instance = None
        
        return {
            "success": True,
            "message": "Watchdog stopped",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/watchdog/status", tags=["Watchdog"])
async def watchdog_status():
    """
    Get watchdog status.
    """
    global watchdog_instance
    
    is_running = watchdog_instance is not None and getattr(watchdog_instance, 'is_running', False)
    
    return {
        "running": is_running,
        "last_price": getattr(watchdog_instance, 'last_price', None) if watchdog_instance else None,
        "threshold": 0.02,  # 2%
        "timestamp": datetime.now().isoformat()
    }


# ============================================================
# STARTUP/SHUTDOWN EVENTS
# ============================================================

@app.on_event("startup")
async def startup_event():
    """Run on application startup."""
    print("🚀 Silver Prediction Agent API Starting...")
    print("📖 Swagger UI: http://localhost:8000/docs")
    print("📖 ReDoc: http://localhost:8000/redoc")


@app.on_event("shutdown")
async def shutdown_event():
    """Run on application shutdown."""
    global watchdog_instance
    if watchdog_instance:
        watchdog_instance.is_running = False
    print("🛑 Silver Prediction Agent API Shutting Down...")


# ============================================================
# RUN (for development)
# ============================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
