# scraper/__init__.py

"""
Scraper package for silver prediction data collection.
Includes stock data fetching and news scraping with adaptive behavior.
Controller-driven architecture with adaptive source prioritization.
"""

from .sources import StockAgent
from .news_scraper import NewsAgent
from .db_helper import ScraperDBHelper

__all__ = [
    'StockAgent',
    'NewsAgent',
    'ScraperDBHelper'
]

__version__ = '1.0.0'