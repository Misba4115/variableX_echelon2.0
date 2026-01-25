"""
Scraper Execution Routes - Complete Flow Integration

These routes execute the FULL flow:
1. Controller creates collection plan
2. Scraper executes (StockAgent + NewsAgent)
3. Data saved to DB
4. Quality metrics updated
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from datetime import datetime
from typing import Dict
from pydantic import BaseModel
import time

from controller import run_collection_cycle, update_quality_after_scrape
from scraper import StockAgent, NewsAgent, ScraperDBHelper, news_agent_available


router = APIRouter(prefix="/api/scrape", tags=["Scraper Execution"])


class ScrapeResponse(BaseModel):
    """Response from scrape execution."""
    success: bool
    message: str
    execution_time_seconds: float
    results: Dict
    timestamp: str


@router.post("/execute-full-flow", response_model=ScrapeResponse)
async def execute_full_scraping_flow(budget: int = 10):
    """
    🚀 Execute the COMPLETE flow from controller to scraper to DB updates.
    
    **Full Flow:**
    1. Controller creates collection plan (prioritizer + budget)
    2. Execute scraping (StockAgent + NewsAgent)
    3. Save data to price_data and news_data tables
    4. Update quality metrics (avg_utility, avg_noise, avg_cost)
    
    **Parameters:**
    - budget: Total API calls to allocate (default: 10)
    
    **This is the MAIN endpoint that actually does real scraping!**
    """
    start_time = time.time()
    results = {
        "collection_plan": None,
        "stock_scraping": None,
        "news_scraping": None,
        "db_entries_created": 0
    }
    
    try:
        # STEP 1: Controller creates collection plan
        print("\n" + "="*70)
        print("STEP 1: Creating collection plan via controller")
        print("="*70)
        
        collection_plan = run_collection_cycle(total_budget=budget)
        results["collection_plan"] = collection_plan
        
        if not collection_plan.get("should_collect"):
            return {
                "success": False,
                "message": "Controller decided not to collect (conditions not met)",
                "execution_time_seconds": time.time() - start_time,
                "results": results,
                "timestamp": datetime.now().isoformat()
            }
        
        # STEP 2: Initialize scraper helpers
        print("\n" + "="*70)
        print("STEP 2: Initializing scrapers")
        print("="*70)
        
        db_helper = ScraperDBHelper()
        
        # STEP 3: Execute Stock Scraping
        print("\n" + "="*70)
        print("STEP 3: Executing Stock Agent")
        print("="*70)
        
        try:
            stock_agent = StockAgent(db_helper=db_helper)
            stock_result = stock_agent.execute_from_controller()
            results["stock_scraping"] = stock_result
            print(f"✅ Stock scraping: {stock_result.get('success', False)}")
        except Exception as e:
            print(f"⚠️  Stock scraping failed: {e}")
            results["stock_scraping"] = {"success": False, "error": str(e)}
        
        # STEP 4: Execute News Scraping
        print("\n" + "="*70)
        print("STEP 4: Executing News Agent")
        print("="*70)
        
        try:
            import os
            mistral_key = os.getenv("MISTRAL_API_KEY")
            if not mistral_key:
                print("⚠️  MISTRAL_API_KEY not found, skipping news scraping")
                results["news_scraping"] = {"success": False, "error": "Missing API key"}
            elif not news_agent_available or NewsAgent is None:
                print("⚠️  NewsAgent not available (Playwright/dependencies missing)")
                results["news_scraping"] = {"success": False, "error": "NewsAgent unavailable"}
            else:
                news_agent = NewsAgent(MISTRAL_API_KEY=mistral_key, db_helper=db_helper)
                news_result = await news_agent.execute_from_controller()
                results["news_scraping"] = news_result
                print(f"✅ News scraping: {news_result.get('success', False)}")
        except Exception as e:
            print(f"⚠️  News scraping failed: {e}")
            results["news_scraping"] = {"success": False, "error": str(e)}
        
        # STEP 5: Get counts of new entries
        print("\n" + "="*70)
        print("STEP 5: Counting new database entries")
        print("="*70)
        
        from database import price_data, news_data
        
        # Count recent entries (last 5 minutes)
        from datetime import timedelta
        recent_time = (datetime.utcnow() - timedelta(minutes=5)).isoformat()
        
        recent_prices = price_data().select("id").gte("fetched_at", recent_time).execute()
        recent_news = news_data().select("id").gte("fetched_at", recent_time).execute()
        
        price_count = len(recent_prices.data) if recent_prices.data else 0
        news_count = len(recent_news.data) if recent_news.data else 0
        results["db_entries_created"] = price_count + news_count
        
        print(f"📊 New entries: {price_count} prices, {news_count} news")
        
        # Success summary
        execution_time = time.time() - start_time
        
        print("\n" + "="*70)
        print("✅ FULL FLOW COMPLETED")
        print("="*70)
        print(f"Execution time: {execution_time:.2f}s")
        print(f"DB entries created: {results['db_entries_created']}")
        
        return {
            "success": True,
            "message": f"Full flow executed successfully. Created {results['db_entries_created']} DB entries.",
            "execution_time_seconds": execution_time,
            "results": results,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        execution_time = time.time() - start_time
        raise HTTPException(
            status_code=500,
            detail=f"Flow execution failed: {str(e)}"
        )


@router.post("/stock-only")
async def execute_stock_scraping_only():
    """
    Execute ONLY stock/price scraping (StockAgent).
    
    Faster than full flow if you only need price data.
    """
    start_time = time.time()
    
    try:
        db_helper = ScraperDBHelper()
        stock_agent = StockAgent(db_helper=db_helper)
        
        result = stock_agent.execute_from_controller()
        
        return {
            "success": result.get("success", False),
            "message": "Stock scraping executed",
            "execution_time_seconds": time.time() - start_time,
            "result": result,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/news-only")
async def execute_news_scraping_only():
    """
    Execute ONLY news scraping (NewsAgent).
    
    Requires MISTRAL_API_KEY in environment.
    """
    start_time = time.time()
    
    try:
        import os
        mistral_key = os.getenv("MISTRAL_API_KEY")
        
        if not mistral_key:
            raise HTTPException(
                status_code=400,
                detail="MISTRAL_API_KEY not found in environment"
            )
        
        db_helper = ScraperDBHelper()
        news_agent = NewsAgent(MISTRAL_API_KEY=mistral_key, db_helper=db_helper)
        
        result = news_agent.execute_from_controller()
        
        return {
            "success": result.get("success", False),
            "message": "News scraping executed",
            "execution_time_seconds": time.time() - start_time,
            "result": result,
            "timestamp": datetime.now().isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/scraping-status")
async def get_scraping_status():
    """
    Check if scraping agents are configured properly.
    
    Returns which API keys are available.
    """
    import os
    
    return {
        "alpha_vantage_configured": bool(os.getenv("ALPHA_VANTAGE_API_KEY")),
        "finnhub_configured": bool(os.getenv("FINNHUB_API_KEY")),
        "mistral_configured": bool(os.getenv("MISTRAL_API_KEY")),
        "timestamp": datetime.now().isoformat()
    }
