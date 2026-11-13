import os

import psycopg2
import psycopg2.pool
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

@st.cache_resource
def _pool():
    return psycopg2.pool.ThreadedConnectionPool(
        2, 10, os.environ["DATABASE_URL"]
    )


def get_conn():
    return _pool().getconn()


def release(conn):
    _pool().putconn(conn)


def run(sql, params=(), session_vars=None, commit=False):
    """Execute a query and return (rows, col_names). Uses default DB user."""
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            if session_vars:
                for k, v in session_vars.items():
                    cur.execute("SELECT set_config(%s, %s, false)", (k, str(v)))
            cur.execute(sql, params)
            if commit:
                conn.commit()
            try:
                rows = cur.fetchall()
                cols = [d[0] for d in cur.description]
                return rows, cols
            except Exception:
                return [], []
    except Exception:
        conn.rollback()
        raise
    finally:
        release(conn)

