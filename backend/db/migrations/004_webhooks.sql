-- Migration 004: Webhook Subscriptions
-- Add webhook subscription management tables

CREATE TABLE IF NOT EXISTS webhook_subscriptions (
    id VARCHAR(255) PRIMARY KEY,
    url TEXT NOT NULL,
    events TEXT[] NOT NULL,
    secret VARCHAR(255) NOT NULL,
    active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_triggered TIMESTAMP,
    total_deliveries INTEGER DEFAULT 0,
    failed_deliveries INTEGER DEFAULT 0
);

CREATE INDEX idx_webhook_active ON webhook_subscriptions(active);
CREATE INDEX idx_webhook_events ON webhook_subscriptions USING GIN(events);

-- Add webhook delivery log for debugging
CREATE TABLE IF NOT EXISTS webhook_delivery_log (
    id SERIAL PRIMARY KEY,
    subscription_id VARCHAR(255) REFERENCES webhook_subscriptions(id) ON DELETE CASCADE,
    event VARCHAR(100) NOT NULL,
    payload JSONB NOT NULL,
    status VARCHAR(50) NOT NULL, -- success, failed, retrying
    response_code INTEGER,
    response_body TEXT,
    attempt_number INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_webhook_log_subscription ON webhook_delivery_log(subscription_id);
CREATE INDEX idx_webhook_log_event ON webhook_delivery_log(event);
CREATE INDEX idx_webhook_log_status ON webhook_delivery_log(status);
CREATE INDEX idx_webhook_log_created ON webhook_delivery_log(created_at);
