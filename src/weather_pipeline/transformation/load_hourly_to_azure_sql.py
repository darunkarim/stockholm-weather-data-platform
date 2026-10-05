import os
from pathlib import Path

import pandas as pd
import pyodbc
from dotenv import load_dotenv


# ---------------------------------------------------------
# PATHS
# ---------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[3]

INPUT_PATH = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "stockholm_temperature_hourly_silver.csv"
)


# ---------------------------------------------------------
# ENVIRONMENT VARIABLES
# ---------------------------------------------------------

# The .env file contains our Azure SQL connection information.
load_dotenv(
    PROJECT_ROOT
    / "src"
    / "weather_pipeline"
    / "ingestion"
    / ".env"
)


SERVER = os.getenv("AZURE_SQL_SERVER")
DATABASE = os.getenv("AZURE_SQL_DATABASE")
USERNAME = os.getenv("AZURE_SQL_USERNAME")
PASSWORD = os.getenv("AZURE_SQL_PASSWORD")


# ---------------------------------------------------------
# VALIDATE ENVIRONMENT VARIABLES
# ---------------------------------------------------------

required_variables = {
    "AZURE_SQL_SERVER": SERVER,
    "AZURE_SQL_DATABASE": DATABASE,
    "AZURE_SQL_USERNAME": USERNAME,
    "AZURE_SQL_PASSWORD": PASSWORD,
}

missing_variables = [
    name
    for name, value in required_variables.items()
    if not value
]

if missing_variables:
    raise ValueError(
        "Missing environment variables: "
        + ", ".join(missing_variables)
    )


# ---------------------------------------------------------
# LOAD SILVER DATA
# ---------------------------------------------------------

print("=" * 60)
print("LOADING SILVER HOURLY DATA")
print("=" * 60)

df = pd.read_csv(INPUT_PATH)

print(f"Rows loaded: {len(df):,}")


# Convert timestamp to datetime.
df["observation_time_utc"] = pd.to_datetime(
    df["observation_time_utc"],
    utc=True,
)


# ---------------------------------------------------------
# AZURE SQL CONNECTION
# ---------------------------------------------------------

connection_string = (
    "DRIVER={ODBC Driver 18 for SQL Server};"
    f"SERVER={SERVER};"
    f"DATABASE={DATABASE};"
    f"UID={USERNAME};"
    f"PWD={PASSWORD};"
    "Encrypt=yes;"
    "TrustServerCertificate=no;"
    "Connection Timeout=30;"
)


print()
print("Connecting to Azure SQL...")

conn = pyodbc.connect(connection_string)

cursor = conn.cursor()

print("Connected successfully!")


# ---------------------------------------------------------
# INSERT DATA
# ---------------------------------------------------------

insert_sql = """
INSERT INTO dbo.silver_temperature_hourly (
    station_id,
    observation_time_utc,
    temperature_c,
    quality
)
VALUES (?, ?, ?, ?)
"""


print()
print("=" * 60)
print("INSERTING DATA")
print("=" * 60)

# Fast batch insertion.
# ---------------------------------------------------------
# INSERT DATA IN BATCHES
# ---------------------------------------------------------

cursor.fast_executemany = True

rows = list(
    df[
        [
            "station_id",
            "observation_time_utc",
            "temperature_c",
            "quality",
        ]
    ].itertuples(
        index=False,
        name=None,
    )
)

batch_size = 5000
total_rows = len(rows)

print(f"Total rows to insert: {total_rows:,}")
print(f"Batch size: {batch_size:,}")
print()

for start in range(0, total_rows, batch_size):

    end = min(
        start + batch_size,
        total_rows,
    )

    batch = rows[start:end]

    cursor.executemany(
        insert_sql,
        batch,
    )

    conn.commit()

    print(
        f"Inserted {end:,} / {total_rows:,}"
    )


# ---------------------------------------------------------
# CLOSE CONNECTION
# ---------------------------------------------------------

cursor.close()
conn.close()

print()
print("=" * 60)
print("UPLOAD COMPLETE")
print("=" * 60)