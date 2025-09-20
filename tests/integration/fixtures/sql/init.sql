-- Database initialization for Helios integration tests
-- This script sets up the test database schema and initial data

-- Create test database schema
CREATE SCHEMA IF NOT EXISTS helios_test;

-- Sessions table for orchestrator
CREATE TABLE IF NOT EXISTS sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(255) NOT NULL,
    session_id VARCHAR(255) UNIQUE NOT NULL,
    workflow_state VARCHAR(100) DEFAULT 'initialized',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE,
    configuration JSONB,
    workflow_history JSONB DEFAULT '[]'::jsonb
);

-- Profiles table for profile data
CREATE TABLE IF NOT EXISTS profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    profile_id VARCHAR(255) UNIQUE NOT NULL,
    session_id VARCHAR(255) REFERENCES sessions(session_id),
    user_id VARCHAR(255) NOT NULL,
    raw_data JSONB NOT NULL,
    processed_data JSONB,
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    processing_status VARCHAR(50) DEFAULT 'pending'
);

-- Career paths table for strategist output
CREATE TABLE IF NOT EXISTS career_paths (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    path_id VARCHAR(255) UNIQUE NOT NULL,
    profile_id VARCHAR(255) REFERENCES profiles(profile_id),
    session_id VARCHAR(255) REFERENCES sessions(session_id),
    path_data JSONB NOT NULL,
    probability DECIMAL(3,2),
    timeline_months INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Market analysis table for analyst output
CREATE TABLE IF NOT EXISTS market_analysis (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    analysis_id VARCHAR(255) UNIQUE NOT NULL,
    profile_id VARCHAR(255) REFERENCES profiles(profile_id),
    session_id VARCHAR(255) REFERENCES sessions(session_id),
    market_data JSONB NOT NULL,
    resume_optimization JSONB,
    competitive_analysis JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Test data table for validation
CREATE TABLE IF NOT EXISTS test_data (
    id SERIAL PRIMARY KEY,
    test_name VARCHAR(255) NOT NULL,
    test_data JSONB NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_sessions_session_id ON sessions(session_id);
CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_sessions_created_at ON sessions(created_at);

CREATE INDEX IF NOT EXISTS idx_profiles_profile_id ON profiles(profile_id);
CREATE INDEX IF NOT EXISTS idx_profiles_session_id ON profiles(session_id);
CREATE INDEX IF NOT EXISTS idx_profiles_user_id ON profiles(user_id);
CREATE INDEX IF NOT EXISTS idx_profiles_created_at ON profiles(created_at);

CREATE INDEX IF NOT EXISTS idx_career_paths_path_id ON career_paths(path_id);
CREATE INDEX IF NOT EXISTS idx_career_paths_profile_id ON career_paths(profile_id);
CREATE INDEX IF NOT EXISTS idx_career_paths_session_id ON career_paths(session_id);

CREATE INDEX IF NOT EXISTS idx_market_analysis_analysis_id ON market_analysis(analysis_id);
CREATE INDEX IF NOT EXISTS idx_market_analysis_profile_id ON market_analysis(profile_id);
CREATE INDEX IF NOT EXISTS idx_market_analysis_session_id ON market_analysis(session_id);

-- Insert test reference data
INSERT INTO test_data (test_name, test_data) VALUES
('sample_skills', '["Python", "JavaScript", "React", "Node.js", "PostgreSQL", "Docker", "Kubernetes", "AWS"]'),
('sample_roles', '["Software Engineer", "Senior Software Engineer", "Staff Engineer", "Principal Engineer", "Engineering Manager"]'),
('sample_companies', '["Google", "Microsoft", "Amazon", "Meta", "Apple", "Netflix", "Uber", "Airbnb"]'),
('performance_thresholds', '{"session_creation": 5, "profile_processing": 30, "career_generation": 10, "market_analysis": 15, "end_to_end": 60}')
ON CONFLICT DO NOTHING;

-- Create test user for integration tests
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT FROM pg_catalog.pg_roles WHERE rolname = 'test_user'
    ) THEN
        CREATE USER test_user WITH PASSWORD 'test_password';
    END IF;
END
$$;

-- Grant permissions to test user
GRANT USAGE ON SCHEMA public TO test_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO test_user;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO test_user;

-- Create function to clean test data
CREATE OR REPLACE FUNCTION clean_test_data()
RETURNS void AS $$
BEGIN
    -- Clean in dependency order
    DELETE FROM market_analysis WHERE session_id LIKE 'test-%' OR profile_id LIKE 'test-%';
    DELETE FROM career_paths WHERE session_id LIKE 'test-%' OR profile_id LIKE 'test-%';
    DELETE FROM profiles WHERE session_id LIKE 'test-%' OR user_id LIKE 'test-%';
    DELETE FROM sessions WHERE user_id LIKE 'test-%' OR session_id LIKE 'test-%';
END;
$$ LANGUAGE plpgsql;

-- Create function to insert test session
CREATE OR REPLACE FUNCTION create_test_session(
    p_user_id VARCHAR(255),
    p_session_id VARCHAR(255) DEFAULT NULL
)
RETURNS VARCHAR(255) AS $$
DECLARE
    v_session_id VARCHAR(255);
BEGIN
    v_session_id := COALESCE(p_session_id, 'test-session-' || extract(epoch from now())::bigint);

    INSERT INTO sessions (user_id, session_id, workflow_state, expires_at, configuration)
    VALUES (
        p_user_id,
        v_session_id,
        'initialized',
        NOW() + INTERVAL '1 hour',
        '{"timeout_minutes": 60, "language": "en", "test_mode": true}'::jsonb
    );

    RETURN v_session_id;
END;
$$ LANGUAGE plpgsql;

-- Create function to validate test data integrity
CREATE OR REPLACE FUNCTION validate_test_data_integrity()
RETURNS TABLE(
    table_name TEXT,
    issue_type TEXT,
    issue_count BIGINT,
    details TEXT
) AS $$
BEGIN
    -- Check for orphaned profiles
    RETURN QUERY
    SELECT
        'profiles'::TEXT,
        'orphaned_profiles'::TEXT,
        COUNT(*)::BIGINT,
        'Profiles without valid sessions'::TEXT
    FROM profiles p
    LEFT JOIN sessions s ON p.session_id = s.session_id
    WHERE s.session_id IS NULL;

    -- Check for orphaned career paths
    RETURN QUERY
    SELECT
        'career_paths'::TEXT,
        'orphaned_career_paths'::TEXT,
        COUNT(*)::BIGINT,
        'Career paths without valid profiles'::TEXT
    FROM career_paths cp
    LEFT JOIN profiles p ON cp.profile_id = p.profile_id
    WHERE p.profile_id IS NULL;

    -- Check for orphaned market analysis
    RETURN QUERY
    SELECT
        'market_analysis'::TEXT,
        'orphaned_market_analysis'::TEXT,
        COUNT(*)::BIGINT,
        'Market analysis without valid profiles'::TEXT
    FROM market_analysis ma
    LEFT JOIN profiles p ON ma.profile_id = p.profile_id
    WHERE p.profile_id IS NULL;

    -- Check for expired sessions
    RETURN QUERY
    SELECT
        'sessions'::TEXT,
        'expired_sessions'::TEXT,
        COUNT(*)::BIGINT,
        'Sessions past expiration time'::TEXT
    FROM sessions
    WHERE expires_at < NOW();
END;
$$ LANGUAGE plpgsql;

-- Create test monitoring view
CREATE OR REPLACE VIEW test_session_summary AS
SELECT
    s.session_id,
    s.user_id,
    s.workflow_state,
    s.created_at,
    s.expires_at,
    CASE WHEN p.profile_id IS NOT NULL THEN 1 ELSE 0 END as has_profile,
    CASE WHEN cp.path_id IS NOT NULL THEN 1 ELSE 0 END as has_career_paths,
    CASE WHEN ma.analysis_id IS NOT NULL THEN 1 ELSE 0 END as has_market_analysis,
    (CASE WHEN p.profile_id IS NOT NULL THEN 1 ELSE 0 END +
     CASE WHEN cp.path_id IS NOT NULL THEN 1 ELSE 0 END +
     CASE WHEN ma.analysis_id IS NOT NULL THEN 1 ELSE 0 END) as workflow_completeness
FROM sessions s
LEFT JOIN profiles p ON s.session_id = p.session_id
LEFT JOIN career_paths cp ON p.profile_id = cp.profile_id
LEFT JOIN market_analysis ma ON p.profile_id = ma.profile_id
WHERE s.user_id LIKE 'test-%';

-- Log initialization
INSERT INTO test_data (test_name, test_data) VALUES
('db_initialized', json_build_object('timestamp', extract(epoch from now()), 'version', '1.0.0'))
ON CONFLICT DO NOTHING;