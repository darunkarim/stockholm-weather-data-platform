import requests
import pandas as pd

from io import StringIO
from pathlib import Path


# ---------------------------------------------------------
# SMHI CONFIGURATION
# ---------------------------------------------------------

STATION_ID = "98230"
STATION_NAME = "Stockholm-Observatoriekullen A"
PARAMETER_ID = "2"

BASE_URL = (
    "https://opendata-download-metobs.smhi.se/"
    "api/version/latest/"
    f"parameter/{PARAMETER_ID}/"
    f"station/{STATION_ID}/"
    "period/latest-months/data.csv"
)

OUTPUT_DIR = Path("data/raw")
OUTPUT_FILE = OUTPUT_DIR / "stockholm_temperature_recent.csv"


# ---------------------------------------------------------
# FETCH DATA
# ---------------------------------------------------------

def fetch_recent_temperature():
    print("=" * 60)
    print("SMHI RECENT TEMPERATURE DOWNLOAD")
    print("=" * 60)

    print(f"Station: {STATION_ID} - {STATION_NAME}")
    print(f"Parameter: {PARAMETER_ID}")
    print("Downloading recent data...")

    response = requests.get(
        BASE_URL,
        timeout=120,
    )

    response.raise_for_status()

    print("Download successful!")

    return response.text


# ---------------------------------------------------------
# TRANSFORM DATA
# ---------------------------------------------------------

def transform_data(data):

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

    # Remove metadata before the actual measurement table.
    csv_data = "\n".join(lines[header_index:])

    # Read the SMHI CSV.
    df = pd.read_csv(
        StringIO(csv_data),
        sep=";",
        encoding="utf-8-sig",
    )

    print()
    print("SMHI CSV columns:")
    print(df.columns.tolist())

    # -----------------------------------------------------
    # Find SMHI columns dynamically
    # -----------------------------------------------------

    from_column = next(
        (
            column
            for column in df.columns
            if "Fr" in column
            and "Datum" in column
            and "UTC" in column
        ),
        None,
    )

    to_column = next(
        (
            column
            for column in df.columns
            if "Till" in column
            and "Datum" in column
            and "UTC" in column
        ),
        None,
    )

    reference_column = next(
        (
            column
            for column in df.columns
            if "Representativt dygn" in column
        ),
        None,
    )

    temperature_column = next(
        (
            column
            for column in df.columns
            if "Lufttemperatur" in column
        ),
        None,
    )

    quality_column = next(
        (
            column
            for column in df.columns
            if "Kvalitet" in column
        ),
        None,
    )

    required_columns = {
        "from": from_column,
        "to": to_column,
        "reference_date": reference_column,
        "temperature": temperature_column,
        "quality": quality_column,
    }

    missing_columns = [
        name
        for name, column in required_columns.items()
        if column is None
    ]

    if missing_columns:
        raise ValueError(
            f"Could not find required SMHI columns: {missing_columns}"
        )

    # -----------------------------------------------------
    # Select and rename columns
    # -----------------------------------------------------

    df = df[
        [
            from_column,
            to_column,
            reference_column,
            temperature_column,
            quality_column,
        ]
    ]

    df = df.rename(
        columns={
            from_column: "from_utc",
            to_column: "to_utc",
            reference_column: "reference_date",
            temperature_column: "temperature_c",
            quality_column: "quality",
        }
    )

    # -----------------------------------------------------
    # Add station metadata
    # -----------------------------------------------------

    df["station_id"] = STATION_ID
    df["station_name"] = STATION_NAME
    df["parameter_id"] = PARAMETER_ID

    # -----------------------------------------------------
    # Convert data types
    # -----------------------------------------------------

    df["from_utc"] = pd.to_datetime(
        df["from_utc"],
        utc=True,
    )

    df["to_utc"] = pd.to_datetime(
        df["to_utc"],
        utc=True,
    )

    df["reference_date"] = pd.to_datetime(
        df["reference_date"],
        errors="coerce",
    ).dt.date

    df["temperature_c"] = pd.to_numeric(
        df["temperature_c"],
        errors="coerce",
    )

    # Remove rows without temperature.
    df = df.dropna(
        subset=["temperature_c"]
    )

    # -----------------------------------------------------
    # Final column order
    # -----------------------------------------------------

    df = df[
        [
            "station_id",
            "station_name",
            "parameter_id",
            "from_utc",
            "to_utc",
            "reference_date",
            "temperature_c",
            "quality",
        ]
    ]

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
    print("Station:")
    print(df["station_id"].iloc[0])
    print(df["station_name"].iloc[0])

    return df


# ---------------------------------------------------------
# VALIDATION
# ---------------------------------------------------------

def validate_data(df):

    print()
    print("=" * 60)
    print("DATA VALIDATION")
    print("=" * 60)

    print(f"Number of rows: {len(df):,}")
    print(f"Start date: {df['reference_date'].min()}")
    print(f"End date: {df['reference_date'].max()}")

    missing_temperatures = df["temperature_c"].isna().sum()
    duplicate_rows = df.duplicated().sum()

    print(f"Missing temperatures: {missing_temperatures}")
    print(f"Duplicate rows: {duplicate_rows}")

    assert len(df) > 0, "Dataset is empty!"
    assert missing_temperatures == 0, "Missing temperatures found!"
    assert duplicate_rows == 0, "Duplicate rows found!"

    assert df["station_id"].notna().all(), \
        "Missing station_id found!"

    assert df["parameter_id"].notna().all(), \
        "Missing parameter_id found!"

    print()
    print("Validation passed!")


# ---------------------------------------------------------
# SAVE DATA
# ---------------------------------------------------------

def save_data(df):

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

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
# MAIN
# ---------------------------------------------------------

def main():

    data = fetch_recent_temperature()

    df = transform_data(data)

    print()
    print("First rows:")
    print(df.head())

    validate_data(df)

    save_data(df)


if __name__ == "__main__":
    main()