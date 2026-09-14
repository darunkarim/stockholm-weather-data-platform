"""
Historical SMHI temperature ingestion.

This script downloads historical daily temperature observations
for Stockholm-Observatoriekullen A (station 98230).

Data source:
SMHI Open Data

Period:
1996-10-01 -> current available historical data

Parameter:
2 = Air temperature, daily mean
"""

import requests
import pandas as pd
from pathlib import Path


# ---------------------------------------------------------
# SMHI configuration
# ---------------------------------------------------------

STATION_ID = "98230"
PARAMETER_ID = "2"

BASE_URL = (
    "https://opendata-download-metobs.smhi.se/"
    "api/version/latest/"
    f"parameter/{PARAMETER_ID}/"
    f"station/{STATION_ID}/"
    "period/corrected-archive/data.csv"
)


# ---------------------------------------------------------
# Local output
# ---------------------------------------------------------

OUTPUT_DIR = Path("data/raw")
OUTPUT_FILE = OUTPUT_DIR / "stockholm_temperature_historical.csv"


# ---------------------------------------------------------
# Download data from SMHI
# ---------------------------------------------------------


def fetch_historical_temperature():
    print("=" * 60)
    print("SMHI HISTORICAL TEMPERATURE DOWNLOAD")
    print("=" * 60)

    print(f"Station: {STATION_ID}")
    print(f"Parameter: {PARAMETER_ID}")
    print("Downloading historical data...")

    response = requests.get(BASE_URL, timeout=120)

    # Stop if SMHI returns an error
    response.raise_for_status()

    print("Download successful!")

    return response.text




# ---------------------------------------------------------
# Convert SMHI response to DataFrame
# ---------------------------------------------------------


def transform_data(data):
    """
    Transform SMHI historical CSV data into our project schema.

    The SMHI CSV contains Swedish column names and metadata.
    We convert them into simple English column names that
    we can use consistently throughout the data pipeline.
    """

    from io import StringIO

    lines = data.splitlines()

    # Find the actual measurement table header.
    header_index = None

    for i, line in enumerate(lines):
        if "Datum" in line and "Tid" in line:
            header_index = i
            break

    if header_index is None:
        raise ValueError(
            "Could not find the measurement header in the SMHI CSV."
        )

    # Remove the metadata before the actual measurement table.
    csv_data = "\n".join(lines[header_index:])

    df = pd.read_csv(
        StringIO(csv_data),
        sep=";",
        encoding="utf-8",
    )

    # Keep only the columns we actually need.
    df = df[
        [
            "Från Datum Tid (UTC)",
            "Till Datum Tid (UTC)",
            "Representativt dygn",
            "Lufttemperatur",
            "Kvalitet",
        ]
    ]

    # Rename SMHI columns to our project naming convention.
    df = df.rename(
        columns={
            "Från Datum Tid (UTC)": "from_utc",
            "Till Datum Tid (UTC)": "to_utc",
            "Representativt dygn": "reference_date",
            "Lufttemperatur": "temperature_c",
            "Kvalitet": "quality",
        }
    )

    # Convert timestamps to datetime.
    df["from_utc"] = pd.to_datetime(
        df["from_utc"],
        utc=True,
    )

    df["to_utc"] = pd.to_datetime(
        df["to_utc"],
        utc=True,
    )

    # Convert reference date to date.
    df["reference_date"] = pd.to_datetime(
        df["reference_date"],
        errors="coerce",
    ).dt.date

    # Convert temperature to numeric.
    df["temperature_c"] = pd.to_numeric(
        df["temperature_c"],
        errors="coerce",
    )

    # Remove rows where temperature is missing.
    df = df.dropna(
        subset=["temperature_c"]
    )

    # Sort chronologically.
    df = df.sort_values(
        "reference_date"
    ).reset_index(drop=True)

    print()
    print("Transformed columns:")
    print(df.columns.tolist())

    print()
    print("Number of valid rows:", len(df))

    print()
    print("Date range:")
    print(f"Start: {df['reference_date'].min()}")
    print(f"End:   {df['reference_date'].max()}")

    print()
    print("First rows:")
    print(df.head())

    return df







# ---------------------------------------------------------
# Validate historical data
# ---------------------------------------------------------

def validate_data(df):
    print()
    print("=" * 60)
    print("DATA VALIDATION")
    print("=" * 60)

    print(f"Number of rows: {len(df):,}")
    print(f"Start date: {df['from_utc'].min()}")
    print(f"End date: {df['from_utc'].max()}")
    print(f"Missing temperatures: {df['temperature_c'].isna().sum()}")
    print(f"Duplicate rows: {df.duplicated().sum()}")

    # Basic validation checks
    assert len(df) > 0, "No data returned from SMHI."

    assert (
        df["temperature_c"].isna().sum() == 0
    ), "Missing temperature values found."

    assert (
        df.duplicated().sum() == 0
    ), "Duplicate rows found."

    print()
    print("Validation passed!")


# ---------------------------------------------------------
# Save data locally
# ---------------------------------------------------------

def save_data(df):
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    df.to_csv(
        OUTPUT_FILE,
        index=False,
    )

    print()
    print("=" * 60)
    print("FILE SAVED")
    print("=" * 60)

    print(f"Saved to: {OUTPUT_FILE}")
    print(f"Rows saved: {len(df):,}")


# ---------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------

def main():
    data = fetch_historical_temperature()

    df = transform_data(data)

    validate_data(df)

    save_data(df)


if __name__ == "__main__":
    main()