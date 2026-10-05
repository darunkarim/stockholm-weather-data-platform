"""
Gold layer for Stockholm temperature data.

This script reads the cleaned Silver temperature data,
adds analytical dimensions such as year, month and season,
and saves the result as a Gold dataset.

Gold data is intended to be easier to use for analytics
and visualization in tools such as Power BI.
"""

from pathlib import Path

import pandas as pd


# Project root directory
PROJECT_ROOT = Path(__file__).resolve().parents[3]

# Input: Silver layer
INPUT_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "stockholm_temperature_silver.csv"
)

# Output: Gold layer
OUTPUT_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "gold_temperature_daily.csv"
)


def load_silver_data() -> pd.DataFrame:
    """Load cleaned temperature data from the Silver layer."""

    print("Loading Silver temperature data...")

    df = pd.read_csv(INPUT_FILE)

    print(f"Loaded {len(df):,} rows.")

    return df


def transform_to_gold(df: pd.DataFrame) -> pd.DataFrame:
    """
    Transform Silver data into an analytics-friendly Gold dataset.
    """

    print("\nTransforming Silver data into Gold...")

    # Convert reference_date to datetime
    df["reference_date"] = pd.to_datetime(
        df["reference_date"],
        errors="coerce"
    )

    # Create year
    df["year"] = df["reference_date"].dt.year

    # Create month number
    df["month"] = df["reference_date"].dt.month

    # Create month name
    month_names = {
        1: "January",
        2: "February",
        3: "March",
        4: "April",
        5: "May",
        6: "June",
        7: "July",
        8: "August",
        9: "September",
        10: "October",
        11: "November",
        12: "December",
    }

    df["month_name"] = df["month"].map(month_names)

    # Create season based on month
    season_mapping = {
        12: "Winter",
        1: "Winter",
        2: "Winter",
        3: "Spring",
        4: "Spring",
        5: "Spring",
        6: "Summer",
        7: "Summer",
        8: "Summer",
        9: "Autumn",
        10: "Autumn",
        11: "Autumn",
    }

    df["season"] = df["month"].map(season_mapping)

    # Select the columns that are useful for analytics
    df = df[
        [
            "reference_date",
            "year",
            "month",
            "month_name",
            "season",
            "temperature_c",
            "quality",
        ]
    ]

    # Sort by date
    df = df.sort_values("reference_date")

    # Reset index after transformation
    df = df.reset_index(drop=True)

    return df


def validate_gold_data(df: pd.DataFrame) -> None:
    """Run basic quality checks on the Gold dataset."""

    print("\nValidating Gold data...")

    # Make sure the dataset is not empty
    if df.empty:
        raise ValueError("Gold dataset is empty.")

    # Check important columns for missing values
    required_columns = [
        "reference_date",
        "year",
        "month",
        "month_name",
        "season",
        "temperature_c",
    ]

    for column in required_columns:
        if df[column].isna().any():
            raise ValueError(
                f"Column '{column}' contains null values."
            )

    # Check that month values are valid
    if not df["month"].between(1, 12).all():
        raise ValueError("Invalid month value found.")

    # Check that temperature is numeric
    if not pd.api.types.is_numeric_dtype(df["temperature_c"]):
        raise ValueError("temperature_c is not numeric.")

    print("Validation passed!")


def save_gold_data(df: pd.DataFrame) -> None:
    """Save the Gold dataset to CSV."""

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    df.to_csv(
        OUTPUT_FILE,
        index=False
    )

    print("\nGold data saved to:")
    print(OUTPUT_FILE)


def main() -> None:
    """Run the Gold transformation pipeline."""

    print("=" * 60)
    print("STOCKHOLM WEATHER - GOLD TRANSFORMATION")
    print("=" * 60)

    # 1. Load Silver data
    df = load_silver_data()

    # 2. Transform Silver into Gold
    df = transform_to_gold(df)

    # 3. Validate Gold data
    validate_gold_data(df)

    # 4. Save Gold data
    save_gold_data(df)

    print("\n" + "=" * 60)
    print("GOLD TRANSFORMATION COMPLETED")
    print("=" * 60)


if __name__ == "__main__":
    main()