"""
Brain Agent Trigger Module - Entry-Count Based Triggering

This module checks if enough fresh data entries exist in the database
before triggering the brain agent for predictions.
"""

from datetime import datetime, timedelta
from typing import Dict, Tuple
import yaml
import os

from database.supabase_client import price_data, news_data, get_client


def load_config() -> Dict:
    """Load configuration from config.yaml."""
    config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config.yaml')
    
    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
            return config.get('brain_trigger', {
                'enabled': True,
                'auto_trigger': True,
                'min_total_fresh_entries': 15,
                'check_interval_minutes': 10
            })
    except Exception as e:
        print(f"[BrainTrigger] Warning: Could not load config ({e}), using defaults")
        return {
            'enabled': True,
            'auto_trigger': True,
            'min_total_fresh_entries': 15,
            'check_interval_minutes': 10
        }


def get_fresh_entry_counts(hours: int = 24) -> Dict[str, int]:
    """
    Get count of fresh entries (within specified hours).
    
    Args:
        hours: How many hours back to consider as "fresh" (default: 24)
    
    Returns:
        Dict with price_count, news_count, and total_count
    """
    try:
        # Calculate cutoff time
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        cutoff_iso = cutoff_time.isoformat()
        
        # Count fresh price entries
        price_response = price_data().select("id", count="exact").gte(
            "fetched_at", cutoff_iso
        ).execute()
        price_count = price_response.count if price_response.count is not None else len(price_response.data or [])
        
        # Count fresh news entries
        news_response = news_data().select("id", count="exact").gte(
            "fetched_at", cutoff_iso
        ).execute()
        news_count = news_response.count if news_response.count is not None else len(news_response.data or [])
        
        return {
            'price_count': price_count,
            'news_count': news_count,
            'total_count': price_count + news_count,
            'cutoff_hours': hours,
            'timestamp': datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        print(f"[BrainTrigger] Error getting entry counts: {e}")
        return {
            'price_count': 0,
            'news_count': 0,
            'total_count': 0,
            'cutoff_hours': hours,
            'error': str(e)
        }


def check_brain_ready() -> Tuple[bool, Dict]:
    """
    Check if the brain agent should be triggered based on entry count.
    
    Returns:
        Tuple of (is_ready: bool, details: dict)
    """
    config = load_config()
    
    # Check if feature is enabled
    if not config.get('enabled', True):
        return False, {
            'status': 'disabled',
            'message': 'Brain trigger is disabled in config'
        }
    
    # Get fresh entry counts
    counts = get_fresh_entry_counts()
    threshold = config.get('min_total_fresh_entries', 15)
    total = counts['total_count']
    
    is_ready = total >= threshold
    
    details = {
        'ready': is_ready,
        'total_fresh_entries': total,
        'price_entries': counts['price_count'],
        'news_entries': counts['news_count'],
        'threshold': threshold,
        'remaining': max(0, threshold - total),
        'cutoff_hours': counts.get('cutoff_hours', 24),
        'auto_trigger': config.get('auto_trigger', True),
        'timestamp': counts['timestamp']
    }
    
    if is_ready:
        details['message'] = f"Ready: {total} entries >= {threshold} threshold"
    else:
        details['message'] = f"Not ready: {total} entries < {threshold} threshold (need {threshold - total} more)"
    
    return is_ready, details


def should_trigger_brain() -> Tuple[bool, str]:
    """
    Check if brain agent should be triggered now.
    
    Returns:
        Tuple of (should_trigger: bool, reason: str)
    """
    config = load_config()
    
    if not config.get('enabled', True):
        return False, "Brain trigger disabled in config"
    
    if not config.get('auto_trigger', True):
        return False, "Auto-trigger disabled (manual trigger only)"
    
    is_ready, details = check_brain_ready()
    
    if is_ready:
        return True, details.get('message', 'Sufficient data available')
    else:
        return False, details.get('message', 'Insufficient data')


async def trigger_brain_agent() -> Dict:
    """
    Execute the brain agent if conditions are met.
    
    Returns:
        Dict with execution results
    """
    from brain.agent import run_prediction_agent
    from database.supabase_client import get_client
    
    print("[BrainTrigger] Checking if brain agent should run...")
    
    # Check if ready
    is_ready, details = check_brain_ready()
    
    if not is_ready:
        print(f"[BrainTrigger] ❌ {details.get('message')}")
        return {
            'success': False,
            'triggered': False,
            'reason': details.get('message'),
            'details': details
        }
    
    print(f"[BrainTrigger] ✅ {details.get('message')}")
    print(f"[BrainTrigger] Triggering brain agent...")
    
    try:
        # Run the brain agent
        db_client = get_client()
        result = await run_prediction_agent(db_client)
        
        print(f"[BrainTrigger] Brain agent completed: {result.get('success', False)}")
        
        return {
            'success': result.get('success', False),
            'triggered': True,
            'reason': details.get('message'),
            'prediction': result.get('prediction'),
            'data_used': result.get('data_used'),
            'entry_details': details
        }
    
    except Exception as e:
        print(f"[BrainTrigger] ❌ Error executing brain agent: {e}")
        import traceback
        traceback.print_exc()
        
        return {
            'success': False,
            'triggered': True,
            'reason': f"Error: {str(e)}",
            'error': str(e)
        }


# Synchronous wrapper
def trigger_brain_agent_sync() -> Dict:
    """Synchronous wrapper for trigger_brain_agent."""
    import asyncio
    return asyncio.run(trigger_brain_agent())
