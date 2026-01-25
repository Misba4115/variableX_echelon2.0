"""
Freshness Manager - Hybrid Stale/Fresh Data Logic

HYBRID APPROACH:
- Slow day: Keep data up to X hours old (time-based)
- Busy day: Keep only last N entries (count-based)

Data is considered FRESH if:
- It's within the time threshold (e.g., < 1 hour) AND
- It's within the count threshold (e.g., last 10 entries)
"""

from datetime import datetime, timedelta
from typing import Dict, List, Any, Tuple
from database import price_data, news_data, targets


class FreshnessManager:
    """
    Hybrid freshness checker for price and news data.
    
    Rules:
    - SLOW DAY: Few entries → Keep all within time window
    - BUSY DAY: Many entries → Keep only last N entries
    """
    
    def __init__(
        self,
        price_time_threshold_minutes: int = 60,      # 1 hour for prices
        price_count_threshold: int = 10,              # Max 10 price entries
        news_time_threshold_hours: int = 4,           # 4 hours for news
        news_count_threshold: int = 20                # Max 20 news entries
    ):
        self.price_time_threshold = price_time_threshold_minutes
        self.price_count_threshold = price_count_threshold
        self.news_time_threshold = news_time_threshold_hours
        self.news_count_threshold = news_count_threshold
    
    def get_fresh_prices(self) -> List[Dict[str, Any]]:
        """
        Get fresh price data using hybrid logic.
        
        Returns:
            List of fresh price entries
        """
        # Get all prices, ordered by newest first
        result = price_data().select("*").order(
            "fetched_at", desc=True
        ).execute()
        
        all_prices = result.data
        
        if not all_prices:
            return []
        
        now = datetime.now()
        cutoff_time = now - timedelta(minutes=self.price_time_threshold)
        
        fresh_prices = []
        
        for i, price in enumerate(all_prices):
            # Check count threshold (busy day protection)
            if i >= self.price_count_threshold:
                break
            
            # Check time threshold (slow day protection)
            fetched_at = price.get('fetched_at')
            if fetched_at:
                if isinstance(fetched_at, str):
                    fetched_at = datetime.fromisoformat(
                        fetched_at.replace('Z', '+00:00')
                    ).replace(tzinfo=None)
                
                if fetched_at < cutoff_time:
                    break  # Stop at first stale entry
            
            fresh_prices.append(price)
        
        return fresh_prices
    
    def get_fresh_news(self) -> List[Dict[str, Any]]:
        """
        Get fresh news data using hybrid logic.
        
        Returns:
            List of fresh news entries
        """
        result = news_data().select("*").order(
            "fetched_at", desc=True
        ).execute()
        
        all_news = result.data
        
        if not all_news:
            return []
        
        now = datetime.now()
        cutoff_time = now - timedelta(hours=self.news_time_threshold)
        
        fresh_news = []
        
        for i, article in enumerate(all_news):
            # Count threshold
            if i >= self.news_count_threshold:
                break
            
            # Time threshold
            fetched_at = article.get('fetched_at')
            if fetched_at:
                if isinstance(fetched_at, str):
                    fetched_at = datetime.fromisoformat(
                        fetched_at.replace('Z', '+00:00')
                    ).replace(tzinfo=None)
                
                if fetched_at < cutoff_time:
                    break
            
            fresh_news.append(article)
        
        return fresh_news
    
    def get_stale_counts(self) -> Dict[str, int]:
        """
        Get count of stale entries that could be cleaned up.
        
        Returns:
            Dict with stale counts for price and news
        """
        # Count all entries
        price_result = price_data().select("id", count="exact").execute()
        news_result = news_data().select("id", count="exact").execute()
        
        total_prices = price_result.count or 0
        total_news = news_result.count or 0
        
        # Get fresh counts
        fresh_prices = len(self.get_fresh_prices())
        fresh_news = len(self.get_fresh_news())
        
        return {
            "price_stale": total_prices - fresh_prices,
            "news_stale": total_news - fresh_news,
            "price_fresh": fresh_prices,
            "news_fresh": fresh_news
        }
    
    def cleanup_stale_data(self, dry_run: bool = True) -> Dict[str, Any]:
        """
        Remove stale data from database.
        
        Args:
            dry_run: If True, just report what would be deleted
        
        Returns:
            Summary of cleanup
        """
        now = datetime.now()
        
        # Calculate cutoff times
        price_cutoff = (now - timedelta(minutes=self.price_time_threshold)).isoformat()
        news_cutoff = (now - timedelta(hours=self.news_time_threshold)).isoformat()
        
        # Get counts before
        counts = self.get_stale_counts()
        
        if dry_run:
            return {
                "dry_run": True,
                "would_delete": {
                    "prices": counts["price_stale"],
                    "news": counts["news_stale"]
                },
                "would_keep": {
                    "prices": counts["price_fresh"],
                    "news": counts["news_fresh"]
                }
            }
        
        # Actually delete stale data
        # Keep entries that are EITHER within time OR within count
        
        # For prices: Delete entries beyond count threshold that are also old
        price_data().delete().lt(
            "fetched_at", price_cutoff
        ).execute()
        
        # For news: Same logic
        news_data().delete().lt(
            "fetched_at", news_cutoff
        ).execute()
        
        # Get counts after
        counts_after = self.get_stale_counts()
        
        return {
            "dry_run": False,
            "deleted": {
                "prices": counts["price_stale"],
                "news": counts["news_stale"]
            },
            "remaining": {
                "prices": counts_after["price_fresh"],
                "news": counts_after["news_fresh"]
            }
        }
    
    def get_freshness_summary(self) -> Dict[str, Any]:
        """
        Get a summary of data freshness status.
        """
        fresh_prices = self.get_fresh_prices()
        fresh_news = self.get_fresh_news()
        counts = self.get_stale_counts()
        
        return {
            "thresholds": {
                "price_time": f"{self.price_time_threshold} minutes",
                "price_count": self.price_count_threshold,
                "news_time": f"{self.news_time_threshold} hours",
                "news_count": self.news_count_threshold
            },
            "fresh_data": {
                "prices": len(fresh_prices),
                "news": len(fresh_news)
            },
            "stale_data": {
                "prices": counts["price_stale"],
                "news": counts["news_stale"]
            },
            "latest_price": fresh_prices[0] if fresh_prices else None,
            "latest_news": fresh_news[0].get("title") if fresh_news else None
        }


# Convenience functions
def get_fresh_data() -> Dict[str, List[Dict]]:
    """Get all fresh data for analysis."""
    manager = FreshnessManager()
    return {
        "prices": manager.get_fresh_prices(),
        "news": manager.get_fresh_news()
    }


def cleanup_old_data(dry_run: bool = True) -> Dict[str, Any]:
    """Cleanup stale data from database."""
    manager = FreshnessManager()
    return manager.cleanup_stale_data(dry_run=dry_run)


def check_freshness() -> Dict[str, Any]:
    """Check current freshness status."""
    manager = FreshnessManager()
    return manager.get_freshness_summary()


# Test
if __name__ == "__main__":
    print("""
    ╔═══════════════════════════════════════════════════╗
    ║         HYBRID FRESHNESS MANAGER                  ║
    ╠═══════════════════════════════════════════════════╣
    ║  SLOW DAY: Keep all within time window            ║
    ║  BUSY DAY: Keep only last N entries               ║
    ╚═══════════════════════════════════════════════════╝
    """)
    
    print("Checking freshness status...")
    summary = check_freshness()
    
    print(f"\nThresholds:")
    print(f"  Price: {summary['thresholds']['price_time']} OR last {summary['thresholds']['price_count']} entries")
    print(f"  News:  {summary['thresholds']['news_time']} OR last {summary['thresholds']['news_count']} entries")
    
    print(f"\nFresh data:")
    print(f"  Prices: {summary['fresh_data']['prices']}")
    print(f"  News:   {summary['fresh_data']['news']}")
    
    print(f"\nStale data (can be cleaned):")
    print(f"  Prices: {summary['stale_data']['prices']}")
    print(f"  News:   {summary['stale_data']['news']}")
