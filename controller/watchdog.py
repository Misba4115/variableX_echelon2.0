"""
WATCHDOG - Simple Event-Driven Trigger

The watchdog ONLY decides WHEN to trigger collection.
WHAT to collect and HOW MUCH is handled by existing logic:
- prioritizer.py → decides which sources
- budget.py → decides how many calls
- scheduler.py → creates collection plan
"""

import asyncio
from datetime import datetime
from typing import Callable, Optional
from dataclasses import dataclass
from enum import Enum


class TriggerType(Enum):
    """Why did we trigger?"""
    PRICE_CHANGE = "price_change"
    PREDICTION_WRONG = "prediction_wrong"
    SOURCE_DOWN = "source_down"
    MANUAL = "manual"


@dataclass
class Trigger:
    """Simple trigger event."""
    trigger_type: TriggerType
    reason: str
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


class Watchdog:
    """
    Simple watchdog that monitors for events and triggers collection.
    
    ONLY responsibility: Detect when to trigger
    Delegates: What to collect, how many calls → existing scheduler/budget logic
    """
    
    def __init__(self, on_trigger: Callable = None):
        """
        Args:
            on_trigger: Function to call when trigger fires.
                       Should call scheduler.run_collection_cycle()
        """
        self.on_trigger = on_trigger
        self.is_running = False
        self.last_price: float = None
        self.price_threshold = 0.02  # 2% change
    
    def _fire_trigger(self, trigger: Trigger):
        """Fire the trigger and call the collection logic."""
        print(f"🔔 TRIGGER: {trigger.trigger_type.value} - {trigger.reason}")
        
        if self.on_trigger:
            # Call the existing collection logic
            self.on_trigger(trigger)
    
    # ============================================================
    # TRIGGER SOURCES
    # ============================================================
    
    def on_price_update(self, new_price: float):
        """
        Called when we receive a price update.
        Checks if price moved enough to trigger collection.
        """
        if self.last_price is not None:
            change = abs(new_price - self.last_price) / self.last_price
            
            if change >= self.price_threshold:
                self._fire_trigger(Trigger(
                    trigger_type=TriggerType.PRICE_CHANGE,
                    reason=f"Price changed {change*100:.1f}% ({self.last_price:.2f} → {new_price:.2f})"
                ))
        
        self.last_price = new_price
    
    def on_prediction_validated(self, was_correct: bool):
        """
        Called when a prediction is validated.
        Triggers if prediction was wrong (need fresh data).
        """
        if not was_correct:
            self._fire_trigger(Trigger(
                trigger_type=TriggerType.PREDICTION_WRONG,
                reason="Recent prediction was incorrect, refreshing data"
            ))
    
    def on_source_error(self, source_name: str, error: str):
        """
        Called when a source fails.
        Triggers collection from alternative sources.
        """
        self._fire_trigger(Trigger(
            trigger_type=TriggerType.SOURCE_DOWN,
            reason=f"{source_name} failed: {error}"
        ))
    
    def trigger_manual(self, reason: str = "Manual trigger"):
        """Manually trigger collection."""
        self._fire_trigger(Trigger(
            trigger_type=TriggerType.MANUAL,
            reason=reason
        ))


# ============================================================
# INTEGRATION: Connect Watchdog to existing collection logic
# ============================================================

def create_watchdog() -> Watchdog:
    """
    Create a watchdog connected to the existing collection logic.
    """
    from .scheduler import run_collection_cycle
    from .brain_trigger import check_brain_ready, trigger_brain_agent_sync
    
    def on_trigger(trigger: Trigger):
        """When watchdog fires, run the collection cycle."""
        print(f"📥 Received trigger: {trigger.reason}")
        print("🚀 Running collection cycle...")
        
        # Use existing logic!
        plan = run_collection_cycle(total_budget=10)
        
        print(f"✅ Collection plan created:")
        if plan.get("should_collect"):
            for source in plan.get("sources", []):
                print(f"   • {source['name']}: {source['allocated_calls']} calls")
        else:
            print(f"   {plan.get('message', 'No collection needed')}")
        
        # After collection, check if brain agent should run
        print("\n🧠 Checking brain agent readiness...")
        is_ready, details = check_brain_ready()
        
        if is_ready and details.get('auto_trigger', True):
            print(f"✅ {details.get('message')}")
            print("🚀 Auto-triggering brain agent...")
            
            try:
                result = trigger_brain_agent_sync()
                if result.get('success'):
                    print(f"✅ Brain agent prediction complete!")
                    prediction = result.get('prediction', {})
                    print(f"   Decision: {prediction.get('decision')}")
                    print(f"   Target: ${prediction.get('target_price')}")
                else:
                    print(f"⚠️  Brain agent did not run: {result.get('reason')}")
            except Exception as e:
                print(f"❌ Brain agent error: {e}")
        else:
            print(f"ℹ️  {details.get('message')}")
    
    return Watchdog(on_trigger=on_trigger)


# ============================================================
# EXAMPLE: How to use with real-time price feed
# ============================================================

async def example_price_stream_monitor():
    """
    Example: Monitor a price stream and trigger on changes.
    
    In production, replace the simulated stream with:
    - WebSocket connection to metals API
    - Supabase Realtime subscription
    - Any real-time data source
    """
    import random
    
    watchdog = create_watchdog()
    watchdog.is_running = True
    
    print("🐕 Watchdog started - monitoring price stream...")
    print("   (Waiting for price to move > 2%)")
    
    base_price = 29.50
    
    while watchdog.is_running:
        # Simulate price update (replace with real data)
        change = random.uniform(-0.03, 0.03)
        new_price = base_price * (1 + change)
        
        print(f"   Price: ${new_price:.2f}")
        
        # This will trigger collection if price moved > 2%
        watchdog.on_price_update(new_price)
        
        base_price = new_price
        await asyncio.sleep(5)


if __name__ == "__main__":
    print("""
    ╔═══════════════════════════════════════════════════╗
    ║           SIMPLE WATCHDOG - Just a Trigger        ║
    ╠═══════════════════════════════════════════════════╣
    ║  Watchdog detects WHEN to collect                 ║
    ║  Existing logic handles WHAT and HOW MUCH         ║
    ╚═══════════════════════════════════════════════════╝
    """)
    
    # Create watchdog
    watchdog = create_watchdog()
    
    # Test manual trigger
    print("Testing manual trigger...")
    watchdog.trigger_manual("Test trigger")
    
    # Test price change trigger
    print("\nSimulating price updates...")
    watchdog.on_price_update(29.50)  # First price
    watchdog.on_price_update(29.60)  # +0.3% (no trigger)
    watchdog.on_price_update(30.20)  # +2% (TRIGGER!)
