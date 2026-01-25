"""
Autonomous Scraper Orchestrator.
Main entry point: Loops, asks BudgetManager, Acts, Stores, and Sleeps Adaptively.
"""
import asyncio
import time
from .budget import BudgetManager
from .sources import APIHandler, ScraperHandler
from .db_helper import ScraperDatabaseHelper
from database.db_client import get_db
from .config import SOURCES

async def run_autonomous_scraper():
    print("🚀 Starting Autonomous Silver Scraper Agent...")
    print("🧠 Initializing Budget Manager & Adaptive Logic...")
    
    # Initialize Components
    budget_mgr = BudgetManager()
    api_handler = APIHandler()
    scraper_handler = ScraperHandler()
    
    try:
        db = get_db() # Supabase client
    except Exception as e:
        print(f"❌ Database Connection Failed: {e}")
        print("   Check your .env file for SUPABASE_URL and SUPABASE_KEY.")
        return
    
    # The Infinite "Loop of Life"
    while True:
        try:
            # 1. ASK: Budget Manager, who should I call?
            next_source = budget_mgr.get_next_source()
            
            result_data = {}
            
            if not next_source:
                print("💤 No suitable source found (Budget/Priority). Skipping execution.")
            else:
                print(f"🎯 Selected Target: {next_source}")
                
                # 2. ACT: Execute the specific fetcher
                source_type = "unknown"
                try:
                    source_config = SOURCES[next_source]
                    source_type = source_config['type']
                    
                    if source_type == "api":
                        # Synchronous API Call
                        print(f"📡 Calling API: {next_source}...")
                        result_data = api_handler.fetch(next_source)
                        
                        # 3. STORE: Save to Supabase
                        if result_data:
                            # Format using db_helper
                            formatted = ScraperDatabaseHelper.format_price_for_db(result_data, symbol="XAG")
                            # Inject extra volatility fields if available
                            formatted["high_24h"] = result_data.get("high_24h")
                            formatted["low_24h"] = result_data.get("low_24h")
                            
                            db.insert_market_data(formatted)
                            print(f"✅ Price data stored: ${result_data.get('price')}")
                        else:
                            print("⚠️ API returned no data.")

                    elif source_type == "scraper":
                        # Async Scraper Call
                        print(f"🕷️ Scraping Web: {next_source}...")
                        result_data = await scraper_handler.fetch(next_source)
                        articles = result_data.get("articles", [])
                        
                        # 3. STORE: Save to Supabase
                        if articles:
                            formatted_batch = ScraperDatabaseHelper.format_news_batch_for_db(articles)
                            for article in formatted_batch:
                                db.insert_market_data(article)
                            print(f"✅ {len(articles)} News articles stored.")
                        else:
                            print("⚠️ Scraper found no articles.")

                except Exception as e:
                    print(f"❌ Execution Failed for {next_source}: {e}")

                # 4. LEARN: Update Budget Manager with results
                # This updates the 'Noise Score' and 'Volatility Factor'
                budget_mgr.update_metrics(next_source, result_data)

            # 5. SLEEP: Adaptive Sampling
            # Ask the brain how long to sleep based on market volatility
            sleep_time = budget_mgr.calculate_adaptive_sleep()
            
            print(f"⏳ Market Volatility: {budget_mgr.volatility_factor:.2f} | Sleeping {sleep_time}s...")
            print("-" * 50)
            
            await asyncio.sleep(sleep_time)

        except KeyboardInterrupt:
            print("\n🛑 Agent stopped by user.")
            break
        except Exception as e:
            print(f"❌ Critical Loop Error: {e}")
            print("   Sleeping 10s before restart...")
            await asyncio.sleep(10)

if __name__ == "__main__":
    asyncio.run(run_autonomous_scraper())
    