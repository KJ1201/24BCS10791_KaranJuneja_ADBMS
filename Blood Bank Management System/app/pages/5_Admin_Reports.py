"""
Screen 5 — Admin Reports
DBMS Feature: Materialized views, Row-Level Security, ER diagram
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import streamlit as st
import pandas as pd
from app.db import run

st.title("📊 Admin Reports")

with st.expander("❓ Problem — expensive aggregations & unrestricted data access"):
    st.markdown("""
- Running `COUNT(*) GROUP BY month` over millions of rows on every page load is slow.
- Without RLS, any DB user can `SELECT * FROM donations` and see everyone's data.

**Naive approach:** aggregate in Python after fetching all rows; rely on app code for access control.
""")

st.markdown("### ✅ Solution — Materialized Views + Row-Level Security")

# ── Materialized view: monthly donations ──────────────────────────────────────
st.subheader("Monthly Donations (Materialized View)")
if st.button("🔄 Refresh Materialized Views"):
    run("REFRESH MATERIALIZED VIEW CONCURRENTLY mv_monthly_donations", commit=True)
    run("REFRESH MATERIALIZED VIEW mv_stock_snapshot", commit=True)
    st.success("Views refreshed.")

rows, cols = run("""
    SELECT month::TEXT, blood_type, total_donations
    FROM   mv_monthly_donations
    ORDER  BY month DESC, blood_type
    LIMIT  96
""")
if rows:
    df = pd.DataFrame(rows, columns=cols)
    pivot = df.pivot(index="month", columns="blood_type", values="total_donations").fillna(0)
    st.bar_chart(pivot)
    with st.expander("Raw data"):
        st.dataframe(df, use_container_width=True)
else:
    st.info("No data — run seed script, then refresh views.")

st.divider()

# ── Materialized view: stock snapshot ────────────────────────────────────────
st.subheader("Stock Snapshot (Materialized View)")
rows, cols = run("SELECT blood_type, units_available, last_updated FROM mv_stock_snapshot ORDER BY blood_type")
if rows:
    st.dataframe(pd.DataFrame(rows, columns=cols), use_container_width=True)

st.divider()

# ── Row-Level Security demo ───────────────────────────────────────────────────
st.subheader("Row-Level Security Demo")
st.markdown("Switch simulated user context to see how PostgreSQL filters rows automatically using session context.")

role = st.radio("Active role", ["Admin", "Donor", "Hospital"], horizontal=True)

session_vars = {"app.current_role": role.lower()}
if role == "Donor":
    donor_rows, _ = run("SELECT donor_id, name FROM donors LIMIT 20")
    if donor_rows:
        dm = {f"{r[0]} — {r[1]}": r[0] for r in donor_rows}
        dk = st.selectbox("Viewing as donor", list(dm))
        session_vars["app.current_donor_id"] = dm[dk]
elif role == "Hospital":
    hosp_rows, _ = run("SELECT hospital_id, name FROM hospitals LIMIT 20")
    if hosp_rows:
        hm = {f"{r[0]} — {r[1]}": r[0] for r in hosp_rows}
        hk = st.selectbox("Viewing as hospital", list(hm))
        session_vars["app.current_hospital_id"] = hm[hk]

col1, col2 = st.columns(2)

with col1:
    st.markdown("**Donations visible**")
    try:
        rows, cols = run(
            "SELECT donation_id, donor_id, blood_type, donated_at FROM v_my_donations ORDER BY donation_id DESC LIMIT 20",
            session_vars=session_vars,
        )
        st.dataframe(pd.DataFrame(rows, columns=cols) if rows else pd.DataFrame(), use_container_width=True)
        st.caption(f"{len(rows)} row(s) returned")
    except Exception as e:
        st.error(str(e))

with col2:
    st.markdown("**Requests visible**")
    try:
        rows, cols = run(
            "SELECT request_id, hospital_id, blood_type, status FROM v_my_requests ORDER BY request_id DESC LIMIT 20",
            session_vars=session_vars,
        )
        st.dataframe(pd.DataFrame(rows, columns=cols) if rows else pd.DataFrame(), use_container_width=True)
        st.caption(f"{len(rows)} row(s) returned")
    except Exception as e:
        st.error(str(e))

st.divider()

# ── ER Diagram ────────────────────────────────────────────────────────────────
st.subheader("ER Diagram")
er_path = os.path.join(os.path.dirname(__file__), "..", "..", "docs", "er_diagram.png")
if os.path.exists(er_path):
    st.image(er_path, use_container_width=True)
else:
    st.info("Place `docs/er_diagram.png` (exported from dbdiagram.io) here to embed it.")
    st.markdown("""
**DBML snippet** — paste into [dbdiagram.io](https://dbdiagram.io) to generate the PNG:

```
Table blood_types { blood_type varchar [pk] }
Table donors { donor_id int [pk, increment]; name varchar; blood_type varchar [ref: > blood_types.blood_type]; dob date; phone varchar; email varchar }
Table hospitals { hospital_id int [pk, increment]; name varchar; city varchar; contact varchar }
Table blood_stock { blood_type varchar [pk, ref: > blood_types.blood_type]; units_available int; last_updated timestamp }
Table donations { donation_id int [pk, increment]; donor_id int [ref: > donors.donor_id]; blood_type varchar [ref: > blood_types.blood_type]; donated_at timestamp; expiry_date date }
Table blood_requests { request_id int [pk, increment]; hospital_id int [ref: > hospitals.hospital_id]; blood_type varchar [ref: > blood_types.blood_type]; units_needed int; status varchar; requested_at timestamp; fulfilled_at timestamp }
```
""")

