from pathlib import Path

import pandas as pd


# =============================================================================
# CONFIGURATION
# =============================================================================

RAW_DIR = Path("data/raw")
PROCESSED_DIR = Path("data/processed")

PROCESSED_DIR.mkdir(parents=True, exist_ok=True)


# Temperaturfiler
TEMPERATURE_FILES = {
    "temperature_98210": RAW_DIR / "stockholm_temperature_98210_historical.csv",
    "temperature_98230": RAW_DIR / "stockholm_temperature_complete.csv",
    "temperature_97200": RAW_DIR / "stockholm_temperature_97200_historical.csv",
    "temperature_97400": RAW_DIR / "stockholm_temperature_97400_historical.csv",
}

# Nederbörd ligger i en gemensam fil för alla stationer.
PRECIPITATION_FILE = RAW_DIR / "stockholm_precipitation.csv"

# Vindfiler
WIND_FILES = {
    "wind_98210": RAW_DIR / "stockholm_wind_98210_historical.csv",
    "wind_97200": RAW_DIR / "stockholm_wind_97200_historical.csv",
    "wind_97400": RAW_DIR / "stockholm_wind_97400_historical.csv",
}


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def calculate_coverage(df, date_column="reference_date"):
    """
    Räknar hur många kalenderdagar som faktiskt finns i datasetet
    jämfört med hur många dagar som borde finnas mellan första och sista datum.
    """

    dates = pd.to_datetime(df[date_column], errors="coerce").dropna().dt.normalize()

    if dates.empty:
        return None

    unique_dates = pd.Series(dates.unique()).sort_values()

    first_date = unique_dates.iloc[0]
    last_date = unique_dates.iloc[-1]

    expected_days = (last_date - first_date).days + 1
    actual_days = len(unique_dates)
    missing_days = expected_days - actual_days

    coverage = (
        actual_days / expected_days * 100
        if expected_days > 0
        else 0
    )

    return {
        "first_date": first_date.date(),
        "last_date": last_date.date(),
        "actual_days": actual_days,
        "expected_days": expected_days,
        "missing_days": missing_days,
        "coverage_percent": round(coverage, 2),
    }


def find_gaps(df, date_column="reference_date"):
    """
    Hittar sammanhängande luckor i kalenderdagarna.
    """

    dates = (
        pd.to_datetime(df[date_column], errors="coerce")
        .dropna()
        .dt.normalize()
        .drop_duplicates()
        .sort_values()
    )

    if dates.empty:
        return []

    full_range = pd.date_range(
        start=dates.min(),
        end=dates.max(),
        freq="D",
    )

    missing = full_range.difference(dates)

    if len(missing) == 0:
        return []

    gaps = []

    gap_start = missing[0]
    previous = missing[0]

    for current in missing[1:]:
        if (current - previous).days > 1:
            gaps.append(
                {
                    "start": gap_start.date(),
                    "end": previous.date(),
                    "days": (previous - gap_start).days + 1,
                }
            )

            gap_start = current

        previous = current

    gaps.append(
        {
            "start": gap_start.date(),
            "end": previous.date(),
            "days": (previous - gap_start).days + 1,
        }
    )

    return gaps


def load_temperature_file(name, path):
    """
    Läser en temperaturfil och returnerar den med ett standardiserat datumfält.
    """

    if not path.exists():
        print(f"{name}: FILE NOT FOUND - skipped")
        return None

    df = pd.read_csv(path, encoding="utf-8-sig")

    if "reference_date" not in df.columns:
        print(f"{name}: reference_date saknas - skipped")
        return None

    df["reference_date"] = pd.to_datetime(
        df["reference_date"],
        errors="coerce",
    )

    df = df.dropna(subset=["reference_date"])

    return df


def load_wind_file(name, path):
    """
    Läser en vindfil och standardiserar datumfältet.
    """

    if not path.exists():
        print(f"{name}: FILE NOT FOUND - skipped")
        return None

    df = pd.read_csv(path, encoding="utf-8-sig")

    if "reference_date" not in df.columns:
        print(f"{name}: reference_date saknas - skipped")
        return None

    df["reference_date"] = pd.to_datetime(
        df["reference_date"],
        errors="coerce",
    )

    df = df.dropna(subset=["reference_date"])

    return df


# =============================================================================
# START
# =============================================================================

print("=" * 80)
print("FINAL STOCKHOLM WEATHER STATION COVERAGE CHECK")
print("=" * 80)


datasets = {}
summary_rows = []


# =============================================================================
# TEMPERATURE
# =============================================================================

for name, path in TEMPERATURE_FILES.items():

    print("\n" + "-" * 80)
    print(name)
    print(f"File: {path}")

    df = load_temperature_file(name, path)

    if df is None:
        continue

    datasets[name] = df

    coverage = calculate_coverage(df)

    print(f"First date:       {coverage['first_date']}")
    print(f"Last date:        {coverage['last_date']}")
    print(f"Actual days:      {coverage['actual_days']:,}")
    print(f"Expected days:    {coverage['expected_days']:,}")
    print(f"Missing days:     {coverage['missing_days']:,}")
    print(f"Coverage:         {coverage['coverage_percent']:.2f}%")

    summary_rows.append(
        {
            "dataset": name,
            **coverage,
        }
    )


# =============================================================================
# PRECIPITATION
# =============================================================================

print("\n" + "-" * 80)
print("PRECIPITATION")
print(f"File: {PRECIPITATION_FILE}")

if PRECIPITATION_FILE.exists():

    precipitation = pd.read_csv(
        PRECIPITATION_FILE,
        encoding="utf-8-sig",
    )

    precipitation["date"] = pd.to_datetime(
        precipitation["date"],
        errors="coerce",
    )

    precipitation = precipitation.dropna(subset=["date"])

    # Kontrollera varje station separat.
    for station_id in sorted(precipitation["station_id"].unique()):

        station_df = precipitation[
            precipitation["station_id"] == station_id
        ].copy()

        station_name = station_df["station_name"].iloc[0]

        name = f"precipitation_{station_id}"

        # Skapa reference_date så att alla dataset använder samma logik.
        station_df["reference_date"] = station_df["date"]

        datasets[name] = station_df

        coverage = calculate_coverage(
            station_df,
            date_column="reference_date",
        )

        print("\n" + "-" * 80)
        print(f"{name}")
        print(f"Station:          {station_name}")
        print(f"First date:       {coverage['first_date']}")
        print(f"Last date:        {coverage['last_date']}")
        print(f"Actual days:      {coverage['actual_days']:,}")
        print(f"Expected days:    {coverage['expected_days']:,}")
        print(f"Missing days:     {coverage['missing_days']:,}")
        print(f"Coverage:         {coverage['coverage_percent']:.2f}%")

        # Kvalitetsfördelning
        if "quality" in station_df.columns:

            quality_counts = station_df["quality"].value_counts()

            g_count = int(quality_counts.get("G", 0))
            y_count = int(quality_counts.get("Y", 0))

            total_quality = g_count + y_count

            g_percent = (
                g_count / total_quality * 100
                if total_quality > 0
                else 0
            )

            y_percent = (
                y_count / total_quality * 100
                if total_quality > 0
                else 0
            )

            print(f"G quality:        {g_count:,} ({g_percent:.2f}%)")
            print(f"Y quality:        {y_count:,} ({y_percent:.2f}%)")

        summary_rows.append(
            {
                "dataset": name,
                **coverage,
            }
        )

else:
    print("FILE NOT FOUND")


# =============================================================================
# WIND
# =============================================================================

for name, path in WIND_FILES.items():

    print("\n" + "-" * 80)
    print(name)
    print(f"File: {path}")

    df = load_wind_file(name, path)

    if df is None:
        continue

    datasets[name] = df

    coverage = calculate_coverage(df)

    print(f"First date:       {coverage['first_date']}")
    print(f"Last date:        {coverage['last_date']}")
    print(f"Actual days:      {coverage['actual_days']:,}")
    print(f"Expected days:    {coverage['expected_days']:,}")
    print(f"Missing days:     {coverage['missing_days']:,}")
    print(f"Coverage:         {coverage['coverage_percent']:.2f}%")

    summary_rows.append(
        {
            "dataset": name,
            **coverage,
        }
    )


# =============================================================================
# COVERAGE SUMMARY
# =============================================================================

print("\n")
print("=" * 80)
print("COVERAGE SUMMARY")
print("-" * 80)

summary_df = pd.DataFrame(summary_rows)

if not summary_df.empty:

    print(
        summary_df.to_string(
            index=False
        )
    )

    summary_df.to_csv(
        PROCESSED_DIR / "final_station_coverage.csv",
        index=False,
        encoding="utf-8-sig",
    )


# =============================================================================
# STATION OVERLAPS
# =============================================================================

print("\n")
print("=" * 80)
print("IMPORTANT STATION OVERLAPS")
print("-" * 80)


OVERLAP_PAIRS = [
    ("temperature_98210", "temperature_98230"),
    ("temperature_98230", "temperature_97200"),
    ("temperature_98210", "temperature_97200"),
    ("temperature_98210", "precipitation_98210"),
    ("temperature_98230", "precipitation_98230"),
    ("temperature_97200", "precipitation_97200"),
    ("wind_98210", "wind_97200"),
    ("wind_98210", "wind_97400"),
    ("wind_97200", "wind_97400"),
]


overlap_rows = []


for dataset_a, dataset_b in OVERLAP_PAIRS:

    if dataset_a not in datasets or dataset_b not in datasets:
        continue

    df_a = datasets[dataset_a]
    df_b = datasets[dataset_b]

    dates_a = set(
        pd.to_datetime(
            df_a["reference_date"],
            errors="coerce",
        )
        .dropna()
        .dt.normalize()
    )

    dates_b = set(
        pd.to_datetime(
            df_b["reference_date"],
            errors="coerce",
        )
        .dropna()
        .dt.normalize()
    )

    overlap = sorted(dates_a.intersection(dates_b))

    if not overlap:
        continue

    overlap_start = overlap[0].date()
    overlap_end = overlap[-1].date()
    overlap_days = len(overlap)

    print(
        f"{dataset_a} vs {dataset_b}: "
        f"{overlap_days:,} days "
        f"({overlap_start} to {overlap_end})"
    )

    overlap_rows.append(
        {
            "dataset_a": dataset_a,
            "dataset_b": dataset_b,
            "overlap_start": overlap_start,
            "overlap_end": overlap_end,
            "overlap_days": overlap_days,
        }
    )


overlap_df = pd.DataFrame(overlap_rows)

if not overlap_df.empty:

    overlap_df.to_csv(
        PROCESSED_DIR / "final_station_overlaps.csv",
        index=False,
        encoding="utf-8-sig",
    )


# =============================================================================
# DATA GAPS
# =============================================================================

print("\n")
print("=" * 80)
print("DATA GAPS")
print("-" * 80)


for name, df in datasets.items():

    gaps = find_gaps(df)

    print(f"{name}:", end=" ")

    if not gaps:
        print("No gaps")
        continue

    print(f"{len(gaps)} gap(s)")

    for gap in gaps[:10]:

        print(
            f"  {gap['start']} to {gap['end']} "
            f"({gap['days']} days)"
        )

    if len(gaps) > 10:
        print(
            f"  ... and {len(gaps) - 10} more"
        )


# =============================================================================
# COMPLETE
# =============================================================================

print("\n")
print("=" * 80)
print("FINAL COVERAGE CHECK COMPLETE")
print("=" * 80)

print(
    f"Saved: {PROCESSED_DIR / 'final_station_coverage.csv'}"
)

print(
    f"Saved: {PROCESSED_DIR / 'final_station_overlaps.csv'}"
)