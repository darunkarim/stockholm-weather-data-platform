"""
Load Gold daily weather data into Azure SQL.

This script:
1. Loads the Gold CSV file.
2. Converts pandas/NumPy values to native Python types.
3. Connects to Azure SQL.
4. Creates the gold_daily_weather table if it does not exist.
5. Clears existing Gold data.
6. Inserts the complete Gold dataset.
7. Verifies the loaded data.
"""

import os
from pathlib import Path

import pandas as pd
import pyodbc
from dotenv import load_dotenv


# ============================================================
# PROJECT PATHS
# ============================================================

# Find the project root.
#
# Current file:
# src/weather_pipeline/load/load_gold_to_azure_sql.py
#
# parents[0] = load
# parents[1] = weather_pipeline
# parents[2] = src
# parents[3] = project root
PROJECT_ROOT = Path(__file__).resolve().parents[3]

GOLD_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "gold_daily_weather.csv"
)


# ============================================================
# ENVIRONMENT VARIABLES
# ============================================================

# The .env file is located here:
#
# src/weather_pipeline/ingestion/.env
#
load_dotenv(
    PROJECT_ROOT
    / "src"
    / "weather_pipeline"
    / "ingestion"
    / ".env"
)


SQL_SERVER = os.getenv("AZURE_SQL_SERVER")
SQL_DATABASE = os.getenv("AZURE_SQL_DATABASE")
SQL_USERNAME = os.getenv("AZURE_SQL_USERNAME")
SQL_PASSWORD = os.getenv("AZURE_SQL_PASSWORD")


if not all(
    [
        SQL_SERVER,
        SQL_DATABASE,
        SQL_USERNAME,
        SQL_PASSWORD,
    ]
):
    raise ValueError(
        "Missing Azure SQL environment variables in .env"
    )


# ============================================================
# SETTINGS
# ============================================================

TABLE_NAME = "gold_daily_weather"


# ============================================================
# START
# ============================================================

print("=" * 70)
print("LOAD GOLD DATA TO AZURE SQL")
print("=" * 70)


# ============================================================
# LOAD GOLD DATASET
# ============================================================

print("\nLoading Gold dataset...")

gold_df = pd.read_csv(GOLD_FILE)

print(f"Rows loaded: {len(gold_df):,}")


# ============================================================
# PREPARE DATA TYPES
# ============================================================

print("\nPreparing data types...")


# Convert date to pandas datetime.
gold_df["date"] = pd.to_datetime(
    gold_df["date"],
    errors="coerce"
)


# Integer columns
integer_columns = [
    "year",
    "month",
    "day",
    "wind_observation_count",
    "temperature_station_id",
    "precipitation_station_id",
    "wind_station_id",
]

for column in integer_columns:

    gold_df[column] = pd.to_numeric(
        gold_df[column],
        errors="coerce"
    )


# Float columns
float_columns = [
    "temperature_c",
    "precipitation_mm",
    "avg_wind_speed_mps",
    "min_wind_speed_mps",
    "max_wind_speed_mps",
]
for column in float_columns:

    gold_df[column] = pd.to_numeric(
        gold_df[column],
        errors="coerce"
    )


# String columns
string_columns = [
    "month_name",
    "season",
    "temperature_quality",
    "precipitation_quality",
]

for column in string_columns:

    gold_df[column] = gold_df[column].astype("string")


# ============================================================
# SQL CONNECTION
# ============================================================

print("\nConnecting to Azure SQL...")


connection_string = (
    "DRIVER={ODBC Driver 18 for SQL Server};"
    f"SERVER={SQL_SERVER};"
    f"DATABASE={SQL_DATABASE};"
    f"UID={SQL_USERNAME};"
    f"PWD={SQL_PASSWORD};"
    "Encrypt=yes;"
    "TrustServerCertificate=no;"
    "Connection Timeout=30;"
)


conn = pyodbc.connect(connection_string)

cursor = conn.cursor()

print("Connected to Azure SQL!")


# ============================================================
# CREATE TABLE
# ============================================================

print("\nCreating Azure SQL table if it does not exist...")


create_table_sql = f"""
IF OBJECT_ID('{TABLE_NAME}', 'U') IS NULL
BEGIN

    CREATE TABLE {TABLE_NAME} (

        date DATE NOT NULL,

        year INT,

        month INT,

        month_name NVARCHAR(20),

        day INT,

        season NVARCHAR(20),

        temperature_c FLOAT,

        precipitation_mm FLOAT,

        avg_wind_speed_mps FLOAT,

        min_wind_speed_mps FLOAT,

        max_wind_speed_mps FLOAT,

        wind_observation_count INT,

        temperature_station_id INT,

        precipitation_station_id INT,

        wind_station_id INT,

        temperature_quality NVARCHAR(10),

        precipitation_quality NVARCHAR(10),

        CONSTRAINT PK_{TABLE_NAME}
            PRIMARY KEY (date)

    )

END
"""


cursor.execute(create_table_sql)

# Add wind columns if the Gold table already existed
# before wind was introduced.

alter_table_sql = f"""
IF COL_LENGTH('{TABLE_NAME}', 'avg_wind_speed_mps') IS NULL
    ALTER TABLE {TABLE_NAME}
    ADD avg_wind_speed_mps FLOAT;

IF COL_LENGTH('{TABLE_NAME}', 'min_wind_speed_mps') IS NULL
    ALTER TABLE {TABLE_NAME}
    ADD min_wind_speed_mps FLOAT;

IF COL_LENGTH('{TABLE_NAME}', 'max_wind_speed_mps') IS NULL
    ALTER TABLE {TABLE_NAME}
    ADD max_wind_speed_mps FLOAT;

IF COL_LENGTH('{TABLE_NAME}', 'wind_observation_count') IS NULL
    ALTER TABLE {TABLE_NAME}
    ADD wind_observation_count INT;

IF COL_LENGTH('{TABLE_NAME}', 'wind_station_id') IS NULL
    ALTER TABLE {TABLE_NAME}
    ADD wind_station_id INT;
"""

cursor.execute(alter_table_sql)

conn.commit()

print("Table ready.")


# ============================================================
# CLEAR EXISTING DATA
# ============================================================

print("\nClearing existing Gold data...")


cursor.execute(
    f"DELETE FROM {TABLE_NAME}"
)

conn.commit()

print("Existing Gold data removed.")


# ============================================================
# INSERT SQL
# ============================================================

print("\nInserting Gold data...")


insert_sql = f"""
INSERT INTO {TABLE_NAME} (
    date,
    year,
    month,
    month_name,
    day,
    season,
    temperature_c,
    precipitation_mm,
    avg_wind_speed_mps,
    min_wind_speed_mps,
    max_wind_speed_mps,
    wind_observation_count,
    temperature_station_id,
    precipitation_station_id,
    wind_station_id,
    temperature_quality,
    precipitation_quality
)
VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
"""


# ============================================================
# CONVERT DATAFRAME TO NATIVE PYTHON TYPES
# ============================================================

# We deliberately convert every value to a normal Python type.
#
# pandas and NumPy use special types such as:
#
#   numpy.int64
#   numpy.float64
#   pd.NA
#   pandas.Timestamp
#
# pyodbc works more reliably with native Python types:
#
#   int
#   float
#   str
#   datetime.date
#   None
#
# This conversion prevents errors such as:
#
#   Unknown object type: NAType
#   Unknown object type numpy.int64
#


rows = []


for _, row in gold_df.iterrows():

    # --------------------------------------------------------
    # DATE
    # --------------------------------------------------------

    if pd.isna(row["date"]):
        date_value = None
    else:
        date_value = row["date"].date()


    # --------------------------------------------------------
    # INTEGER VALUES
    # --------------------------------------------------------

    def to_int(value):

        if pd.isna(value):
            return None

        return int(value)


    # --------------------------------------------------------
    # FLOAT VALUES
    # --------------------------------------------------------

    def to_float(value):

        if pd.isna(value):
            return None

        return float(value)


    # --------------------------------------------------------
    # STRING VALUES
    # --------------------------------------------------------

    def to_string(value):

        if pd.isna(value):
            return None

        return str(value)


    # --------------------------------------------------------
    # CREATE ONE SQL ROW
    # --------------------------------------------------------

    sql_row = (

    date_value,

    to_int(row["year"]),

    to_int(row["month"]),

    to_string(row["month_name"]),

    to_int(row["day"]),

    to_string(row["season"]),

    to_float(row["temperature_c"]),

    to_float(row["precipitation_mm"]),

    to_float(row["avg_wind_speed_mps"]),

    to_float(row["min_wind_speed_mps"]),

    to_float(row["max_wind_speed_mps"]),

    to_int(row["wind_observation_count"]),

    to_int(row["temperature_station_id"]),

    to_int(row["precipitation_station_id"]),

    to_int(row["wind_station_id"]),

    to_string(row["temperature_quality"]),

    to_string(row["precipitation_quality"]),
)


    rows.append(sql_row)


print(f"Rows prepared for SQL: {len(rows):,}")


# ============================================================
# INSERT DATA
# ============================================================

# fast_executemany speeds up large batch inserts.
cursor.fast_executemany = True


cursor.executemany(
    insert_sql,
    rows
)

conn.commit()


print(f"Rows inserted: {len(rows):,}")


# ============================================================
# VERIFY DATA
# ============================================================

print("\nVerifying Azure SQL data...")


cursor.execute(
    f"""
    SELECT
        COUNT(*) AS row_count,
        MIN(date) AS min_date,
        MAX(date) AS max_date,
        COUNT(avg_wind_speed_mps) AS wind_row_count
    FROM {TABLE_NAME}
    """
)


result = cursor.fetchone()

row_count = result[0]
min_date = result[1]
max_date = result[2]
wind_row_count = result[3]


print(f"Rows in Azure SQL: {row_count:,}")
print(f"Minimum date:      {min_date}")
print(f"Maximum date:      {max_date}")
print(f"Wind rows:         {wind_row_count:,}")

# ============================================================
# CLOSE CONNECTION
# ============================================================

cursor.close()
conn.close()


# ============================================================
# FINAL VALIDATION
# ============================================================

print("\n" + "=" * 70)
print("AZURE SQL LOAD COMPLETED")
print("=" * 70)


if row_count == len(gold_df):

    print("\nVALIDATION PASSED")

    print(
        f"Azure SQL contains all {row_count:,} Gold rows."
    )

else:

    print("\nVALIDATION FAILED")

    print(
        f"Expected: {len(gold_df):,}"
    )

    print(
        f"Actual:   {row_count:,}"
    )


print("\nGold table:")
print(f"    {TABLE_NAME}")

print("\nDate range:")
print(f"    {min_date} → {max_date}")

print("\nDone!")