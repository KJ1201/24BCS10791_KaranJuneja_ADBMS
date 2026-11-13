-- ============================================================
-- VIEWS & MATERIALIZED VIEWS
-- ============================================================

-- Live stock view
CREATE VIEW v_available_stock AS
SELECT bt.blood_type,
       COALESCE(bs.units_available, 0) AS units_available,
       bs.last_updated
FROM   blood_types bt
LEFT   JOIN blood_stock bs USING (blood_type);

-- Materialized: monthly donation totals (Admin Reports)
CREATE MATERIALIZED VIEW mv_monthly_donations AS
SELECT DATE_TRUNC('month', donated_at)::DATE AS month,
       blood_type,
       COUNT(*)::INT                          AS total_donations
FROM   donations
GROUP  BY 1, 2
ORDER  BY 1 DESC, 2;

CREATE UNIQUE INDEX ON mv_monthly_donations(month, blood_type);

-- Materialized: current stock snapshot (Admin Reports)
CREATE MATERIALIZED VIEW mv_stock_snapshot AS
SELECT blood_type, units_available, last_updated
FROM   blood_stock;

-- Dynamic role-filtered views (demonstrating role-based access without custom DB roles)
CREATE OR REPLACE VIEW v_my_donations AS
SELECT donation_id, donor_id, blood_type, donated_at, expiry_date
FROM   donations
WHERE  current_setting('app.current_role', TRUE) = 'admin'
   OR  donor_id = NULLIF(current_setting('app.current_donor_id', TRUE), '')::INT;

CREATE OR REPLACE VIEW v_my_requests AS
SELECT request_id, hospital_id, blood_type, units_needed, status, requested_at, fulfilled_at
FROM   blood_requests
WHERE  current_setting('app.current_role', TRUE) = 'admin'
   OR  hospital_id = NULLIF(current_setting('app.current_hospital_id', TRUE), '')::INT;

