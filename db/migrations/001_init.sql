CREATE TABLE IF NOT EXISTS admins (
    id SERIAL PRIMARY KEY,
    telegram_id BIGINT UNIQUE NOT NULL,
    added_by BIGINT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS instagram_accounts (
    id SERIAL PRIMARY KEY,
    ig_user_id TEXT NOT NULL UNIQUE,
    username TEXT NOT NULL,
    access_token TEXT NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT true,
    needs_reauth BOOLEAN NOT NULL DEFAULT false,
    last_error TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS rules (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    keyword TEXT NOT NULL,
    message TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS rule_accounts (
    rule_id INTEGER NOT NULL REFERENCES rules(id) ON DELETE CASCADE,
    account_id INTEGER NOT NULL REFERENCES instagram_accounts(id) ON DELETE CASCADE,
    PRIMARY KEY (rule_id, account_id)
);

CREATE TABLE IF NOT EXISTS processed_events (
    event_id TEXT PRIMARY KEY,
    account_id INTEGER REFERENCES instagram_accounts(id) ON DELETE SET NULL,
    processed_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    result TEXT
);

-- Внутренний технический механизм (не пользовательская логика):
-- связывает Meta OAuth callback с телеграм-админом, который его инициировал.
CREATE TABLE IF NOT EXISTS oauth_states (
    state TEXT PRIMARY KEY,
    telegram_id BIGINT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_rule_accounts_account ON rule_accounts(account_id);
CREATE INDEX IF NOT EXISTS idx_rule_accounts_rule ON rule_accounts(rule_id);