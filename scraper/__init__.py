"""
Scraper module for Autonomous Silver Prediction Agent.
Handles web scraping with Playwright and API data collection.
"""

from .web_scraper import WebScraper
from .metals_api import MetalsAPI

__all__ = ["WebScraper", "MetalsAPI"]
