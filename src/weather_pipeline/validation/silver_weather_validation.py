from pathlib import Path
import pandas as pd


# ============================================================
# SILVER WEATHER QUALITY CHECK
# ============================================================
# This script validates the Silver weather dataset before
# moving on to the Gold layer.
#
# We check:
#   1. Schema
#   2. Date ranges
#   3. Station selection
#   4. Duplicate observations
#   5. Missing values
#   6. Temperature station transition
#   7. Precipitation gaps
#   8. Basic value ranges
# ============================================================


# ------------------------------------------------------------
# Paths
# ------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[3]

SILVER_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "silver_weather_observations.csv"
)


# ------------------------------------------------------------
# Load Silver dataset
# ------------------------------------------------------------

print("=" * 70)
print("SILVER WEATHER QUALITY CHECK")
print("=" * 70)

print()
print("Loading Silver dataset...")

df = pd.read_csv(
    SILVER_FILE
)

df["date"] = pd.to_datetime(
    df["date"]
)
# Normalize station IDs so that values such as
# 98210, "98210" and 98210.0 are treated consistently.
df["station_id"] = (
    pd.to_numeric(
        df["station_id"],
        errors="coerce"
    )
    .astype("Int64")
    .astype(str)
)
df["time_utc"] = pd.to_datetime(
    df["time_utc"],
    errors="coerce"
)

print(
    f"Rows loaded: {len(df):,}"
)


# ============================================================
# 1. SCHEMA CHECK
# ============================================================

print()
print("-" * 70)
print("1. SCHEMA CHECK")
print("-" * 70)

expected_columns = [
    "date",
    "time_utc",
    "station_id",
    "station_name",
    "parameter",
    "value",
    "unit",
    "quality",
]

missing_columns = [
    column
    for column in expected_columns
    if column not in df.columns
]

if missing_columns:
    raise ValueError(
        f"Missing columns: {missing_columns}"
    )

print("Schema: OK")


# ============================================================
# 2. NULL CHECK
# ============================================================

print()
print("-" * 70)
print("2. NULL CHECK")
print("-" * 70)

for column in [
    "date",
    "station_id",
    "parameter",
    "value",
]:

    missing = df[column].isna().sum()

    print(
        f"{column}: {missing:,} missing"
    )

    if missing > 0:
        raise ValueError(
            f"Missing values found in {column}"
        )

print("Required fields: OK")


# ============================================================
# 3. DUPLICATE CHECK
# ============================================================

print()
print("-" * 70)
print("3. DUPLICATE CHECK")
print("-" * 70)

duplicate_count = df.duplicated(
    subset=[
        "date",
        "time_utc",
        "station_id",
        "parameter",
    ]
).sum()

print(
    f"Duplicate observations: {duplicate_count:,}"
)

if duplicate_count > 0:
    raise ValueError(
        "Duplicate observations found."
    )

print("Duplicates: OK")


# ============================================================
# 4. PARAMETER CHECK
# ============================================================

print()
print("-" * 70)
print("4. PARAMETER CHECK")
print("-" * 70)

print(
    df["parameter"]
    .value_counts()
    .to_string()
)

allowed_parameters = {
    "temperature",
    "precipitation",
}

actual_parameters = set(
    df["parameter"].unique()
)

unexpected = (
    actual_parameters
    - allowed_parameters
)

if unexpected:
    raise ValueError(
        f"Unexpected parameters: {unexpected}"
    )

print()
print("Parameters: OK")


# ============================================================
# 5. TEMPERATURE STATION TRANSITION
# ============================================================

print()
print("-" * 70)
print("5. TEMPERATURE STATION TRANSITION")
print("-" * 70)

temperature = df[
    df["parameter"] == "temperature"
].copy()


# Before the transition date, only 98210 is allowed.
before_transition = temperature[
    temperature["date"] <= "2024-03-31"
]

wrong_before = before_transition[
    before_transition["station_id"] != "98210"
]


# From the transition date, only 98230 is allowed.
after_transition = temperature[
    temperature["date"] >= "2024-04-01"
]

wrong_after = after_transition[
    after_transition["station_id"] != "98230"
]


print(
    f"Before transition: "
    f"{len(before_transition):,} rows"
)

print(
    f"After transition: "
    f"{len(after_transition):,} rows"
)

print(
    f"Wrong station before transition: "
    f"{len(wrong_before):,}"
)

print(
    f"Wrong station after transition: "
    f"{len(wrong_after):,}"
)

if len(wrong_before) > 0:
    raise ValueError(
        "Wrong temperature station found before transition."
    )

if len(wrong_after) > 0:
    raise ValueError(
        "Wrong temperature station found after transition."
    )

print("Temperature station selection: OK")


# ============================================================
# 6. PRECIPITATION STATION CHECK
# ============================================================

print()
print("-" * 70)
print("6. PRECIPITATION STATION CHECK")
print("-" * 70)

precipitation = df[
    df["parameter"] == "precipitation"
].copy()

wrong_precipitation_station = precipitation[
    precipitation["station_id"] != "98210"
]

print(
    f"Precipitation rows: "
    f"{len(precipitation):,}"
)

print(
    f"Wrong station: "
    f"{len(wrong_precipitation_station):,}"
)

if len(wrong_precipitation_station) > 0:
    raise ValueError(
        "Unexpected precipitation station found."
    )

print("Precipitation station selection: OK")


# ============================================================
# 7. DATE RANGES
# ============================================================

print()
print("-" * 70)
print("7. DATE RANGES")
print("-" * 70)

for parameter in sorted(
    df["parameter"].unique()
):

    parameter_df = df[
        df["parameter"] == parameter
    ]

    print(
        f"{parameter}: "
        f"{parameter_df['date'].min().date()} "
        f"→ "
        f"{parameter_df['date'].max().date()}"
    )


# ============================================================
# 8. TEMPERATURE VALUE CHECK
# ============================================================

print()
print("-" * 70)
print("8. TEMPERATURE VALUE CHECK")
print("-" * 70)

temperature_values = temperature["value"]

print(
    f"Minimum: {temperature_values.min():.2f} °C"
)

print(
    f"Maximum: {temperature_values.max():.2f} °C"
)

print(
    f"Mean:    {temperature_values.mean():.2f} °C"
)


# These are broad sanity limits.
# They are not intended to determine whether an individual
# measurement is scientifically correct.
invalid_temperature = temperature[
    (temperature["value"] < -50)
    | (temperature["value"] > 50)
]

print(
    f"Values outside sanity range: "
    f"{len(invalid_temperature):,}"
)

if len(invalid_temperature) > 0:
    raise ValueError(
        "Temperature values outside sanity range."
    )

print("Temperature values: OK")


# ============================================================
# 9. PRECIPITATION VALUE CHECK
# ============================================================

print()
print("-" * 70)
print("9. PRECIPITATION VALUE CHECK")
print("-" * 70)

precipitation_values = precipitation["value"]

print(
    f"Minimum: {precipitation_values.min():.2f} mm"
)

print(
    f"Maximum: {precipitation_values.max():.2f} mm"
)

print(
    f"Mean:    {precipitation_values.mean():.2f} mm"
)


# Negative precipitation is impossible.
negative_precipitation = precipitation[
    precipitation["value"] < 0
]

print(
    f"Negative values: "
    f"{len(negative_precipitation):,}"
)

if len(negative_precipitation) > 0:
    raise ValueError(
        "Negative precipitation values found."
    )

print("Precipitation values: OK")


# ============================================================
# 10. PRECIPITATION GAPS
# ============================================================

print()
print("-" * 70)
print("10. PRECIPITATION GAP CHECK")
print("-" * 70)

precip_dates = (
    precipitation["date"]
    .drop_duplicates()
    .sort_values()
)

expected_dates = pd.date_range(
    start=precip_dates.min(),
    end=precip_dates.max(),
    freq="D",
)

missing_precip_dates = expected_dates.difference(
    precip_dates
)

print(
    f"Expected calendar days: "
    f"{len(expected_dates):,}"
)

print(
    f"Actual observation days: "
    f"{len(precip_dates):,}"
)

print(
    f"Missing calendar days: "
    f"{len(missing_precip_dates):,}"
)


# We expect missing dates because our earlier station
# coverage analysis identified gaps.
#
# We therefore report them instead of failing validation.
if len(missing_precip_dates) > 0:

    print()
    print("First missing precipitation dates:")

    for date in missing_precip_dates[:10]:
        print(
            f"  {date.date()}"
        )


# ============================================================
# 11. QUALITY DISTRIBUTION
# ============================================================

print()
print("-" * 70)
print("11. QUALITY DISTRIBUTION")
print("-" * 70)

quality_summary = (
    df.groupby(
        ["parameter", "quality"]
    )
    .size()
    .reset_index(name="rows")
)

print(
    quality_summary.to_string(
        index=False
    )
)


# ============================================================
# FINAL RESULT
# ============================================================

print()
print("=" * 70)
print("SILVER QUALITY CHECK PASSED")
print("=" * 70)

print()
print(
    f"Total Silver rows: {len(df):,}"
)

print(
    f"Date range: "
    f"{df['date'].min().date()} "
    f"→ "
    f"{df['date'].max().date()}"
)

print()
print("Silver dataset is ready for the next layer.")
print()