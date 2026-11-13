import streamlit as st

st.set_page_config(page_title="Blood Bank Management System", page_icon="🩸", layout="wide")

st.title("🩸 Blood Bank Management System")
st.caption("Advanced DBMS Project · PostgreSQL + PL/pgSQL + Streamlit")

st.markdown("""
| Screen | Feature Demonstrated | Team Member |
|--------|----------------------|-------------|
| 1 · Donor Management | Schema design, FK & CHECK constraints | Member 1 |
| 2 · Blood Stock | Triggers (auto stock update on donation) | Member 2 |
| 3 · Hospital Requests | Concurrency — SELECT FOR UPDATE | Member 3 |
| 4 · Expiry & Compatibility | BEFORE INSERT trigger, generated columns | Member 4 |
| 5 · Admin Reports | Materialized views, RLS, ER diagram | Member 5 |

**Tech stack:** PostgreSQL 15 · PL/pgSQL · psycopg2 · Streamlit · Faker
""")

st.info("Use the sidebar to navigate between screens.")

try:
    from app import db
    rows, _ = db.run("SELECT COUNT(*) FROM donors")
    st.success(f"✅ Database connected — {rows[0][0]:,} donors in system")
except Exception as e:
    st.error(f"Database not connected: {e}")

