"""
Main entry point for the Autonomous Silver Prediction Agent.
"""

import asyncio
from database import SupabaseClient, StateManager

from brain import SilverAgentGraph


async def main():
    """Run the silver prediction agent."""
    print("🥈 Silver Prediction Agent Starting...")
    
    try:
        db = SupabaseClient()
        state_mgr = StateManager(db)
        agent = SilverAgentGraph(db, state_mgr)
        
        result = await agent.run()
        print(f"Agent completed. Session: {result['session_id']}")
        
    except Exception as e:
        print(f"Error: {e}")
        print("Tip: Check your .env file for credentials")


if __name__ == "__main__":
    asyncio.run(main())
