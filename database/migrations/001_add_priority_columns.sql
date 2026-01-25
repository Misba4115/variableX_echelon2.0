-- ===========================================
-- ADD COLUMNS FOR PRIORITY CALCULATION
-- Run this in Supabase SQL Editor
-- ===========================================

-- Add priority tracking columns to targets table
ALTER TABLE targets ADD COLUMN IF NOT EXISTS avg_utility NUMERIC DEFAULT 0.5;
ALTER TABLE targets ADD COLUMN IF NOT EXISTS avg_noise NUMERIC DEFAULT 0.1;
ALTER TABLE targets ADD COLUMN IF NOT EXISTS avg_cost NUMERIC DEFAULT 1.0;
