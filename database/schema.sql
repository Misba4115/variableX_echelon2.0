-- WARNING: This schema is for context only and is not meant to be run.
-- Table order and constraints may not be valid for execution.

CREATE TABLE public.agent_logs (
  id uuid NOT NULL DEFAULT uuid_generate_v4(),
  session_id uuid NOT NULL,
  reasoning_chain text,
  decision text,
  prediction_value jsonb,
  confidence_score numeric,
  raw_response jsonb,
  created_at timestamp with time zone DEFAULT now(),
  CONSTRAINT agent_logs_pkey PRIMARY KEY (id)
);
CREATE TABLE public.news_data (
  id uuid NOT NULL DEFAULT uuid_generate_v4(),
  target_id uuid,
  title text NOT NULL,
  content text,
  source_url text,
  fetched_at timestamp with time zone DEFAULT now(),
  raw_data jsonb,
  CONSTRAINT news_data_pkey PRIMARY KEY (id),
  CONSTRAINT news_data_target_id_fkey FOREIGN KEY (target_id) REFERENCES public.targets(id)
);
CREATE TABLE public.price_data (
  id uuid NOT NULL DEFAULT uuid_generate_v4(),
  target_id uuid,
  price numeric NOT NULL,
  currency character varying DEFAULT 'USD'::character varying,
  price_change numeric,
  price_change_percent numeric,
  high_24h numeric,
  low_24h numeric,
  volume numeric,
  fetched_at timestamp with time zone DEFAULT now(),
  source_timestamp timestamp with time zone,
  raw_data jsonb,
  CONSTRAINT price_data_pkey PRIMARY KEY (id),
  CONSTRAINT price_data_target_id_fkey FOREIGN KEY (target_id) REFERENCES public.targets(id)
);
CREATE TABLE public.targets (
  id uuid NOT NULL DEFAULT uuid_generate_v4(),
  name character varying NOT NULL,
  source_type character varying NOT NULL CHECK (source_type::text = ANY (ARRAY['api'::character varying, 'scrape'::character varying, 'rss'::character varying]::text[])),
  url text NOT NULL,
  category character varying DEFAULT 'general'::character varying,
  scrape_selector text,
  api_endpoint text,
  headers jsonb DEFAULT '{}'::jsonb,
  is_active boolean DEFAULT true,
  poll_interval_seconds integer DEFAULT 300,
  last_scraped_at timestamp with time zone,
  updated_at timestamp with time zone DEFAULT now(),
  avg_utility numeric DEFAULT 0.5,
  avg_noise numeric DEFAULT 0.1,
  avg_cost numeric DEFAULT 1.0,
  CONSTRAINT targets_pkey PRIMARY KEY (id)
);