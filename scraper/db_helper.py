"""
db_helper.py: Database abstraction layer for the Silver Prediction Agent.
Handles all Supabase interactions using the centralized client.
"""
from typing import List, Dict, Any, Optional
from datetime import datetime

# Import the helper functions from your Supabase client file
# Ensure the filename below matches your actual client filename (e.g., supabase_client.py)
# Import from the database package
from database.supabase_client import targets, price_data, news_data, agent_logs

class ScraperDBHelper:
    
    # --- TARGET MANAGEMENT ---
    
    @staticmethod
    def get_next_news_target() -> Optional[Dict]:
        """Fetch the next active news scraping target."""
        try:
            print("[DB_Helper] Fetching next news target...")
            response = targets().select("*")\
                .eq("category", "news")\
                .eq("is_active", True)\
                .limit(1).execute()
            print(f"[DB_Helper] Found news target: {response.data[0]['name'] if response.data else 'None'}")
            return response.data[0] if response.data else None
        except Exception as e:
            print(f"[DB_Helper] Error fetching news target: {e}")
            return None

    @staticmethod
    def get_next_stock_target() -> Optional[Dict]:
        """Fetch the next active stock/API target."""
        try:
            print("[DB_Helper] Fetching next stock target...")
            response = targets().select("*")\
                .eq("category", "price")\
                .eq("is_active", True)\
                .limit(1).execute()
            print(f"[DB_Helper] Found stock target: {response.data[0]['name'] if response.data else 'None'}")
            return response.data[0] if response.data else None
        except Exception as e:
            print(f"[DB_Helper] Error fetching stock target: {e}")
            return None

    @staticmethod
    def mark_target_completed(target_id: str):
        """Update a target status to completed."""
        try:
            targets().update({"last_scraped_at": datetime.utcnow().isoformat()})\
                .eq("id", target_id).execute()
        except Exception as e:
            print(f"[DB_Helper] Error marking target completed: {e}")

    # --- DATA INSERTION ---

    @staticmethod
    def insert_news_data(articles: List[Dict]) -> bool:
        """Insert structured news articles into news_data table."""
        try:
            if not articles:
                return False
            # Uses the news_data() helper from your client
            news_data().insert(articles).execute()
            return True
        except Exception as e:
            print(f"[DB_Helper] Error inserting news: {e}")
            return False

    @staticmethod
    def insert_stock_data(data_list: List[Dict], target_id: Optional[str] = None) -> bool:
        """Insert real-time price data into price_data table."""
        try:
            if not data_list:
                return False
            
            # Add target_id to all items
            if target_id:
                for item in data_list:
                    item["target_id"] = target_id
                    
            # Uses the price_data() helper from your client
            price_data().insert(data_list).execute()
            return True
        except Exception as e:
            print(f"[DB_Helper] Error inserting stock data: {e}")
            return False

    # --- LOGGING & METRICS ---

    @staticmethod
    def insert_noise_metrics(category: str, source: str, metrics: Dict):
        """Log performance and noise metrics for the controller."""
        try:
            log_entry = {
                "category": category,
                "source": source,
                "metrics": metrics,
                "timestamp": datetime.utcnow().isoformat(),
                "level": "INFO"
            }
            agent_logs().insert(log_entry).execute()
        except Exception as e:
            print(f"[DB_Helper] Error logging metrics: {e}")

    # --- FORMATTING HELPER ---

    @staticmethod
    def format_stock_data(price, currency, change, change_p, high, low, vol, ts) -> Dict:
        """
        Helper to standardize stock data format before DB insertion.
        Returns data in the specific order requested:
        price, currency, price_change, price_change_percent, high_24h, low_24h, volume, fetched_at, source_timestamp
        """
        return {
            "price": price,
            "currency": currency,
            "price_change": change,
            "price_change_percent": change_p,
            "high_24h": high,
            "low_24h": low,
            "volume": vol,
            "fetched_at": datetime.utcnow().isoformat(),
            "source_timestamp": ts
        }