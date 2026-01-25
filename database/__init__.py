"""
Database module - Simple Supabase client.
"""

from .supabase_client import supabase, get_client, targets, price_data, news_data, agent_logs

__all__ = ["supabase", "get_client", "targets", "price_data", "news_data", "agent_logs"]
