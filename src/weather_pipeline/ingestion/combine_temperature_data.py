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

    # Combine historical and recent data.
    #
    # The recent dataset overlaps with the historical
    # dataset, so some observations exist in both files.
    combined = pd.concat(
        [historical, recent],
        ignore_index=True,
    )

    print(
        f"Rows before removing duplicates: "
        f"{len(combined):,}"
    )

    # Convert date/time columns to proper datetime values.
    combined["from_utc"] = pd.to_datetime(
        combined["from_utc"],
        utc=True,
    )

    combined["to_utc"] = pd.to_datetime(
        combined["to_utc"],
        utc=True,
    )

    combined["reference_date"] = pd.to_datetime(
        combined["reference_date"]
    ).dt.date

    # -----------------------------------------------------
    # REMOVE DUPLICATE OBSERVATIONS
    # -----------------------------------------------------
    #
    # We identify an observation using:
    #
    # station_id
    # parameter_id
    # from_utc
    # to_utc
    #
    # This is better than using only reference_date because
    # the same date could later contain multiple observations.
    #
    duplicate_columns = [
        "station_id",
        "parameter_id",
        "from_utc",
        "to_utc",
    ]

    duplicates_before = combined.duplicated(
        subset=duplicate_columns
    ).sum()

    print(
        f"Duplicate observations found: "
        f"{duplicates_before:,}"
    )

    combined = combined.drop_duplicates(
        subset=duplicate_columns,
        keep="last",
    )

    print(
        f"Rows after removing duplicates: "
        f"{len(combined):,}"
    )

    # Sort chronologically.
    combined = combined.sort_values(
        [
            "station_id",
            "parameter_id",
            "reference_date",
            "from_utc",
        ]
    ).reset_index(drop=True)

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

    duplicate_observations = df.duplicated(
        subset=[
            "station_id",
            "parameter_id",
            "from_utc",
            "to_utc",
        ]
    ).sum()

    missing_station_ids = df["station_id"].isna().sum()

    missing_parameter_ids = df["parameter_id"].isna().sum()

    print(f"Number of rows:             {len(df):,}")
    print(f"Start date:                 {start_date}")
    print(f"End date:                   {end_date}")
    print(f"Missing temperatures:       {missing_temperatures}")
    print(f"Missing station IDs:        {missing_station_ids}")
    print(f"Missing parameter IDs:      {missing_parameter_ids}")
    print(
        f"Duplicate observations:    "
        f"{duplicate_observations}"
    )

    print()
    print("Stations:")
    print(
        df[
            ["station_id", "station_name"]
        ].drop_duplicates().to_string(index=False)
    )

    print()
    print("Parameters:")
    print(
        df[
            ["parameter_id"]
        ].drop_duplicates().to_string(index=False)
    )

    # -----------------------------------------------------
    # ASSERTIONS
    # -----------------------------------------------------

    assert len(df) > 0, "Dataset is empty!"

    assert (
        missing_temperatures == 0
    ), "Missing temperatures found!"

    assert (
        missing_station_ids == 0
    ), "Missing station IDs found!"

    assert (
        missing_parameter_ids == 0
    ), "Missing parameter IDs found!"

    assert (
        duplicate_observations == 0
    ), "Duplicate observations found!"

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