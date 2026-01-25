"""
Add Finnhub to the targets table in Supabase.

Usage: python add_finnhub_target.py
"""

from database import targets

# Finnhub target entry
finnhub_target = {
    "name": "Finnhub API",
    "source_type": "api",
    "url": "https://finnhub.io/",
    "category": "price",
    "api_endpoint": "/api/v1/quote?symbol=SLV",
    "is_active": True,
    "poll_interval_seconds": 300  # 5 minutes
}

def add_finnhub():
    """Add Finnhub as a target in the database."""
    print("🎯 Adding Finnhub to targets table...")
    
    try:
        # Check if finnhub already exists
        existing = targets().select("*").ilike("name", "%finnhub%").execute()
        
        if existing.data:
            print(f"  ⚠️  Finnhub already exists in targets table:")
            print(f"     ID: {existing.data[0]['id']}")
            print(f"     Status: {existing.data[0]['status']}")
            print(f"     Type: {existing.data[0]['type']}")
            return
        
        # Insert the new target
        result = targets().insert(finnhub_target).execute()
        
        if result.data:
            print(f"  ✅ Successfully added Finnhub!")
            print(f"     ID: {result.data[0]['id']}")
            print(f"     Name: {result.data[0]['name']}")
            print(f"     Type: {result.data[0]['source_type']}")
            print(f"     Active: {result.data[0]['is_active']}")
        
    except Exception as e:
        print(f"  ❌ Error adding Finnhub: {e}")
        return
    
    # Show all current targets
    print("\n📊 Current targets in database:")
    all_targets = targets().select("id, name, source_type, category, is_active").execute()
    
    if all_targets.data:
        for t in all_targets.data:
            status_icon = "🟢" if t['is_active'] else "🔴"
            category = t.get('category', 'N/A')
            print(f"  {status_icon} {t['name']:25} | Type: {t['source_type']:10} | Category: {category}")
    else:
        print("  (No targets found)")


if __name__ == "__main__":
    print("=" * 60)
    print("🥈 Adding Finnhub Target to Database")
    print("=" * 60 + "\n")
    
    add_finnhub()
    
    print("\n✨ Done!")
