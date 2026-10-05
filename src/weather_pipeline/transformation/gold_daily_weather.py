"""
Gold layer transformation for the Stockholm Weather Data Platform.

Purpose:
- Transform Silver weather observations into one daily analytics table.
- Combine temperature and precipitation.
- Add calendar attributes for Power BI.
- Keep station IDs and quality information for data lineage.
- Validate the final Gold dataset before saving it.
"""

from pathlib import Path

import pandas as pd


# ============================================================================
# CONFIGURATION
# ============================================================================

PROJECT_ROOT = Path(__file__).resolve().parents[3]

SILVER_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "silver_weather_observations.csv"
)

WIND_SILVER_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "stockholm_wind_silver.csv"
)

WIND_STATION = "98210"


GOLD_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "gold_daily_weather.csv"
)

# Temperature station transition:
# 98210 is used up to and including 2024-03-31.
# 98230 is used from 2024-04-01 onward.
TEMPERATURE_TRANSITION_DATE = pd.Timestamp("2024-04-01")

TEMPERATURE_STATION_BEFORE = "98210"
TEMPERATURE_STATION_AFTER = "98230"

# Main historical precipitation station.
PRECIPITATION_STATION = "98210"


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def normalize_station_id(series: pd.Series) -> pd.Series:
    """
    Normalize station IDs.

    CSV files can sometimes load integer station IDs as values such as
    98210.0. We convert them to the consistent string format "98210".
    """

    return (
        pd.to_numeric(series, errors="coerce")
        .astype("Int64")
        .astype(str)
    )


# ============================================================================
# LOAD SILVER
# ============================================================================

print("=" * 70)
print("GOLD DAILY WEATHER")
print("=" * 70)

print("\nLoading Silver dataset...")

if not SILVER_FILE.exists():
    raise FileNotFoundError(
        f"Silver file not found: {SILVER_FILE}"
    )

silver = pd.read_csv(SILVER_FILE)

print(f"Silver rows loaded: {len(silver):,}")


# ============================================================================
# BASIC SILVER CLEANUP
# ============================================================================

silver["date"] = pd.to_datetime(
    silver["date"],
    errors="coerce"
)

silver["station_id"] = normalize_station_id(
    silver["station_id"]
)

silver["parameter"] = (
    silver["parameter"]
    .astype(str)
    .str.strip()
    .str.lower()
)


# ============================================================================
# PREPARE TEMPERATURE
# ============================================================================

print("\nPreparing temperature data...")

temperature = silver[
    silver["parameter"] == "temperature"
].copy()

if temperature.empty:
    raise ValueError("No temperature data found in Silver dataset.")


temperature = temperature[
    [
        "date",
        "value",
        "station_id",
        "quality",
    ]
].copy()


temperature = temperature.rename(
    columns={
        "value": "temperature_c",
        "station_id": "temperature_station_id",
        "quality": "temperature_quality",
    }
)


# Make sure temperature values are numeric.
temperature["temperature_c"] = pd.to_numeric(
    temperature["temperature_c"],
    errors="coerce"
)


# Check for duplicate temperature dates.
duplicate_temperature_dates = (
    temperature["date"].duplicated().sum()
)

print(
    f"Duplicate temperature dates: "
    f"{duplicate_temperature_dates}"
)

if duplicate_temperature_dates > 0:
    raise ValueError(
        "Duplicate temperature dates found."
    )


# ============================================================================
# PREPARE PRECIPITATION
# ============================================================================

print("\nPreparing precipitation data...")

precipitation = silver[
    silver["parameter"] == "precipitation"
].copy()

if precipitation.empty:
    raise ValueError(
        "No precipitation data found in Silver dataset."
    )


precipitation = precipitation[
    [
        "date",
        "value",
        "station_id",
        "quality",
    ]
].copy()


precipitation = precipitation.rename(
    columns={
        "value": "precipitation_mm",
        "station_id": "precipitation_station_id",
        "quality": "precipitation_quality",
    }
)


# Make sure precipitation values are numeric.
precipitation["precipitation_mm"] = pd.to_numeric(
    precipitation["precipitation_mm"],
    errors="coerce"
)


# Check for duplicate precipitation dates.
duplicate_precipitation_dates = (
    precipitation["date"].duplicated().sum()
)

print(
    f"Duplicate precipitation dates: "
    f"{duplicate_precipitation_dates}"
)

if duplicate_precipitation_dates > 0:
    raise ValueError(
        "Duplicate precipitation dates found."
    )


# ============================================================================
# PREPARE WIND
# ============================================================================

print("\nPreparing wind data...")

if not WIND_SILVER_FILE.exists():
    raise FileNotFoundError(
        f"Wind Silver file not found: {WIND_SILVER_FILE}"
    )

wind = pd.read_csv(WIND_SILVER_FILE)

print(f"Wind Silver rows loaded: {len(wind):,}")

if wind.empty:
    raise ValueError(
        "No wind data found in Wind Silver dataset."
    )

wind["observation_time_utc"] = pd.to_datetime(
    wind["observation_time_utc"],
    errors="coerce",
    utc=True
)

wind["date"] = pd.to_datetime(
    wind["observation_date"],
    errors="coerce"
)

wind["station_id"] = normalize_station_id(
    wind["station_id"]
)

wind["wind_speed_mps"] = pd.to_numeric(
    wind["wind_speed_mps"],
    errors="coerce"
)

wind = wind.dropna(
    subset=[
        "date",
        "wind_speed_mps",
        "station_id",
    ]
)

wrong_wind_station = (
    wind["station_id"] != WIND_STATION
).sum()

print(
    f"Wrong wind station rows: "
    f"{wrong_wind_station}"
)

if wrong_wind_station > 0:
    raise ValueError(
        "Incorrect wind station found."
    )

# Aggregate wind observations into one row per day.
wind_daily = (
    wind.groupby("date", as_index=False)
    .agg(
        avg_wind_speed_mps=(
            "wind_speed_mps",
            "mean",
        ),
        min_wind_speed_mps=(
            "wind_speed_mps",
            "min",
        ),
        max_wind_speed_mps=(
            "wind_speed_mps",
            "max",
        ),
        wind_observation_count=(
            "wind_speed_mps",
            "count",
        ),
    )
)

wind_daily["wind_station_id"] = WIND_STATION

print(
    f"Daily wind rows: "
    f"{len(wind_daily):,}"
)

duplicate_wind_dates = (
    wind_daily["date"].duplicated().sum()
)

print(
    f"Duplicate wind dates: "
    f"{duplicate_wind_dates}"
)

if duplicate_wind_dates > 0:
    raise ValueError(
        "Duplicate wind dates found."
    )

# ============================================================================
# COMBINE TEMPERATURE AND PRECIPITATION
# ============================================================================

print("\nCombining daily weather data...")

gold = pd.merge(
    temperature,
    precipitation,
    on="date",
    how="outer",
)

gold = pd.merge(
    gold,
    wind_daily,
    on="date",
    how="outer",
)


# ============================================================================
# NORMALIZE STATION IDS
# ============================================================================

# IMPORTANT:
# CSV files may turn station IDs into values such as 98210.0.
# Normalize them before performing station validation.

gold["temperature_station_id"] = normalize_station_id(
    gold["temperature_station_id"]
)

gold["precipitation_station_id"] = normalize_station_id(
    gold["precipitation_station_id"]
)


# ============================================================================
# CREATE CALENDAR ATTRIBUTES
# ============================================================================

print("\nCreating calendar attributes...")

gold["year"] = gold["date"].dt.year
gold["month"] = gold["date"].dt.month
gold["day"] = gold["date"].dt.day


# Swedish month names.
swedish_months = {
    1: "Januari",
    2: "Februari",
    3: "Mars",
    4: "April",
    5: "Maj",
    6: "Juni",
    7: "Juli",
    8: "Augusti",
    9: "September",
    10: "Oktober",
    11: "November",
    12: "December",
}

gold["month_name"] = gold["month"].map(
    swedish_months
)


# Seasons based on meteorological/calendar months.
def get_season(month: int) -> str:
    if month in [12, 1, 2]:
        return "Winter"

    if month in [3, 4, 5]:
        return "Spring"

    if month in [6, 7, 8]:
        return "Summer"

    return "Autumn"


gold["season"] = gold["month"].apply(
    get_season
)


# ============================================================================
# SORT AND ORDER COLUMNS
# ============================================================================

gold = gold.sort_values(
    "date"
).reset_index(drop=True)


gold = gold[
    [
        "date",
        "year",
        "month",
        "month_name",
        "day",
        "season",
        "temperature_c",
        "precipitation_mm",
        "avg_wind_speed_mps",
        "min_wind_speed_mps",
        "max_wind_speed_mps",
        "wind_observation_count",
        "temperature_station_id",
        "precipitation_station_id",
        "wind_station_id",
        "temperature_quality",
        "precipitation_quality",
    ]
]


# ============================================================================
# GOLD VALIDATION
# ============================================================================

print("\n" + "=" * 70)
print("GOLD VALIDATION")
print("=" * 70)


# --------------------------------------------------------------------------
# Validate unique dates
# --------------------------------------------------------------------------

duplicate_dates = gold["date"].duplicated().sum()

print(f"Duplicate dates: {duplicate_dates}")

if duplicate_dates > 0:
    raise ValueError(
        "Duplicate dates found in Gold dataset."
    )


# --------------------------------------------------------------------------
# Validate date continuity
# --------------------------------------------------------------------------

expected_dates = pd.date_range(
    start=gold["date"].min(),
    end=gold["date"].max(),
    freq="D",
)

actual_dates = pd.DatetimeIndex(
    gold["date"]
)

missing_dates = expected_dates.difference(
    actual_dates
)

print(
    f"Missing dates: {len(missing_dates)}"
)

if len(missing_dates) > 0:
    print(
        "WARNING: Missing calendar dates detected."
    )


# --------------------------------------------------------------------------
# Validate temperature station before transition
# --------------------------------------------------------------------------

before_transition = gold[
    gold["date"] < TEMPERATURE_TRANSITION_DATE
].copy()

wrong_temperature_before = (
    (
        before_transition["temperature_station_id"]
        .notna()
    )
    &
    (
        before_transition["temperature_station_id"]
        != TEMPERATURE_STATION_BEFORE
    )
).sum()


print(
    "Wrong temperature station before transition: "
    f"{wrong_temperature_before}"
)


if wrong_temperature_before > 0:
    raise ValueError(
        "Incorrect temperature station before transition."
    )


# --------------------------------------------------------------------------
# Validate temperature station after transition
# --------------------------------------------------------------------------

after_transition = gold[
    gold["date"] >= TEMPERATURE_TRANSITION_DATE
].copy()

wrong_temperature_after = (
    (
        after_transition["temperature_station_id"]
        .notna()
    )
    &
    (
        after_transition["temperature_station_id"]
        != TEMPERATURE_STATION_AFTER
    )
).sum()


print(
    "Wrong temperature station after transition: "
    f"{wrong_temperature_after}"
)


if wrong_temperature_after > 0:
    raise ValueError(
        "Incorrect temperature station after transition."
    )


# --------------------------------------------------------------------------
# Validate precipitation station
# --------------------------------------------------------------------------

wrong_precipitation_station = (
    (
        gold["precipitation_station_id"]
        .notna()
    )
    &
    (
        gold["precipitation_station_id"]
        != PRECIPITATION_STATION
    )
).sum()


print(
    "Wrong precipitation station: "
    f"{wrong_precipitation_station}"
)


if wrong_precipitation_station > 0:
    raise ValueError(
        "Incorrect precipitation station."
    )


# --------------------------------------------------------------------------
# Validate temperature values
# --------------------------------------------------------------------------

temperature_min = gold[
    "temperature_c"
].min()

temperature_max = gold[
    "temperature_c"
].max()

temperature_mean = gold[
    "temperature_c"
].mean()

invalid_temperature = (
    (
        gold["temperature_c"].notna()
    )
    &
    (
        (
            gold["temperature_c"] < -50
        )
        |
        (
            gold["temperature_c"] > 50
        )
    )
).sum()


print(
    f"Temperature min: {temperature_min:.2f} °C"
)

print(
    f"Temperature max: {temperature_max:.2f} °C"
)

print(
    f"Temperature mean: {temperature_mean:.2f} °C"
)

print(
    f"Invalid temperature values: "
    f"{invalid_temperature}"
)


if invalid_temperature > 0:
    raise ValueError(
        "Invalid temperature values found."
    )


# --------------------------------------------------------------------------
# Validate precipitation values
# --------------------------------------------------------------------------

precipitation_min = gold[
    "precipitation_mm"
].min()

precipitation_max = gold[
    "precipitation_mm"
].max()

precipitation_mean = gold[
    "precipitation_mm"
].mean()

negative_precipitation = (
    (
        gold["precipitation_mm"].notna()
    )
    &
    (
        gold["precipitation_mm"] < 0
    )
).sum()


print(
    f"Precipitation min: "
    f"{precipitation_min:.2f} mm"
)

print(
    f"Precipitation max: "
    f"{precipitation_max:.2f} mm"
)

print(
    f"Precipitation mean: "
    f"{precipitation_mean:.2f} mm"
)

print(
    f"Negative precipitation values: "
    f"{negative_precipitation}"
)


if negative_precipitation > 0:
    raise ValueError(
        "Negative precipitation values found."
    )

# --------------------------------------------------------------------------
# Validate wind values
# --------------------------------------------------------------------------

wind_min = gold[
    "min_wind_speed_mps"
].min()

wind_max = gold[
    "max_wind_speed_mps"
].max()

wind_mean = gold[
    "avg_wind_speed_mps"
].mean()

negative_wind = (
    (
        gold["min_wind_speed_mps"].notna()
    )
    &
    (
        gold["min_wind_speed_mps"] < 0
    )
).sum()


print(
    f"Wind min: {wind_min:.2f} m/s"
)

print(
    f"Wind max: {wind_max:.2f} m/s"
)

print(
    f"Daily average wind mean: "
    f"{wind_mean:.2f} m/s"
)

print(
    f"Negative wind values: "
    f"{negative_wind}"
)


if negative_wind > 0:
    raise ValueError(
        "Negative wind values found."
    )


# --------------------------------------------------------------------------
# Print row and date information
# --------------------------------------------------------------------------

print(
    f"\nGold rows: {len(gold):,}"
)

print(
    f"Date range: "
    f"{gold['date'].min().date()} → "
    f"{gold['date'].max().date()}"
)

print(
    f"Temperature rows: "
    f"{gold['temperature_c'].notna().sum():,}"
)

print(
    f"Precipitation rows: "
    f"{gold['precipitation_mm'].notna().sum():,}"
)

print(
    f"Wind rows: "
    f"{gold['avg_wind_speed_mps'].notna().sum():,}"
)


# ============================================================================
# SAVE GOLD DATASET
# ============================================================================

print("\nSaving Gold dataset...")

gold.to_csv(
    GOLD_FILE,
    index=False,
    encoding="utf-8-sig",
)

print(
    f"Gold dataset saved to:\n{GOLD_FILE}"
)


# ============================================================================
# FINAL SUCCESS MESSAGE
# ============================================================================

print("\n" + "=" * 70)
print("GOLD VALIDATION PASSED")
print("=" * 70)

print(
    "\nGold layer successfully created."
)

print(
    "Ready for the next stage: Azure SQL / dbt / Power BI."
)