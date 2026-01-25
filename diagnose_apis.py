import os
import json
import asyncio
from dotenv import load_dotenv
import requests

# Load env
load_dotenv()

async def test_finnhub():
    print("\n--- Testing Finnhub API ---")
    api_key = os.getenv("FINNHUB_API_KEY")
    if not api_key:
        print("❌ FINNHUB_API_KEY not found in .env")
        return
    
    symbol = "SLV"
    url = f"https://finnhub.io/api/v1/quote?symbol={symbol}&token={api_key}"
    
    try:
        r = requests.get(url, timeout=10)
        print(f"Status Code: {r.status_code}")
        raw = r.json()
        print(f"Raw Response: {json.dumps(raw, indent=2)}")
        
        if "c" in raw and raw["c"] > 0:
            print(f"✅ Success! Price: {raw['c']}")
        else:
            print("❌ Invalid price returned (0 or missing 'c')")
    except Exception as e:
        print(f"❌ Error: {e}")

async def test_news_agent():
    print("\n--- Testing News Agent (Kitco) ---")
    mistral_key = os.getenv("MISTRAL_API_KEY")
    if not mistral_key:
        print("❌ MISTRAL_API_KEY not found in .env")
        return
    
    from scraper import NewsAgent, ScraperDBHelper
    from database import targets
    
    try:
        db_helper = ScraperDBHelper()
        agent = NewsAgent(MISTRAL_API_KEY=mistral_key, db_helper=db_helper)
        
        # Test just scraping logic without DB update
        url = "https://www.kitco.com/news/silver"
        print(f"Scraping Kitco News at {url}...")
        articles, noise = await agent.scrape_source("Kitco Silver News", url)
        
        print(f"Articles Found: {len(articles)}")
        print(f"Noise Metrics: {json.dumps(noise, indent=2)}")
        
        if articles:
            print(f"✅ First Article Title: {articles[0]['title']}")
        else:
            print("❌ No articles found. Checking for blocks...")
            if noise.get("total_blocks", 0) > 0:
                print(f"Wait, {noise.get('total_blocks')} blocks found but 0 articles. Content mismatch?")
    except Exception as e:
        print(f"❌ News Agent Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_finnhub())
    asyncio.run(test_news_agent())
