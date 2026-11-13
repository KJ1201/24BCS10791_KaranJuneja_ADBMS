"""
Trigger unit tests — run with: poetry run pytest tests/ -v
Requires a live PostgreSQL DB with schema applied.
"""
import os
import threading
import pytest
import psycopg2
from dotenv import load_dotenv

load_dotenv()
DB_URL = os.environ["DATABASE_URL"]


@pytest.fixture(scope="module")
def conn():
    c = psycopg2.connect(DB_URL)
    c.autocommit = False
    yield c
    c.close()


def _fresh_conn():
    c = psycopg2.connect(DB_URL)
    c.autocommit = False
    return c


def _get_stock(cur, bt):
    cur.execute("SELECT units_available FROM blood_stock WHERE blood_type=%s", (bt,))
    return cur.fetchone()[0]


def _any_donor(cur):
    cur.execute("SELECT donor_id, blood_type FROM donors LIMIT 1")
    return cur.fetchone()


def _any_hospital(cur):
    cur.execute("SELECT hospital_id FROM hospitals LIMIT 1")
    row = cur.fetchone()
    return row[0] if row else None


# ── Test 1: stock increments on donation ──────────────────────────────────────
def test_stock_increments_on_donation(conn):
    cur = conn.cursor()
    donor_id, bt = _any_donor(cur)
    before = _get_stock(cur, bt)
    cur.execute("INSERT INTO donations(donor_id, blood_type) VALUES (%s,%s)", (donor_id, bt))
    conn.commit()
    after = _get_stock(cur, bt)
    assert after == before + 1


# ── Test 2: request fulfilled when stock is sufficient ───────────────────────
def test_request_fulfilled_when_stock_ok(conn):
    cur = conn.cursor()
    donor_id, bt = _any_donor(cur)
    h_id = _any_hospital(cur)
    # Ensure at least 1 unit
    cur.execute("INSERT INTO donations(donor_id, blood_type) VALUES (%s,%s)", (donor_id, bt))
    conn.commit()
    cur.execute(
        "INSERT INTO blood_requests(hospital_id,blood_type,units_needed) VALUES(%s,%s,1)",
        (h_id, bt),
    )
    conn.commit()
    cur.execute("SELECT status FROM blood_requests ORDER BY request_id DESC LIMIT 1")
    assert cur.fetchone()[0] == "fulfilled"


# ── Test 3: request rejected when stock is 0 ─────────────────────────────────
def test_request_rejected_when_no_stock(conn):
    cur = conn.cursor()
    h_id = _any_hospital(cur)
    cur.execute("UPDATE blood_stock SET units_available=0 WHERE blood_type='AB-'")
    conn.commit()
    with pytest.raises(psycopg2.errors.RaiseException):
        cur.execute(
            "INSERT INTO blood_requests(hospital_id,blood_type,units_needed) VALUES(%s,'AB-',1)",
            (h_id,),
        )
        conn.commit()
    conn.rollback()


# ── Test 4: concurrent requests — only one wins ───────────────────────────────
def test_concurrent_requests_only_one_wins():
    # Set stock to exactly 1
    c = _fresh_conn()
    c.autocommit = True
    c.cursor().execute("UPDATE blood_stock SET units_available=1 WHERE blood_type='O-'")
    c.close()

    c2 = _fresh_conn()
    c2.cursor().execute("SELECT hospital_id FROM hospitals LIMIT 1")
    h_id = c2.cursor().fetchone()
    c2.close()

    # Re-fetch cleanly
    cx = psycopg2.connect(DB_URL)
    cx.autocommit = True
    cur = cx.cursor()
    cur.execute("SELECT hospital_id FROM hospitals LIMIT 1")
    h_id = cur.fetchone()[0]
    cx.close()

    results = {}

    def attempt(label):
        conn = _fresh_conn()
        try:
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO blood_requests(hospital_id,blood_type,units_needed) VALUES(%s,'O-',1)",
                (h_id,),
            )
            conn.commit()
            results[label] = "ok"
        except Exception:
            conn.rollback()
            results[label] = "fail"
        finally:
            conn.close()

    t1 = threading.Thread(target=attempt, args=("A",))
    t2 = threading.Thread(target=attempt, args=("B",))
    t1.start(); t2.start()
    t1.join();  t2.join()

    successes = sum(1 for v in results.values() if v == "ok")
    assert successes == 1, f"Expected exactly 1 success, got {successes}: {results}"

    # Stock must not be negative
    cx = psycopg2.connect(DB_URL)
    cx.autocommit = True
    cur = cx.cursor()
    cur.execute("SELECT units_available FROM blood_stock WHERE blood_type='O-'")
    stock = cur.fetchone()[0]
    cx.close()
    assert stock >= 0

