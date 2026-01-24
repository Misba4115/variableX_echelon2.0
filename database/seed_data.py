"""
Seed initial data into Supabase.
Run this after creating tables with schema.sql

Usage: python -m database.seed_data
"""

from database import targets, agent_logs

# Initial silver news sources and API endpoints
INITIAL_TARGETS = [
    {
        "name": "Kitco Silver News",
        "source_type": "scrape",
        "url": "https://www.kitco.com/news/silver",
        "category": "news",
        "is_active": True,
        "poll_interval_seconds": 3600  # 1 hour
    },
    {
        "name": "Reuters Commodities",
        "source_type": "scrape",
        "url": "https://www.reuters.com/markets/commodities/",
        "category": "news",
        "is_active": True,
        "poll_interval_seconds": 3600
    },
    {
        "name": "Investing.com Silver",
        "source_type": "scrape",
        "url": "https://www.investing.com/commodities/silver-news",
        "category": "news",
        "is_active": True,
        "poll_interval_seconds": 3600
    },
    {
        "name": "Silver Institute News",
        "source_type": "scrape",
        "url": "https://www.silverinstitute.org/news/",
        "category": "news",
        "is_active": True,
        "poll_interval_seconds": 7200  # 2 hours
    },
    {
        "name": "Metals API - Silver Price",
        "source_type": "api",
        "url": "https://metals-api.com/api/latest",
        "category": "price",
        "api_endpoint": "/latest?symbols=XAG",
        "is_active": True,
        "poll_interval_seconds": 300  # 5 minutes
    }
]


def seed_targets():
    """Insert initial targets into database."""
    print("🌱 Seeding targets table...")
    
    for target in INITIAL_TARGETS:
        try:
            result = targets().insert(target).execute()
            print(f"  ✅ Added: {target['name']}")
        except Exception as e:
            print(f"  ❌ Failed: {target['name']} - {e}")
    
    print("\n📊 Current targets:")
    all_targets = targets().select("name, source_type, category").execute()
    for t in all_targets.data:
        print(f"  - {t['name']} ({t['source_type']}, {t['category']})")


def seed_initial_log():
    """Create initial agent log entry."""
    print("\n📝 Creating initial agent log...")
    
    import uuid
    log_entry = {
        "session_id": str(uuid.uuid4()),
        "log_type": "action",
        "severity": "info",
        "agent_state": "initialized",
        "action_taken": "Database seeded with initial targets"
    }
    
    agent_logs().insert(log_entry).execute()
    print("  ✅ Initial log created")


if __name__ == "__main__":
    print("=" * 50)
    print("🥈 Silver Prediction Agent - Database Seeder")
    print("=" * 50 + "\n")
    
    seed_targets()
    seed_initial_log()
    
    print("\n✨ Done! Your database is ready.")
