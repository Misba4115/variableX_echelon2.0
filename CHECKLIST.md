# Project Checklist

## Phase 1: Database Setup ✅
- [x] Create Supabase project
- [x] Create schema.sql with 3 tables (targets, market_data, agent_logs)
- [x] Run schema in Supabase SQL Editor
- [x] Create seed_data.py script
- [x] Insert 5 initial targets (4 news + 1 API)
- [x] Document tables in README

---

## Phase 2: Scraper Module
- [ ] Test Playwright web scraper
- [ ] Scrape news from Kitco, Reuters, Investing.com
- [ ] Fetch silver prices from Metals API
- [ ] Store data in `market_data` table
- [ ] Add error handling

---

## Phase 3: Brain/LangGraph
- [ ] Setup OpenAI connection
- [ ] Create LangGraph state machine (COLLECT → ANALYZE → PREDICT → LOG)
- [ ] Implement analysis prompts
- [ ] Store reasoning in `agent_logs` table

---

## Phase 4: Dashboard
- [ ] Setup Streamlit app
- [ ] Price chart + news feed components
- [ ] Agent logs viewer
- [ ] Predictions display

---

## Phase 5: Integration
- [ ] Connect all modules
- [ ] End-to-end testing
- [ ] Documentation review
