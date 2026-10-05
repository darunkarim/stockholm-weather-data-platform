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
    / "stockholm_precipitation_historical_combined.csv"
)

OUTPUT_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "stockholm_precipitation_silver.csv"
)


# ---------------------------------------------------------
# Load raw data
# ---------------------------------------------------------

print("=" * 60)
print("SMHI PRECIPITATION SILVER TRANSFORMATION")
print("=" * 60)

print()
print("Loading raw precipitation data...")

data = pd.read_csv(INPUT_FILE)

print(f"Rows loaded: {len(data):,}")


# ---------------------------------------------------------
# Transform data types
# ---------------------------------------------------------

data["station_id"] = data["station_id"].astype(str)

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

data["quality"] = data["quality"].astype(str)


# ---------------------------------------------------------
# Remove invalid rows
# ---------------------------------------------------------

data = data.dropna(
    subset=[
        "station_id",
        "from_utc",
        "to_utc",
        "reference_date",
        "precipitation_mm"
    ]
)


# ---------------------------------------------------------
# Remove duplicates
# ---------------------------------------------------------

data = data.drop_duplicates(
    subset=[
        "station_id",
        "reference_date"
    ]
)


# ---------------------------------------------------------
# Sort data
# ---------------------------------------------------------

data = data.sort_values(
    ["reference_date", "station_id"]
).reset_index(drop=True)


# ---------------------------------------------------------
# Validation
# ---------------------------------------------------------

print()
print("=" * 60)
print("SILVER VALIDATION")
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
print(f"Rows: {len(data):,}")

print()
print("Saved to:")
print(OUTPUT_FILE)

print("=" * 60)