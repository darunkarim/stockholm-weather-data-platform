import requests
import pandas as pd

from io import StringIO
from pathlib import Path


# ---------------------------------------------------------
# SMHI CONFIGURATION
# ---------------------------------------------------------

STATION_ID = "98230"
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

    print(f"Station: {STATION_ID}")
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
    """
    Transform SMHI CSV data into our project schema.

    The SMHI CSV contains metadata before the actual
    measurement table, so we first locate the table header.
    """

    lines = data.splitlines()

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

    df = pd.read_csv(
        StringIO(csv_data),
        sep=";",
        encoding="utf-8",
    )

    print()
    print("SMHI CSV columns:")
    print(df.columns.tolist())

    # Keep only the columns we need.
    df = df[
        [
            "Från Datum Tid (UTC)",
            "Till Datum Tid (UTC)",
            "Representativt dygn",
            "Lufttemperatur",
            "Kvalitet",
        ]
    ]

    # Rename columns to our project naming convention.
    df = df.rename(
        columns={
            "Från Datum Tid (UTC)": "from_utc",
            "Till Datum Tid (UTC)": "to_utc",
            "Representativt dygn": "reference_date",
            "Lufttemperatur": "temperature_c",
            "Kvalitet": "quality",
        }
    )

    # Convert timestamps.
    df["from_utc"] = pd.to_datetime(
        df["from_utc"],
        utc=True,
    )

    df["to_utc"] = pd.to_datetime(
        df["to_utc"],
        utc=True,
    )

    # Convert reference date.
    df["reference_date"] = pd.to_datetime(
        df["reference_date"],
        errors="coerce",
    ).dt.date

    # Convert temperature to numeric.
    df["temperature_c"] = pd.to_numeric(
        df["temperature_c"],
        errors="coerce",
    )

    # Remove rows without a temperature.
    df = df.dropna(
        subset=["temperature_c"]
    )

    # Remove duplicate dates.
    df = df.drop_duplicates(
        subset=["reference_date"]
    )

    # Sort chronologically.
    df = df.sort_values(
        "reference_date"
    ).reset_index(drop=True)

    return df


# ---------------------------------------------------------
# VALIDATION
# ---------------------------------------------------------

def validate_data(df):

    print()
    print("=" * 60)
    print("DATA VALIDATION")
    print("=" * 60)

    print(f"Number of rows: {len(df)}")
    print(f"Start date: {df['reference_date'].min()}")
    print(f"End date: {df['reference_date'].max()}")

    missing_temperatures = df["temperature_c"].isna().sum()
    duplicate_dates = df["reference_date"].duplicated().sum()

    print(f"Missing temperatures: {missing_temperatures}")
    print(f"Duplicate dates: {duplicate_dates}")

    assert len(df) > 0, "Dataset is empty!"
    assert missing_temperatures == 0, "Missing temperatures found!"
    assert duplicate_dates == 0, "Duplicate dates found!"

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
    print(f"Rows saved: {len(df)}")


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