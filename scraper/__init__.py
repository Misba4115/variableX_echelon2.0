# scraper/__init__.py

"""
Scraper package for silver prediction data collection.
Includes stock data fetching and news scraping with adaptive behavior.
Controller-driven architecture with adaptive source prioritization.
"""

from .sources import StockAgent
try:
    from .news_scraper import NewsAgent
    news_agent_available = True
except ImportError:
    NewsAgent = None
    news_agent_available = False
from .db_helper import ScraperDBHelper

__all__ = [
    'StockAgent',
    'NewsAgent',
    'ScraperDBHelper',
    'news_agent_available'
]

__version__ = '1.0.0'