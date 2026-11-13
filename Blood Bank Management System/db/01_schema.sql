-- ============================================================
-- SCHEMA: Blood Bank Management System
-- ============================================================

CREATE TABLE blood_types (
    blood_type VARCHAR(3) PRIMARY KEY
);

INSERT INTO blood_types VALUES ('A+'),('A-'),('B+'),('B-'),('AB+'),('AB-'),('O+'),('O-');

CREATE TABLE donors (
    donor_id   SERIAL PRIMARY KEY,
    name       VARCHAR(100) NOT NULL,
    blood_type VARCHAR(3)   NOT NULL REFERENCES blood_types(blood_type),
    dob        DATE         NOT NULL,
    phone      VARCHAR(20),
    email      VARCHAR(100) UNIQUE,
    created_at TIMESTAMPTZ  DEFAULT now()
);

CREATE TABLE hospitals (
    hospital_id SERIAL PRIMARY KEY,
    name        VARCHAR(150) NOT NULL,
    city        VARCHAR(100),
    contact     VARCHAR(20)
);

CREATE TABLE blood_stock (
    blood_type      VARCHAR(3) PRIMARY KEY REFERENCES blood_types(blood_type),
    units_available INT        NOT NULL DEFAULT 0 CHECK (units_available >= 0),
    last_updated    TIMESTAMPTZ DEFAULT now()
);

-- Seed stock rows so the trigger can UPDATE instead of INSERT
INSERT INTO blood_stock(blood_type, units_available)
SELECT blood_type, 0 FROM blood_types;

CREATE TABLE donations (
    donation_id SERIAL PRIMARY KEY,
    donor_id    INT         NOT NULL REFERENCES donors(donor_id),
    blood_type  VARCHAR(3)  NOT NULL REFERENCES blood_types(blood_type),
    donated_at  TIMESTAMP   DEFAULT CURRENT_TIMESTAMP,
    expiry_date DATE        GENERATED ALWAYS AS ((donated_at::DATE + 42)) STORED
);

CREATE TABLE blood_requests (
    request_id   SERIAL PRIMARY KEY,
    hospital_id  INT         NOT NULL REFERENCES hospitals(hospital_id),
    blood_type   VARCHAR(3)  NOT NULL REFERENCES blood_types(blood_type),
    units_needed INT         NOT NULL CHECK (units_needed > 0),
    status       VARCHAR(20) NOT NULL DEFAULT 'pending'
                             CHECK (status IN ('pending','fulfilled','rejected')),
    requested_at TIMESTAMPTZ DEFAULT now(),
    fulfilled_at TIMESTAMPTZ
);

-- Indexes
CREATE INDEX idx_donations_donor   ON donations(donor_id);
CREATE INDEX idx_donations_expiry  ON donations(expiry_date);
CREATE INDEX idx_requests_hospital ON blood_requests(hospital_id);
CREATE INDEX idx_requests_status   ON blood_requests(status);
CREATE INDEX idx_pending_requests  ON blood_requests(blood_type) WHERE status = 'pending';

