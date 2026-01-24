"""
Web Scraper using Playwright for the Silver Prediction Agent.
Collects news and data from configured web sources.
"""

import asyncio
from datetime import datetime
from typing import Any, Dict, List, Optional
from playwright.async_api import async_playwright, Browser, Page


class WebScraper:
    """
    Playwright-based web scraper for collecting news and data.
    """
    
    def __init__(self, headless: bool = True, timeout_ms: int = 30000):
        """
        Initialize the web scraper.
        
        Args:
            headless: Run browser in headless mode.
            timeout_ms: Default timeout for page operations.
        """
        self.headless = headless
        self.timeout_ms = timeout_ms
        self._browser: Optional[Browser] = None
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.start()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
    
    async def start(self) -> None:
        """Start the browser instance."""
        playwright = await async_playwright().start()
        self._browser = await playwright.chromium.launch(headless=self.headless)
    
    async def close(self) -> None:
        """Close the browser instance."""
        if self._browser:
            await self._browser.close()
            self._browser = None
    
    async def scrape_page(
        self, 
        url: str, 
        selectors: Dict[str, str]
    ) -> Dict[str, Any]:
        """
        Scrape a single page using CSS selectors.
        
        Args:
            url: The URL to scrape.
            selectors: Dict of field names to CSS selectors.
        
        Returns:
            Dict with scraped data.
        """
        if not self._browser:
            raise RuntimeError("Browser not started. Call start() first.")
        
        page = await self._browser.new_page()
        
        try:
            await page.goto(url, timeout=self.timeout_ms)
            await page.wait_for_load_state("networkidle")
            
            result = {
                "url": url,
                "scraped_at": datetime.utcnow().isoformat(),
                "data": {}
            }
            
            for field_name, selector in selectors.items():
                try:
                    elements = await page.query_selector_all(selector)
                    if len(elements) == 1:
                        result["data"][field_name] = await elements[0].inner_text()
                    else:
                        result["data"][field_name] = [
                            await el.inner_text() for el in elements
                        ]
                except Exception as e:
                    result["data"][field_name] = None
                    result.setdefault("errors", {})[field_name] = str(e)
            
            return result
            
        finally:
            await page.close()
    
    async def scrape_news_headlines(
        self, 
        url: str,
        headline_selector: str = "h2 a, h3 a",
        limit: int = 10
    ) -> List[Dict[str, str]]:
        """
        Scrape news headlines from a page.
        
        Args:
            url: News page URL.
            headline_selector: CSS selector for headlines.
            limit: Maximum headlines to collect.
        
        Returns:
            List of headline dicts with title and link.
        """
        if not self._browser:
            raise RuntimeError("Browser not started. Call start() first.")
        
        page = await self._browser.new_page()
        
        try:
            await page.goto(url, timeout=self.timeout_ms)
            await page.wait_for_load_state("networkidle")
            
            headlines = []
            elements = await page.query_selector_all(headline_selector)
            
            for el in elements[:limit]:
                try:
                    title = await el.inner_text()
                    href = await el.get_attribute("href")
                    
                    if title and title.strip():
                        headlines.append({
                            "title": title.strip(),
                            "link": href,
                            "source_url": url,
                            "collected_at": datetime.utcnow().isoformat()
                        })
                except Exception:
                    continue
            
            return headlines
            
        finally:
            await page.close()


# Convenience function for one-off scraping
async def scrape_url(url: str, selectors: Dict[str, str]) -> Dict[str, Any]:
    """
    Scrape a URL with the given selectors.
    
    Args:
        url: URL to scrape.
        selectors: CSS selectors for data extraction.
    
    Returns:
        Scraped data dict.
    """
    async with WebScraper() as scraper:
        return await scraper.scrape_page(url, selectors)
