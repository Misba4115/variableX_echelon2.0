# 🥈 Autonomous Silver Prediction Agent

An intelligent, event-driven AI agent that autonomously collects silver market data, analyzes trends using LLMs, and generates price predictions. Features include adaptive scheduling, quality-based prioritization, and entry-count based brain triggering.

## ✨ Key Features

### 🤖 Intelligent Data Collection
- **Event-Driven Watchdog**: Triggers collection based on market conditions, not fixed schedules
- **Adaptive Scheduling**: Prioritizes high-quality sources dynamically
- **Multi-Source Scraping**: Collects data from news sites and price APIs
- **Quality Tracking**: Monitors source reliability and adjusts collection accordingly

### 🧠 AI-Powered Predictions
- **Entry-Based Triggering**: Brain agent only runs when sufficient data exists (configurable threshold)
- **LLM Analysis**: Uses Google Gemini for market analysis and predictions
- **Sentiment Analysis**: Analyzes news with Mistral AI for sentiment scoring
- **Confidence Scoring**: Provides prediction confidence levels (0-1 scale)

### 🎯 Smart Trigger System
- **Volatility Detection**: Triggers on 2%+ price changes
- **Quality Monitoring**: Detects when source quality degrades
- **Dynamic Staleness**: Adjusts data freshness thresholds based on source quality
- **Auto-Brain Trigger**: Automatically runs predictions when entry threshold is met

### 📊 Full-Stack Dashboard
- **FastAPI Backend**: RESTful API with Swagger documentation
- **Next.js Frontend**: Modern, responsive UI with real-time updates
- **Supabase Database**: Scalable PostgreSQL storage
- **Interactive Charts**: Price performance and prediction visualization

---

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- Node.js 18+ (for frontend)
- Supabase account (free tier works)
- Gemini API key (free tier available)
- Mistral API key (optional, for news sentiment)

### 1. Environment Setup

```bash
# Clone repository
git clone https://github.com/Misba4115/Data-Collection-Agent.git
cd Data-Collection-Agent

# Install Python dependencies
pip install -r requirements.txt

# Install Playwright browsers
playwright install chromium

# Setup environment variables
cp .env.example .env
# Edit .env with your credentials (see below)
```

### 2. Configure Environment Variables

Edit `.env` file:

```env
# Supabase Database
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key

# AI APIs
GEMINI_API_KEY=your-gemini-api-key
MISTRAL_API_KEY=your-mistral-api-key  # Optional

# Optional APIs
ALPHA_VANTAGE_API_KEY=your-av-key     # For price data
FINNHUB_API_KEY=your-finnhub-key      # Alternative price source
```

### 3. Database Setup

```bash
# In Supabase SQL Editor, paste the contents of:
database/schema.sql

# Disable Row Level Security for all tables:
ALTER TABLE targets DISABLE ROW LEVEL SECURITY;
ALTER TABLE price_data DISABLE ROW LEVEL SECURITY;
ALTER TABLE news_data DISABLE ROW LEVEL SECURITY;
ALTER TABLE agent_logs DISABLE ROW LEVEL SECURITY;

# Seed initial data
python -m database.seed_data
```

### 4. Run the Application

#### Option A: Backend API + Frontend

```bash
# Terminal 1: Start FastAPI backend
python -m uvicorn api.main:app --reload
# API will be available at http://localhost:8000
# Swagger docs at http://localhost:8000/docs

# Terminal 2: Start Next.js frontend
cd frontend
npm install
npm run dev
# Frontend at http://localhost:3000
```

#### Option B: Brain Agent Only

```bash
# Run prediction agent directly
python main.py
```

#### Option C: Test Pipeline

```bash
# Test complete data collection + prediction pipeline
python test_complete_pipeline.py

# Test brain trigger feature
python test_brain_trigger.py
```

---

## 📁 Project Structure

```
Data-Collection-Agent/
├── main.py                          # Brain agent entry point
├── config.yaml                      # System configuration
├── requirements.txt                 # Python dependencies
├── .env.example                     # Environment template
│
├── api/                             # FastAPI Backend
│   ├── main.py                      # API routes & endpoints
│   └── scraper_routes.py            # Scraper execution endpoints
│
├── scraper/                         # Data Collection
│   ├── sources.py                   # Stock price scraper
│   ├── news_scraper.py              # News article scraper
│   └── db_helper.py                 # Database operations
│
├── brain/                           # AI & Prediction
│   ├── agent.py                     # Main prediction agent
│   ├── gemini_client.py             # Gemini LLM integration
│   ├── llm_client.py                # LLM abstraction layer
│   └── prompts.py                   # LLM prompt templates
│
├── controller/                      # Orchestration & Control
│   ├── scheduler.py                 # Collection scheduling
│   ├── triggers.py                  # Event-driven triggers
│   ├── watchdog.py                  # Monitoring service
│   ├── brain_trigger.py             # Entry-based brain triggering
│   ├── prioritizer.py               # Source prioritization
│   ├── budget.py                    # API call budgeting
│   ├── quality_tracker.py           # Source quality metrics
│   └── freshness.py                 # Data freshness management
│
├── database/                        # Database Layer
│   ├── schema.sql                   # Table definitions
│   ├── supabase_client.py           # Supabase client
│   └── seed_data.py                 # Initial data seeding
│
├── frontend/                        # Next.js Dashboard
│   ├── app/
│   │   ├── page.tsx                 # Main dashboard
│   │   └── layout.tsx               # App layout
│   └── lib/
│       └── supabase.ts              # Supabase client
│
└── tests/                           # Test Scripts
    ├── test_complete_pipeline.py    # Full pipeline test
    ├── test_brain_trigger.py        # Brain trigger test
    └── test_agent_flow.py           # Agent flow test
```

---

## 🗄️ Database Schema

### `targets` - Data Sources
Stores URLs and APIs to monitor for data collection.

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID | Primary key |
| `name` | VARCHAR | Source name (e.g., "Kitco Silver News") |
| `source_type` | VARCHAR | `api`, `scrape`, or `rss` |
| `url` | TEXT | URL to scrape/fetch |
| `category` | VARCHAR | `news` or `price` |
| `is_active` | BOOLEAN | Enable/disable source |
| `poll_interval_seconds` | INT | Collection frequency (default: 300) |
| `last_scraped_at` | TIMESTAMP | Last successful collection |
| `avg_utility` | DECIMAL | Quality score (0-1) |
| `avg_noise` | DECIMAL | Noise ratio (0-1) |
| `avg_cost` | DECIMAL | API call cost estimate |

### `price_data` - Silver Prices
Stores collected silver price data.

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID | Primary key |
| `target_id` | UUID | FK to targets |
| `price` | DECIMAL | Current price in USD |
| `currency` | VARCHAR | Currency (USD/INR) |
| `price_change` | DECIMAL | Absolute change |
| `price_change_percent` | DECIMAL | Percentage change |
| `high_24h` | DECIMAL | 24h high |
| `low_24h` | DECIMAL | 24h low |
| `volume` | DECIMAL | Trading volume |
| `fetched_at` | TIMESTAMP | Collection timestamp |
| `raw_data` | JSONB | Full API response |

### `news_data` - Market News
Stores scraped news articles.

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID | Primary key |
| `target_id` | UUID | FK to targets |
| `title` | TEXT | Article headline |
| `content` | TEXT | Article summary (20 words max) |
| `source_url` | TEXT | Article URL |
| `fetched_at` | TIMESTAMP | Collection timestamp |
| `raw_data` | JSONB | Full article text + metadata |

### `agent_logs` - Predictions & Reasoning
Stores AI-generated predictions and analysis.

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID | Primary key |
| `session_id` | UUID | Groups related predictions |
| `reasoning_chain` | TEXT | AI's thought process |
| `decision` | TEXT | `BULLISH`, `BEARISH`, or `NEUTRAL` |
| `prediction_value` | JSONB | Full prediction details |
| `confidence_score` | DECIMAL | Confidence level (0-1) |
| `raw_response` | JSONB | Complete LLM response |
| `created_at` | TIMESTAMP | Prediction timestamp |

---

## 🔧 Configuration

Edit `config.yaml` to customize behavior:

```yaml
# Agent Settings
agent:
  name: "Silver Scout Agent"
  version: "2.0.0"
  poll_interval_seconds: 300
  max_retries: 3

# Brain Agent Trigger
brain_trigger:
  enabled: true
  auto_trigger: true             # Auto-run when threshold met
  min_total_fresh_entries: 15    # Minimum data entries required
  check_interval_minutes: 10     # Monitoring frequency

# Stock Data Sources
stock_sources:
  - name: "alpha_vantage"
    provider: "Alpha Vantage"
    symbol: "SLV"

# News Sources
news_sources:
  - name: "silverseek_news"
    url: "https://silverseek.com/articles/silver-market-updates"
    type: "scrape"
```

---

## 🔌 API Endpoints

### Health & Status

- `GET /` - API info and links
- `GET /health` - Health check
- `GET /docs` - Swagger documentation
- `GET /api/status` - System status

### Data Collection

- `POST /api/trigger` - Manually trigger data collection
- `GET /api/metrics` - View source quality metrics
- `GET /api/freshness` - Check data freshness
- `GET /api/data/fresh` - Get fresh data only

### Brain Agent

- `GET /api/brain/ready` - Check if brain can run (entry count status)
- `POST /api/brain/trigger` - Manually trigger prediction
- `POST /api/predict` - Generate prediction (legacy endpoint)

### Watchdog

- `POST /api/watchdog/start` - Start event monitoring
- `POST /api/watchdog/stop` - Stop monitoring
- `GET /api/watchdog/status` - Check watchdog status

### Scraper Execution

- `POST /api/scraper/stock/execute` - Run stock scraper
- `POST /api/scraper/news/execute` - Run news scraper

---

## 🧪 Testing

```bash
# Test brain trigger feature
python test_brain_trigger.py

# Test complete pipeline (scraper → brain → logs)
python test_complete_pipeline.py

# Test Gemini integration
python test_gemini_integration.py

# Test scraper integration
python test_scraper_integration.py
```

---

## 🎯 Usage Examples

### Check Brain Readiness

```python
from controller import check_brain_ready, get_fresh_entry_counts

# Get current entry counts
counts = get_fresh_entry_counts()
print(f"Total entries: {counts['total_count']}")
# Output: Total entries: 4

# Check if brain can run
is_ready, details = check_brain_ready()
if is_ready:
    print("Brain agent ready!")
else:
    print(f"Need {details['remaining']} more entries")
# Output: Need 11 more entries
```

### Trigger Collection & Prediction

```python
from controller import run_collection_cycle
from controller.brain_trigger import trigger_brain_agent_sync

# Collect data
plan = run_collection_cycle(total_budget=10)
print(f"Collected from {len(plan['sources'])} sources")

# Run prediction (if enough data)
result = trigger_brain_agent_sync()
if result['success']:
    pred = result['prediction']
    print(f"Prediction: {pred['decision']}")
    print(f"Target: ${pred['target_price']}")
    print(f"Confidence: {pred['confidence_score']:.2%}")
```

### Use API via cURL

```bash
# Check brain readiness
curl http://localhost:8000/api/brain/ready

# Trigger prediction
curl -X POST http://localhost:8000/api/brain/trigger

# Get latest prediction
curl http://localhost:8000/api/predictions/latest
```

---

## 🔑 Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `SUPABASE_URL` | ✅ | Supabase project URL |
| `SUPABASE_KEY` | ✅ | Supabase anon/public key |
| `GEMINI_API_KEY` | ✅ | Google Gemini API key |
| `MISTRAL_API_KEY` | ⚠️ | Mistral AI key (for news sentiment) |
| `ALPHA_VANTAGE_API_KEY` | ⚠️ | Alpha Vantage key (for price data) |
| `FINNHUB_API_KEY` | ⚠️ | Finnhub key (alternative price source) |

---

## 📊 How It Works

### 1. Data Collection Flow

```
Watchdog Event → Controller → Scheduler → Prioritizer → Budget Allocator → Scraper → Database
```

1. **Event Detection**: Watchdog monitors for triggers (price change, staleness, quality drop)
2. **Collection Planning**: Controller creates collection plan with source priorities
3. **Budget Allocation**: Distributes API calls based on source quality
4. **Scraping**: Collects price/news data from prioritized sources
5. **Storage**: Saves to Supabase with quality metrics

### 2. Brain Agent Flow

```
Entry Count Check → Data Fetch → LLM Analysis → Prediction Generation → Storage
```

1. **Threshold Check**: Verifies min 15 fresh entries exist
2. **Data Retrieval**: Fetches latest price + news from database
3. **Market Analysis**: Gemini analyzes price trends
4. **Sentiment Analysis**: Mistral evaluates news sentiment
5. **Prediction**: Combines analysis with 80/20 weighting (price/news)
6. **Logging**: Saves prediction + reasoning to agent_logs

### 3. Auto-Trigger Logic

After each data collection:
- Check fresh entry count
- If `>= 15 entries`: Auto-trigger brain agent
- If `< 15 entries`: Wait for more data

---

## 🤝 Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

---

## 📝 License

MIT License - see LICENSE file for details

---

## 🙏 Acknowledgments

- **Supabase** - Database and backend infrastructure
- **Google Gemini** - AI-powered market analysis
- **Mistral AI** - News sentiment analysis
- **Next.js** - Modern web framework
- **FastAPI** - High-performance Python API

---

## 📧 Support

For issues, questions, or feature requests:
- Open an issue on GitHub
- Check existing documentation in `/docs`
- Review API docs at `/docs` endpoint

---

**Built with ❤️ for autonomous silver market analysis**
