import requests
import pandas as pd
from io import StringIO
from pathlib import Path


# ---------------------------------------------------------
# Configuration
# ---------------------------------------------------------

STATION_ID = "98230"
PARAMETER_ID = "2"

DATA_URL = (
    "https://opendata-download-metobs.smhi.se/api/version/1.0/"
    f"parameter/{PARAMETER_ID}/station/{STATION_ID}/"
    "period/corrected-archive/data.csv"
)

OUTPUT_DIR = Path("data/raw")
OUTPUT_FILE = OUTPUT_DIR / "stockholm_temperature_historical.csv"


# ---------------------------------------------------------
# Fetch data
# ---------------------------------------------------------

def fetch_data():
    """Download historical temperature data from SMHI."""

    print("Downloading historical temperature data from SMHI...")

    response = requests.get(
        DATA_URL,
        timeout=120
    )

    response.raise_for_status()

    print("Download completed.")

    return response.content.decode("utf-8-sig")


# ---------------------------------------------------------
# Find observation header
# ---------------------------------------------------------

def find_header_line(csv_text):
    """
    Find the line containing the actual weather observations.

    SMHI's CSV contains metadata before the observation table.
    """

    lines = csv_text.splitlines()

    for index, line in enumerate(lines):

        if line.startswith(
            "Från Datum Tid (UTC);"
        ):
            return index

    raise ValueError(
        "Could not find the observation header in the SMHI CSV."
    )


# ---------------------------------------------------------
# Transform data
# ---------------------------------------------------------

def transform_data(csv_text):
    """Extract and transform the weather observations."""

    header_line = find_header_line(csv_text)

    print(
        f"Observation header found on CSV line "
        f"{header_line + 1}."
    )

    # Only read the actual observation table
    observation_lines = csv_text.splitlines()[
        header_line:
    ]

    observation_text = "\n".join(
        observation_lines
    )

    df = pd.read_csv(
        StringIO(observation_text),
        sep=";",
        usecols=[
            "Från Datum Tid (UTC)",
            "Till Datum Tid (UTC)",
            "Representativt dygn",
            "Lufttemperatur",
            "Kvalitet"
        ]
    )

    # Rename columns to English / data-engineering-friendly names
    df = df.rename(
        columns={
            "Från Datum Tid (UTC)": "from_utc",
            "Till Datum Tid (UTC)": "to_utc",
            "Representativt dygn": "reference_date",
            "Lufttemperatur": "temperature_c",
            "Kvalitet": "quality"
        }
    )

    # Convert dates
    df["from_utc"] = pd.to_datetime(
        df["from_utc"],
        errors="coerce"
    )

    df["to_utc"] = pd.to_datetime(
        df["to_utc"],
        errors="coerce"
    )

    df["reference_date"] = pd.to_datetime(
        df["reference_date"],
        errors="coerce"
    )

    # Convert temperature to numeric
    df["temperature_c"] = pd.to_numeric(
        df["temperature_c"],
        errors="coerce"
    )

    # Add metadata
    df["station_id"] = STATION_ID
    df["parameter_id"] = PARAMETER_ID

    # Remove rows where the date is missing
    df = df.dropna(
        subset=["reference_date"]
    )

    # Reorder columns
    df = df[
        [
            "station_id",
            "parameter_id",
            "from_utc",
            "to_utc",
            "reference_date",
            "temperature_c",
            "quality"
        ]
    ]

    # Sort chronologically
    df = df.sort_values(
        "reference_date"
    ).reset_index(drop=True)

    return df


# ---------------------------------------------------------
# Data validation
# ---------------------------------------------------------

def validate_data(df):
    """Run basic data quality checks."""

    print("\n----------------------------------------")
    print("DATA QUALITY CHECKS")
    print("----------------------------------------")

    print(f"Rows: {len(df)}")

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

    print("\nQuality values:")

    print(
        df["quality"].value_counts(
            dropna=False
        )
    )


# ---------------------------------------------------------
# Save data
# ---------------------------------------------------------

def save_data(df):
    """Save historical temperature data."""

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    df.to_csv(
        OUTPUT_FILE,
        index=False,
        encoding="utf-8"
    )

    print("\n----------------------------------------")
    print("DATA SAVED")
    print("----------------------------------------")

    print(OUTPUT_FILE)


# ---------------------------------------------------------
# Main
# ---------------------------------------------------------

def main():

    try:

        # Download
        csv_text = fetch_data()

        # Transform
        df = transform_data(
            csv_text
        )

        print(
            "\nHistorical data successfully processed!"
        )

        # Show sample
        print("\nFirst 5 observations:")

        print(
            df.head().to_string(
                index=False
            )
        )

        # Validate
        validate_data(df)

        # Save
        save_data(df)

    except requests.exceptions.RequestException as error:

        print(
            "\nSMHI API request failed:"
        )

        print(error)

    except Exception as error:

        print(
            "\nAn error occurred:"
        )

        print(error)


if __name__ == "__main__":
    main()