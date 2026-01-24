"""
Simple Supabase client for the Silver Prediction Agent.
"""

import os
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

# Initialize Supabase client
_url = os.getenv("SUPABASE_URL")
_key = os.getenv("SUPABASE_KEY")

if not _url or not _key:
    print("⚠️  Warning: SUPABASE_URL or SUPABASE_KEY not set in .env")
    supabase: Client = None
else:
    supabase: Client = create_client(_url, _key)


def get_client() -> Client:
    """Get the Supabase client instance."""
    if supabase is None:
        raise ValueError("Supabase not configured. Check your .env file.")
    return supabase


# Quick access to tables
def targets():
    """Access the targets table."""
    return get_client().table("targets")


def price_data():
    """Access the price_data table."""
    return get_client().table("price_data")


def news_data():
    """Access the news_data table."""
    return get_client().table("news_data")


def agent_logs():
    """Access the agent_logs table."""
    return get_client().table("agent_logs")
