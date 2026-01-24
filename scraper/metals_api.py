"""
Metals API client for fetching silver and precious metals prices.
"""

import os
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
import httpx
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class MetalsAPI:
    """
    Client for fetching precious metals price data.
    """
    
    BASE_URL = "https://metals-api.com/api"
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the Metals API client.
        
        Args:
            api_key: API key for metals-api.com (or use METALS_API_KEY env var)
        """
        self.api_key = api_key or os.getenv("METALS_API_KEY")
        
        if not self.api_key:
            raise ValueError(
                "Missing METALS_API_KEY. Please provide it or set in .env file."
            )
        
        self._client = httpx.Client(timeout=30.0)
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self._client.close()
    
    def _make_request(self, endpoint: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Make an API request."""
        params = params or {}
        params["access_key"] = self.api_key
        
        response = self._client.get(f"{self.BASE_URL}{endpoint}", params=params)
        response.raise_for_status()
        
        data = response.json()
        
        if not data.get("success", True):
            error = data.get("error", {})
            raise Exception(f"API Error: {error.get('info', 'Unknown error')}")
        
        return data
    
    def get_latest_prices(
        self, 
        base: str = "USD",
        symbols: List[str] = None
    ) -> Dict[str, Any]:
        """
        Get latest precious metals prices.
        
        Args:
            base: Base currency (default: USD)
            symbols: List of symbols (default: XAG, XAU for silver and gold)
        
        Returns:
            Dict with price data.
        """
        symbols = symbols or ["XAG", "XAU"]
        
        params = {
            "base": base,
            "symbols": ",".join(symbols)
        }
        
        data = self._make_request("/latest", params)
        
        # Transform to more usable format
        result = {
            "timestamp": data.get("timestamp"),
            "date": data.get("date"),
            "base": base,
            "prices": {}
        }
        
        rates = data.get("rates", {})
        for symbol in symbols:
            if symbol in rates:
                # Metals API returns rates as 1/price, so we invert
                rate = rates[symbol]
                price = 1 / rate if rate != 0 else 0
                result["prices"][symbol] = {
                    "price": round(price, 4),
                    "rate": rate
                }
        
        return result
    
    def get_silver_price(self) -> Dict[str, Any]:
        """
        Get current silver price in USD.
        
        Returns:
            Dict with silver price data.
        """
        data = self.get_latest_prices(symbols=["XAG"])
        
        silver = data["prices"].get("XAG", {})
        
        return {
            "symbol": "XAG",
            "price": silver.get("price"),
            "currency": "USD",
            "timestamp": data["timestamp"],
            "collected_at": datetime.utcnow().isoformat()
        }
    
    def get_historical_prices(
        self,
        start_date: str,
        end_date: str,
        base: str = "USD",
        symbols: List[str] = None
    ) -> Dict[str, Any]:
        """
        Get historical prices for a date range.
        
        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            base: Base currency
            symbols: List of symbols
        
        Returns:
            Dict with historical price data.
        """
        symbols = symbols or ["XAG"]
        
        params = {
            "start_date": start_date,
            "end_date": end_date,
            "base": base,
            "symbols": ",".join(symbols)
        }
        
        return self._make_request("/timeseries", params)
    
    def get_price_change(
        self, 
        symbol: str = "XAG",
        days: int = 1
    ) -> Dict[str, Any]:
        """
        Calculate price change over a period.
        
        Args:
            symbol: Metal symbol
            days: Number of days to compare
        
        Returns:
            Dict with price change data.
        """
        end_date = datetime.utcnow().strftime("%Y-%m-%d")
        start_date = (datetime.utcnow() - timedelta(days=days)).strftime("%Y-%m-%d")
        
        data = self.get_historical_prices(start_date, end_date, symbols=[symbol])
        
        rates = data.get("rates", {})
        dates = sorted(rates.keys())
        
        if len(dates) < 2:
            return {"error": "Insufficient data for comparison"}
        
        first_rate = rates[dates[0]].get(symbol, 0)
        last_rate = rates[dates[-1]].get(symbol, 0)
        
        first_price = 1 / first_rate if first_rate != 0 else 0
        last_price = 1 / last_rate if last_rate != 0 else 0
        
        change = last_price - first_price
        change_percent = (change / first_price * 100) if first_price != 0 else 0
        
        return {
            "symbol": symbol,
            "start_date": dates[0],
            "end_date": dates[-1],
            "start_price": round(first_price, 4),
            "end_price": round(last_price, 4),
            "change": round(change, 4),
            "change_percent": round(change_percent, 2)
        }


# Convenience function
def get_current_silver_price() -> Dict[str, Any]:
    """Get the current silver price."""
    with MetalsAPI() as api:
        return api.get_silver_price()
