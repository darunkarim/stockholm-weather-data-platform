from pathlib import Path

import pandas as pd


# ---------------------------------------------------------
# Configuration
# ---------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[3]

INPUT_FILE = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "stockholm_wind_speed_historical_combined.csv"
)

OUTPUT_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "stockholm_wind_silver.csv"
)


# ---------------------------------------------------------
# Load raw data
# ---------------------------------------------------------

print("=" * 60)
print("SMHI WIND SPEED SILVER TRANSFORMATION")
print("=" * 60)

print()
print("Loading raw wind data...")

data = pd.read_csv(INPUT_FILE)

print(f"Rows loaded: {len(data):,}")


# ---------------------------------------------------------
# Transform data types
# ---------------------------------------------------------

data["station_id"] = data["station_id"].astype(str)

data["observation_time_utc"] = pd.to_datetime(
    data["observation_time_utc"],
    errors="coerce",
    utc=True
)

data["wind_speed_mps"] = pd.to_numeric(
    data["wind_speed_mps"],
    errors="coerce"
)

data["quality"] = data["quality"].astype(str)


# ---------------------------------------------------------
# Remove invalid rows
# ---------------------------------------------------------

data = data.dropna(
    subset=[
        "station_id",
        "observation_time_utc",
        "wind_speed_mps"
    ]
)

# Wind speed cannot be negative.
data = data[
    data["wind_speed_mps"] >= 0
]


# ---------------------------------------------------------
# Remove duplicates
# ---------------------------------------------------------

data = data.drop_duplicates(
    subset=[
        "station_id",
        "observation_time_utc"
    ]
)


# ---------------------------------------------------------
# Add useful time dimensions
# ---------------------------------------------------------

data["observation_date"] = (
    data["observation_time_utc"]
    .dt.date
)

data["year"] = (
    data["observation_time_utc"]
    .dt.year
)

data["month"] = (
    data["observation_time_utc"]
    .dt.month
)

data["day"] = (
    data["observation_time_utc"]
    .dt.day
)

data["hour"] = (
    data["observation_time_utc"]
    .dt.hour
)


# ---------------------------------------------------------
# Sort data
# ---------------------------------------------------------

data = data.sort_values(
    [
        "observation_time_utc",
        "station_id"
    ]
).reset_index(drop=True)


# ---------------------------------------------------------
# Validation
# ---------------------------------------------------------

print()
print("=" * 60)
print("SILVER WIND VALIDATION")
print("=" * 60)

print()
print("Rows by station:")
print(data["station_id"].value_counts())

print()
print("Missing values:")
print(data.isna().sum())

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
# Save Silver data
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
    "Rows:",
    f"{len(data):,}"
)

print()
print("Saved to:")
print(OUTPUT_FILE)

print("=" * 60)