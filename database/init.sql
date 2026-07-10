-- JHA ML Platform — Full Schema
-- 11 tables, dependency-ordered

-- 1. users
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL DEFAULT 'analyst'
        CHECK (role IN ('admin', 'data_scientist', 'analyst')),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 2. projects
CREATE TABLE IF NOT EXISTS projects (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) UNIQUE NOT NULL,
    description TEXT,
    status VARCHAR(50) DEFAULT 'draft'
        CHECK (status IN ('draft', 'experimenting', 'deployed', 'archived')),
    model_type VARCHAR(100),
    use_case VARCHAR(255),
    data_source_config JSONB DEFAULT '{}',
    label_column VARCHAR(255),
    time_column VARCHAR(255),
    train_eval_split FLOAT DEFAULT 0.8,
    embargo_days INTEGER DEFAULT 14,
    created_by INTEGER REFERENCES users(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 3. datasets
CREATE TABLE IF NOT EXISTS datasets (
    id SERIAL PRIMARY KEY,
    project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    name VARCHAR(255),
    source_type VARCHAR(50)
        CHECK (source_type IN ('upload', 'bigquery', 'featurestore', 's3')),
    filepath VARCHAR(500),
    file_size BIGINT,
    row_count INTEGER,
    column_count INTEGER,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 4. dataset_versions
CREATE TABLE IF NOT EXISTS dataset_versions (
    id SERIAL PRIMARY KEY,
    dataset_id INTEGER NOT NULL REFERENCES datasets(id) ON DELETE CASCADE,
    version_num INTEGER NOT NULL,
    row_count INTEGER,
    column_count INTEGER,
    positive_count INTEGER,
    negative_count INTEGER,
    positive_rate FLOAT,
    profile_stats JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(dataset_id, version_num)
);

-- 5. runs
CREATE TABLE IF NOT EXISTS runs (
    id SERIAL PRIMARY KEY,
    project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    name VARCHAR(255),
    preset VARCHAR(50) DEFAULT 'performance'
        CHECK (preset IN ('quality', 'performance', 'speed', 'experimental')),
    status VARCHAR(50) DEFAULT 'queued'
        CHECK (status IN ('queued', 'running', 'completed', 'failed')),
    feature_count INTEGER,
    feature_selection VARCHAR(50) DEFAULT 'auto',
    hyperparams JSONB DEFAULT '{}',
    metrics JSONB DEFAULT '{}',
    duration_seconds FLOAT,
    is_champion BOOLEAN DEFAULT FALSE,
    is_challenger BOOLEAN DEFAULT FALSE,
    created_by INTEGER REFERENCES users(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ
);

-- 6. model_artifacts
CREATE TABLE IF NOT EXISTS model_artifacts (
    id SERIAL PRIMARY KEY,
    run_id INTEGER NOT NULL REFERENCES runs(id) ON DELETE CASCADE,
    filepath VARCHAR(500) NOT NULL,
    model_format VARCHAR(100),
    file_size BIGINT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 7. rules
CREATE TABLE IF NOT EXISTS rules (
    id SERIAL PRIMARY KEY,
    project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    condition_json JSONB NOT NULL,
    outcome VARCHAR(50) NOT NULL
        CHECK (outcome IN ('APPROVE', 'REVIEW', 'BLOCK', 'ESCALATE')),
    order_position INTEGER NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    frequency_daily INTEGER DEFAULT 0,
    last_fired_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 8. predictions
CREATE TABLE IF NOT EXISTS predictions (
    id SERIAL PRIMARY KEY,
    project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    run_id INTEGER REFERENCES runs(id),
    transaction_id VARCHAR(255),
    score FLOAT,
    decision VARCHAR(50),
    threshold_used FLOAT,
    rule_trace JSONB DEFAULT '[]',
    latency_ms FLOAT,
    features_used JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 9. labels
CREATE TABLE IF NOT EXISTS labels (
    id SERIAL PRIMARY KEY,
    prediction_id INTEGER NOT NULL REFERENCES predictions(id) ON DELETE CASCADE,
    analyst_id INTEGER NOT NULL REFERENCES users(id),
    label VARCHAR(50) NOT NULL
        CHECK (label IN ('fraud', 'legit', 'skip')),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 10. alerts
CREATE TABLE IF NOT EXISTS alerts (
    id SERIAL PRIMARY KEY,
    project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    alert_type VARCHAR(50) NOT NULL
        CHECK (alert_type IN ('drift', 'latency', 'error', 'slo')),
    severity VARCHAR(10) NOT NULL
        CHECK (severity IN ('low', 'med', 'high')),
    feature_name VARCHAR(255),
    metric_value FLOAT,
    threshold_value FLOAT,
    message TEXT,
    status VARCHAR(50) DEFAULT 'open'
        CHECK (status IN ('open', 'acknowledged', 'resolved')),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    resolved_at TIMESTAMPTZ
);

-- 11. audit_log
CREATE TABLE IF NOT EXISTS audit_log (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    action VARCHAR(100) NOT NULL,
    entity_type VARCHAR(100),
    entity_id INTEGER,
    details JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);
CREATE INDEX IF NOT EXISTS idx_projects_status ON projects(status);
CREATE INDEX IF NOT EXISTS idx_projects_created_by ON projects(created_by);
CREATE INDEX IF NOT EXISTS idx_datasets_project_id ON datasets(project_id);
CREATE INDEX IF NOT EXISTS idx_dataset_versions_dataset_id ON dataset_versions(dataset_id);
CREATE INDEX IF NOT EXISTS idx_runs_project_id ON runs(project_id);
CREATE INDEX IF NOT EXISTS idx_runs_status ON runs(status);
CREATE INDEX IF NOT EXISTS idx_runs_project_champion ON runs(project_id) WHERE is_champion = TRUE;
CREATE INDEX IF NOT EXISTS idx_model_artifacts_run_id ON model_artifacts(run_id);
CREATE INDEX IF NOT EXISTS idx_rules_project_id ON rules(project_id);
CREATE INDEX IF NOT EXISTS idx_rules_project_order ON rules(project_id, order_position);
CREATE INDEX IF NOT EXISTS idx_predictions_project_id ON predictions(project_id);
CREATE INDEX IF NOT EXISTS idx_predictions_run_id ON predictions(run_id);
CREATE INDEX IF NOT EXISTS idx_predictions_created_at ON predictions(created_at);
CREATE INDEX IF NOT EXISTS idx_predictions_transaction_id ON predictions(transaction_id);
CREATE INDEX IF NOT EXISTS idx_labels_prediction_id ON labels(prediction_id);
CREATE INDEX IF NOT EXISTS idx_labels_analyst_id ON labels(analyst_id);
CREATE INDEX IF NOT EXISTS idx_alerts_project_id ON alerts(project_id);
CREATE INDEX IF NOT EXISTS idx_alerts_status ON alerts(status);
CREATE INDEX IF NOT EXISTS idx_audit_log_user_id ON audit_log(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_log_entity ON audit_log(entity_type, entity_id);
CREATE INDEX IF NOT EXISTS idx_audit_log_created_at ON audit_log(created_at);
