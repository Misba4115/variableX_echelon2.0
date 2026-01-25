#!/usr/bin/env python
"""
Supabase Data Verification Script
Shows exactly what data is stored in your Supabase database.
"""

import os
from dotenv import load_dotenv

load_dotenv()

def main():
    print("\n" + "="*70)
    print("📊 SUPABASE DATA VERIFICATION")
    print("="*70)
    
    try:
        from database.supabase_client import (
            price_data, news_data, targets, agent_logs
        )
        
        # 1. Check targets
        print("\n1️⃣  DATA COLLECTION TARGETS")
        print("-" * 70)
        targets_response = targets().select("*").execute()
        if targets_response.data:
            print(f"Total targets: {len(targets_response.data)}\n")
            for t in targets_response.data:
                print(f"  📌 {t['name']}")
                print(f"     Category: {t['category']}")
                print(f"     Type: {t['source_type']}")
                print(f"     Active: {t['is_active']}")
                print(f"     Last scraped: {t.get('last_scraped_at', 'Never')[:10]}")
                print()
        else:
            print("❌ No targets found")
        
        # 2. Check price data
        print("\n2️⃣  PRICE DATA (Last 10 records)")
        print("-" * 70)
        prices_response = price_data().select("*").order("fetched_at", desc=True).limit(10).execute()
        if prices_response.data:
            print(f"Total price records in database: {len(prices_response.data)}\n")
            for i, p in enumerate(prices_response.data[:5], 1):
                target_id = p.get('target_id', 'N/A')
                # Find target name
                target_name = "Unknown"
                if targets_response.data:
                    for t in targets_response.data:
                        if t['id'] == target_id:
                            target_name = t['name']
                            break
                
                print(f"  💰 Record {i}:")
                print(f"     Price: ${p['price']} {p.get('currency', 'USD')}")
                print(f"     Change: {p.get('price_change', 0)} ({p.get('price_change_percent', 0)}%)")
                print(f"     High: ${p.get('high_24h', 0)} | Low: ${p.get('low_24h', 0)}")
                print(f"     Source: {target_name}")
                print(f"     Fetched: {str(p.get('fetched_at', 'N/A'))[:19]}")
                print()
        else:
            print("❌ No price data found")
        
        # 3. Check news data
        print("\n3️⃣  NEWS DATA (Last 10 records)")
        print("-" * 70)
        news_response = news_data().select("*").order("fetched_at", desc=True).limit(10).execute()
        if news_response.data:
            print(f"Total news records in database: {len(news_response.data)}\n")
            for i, n in enumerate(news_response.data[:5], 1):
                target_id = n.get('target_id', 'N/A')
                # Find target name
                target_name = "Unknown"
                if targets_response.data:
                    for t in targets_response.data:
                        if t['id'] == target_id:
                            target_name = t['name']
                            break
                
                print(f"  📰 Article {i}:")
                print(f"     Title: {n.get('title', 'No title')[:60]}...")
                print(f"     Content: {n.get('content', 'No content')[:60]}...")
                print(f"     Source: {target_name}")
                print(f"     URL: {n.get('source_url', 'N/A')[:50]}...")
                print(f"     Fetched: {str(n.get('fetched_at', 'N/A'))[:19]}")
                print()
        else:
            print("❌ No news data found")
        
        # 4. Check agent logs
        print("\n4️⃣  AGENT EXECUTION LOGS (Last 10 records)")
        print("-" * 70)
        logs_response = agent_logs().select("*").order("created_at", desc=True).limit(10).execute()
        if logs_response.data:
            print(f"Total log records: {len(logs_response.data)}\n")
            for i, log in enumerate(logs_response.data[:5], 1):
                reasoning = log.get('reasoning_chain', 'N/A')
                decision = log.get('decision', 'N/A')
                
                print(f"  📝 Log {i}:")
                print(f"     Reasoning: {str(reasoning)[:60]}...")
                print(f"     Decision: {str(decision)[:60]}...")
                print(f"     Confidence: {log.get('confidence_score', 0)}")
                print(f"     Created: {str(log.get('created_at', 'N/A'))[:19]}")
                print()
        else:
            print("❌ No log data found")
        
        # 5. Summary Statistics
        print("\n5️⃣  SUMMARY STATISTICS")
        print("-" * 70)
        print(f"Total targets configured: {len(targets_response.data) if targets_response.data else 0}")
        print(f"Total price records: {len(prices_response.data) if prices_response.data else 0}")
        print(f"Total news records: {len(news_response.data) if news_response.data else 0}")
        print(f"Total log records: {len(logs_response.data) if logs_response.data else 0}")
        
        # Calculate stats
        if prices_response.data:
            prices = [p['price'] for p in prices_response.data]
            print(f"\n📊 Price Statistics:")
            print(f"  Average: ${sum(prices)/len(prices):.2f}")
            print(f"  Min: ${min(prices):.2f}")
            print(f"  Max: ${max(prices):.2f}")
        
        print("\n" + "="*70)
        print("✅ Database verification complete!")
        print("="*70 + "\n")
        
    except Exception as e:
        print(f"❌ Error: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
