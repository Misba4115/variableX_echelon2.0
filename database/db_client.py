"""
Supabase Database Client for the Silver Prediction Agent.
Handles all database operations with Supabase.
"""

import os
from datetime import datetime
from typing import Any, Dict, List, Optional
from dotenv import load_dotenv
from supabase import create_client, Client

# Load environment variables
load_dotenv()


class SupabaseClient:
    """
    Supabase client wrapper for database operations.
    """
    
    _instance: Optional["SupabaseClient"] = None
    _client: Optional[Client] = None
    
    def __new__(cls) -> "SupabaseClient":
        """Singleton pattern to ensure one client instance."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize the Supabase client."""
        if self._client is None:
            url = os.getenv("SUPABASE_URL")
            key = os.getenv("SUPABASE_KEY")
            
            if not url or not key:
                raise ValueError(
                    "Missing SUPABASE_URL or SUPABASE_KEY environment variables. "
                    "Please check your .env file."
                )
            
            self._client = create_client(url, key)
    
    @property
    def client(self) -> Client:
        """Get the Supabase client instance."""
        return self._client
    
    # =========================================
    # TARGETS TABLE OPERATIONS
    # =========================================
    
    def get_active_targets(self) -> List[Dict[str, Any]]:
        """Fetch all active monitoring targets."""
        response = self._client.table("targets").select("*").eq("is_active", True).execute()
        return response.data
    
    def add_target(self, target_data: Dict[str, Any]) -> Dict[str, Any]:
        """Add a new monitoring target."""
        response = self._client.table("targets").insert(target_data).execute()
        return response.data[0] if response.data else None
    
    def update_target_last_scraped(self, target_id: str) -> None:
        """Update the last_scraped_at timestamp for a target."""
        self._client.table("targets").update({
            "last_scraped_at": datetime.utcnow().isoformat()
        }).eq("id", target_id).execute()
    
    # =========================================
    # MARKET DATA TABLE OPERATIONS
    # =========================================
    
    def insert_market_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Insert market data (price, news, etc.)."""
        response = self._client.table("market_data").insert(data).execute()
        return response.data[0] if response.data else None
    
    def get_latest_price(self, symbol: str = "XAG") -> Optional[Dict[str, Any]]:
        """Get the latest price for a symbol."""
        response = (
            self._client.table("market_data")
            .select("*")
            .eq("symbol", symbol)
            .eq("data_type", "price")
            .order("collected_at", desc=True)
            .limit(1)
            .execute()
        )
        return response.data[0] if response.data else None
    
    def get_price_history(
        self, 
        symbol: str = "XAG", 
        days: int = 30
    ) -> List[Dict[str, Any]]:
        """Get price history for a symbol."""
        from datetime import timedelta
        start_date = (datetime.utcnow() - timedelta(days=days)).isoformat()
        
        response = (
            self._client.table("market_data")
            .select("*")
            .eq("symbol", symbol)
            .eq("data_type", "price")
            .gte("collected_at", start_date)
            .order("collected_at", desc=False)
            .execute()
        )
        return response.data
    
    def get_recent_news(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get recent news articles."""
        response = (
            self._client.table("market_data")
            .select("*")
            .eq("data_type", "news")
            .order("collected_at", desc=True)
            .limit(limit)
            .execute()
        )
        return response.data
    
    # =========================================
    # AGENT LOGS TABLE OPERATIONS
    # =========================================
    
    def log_agent_action(self, log_data: Dict[str, Any]) -> Dict[str, Any]:
        """Log an agent action or decision."""
        response = self._client.table("agent_logs").insert(log_data).execute()
        return response.data[0] if response.data else None
    
    def get_session_logs(self, session_id: str) -> List[Dict[str, Any]]:
        """Get all logs for a specific session."""
        response = (
            self._client.table("agent_logs")
            .select("*")
            .eq("session_id", session_id)
            .order("created_at", desc=False)
            .execute()
        )
        return response.data
    
    def get_recent_predictions(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent predictions made by the agent."""
        response = (
            self._client.table("agent_logs")
            .select("*")
            .eq("log_type", "prediction")
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        )
        return response.data


# Convenience function for getting the client
def get_db() -> SupabaseClient:
    """Get the Supabase client instance."""
    return SupabaseClient()
