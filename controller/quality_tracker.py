"""
Quality Tracker - Automatically updates utility/noise/cost after each scrape.

HOW VALUES ARE CALCULATED:
==========================

UTILITY (0.0 to 1.0):
- Measures: Did the scrape return useful data?
- Calculation: success_rate over last N scrapes
  - Success = got new, non-empty data
  - Failure = error, empty, or duplicate

NOISE (0.0 to 1.0):  
- Measures: How much irrelevant content?
- Calculation: Based on keyword relevance
  - Check if silver-related keywords are present
  - Higher noise = more off-topic content

COST (seconds):
- Measures: How expensive is this source?
- Calculation: Average response time in seconds
  - Fast source = low cost = higher priority
"""

from datetime import datetime
from typing import Dict, Any, Optional
from database import targets


# Keywords that indicate relevant silver content
SILVER_KEYWORDS = [
    'silver', 'xag', 'precious metal', 'bullion', 
    'spot price', 'commodity', 'mining', 'ounce', 'oz'
]


class QualityTracker:
    """
    Tracks and updates source quality metrics after each scrape.
    Uses rolling averages to smooth out fluctuations.
    """
    
    def __init__(self, smoothing_factor: float = 0.2):
        """
        Args:
            smoothing_factor: How much new data affects the average (0.0-1.0)
                             Higher = more responsive to recent data
                             Lower = more stable average
        """
        self.smoothing_factor = smoothing_factor
    
    def calculate_utility(
        self, 
        scrape_result: Dict[str, Any],
        previous_data: Optional[Dict[str, Any]] = None
    ) -> float:
        """
        Calculate utility score from scrape result.
        
        Args:
            scrape_result: The scraped data
            previous_data: Previous scrape from same source (to check duplicates)
        
        Returns:
            Utility score 0.0 to 1.0
        """
        utility = 0.0
        
        # Check 1: Did we get data at all?
        if scrape_result is None:
            return 0.0
        
        # Check 2: Is there content?
        content = scrape_result.get('content') or scrape_result.get('title') or ''
        if content:
            utility += 0.4
        
        # Check 3: Is it new (not duplicate)?
        if previous_data:
            prev_content = previous_data.get('content') or previous_data.get('title') or ''
            if content != prev_content:
                utility += 0.3  # New content = good
        else:
            utility += 0.3  # First scrape = assume good
        
        # Check 4: Is it substantial?
        if len(content) > 100:
            utility += 0.3
        elif len(content) > 50:
            utility += 0.15
        
        return min(utility, 1.0)
    
    def calculate_noise(self, scrape_result: Dict[str, Any]) -> float:
        """
        Calculate noise score from scrape result.
        
        Args:
            scrape_result: The scraped data
        
        Returns:
            Noise score 0.0 to 1.0 (higher = more noise = worse)
        """
        if scrape_result is None:
            return 1.0  # No data = maximum noise
        
        content = scrape_result.get('content') or scrape_result.get('title') or ''
        content_lower = content.lower()
        
        if not content:
            return 1.0
        
        # Count how many silver keywords are present
        keyword_count = sum(1 for kw in SILVER_KEYWORDS if kw in content_lower)
        
        # More keywords = lower noise
        if keyword_count >= 3:
            return 0.1  # Very relevant
        elif keyword_count >= 1:
            return 0.3  # Somewhat relevant
        else:
            return 0.7  # Not very relevant (high noise)
    
    def calculate_cost(self, response_time_seconds: float) -> float:
        """
        Calculate cost from response time.
        
        Args:
            response_time_seconds: How long the scrape took
        
        Returns:
            Cost value (in seconds, normalized)
        """
        # Normalize to a 0-1 scale based on typical response times
        # < 1 second = very fast = low cost
        # > 10 seconds = very slow = high cost
        return min(response_time_seconds / 10.0, 1.0) + 0.1  # minimum 0.1
    
    def update_source_metrics(
        self,
        source_id: str,
        scrape_result: Dict[str, Any],
        response_time: float,
        previous_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, float]:
        """
        Update a source's quality metrics after a scrape.
        Uses exponential moving average for smooth updates.
        
        Args:
            source_id: UUID of the source
            scrape_result: The data that was scraped
            response_time: How long it took in seconds
            previous_data: Previous scrape data (for duplicate detection)
        
        Returns:
            Updated metrics dict
        """
        # Calculate new values
        new_utility = self.calculate_utility(scrape_result, previous_data)
        new_noise = self.calculate_noise(scrape_result)
        new_cost = self.calculate_cost(response_time)
        
        # Get current values from database
        result = targets().select("avg_utility, avg_noise, avg_cost").eq("id", source_id).execute()
        
        if not result.data:
            return {"error": "Source not found"}
        
        current = result.data[0]
        old_utility = current.get('avg_utility') or 0.5
        old_noise = current.get('avg_noise') or 0.1
        old_cost = current.get('avg_cost') or 1.0
        
        # Apply exponential moving average
        # new_avg = old_avg * (1 - factor) + new_value * factor
        factor = self.smoothing_factor
        
        updated_utility = old_utility * (1 - factor) + new_utility * factor
        updated_noise = old_noise * (1 - factor) + new_noise * factor
        updated_cost = old_cost * (1 - factor) + new_cost * factor
        
        # Update database
        targets().update({
            "avg_utility": round(updated_utility, 4),
            "avg_noise": round(updated_noise, 4),
            "avg_cost": round(updated_cost, 4),
            "last_scraped_at": datetime.utcnow().isoformat()
        }).eq("id", source_id).execute()
        
        return {
            "source_id": source_id,
            "utility": round(updated_utility, 4),
            "noise": round(updated_noise, 4),
            "cost": round(updated_cost, 4),
            "this_scrape": {
                "utility": new_utility,
                "noise": new_noise,
                "cost": new_cost
            }
        }


# Convenience function
def update_quality_after_scrape(
    source_id: str,
    scrape_result: Dict[str, Any],
    response_time: float,
    previous_data: Optional[Dict[str, Any]] = None
) -> Dict[str, float]:
    """
    Update source quality metrics after a scrape.
    
    Call this after every successful scrape!
    
    Args:
        source_id: The source's UUID
        scrape_result: The scraped data (dict with 'title', 'content', etc.)
        response_time: How long the scrape took (seconds)
        previous_data: Previous scrape to check for duplicates
    
    Returns:
        Updated metrics
    """
    tracker = QualityTracker()
    return tracker.update_source_metrics(source_id, scrape_result, response_time, previous_data)
