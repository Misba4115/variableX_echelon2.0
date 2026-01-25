# Autonomous Silver Prediction Agent

An AI-powered agent that autonomously collects silver market data, analyzes trends, and generates price predictions.

## 🚀 Quick Start

```bash
# 1. Install dependencies
pip install supabase python-dotenv playwright pandas streamlit
playwright install chromium

# 2. Setup environment
cp .env.example .env
# Edit .env with your Supabase credentials

# 3. Create tables in Supabase SQL Editor
# Paste contents of database/schema.sql
# Then run: ALTER TABLE targets DISABLE ROW LEVEL SECURITY;
#           ALTER TABLE market_data DISABLE ROW LEVEL SECURITY;
#           ALTER TABLE agent_logs DISABLE ROW LEVEL SECURITY;

# 4. Seed initial data
python -m database.seed_data
```

## 🏗️ Project Structure

```
Data-Collection-Agent/
├── main.py              # Entry point
├── config.yaml          # Agent configuration
├── requirements.txt     # Dependencies
├── .env.example         # Environment template
│
├── scraper/             # Data collection
│   ├── web_scraper.py   # Playwright scraper
│   └── metals_api.py    # Price API client
│
├── brain/               # AI & orchestration
│   ├── graph.py         # LangGraph state machine
│   └── prompts.py       # LLM prompts
│
├── database/            # Supabase
│   ├── schema.sql       # Table definitions
│   ├── supabase_client.py # DB client
│   └── seed_data.py     # Initial data
│
└── dashboard/           # Streamlit UI
    └── app.py
```

---

## 📊 Database Tables

### `targets` - What to Monitor
Stores URLs and APIs the agent should scrape/fetch.

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID | Primary key |
| `name` | VARCHAR | Friendly name (e.g., "Kitco Silver News") |
| `source_type` | VARCHAR | `api`, `scrape`, or `rss` |
| `url` | TEXT | Full URL to monitor |
| `category` | VARCHAR | `news`, `price`, or `general` |
| `is_active` | BOOLEAN | Enable/disable monitoring |
| `poll_interval_seconds` | INT | How often to check (default: 300) |
| `last_scraped_at` | TIMESTAMP | Last successful fetch |

**Initial Data:** 4 news sources + 1 price API

---

### `market_data` - Collected Data
Stores all data the agent collects (prices, news, sentiment).

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID | Primary key |
| `target_id` | UUID | FK to targets table |
| `data_type` | VARCHAR | `price`, `news`, `indicator`, `sentiment` |
| `symbol` | VARCHAR | e.g., "XAG" for silver |
| `price` | DECIMAL | Price value (for price data) |
| `title` | TEXT | News headline (for news data) |
| `content` | TEXT | Full article text |
| `sentiment_score` | DECIMAL | -1.0 to 1.0 |
| `collected_at` | TIMESTAMP | When data was fetched |

---

### `agent_logs` - Agent Reasoning
Stores the agent's decisions, predictions, and thought process.

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID | Primary key |
| `session_id` | UUID | Groups logs by run session |
| `log_type` | VARCHAR | `reasoning`, `decision`, `action`, `error`, `prediction` |
| `severity` | VARCHAR | `debug`, `info`, `warning`, `error`, `critical` |
| `reasoning_chain` | TEXT | The agent's thought process |
| `prediction_value` | JSONB | Prediction details |
| `confidence_score` | DECIMAL | 0.0 to 1.0 |
| `was_correct` | BOOLEAN | Validated after prediction window |

---

## 🔑 Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `SUPABASE_URL` | ✅ | Your project URL |
| `SUPABASE_KEY` | ✅ | Anon/public API key |
| `METALS_API_KEY` | Later | For price data |
| `OPENAI_API_KEY` | Later | For LLM reasoning |
