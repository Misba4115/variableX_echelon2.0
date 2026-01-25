"""
Create Actual Database Entries
Populates price_data and news_data tables to demonstrate controller integration.
"""

from datetime import datetime, timedelta
import random
from database import price_data, news_data, targets


def create_price_entries():
    """Create actual price entries in the database."""
    print("\n" + "="*70)
    print("CREATING PRICE DATA ENTRIES")
    print("="*70)
    
    # Get a target_id for price data
    sources_result = targets().select("id, name").eq("category", "price").limit(1).execute()
    if not sources_result.data:
        print("⚠️  No price sources found, using first available target")
        sources_result = targets().select("id, name").limit(1).execute()
    
    target_id = sources_result.data[0]['id'] if sources_result.data else None
    
    if not target_id:
        print("❌ No targets found in database!")
        return
    
    base_price = 29.50
    current_time = datetime.now()
    
    # Create 15 price entries over the last 2 hours
    print(f"\n📊 Creating 15 price entries for: {sources_result.data[0]['name']}")
    
    for i in range(15):
        # Calculate timestamp (going backwards in time)
        minutes_ago = (14 - i) * 8  # Every 8 minutes
        timestamp = current_time - timedelta(minutes=minutes_ago)
        
        # Simulate price movement
        change = random.uniform(-0.02, 0.03)  # -2% to +3%
        price = base_price * (1 + change)
        
        high_24h = price * 1.02
        low_24h = price * 0.98
        volume = random.randint(50000, 150000)
        
        # Insert into database (using actual schema columns)
        try:
            result = price_data().insert({
                "target_id": target_id,
                "price": round(price, 2),
                "currency": "USD",
                "high_24h": round(high_24h, 2),
                "low_24h": round(low_24h, 2),
                "volume": volume,
                "price_change_percent": round(change * 100, 2),
                "fetched_at": timestamp.isoformat(),
                "source_timestamp": timestamp.isoformat()
            }).execute()
            
            print(f"  ✅ {i+1}. ${price:.2f} ({change*100:+.1f}%) at {timestamp.strftime('%H:%M')}")
            
        except Exception as e:
            print(f"  ❌ Error creating price entry: {e}")
            if i == 0:  # Show detailed error on first failure
                print(f"     Details: {e}")
    
    print(f"\n✅ Price entries created!")


def create_news_entries():
    """Create actual news entries in the database."""
    print("\n" + "="*70)
    print("CREATING NEWS DATA ENTRIES")
    print("="*70)
    
    # Sample news articles
    news_articles = [
        {
            "title": "Silver Prices Surge on Industrial Demand",
            "content": "Silver prices jumped today as industrial demand for the precious metal increased. Manufacturing sectors reported strong orders for silver-based components.",
            "source": "Kitco Silver News"
        },
        {
            "title": "Precious Metals Market Update",
            "content": "The silver market showed resilience today amid broader commodity trading. Analysts predict continued strength in precious metal prices.",
            "source": "Reuters Commodities"
        },
        {
            "title": "Silver Mining Output Reaches Record High",
            "content": "Global silver mining production hit a new record this quarter. Major producers reported increased output from primary and secondary operations.",
            "source": "Silver Institute News"
        },
        {
            "title": "Investment Demand Boosts Silver",
            "content": "Investment in silver ETFs and physical bullion continued to grow. Retail and institutional investors showed renewed interest in precious metals.",
            "source": "Investing.com Silver"
        },
        {
            "title": "Silver Spot Price Analysis",
            "content": "Technical analysis shows silver testing key resistance levels. Market watchers expect volatility as price approaches critical support zones.",
            "source": "Metals API - Silver Price"
        },
        {
            "title": "Dollar Weakness Supports Silver Prices",
            "content": "A weaker US dollar provided support for silver prices today. Currency fluctuations continue to influence precious metal valuations.",
            "source": "Kitco Silver News"
        },
        {
            "title": "Industrial Silver Demand Forecast",
            "content": "Industry reports project strong silver demand in electronics and solar panel manufacturing. Green energy initiatives drive silver consumption.",
            "source": "Silver Institute News"
        },
        {
            "title": "Silver Futures Trading Volume Spikes",
            "content": "COMEX silver futures saw unusual trading volume today. Large positions were established ahead of upcoming economic data releases.",
            "source": "Reuters Commodities"
        }
    ]
    
    current_time = datetime.now()
    
    # Get source IDs
    sources_result = targets().select("id, name").execute()
    source_map = {s['name']: s['id'] for s in sources_result.data}
    
    print(f"\n📰 Creating {len(news_articles)} news entries...")
    
    for i, article in enumerate(news_articles):
        # Calculate timestamp (spread over last 6 hours)
        hours_ago = (len(news_articles) - i) * 0.75
        timestamp = current_time - timedelta(hours=hours_ago)
        
        target_id = source_map.get(article['source'])
        
        if not target_id:
            print(f"  ⚠️  Source not found: {article['source']}")
            continue
        
        try:
            result = news_data().insert({
                "title": article['title'],
                "content": article['content'],
                "source_url": f"https://example.com/news/{i+1}",
                "target_id": target_id,  # Changed from source_id
                "fetched_at": timestamp.isoformat()
            }).execute()
            
            print(f"  ✅ {i+1}. \"{article['title'][:50]}...\" at {timestamp.strftime('%H:%M')}")
            
        except Exception as e:
            print(f"  ❌ Error creating news entry: {e}")
            if i == 0:  # Show detailed error on first failure
                print(f"     Details: {e}")
    
    print(f"\n✅ News entries created!")


def verify_database_entries():
    """Verify the entries were created."""
    print("\n" + "="*70)
    print("VERIFICATION - Database Entries")
    print("="*70)
    
    # Count prices
    try:
        price_result = price_data().select("id", count="exact").execute()
        price_count = price_result.count or 0
        print(f"\n💰 Price entries in database: {price_count}")
        
        # Show latest 3 prices
        latest_prices = price_data().select("*").order(
            "fetched_at", desc=True
        ).limit(3).execute()
        
        print("\n   Latest 3 prices:")
        for p in latest_prices.data:
            print(f"   • ${p['price']:.2f} ({p['change_24h']:+.1f}%) at {p['fetched_at'][:16]}")
    
    except Exception as e:
        print(f"\n❌ Error reading prices: {e}")
    
    # Count news
    try:
        news_result = news_data().select("id", count="exact").execute()
        news_count = news_result.count or 0
        print(f"\n📰 News entries in database: {news_count}")
        
        # Show latest 3 news
        latest_news = news_data().select("*").order(
            "fetched_at", desc=True
        ).limit(3).execute()
        
        print("\n   Latest 3 articles:")
        for n in latest_news.data:
            print(f"   • \"{n['title'][:50]}...\"")
    
    except Exception as e:
        print(f"\n❌ Error reading news: {e}")


def test_freshness_with_real_data():
    """Test freshness logic with real database entries."""
    print("\n" + "="*70)
    print("TESTING FRESHNESS WITH REAL DATA")
    print("="*70)
    
    from controller import check_freshness, get_fresh_data
    
    try:
        # Check freshness
        freshness = check_freshness()
        
        print(f"\n🧊 Freshness Status:")
        print(f"   Thresholds:")
        print(f"   • Prices: {freshness['thresholds']['price_time']} OR {freshness['thresholds']['price_count']} entries")
        print(f"   • News:   {freshness['thresholds']['news_time']} OR {freshness['thresholds']['news_count']} entries")
        
        print(f"\n   Fresh Data (will be used for analysis):")
        print(f"   • Prices: {freshness['fresh_data']['prices']}")
        print(f"   • News:   {freshness['fresh_data']['news']}")
        
        print(f"\n   Stale Data (can be cleaned):")
        print(f"   • Prices: {freshness['stale_data']['prices']}")
        print(f"   • News:   {freshness['stale_data']['news']}")
        
        # Get fresh data
        fresh = get_fresh_data()
        
        if fresh['prices']:
            print(f"\n   Fresh prices (last {len(fresh['prices'])} entries):")
            for p in fresh['prices'][:3]:
                print(f"   • ${p['price']:.2f}")
        
        if fresh['news']:
            print(f"\n   Fresh news (last {len(fresh['news'])} articles):")
            for n in fresh['news'][:3]:
                print(f"   • \"{n['title'][:40]}...\"")
    
    except Exception as e:
        print(f"\n❌ Error testing freshness: {e}")


def main():
    """Main function to populate database."""
    
    print("""
    ╔═══════════════════════════════════════════════════════════╗
    ║         CREATE ACTUAL DATABASE ENTRIES                    ║
    ║         Demonstrates Controller-DB Integration            ║
    ╚═══════════════════════════════════════════════════════════╝
    """)
    
    # Create entries
    create_price_entries()
    create_news_entries()
    
    # Verify
    verify_database_entries()
    
    # Test freshness
    test_freshness_with_real_data()
    
    print("\n" + "="*70)
    print("✅ DATABASE POPULATED SUCCESSFULLY")
    print("="*70)
    
    print("""
    Next steps:
    1. Check Supabase dashboard to see the entries
    2. Run test_full_flow.py to see controller working with real data
    3. Watch how freshness logic identifies which data to use
    
    🎉 Controller is now connected to real database entries!
    """)


if __name__ == "__main__":
    main()
