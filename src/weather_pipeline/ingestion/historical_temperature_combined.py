import pandas as pd
import requests
from io import StringIO
from pathlib import Path


# ---------------------------------------------------------
# SETTINGS
# ---------------------------------------------------------

# SMHI stations
STATION_98210 = "98210"
STATION_98230 = "98230"

# Parameter 1 = Air temperature, observation values
PARAMETER_ID = "1"

# Datum då vi byter från den gamla stationen till den nya.
# 98210 används före detta datum.
# 98230 används från och med detta datum.
SWITCH_DATE = pd.Timestamp("1996-10-01", tz="UTC")


# ---------------------------------------------------------
# PATHS
# ---------------------------------------------------------

# Find the project root folder.
PROJECT_ROOT = Path(__file__).resolve().parents[3]

# Where the combined historical raw data will be saved.
OUTPUT_PATH = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "stockholm_temperature_hourly_historical.csv"
)


# ---------------------------------------------------------
# SMHI API
# ---------------------------------------------------------

def build_url(station_id):
    """
    Build the SMHI API URL for a specific station.
    """

    return (
        "https://opendata-download-metobs.smhi.se/"
        "api/version/latest/"
        f"parameter/{PARAMETER_ID}/"
        f"station/{station_id}/"
        "period/corrected-archive/data.csv"
    )


# ---------------------------------------------------------
# DOWNLOAD DATA
# ---------------------------------------------------------

def fetch_station_data(station_id):
    """
    Download temperature observations from SMHI
    and convert them into a clean DataFrame.
    """

    url = build_url(station_id)

    print("=" * 60)
    print(f"Downloading station {station_id}")
    print("=" * 60)

    response = requests.get(url, timeout=60)
    response.raise_for_status()

    # SMHI's CSV contains metadata before the actual table.
    # We therefore find the row where the real table starts.
    lines = response.text.splitlines()

    header_index = None

    for i, line in enumerate(lines):
        if line.startswith("Datum;"):
            header_index = i
            break

    if header_index is None:
        raise ValueError(
            f"Could not find the data header for station {station_id}."
        )

    # Keep only the actual CSV table.
    csv_data = "\n".join(lines[header_index:])

    df = pd.read_csv(
        StringIO(csv_data),
        sep=";",
        decimal=",",
    )

    print(f"Rows downloaded: {len(df):,}")

    # -----------------------------------------------------
    # Select the columns we actually need.
    # -----------------------------------------------------

    df = df[
        [
            "Datum",
            "Tid (UTC)",
            "Lufttemperatur",
            "Kvalitet",
        ]
    ]

    # -----------------------------------------------------
    # Rename columns to English names used in our pipeline.
    # -----------------------------------------------------

    df = df.rename(
        columns={
            "Datum": "date",
            "Tid (UTC)": "time_utc",
            "Lufttemperatur": "temperature_c",
            "Kvalitet": "quality",
        }
    )

    # -----------------------------------------------------
    # Create one UTC timestamp.
    # -----------------------------------------------------

    df["observation_time_utc"] = pd.to_datetime(
        df["date"].astype(str)
        + " "
        + df["time_utc"].astype(str),
        utc=True,
        errors="coerce",
    )

    # Convert temperature to a number.
    df["temperature_c"] = pd.to_numeric(
        df["temperature_c"],
        errors="coerce",
    )

    # Remove rows where timestamp or temperature is missing.
    df = df.dropna(
        subset=[
            "observation_time_utc",
            "temperature_c",
        ]
    )

    # Add the station ID so we know where every observation came from.
    df["station_id"] = station_id

    # Keep only the columns we want in the raw dataset.
    df = df[
        [
            "station_id",
            "observation_time_utc",
            "temperature_c",
            "quality",
        ]
    ]

    # Sort chronologically.
    df = df.sort_values(
        "observation_time_utc"
    ).reset_index(drop=True)

    print(f"Clean rows: {len(df):,}")
    print(
        f"First observation: "
        f"{df['observation_time_utc'].min()}"
    )
    print(
        f"Last observation: "
        f"{df['observation_time_utc'].max()}"
    )

    return df


# ---------------------------------------------------------
# VALIDATION
# ---------------------------------------------------------

def validate_data(df):
    """
    Perform basic quality checks on the combined dataset.
    """

    print()
    print("=" * 60)
    print("VALIDATION")
    print("=" * 60)

    # Check for missing values.
    print("\nMissing values:")
    print(df.isna().sum())

    # Check for duplicate observations within each station.
    duplicates = df.duplicated(
        subset=[
            "station_id",
            "observation_time_utc",
        ]
    ).sum()

    print(f"\nDuplicate station/timestamp rows: {duplicates:,}")

    if duplicates > 0:
        raise ValueError(
            "Duplicate observations were found."
        )

    # Check that the data is sorted.
    is_sorted = df["observation_time_utc"].is_monotonic_increasing

    print(f"Sorted chronologically: {is_sorted}")

    if not is_sorted:
        raise ValueError(
            "Data is not sorted chronologically."
        )

    # Check station ranges.
    print("\nStation ranges:")

    for station_id in [STATION_98210, STATION_98230]:

        station_df = df[
            df["station_id"] == station_id
        ]

        if len(station_df) == 0:
            print(f"{station_id}: NO DATA")
            continue

        print(
            f"{station_id}: "
            f"{station_df['observation_time_utc'].min()} "
            f"→ "
            f"{station_df['observation_time_utc'].max()} "
            f"({len(station_df):,} rows)"
        )

    # Make sure the station switch is correct.
    old_station = df[
        df["station_id"] == STATION_98210
    ]

    new_station = df[
        df["station_id"] == STATION_98230
    ]

    if len(old_station) > 0:
        if old_station["observation_time_utc"].max() >= SWITCH_DATE:
            raise ValueError(
                "Station 98210 contains observations "
                "on or after the switch date."
            )

    if len(new_station) > 0:
        if new_station["observation_time_utc"].min() < SWITCH_DATE:
            raise ValueError(
                "Station 98230 contains observations "
                "before the switch date."
            )

    print("\nValidation passed!")


# ---------------------------------------------------------
# MAIN PIPELINE
# ---------------------------------------------------------

def main():

    # -----------------------------------------------------
    # 1. Download station 98210
    # -----------------------------------------------------

    df_98210 = fetch_station_data(STATION_98210)

    # Keep 98210 only before 1996-10-01.
    df_98210 = df_98210[
        df_98210["observation_time_utc"] < SWITCH_DATE
    ].copy()

    print(
        f"\n98210 rows after date filter: "
        f"{len(df_98210):,}"
    )

    # -----------------------------------------------------
    # 2. Download station 98230
    # -----------------------------------------------------

    df_98230 = fetch_station_data(STATION_98230)

    # Keep 98230 from 1996-10-01 onwards.
    df_98230 = df_98230[
        df_98230["observation_time_utc"] >= SWITCH_DATE
    ].copy()

    print(
        f"98230 rows after date filter: "
        f"{len(df_98230):,}"
    )

    # -----------------------------------------------------
    # 3. Combine the two stations
    # -----------------------------------------------------

    df = pd.concat(
        [
            df_98210,
            df_98230,
        ],
        ignore_index=True,
    )

    # Sort everything chronologically.
    df = df.sort_values(
        "observation_time_utc"
    ).reset_index(drop=True)

    # -----------------------------------------------------
    # 4. Validate
    # -----------------------------------------------------

    validate_data(df)

    # -----------------------------------------------------
    # 5. Save
    # -----------------------------------------------------

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    df.to_csv(
        OUTPUT_PATH,
        index=False,
    )

    print()
    print("=" * 60)
    print("COMBINED HISTORICAL DATA")
    print("=" * 60)

    print(f"Total rows: {len(df):,}")
    print(
        f"First observation: "
        f"{df['observation_time_utc'].min()}"
    )
    print(
        f"Last observation: "
        f"{df['observation_time_utc'].max()}"
    )

    print("\nRows by station:")
    print(df["station_id"].value_counts())

    print("\nSaved to:")
    print(OUTPUT_PATH)


if __name__ == "__main__":
    main()