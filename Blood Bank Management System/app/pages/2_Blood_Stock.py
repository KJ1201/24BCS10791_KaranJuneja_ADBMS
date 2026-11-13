"""
Screen 2 — Blood Stock
DBMS Feature: AFTER INSERT trigger auto-increments stock on donation
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import streamlit as st
import pandas as pd
from app.db import run

st.title("🩸 Blood Stock")

with st.expander("❓ Problem — manual stock updates"):
    st.markdown("""
Without a trigger, every time a donation is recorded the application must
**also** manually update the stock table. If that second step is missed
(bug, crash, etc.) the stock count becomes wrong.

**Naive approach:** two separate UPDATE + INSERT calls in application code.
""")

st.markdown("### ✅ Solution — `trg_increment_stock` trigger")
st.code("""
AFTER INSERT ON donations → fn_increment_stock()
  UPDATE blood_stock SET units_available = units_available + 1 …
""", language="sql")

# ── Record a donation ─────────────────────────────────────────────────────────
st.subheader("Record Donation")
rows, _ = run("SELECT donor_id, name FROM donors ORDER BY donor_id DESC LIMIT 200")
if not rows:
    st.warning("No donors yet — go to Donor Management and register one.")
    st.stop()

donor_map = {f"{r[0]} — {r[1]}": r[0] for r in rows}
with st.form("add_donation"):
    donor_key = st.selectbox("Donor", list(donor_map))
    bt         = st.selectbox("Blood type", ["A+","A-","B+","B-","AB+","AB-","O+","O-"])
    if st.form_submit_button("Record"):
        try:
            run(
                "INSERT INTO donations(donor_id, blood_type) VALUES (%s,%s)",
                (donor_map[donor_key], bt),
                commit=True,
            )
            st.success("Donation recorded. Stock updated automatically by trigger ✅")
        except Exception as e:
            st.error(str(e))

st.divider()

# ── Current stock ─────────────────────────────────────────────────────────────
st.subheader("Current Stock")
rows, cols = run("SELECT blood_type, units_available, last_updated FROM v_available_stock ORDER BY blood_type")
df = pd.DataFrame(rows, columns=cols)
col1, col2 = st.columns(2)
with col1:
    st.dataframe(df, use_container_width=True)
with col2:
    st.bar_chart(df.set_index("blood_type")["units_available"])

