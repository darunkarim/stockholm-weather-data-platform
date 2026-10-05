from pathlib import Path
import pandas as pd


# ============================================================
# SILVER WEATHER TRANSFORMATION
# ============================================================
# This script transforms the selected SMHI weather data into
# one clean and standardized Silver dataset.
#
# Bronze/Raw:
#   - Different files
#   - Different column names
#   - Different station periods
#
# Silver:
#   - Standardized column names
#   - Standardized parameter names
#   - Standardized units
#   - Only selected stations/periods
#   - Clean dates and values
#
# The Gold layer will later build business/analytics-friendly
# tables from this Silver dataset.
# ============================================================


# ------------------------------------------------------------
# Project paths
# ------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[3]

RAW_DIR = PROJECT_ROOT / "data" / "raw"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"


# ------------------------------------------------------------
# Input files
# ------------------------------------------------------------

TEMPERATURE_98210 = (
    RAW_DIR / "stockholm_temperature_98210_historical.csv"
)

TEMPERATURE_98230 = (
    RAW_DIR / "stockholm_temperature_complete.csv"
)

PRECIPITATION = (
    RAW_DIR / "stockholm_precipitation.csv"
)

STATION_SELECTION = (
    PROCESSED_DIR / "station_selection.csv"
)


# ------------------------------------------------------------
# Output
# ------------------------------------------------------------

OUTPUT_FILE = (
    PROCESSED_DIR / "silver_weather_observations.csv"
)


# ============================================================
# LOAD STATION SELECTION
# ============================================================

print("=" * 70)
print("SILVER WEATHER TRANSFORMATION")
print("=" * 70)

print()
print("Loading station selection...")

selection = pd.read_csv(
    STATION_SELECTION
)

selection["valid_from"] = pd.to_datetime(
    selection["valid_from"]
)

selection["valid_to"] = pd.to_datetime(
    selection["valid_to"]
)

print(
    f"Station selection rows: {len(selection)}"
)


# ============================================================
# TEMPERATURE
# ============================================================

print()
print("Loading temperature data...")


# Load historical 98210
temperature_98210 = pd.read_csv(
    TEMPERATURE_98210
)

# Load modern 98230
temperature_98230 = pd.read_csv(
    TEMPERATURE_98230
)


# Convert reference date to datetime.
#
# reference_date represents the calendar day for the
# daily temperature observation.
temperature_98210["reference_date"] = pd.to_datetime(
    temperature_98210["reference_date"]
)

temperature_98230["reference_date"] = pd.to_datetime(
    temperature_98230["reference_date"]
)


# ------------------------------------------------------------
# Apply station selection
# ------------------------------------------------------------

# 98210:
# 1859-01-01 -> 2024-03-31
temperature_98210 = temperature_98210[
    (temperature_98210["reference_date"] >= "1859-01-01")
    & (temperature_98210["reference_date"] <= "2024-03-31")
].copy()


# 98230:
# 2024-04-01 -> present
temperature_98230 = temperature_98230[
    (temperature_98230["reference_date"] >= "2024-04-01")
    & (temperature_98230["reference_date"] <= "2026-09-17")
].copy()


# ------------------------------------------------------------
# Standardize temperature columns
# ------------------------------------------------------------

temperature_98210 = temperature_98210[
    [
        "reference_date",
        "from_utc",
        "station_id",
        "station_name",
        "temperature_c",
        "quality",
    ]
].copy()


temperature_98230 = temperature_98230[
    [
        "reference_date",
        "from_utc",
        "station_id",
        "station_name",
        "temperature_c",
        "quality",
    ]
].copy()


# Rename columns to the common Silver schema
temperature_98210 = temperature_98210.rename(
    columns={
        "reference_date": "date",
        "temperature_c": "value",
    }
)

temperature_98230 = temperature_98230.rename(
    columns={
        "reference_date": "date",
        "temperature_c": "value",
    }
)


# Add standardized parameter and unit
temperature_98210["parameter"] = "temperature"
temperature_98210["unit"] = "C"

temperature_98230["parameter"] = "temperature"
temperature_98230["unit"] = "C"


# Combine both temperature periods
temperature = pd.concat(
    [
        temperature_98210,
        temperature_98230,
    ],
    ignore_index=True
)


# ============================================================
# PRECIPITATION
# ============================================================

print()
print("Loading precipitation data...")


precipitation = pd.read_csv(
    PRECIPITATION
)


# Convert date
precipitation["date"] = pd.to_datetime(
    precipitation["date"]
)


# ------------------------------------------------------------
# Apply precipitation station selection
# ------------------------------------------------------------

precipitation = precipitation[
    (precipitation["station_id"] == 98210)
    & (precipitation["date"] >= "1859-01-01")
    & (precipitation["date"] <= "2024-03-31")
].copy()


# ------------------------------------------------------------
# Standardize precipitation columns
# ------------------------------------------------------------

precipitation = precipitation[
    [
        "date",
        "station_id",
        "station_name",
        "precipitation_mm",
        "quality",
    ]
].copy()


precipitation = precipitation.rename(
    columns={
        "precipitation_mm": "value",
    }
)


# Precipitation is daily data, so there is no separate
# observation time that we need in the Silver table.
precipitation["time_utc"] = pd.NaT

precipitation["parameter"] = "precipitation"
precipitation["unit"] = "mm"


# ============================================================
# COMBINE PARAMETERS
# ============================================================

print()
print("Combining temperature and precipitation...")


# Temperature needs a standardized time column.
temperature["time_utc"] = pd.to_datetime(
    temperature["from_utc"],
    errors="coerce"
)


temperature = temperature[
    [
        "date",
        "time_utc",
        "station_id",
        "station_name",
        "parameter",
        "value",
        "unit",
        "quality",
    ]
]


precipitation = precipitation[
    [
        "date",
        "time_utc",
        "station_id",
        "station_name",
        "parameter",
        "value",
        "unit",
        "quality",
    ]
]


silver = pd.concat(
    [
        temperature,
        precipitation,
    ],
    ignore_index=True
)


# ============================================================
# DATA CLEANING
# ============================================================

print()
print("Cleaning Silver data...")


# Make sure station IDs are strings.
silver["station_id"] = (
    silver["station_id"]
    .astype(str)
)


# Make sure values are numeric.
silver["value"] = pd.to_numeric(
    silver["value"],
    errors="coerce"
)


# Remove rows where the actual measurement is missing.
silver = silver.dropna(
    subset=[
        "date",
        "value",
        "station_id",
        "parameter",
    ]
)


# Remove exact duplicate observations.
silver = silver.drop_duplicates()


# Sort the dataset.
silver = silver.sort_values(
    by=[
        "date",
        "parameter",
        "station_id",
    ]
).reset_index(drop=True)


# ============================================================
# VALIDATION
# ============================================================

print()
print("Running Silver validation...")

# Dates may not be missing.
if silver["date"].isna().any():
    raise ValueError(
        "Silver dataset contains missing dates."
    )


# Measurements may not be missing.
if silver["value"].isna().any():
    raise ValueError(
        "Silver dataset contains missing values."
    )


# Station IDs may not be missing.
if silver["station_id"].isna().any():
    raise ValueError(
        "Silver dataset contains missing station IDs."
    )


# Parameters may not be missing.
if silver["parameter"].isna().any():
    raise ValueError(
        "Silver dataset contains missing parameters."
    )


# Check that only expected parameters exist.
allowed_parameters = {
    "temperature",
    "precipitation",
}

unexpected_parameters = set(
    silver["parameter"].unique()
) - allowed_parameters

if unexpected_parameters:
    raise ValueError(
        f"Unexpected parameters found: "
        f"{unexpected_parameters}"
    )


# Check for duplicate observations.
duplicates = silver.duplicated(
    subset=[
        "date",
        "time_utc",
        "station_id",
        "parameter",
    ]
).sum()

if duplicates > 0:
    raise ValueError(
        f"Found {duplicates} duplicate observations."
    )


# ============================================================
# SAVE
# ============================================================

PROCESSED_DIR.mkdir(
    parents=True,
    exist_ok=True
)

silver.to_csv(
    OUTPUT_FILE,
    index=False
)


# ============================================================
# SUMMARY
# ============================================================

print()
print("=" * 70)
print("SILVER VALIDATION PASSED")
print("=" * 70)

print()

print(
    f"Rows saved: {len(silver):,}"
)

print(
    f"Date range: "
    f"{silver['date'].min().date()} → "
    f"{silver['date'].max().date()}"
)

print()

print("Parameters:")
print(
    silver["parameter"]
    .value_counts()
    .to_string()
)

print()

print("Stations:")
print(
    silver[
        ["station_id", "station_name"]
    ]
    .drop_duplicates()
    .sort_values("station_id")
    .to_string(index=False)
)

print()

print("Output:")
print(OUTPUT_FILE)

print()
print("=" * 70)