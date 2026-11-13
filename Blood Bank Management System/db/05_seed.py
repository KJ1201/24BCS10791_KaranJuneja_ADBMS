"""
Seed the blood_bank database with realistic data using Faker.

Usage:
    python db/05_seed.py              # 10 000 records (demo default)
    python db/05_seed.py --count 1000000  # 1 M records (stress test)
"""
import argparse
import os
import random

import psycopg2
from dotenv import load_dotenv
from faker import Faker

load_dotenv()

BLOOD_TYPES = ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"]
BATCH = 1000


def seed(count: int) -> None:
    conn = psycopg2.connect(os.environ["DATABASE_URL"])
    cur = conn.cursor()

    # Donors (~half the count)
    n_donors = max(count // 2, 10)
    fake = Faker("en_IN")
    print(f"Inserting {n_donors} donors…")
    batch = []
    for _ in range(n_donors):
        batch.append((
            fake.name(),
            random.choice(BLOOD_TYPES),
            fake.date_of_birth(minimum_age=18, maximum_age=65),
            fake.phone_number()[:20],
            fake.unique.email(),
        ))
        if len(batch) == BATCH:
            cur.executemany(
                "INSERT INTO donors(name,blood_type,dob,phone,email) "
                "VALUES (%s,%s,%s,%s,%s) ON CONFLICT DO NOTHING",
                batch,
            )
            conn.commit()
            batch.clear()
    if batch:
        cur.executemany(
            "INSERT INTO donors(name,blood_type,dob,phone,email) "
            "VALUES (%s,%s,%s,%s,%s) ON CONFLICT DO NOTHING",
            batch,
        )
        conn.commit()

    # Hospitals (fixed 50)
    print("Inserting 50 hospitals…")
    for _ in range(50):
        cur.execute(
            "INSERT INTO hospitals(name,city,contact) VALUES (%s,%s,%s) ON CONFLICT DO NOTHING",
            (fake.company() + " Hospital", fake.city(), fake.phone_number()[:20]),
        )
    conn.commit()

    # Donations (triggers auto-update blood_stock)
    cur.execute("SELECT donor_id, blood_type FROM donors")
    donor_rows = cur.fetchall()
    print(f"Inserting {count} donations (trigger updates stock automatically)…")
    batch = []
    for donor_id, bt in random.choices(donor_rows, k=count):
        batch.append((donor_id, bt))
        if len(batch) == BATCH:
            cur.executemany(
                "INSERT INTO donations(donor_id, blood_type) VALUES (%s,%s)", batch
            )
            conn.commit()
            batch.clear()
    if batch:
        cur.executemany(
            "INSERT INTO donations(donor_id, blood_type) VALUES (%s,%s)", batch
        )
        conn.commit()

    # Refresh materialized views
    cur.execute("REFRESH MATERIALIZED VIEW mv_monthly_donations")
    cur.execute("REFRESH MATERIALIZED VIEW mv_stock_snapshot")
    conn.commit()

    cur.close()
    conn.close()
    print("Done.")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--count", type=int, default=10_000)
    args = ap.parse_args()
    seed(args.count)

