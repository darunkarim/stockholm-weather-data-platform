import pandas as pd
from pathlib import Path


# ---------------------------------------------------------
# Configuration
# ---------------------------------------------------------

RAW_DIR = Path("data/raw")
PROCESSED_DIR = Path("data/processed")

HISTORICAL_FILE = (
    RAW_DIR / "stockholm_temperature_historical.csv"
)

LATEST_FILE = (
    RAW_DIR / "stockholm_temperature_latest_month.csv"
)

OUTPUT_FILE = (
    PROCESSED_DIR / "stockholm_temperature.csv"
)


# ---------------------------------------------------------
# Load data
# ---------------------------------------------------------

def load_data():

    print("Loading historical data...")

    historical = pd.read_csv(
        HISTORICAL_FILE
    )

    print(
        f"Historical rows: {len(historical)}"
    )

    print("\nLoading latest data...")

    latest = pd.read_csv(
        LATEST_FILE
    )

    print(
        f"Latest rows: {len(latest)}"
    )

    return historical, latest


# ---------------------------------------------------------
# Combine
# ---------------------------------------------------------

def combine_data(
    historical,
    latest
):

    print("\nCombining datasets...")

    combined = pd.concat(
        [
            historical,
            latest
        ],
        ignore_index=True
    )

    return combined


# ---------------------------------------------------------
# Clean
# ---------------------------------------------------------

def clean_data(df):

    print("\nCleaning data...")

    # Convert date
    df["reference_date"] = pd.to_datetime(
        df["reference_date"],
        errors="coerce"
    )

    # Convert temperature
    df["temperature_c"] = pd.to_numeric(
        df["temperature_c"],
        errors="coerce"
    )

    # Remove rows without dates
    df = df.dropna(
        subset=["reference_date"]
    )

    # Remove duplicate dates
    df = df.drop_duplicates(
        subset=["reference_date"],
        keep="last"
    )

    # Sort chronologically
    df = df.sort_values(
        "reference_date"
    )

    # Reset index
    df = df.reset_index(
        drop=True
    )

    return df


# ---------------------------------------------------------
# Validation
# ---------------------------------------------------------

def validate_data(df):

    print("\n----------------------------------------")
    print("COMBINED DATA QUALITY CHECKS")
    print("----------------------------------------")

    print(
        f"Total rows: {len(df)}"
    )

    print(
        f"Missing temperatures: "
        f"{df['temperature_c'].isna().sum()}"
    )

    print(
        f"Duplicate dates: "
        f"{df['reference_date'].duplicated().sum()}"
    )

    print(
        f"Start date: "
        f"{df['reference_date'].min().date()}"
    )

    print(
        f"End date: "
        f"{df['reference_date'].max().date()}"
    )

    print("\nTemperature statistics:")

    print(
        df["temperature_c"].describe()
    )


# ---------------------------------------------------------
# Save
# ---------------------------------------------------------

def save_data(df):

    PROCESSED_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    df.to_csv(
        OUTPUT_FILE,
        index=False,
        encoding="utf-8"
    )

    print("\n----------------------------------------")
    print("PROCESSED DATA SAVED")
    print("----------------------------------------")

    print(OUTPUT_FILE)


# ---------------------------------------------------------
# Main
# ---------------------------------------------------------

def main():

    try:

        historical, latest = load_data()

        combined = combine_data(
            historical,
            latest
        )

        combined = clean_data(
            combined
        )

        validate_data(
            combined
        )

        save_data(
            combined
        )

    except Exception as error:

        print("\nAn error occurred:")
        print(error)


if __name__ == "__main__":
    main()