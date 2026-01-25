"""
Budget Allocator - Distributes API calls across sources based on priority scores.
"""

from typing import Dict, List, Any
from .prioritizer import get_all_priorities


class BudgetAllocator:
    """Allocates API call budget across sources based on their priority scores."""
    
    def __init__(self, total_budget: int = 10):
        """
        Initialize the allocator.
        
        Args:
            total_budget: Total number of API calls to distribute per cycle
        """
        self.total_budget = total_budget
    
    def allocate(self) -> List[Dict[str, Any]]:
        """
        Allocate API calls to each source based on priority scores.
        
        Returns:
            List of sources with 'allocated_calls' field added
        """
        sources = get_all_priorities()
        
        if not sources:
            return []
        
        # Calculate total priority score
        total_score = sum(s['priority_score'] for s in sources)
        
        if total_score == 0:
            # If all scores are 0, distribute evenly
            calls_each = self.total_budget // len(sources)
            for source in sources:
                source['allocated_calls'] = calls_each
            return sources
        
        # Distribute budget proportionally to priority
        allocated = 0
        for source in sources:
            # Calculate percentage of total score
            percentage = source['priority_score'] / total_score
            
            # Allocate calls (at least 1 for active sources)
            calls = max(1, int(self.total_budget * percentage))
            source['allocated_calls'] = calls
            allocated += calls
        
        # Handle rounding (give extras to highest priority)
        remaining = self.total_budget - allocated
        if remaining > 0 and sources:
            sources[0]['allocated_calls'] += remaining
        
        return sources
    
    def get_allocation_summary(self) -> Dict[str, Any]:
        """
        Get a summary of the current budget allocation.
        
        Returns:
            Summary dict with allocation details
        """
        sources = self.allocate()
        
        return {
            'total_budget': self.total_budget,
            'sources': [
                {
                    'name': s['name'],
                    'priority_score': round(s['priority_score'], 3),
                    'allocated_calls': s['allocated_calls'],
                    'percentage': round(s['allocated_calls'] / self.total_budget * 100, 1)
                }
                for s in sources
            ]
        }


def allocate_budget(total_calls: int = 10) -> List[Dict[str, Any]]:
    """
    Convenience function to allocate budget.
    
    Args:
        total_calls: Total API calls to distribute
    
    Returns:
        List of sources with allocated_calls
    """
    allocator = BudgetAllocator(total_calls)
    return allocator.allocate()
