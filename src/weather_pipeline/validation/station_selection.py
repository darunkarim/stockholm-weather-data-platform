from pathlib import Path
import pandas as pd


# ============================================================
# STATION SELECTION
# ============================================================
# This file documents which SMHI station is used for each
# weather parameter and during which period.
#
# The goal is to create a consistent "Stockholm" dataset
# without blindly averaging measurements from different
# stations.
# ============================================================


# Project root
PROJECT_ROOT = Path(__file__).resolve().parents[3]

# Output directory
OUTPUT_DIR = PROJECT_ROOT / "data" / "processed"


# ------------------------------------------------------------
# Temperature
# ------------------------------------------------------------
# 98210 has the longest historical temperature coverage.
#
# 98230 overlaps with 98210 from 1996-10-01 to 2024-03-31
# and the two stations are extremely similar during that
# period.
#
# Therefore:
#   1859-01-01 -> 2024-03-31 : 98210
#   2024-04-01 -> present     : 98230
#
# We switch on 2024-04-01 so that the two datasets do not
# contain the same calendar day in the final Gold dataset.

temperature_selection = [
    {
        "parameter": "temperature",
        "valid_from": "1859-01-01",
        "valid_to": "2024-03-31",
        "station_id": "98210",
        "station_name": "Stockholm-Observatoriekullen",
        "reason": "Longest historical coverage with excellent data completeness.",
    },
    {
        "parameter": "temperature",
        "valid_from": "2024-04-01",
        "valid_to": "2026-09-17",
        "station_id": "98230",
        "station_name": "Stockholm-Observatoriekullen A",
        "reason": "Modern continuation with excellent coverage and strong overlap agreement with station 98210.",
    },
]


# ------------------------------------------------------------
# Precipitation
# ------------------------------------------------------------
# 98210 provides a long historical precipitation series.
#
# 98230 has only 11.8% coverage, so it should NOT be used
# as the main precipitation source for the historical period.
#
# For now we use 98210 through its available period.
# We will investigate a suitable modern precipitation station
# before creating a complete 2024+ precipitation series.

precipitation_selection = [
    {
        "parameter": "precipitation",
        "valid_from": "1859-01-01",
        "valid_to": "2024-03-31",
        "station_id": "98210",
        "station_name": "Stockholm-Observatoriekullen",
        "reason": "Longest usable precipitation coverage with 99.40% calendar-day coverage and 79.46% G-quality observations.",
    }
]


# ------------------------------------------------------------
# Wind
# ------------------------------------------------------------
# Wind is intentionally NOT finalized yet.
#
# The stations have different observation frequencies,
# geographical locations and quality profiles.
#
# We therefore need another validation step before selecting
# the final Stockholm wind series.

wind_selection = []


# ------------------------------------------------------------
# Combine selections
# ------------------------------------------------------------

selection = (
    temperature_selection
    + precipitation_selection
    + wind_selection
)


df = pd.DataFrame(selection)


# Convert dates to proper datetime values
df["valid_from"] = pd.to_datetime(df["valid_from"])
df["valid_to"] = pd.to_datetime(df["valid_to"])


# Sort the final table
df = df.sort_values(
    by=["parameter", "valid_from"]
).reset_index(drop=True)


# ------------------------------------------------------------
# Validation
# ------------------------------------------------------------

print("=" * 70)
print("STATION SELECTION")
print("=" * 70)

print()

for parameter in df["parameter"].unique():

    parameter_df = df[df["parameter"] == parameter]

    print(f"{parameter.upper()}")

    for _, row in parameter_df.iterrows():

        print(
            f"  {row['valid_from'].date()} → "
            f"{row['valid_to'].date()} | "
            f"Station {row['station_id']} | "
            f"{row['station_name']}"
        )

    print()


# Check that there are no overlapping periods for the same
# parameter.
for parameter in df["parameter"].unique():

    parameter_df = df[
        df["parameter"] == parameter
    ].sort_values("valid_from")

    previous_end = None

    for _, row in parameter_df.iterrows():

        if previous_end is not None:

            if row["valid_from"] <= previous_end:

                raise ValueError(
                    f"Overlapping station selection found for "
                    f"{parameter}: {row['station_id']}"
                )

        previous_end = row["valid_to"]


# ------------------------------------------------------------
# Save result
# ------------------------------------------------------------

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True
)

output_file = (
    OUTPUT_DIR
    / "station_selection.csv"
)

df.to_csv(
    output_file,
    index=False
)

print("=" * 70)
print("VALIDATION PASSED")
print("=" * 70)

print()
print(f"Saved: {output_file}")
print()
print(df.to_string(index=False))