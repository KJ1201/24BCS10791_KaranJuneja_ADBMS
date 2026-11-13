# Blood Bank Management System

Advanced DBMS course project — PostgreSQL · PL/pgSQL · Streamlit

## Team & Screens

| Screen | DBMS Feature | Member |
|--------|-------------|--------|
| 1 · Donor Management | Schema, FK & CHECK constraints | Member 1 |
| 2 · Blood Stock | AFTER INSERT trigger (auto stock update) | Member 2 |
| 3 · Hospital Requests | Concurrency — SELECT FOR UPDATE | Member 3 |
| 4 · Expiry & Compatibility | BEFORE INSERT trigger, generated columns | Member 4 |
| 5 · Admin Reports | Materialized views, RLS, ER diagram | Member 5 |

## Prerequisites

- PostgreSQL 15+
- Python 3.11+
- pip (or Poetry)

## Setup

### 1. Install Dependencies
You can use standard `pip` (easiest):
```bash
pip install -r requirements.txt
```
*Or if you use Poetry:*
```bash
poetry install
```

### 2. Configure Environment
Copy `.env.example` to `.env` and configure your database connection string:
```bash
# In Windows PowerShell:
Copy-Item .env.example .env
```

### 3. Database Setup (psql or pgAdmin)
Run the SQL files in order in pgAdmin or psql:
- `db/01_schema.sql`
- `db/02_triggers.sql`
- `db/03_views.sql`
- `db/04_rls.sql`
*(All run under your default `postgres` user. No extra roles required!)*

### 4. Seed Data (~10,000 records)
```bash
python db/05_seed.py
```

### 5. Run the Streamlit Web App
```bash
streamlit run app/main.py
```

## ER Diagram

Generate PNG from [dbdiagram.io](https://dbdiagram.io) using this DBML, then save as `docs/er_diagram.png`:

```
Table blood_types { blood_type varchar [pk] }

Table donors {
  donor_id   int [pk, increment]
  name       varchar
  blood_type varchar [ref: > blood_types.blood_type]
  dob        date
  phone      varchar
  email      varchar
}

Table hospitals {
  hospital_id int [pk, increment]
  name        varchar
  city        varchar
  contact     varchar
}

Table blood_stock {
  blood_type      varchar [pk, ref: > blood_types.blood_type]
  units_available int
  last_updated    timestamp
}

Table donations {
  donation_id int [pk, increment]
  donor_id    int [ref: > donors.donor_id]
  blood_type  varchar [ref: > blood_types.blood_type]
  donated_at  timestamp
  expiry_date date
}

Table blood_requests {
  request_id   int [pk, increment]
  hospital_id  int [ref: > hospitals.hospital_id]
  blood_type   varchar [ref: > blood_types.blood_type]
  units_needed int
  status       varchar
  requested_at timestamp
  fulfilled_at timestamp
}
```

## Key Design Points

- **Triggers** — stock is updated automatically on every donation insert; no application code needed.
- **SELECT FOR UPDATE** — inside the fulfill trigger, locks the stock row so two simultaneous requests can never both succeed against the same last unit.
- **Generated column** — `expiry_date = donated_at + 42 days` computed by PostgreSQL; always correct.
- **Materialized views** — monthly aggregates are pre-computed; Admin Reports page refreshes them on demand.
- **Row-Level Security** — `donor_role` sees only their own donations; `hospital_role` sees only their own requests; `admin_role` sees everything.

