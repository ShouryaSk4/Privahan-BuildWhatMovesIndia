-- ====================================================================
-- Parivahan Seva — Complete PostgreSQL Schema (Supabase)
-- ====================================================================

CREATE TABLE IF NOT EXISTS dim_rto (
    rto_code VARCHAR(10) PRIMARY KEY,
    state_code VARCHAR(5) NOT NULL,
    office_name VARCHAR(150) NOT NULL,
    address TEXT NOT NULL,
    jurisdiction_pincodes TEXT[] DEFAULT '{}',
    has_adtt_track BOOLEAN DEFAULT TRUE,
    daily_slot_capacity INT DEFAULT 30,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS dim_vehicle_class (
    class_code VARCHAR(10) PRIMARY KEY,
    title VARCHAR(100) NOT NULL,
    description TEXT NOT NULL,
    min_age INT NOT NULL DEFAULT 18,
    statutory_fee INT NOT NULL DEFAULT 1350,
    has_gear BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS dim_journey_stages (
    stage_code VARCHAR(50) PRIMARY KEY,
    order_index INT NOT NULL,
    title VARCHAR(100) NOT NULL,
    next_action_type VARCHAR(50),
    next_action_label VARCHAR(150),
    sla_days INT DEFAULT 21,
    validity_days INT DEFAULT 180,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS dim_exam_questions (
    question_id VARCHAR(50) PRIMARY KEY,
    category VARCHAR(50) NOT NULL DEFAULT 'rules',
    prompt_en TEXT NOT NULL,
    prompt_hi TEXT NOT NULL,
    options_en JSONB NOT NULL,
    options_hi JSONB NOT NULL,
    correct_option INT NOT NULL,
    explanation_en TEXT NOT NULL,
    explanation_hi TEXT NOT NULL,
    icon VARCHAR(10) DEFAULT '📌',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS tbl_citizens (
    citizen_id VARCHAR(100) PRIMARY KEY,
    phone VARCHAR(20) UNIQUE NOT NULL,
    full_name VARCHAR(150) NOT NULL,
    dob DATE NOT NULL,
    gender VARCHAR(10) DEFAULT 'other',
    photo_url TEXT,
    aadhaar_last_four VARCHAR(4),
    registered_address TEXT NOT NULL,
    pincode VARCHAR(10),
    gps_suggested_rto VARCHAR(10) REFERENCES dim_rto(rto_code),
    addresses_match BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS tbl_identity_verifications (
    verification_id BIGSERIAL PRIMARY KEY,
    citizen_id VARCHAR(100) NOT NULL REFERENCES tbl_citizens(citizen_id) ON DELETE CASCADE,
    pan_number VARCHAR(20),
    pan_name VARCHAR(150),
    pan_dob DATE,
    mismatches JSONB DEFAULT '[]'::jsonb,
    clear_to_submit BOOLEAN DEFAULT TRUE,
    source VARCHAR(50) DEFAULT 'digilocker_aadhaar',
    verified_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS tbl_applications (
    application_number VARCHAR(50) PRIMARY KEY,
    citizen_id VARCHAR(100) NOT NULL REFERENCES tbl_citizens(citizen_id) ON DELETE CASCADE,
    rto_code VARCHAR(10) NOT NULL REFERENCES dim_rto(rto_code),
    vehicle_class VARCHAR(10) NOT NULL REFERENCES dim_vehicle_class(class_code),
    current_stage VARCHAR(50) NOT NULL REFERENCES dim_journey_stages(stage_code),
    selected_jurisdiction_type VARCHAR(20) DEFAULT 'aadhaar',
    confirmed_rto_code VARCHAR(10) REFERENCES dim_rto(rto_code),
    ll_valid_till TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS tbl_exam_sessions (
    session_token VARCHAR(100) PRIMARY KEY,
    application_number VARCHAR(50) NOT NULL REFERENCES tbl_applications(application_number) ON DELETE CASCADE,
    score INT NOT NULL DEFAULT 0,
    passed BOOLEAN NOT NULL DEFAULT FALSE,
    integrity_score INT NOT NULL DEFAULT 100,
    integrity_tier VARCHAR(20) NOT NULL DEFAULT 'clear',
    violations_log JSONB DEFAULT '[]'::jsonb,
    completed_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS tbl_track_bookings (
    booking_id VARCHAR(50) PRIMARY KEY,
    application_number VARCHAR(50) NOT NULL REFERENCES tbl_applications(application_number) ON DELETE CASCADE,
    slot_id VARCHAR(50) NOT NULL,
    rto_code VARCHAR(10) NOT NULL REFERENCES dim_rto(rto_code),
    scheduled_at TIMESTAMPTZ NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'booked',
    failure_checkpoint VARCHAR(100),
    booked_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS tbl_licences (
    licence_number VARCHAR(50) PRIMARY KEY,
    application_number VARCHAR(50) NOT NULL REFERENCES tbl_applications(application_number) ON DELETE CASCADE,
    citizen_id VARCHAR(100) NOT NULL REFERENCES tbl_citizens(citizen_id) ON DELETE CASCADE,
    licence_type VARCHAR(10) NOT NULL,
    vehicle_classes TEXT[] NOT NULL DEFAULT '{"LMV"}',
    issued_at TIMESTAMPTZ DEFAULT NOW(),
    valid_till TIMESTAMPTZ NOT NULL,
    status VARCHAR(20) DEFAULT 'active'
);

CREATE TABLE IF NOT EXISTS tbl_agent_sessions (
    session_id VARCHAR(100) PRIMARY KEY,
    citizen_id VARCHAR(100) REFERENCES tbl_citizens(citizen_id) ON DELETE SET NULL,
    channel VARCHAR(30) DEFAULT 'web_voice',
    active_intent VARCHAR(100),
    pending_action JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS tbl_agent_messages (
    message_id BIGSERIAL PRIMARY KEY,
    session_id VARCHAR(100) NOT NULL REFERENCES tbl_agent_sessions(session_id) ON DELETE CASCADE,
    sender VARCHAR(20) NOT NULL,
    content TEXT NOT NULL,
    tool_called VARCHAR(100),
    tool_result JSONB,
    interactive_options JSONB DEFAULT '[]'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_citizens_phone ON tbl_citizens(phone);
CREATE INDEX IF NOT EXISTS idx_applications_citizen ON tbl_applications(citizen_id);
CREATE INDEX IF NOT EXISTS idx_agent_messages_session ON tbl_agent_messages(session_id, created_at);
