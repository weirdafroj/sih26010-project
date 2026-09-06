# SIH26010: Complete Database Schema & Architecture

## DATABASE TECHNOLOGY CHOICE
**Primary Database**: PostgreSQL 14+
**Spatial Extension**: PostGIS (for geospatial queries)
**Cache Layer**: Redis (for offline sync queue and session management)
**Time-Series**: TimescaleDB (for analytics and monitoring)

---

## DATABASE SCHEMA SETUP

### Initial Setup Script
```sql
-- Create extensions
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS timescaledb;
CREATE EXTENSION IF NOT EXISTS uuid-ossp;

-- Create schema
CREATE SCHEMA IF NOT EXISTS sih26010;
SET search_path TO sih26010;

-- Create enum types
CREATE TYPE user_role AS ENUM ('farmer', 'surveyor', 'officer', 'admin', 'reviewer');
CREATE TYPE survey_status AS ENUM ('draft', 'submitted', 'under_review', 'approved', 'rejected', 'corrections_needed');
CREATE TYPE image_type AS ENUM ('drone', 'ground', 'boundary', 'reference', 'other');
CREATE TYPE record_status AS ENUM ('draft', 'pending_approval', 'approved', 'rejected', 'archived');
CREATE TYPE sync_status AS ENUM ('pending', 'synced', 'failed', 'conflict');
CREATE TYPE boundary_quality AS ENUM ('excellent', 'good', 'fair', 'poor', 'needs_verification');
```

---

## CORE TABLES

### 1. USERS TABLE
```sql
CREATE TABLE users (
    id BIGSERIAL PRIMARY KEY,
    user_id UUID NOT NULL UNIQUE DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    phone VARCHAR(15) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    role user_role NOT NULL DEFAULT 'farmer',
    
    -- Profile Information
    profile_photo_url VARCHAR(500),
    aadhar_number VARCHAR(12),  -- Stored encrypted
    pan_number VARCHAR(10),      -- Stored encrypted
    
    -- Location Information
    district_code VARCHAR(10),
    taluka_code VARCHAR(10),
    village_name VARCHAR(255),
    
    -- Account Status
    is_active BOOLEAN DEFAULT TRUE,
    email_verified BOOLEAN DEFAULT FALSE,
    phone_verified BOOLEAN DEFAULT FALSE,
    last_login TIMESTAMP WITH TIME ZONE,
    password_reset_token VARCHAR(255),
    password_reset_expiry TIMESTAMP WITH TIME ZONE,
    
    -- Audit Fields
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by BIGINT REFERENCES users(id),
    updated_by BIGINT REFERENCES users(id)
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_phone ON users(phone);
CREATE INDEX idx_users_role ON users(role);
CREATE INDEX idx_users_district ON users(district_code);
CREATE INDEX idx_users_active ON users(is_active);
```

---

### 2. LAND PLOTS TABLE
```sql
CREATE TABLE land_plots (
    id BIGSERIAL PRIMARY KEY,
    plot_id UUID NOT NULL UNIQUE DEFAULT gen_random_uuid(),
    
    -- Plot Identification
    plot_number VARCHAR(50) UNIQUE NOT NULL,  -- MH-DIST-01-001
    owner_id BIGINT NOT NULL REFERENCES users(id),
    co_owner_id BIGINT REFERENCES users(id),
    
    -- Location Information
    district_code VARCHAR(10) NOT NULL,
    taluka_code VARCHAR(10) NOT NULL,
    village_code VARCHAR(10),
    
    -- Property Details
    area_sq_meters DECIMAL(15, 2) NOT NULL,
    area_acres DECIMAL(10, 2),
    area_hectares DECIMAL(10, 2),
    
    crop_type VARCHAR(100),
    irrigation_type VARCHAR(50),  -- rainfed, irrigated, etc
    
    -- Geospatial Data (will be populated by surveys)
    gps_centroid GEOMETRY(Point, 4326),
    boundary_geometry GEOMETRY(Polygon, 4326),
    
    -- Verification Status
    survey_count INT DEFAULT 0,
    last_survey_date TIMESTAMP WITH TIME ZONE,
    is_boundary_verified BOOLEAN DEFAULT FALSE,
    boundary_confidence DECIMAL(5, 2),  -- 0-100
    
    -- Audit Fields
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by BIGINT NOT NULL REFERENCES users(id),
    updated_by BIGINT REFERENCES users(id)
);

-- Spatial Index
CREATE INDEX idx_land_plots_boundary ON land_plots USING GIST(boundary_geometry);
CREATE INDEX idx_land_plots_centroid ON land_plots USING GIST(gps_centroid);
CREATE INDEX idx_land_plots_owner ON land_plots(owner_id);
CREATE INDEX idx_land_plots_district ON land_plots(district_code);
CREATE INDEX idx_land_plots_verified ON land_plots(is_boundary_verified);
```

---

### 3. SURVEYS TABLE
```sql
CREATE TABLE surveys (
    id BIGSERIAL PRIMARY KEY,
    survey_id UUID NOT NULL UNIQUE DEFAULT gen_random_uuid(),
    
    -- Survey Metadata
    plot_id BIGINT NOT NULL REFERENCES land_plots(id),
    surveyor_id BIGINT NOT NULL REFERENCES users(id),
    survey_date DATE NOT NULL,
    
    -- GPS Boundary Data
    gps_boundary_points INT,  -- Number of GPS points collected
    gps_boundary_geometry GEOMETRY(LineString, 4326),
    gps_accuracy_meters DECIMAL(6, 2),  -- Average accuracy
    
    -- Spatial Coverage
    coverage_area_sq_meters DECIMAL(15, 2),
    
    -- Status Tracking
    status survey_status NOT NULL DEFAULT 'draft',
    completion_percentage INT DEFAULT 0,
    
    -- Quality Metrics
    boundary_quality boundary_quality,
    surveyor_notes TEXT,
    quality_rating DECIMAL(3, 2),  -- 1-5 stars
    
    -- Syncing Information
    sync_status sync_status DEFAULT 'pending',
    offline_created BOOLEAN DEFAULT FALSE,
    device_id VARCHAR(255),
    
    -- AI Processing
    ai_boundary_confidence DECIMAL(5, 2),
    requires_manual_review BOOLEAN DEFAULT FALSE,
    
    -- Temporal Tracking
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    submitted_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Audit
    created_by BIGINT REFERENCES users(id),
    updated_by BIGINT REFERENCES users(id)
);

CREATE INDEX idx_surveys_plot ON surveys(plot_id);
CREATE INDEX idx_surveys_surveyor ON surveys(surveyor_id);
CREATE INDEX idx_surveys_status ON surveys(status);
CREATE INDEX idx_surveys_date ON surveys(survey_date);
CREATE INDEX idx_surveys_sync ON surveys(sync_status);
CREATE INDEX idx_surveys_boundary ON surveys USING GIST(gps_boundary_geometry);
CREATE INDEX idx_surveys_created ON surveys(created_at DESC);
```

---

### 4. GPS POINTS TABLE
```sql
CREATE TABLE gps_points (
    id BIGSERIAL PRIMARY KEY,
    
    survey_id BIGINT NOT NULL REFERENCES surveys(id) ON DELETE CASCADE,
    point_sequence INT NOT NULL,
    
    -- GPS Coordinates
    latitude DECIMAL(11, 8) NOT NULL,
    longitude DECIMAL(11, 8) NOT NULL,
    altitude DECIMAL(10, 2),
    
    -- Accuracy Metrics
    accuracy_meters DECIMAL(6, 2),
    
    -- Timestamps
    recorded_at TIMESTAMP WITH TIME ZONE NOT NULL,
    
    -- Point Details
    is_corner_point BOOLEAN DEFAULT FALSE,
    point_type VARCHAR(50),  -- 'corner', 'boundary', 'reference'
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_gps_points_survey ON gps_points(survey_id);
CREATE INDEX idx_gps_points_sequence ON gps_points(survey_id, point_sequence);
CREATE INDEX idx_gps_points_corner ON gps_points(is_corner_point);
```

---

### 5. SURVEY IMAGES TABLE
```sql
CREATE TABLE survey_images (
    id BIGSERIAL PRIMARY KEY,
    image_id UUID NOT NULL UNIQUE DEFAULT gen_random_uuid(),
    
    -- Association
    survey_id BIGINT NOT NULL REFERENCES surveys(id) ON DELETE CASCADE,
    
    -- Image Metadata
    image_type image_type NOT NULL,
    original_filename VARCHAR(255),
    file_size_bytes BIGINT,
    mime_type VARCHAR(50),
    
    -- Image Location
    image_url VARCHAR(500) NOT NULL,  -- CDN URL
    local_path VARCHAR(500),  -- Local storage path (optional)
    
    -- Geospatial Context
    image_latitude DECIMAL(11, 8),
    image_longitude DECIMAL(11, 8),
    image_location GEOMETRY(Point, 4326),
    
    -- Image Processing Results
    ai_analyzed BOOLEAN DEFAULT FALSE,
    ai_confidence DECIMAL(5, 2),
    detected_features VARCHAR(500),  -- JSON array
    processing_time_ms INT,
    
    -- Drone Image Specifics (if applicable)
    drone_altitude_meters DECIMAL(10, 2),
    drone_gimbal_pitch DECIMAL(6, 2),
    drone_timestamp TIMESTAMP WITH TIME ZONE,
    
    -- Captions & Notes
    caption VARCHAR(500),
    uploaded_by BIGINT REFERENCES users(id),
    
    -- Temporal
    uploaded_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_survey_images_survey ON survey_images(survey_id);
CREATE INDEX idx_survey_images_type ON survey_images(image_type);
CREATE INDEX idx_survey_images_analyzed ON survey_images(ai_analyzed);
CREATE INDEX idx_survey_images_location ON survey_images USING GIST(image_location);
```

---

### 6. LAND RECORDS TABLE
```sql
CREATE TABLE land_records (
    id BIGSERIAL PRIMARY KEY,
    record_id UUID NOT NULL UNIQUE DEFAULT gen_random_uuid(),
    
    -- Record Reference
    land_record_number VARCHAR(50) UNIQUE NOT NULL,  -- LR-MH-DIST-01-001-2026
    plot_id BIGINT NOT NULL REFERENCES land_plots(id),
    survey_id BIGINT NOT NULL REFERENCES surveys(id),
    
    -- Record Content
    owner_name VARCHAR(255) NOT NULL,
    owner_aadhar VARCHAR(12),  -- Encrypted
    co_owner_name VARCHAR(255),
    
    -- Plot Information
    plot_area_sq_meters DECIMAL(15, 2),
    plot_area_acres DECIMAL(10, 2),
    plot_area_hectares DECIMAL(10, 2),
    
    crop_type VARCHAR(100),
    irrigation_type VARCHAR(50),
    
    -- Boundary Data
    boundary_geometry GEOMETRY(Polygon, 4326),
    boundary_gps_points INT,
    
    -- Verification Data
    gps_accuracy_meters DECIMAL(6, 2),
    ai_confidence DECIMAL(5, 2),
    surveyor_name VARCHAR(255),
    surveyor_id BIGINT REFERENCES users(id),
    survey_date DATE,
    
    -- Status
    status record_status DEFAULT 'draft',
    approval_status record_status,
    
    -- Approvals
    reviewer_id BIGINT REFERENCES users(id),
    reviewed_at TIMESTAMP WITH TIME ZONE,
    review_comments TEXT,
    
    -- Document Generation
    pdf_document_url VARCHAR(500),
    json_document_url VARCHAR(500),
    document_hash VARCHAR(255),  -- SHA256 hash for verification
    
    -- Optional Blockchain
    blockchain_tx_hash VARCHAR(255),  -- For immutable verification
    blockchain_timestamp TIMESTAMP WITH TIME ZONE,
    
    -- Audit Trail
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    published_at TIMESTAMP WITH TIME ZONE,
    
    created_by BIGINT REFERENCES users(id),
    updated_by BIGINT REFERENCES users(id)
);

CREATE INDEX idx_land_records_plot ON land_records(plot_id);
CREATE INDEX idx_land_records_survey ON land_records(survey_id);
CREATE INDEX idx_land_records_status ON land_records(status);
CREATE INDEX idx_land_records_owner ON land_records(owner_aadhar);
CREATE INDEX idx_land_records_number ON land_records(land_record_number);
CREATE INDEX idx_land_records_boundary ON land_records USING GIST(boundary_geometry);
CREATE INDEX idx_land_records_created ON land_records(created_at DESC);
```

---

### 7. OFFLINE SYNC QUEUE TABLE
```sql
CREATE TABLE offline_sync_queue (
    id BIGSERIAL PRIMARY KEY,
    sync_id UUID NOT NULL UNIQUE DEFAULT gen_random_uuid(),
    
    -- Sync Details
    user_id BIGINT NOT NULL REFERENCES users(id),
    device_id VARCHAR(255),
    
    -- Data to Sync
    entity_type VARCHAR(50),  -- 'survey', 'land_plot', etc
    entity_id UUID,
    local_id VARCHAR(255),  -- ID on the mobile device
    
    -- Sync Information
    sync_status sync_status DEFAULT 'pending',
    sync_payload JSONB NOT NULL,
    
    -- Retry Information
    attempt_count INT DEFAULT 0,
    max_attempts INT DEFAULT 5,
    last_error TEXT,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    synced_at TIMESTAMP WITH TIME ZONE,
    
    -- Result
    server_entity_id BIGINT,  -- ID assigned by server
    server_entity_uuid UUID,
    
    CONSTRAINT max_attempts_check CHECK (attempt_count <= max_attempts)
);

CREATE INDEX idx_sync_queue_user ON offline_sync_queue(user_id);
CREATE INDEX idx_sync_queue_status ON offline_sync_queue(sync_status);
CREATE INDEX idx_sync_queue_device ON offline_sync_queue(device_id);
CREATE INDEX idx_sync_queue_created ON offline_sync_queue(created_at);
```

---

### 8. AUDIT LOG TABLE
```sql
CREATE TABLE audit_logs (
    id BIGSERIAL PRIMARY KEY,
    
    -- User & Action
    user_id BIGINT REFERENCES users(id),
    action VARCHAR(100),  -- 'create', 'update', 'delete', 'approve'
    entity_type VARCHAR(50),
    entity_id BIGINT,
    
    -- Change Details
    old_values JSONB,
    new_values JSONB,
    
    -- Metadata
    ip_address INET,
    user_agent VARCHAR(500),
    
    -- Timestamp
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_audit_logs_user ON audit_logs(user_id);
CREATE INDEX idx_audit_logs_entity ON audit_logs(entity_type, entity_id);
CREATE INDEX idx_audit_logs_action ON audit_logs(action);
CREATE INDEX idx_audit_logs_created ON audit_logs(created_at DESC);
```

---

### 9. ANALYTICS TABLE (TimescaleDB Hypertable)
```sql
CREATE TABLE survey_metrics (
    time TIMESTAMP WITH TIME ZONE NOT NULL,
    district_code VARCHAR(10),
    surveyor_id BIGINT,
    
    surveys_completed INT,
    surveys_failed INT,
    avg_gps_accuracy DECIMAL(6, 2),
    avg_processing_time INT,
    total_area_covered DECIMAL(15, 2),
    
    device_type VARCHAR(50),
    os_version VARCHAR(50),
    network_type VARCHAR(50)
);

-- Convert to hypertable for better time-series performance
SELECT create_hypertable('survey_metrics', 'time', if_not_exists => TRUE);

-- Retention policy (keep 6 months of detailed data)
SELECT add_retention_policy('survey_metrics', INTERVAL '6 months', if_not_exists => TRUE);

CREATE INDEX idx_survey_metrics_district ON survey_metrics(district_code, time DESC);
CREATE INDEX idx_survey_metrics_surveyor ON survey_metrics(surveyor_id, time DESC);
```

---

### 10. SETTINGS & CONFIGURATION TABLE
```sql
CREATE TABLE app_settings (
    id SERIAL PRIMARY KEY,
    
    setting_key VARCHAR(100) UNIQUE NOT NULL,
    setting_value JSONB NOT NULL,
    setting_type VARCHAR(50),  -- 'string', 'number', 'boolean', 'json'
    
    description TEXT,
    is_public BOOLEAN DEFAULT FALSE,
    
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_by BIGINT REFERENCES users(id)
);

-- Sample settings
INSERT INTO app_settings (setting_key, setting_value, setting_type) VALUES
('gps_accuracy_threshold_meters', '5.0', 'number'),
('ai_confidence_threshold', '0.85', 'number'),
('max_survey_time_minutes', '180', 'number'),
('offline_sync_interval_seconds', '300', 'number'),
('image_compression_quality', '0.8', 'number');
```

---

## DATABASE VIEWS (For Common Queries)

### Survey Completion Dashboard View
```sql
CREATE VIEW v_survey_dashboard AS
SELECT 
    d.district_code,
    COUNT(DISTINCT s.id) as total_surveys,
    COUNT(DISTINCT CASE WHEN s.status = 'completed' THEN s.id END) as completed_surveys,
    COUNT(DISTINCT CASE WHEN s.status = 'draft' THEN s.id END) as draft_surveys,
    COUNT(DISTINCT CASE WHEN s.status = 'submitted' THEN s.id END) as submitted_surveys,
    AVG(s.gps_accuracy_meters) as avg_gps_accuracy,
    SUM(lp.area_sq_meters) / 10000.0 as total_area_hectares,
    COUNT(DISTINCT s.surveyor_id) as active_surveyors
FROM surveys s
JOIN land_plots lp ON s.plot_id = lp.id
JOIN users d ON s.surveyor_id = d.id
WHERE s.created_at >= NOW() - INTERVAL '30 days'
GROUP BY d.district_code;
```

### Land Records Pending Approval View
```sql
CREATE VIEW v_pending_approvals AS
SELECT 
    lr.land_record_number,
    lp.plot_number,
    u.full_name as owner_name,
    lr.plot_area_hectares,
    s.survey_date,
    lr.created_at,
    lr.status
FROM land_records lr
JOIN land_plots lp ON lr.plot_id = lp.id
JOIN users u ON lp.owner_id = u.id
JOIN surveys s ON lr.survey_id = s.id
WHERE lr.status = 'pending_approval'
ORDER BY lr.created_at ASC;
```

---

## OPTIMIZATION STRATEGIES

### 1. Partitioning (for large tables)
```sql
-- Partition surveys by year for faster queries
CREATE TABLE surveys_2026 PARTITION OF surveys
    FOR VALUES FROM ('2026-01-01') TO ('2027-01-01');

CREATE TABLE surveys_2027 PARTITION OF surveys
    FOR VALUES FROM ('2027-01-01') TO ('2028-01-01');
```

### 2. Materialized Views (for heavy analytics)
```sql
CREATE MATERIALIZED VIEW mv_district_statistics AS
SELECT 
    d.district_code,
    COUNT(*) as plot_count,
    AVG(lp.area_sq_meters) as avg_plot_size,
    SUM(lp.area_sq_meters) as total_area
FROM land_plots lp
JOIN users u ON lp.created_by = u.id
GROUP BY d.district_code;

-- Refresh daily
-- REFRESH MATERIALIZED VIEW mv_district_statistics;
```

### 3. Connection Pooling Configuration (for production)
```
PgBouncer Configuration:
- max_client_conn = 1000
- default_pool_size = 25
- pool_mode = transaction
- reserve_pool_size = 5
```

---

## BACKUP & RECOVERY STRATEGY

### Daily Backup Script
```bash
#!/bin/bash
BACKUP_DIR="/backups/postgres"
DATE=$(date +%Y%m%d_%H%M%S)

# Full backup
pg_dump -U postgres sih26010 | gzip > $BACKUP_DIR/full_$DATE.sql.gz

# Incremental WAL backup
pg_basebackup -D $BACKUP_DIR/wal_$DATE -Ft -z

# Upload to S3
aws s3 cp $BACKUP_DIR/ s3://sih26010-backups/ --recursive
```

---

## SECURITY BEST PRACTICES

### 1. Encryption at Rest
```sql
-- Enable transparent data encryption (TDE)
ALTER DATABASE sih26010 SET ssl = ON;
```

### 2. Row-Level Security
```sql
-- Farmers can only see their own plots
CREATE POLICY farmer_plots_policy ON land_plots
    USING (owner_id = current_user_id OR owner_id = co_owner_id);

ALTER TABLE land_plots ENABLE ROW LEVEL SECURITY;
```

### 3. Sensitive Data Masking
```sql
-- Mask Aadhar in views for general users
CREATE VIEW v_land_plots_masked AS
SELECT 
    id,
    plot_number,
    CASE WHEN current_user != 'admin' THEN '****' || RIGHT(aadhar_number, 4)
         ELSE aadhar_number
    END as aadhar_number
FROM land_plots;
```

---

## PERFORMANCE TUNING

### Key Configuration (postgresql.conf)
```
# Memory
shared_buffers = 256MB  # 25% of system RAM
effective_cache_size = 1GB  # 50-75% of system RAM
work_mem = 16MB

# Parallel Query Execution
max_parallel_workers_per_gather = 4
max_parallel_workers = 8

# Logging
log_statement = 'all'
log_duration = on
log_min_duration_statement = 1000  # Log queries > 1 second

# WAL & Checkpointing
wal_level = replica
max_wal_senders = 10
```

### Query Optimization Tips
```sql
-- Use EXPLAIN ANALYZE to find slow queries
EXPLAIN ANALYZE
SELECT * FROM surveys 
WHERE plot_id = 123 AND created_at > NOW() - INTERVAL '30 days';

-- Vacuum regularly
VACUUM ANALYZE land_plots;

-- Reindex if needed
REINDEX INDEX idx_surveys_plot;
```

---

## MIGRATION STRATEGY (From Legacy Systems)

### Data Import Script
```python
# import_legacy_data.py
import psycopg2
from legacy_system import get_plot_data

conn = psycopg2.connect("dbname=sih26010")
cur = conn.cursor()

for plot in get_plot_data():
    cur.execute("""
        INSERT INTO land_plots (plot_number, owner_id, area_sq_meters, ...)
        VALUES (%s, %s, %s, ...)
    """, (plot['number'], plot['owner_id'], plot['area']))

conn.commit()
cur.close()
conn.close()
```

---

## MONITORING & ALERTING

### Critical Metrics to Monitor
```sql
-- Table size monitoring
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
FROM pg_tables
WHERE schemaname = 'sih26010'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;

-- Query performance
SELECT 
    query,
    calls,
    total_time,
    mean_time
FROM pg_stat_statements
ORDER BY mean_time DESC LIMIT 10;

-- Connection monitoring
SELECT datname, count(*) FROM pg_stat_activity GROUP BY datname;
```

---

## DISASTER RECOVERY PLAN

**RTO (Recovery Time Objective)**: 1 hour
**RPO (Recovery Point Objective)**: 15 minutes

1. **Automated Failover**: Hot standby replica
2. **Daily Backups**: Full backup + incremental WAL
3. **Point-in-Time Recovery**: Enabled with continuous archiving
4. **Test Recovery**: Monthly recovery drills

