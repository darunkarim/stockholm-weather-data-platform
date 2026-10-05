from pathlib import Path
import os

import pandas as pd
import pyodbc
from dotenv import load_dotenv


# ---------------------------------------------------------
# Configuration
# ---------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[3]

INPUT_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "stockholm_precipitation_silver.csv"
)

# The .env file is located in the ingestion folder.
ENV_FILE = (
    PROJECT_ROOT
    / "src"
    / "weather_pipeline"
    / "ingestion"
    / ".env"
)

load_dotenv(ENV_FILE)


# ---------------------------------------------------------
# Load data
# ---------------------------------------------------------

print("=" * 60)
print("LOAD PRECIPITATION TO AZURE SQL")
print("=" * 60)

print()
print("Loading Silver data...")

data = pd.read_csv(INPUT_FILE)

print(f"Rows loaded: {len(data):,}")


# ---------------------------------------------------------
# Convert data types
# ---------------------------------------------------------

data["station_id"] = data["station_id"].astype(str)

data["from_utc"] = pd.to_datetime(
    data["from_utc"],
    errors="coerce"
)

data["to_utc"] = pd.to_datetime(
    data["to_utc"],
    errors="coerce"
)

data["reference_date"] = pd.to_datetime(
    data["reference_date"],
    errors="coerce"
).dt.date

data["precipitation_mm"] = pd.to_numeric(
    data["precipitation_mm"],
    errors="coerce"
)


# ---------------------------------------------------------
# Azure SQL connection
# ---------------------------------------------------------

server = os.getenv("AZURE_SQL_SERVER")
database = os.getenv("AZURE_SQL_DATABASE")
username = os.getenv("AZURE_SQL_USERNAME")
password = os.getenv("AZURE_SQL_PASSWORD")

connection_string = (
    "DRIVER={ODBC Driver 18 for SQL Server};"
    f"SERVER={server};"
    f"DATABASE={database};"
    f"UID={username};"
    f"PWD={password};"
    "Encrypt=yes;"
    "TrustServerCertificate=no;"
    "Connection Timeout=30;"
)


# ---------------------------------------------------------
# Connect to Azure SQL
# ---------------------------------------------------------

print()
print("Connecting to Azure SQL...")

conn = pyodbc.connect(connection_string)

cursor = conn.cursor()

print("Connected to Azure SQL!")


# ---------------------------------------------------------
# Insert data
# ---------------------------------------------------------

insert_sql = """
INSERT INTO dbo.silver_precipitation (
    station_id,
    from_utc,
    to_utc,
    reference_date,
    precipitation_mm,
    quality
)
VALUES (?, ?, ?, ?, ?, ?)
"""

# Insert rows in batches.
batch_size = 5000

cursor.fast_executemany = True

total_rows = len(data)

print()
print("Uploading data...")

for start in range(0, total_rows, batch_size):

    end = min(
        start + batch_size,
        total_rows
    )

    batch = data.iloc[start:end]

    rows = list(
        batch[
            [
                "station_id",
                "from_utc",
                "to_utc",
                "reference_date",
                "precipitation_mm",
                "quality"
            ]
        ].itertuples(
            index=False,
            name=None
        )
    )

    cursor.executemany(
        insert_sql,
        rows
    )

    conn.commit()

    print(
        f"Uploaded {end:,} / {total_rows:,} rows"
    )


# ---------------------------------------------------------
# Close connection
# ---------------------------------------------------------

cursor.close()
conn.close()

print()
print("Upload completed successfully!")

print("=" * 60)