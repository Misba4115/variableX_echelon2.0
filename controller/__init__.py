"""
Controller module for Autonomous Silver Prediction Agent.
Handles adaptive scheduling, source prioritization, and budget allocation.
"""

from .prioritizer import calculate_priority, get_all_priorities
from .budget import allocate_budget, BudgetAllocator
from .scheduler import AdaptiveScheduler, run_collection_cycle, check_triggers
from .quality_tracker import QualityTracker, update_quality_after_scrape
from .triggers import EventDrivenTrigger, should_collect_now, get_collection_reason
from .freshness import FreshnessManager, get_fresh_data, cleanup_old_data, check_freshness
from .watchdog import Watchdog, create_watchdog
from .brain_trigger import (
    check_brain_ready, 
    get_fresh_entry_counts, 
    should_trigger_brain,
    trigger_brain_agent,
    trigger_brain_agent_sync
)


__all__ = [
    # Priority & Budget
    "calculate_priority",
    "get_all_priorities", 
    "allocate_budget",
    "BudgetAllocator",
    
    # Scheduling
    "AdaptiveScheduler",
    "run_collection_cycle",
    "check_triggers",
    
    # Quality Tracking
    "QualityTracker",
    "update_quality_after_scrape",
    
    # Triggers
    "EventDrivenTrigger",
    "should_collect_now",
    "get_collection_reason",
    
    # Freshness
    "FreshnessManager",
    "get_fresh_data",
    "cleanup_old_data",
    "check_freshness",
    
    # Watchdog
    "Watchdog",
    "create_watchdog",
    
    # Brain Trigger
    "check_brain_ready",
    "get_fresh_entry_counts",
    "should_trigger_brain",
    "trigger_brain_agent",
    "trigger_brain_agent_sync"
]




