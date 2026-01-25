"""
Prioritizer - Calculates priority scores for each source.
Uses the formula: score = (utility / cost) * (1 - (noise * penalty))
"""

from typing import Dict, List, Any
from database import targets


class AdaptiveStrategy:
    """Calculates priority scores for sources based on utility, noise, and cost."""
    
    def __init__(self, noise_penalty_weight: float = 1.5):
        """
        Initialize the strategy.
        
        Args:
            noise_penalty_weight: How harshly to punish noisy sources (default 1.5)
        """
        self.noise_penalty_weight = noise_penalty_weight

    def calculate_priority(self, source_stats: Dict[str, float]) -> float:
        """
        Calculate priority score for a source.
        
        Args:
            source_stats: dict containing:
                - avg_utility: 0 to 1 (Quality of data)
                - avg_noise: 0 to 1 (Junk content ratio)
                - avg_cost: Cost per scrape (time or money)
        
        Returns:
            Priority score (higher = better source)
        """
        utility = source_stats.get('avg_utility', 0.5)
        noise = source_stats.get('avg_noise', 0.1)
        cost = max(source_stats.get('avg_cost', 1.0), 0.001)  # Avoid div by zero

        # The Formula:
        # High Utility + Low Noise + Low Cost = High Priority
        score = (utility / cost) * (1 - (noise * self.noise_penalty_weight))
        
        return max(score, 0)  # Score cannot be negative


def calculate_priority(source: Dict[str, Any], penalty_weight: float = 1.5) -> float:
    """
    Convenience function to calculate priority for a single source.
    
    Args:
        source: Source dict with avg_utility, avg_noise, avg_cost fields
        penalty_weight: Noise penalty multiplier
    
    Returns:
        Priority score
    """
    strategy = AdaptiveStrategy(penalty_weight)
    return strategy.calculate_priority({
        'avg_utility': source.get('avg_utility', 0.5),
        'avg_noise': source.get('avg_noise', 0.1),
        'avg_cost': source.get('avg_cost', 1.0)
    })


def get_all_priorities() -> List[Dict[str, Any]]:
    """
    Get all active sources with their calculated priority scores.
    
    Returns:
        List of sources with 'priority_score' added
    """
    # Fetch all active sources from database
    result = targets().select("*").eq("is_active", True).execute()
    sources = result.data
    
    strategy = AdaptiveStrategy()
    
    # Calculate priority for each source
    for source in sources:
        source['priority_score'] = strategy.calculate_priority({
            'avg_utility': source.get('avg_utility', 0.5),
            'avg_noise': source.get('avg_noise', 0.1),
            'avg_cost': source.get('avg_cost', 1.0)
        })
    
    # Sort by priority (highest first)
    sources.sort(key=lambda x: x['priority_score'], reverse=True)
    
    return sources
