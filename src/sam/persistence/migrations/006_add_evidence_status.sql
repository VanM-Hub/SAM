-- Migration 006: Add status column to evidence table
-- Date: 2026-07-23

ALTER TABLE evidence ADD COLUMN status TEXT DEFAULT 'collected';

-- Update existing records to have 'collected' status
UPDATE evidence SET status = 'collected' WHERE status IS NULL;