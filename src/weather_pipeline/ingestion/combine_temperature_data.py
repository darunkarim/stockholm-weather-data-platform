import pandas as pd

from pathlib import Path


# ---------------------------------------------------------
# FILE PATHS
# ---------------------------------------------------------

HISTORICAL_FILE = Path(
    "data/raw/stockholm_temperature_historical.csv"
)

RECENT_FILE = Path(
    "data/raw/stockholm_temperature_recent.csv"
)

OUTPUT_FILE = Path(
    "data/raw/stockholm_temperature_complete.csv"
)


# ---------------------------------------------------------
# LOAD DATA
# ---------------------------------------------------------

def load_data():

    print("=" * 60)
    print("LOADING TEMPERATURE DATA")
    print("=" * 60)

    historical = pd.read_csv(
        HISTORICAL_FILE
    )

    recent = pd.read_csv(
        RECENT_FILE
    )

    print(f"Historical rows: {len(historical):,}")
    print(f"Recent rows:     {len(recent):,}")

    return historical, recent


# ---------------------------------------------------------
# COMBINE DATA
# ---------------------------------------------------------

def combine_data(historical, recent):

    print()
    print("=" * 60)
    print("COMBINING DATA")
    print("=" * 60)

    # Combine the two datasets.
    combined = pd.concat(
        [historical, recent],
        ignore_index=True,
    )

    print(f"Rows before removing duplicates: {len(combined):,}")

    # Convert reference_date to a proper date.
    combined["reference_date"] = pd.to_datetime(
        combined["reference_date"]
    ).dt.date

    # Remove duplicate days.
    #
    # The recent dataset overlaps with the historical
    # dataset, so some dates occur in both files.
    combined = combined.drop_duplicates(
        subset=["reference_date"],
        keep="last",
    )

    # Sort chronologically.
    combined = combined.sort_values(
        "reference_date"
    ).reset_index(drop=True)

    print(
        f"Rows after removing duplicates:  {len(combined):,}"
    )

    return combined


# ---------------------------------------------------------
# VALIDATION
# ---------------------------------------------------------

def validate_data(df):

    print()
    print("=" * 60)
    print("COMPLETE DATA VALIDATION")
    print("=" * 60)

    start_date = df["reference_date"].min()
    end_date = df["reference_date"].max()

    missing_temperatures = (
        df["temperature_c"].isna().sum()
    )

    duplicate_dates = (
        df["reference_date"].duplicated().sum()
    )

    print(f"Number of rows:       {len(df):,}")
    print(f"Start date:           {start_date}")
    print(f"End date:             {end_date}")
    print(f"Missing temperatures: {missing_temperatures}")
    print(f"Duplicate dates:      {duplicate_dates}")

    assert len(df) > 0, "Dataset is empty!"

    assert (
        missing_temperatures == 0
    ), "Missing temperatures found!"

    assert (
        duplicate_dates == 0
    ), "Duplicate dates found!"

    print()
    print("Validation passed!")


# ---------------------------------------------------------
# SAVE DATA
# ---------------------------------------------------------

def save_data(df):

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    df.to_csv(
        OUTPUT_FILE,
        index=False,
    )

    print()
    print("=" * 60)
    print("COMPLETE DATASET SAVED")
    print("=" * 60)

    print(f"Saved to: {OUTPUT_FILE}")
    print(f"Rows saved: {len(df):,}")


# ---------------------------------------------------------
# MAIN
# ---------------------------------------------------------

def main():

    historical, recent = load_data()

    combined = combine_data(
        historical,
        recent,
    )

    print()
    print("First rows:")
    print(combined.head())

    print()
    print("Last rows:")
    print(combined.tail())

    validate_data(combined)

    save_data(combined)


if __name__ == "__main__":
    main()