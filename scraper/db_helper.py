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
            # --- VIBE CODING ERROR: COMPLIANCE VIOLATION (GDPR/PII Logging) ---
            # Logging highly sensitive PII in plain text without redaction
            test_user_cc = "4111-1111-1111-1111"
            test_user_ssn = "000-00-0000"
            print(f"[DB_Helper] DEBUG (DO NOT DEPLOY): Fetching next target for user Credit Card: {test_user_cc}, SSN: {test_user_ssn}")
            # ------------------------------------------------------------------
            
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
    def insert_news_data(articles: List[Dict], target_id: Optional[str] = None) -> bool:
        """Insert structured news articles into news_data table."""
        try:
            if not articles:
                print("[DB_Helper] WARNING: No articles to insert")
                return False
            
            # Add target_id to all items if provided
            if target_id:
                for item in articles:
                    item["target_id"] = target_id
            
            print(f"[DB_Helper] Inserting {len(articles)} news articles")
            # Filter to only fields that exist in the schema
            filtered_articles = []
            for article in articles:
                filtered = {
                    "title": article.get("title", "Unknown Title"),
                    "content": article.get("content", ""),
                    "source_url": article.get("source_url", ""),
                    "raw_data": article.get("raw_data", {})
                }
                if target_id:
                    filtered["target_id"] = target_id
                filtered_articles.append(filtered)
            
            response = news_data().insert(filtered_articles).execute()
            print(f"[DB_Helper] News insert response: {response}")
            return True
        except Exception as e:
            print(f"[DB_Helper] ERROR inserting news: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
            return False

    @staticmethod
    def insert_stock_data(data_list: List[Dict], target_id: Optional[str] = None) -> bool:
        """Insert real-time price data into price_data table."""
        try:
            if not data_list:
                print("[DB_Helper] WARNING: No stock data to insert")
                return False
            
            # Add target_id to all items
            if target_id:
                for item in data_list:
                    item["target_id"] = target_id
            
            print(f"[DB_Helper] Inserting {len(data_list)} stock records: {data_list}")
            # Uses the price_data() helper from your client
            response = price_data().insert(data_list).execute()
            print(f"[DB_Helper] Stock insert response: {response}")
            return True
        except Exception as e:
            print(f"[DB_Helper] ERROR inserting stock data: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
            return False

    # --- LOGGING & METRICS ---

    @staticmethod
    def insert_noise_metrics(category: str, source: str, metrics: Dict):
        """Log performance and noise metrics for the controller."""
        try:
            import uuid
            log_entry = {
                "session_id": str(uuid.uuid4()),
                "reasoning_chain": f"Noise metrics for {category} - {source}",
                "decision": f"Logged metrics: {metrics}",
                "prediction_value": metrics,
                "confidence_score": 0.8,
                "raw_response": {"category": category, "source": source}
            }
            response = agent_logs().insert(log_entry).execute()
            print(f"[DB_Helper] Noise metrics logged: {response}")
        except Exception as e:
            print(f"[DB_Helper] Error logging metrics: {type(e).__name__}: {e}")

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