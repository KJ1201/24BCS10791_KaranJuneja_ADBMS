-- ============================================================
-- TRIGGERS
-- ============================================================

-- 1. Auto-increment stock when a donation is recorded
CREATE OR REPLACE FUNCTION fn_increment_stock()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN
    UPDATE blood_stock
    SET units_available = units_available + 1,
        last_updated    = now()
    WHERE blood_type = NEW.blood_type;
    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_increment_stock
AFTER INSERT ON donations
FOR EACH ROW EXECUTE FUNCTION fn_increment_stock();


-- 2. Validate and fulfill a blood request (BEFORE INSERT)
--    Uses SELECT FOR UPDATE to prevent race conditions.
CREATE OR REPLACE FUNCTION fn_fulfill_request()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
DECLARE
    avail INT;
BEGIN
    -- Lock the stock row for this blood type
    SELECT units_available INTO avail
    FROM   blood_stock
    WHERE  blood_type = NEW.blood_type
    FOR UPDATE;

    IF avail IS NULL OR avail < NEW.units_needed THEN
        RAISE EXCEPTION 'Insufficient stock for %. Available: %, Requested: %',
            NEW.blood_type, COALESCE(avail, 0), NEW.units_needed;
    END IF;

    UPDATE blood_stock
    SET units_available = units_available - NEW.units_needed,
        last_updated    = now()
    WHERE blood_type = NEW.blood_type;

    NEW.status       := 'fulfilled';
    NEW.fulfilled_at := now();
    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_fulfill_request
BEFORE INSERT ON blood_requests
FOR EACH ROW EXECUTE FUNCTION fn_fulfill_request();

