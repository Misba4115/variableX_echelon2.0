# scraper/sources.py

"""
sources.py: StockAgent.
Executes stock data fetching based on controller's adaptive decisions.
"""
import os
import requests
import datetime
from typing import Dict, Any
from .db_helper import ScraperDBHelper

class StockAgent:
    def __init__(self, db_helper: ScraperDBHelper):
        self.av_key = os.getenv("ALPHA_VANTAGE_API_KEY")
        self.fh_key = os.getenv("FINNHUB_API_KEY")
        self.db_helper = db_helper
        
        if self.av_key: 
            print(f"[StockAgent] AV Key Loaded: {self.av_key[:4]}***")
        else: 
            print("[StockAgent] WARNING: ALPHA_VANTAGE_API_KEY not found")
        
        if self.fh_key: 
            print(f"[StockAgent] FH Key Loaded: {self.fh_key[:4]}***")
        else: 
            print("[StockAgent] WARNING: FINNHUB_API_KEY not found")

    def execute_from_controller(self) -> Dict[str, Any]:
        """
        Main entry point: Fetch next target from controller via DB,
        execute the scraping, store data and noise metrics.
        
        Returns: {
            "success": bool,
            "source_name": str,
            "data_stored": bool,
            "noise_score": float
        }
        """
        # 1. Get next target from controller (via TARGETS table in DB)
        target = self.db_helper.get_next_stock_target()
        
        if not target:
            print("[StockAgent] No target available from controller")
            return {
                "success": False,
                "source_name": None,
                "data_stored": False,
                "noise_score": 1.0
            }
        
        source_name = target['name']
        print(f"[StockAgent] Controller assigned target: {source_name}")
        
        # 2. Execute the scraping
        result = self.execute(source_name)
        
        # 3. Store data if valid
        data_stored = False
        if result["data"]:
            data_stored = self.db_helper.insert_stock_data([result["data"]], target_id=target['id'])
            print(f"[StockAgent] Data stored: {data_stored}")
        
        # 4. Report noise metrics back to DB (for controller's next decision)
        noise_metrics = {
            "total_items": 1,
            "valid_items": 1 if result["data"] else 0,
            "noise_items": 0 if result["data"] else 1,
            "noise_ratio": result["noise_score"]
        }
        self.db_helper.insert_noise_metrics('stock', source_name, noise_metrics)
        
        # 5. Mark target as completed
        self.db_helper.mark_target_completed(target['id'])
        
        return {
            "success": result["data"] is not None,
            "source_name": source_name,
            "data_stored": data_stored,
            "noise_score": result["noise_score"]
        }

    def execute(self, instruction: str) -> Dict[str, Any]:
        """
        Execute stock data fetching for a specific source.
        
        Args:
            instruction: Source to fetch from ("alpha_vantage" or "finnhub", or full target name)
        
        Returns: {
            "data": Dict (formatted for DB) | None,
            "noise_score": float (0.0=Clean, 1.0=Noisy/Empty)
        }
        """
        instr_lower = instruction.lower()
        if "alpha" in instr_lower or "vantage" in instr_lower:
            return self._fetch_alpha_vantage()
        elif "finnhub" in instr_lower:
            return self._fetch_finnhub()
        else:
            print(f"[StockAgent] WARNING: Unknown instruction '{instruction}'")
            return {"data": None, "noise_score": 1.0}

    def _fetch_alpha_vantage(self) -> Dict[str, Any]:
        """Fetch silver (SLV ETF) data from Alpha Vantage"""
        try:
            if not self.av_key:
                print("[StockAgent] ERROR: Alpha Vantage API key missing")
                return {"data": None, "noise_score": 1.0}
            
            url = "https://www.alphavantage.co/query"
            params = {
                "function": "GLOBAL_QUOTE",
                "symbol": "SLV",
                "apikey": self.av_key
            }
            
            r = requests.get(url, params=params, timeout=10)
            
            if r.status_code != 200:
                print(f"[StockAgent] ERROR: AV API returned status {r.status_code}")
                return {"data": None, "noise_score": 1.0}
            
            full_res = r.json()
            raw = full_res.get("Global Quote", {})
            
            if "Note" in full_res:
                print(f"[StockAgent] WARNING: AV API Limit: {full_res['Note']}")
                return {"data": None, "noise_score": 1.0}
            
            if "Error Message" in full_res:
                print(f"[StockAgent] ERROR: AV API Error: {full_res['Error Message']}")
                return {"data": None, "noise_score": 1.0}
            
            if not raw or "05. price" not in raw:
                print(f"[StockAgent] WARNING: AV invalid response")
                return {"data": None, "noise_score": 1.0}

            price = float(raw.get("05. price", 0))
            change = float(raw.get("09. change", 0))
            change_percent_str = raw.get("10. change percent", "0%").strip().rstrip('%')
            change_p = float(change_percent_str)
            high = float(raw.get("03. high", 0))
            low = float(raw.get("04. low", 0))
            vol = int(float(raw.get("06. volume", 0)))
            ts = raw.get("07. latest trading day", "")

            if price == 0:
                print("[StockAgent] WARNING: AV returned price = 0")
                return {"data": None, "noise_score": 0.9}

            data = ScraperDBHelper.format_stock_data(
                price, "USD", change, change_p, high, low, vol, ts
            )

            noise = 0.0 if vol > 1000000 else 0.2 if vol > 0 else 0.8
            
            print(f"[StockAgent] AV SUCCESS: ${price}, Vol: {vol:,}, Noise: {noise}")
            return {"data": data, "noise_score": noise}

        except Exception as e:
            print(f"[StockAgent] ERROR (AV): {e}")
            return {"data": None, "noise_score": 1.0}

    def _fetch_finnhub(self) -> Dict[str, Any]:
        """Fetch silver (SLV ETF) data from Finnhub"""
        try:
            if not self.fh_key:
                print("[StockAgent] ERROR: Finnhub API key missing")
                return {"data": None, "noise_score": 1.0}
            
            url = "https://finnhub.io/api/v1/quote"
            params = {"symbol": "SLV", "token": self.fh_key}
            
            r = requests.get(url, params=params, timeout=10)
            
            if r.status_code != 200:
                print(f"[StockAgent] ERROR: Finnhub returned status {r.status_code}")
                return {"data": None, "noise_score": 1.0}
            
            raw = r.json()
            print(f"[StockAgent] Finnhub raw response: {raw}")
            
            if "error" in raw:
                print(f"[StockAgent] ERROR: Finnhub API: {raw['error']}")
                return {"data": None, "noise_score": 1.0}
            
            if not raw or "c" not in raw:
                print(f"[StockAgent] WARNING: FH missing 'c' field")
                return {"data": None, "noise_score": 1.0}

            price = float(raw.get("c", 0))
            change = float(raw.get("d", 0))
            change_p = float(raw.get("dp", 0))
            high = float(raw.get("h", 0))
            low = float(raw.get("l", 0))
            
            if price == 0:
                print("[StockAgent] WARNING: Finnhub returned price = 0")
                return {"data": None, "noise_score": 0.9}
            
            ts_raw = raw.get("t", 0)
            if ts_raw:
                ts = datetime.datetime.fromtimestamp(ts_raw).isoformat()
            else:
                ts = datetime.datetime.utcnow().isoformat()

            vol = 0  # Finnhub quote doesn't provide volume
            
            data = ScraperDBHelper.format_stock_data(
                price, "USD", change, change_p, high, low, vol, ts
            )
            
            print(f"[StockAgent] FH SUCCESS: ${price}, Noise: 0.3 (no volume)")
            return {"data": data, "noise_score": 0.3}

        except Exception as e:
            print(f"[StockAgent] ERROR (FH): {e}")
            return {"data": None, "noise_score": 1.0}