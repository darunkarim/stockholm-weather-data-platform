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
    / "stockholm_wind_silver.csv"
)

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
print("LOAD WIND TO AZURE SQL")
print("=" * 60)

print()
print("Loading Silver wind data...")

data = pd.read_csv(INPUT_FILE)

print(f"Rows loaded: {len(data):,}")

if data.empty:
    raise ValueError(
        "Wind Silver dataset is empty. "
        "Azure SQL load aborted."
    )


# ---------------------------------------------------------
# Convert data types
# ---------------------------------------------------------

data["station_id"] = data["station_id"].astype(str)

data["observation_time_utc"] = pd.to_datetime(
    data["observation_time_utc"],
    errors="coerce",
    utc=True
)

data["observation_date"] = pd.to_datetime(
    data["observation_date"],
    errors="coerce"
).dt.date

data["wind_speed_mps"] = pd.to_numeric(
    data["wind_speed_mps"],
    errors="coerce"
)

data["year"] = pd.to_numeric(
    data["year"],
    errors="coerce"
)

data["month"] = pd.to_numeric(
    data["month"],
    errors="coerce"
)

data["day"] = pd.to_numeric(
    data["day"],
    errors="coerce"
)

data["hour"] = pd.to_numeric(
    data["hour"],
    errors="coerce"
)


# ---------------------------------------------------------
# Validate before upload
# ---------------------------------------------------------

required_columns = [
    "station_id",
    "observation_time_utc",
    "wind_speed_mps",
    "quality",
    "observation_date",
    "year",
    "month",
    "day",
    "hour"
]

missing_columns = [
    column
    for column in required_columns
    if column not in data.columns
]

if missing_columns:
    raise ValueError(
        f"Missing required columns: {missing_columns}"
    )

if data[required_columns].isna().any().any():
    raise ValueError(
        "Missing values detected in required wind columns."
    )

duplicate_count = data.duplicated(
    subset=[
        "station_id",
        "observation_time_utc"
    ]
).sum()

if duplicate_count > 0:
    raise ValueError(
        f"Duplicate wind observations detected: {duplicate_count}"
    )

print("Pre-load validation passed!")


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
# Create Silver wind table
# ---------------------------------------------------------

print()
print("Creating Silver wind table if it does not exist...")

create_table_sql = """
IF OBJECT_ID('dbo.silver_wind', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.silver_wind (
        station_id VARCHAR(20) NOT NULL,
        observation_time_utc DATETIME2 NOT NULL,
        wind_speed_mps FLOAT NOT NULL,
        quality VARCHAR(10) NOT NULL,
        observation_date DATE NOT NULL,
        year INT NOT NULL,
        month INT NOT NULL,
        day INT NOT NULL,
        hour INT NOT NULL
    );
END
"""

cursor.execute(create_table_sql)
conn.commit()

print("Table ready.")


# ---------------------------------------------------------
# Clear existing data
# ---------------------------------------------------------

print()
print("Clearing existing wind data...")

cursor.execute(
    "DELETE FROM dbo.silver_wind"
)

conn.commit()

print("Existing wind data removed.")


# ---------------------------------------------------------
# Insert data
# ---------------------------------------------------------

insert_sql = """
INSERT INTO dbo.silver_wind (
    station_id,
    observation_time_utc,
    wind_speed_mps,
    quality,
    observation_date,
    year,
    month,
    day,
    hour
)
VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
"""

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
                "observation_time_utc",
                "wind_speed_mps",
                "quality",
                "observation_date",
                "year",
                "month",
                "day",
                "hour"
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
# Verify Azure SQL data
# ---------------------------------------------------------

print()
print("Verifying Azure SQL data...")

cursor.execute(
    """
    SELECT
        COUNT(*),
        MIN(observation_time_utc),
        MAX(observation_time_utc)
    FROM dbo.silver_wind
    """
)

sql_count, min_date, max_date = cursor.fetchone()

print(f"Rows in Azure SQL: {sql_count:,}")
print(f"First observation: {min_date}")
print(f"Last observation:  {max_date}")

if sql_count != total_rows:
    raise ValueError(
        f"Row count mismatch. "
        f"CSV: {total_rows:,}, "
        f"Azure SQL: {sql_count:,}"
    )

print()
print("VALIDATION PASSED")
print("Azure SQL contains all Silver wind rows.")


# ---------------------------------------------------------
# Close connection
# ---------------------------------------------------------

cursor.close()
conn.close()

print()
print("Upload completed successfully!")

print("=" * 60)