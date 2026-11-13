-- ============================================================
-- ROW-LEVEL SECURITY (RLS)
-- Demonstrates database-level security policies using session context
-- Runs on default role (no custom roles required)
-- ============================================================

ALTER TABLE donations      ENABLE ROW LEVEL SECURITY;
ALTER TABLE blood_requests ENABLE ROW LEVEL SECURITY;

-- Drop existing policies if re-running
DROP POLICY IF EXISTS rls_donations_policy ON donations;
DROP POLICY IF EXISTS rls_requests_policy ON blood_requests;

-- Policy on donations:
-- Admin sees all; Donors see only their own donations
CREATE POLICY rls_donations_policy ON donations
    FOR ALL
    USING (
        current_setting('app.current_role', TRUE) = 'admin'
        OR current_setting('app.current_role', TRUE) IS NULL
        OR donor_id = NULLIF(current_setting('app.current_donor_id', TRUE), '')::INT
    );

-- Policy on blood_requests:
-- Admin sees all; Hospitals see only their own requests
CREATE POLICY rls_requests_policy ON blood_requests
    FOR ALL
    USING (
        current_setting('app.current_role', TRUE) = 'admin'
        OR current_setting('app.current_role', TRUE) IS NULL
        OR hospital_id = NULLIF(current_setting('app.current_hospital_id', TRUE), '')::INT
    );
