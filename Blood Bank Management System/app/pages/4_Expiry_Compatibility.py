"""
Screen 4 — Expiry & Compatibility
DBMS Feature: BEFORE INSERT trigger refuses bad requests; generated columns for expiry
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import streamlit as st
import pandas as pd
from app.db import run

st.title("⏰ Expiry & Compatibility")

with st.expander("❓ Problem — no DB-level expiry enforcement"):
    st.markdown("""
If expiry logic lives only in the application, a direct SQL INSERT
(e.g. from a script or another app) can bypass it and fulfil a request
even when all available blood is expired or incompatible.

**Naive approach:** `WHERE expiry_date > NOW()` check in application code only.
""")

st.markdown("### ✅ Solution — trigger + generated columns")
st.markdown("""
- `expiry_date` is a **generated column**: `donated_at::DATE + 42` (42-day shelf life) — computed by PostgreSQL, never wrong.
- The `trg_fulfill_request` trigger checks `units_available` **at the DB level** before committing any request.
- If stock is 0 (because all bags expired and were removed), the trigger raises an exception.
""")

# ── Expiring donations ────────────────────────────────────────────────────────
st.subheader("Donations Expiring Soon (next 7 days)")
rows, cols = run("""
    SELECT donation_id, donor_id, blood_type, donated_at::DATE, expiry_date
    FROM   donations
    WHERE  expiry_date BETWEEN CURRENT_DATE AND CURRENT_DATE + 7
    ORDER  BY expiry_date
    LIMIT  100
""")
if rows:
    st.dataframe(pd.DataFrame(rows, columns=cols), use_container_width=True)
else:
    st.info("No donations expiring in the next 7 days.")

st.divider()

# ── Already-expired donations ─────────────────────────────────────────────────
st.subheader("Expired Donations")
rows, cols = run("""
    SELECT donation_id, donor_id, blood_type, donated_at::DATE, expiry_date
    FROM   donations
    WHERE  expiry_date < CURRENT_DATE
    ORDER  BY expiry_date DESC
    LIMIT  100
""")
if rows:
    st.dataframe(pd.DataFrame(rows, columns=cols), use_container_width=True)
else:
    st.info("No expired donations on record.")

st.divider()

# ── Live demo: try to request a blood type with 0 stock ──────────────────────
st.subheader("🔬 Demo — Request Blood With Zero Stock")
st.markdown("Force a blood type to 0 units and try to request it — the trigger should reject it.")

col1, col2 = st.columns(2)
with col1:
    demo_bt = st.selectbox("Blood type", ["A+","A-","B+","B-","AB+","AB-","O+","O-"], key="demo_bt")
    if st.button("Set stock to 0"):
        run(f"UPDATE blood_stock SET units_available=0 WHERE blood_type=%s", (demo_bt,), commit=True)
        st.warning(f"{demo_bt} stock set to 0.")

with col2:
    hosp_rows, _ = run("SELECT hospital_id, name FROM hospitals LIMIT 1")
    if hosp_rows:
        h_id = hosp_rows[0][0]
        if st.button("Try to request 1 unit"):
            try:
                run(
                    "INSERT INTO blood_requests(hospital_id,blood_type,units_needed) VALUES(%s,%s,1)",
                    (h_id, demo_bt),
                    commit=True,
                )
                st.success("Fulfilled (stock was available).")
            except Exception as e:
                st.error(f"Trigger rejected the request ✅\n\n`{e}`")
    else:
        st.info("Run seed script to add hospitals.")

