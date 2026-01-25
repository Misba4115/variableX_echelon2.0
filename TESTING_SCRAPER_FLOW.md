# How to Test the Complete Flow

## ✅ New Scraper Execution Routes Added!

The API now has routes that execute **REAL scraping** and complete the full flow.

---

## Main Endpoint: Execute Full Flow

### POST /api/scrape/execute-full-flow

This runs the COMPLETE flow:

```
1. Controller creates collection plan
   ↓
2. StockAgent scrapes price data (Alpha Vantage / Finnhub)
   ↓
3. NewsAgent scrapes news articles (with Mistral AI)
   ↓
4. Data saved to price_data and news_data tables
   ↓
5. Quality metrics updated in targets table
```

### How to Test in Swagger

1. Go to `http://localhost:8000/docs`
2. Find **POST /api/scrape/execute-full-flow** under "Scraper Execution"
3. Click "Try it out"
4. Enter budget (default: 10)
5. Click "Execute"
6. **Wait 30-60 seconds** (real scraping takes time!)
7. Check the response - you'll see:
   - Collection plan
   - Stock scraping results
   - News scraping results  
   - Number of DB entries created

---

## Other Endpoints

### POST /api/scrape/stock-only
- Runs ONLY stock/price scraping (faster)
- Good for testing price collection

### POST /api/scrape/news-only
- Runs ONLY news scraping
- Requires MISTRAL_API_KEY

### GET /api/scrape/scraping-status
- Check which API keys are configured
- Verify scraper is ready

---

## Verify It Worked

After running `/api/scrape/execute-full-flow`:

### Option 1: Check in Swagger
```
GET /api/data/fresh
```
You should see new prices and news!

### Option 2: Check Supabase Dashboard
Go to your Supabase dashboard:
- `price_data` table should have new entries
- `news_data` table should have new entries
- `targets` table should have updated metrics

### Option 3: Check Metrics
```
GET /api/metrics
```
The `avg_utility`, `avg_noise`, `avg_cost` values should change!

---

## Required API Keys

For full scraping to work, you need these in your `.env` file:

```env
# For stock data
ALPHA_VANTAGE_API_KEY=your_key_here
FINNHUB_API_KEY=your_key_here

# For news scraping
MISTRAL_API_KEY=your_key_here
```

Check what's configured:
```
GET /api/scrape/scraping-status
```

---

## Troubleshooting

**"No database entries created"**
- Check API keys are set
- Check Supabase connection in `.env`
- View terminal logs for errors

**Takes too long**
- Normal! Real scraping can take 30-60 seconds
- Use `/api/scrape/stock-only` for faster testing

**Error 500**
- Check terminal for detailed error
- Verify all dependencies installed
- Check API keys are valid

---

## Full Flow Summary

```plaintext
YOU → POST /api/scrape/execute-full-flow
      ↓
Controller → Creates plan with priorities
      ↓
StockAgent → Fetches prices from APIs
      ↓
NewsAgent → Scrapes news websites
      ↓
Database → Saves to price_data & news_data
      ↓
Quality Tracker → Updates avg metrics
      ↓
RESPONSE → Shows what was created
```

**This is the real thing - actual web scraping!**
