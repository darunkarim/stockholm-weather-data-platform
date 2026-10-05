import pandas as pd


# ---------------------------------------------------------
# INSTÄLLNINGAR
# ---------------------------------------------------------

INPUT_FILE = "data/raw/stockholm_precipitation.csv"


# ---------------------------------------------------------
# LÄS DATA
# ---------------------------------------------------------

print("=" * 80)
print("STOCKHOLM WEATHER – JÄMFÖRELSE AV NEDERBÖRDSSTATIONER")
print("=" * 80)
print()

df = pd.read_csv(INPUT_FILE)

# Säkerställ att datumet behandlas som datum.
df["date"] = pd.to_datetime(df["date"])


# ---------------------------------------------------------
# ANALYSERA VARJE STATION
# ---------------------------------------------------------

results = []

for station_id, station_df in df.groupby("station_id"):

    station_df = station_df.sort_values("date").copy()

    station_name = station_df["station_name"].iloc[0]

    first_date = station_df["date"].min()
    last_date = station_df["date"].max()

    # Antal faktiska observationer.
    observations = len(station_df)

    # Skapa alla datum som borde finnas mellan
    # första och sista observationen.
    expected_dates = pd.date_range(
        start=first_date,
        end=last_date,
        freq="D"
    )

    actual_dates = pd.DatetimeIndex(
        station_df["date"].unique()
    )

    missing_dates = expected_dates.difference(
        actual_dates
    )

    # Kvalitetsfördelning.
    quality_counts = station_df["quality"].value_counts()

    g_count = quality_counts.get("G", 0)
    y_count = quality_counts.get("Y", 0)

    # Procent G/Y.
    g_percent = (
        g_count / observations * 100
        if observations > 0
        else 0
    )

    y_percent = (
        y_count / observations * 100
        if observations > 0
        else 0
    )

    # Antal förväntade dygn.
    expected_count = len(expected_dates)

    # Täckningsgrad.
    coverage_percent = (
        observations / expected_count * 100
        if expected_count > 0
        else 0
    )

    results.append(
        {
            "station_id": station_id,
            "station_name": station_name,
            "first_date": first_date.date(),
            "last_date": last_date.date(),
            "observations": observations,
            "expected_days": expected_count,
            "missing_days": len(missing_dates),
            "coverage_percent": coverage_percent,
            "G_count": g_count,
            "G_percent": g_percent,
            "Y_count": y_count,
            "Y_percent": y_percent,
        }
    )


# ---------------------------------------------------------
# SKAPA RESULTATTABELL
# ---------------------------------------------------------

comparison = pd.DataFrame(results)

# Sortera efter högst täckningsgrad.
comparison = comparison.sort_values(
    "coverage_percent",
    ascending=False
)


# ---------------------------------------------------------
# VISA RESULTAT
# ---------------------------------------------------------

print("STATIONSKÖVERSIKT")
print("-" * 80)

print(
    comparison.to_string(
        index=False,
        formatters={
            "coverage_percent": "{:.2f}%".format,
            "G_percent": "{:.2f}%".format,
            "Y_percent": "{:.2f}%".format,
        }
    )
)

print()


# ---------------------------------------------------------
# MER LÄTTLÄST VERSION
# ---------------------------------------------------------

print("=" * 80)
print("SAMMANFATTNING")
print("=" * 80)

for _, row in comparison.iterrows():

    print()
    print(
        f"Station {row['station_id']} – "
        f"{row['station_name']}"
    )

    print(
        f"  Period:       "
        f"{row['first_date']} → {row['last_date']}"
    )

    print(
        f"  Observationer: {row['observations']:,}"
    )

    print(
        f"  Saknade dygn:  {row['missing_days']:,}"
    )

    print(
        f"  Täckning:      "
        f"{row['coverage_percent']:.2f}%"
    )

    print(
        f"  G-kvalitet:    "
        f"{row['G_percent']:.2f}%"
    )

    print(
        f"  Y-kvalitet:    "
        f"{row['Y_percent']:.2f}%"
    )


# ---------------------------------------------------------
# SPARA JÄMFÖRELSEN
# ---------------------------------------------------------

OUTPUT_FILE = (
    "data/processed/precipitation_station_comparison.csv"
)

comparison.to_csv(
    OUTPUT_FILE,
    index=False
)

print()
print("=" * 80)
print("JÄMFÖRELSE KLAR")
print("=" * 80)

print()
print(
    f"Resultatet sparades till: {OUTPUT_FILE}"
)