import pandas as pd
from pathlib import Path


# ---------------------------------------------------------
# PATHS
# ---------------------------------------------------------

# Find the project root folder.
PROJECT_ROOT = Path(__file__).resolve().parents[3]

# Input: our combined historical raw dataset.
INPUT_PATH = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "stockholm_temperature_hourly_historical.csv"
)

# Output: cleaned Silver dataset.
OUTPUT_PATH = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "stockholm_temperature_hourly_silver.csv"
)


# ---------------------------------------------------------
# LOAD DATA
# ---------------------------------------------------------

def load_data():
    """
    Load the combined historical temperature data.
    """

    print("=" * 60)
    print("LOADING RAW HOURLY DATA")
    print("=" * 60)

    df = pd.read_csv(INPUT_PATH)

    print(f"Rows loaded: {len(df):,}")

    return df


# ---------------------------------------------------------
# TRANSFORM DATA
# ---------------------------------------------------------

def transform_data(df):
    """
    Clean and transform the raw temperature observations
    into our Silver layer.
    """

    print()
    print("=" * 60)
    print("TRANSFORMING TO SILVER")
    print("=" * 60)

    # -----------------------------------------------------
    # Convert timestamp to a proper UTC datetime.
    # -----------------------------------------------------

    df["observation_time_utc"] = pd.to_datetime(
        df["observation_time_utc"],
        utc=True,
        errors="coerce",
    )

    # -----------------------------------------------------
    # Make sure temperature is numeric.
    # -----------------------------------------------------

    df["temperature_c"] = pd.to_numeric(
        df["temperature_c"],
        errors="coerce",
    )

    # -----------------------------------------------------
    # Remove rows where important values are missing.
    # -----------------------------------------------------

    df = df.dropna(
        subset=[
            "station_id",
            "observation_time_utc",
            "temperature_c",
        ]
    )

    # -----------------------------------------------------
    # Make station_id a string.
    # -----------------------------------------------------

    df["station_id"] = df["station_id"].astype(str)

    # -----------------------------------------------------
    # Clean quality values.
    # -----------------------------------------------------

    df["quality"] = df["quality"].astype(str).str.strip()

    # -----------------------------------------------------
    # Remove duplicate observations.
    #
    # A unique observation is identified by:
    # station + timestamp.
    # -----------------------------------------------------

    df = df.drop_duplicates(
        subset=[
            "station_id",
            "observation_time_utc",
        ]
    )

    # -----------------------------------------------------
    # Sort chronologically.
    # -----------------------------------------------------

    df = df.sort_values(
        "observation_time_utc"
    ).reset_index(drop=True)

    # -----------------------------------------------------
    # Keep only the columns needed in Silver.
    # -----------------------------------------------------

    df = df[
        [
            "station_id",
            "observation_time_utc",
            "temperature_c",
            "quality",
        ]
    ]

    return df


# ---------------------------------------------------------
# VALIDATION
# ---------------------------------------------------------

def validate_data(df):
    """
    Validate the Silver dataset before saving it.
    """

    print()
    print("=" * 60)
    print("SILVER VALIDATION")
    print("=" * 60)

    # -----------------------------------------------------
    # Check missing values.
    # -----------------------------------------------------

    print("\nMissing values:")
    print(df.isna().sum())

    # -----------------------------------------------------
    # Check duplicates.
    # -----------------------------------------------------

    duplicates = df.duplicated(
        subset=[
            "station_id",
            "observation_time_utc",
        ]
    ).sum()

    print(
        f"\nDuplicate station/timestamp rows: "
        f"{duplicates:,}"
    )

    if duplicates > 0:
        raise ValueError(
            "Duplicate observations found."
        )

    # -----------------------------------------------------
    # Check chronological order.
    # -----------------------------------------------------

    sorted_correctly = (
        df["observation_time_utc"]
        .is_monotonic_increasing
    )

    print(
        f"Sorted chronologically: "
        f"{sorted_correctly}"
    )

    if not sorted_correctly:
        raise ValueError(
            "Silver data is not sorted chronologically."
        )

    # -----------------------------------------------------
    # Check temperature range.
    # -----------------------------------------------------

    print(
        f"\nMinimum temperature: "
        f"{df['temperature_c'].min()} °C"
    )

    print(
        f"Maximum temperature: "
        f"{df['temperature_c'].max()} °C"
    )

    # -----------------------------------------------------
    # Show station counts.
    # -----------------------------------------------------

    print("\nRows by station:")
    print(df["station_id"].value_counts())

    print("\nValidation passed!")


# ---------------------------------------------------------
# MAIN
# ---------------------------------------------------------

def main():

    # 1. Load raw data.
    df = load_data()

    # 2. Transform data.
    df = transform_data(df)

    # 3. Validate Silver data.
    validate_data(df)

    # 4. Create output directory if necessary.
    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    # 5. Save Silver dataset.
    df.to_csv(
        OUTPUT_PATH,
        index=False,
    )

    print()
    print("=" * 60)
    print("SILVER DATA SAVED")
    print("=" * 60)

    print(f"Rows: {len(df):,}")

    print(
        f"First observation: "
        f"{df['observation_time_utc'].min()}"
    )

    print(
        f"Last observation: "
        f"{df['observation_time_utc'].max()}"
    )

    print("\nSaved to:")
    print(OUTPUT_PATH)


if __name__ == "__main__":
    main()