# backend/scripts/clear_demo_cache.py

import os
import psycopg2
from pathlib import Path
from dotenv import load_dotenv

# Load env variables from backend directory
load_dotenv(Path(__file__).parent.parent / ".env")

KEEP_TYPES = (
    "GROSS_WEIGHT",
    "NET_WEIGHT",
    "PACKAGE_COUNT",
)

database_url = os.getenv("DATABASE_URL")

if not database_url:
    print("Error: DATABASE_URL not found in .env")
    exit(1)

try:
    conn = psycopg2.connect(database_url)
    with conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM norm_cache;")
        before = cur.fetchone()[0]

        cur.execute(
            """
            DELETE FROM norm_cache
            WHERE split_part(cache_key, ':', 1) NOT IN %s
            """,
            (KEEP_TYPES,)
        )

        deleted = cur.rowcount
        conn.commit()

    print(f"Cache reduced from {before} → {before - deleted} entries (deleted {deleted}).")
    print("Ready for optional live Tier 3 demonstration.")

except Exception as exc:
    print(f"Failed to clear demo cache in PostgreSQL: {exc}")
finally:
    if 'conn' in locals() and conn:
        conn.close()
