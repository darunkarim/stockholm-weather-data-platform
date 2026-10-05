from pathlib import Path

import pandas as pd
import requests


# ---------------------------------------------------------
# Configuration
# ---------------------------------------------------------

PARAMETER_ID = 4

OLD_STATION_ID = 98210
NEW_STATION_ID = 98230



PROJECT_ROOT = Path(__file__).resolve().parents[3]

OUTPUT_FILE = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "stockholm_wind_speed_historical_combined.csv"
)


# ---------------------------------------------------------
# Download function
# ---------------------------------------------------------

def download_station_data(station_id):
    """
    Download corrected historical wind-speed data
    for one SMHI station.
    """

    url = (
        f"https://opendata-download-metobs.smhi.se/"
        f"api/version/latest/parameter/{PARAMETER_ID}/"
        f"station/{station_id}/period/corrected-archive/data.csv"
    )

    print()
    print(f"Downloading station {station_id}...")

    response = requests.get(
        url,
        timeout=120
    )

    response.raise_for_status()

    print("Download successful!")

    lines = response.text.splitlines()

    # TEMPORARY DEBUG:
    # Show the first 30 lines exactly as SMHI returns them.
    

    data_rows = []

    for line in lines:

        parts = line.split(";")

        # We need at least:
        # Date;Time;Wind speed;Quality
        if len(parts) < 4:
            continue

        date = parts[0].strip()
        time = parts[1].strip()
        wind_speed = parts[2].strip()
        quality = parts[3].strip()

        # Check that the first column is actually a date.
        parsed_date = pd.to_datetime(
    date,
    format="%Y-%m-%d",
    errors="coerce"
)

        if pd.isna(parsed_date):
            continue

        # Check that the second column looks like a time.
        parsed_time = pd.to_datetime(
            time,
            format="%H:%M:%S",
            errors="coerce"
        )

        if pd.isna(parsed_time):
            continue

        # Check that wind speed is numeric.
        parsed_wind_speed = pd.to_numeric(
            wind_speed,
            errors="coerce"
        )

        if pd.isna(parsed_wind_speed):
            continue

        data_rows.append(
            [
                date,
                time,
                wind_speed,
                quality
            ]
        )

    data = pd.DataFrame(
        data_rows,
        columns=[
            "date",
            "time_utc",
            "wind_speed_mps",
            "quality"
        ]
    )

    data["station_id"] = str(station_id)

    return data


# ---------------------------------------------------------
# Clean function
# ---------------------------------------------------------

def clean_station_data(data):
    """
    Clean and validate downloaded SMHI wind data.
    """

    # Combine date and time into one UTC timestamp.
    data["observation_time_utc"] = pd.to_datetime(
        data["date"] + " " + data["time_utc"],
        errors="coerce",
        utc=True
    )

    data["wind_speed_mps"] = pd.to_numeric(
        data["wind_speed_mps"],
        errors="coerce"
    )

    # Remove invalid rows.
    data = data.dropna(
        subset=[
            "observation_time_utc",
            "wind_speed_mps"
        ]
    )

    # Keep valid SMHI quality codes.
    data = data[
        data["quality"].isin(
            ["G", "Y"]
        )
    ]

    # Wind speed cannot be negative.
    data = data[
        data["wind_speed_mps"] >= 0
    ]

    # Remove duplicate observations.
    data = data.drop_duplicates(
        subset=[
            "station_id",
            "observation_time_utc"
        ]
    )

    # Sort chronologically.
    data = data.sort_values(
        "observation_time_utc"
    ).reset_index(drop=True)

    return data


# ---------------------------------------------------------
# Download both stations
# ---------------------------------------------------------

print("=" * 60)
print("SMHI HISTORICAL WIND SPEED")
print("=" * 60)

old_data = download_station_data(
    OLD_STATION_ID
)

new_data = download_station_data(
    NEW_STATION_ID
)


# ---------------------------------------------------------
# Clean both datasets
# ---------------------------------------------------------

old_data = clean_station_data(
    old_data
)

new_data = clean_station_data(
    new_data
)

print()
print(
    f"Clean rows {OLD_STATION_ID}: "
    f"{len(old_data):,}"
)

print(
    f"Clean rows {NEW_STATION_ID}: "
    f"{len(new_data):,}"
)





# ---------------------------------------------------------
# Select final columns
# ---------------------------------------------------------

old_data = old_data[
    [
        "station_id",
        "observation_time_utc",
        "wind_speed_mps",
        "quality"
    ]
]

new_data = new_data[
    [
        "station_id",
        "observation_time_utc",
        "wind_speed_mps",
        "quality"
    ]
]


# ---------------------------------------------------------
# Combine both stations
# ---------------------------------------------------------

data = pd.concat(
    [
        old_data,
        new_data
    ],
    ignore_index=True
)

data = data.sort_values(
    "observation_time_utc"
).reset_index(drop=True)


# ---------------------------------------------------------
# Validation
# ---------------------------------------------------------

print()
print("=" * 60)
print("WIND SPEED VALIDATION")
print("=" * 60)

print()
print("Rows by station:")
print(
    data["station_id"].value_counts()
)

print()
print("Missing values:")
print(
    data.isna().sum()
)

print()
print(
    "Duplicate station/timestamp rows:",
    data.duplicated(
        subset=[
            "station_id",
            "observation_time_utc"
        ]
    ).sum()
)

print()
print(
    "First observation:",
    data["observation_time_utc"].min()
)

print(
    "Last observation:",
    data["observation_time_utc"].max()
)

print()
print(
    "Minimum wind speed:",
    data["wind_speed_mps"].min(),
    "m/s"
)

print(
    "Maximum wind speed:",
    data["wind_speed_mps"].max(),
    "m/s"
)

print(
    "Average wind speed:",
    f"{data['wind_speed_mps'].mean():.2f}",
    "m/s"
)


# ---------------------------------------------------------
# Save
# ---------------------------------------------------------

OUTPUT_FILE.parent.mkdir(
    parents=True,
    exist_ok=True
)

data.to_csv(
    OUTPUT_FILE,
    index=False,
    encoding="utf-8"
)

print()
print("Validation passed!")

print()
print(
    "Total rows:",
    f"{len(data):,}"
)

print()
print("Saved to:")
print(OUTPUT_FILE)

print("=" * 60)