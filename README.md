# Autonomous Silver Prediction Agent

An AI-powered agent that autonomously collects silver market data, analyzes trends, and generates price predictions.

## 🏗️ Project Structure

```
Data-Collection-Agent/
├── main.py              # Main entry point
├── config.yaml          # Configuration settings
├── requirements.txt     # Python dependencies
├── .env.example         # Environment variables template
├── .gitignore           # Git ignore rules
│
├── scraper/             # Data collection
│   ├── web_scraper.py   # Playwright web scraping
│   └── metals_api.py    # Metals price API client
│
├── brain/               # AI & LangGraph logic
│   ├── graph.py         # State machine workflow
│   └── prompts.py       # LLM prompts
│
├── database/            # Supabase & state
│   ├── schema.sql       # Database schema
│   ├── db_client.py     # Supabase client
│   └── state_manager.py # Agent state tracking
│
└── dashboard/           # Streamlit UI
    └── app.py           # Dashboard application
```

## 🚀 Quick Start

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   playwright install chromium
   ```

2. **Configure environment:**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

3. **Setup Supabase:**
   - Create a project at supabase.com
   - Run `database/schema.sql` in SQL Editor

4. **Run the agent:**
   ```bash
   python main.py
   ```

5. **Launch dashboard:**
   ```bash
   streamlit run dashboard/app.py
   ```

## 🔑 Environment Variables

| Variable | Description |
|----------|-------------|
| `SUPABASE_URL` | Your Supabase project URL |
| `SUPABASE_KEY` | Supabase anon/public key |
| `METALS_API_KEY` | API key for metals-api.com |
| `OPENAI_API_KEY` | OpenAI API key for LLM |

## 📊 Database Tables

- **targets**: Monitoring URLs and APIs
- **market_data**: Price, news, and sentiment data
- **agent_logs**: Reasoning and prediction logs
