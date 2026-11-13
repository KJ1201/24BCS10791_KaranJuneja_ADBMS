"""
Screen 3 — Hospital Requests
DBMS Feature: Concurrency control via SELECT FOR UPDATE inside trigger
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import threading
import streamlit as st
import pandas as pd
import psycopg2
from dotenv import load_dotenv
from app.db import run

load_dotenv()
DB_URL = os.environ["DATABASE_URL"]

st.title("🏥 Hospital Requests")

with st.expander("❓ Problem — concurrent requests without locking"):
    st.markdown("""
Two hospitals simultaneously request the last available unit of `O-` blood.
Without a lock, both transactions read `units_available = 1`, both decide
"enough stock", both decrement — stock drops to **-1**. Data corruption.

**Naive approach:** `SELECT` then `UPDATE` in two separate statements (TOCTOU bug).
""")

st.markdown("### ✅ Solution — `SELECT FOR UPDATE` inside the trigger")
st.code("""
SELECT units_available INTO avail
FROM   blood_stock
WHERE  blood_type = NEW.blood_type
FOR UPDATE;  -- locks the row; second transaction waits
""", language="sql")

# ── Submit a single request ───────────────────────────────────────────────────
st.subheader("Submit Request")
hosp_rows, _ = run("SELECT hospital_id, name FROM hospitals ORDER BY name LIMIT 100")
if not hosp_rows:
    st.warning("No hospitals — run the seed script first.")
else:
    hosp_map = {f"{r[0]} — {r[1]}": r[0] for r in hosp_rows}
    with st.form("req_form"):
        hkey  = st.selectbox("Hospital", list(hosp_map))
        bt    = st.selectbox("Blood type", ["A+","A-","B+","B-","AB+","AB-","O+","O-"])
        units = st.number_input("Units needed", 1, 100, 1)
        if st.form_submit_button("Request"):
            try:
                run(
                    "INSERT INTO blood_requests(hospital_id,blood_type,units_needed) VALUES(%s,%s,%s)",
                    (hosp_map[hkey], bt, units),
                    commit=True,
                )
                st.success("Request fulfilled ✅")
            except Exception as e:
                st.error(f"Rejected: {e}")

st.divider()

# ── Concurrency race demo ─────────────────────────────────────────────────────
st.subheader("🔀 Concurrency Race Demo")
st.markdown(
    "Sets stock of `O-` to **1 unit**, then fires **two threads simultaneously** — "
    "both try to claim that 1 unit. Only one should win."
)

if st.button("▶ Run Race"):
    # Force stock to 1
    run("UPDATE blood_stock SET units_available=1 WHERE blood_type='O-'", commit=True)

    # Pick any hospital
    h_rows, _ = run("SELECT hospital_id FROM hospitals LIMIT 1")
    if not h_rows:
        st.error("Need at least one hospital.")
        st.stop()
    h_id = h_rows[0][0]

    results = {}

    def attempt(label: str):
        conn = psycopg2.connect(DB_URL)
        conn.autocommit = False
        try:
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO blood_requests(hospital_id,blood_type,units_needed) VALUES(%s,'O-',1)",
                (h_id,),
            )
            conn.commit()
            results[label] = "✅ Fulfilled"
        except Exception as e:
            conn.rollback()
            results[label] = f"❌ Rejected — {e}"
        finally:
            conn.close()

    t1 = threading.Thread(target=attempt, args=("Thread A",))
    t2 = threading.Thread(target=attempt, args=("Thread B",))
    t1.start(); t2.start()
    t1.join();  t2.join()

    for label, result in results.items():
        st.write(f"**{label}:** {result}")

    rows, _ = run("SELECT units_available FROM blood_stock WHERE blood_type='O-'")
    st.info(f"O- stock after race: **{rows[0][0]} units** (never goes negative)")

st.divider()

# ── Recent requests ───────────────────────────────────────────────────────────
st.subheader("Recent Requests")
rows, cols = run("""
    SELECT r.request_id, h.name AS hospital, r.blood_type,
           r.units_needed, r.status, r.requested_at
    FROM   blood_requests r
    JOIN   hospitals h USING(hospital_id)
    ORDER  BY r.requested_at DESC LIMIT 50
""")
if rows:
    st.dataframe(pd.DataFrame(rows, columns=cols), use_container_width=True)

