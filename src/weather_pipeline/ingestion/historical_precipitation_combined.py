import io
from pathlib import Path

import pandas as pd
import requests


# ---------------------------------------------------------
# Configuration
# ---------------------------------------------------------

PARAMETER_ID = 5

# Older Stockholm-Observatoriekullen station
OLD_STATION_ID = 98210

# Current Stockholm-Observatoriekullen A station
NEW_STATION_ID = 98230

# Keep the same station cut as the temperature pipeline.
OLD_STATION_END = "1996-09-30"
NEW_STATION_START = "1996-10-01"

PROJECT_ROOT = Path(__file__).resolve().parents[3]

OUTPUT_FILE = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "stockholm_precipitation_historical_combined.csv"
)


# ---------------------------------------------------------
# Download function
# ---------------------------------------------------------

def download_station_data(station_id):
    """Download precipitation data for one SMHI station."""

    url = (
        f"https://opendata-download-metobs.smhi.se/"
        f"api/version/latest/parameter/{PARAMETER_ID}/"
        f"station/{station_id}/period/corrected-archive/data.csv"
    )

    print()
    print(f"Downloading station {station_id}...")

    response = requests.get(url, timeout=60)
    response.raise_for_status()

    print("Download successful!")

    # Read the CSV line by line because SMHI includes
    # metadata before the actual observations.
    text = response.content.decode("utf-8")
    lines = text.splitlines()

    data_lines = []

    for line in lines:

        parts = line.split(";")

        # A valid observation contains at least five columns.
        if len(parts) < 5:
            continue

        first_value = parts[0].strip()

        # Check whether the first column is a valid datetime.
        parsed_date = pd.to_datetime(
            first_value,
            errors="coerce"
        )

        if pd.notna(parsed_date):
            data_lines.append(parts[:5])

    data = pd.DataFrame(
        data_lines,
        columns=[
            "from_utc",
            "to_utc",
            "reference_date",
            "precipitation_mm",
            "quality"
        ]
    )

    # Add station ID so we know which station each
    # observation came from.
    data["station_id"] = str(station_id)

    return data


# ---------------------------------------------------------
# Clean station data
# ---------------------------------------------------------

def clean_station_data(data):
    """Clean and validate precipitation data."""

    data["from_utc"] = pd.to_datetime(
        data["from_utc"],
        errors="coerce",
        utc=True
    )

    data["to_utc"] = pd.to_datetime(
        data["to_utc"],
        errors="coerce",
        utc=True
    )

    data["reference_date"] = pd.to_datetime(
        data["reference_date"],
        errors="coerce"
    )

    data["precipitation_mm"] = pd.to_numeric(
        data["precipitation_mm"],
        errors="coerce"
    )

    # Remove metadata or invalid rows.
    data = data.dropna(
        subset=[
            "from_utc",
            "to_utc",
            "reference_date",
            "precipitation_mm"
        ]
    )

    # Keep valid SMHI quality codes.
    data = data[
        data["quality"].isin(["G", "Y", "X", "M"])
    ]

    return data


# ---------------------------------------------------------
# Download both stations
# ---------------------------------------------------------

print("=" * 60)
print("SMHI HISTORICAL PRECIPITATION")
print("=" * 60)

old_data = download_station_data(OLD_STATION_ID)
new_data = download_station_data(NEW_STATION_ID)

print()
print(f"Rows downloaded 98210: {len(old_data):,}")
print(f"Rows downloaded 98230: {len(new_data):,}")


# ---------------------------------------------------------
# Clean both stations
# ---------------------------------------------------------

old_data = clean_station_data(old_data)
new_data = clean_station_data(new_data)

print()
print(f"Clean rows 98210: {len(old_data):,}")
print(f"Clean rows 98230: {len(new_data):,}")


# ---------------------------------------------------------
# Apply date ranges
# ---------------------------------------------------------

# The older station is used up to 1996-09-30.
old_data = old_data[
    old_data["reference_date"]
    <= pd.Timestamp(OLD_STATION_END)
]

# The newer station is used from 1996-10-01.
new_data = new_data[
    new_data["reference_date"]
    >= pd.Timestamp(NEW_STATION_START)
]


# ---------------------------------------------------------
# Combine stations
# ---------------------------------------------------------

data = pd.concat(
    [old_data, new_data],
    ignore_index=True
)

# Sort chronologically.
data = data.sort_values(
    ["reference_date", "station_id"]
).reset_index(drop=True)


# ---------------------------------------------------------
# Validation
# ---------------------------------------------------------

print()
print("=" * 60)
print("PRECIPITATION VALIDATION")
print("=" * 60)

print()
print("Rows by station:")
print(data["station_id"].value_counts())

print()
print("Missing values:")
print(data.isna().sum())

print()
print(
    "Duplicate station/reference date rows:",
    data.duplicated(
        subset=["station_id", "reference_date"]
    ).sum()
)

print()
print(
    "Duplicate station/timestamp rows:",
    data.duplicated(
        subset=["station_id", "from_utc"]
    ).sum()
)

print()
print(
    "First observation:",
    data["reference_date"].min()
)

print(
    "Last observation:",
    data["reference_date"].max()
)

print()
print(
    "Minimum precipitation:",
    data["precipitation_mm"].min(),
    "mm"
)

print(
    "Maximum precipitation:",
    data["precipitation_mm"].max(),
    "mm"
)

print(
    "Average precipitation:",
    f"{data['precipitation_mm'].mean():.2f}",
    "mm"
)


# ---------------------------------------------------------
# Save combined data
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
print("Validation completed!")

print()
print("Saved to:")
print(OUTPUT_FILE)

print("=" * 60)