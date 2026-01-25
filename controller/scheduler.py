"""
Adaptive Scheduler - Orchestrates the collection cycle.
Uses EVENT-DRIVEN TRIGGERS (not fixed schedule!)
"""

from datetime import datetime
from typing import Dict, List, Any
from database import targets
from .budget import BudgetAllocator
from .triggers import EventDrivenTrigger, should_collect_now


class AdaptiveScheduler:
    """
    Event-driven scheduler that decides WHEN to collect.
    
    NOT periodic! Collects based on:
    - Volatility (price moved significantly)
    - Degradation (predictions becoming less accurate)
    - Quality drop (source quality degrading)
    - Importance (critical market hours)
    - Dynamic staleness (high-value sources = shorter threshold)
    """
    
    def __init__(self, total_budget: int = 10):
        """
        Initialize the scheduler.
        
        Args:
            total_budget: Total API calls per cycle
        """
        self.budget_allocator = BudgetAllocator(total_budget)
        self.trigger_system = EventDrivenTrigger()
    
    def should_trigger_collection(self) -> Dict[str, Any]:
        """
        Decide if we should trigger a collection cycle NOW.
        
        Returns:
            Dict with decision and reasons
        """
        should_collect, triggers = self.trigger_system.should_collect()
        
        return {
            "should_collect": should_collect,
            "triggers_fired": len(triggers),
            "reasons": triggers,
            "timestamp": datetime.now().isoformat()
        }
    
    def get_collection_plan(self) -> Dict[str, Any]:
        """
        Generate the collection plan for this cycle.
        Only called when triggers indicate collection is needed.
        
        Returns:
            Plan with sources to collect and their allocated calls
        """
        # Check triggers first
        trigger_result = self.should_trigger_collection()
        
        if not trigger_result["should_collect"]:
            return {
                "should_collect": False,
                "message": "No collection needed - all conditions stable",
                "timestamp": datetime.now().isoformat()
            }
        
        # Get budget allocation
        allocated_sources = self.budget_allocator.allocate()
        
        # Adjust allocation based on trigger type
        for source in allocated_sources:
            source['trigger_reasons'] = trigger_result['reasons']
        
        # Boost allocation for sources if volatility detected
        for trigger in trigger_result['reasons']:
            if trigger.get('urgency') == 'high':
                # Increase budget for high urgency
                for source in allocated_sources[:2]:  # Top 2 sources
                    source['allocated_calls'] = min(
                        source['allocated_calls'] + 2, 
                        10
                    )
        
        return {
            "should_collect": True,
            "timestamp": datetime.now().isoformat(),
            "total_budget": self.budget_allocator.total_budget,
            "triggers": trigger_result['reasons'],
            "sources": allocated_sources
        }


def run_collection_cycle(total_budget: int = 10) -> Dict[str, Any]:
    """
    Run a single collection cycle.
    
    This is the main entry point for the controller.
    Only collects if triggers indicate it's needed!
    
    Args:
        total_budget: Total API calls to allocate
    
    Returns:
        Collection plan with sources and allocations
    """
    scheduler = AdaptiveScheduler(total_budget)
    return scheduler.get_collection_plan()


def check_triggers() -> Dict[str, Any]:
    """
    Just check triggers without generating a full plan.
    Useful for monitoring.
    """
    scheduler = AdaptiveScheduler()
    return scheduler.should_trigger_collection()
