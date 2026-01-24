"""
Database module - Simple Supabase client.
"""

from .supabase_client import supabase, get_client, targets, market_data, agent_logs

__all__ = ["supabase", "get_client", "targets", "market_data", "agent_logs"]
