"""
Silver layer for Stockholm temperature data.

This script reads raw temperature data from the Bronze layer,
cleans and validates the data, and saves the result as a
Silver dataset.
"""

from pathlib import Path

import pandas as pd


# Project root directory
PROJECT_ROOT = Path(__file__).resolve().parents[3]

# Input: Bronze / Raw data
INPUT_FILE = PROJECT_ROOT / "data" / "raw" / "stockholm_temperature_complete.csv"

# Output: Silver data
OUTPUT_FILE = PROJECT_ROOT / "data" / "processed" / "stockholm_temperature_silver.csv"


def load_raw_data() -> pd.DataFrame:
    """Load raw temperature data from CSV."""

    print("Loading raw temperature data...")

    df = pd.read_csv(INPUT_FILE)

    print(f"Loaded {len(df):,} rows.")

    return df


def clean_temperature_data(df: pd.DataFrame) -> pd.DataFrame:
    """Clean and standardize the temperature data."""

    print("\nCleaning temperature data...")

    # Standardize column names
    df.columns = (
        df.columns
        .str.strip()
        .str.lower()
        .str.replace(" ", "_")
    )

    # Convert temperature to numeric
    df["temperature_c"] = pd.to_numeric(
        df["temperature_c"],
        errors="coerce"
    )

    # Convert dates to datetime
    df["from_utc"] = pd.to_datetime(
        df["from_utc"],
        errors="coerce",
        utc=True
    )

    df["to_utc"] = pd.to_datetime(
        df["to_utc"],
        errors="coerce",
        utc=True
    )

    # Remove rows where important values are missing
    df = df.dropna(
        subset=[
            "from_utc",
            "to_utc",
            "temperature_c"
        ]
    )

    # Remove duplicate measurements
    df = df.drop_duplicates()

    # Sort chronologically
    df = df.sort_values("from_utc")

    # Reset index after cleaning
    df = df.reset_index(drop=True)

    return df


def validate_silver_data(df: pd.DataFrame) -> None:
    """Run basic quality checks on the Silver dataset."""

    print("\nValidating Silver data...")

    # Check that the dataframe is not empty
    if df.empty:
        raise ValueError("Silver dataset is empty.")

    # Check for missing important values
    if df["temperature_c"].isna().any():
        raise ValueError("Temperature contains null values.")

    if df["from_utc"].isna().any():
        raise ValueError("from_utc contains null values.")

    # Check for duplicate rows
    if df.duplicated().any():
        raise ValueError("Silver dataset contains duplicate rows.")

    print("Validation passed!")


def save_silver_data(df: pd.DataFrame) -> None:
    """Save cleaned data to the Silver layer."""

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    df.to_csv(
        OUTPUT_FILE,
        index=False
    )

    print(f"\nSilver data saved to:")
    print(OUTPUT_FILE)


def main() -> None:
    """Run the Silver transformation pipeline."""

    print("=" * 60)
    print("STOCKHOLM WEATHER - SILVER TRANSFORMATION")
    print("=" * 60)

    # 1. Load Bronze data
    df = load_raw_data()

    # 2. Clean and transform
    df = clean_temperature_data(df)

    # 3. Validate Silver data
    validate_silver_data(df)

    # 4. Save Silver data
    save_silver_data(df)

    print("\n" + "=" * 60)
    print("SILVER TRANSFORMATION COMPLETED")
    print("=" * 60)


if __name__ == "__main__":
    main()