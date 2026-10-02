import os
from pathlib import Path

import pandas as pd
import pyodbc
from dotenv import load_dotenv

from src.weather_pipeline.ingestion.latest_weather import fetch_latest_weather


# ============================================================
# PROJECT ROOT
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[3]


# ============================================================
# ENVIRONMENT VARIABLES
# ============================================================

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

TABLE_NAME = "latest_weather"


# ============================================================
# LOAD FUNCTION
# ============================================================

def load_latest_weather(weather_df=None):
    """
    Load the latest weather observations into Azure SQL.

    If no DataFrame is supplied, the latest observations
    are fetched directly from SMHI.
    """

    print("=" * 70)
    print("LOAD LATEST WEATHER TO AZURE SQL")
    print("=" * 70)

    # --------------------------------------------------------
    # FETCH DATA
    # --------------------------------------------------------

    if weather_df is None:
        print("\nFetching latest weather from SMHI...")
        weather_df = fetch_latest_weather()
    else:
        print("\nUsing supplied weather DataFrame...")

    print(f"Observations received: {len(weather_df)}")

    # Work with a copy so the original DataFrame is not modified.
    weather_df = weather_df.copy()

    # --------------------------------------------------------
    # PREPARE DATA TYPES
    # --------------------------------------------------------

    print("\nPreparing data types...")

    weather_df["observation_time"] = pd.to_datetime(
        weather_df["observation_time"],
        errors="coerce",
        utc=True
    )

    weather_df["reference_date"] = pd.to_datetime(
        weather_df["reference_date"],
        errors="coerce"
    )

    # --------------------------------------------------------
    # SQL CONNECTION
    # --------------------------------------------------------

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

    try:

        # ----------------------------------------------------
        # CREATE TABLE
        # ----------------------------------------------------

        print("\nCreating latest_weather table if it does not exist...")

        create_table_sql = f"""
        IF OBJECT_ID('{TABLE_NAME}', 'U') IS NULL
        BEGIN

            CREATE TABLE {TABLE_NAME} (

                parameter NVARCHAR(50) NOT NULL,

                parameter_id INT,

                station_id INT,

                station_name NVARCHAR(100),

                value FLOAT,

                unit NVARCHAR(20),

                observation_time DATETIME2,

                reference_date DATE,

                quality NVARCHAR(10),

                loaded_at DATETIME2 NOT NULL
                    DEFAULT SYSUTCDATETIME(),

                CONSTRAINT PK_{TABLE_NAME}
                    PRIMARY KEY (parameter)

            )

        END
        """

        cursor.execute(create_table_sql)
        conn.commit()

        print("Table ready.")

        # ----------------------------------------------------
        # CLEAR OLD DATA
        # ----------------------------------------------------

        print("\nClearing previous latest weather observations...")

        cursor.execute(
            f"DELETE FROM {TABLE_NAME}"
        )

        conn.commit()

        print("Previous observations removed.")

        # ----------------------------------------------------
        # INSERT SQL
        # ----------------------------------------------------

        insert_sql = f"""
        INSERT INTO {TABLE_NAME} (
            parameter,
            parameter_id,
            station_id,
            station_name,
            value,
            unit,
            observation_time,
            reference_date,
            quality
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """

        # ----------------------------------------------------
        # CONVERT TO PYTHON TYPES
        # ----------------------------------------------------

        rows = []

        for _, row in weather_df.iterrows():

            parameter = (
                None
                if pd.isna(row["parameter"])
                else str(row["parameter"])
            )

            parameter_id = (
                None
                if pd.isna(row["parameter_id"])
                else int(row["parameter_id"])
            )

            station_id = (
                None
                if pd.isna(row["station_id"])
                else int(row["station_id"])
            )

            station_name = (
                None
                if pd.isna(row["station_name"])
                else str(row["station_name"])
            )

            value = (
                None
                if pd.isna(row["value"])
                else float(row["value"])
            )

            unit = (
                None
                if pd.isna(row["unit"])
                else str(row["unit"])
            )

            observation_time = (
                None
                if pd.isna(row["observation_time"])
                else row["observation_time"]
                .to_pydatetime()
                .replace(tzinfo=None)
            )

            reference_date = (
                None
                if pd.isna(row["reference_date"])
                else row["reference_date"].date()
            )

            quality = (
                None
                if pd.isna(row["quality"])
                else str(row["quality"])
            )

            sql_row = (
                parameter,
                parameter_id,
                station_id,
                station_name,
                value,
                unit,
                observation_time,
                reference_date,
                quality,
            )

            rows.append(sql_row)

        print(f"\nRows prepared for SQL: {len(rows)}")

        # ----------------------------------------------------
        # INSERT DATA
        # ----------------------------------------------------

        print("\nInserting latest weather data...")

        cursor.executemany(
            insert_sql,
            rows
        )

        conn.commit()

        print(f"Rows inserted: {len(rows)}")

        # ----------------------------------------------------
        # VERIFY
        # ----------------------------------------------------

        print("\nVerifying Azure SQL data...")

        cursor.execute(
            f"""
            SELECT
                parameter,
                value,
                unit,
                station_name,
                observation_time,
                reference_date,
                quality,
                loaded_at
            FROM {TABLE_NAME}
            ORDER BY parameter
            """
        )

        results = cursor.fetchall()

        print()

        for result in results:
            print(
                f"{result.parameter}: "
                f"{result.value} {result.unit} | "
                f"{result.station_name} | "
                f"{result.observation_time}"
            )

        # ----------------------------------------------------
        # VALIDATION
        # ----------------------------------------------------

        cursor.execute(
            f"SELECT COUNT(*) FROM {TABLE_NAME}"
        )

        row_count = cursor.fetchone()[0]

        print("\n" + "=" * 70)
        print("LATEST WEATHER SQL LOAD COMPLETED")
        print("=" * 70)

        if row_count == len(weather_df):

            print("\nVALIDATION PASSED")
            print(
                f"Azure SQL contains all "
                f"{row_count} latest weather observations."
            )

        else:

            raise ValueError(
                f"Validation failed. "
                f"Expected {len(weather_df)} rows, "
                f"but Azure SQL contains {row_count}."
            )

        return row_count

    except Exception:
        conn.rollback()
        raise

    finally:
        cursor.close()
        conn.close()


# ============================================================
# RUN DIRECTLY
# ============================================================

if __name__ == "__main__":
    load_latest_weather()