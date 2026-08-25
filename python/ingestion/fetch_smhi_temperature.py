import requests
import pandas as pd
from pathlib import Path


# ---------------------------------------------------------
# Configuration
# ---------------------------------------------------------

STATION_ID = "98230"
PARAMETER_ID = "2"

BASE_URL = (
    f"https://opendata-download-metobs.smhi.se/api/version/latest/"
    f"parameter/{PARAMETER_ID}/station/{STATION_ID}/"
    f"period/latest-months/data.json"
)

OUTPUT_DIR = Path("data/raw")
OUTPUT_FILE = OUTPUT_DIR / "stockholm_temperature_recent.csv"


# ---------------------------------------------------------
# Fetch data
# ---------------------------------------------------------

def fetch_data():
    """Fetch weather observations from the SMHI API."""

    print("Fetching data from SMHI...")

    response = requests.get(BASE_URL, timeout=30)
    response.raise_for_status()

    return response.json()


# ---------------------------------------------------------
# Transform data
# ---------------------------------------------------------

def transform_data(data):
    """Transform SMHI API response into a pandas DataFrame."""

    observations = data.get("value", [])

    if not observations:
        raise ValueError("No observations were found in the SMHI response.")

    df = pd.DataFrame(observations)

    # Convert SMHI timestamps from milliseconds to datetime
    df["from"] = pd.to_datetime(df["from"], unit="ms")
    df["to"] = pd.to_datetime(df["to"], unit="ms")

    # Convert SMHI reference date to datetime
    df["ref"] = pd.to_datetime(df["ref"])

    # Convert measurement value from string to numeric
    df["value"] = pd.to_numeric(df["value"], errors="coerce")

    # Rename SMHI columns to clearer names
    df = df.rename(
        columns={
            "ref": "reference_date",
            "value": "temperature_c"
        }
    )

    # Add metadata
    df["station_id"] = STATION_ID
    df["parameter_id"] = PARAMETER_ID

    # Select and order relevant columns
    df = df[
        [
            "station_id",
            "parameter_id",
            "from",
            "to",
            "reference_date",
            "temperature_c",
            "quality"
        ]
    ]

    return df


# ---------------------------------------------------------
# Save data
# ---------------------------------------------------------

def save_data(df):
    """Save transformed data as CSV."""

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    df.to_csv(
        OUTPUT_FILE,
        index=False,
        encoding="utf-8"
    )

    print("\nData saved to:")
    print(OUTPUT_FILE)


# ---------------------------------------------------------
# Main
# ---------------------------------------------------------

def main():

    try:

        # Fetch data
        data = fetch_data()

        # Transform data
        df = transform_data(data)

        # Display results
        print("\nSuccessfully fetched weather data!")
        print(f"Number of observations: {len(df)}")

        print("\nFirst 5 observations:")
        print(df.head().to_string(index=False))

        print("\nData types:")
        print(df.dtypes)

        print("\nDate range:")
        print(f"From: {df['from'].min()}")
        print(f"To:   {df['to'].max()}")

        print("\nTemperature statistics:")
        print(df["temperature_c"].describe())

        # Save data
        save_data(df)

    except requests.exceptions.RequestException as error:

        print("\nSMHI API request failed:")
        print(error)

    except Exception as error:

        print("\nAn error occurred:")
        print(error)


if __name__ == "__main__":
    main()