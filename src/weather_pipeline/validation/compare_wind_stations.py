from pathlib import Path
from itertools import combinations

import pandas as pd


INPUT_FILES = {
    "98210": Path("data/raw/stockholm_wind_98210_historical.csv"),
    "97200": Path("data/raw/stockholm_wind_97200_historical.csv"),
    "97400": Path("data/raw/stockholm_wind_97400_historical.csv"),
}

OUTPUT_OVERVIEW = Path(
    "data/processed/wind_station_comparison.csv"
)

OUTPUT_OVERLAP = Path(
    "data/processed/wind_station_overlap_comparison.csv"
)


def load_station_data(station_id, path):
    """
    Läser in en stations vinddata och förbereder den
    för jämförelse med andra stationer.
    """

    print(
        f"Loading station {station_id}: {path}"
    )

    if not path.exists():
        print("  File not found - skipping")
        return None

    df = pd.read_csv(path)

    print(
        f"  Rows loaded: {len(df):,}"
    )

    # Konvertera observationstiden till datetime.
    df["from_utc"] = pd.to_datetime(
        df["from_utc"],
        errors="coerce",
        utc=True,
    )

    # Konvertera vindhastighet till numeriskt värde.
    df["wind_speed_ms"] = pd.to_numeric(
        df["wind_speed_ms"],
        errors="coerce",
    )

    # Ta bort rader som saknar timestamp eller vindhastighet.
    df = df.dropna(
        subset=[
            "from_utc",
            "wind_speed_ms",
        ]
    ).copy()

    # Varje timestamp representerar en observation.
    df["observation_date"] = (
        df["from_utc"].dt.date
    )

    # Kontrollera dubbletter.
    duplicate_count = df.duplicated(
        subset=["from_utc"]
    ).sum()

    if duplicate_count > 0:
        print(
            f"  Warning: {duplicate_count:,} "
            "duplicate timestamps found"
        )

        # Behåll första observationen per timestamp.
        df = df.drop_duplicates(
            subset=["from_utc"],
            keep="first",
        )

    return df


def create_station_overview(stations):
    """
    Skapar en översikt över varje station.

    Coverage beräknas baserat på kalenderdagar,
    medan observations räknas som faktiska mätpunkter.
    """

    rows = []

    for station_id, df in stations.items():

        station_name = df["station_name"].iloc[0]

        first_date = (
            df["observation_date"].min()
        )

        last_date = (
            df["observation_date"].max()
        )

        expected_days = (
            pd.Timestamp(last_date)
            - pd.Timestamp(first_date)
        ).days + 1

        actual_days = (
            df["observation_date"]
            .nunique()
        )

        missing_days = (
            expected_days - actual_days
        )

        coverage = (
            actual_days / expected_days * 100
            if expected_days > 0
            else 0
        )

        g_count = (
            df["quality"]
            .eq("G")
            .sum()
        )

        y_count = (
            df["quality"]
            .eq("Y")
            .sum()
        )

        total = len(df)

        rows.append(
            {
                "station_id": station_id,
                "station_name": station_name,
                "first_date": first_date,
                "last_date": last_date,
                "observations": total,
                "actual_days": actual_days,
                "expected_days": expected_days,
                "missing_days": missing_days,
                "coverage_percent": round(
                    coverage,
                    2,
                ),
                "G_count": g_count,
                "G_percent": round(
                    g_count / total * 100,
                    2,
                ) if total else 0,
                "Y_count": y_count,
                "Y_percent": round(
                    y_count / total * 100,
                    2,
                ) if total else 0,
            }
        )

    return pd.DataFrame(rows)


def compare_station_pair(
    station_a,
    df_a,
    station_b,
    df_b,
):
    """
    Jämför två stationer på exakt observationstid.

    Exempel:

    98210:
    2008-01-01 06:00 → 3.0 m/s

    97200:
    2008-01-01 06:00 → 3.5 m/s

    Dessa två observationer räknas som en match.
    """

    a = df_a[
        ["from_utc", "wind_speed_ms"]
    ].rename(
        columns={
            "wind_speed_ms":
                "wind_speed_a_ms"
        }
    )

    b = df_b[
        ["from_utc", "wind_speed_ms"]
    ].rename(
        columns={
            "wind_speed_ms":
                "wind_speed_b_ms"
        }
    )

    # Matcha stationerna på exakt timestamp.
    merged = pd.merge(
        a,
        b,
        on="from_utc",
        how="inner",
    )

    if merged.empty:
        return None

    merged["difference_ms"] = (
        merged["wind_speed_a_ms"]
        - merged["wind_speed_b_ms"]
    )

    merged["absolute_difference_ms"] = (
        merged["difference_ms"].abs()
    )

    overlap_start = (
        merged["from_utc"].min()
    )

    overlap_end = (
        merged["from_utc"].max()
    )

    overlap_observations = len(merged)

    overlap_days = (
        merged["from_utc"]
        .dt.date
        .nunique()
    )

    correlation = (
        merged["wind_speed_a_ms"]
        .corr(merged["wind_speed_b_ms"])
    )

    return {
        "station_a": station_a,
        "station_b": station_b,
        "overlap_start": overlap_start.date(),
        "overlap_end": overlap_end.date(),
        "overlap_days": overlap_days,
        "overlap_observations": overlap_observations,
        "mean_wind_a_ms": round(
            merged["wind_speed_a_ms"].mean(),
            2,
        ),
        "mean_wind_b_ms": round(
            merged["wind_speed_b_ms"].mean(),
            2,
        ),
        "mean_difference_ms": round(
            merged["difference_ms"].mean(),
            2,
        ),
        "mean_absolute_difference_ms": round(
            merged[
                "absolute_difference_ms"
            ].mean(),
            2,
        ),
        "correlation": round(
            correlation,
            4,
        ) if pd.notna(correlation) else None,
    }


def main():

    print("=" * 80)
    print("STOCKHOLM WEATHER - WIND STATION COMPARISON")
    print("=" * 80)

    stations = {}

    # Läs in alla stationer.
    for station_id, path in INPUT_FILES.items():

        df = load_station_data(
            station_id,
            path,
        )

        if df is not None:
            stations[station_id] = df

    print()

    if len(stations) < 2:
        print(
            "Not enough stations available "
            "for comparison."
        )
        return

    # ---------------------------------------------------------
    # STATION OVERVIEW
    # ---------------------------------------------------------

    print()
    print("=" * 80)
    print("STATION OVERVIEW")
    print("-" * 80)

    overview = create_station_overview(
        stations
    )

    print(
        overview.to_string(
            index=False
        )
    )

    # ---------------------------------------------------------
    # STATION OVERLAP
    # ---------------------------------------------------------

    print()
    print("=" * 80)
    print("STATION OVERLAP COMPARISON")
    print("-" * 80)

    overlap_results = []

    station_pairs = combinations(
        stations.keys(),
        2,
    )

    for station_a, station_b in station_pairs:

        result = compare_station_pair(
            station_a,
            stations[station_a],
            station_b,
            stations[station_b],
        )

        if result is None:
            print(
                f"{station_a} vs {station_b}: "
                "no overlapping observations"
            )
            continue

        overlap_results.append(result)

        print(
            f"{station_a} vs {station_b}: "
            f"{result['overlap_observations']:,} "
            f"observations across "
            f"{result['overlap_days']:,} calendar days"
        )

    overlap_df = pd.DataFrame(
        overlap_results
    )

    print()

    if not overlap_df.empty:
        print(
            overlap_df.to_string(
                index=False
            )
        )

    # ---------------------------------------------------------
    # SAVE RESULTS
    # ---------------------------------------------------------

    OUTPUT_OVERVIEW.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    overview.to_csv(
        OUTPUT_OVERVIEW,
        index=False,
    )

    overlap_df.to_csv(
        OUTPUT_OVERLAP,
        index=False,
    )

    print()
    print("=" * 80)
    print("COMPARISON COMPLETE")
    print("=" * 80)

    print()
    print(
        f"Station comparison saved to: "
        f"{OUTPUT_OVERVIEW}"
    )

    print(
        f"Overlap comparison saved to: "
        f"{OUTPUT_OVERLAP}"
    )


if __name__ == "__main__":
    main()