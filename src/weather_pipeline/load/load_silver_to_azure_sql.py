"""
Load Silver temperature data into Azure SQL.

This script reads the cleaned Silver CSV file and loads
the data into the silver_temperature table in Azure SQL.
"""

from pathlib import Path
import os

import pandas as pd
import pyodbc
from dotenv import load_dotenv


# Project root directory
PROJECT_ROOT = Path(__file__).resolve().parents[3]

# Silver input file
INPUT_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "stockholm_temperature_silver.csv"
)


# Load environment variables from .env
load_dotenv(
    PROJECT_ROOT
    / "src"
    / "weather_pipeline"
    / "ingestion"
    / ".env"
)


def load_silver_data() -> pd.DataFrame:
    """Read Silver data from CSV."""

    print("Loading Silver data...")

    df = pd.read_csv(INPUT_FILE)

    print(f"Loaded {len(df):,} rows.")

    return df


def create_connection():
    """Create connection to Azure SQL."""

    connection_string = os.getenv("AZURE_SQL_CONNECTION_STRING")

    if not connection_string:
        raise ValueError(
            "AZURE_SQL_CONNECTION_STRING was not found in .env"
        )

    return pyodbc.connect(connection_string)


def create_table(cursor) -> None:
    """Create Silver table if it does not already exist."""

    print("\nCreating Azure SQL table if needed...")

    cursor.execute("""
        IF OBJECT_ID('dbo.silver_temperature', 'U') IS NULL
        BEGIN
            CREATE TABLE dbo.silver_temperature (
                reference_date DATE NOT NULL,
                temperature_c FLOAT NOT NULL,
                quality VARCHAR(10)
            )
        END
    """)

    cursor.commit()

    print("Table ready!")


def load_data(cursor, df: pd.DataFrame) -> None:
    """Insert Silver data into Azure SQL."""

    print("\nLoading data into Azure SQL...")

    # Clear existing data so the table represents
    # the current Silver dataset.
    cursor.execute("DELETE FROM dbo.silver_temperature")

    insert_query = """
        INSERT INTO dbo.silver_temperature
        (
            reference_date,
            temperature_c,
            quality
        )
        VALUES (?, ?, ?)
    """

    rows = [
        (
            row.reference_date,
            row.temperature_c,
            row.quality
        )
        for row in df.itertuples(index=False)
    ]

    cursor.fast_executemany = True
    cursor.executemany(insert_query, rows)

    cursor.commit()

    print(f"Inserted {len(rows):,} rows.")


def verify_data(cursor) -> None:
    """Verify the number of rows loaded into Azure SQL."""

    cursor.execute(
        "SELECT COUNT(*) FROM dbo.silver_temperature"
    )

    count = cursor.fetchone()[0]

    print("\nAzure SQL validation:")
    print(f"Rows in silver_temperature: {count:,}")


def main() -> None:
    """Run the Azure SQL Silver loading pipeline."""

    print("=" * 60)
    print("LOAD SILVER DATA TO AZURE SQL")
    print("=" * 60)

    # Load Silver CSV
    df = load_silver_data()

    # Connect to Azure SQL
    print("\nConnecting to Azure SQL...")

    connection = create_connection()
    cursor = connection.cursor()

    print("Connected to Azure SQL!")

    # Create table
    create_table(cursor)

    # Load data
    load_data(cursor, df)

    # Verify
    verify_data(cursor)

    cursor.close()
    connection.close()

    print("\n" + "=" * 60)
    print("AZURE SQL LOAD COMPLETED")
    print("=" * 60)


if __name__ == "__main__":
    main()