"""
Screen 1 — Donor Management
DBMS Feature: Schema design, FK constraints, CHECK constraints
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import streamlit as st
import pandas as pd
from app.db import run

st.title("👤 Donor Management")

with st.expander("❓ Problem — without FK constraints"):
    st.markdown("""
Without referential integrity, a donation row could reference a `donor_id`
that doesn't exist, or use a blood type like `'XX'` that is invalid.

**Naive approach:** application-level validation only — easy to bypass or forget.
""")

st.markdown("### ✅ Solution — FK & CHECK constraints enforced by PostgreSQL")

# ── Register a new donor ──────────────────────────────────────────────────────
st.subheader("Register Donor")
with st.form("add_donor"):
    name  = st.text_input("Full name")
    bt    = st.selectbox("Blood type", ["A+","A-","B+","B-","AB+","AB-","O+","O-"])
    dob   = st.date_input("Date of birth")
    phone = st.text_input("Phone")
    email = st.text_input("Email")
    if st.form_submit_button("Register"):
        try:
            run(
                "INSERT INTO donors(name,blood_type,dob,phone,email) VALUES(%s,%s,%s,%s,%s)",
                (name, bt, str(dob), phone, email),
                commit=True,
            )
            st.success(f"Donor '{name}' registered.")
        except Exception as e:
            st.error(str(e))

st.divider()

# ── Search donors ─────────────────────────────────────────────────────────────
st.subheader("Search Donors")
q = st.text_input("Name or blood type filter")
sql = """
    SELECT donor_id, name, blood_type, dob, phone, email, created_at
    FROM   donors
    WHERE  name ILIKE %s OR blood_type = %s
    ORDER  BY donor_id DESC
    LIMIT  100
"""
rows, cols = run(sql, (f"%{q}%", q))
if rows:
    st.dataframe(pd.DataFrame(rows, columns=cols), use_container_width=True)
else:
    st.info("No donors found.")

st.divider()
st.caption("🔍 **Demo:** Try registering with blood type `ZZ` — PostgreSQL rejects it via FK constraint.")

