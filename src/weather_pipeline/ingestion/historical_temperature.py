"""
Historical SMHI temperature ingestion.

Downloads historical daily temperature observations
for a selected SMHI station.

Parameter:
2 = Air temperature, daily mean
"""

import sys
import requests
import pandas as pd
from pathlib import Path
from io import StringIO


# ---------------------------------------------------------
# SMHI configuration
# ---------------------------------------------------------

PARAMETER_ID = "2"

# Known Stockholm-area stations.
STATIONS = {
    "98210": "Stockholm-Observatoriekullen",
    "98230": "Stockholm-Observatoriekullen A",
    "97200": "Stockholm-Bromma Flygplats",
    "97400": "Stockholm-Arlanda Flygplats",
}


# ---------------------------------------------------------
# Local output
# ---------------------------------------------------------

OUTPUT_DIR = Path("data/raw")


# ---------------------------------------------------------
# Get station from command line
# ---------------------------------------------------------

def get_station_id():

    # We expect the station ID after the script name.
    #
    # Example:
    # python .../historical_temperature.py 98210

    if len(sys.argv) < 2:

        print()
        print("ERROR: No station ID supplied.")
        print()
        print("Available stations:")

        for station_id, station_name in STATIONS.items():
            print(f"  {station_id} - {station_name}")

        print()
        print("Example:")
        print(
            "python "
            "src/weather_pipeline/ingestion/"
            "historical_temperature.py 98210"
        )

        sys.exit(1)

    station_id = sys.argv[1]

    if station_id not in STATIONS:

        raise ValueError(
            f"Unknown station ID: {station_id}\n"
            f"Available stations: {list(STATIONS.keys())}"
        )

    return station_id


# ---------------------------------------------------------
# Download data from SMHI
# ---------------------------------------------------------

def fetch_historical_temperature(
    station_id,
):

    station_name = STATIONS[station_id]

    base_url = (
        "https://opendata-download-metobs.smhi.se/"
        "api/version/latest/"
        f"parameter/{PARAMETER_ID}/"
        f"station/{station_id}/"
        "period/corrected-archive/data.csv"
    )

    print("=" * 60)
    print("SMHI HISTORICAL TEMPERATURE DOWNLOAD")
    print("=" * 60)

    print(f"Station: {station_id} - {station_name}")
    print(f"Parameter: {PARAMETER_ID}")
    print("Downloading historical data...")

    response = requests.get(
        base_url,
        timeout=120,
    )

    response.raise_for_status()

    print("Download successful!")

    return response.text


# ---------------------------------------------------------
# Convert SMHI response to DataFrame
# ---------------------------------------------------------

def transform_data(
    data,
    station_id,
):

    station_name = STATIONS[station_id]

    lines = data.splitlines()

    # Find the actual measurement table header.
    header_index = None

    for i, line in enumerate(lines):

        if "Datum" in line and "Tid" in line:

            header_index = i
            break

    if header_index is None:

        raise ValueError(
            "Could not find the measurement header "
            "in the SMHI CSV."
        )

    # Remove metadata before the measurement table.
    csv_data = "\n".join(
        lines[header_index:]
    )

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
            f"Could not find required SMHI columns: "
            f"{missing_columns}"
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
    # Add source metadata
    # -----------------------------------------------------

    df["station_id"] = station_id
    df["station_name"] = station_name
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

    # Remove rows without a temperature value.
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
    print(f"Number of valid rows: {len(df):,}")

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
# Validate historical data
# ---------------------------------------------------------

def validate_data(df):

    print()
    print("=" * 60)
    print("DATA VALIDATION")
    print("=" * 60)

    print(f"Number of rows: {len(df):,}")
    print(f"Start date: {df['from_utc'].min()}")
    print(f"End date: {df['to_utc'].max()}")
    print(
        f"Missing temperatures: "
        f"{df['temperature_c'].isna().sum()}"
    )
    print(
        f"Duplicate rows: "
        f"{df.duplicated().sum()}"
    )

    assert len(df) > 0, (
        "No data returned from SMHI."
    )

    assert (
        df["temperature_c"].isna().sum() == 0
    ), "Missing temperature values found."

    assert (
        df.duplicated().sum() == 0
    ), "Duplicate rows found."

    assert (
        df["station_id"].notna().all()
    ), "Missing station_id found."

    assert (
        df["parameter_id"].notna().all()
    ), "Missing parameter_id found."

    print()
    print("Validation passed!")


# ---------------------------------------------------------
# Save data locally
# ---------------------------------------------------------

def save_data(
    df,
    station_id,
):

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    output_file = (
        OUTPUT_DIR
        / f"stockholm_temperature_{station_id}_historical.csv"
    )

    df.to_csv(
        output_file,
        index=False,
    )

    print()
    print("=" * 60)
    print("FILE SAVED")
    print("=" * 60)

    print(f"Saved to: {output_file}")
    print(f"Rows saved: {len(df):,}")


# ---------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------

def main():

    station_id = get_station_id()

    data = fetch_historical_temperature(
        station_id
    )

    df = transform_data(
        data,
        station_id,
    )

    validate_data(df)

    save_data(
        df,
        station_id,
    )


if __name__ == "__main__":
    main()