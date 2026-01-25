"""
Event-Driven Trigger System - Decides WHEN to collect (NOT periodic!)

TRIGGERS (collect data when ANY of these fire):
1. DEGRADATION - Prediction accuracy dropping
2. VOLATILITY  - Price moving significantly  
3. STALENESS   - Data too old (but with dynamic threshold)
4. IMPORTANCE  - Critical time window (market open, news event)
5. QUALITY_DROP - Source quality degrading

This replaces simple time-based checks with intelligent triggers.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Any, Tuple
from database import targets, price_data, agent_logs


class TriggerReason:
    """Enum-like class for trigger reasons."""
    DEGRADATION = "degradation"      # Predictions becoming less accurate
    VOLATILITY = "volatility"         # Significant price movement
    STALENESS = "staleness"           # Data is stale (dynamic threshold)
    IMPORTANCE = "importance"         # Critical time period
    QUALITY_DROP = "quality_drop"     # Source quality degrading
    MANUAL = "manual"                 # Manual trigger


class EventDrivenTrigger:
    """
    Intelligent trigger system that decides WHEN to collect data.
    NOT based on fixed schedule - based on CONDITIONS.
    """
    
    def __init__(self):
        # Thresholds (can be tuned)
        self.volatility_threshold = 0.02      # 2% price change triggers collection
        self.accuracy_drop_threshold = 0.1    # 10% accuracy drop triggers refresh
        self.quality_drop_threshold = 0.15    # 15% quality drop triggers refresh
        self.base_stale_minutes = 30          # Base staleness (adjusted dynamically)
        
        # Important time windows (market events)
        self.important_hours = [9, 10, 14, 15]  # Market open/close hours (ET)
    
    def check_volatility_trigger(self) -> Tuple[bool, Dict]:
        """
        TRIGGER 1: Price volatility detection.
        Collects data if price moved significantly since last check.
        """
        try:
            # Get last 2 price points
            result = price_data().select("price, fetched_at").order(
                "fetched_at", desc=True
            ).limit(2).execute()
            
            if len(result.data) < 2:
                return False, {}
            
            latest = float(result.data[0]['price'])
            previous = float(result.data[1]['price'])
            
            change = abs(latest - previous) / previous
            
            if change >= self.volatility_threshold:
                return True, {
                    "reason": TriggerReason.VOLATILITY,
                    "details": f"Price moved {change*100:.2f}% ({previous} → {latest})",
                    "urgency": "high" if change > 0.05 else "medium"
                }
            
            return False, {}
        except Exception as e:
            return False, {"error": str(e)}
    
    def check_degradation_trigger(self) -> Tuple[bool, Dict]:
        """
        TRIGGER 2: Prediction accuracy degradation.
        Collects data if recent predictions are becoming less accurate.
        """
        try:
            # Get last 10 predictions with validation
            result = agent_logs().select(
                "was_correct, confidence_score, created_at"
            ).not_.is_("was_correct", "null").order(
                "created_at", desc=True
            ).limit(10).execute()
            
            if len(result.data) < 5:
                return False, {}  # Not enough data
            
            # Calculate recent accuracy (last 5) vs older (5 before that)
            recent = result.data[:5]
            older = result.data[5:10] if len(result.data) >= 10 else []
            
            if not older:
                return False, {}
            
            recent_accuracy = sum(1 for r in recent if r['was_correct']) / len(recent)
            older_accuracy = sum(1 for r in older if r['was_correct']) / len(older)
            
            accuracy_drop = older_accuracy - recent_accuracy
            
            if accuracy_drop >= self.accuracy_drop_threshold:
                return True, {
                    "reason": TriggerReason.DEGRADATION,
                    "details": f"Accuracy dropped from {older_accuracy*100:.0f}% to {recent_accuracy*100:.0f}%",
                    "urgency": "high"
                }
            
            return False, {}
        except Exception as e:
            return False, {"error": str(e)}
    
    def check_quality_drop_trigger(self) -> Tuple[bool, Dict]:
        """
        TRIGGER 3: Source quality degradation.
        Collects from alternate sources if current source quality drops.
        """
        try:
            # Get sources with significant utility drop
            result = targets().select("id, name, avg_utility, avg_noise").eq(
                "is_active", True
            ).execute()
            
            degraded_sources = []
            for source in result.data:
                utility = source.get('avg_utility', 0.5)
                noise = source.get('avg_noise', 0.1)
                
                # Quality is degraded if utility is low OR noise is high
                if utility < 0.3 or noise > 0.5:
                    degraded_sources.append(source['name'])
            
            if degraded_sources:
                return True, {
                    "reason": TriggerReason.QUALITY_DROP,
                    "details": f"Low quality sources: {', '.join(degraded_sources)}",
                    "urgency": "medium",
                    "action": "prioritize_alternate_sources"
                }
            
            return False, {}
        except Exception as e:
            return False, {"error": str(e)}
    
    def check_importance_trigger(self) -> Tuple[bool, Dict]:
        """
        TRIGGER 4: Important time windows.
        Collects data during critical market hours.
        """
        current_hour = datetime.now().hour
        
        if current_hour in self.important_hours:
            return True, {
                "reason": TriggerReason.IMPORTANCE,
                "details": f"Important market hour: {current_hour}:00",
                "urgency": "medium"
            }
        
        return False, {}
    
    def check_dynamic_staleness(self) -> Tuple[bool, Dict]:
        """
        TRIGGER 5: Dynamic staleness (NOT fixed time!).
        Threshold adjusts based on market conditions.
        """
        try:
            # Get sources
            result = targets().select(
                "id, name, last_scraped_at, avg_utility"
            ).eq("is_active", True).execute()
            
            stale_sources = []
            now = datetime.now()
            
            for source in result.data:
                last_scraped = source.get('last_scraped_at')
                utility = source.get('avg_utility', 0.5)
                
                if not last_scraped:
                    stale_sources.append(source['name'])
                    continue
                
                # Parse timestamp
                if isinstance(last_scraped, str):
                    last_scraped = datetime.fromisoformat(
                        last_scraped.replace('Z', '+00:00')
                    ).replace(tzinfo=None)
                
                # DYNAMIC THRESHOLD:
                # High utility sources = shorter threshold (check more often)
                # Low utility sources = longer threshold (check less often)
                dynamic_threshold = self.base_stale_minutes * (1.5 - utility)
                # utility=0.9 → threshold=18min (check often)
                # utility=0.3 → threshold=36min (check less)
                
                age_minutes = (now - last_scraped).total_seconds() / 60
                
                if age_minutes > dynamic_threshold:
                    stale_sources.append(source['name'])
            
            if stale_sources:
                return True, {
                    "reason": TriggerReason.STALENESS,
                    "details": f"Stale sources: {', '.join(stale_sources)}",
                    "urgency": "low",
                    "stale_count": len(stale_sources)
                }
            
            return False, {}
        except Exception as e:
            return False, {"error": str(e)}
    
    def should_collect(self) -> Tuple[bool, List[Dict]]:
        """
        Main method: Check ALL triggers and decide if we should collect.
        
        Returns:
            (should_collect: bool, list of triggered reasons)
        """
        triggers_fired = []
        
        # Check each trigger
        checks = [
            ("volatility", self.check_volatility_trigger),
            ("degradation", self.check_degradation_trigger),
            ("quality_drop", self.check_quality_drop_trigger),
            ("importance", self.check_importance_trigger),
            ("staleness", self.check_dynamic_staleness),
        ]
        
        for name, check_fn in checks:
            fired, details = check_fn()
            if fired:
                triggers_fired.append({
                    "trigger": name,
                    **details
                })
        
        # Sort by urgency
        urgency_order = {"high": 0, "medium": 1, "low": 2}
        triggers_fired.sort(key=lambda x: urgency_order.get(x.get("urgency", "low"), 3))
        
        should_collect = len(triggers_fired) > 0
        
        return should_collect, triggers_fired
    
    def get_trigger_summary(self) -> Dict:
        """Get a summary of current trigger states."""
        should_collect, triggers = self.should_collect()
        
        return {
            "should_collect": should_collect,
            "triggers_fired": len(triggers),
            "triggers": triggers,
            "timestamp": datetime.now().isoformat()
        }


# Convenience functions
def should_collect_now() -> Tuple[bool, List[Dict]]:
    """Check if we should collect data right now."""
    trigger = EventDrivenTrigger()
    return trigger.should_collect()


def get_collection_reason() -> str:
    """Get human-readable reason for collection."""
    should_collect, triggers = should_collect_now()
    
    if not should_collect:
        return "No collection needed - all conditions stable"
    
    reasons = [t.get('details', t.get('reason', 'unknown')) for t in triggers]
    return f"Collection triggered: {'; '.join(reasons)}"
