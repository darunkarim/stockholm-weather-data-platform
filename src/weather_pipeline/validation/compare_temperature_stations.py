import pandas as pd
from pathlib import Path
from itertools import combinations


# ---------------------------------------------------------
# INPUT FILES
# ---------------------------------------------------------

INPUT_FILES = {
    "98210": Path(
        "data/raw/stockholm_temperature_98210_historical.csv"
    ),
    "98230": Path(
        "data/raw/stockholm_temperature_complete.csv"
    ),
    "97200": Path(
        "data/raw/stockholm_temperature_97200_historical.csv"
    ),
    "97400": Path(
        "data/raw/stockholm_temperature_97400_historical.csv"
    ),
}


# ---------------------------------------------------------
# OUTPUT FILES
# ---------------------------------------------------------

STATION_OUTPUT_FILE = Path(
    "data/processed/temperature_station_comparison.csv"
)

OVERLAP_OUTPUT_FILE = Path(
    "data/processed/temperature_station_overlap_comparison.csv"
)


# ---------------------------------------------------------
# LOAD DATA
# ---------------------------------------------------------

def load_station_data():

    print("=" * 80)
    print("STOCKHOLM WEATHER - TEMPERATURE STATION COMPARISON")
    print("=" * 80)
    print()

    station_data = {}

    for station_id, input_file in INPUT_FILES.items():

        print(
            f"Loading station {station_id}: "
            f"{input_file}"
        )

        if not input_file.exists():

            raise FileNotFoundError(
                f"File not found: {input_file}"
            )

        df = pd.read_csv(
            input_file
        )

        # Convert reference date to datetime.
        df["date"] = pd.to_datetime(
            df["reference_date"],
            errors="coerce",
        )

        # Convert temperature to numeric.
        df["temperature_c"] = pd.to_numeric(
            df["temperature_c"],
            errors="coerce",
        )

        # Make sure required columns exist.
        required_columns = [
            "station_id",
            "station_name",
            "reference_date",
            "temperature_c",
        ]

        missing_columns = [
            column
            for column in required_columns
            if column not in df.columns
        ]

        if missing_columns:

            raise ValueError(
                f"Missing columns in {input_file}: "
                f"{missing_columns}"
            )

        station_data[station_id] = df

        print(
            f"  Rows loaded: {len(df):,}"
        )

    print()

    return station_data


# ---------------------------------------------------------
# ANALYZE INDIVIDUAL STATIONS
# ---------------------------------------------------------

def analyze_stations(station_data):

    results = []

    for station_id, station_df in station_data.items():

        station_df = (
            station_df
            .sort_values("date")
            .copy()
        )

        # -------------------------------------------------
        # BASIC INFORMATION
        # -------------------------------------------------

        observations = len(
            station_df
        )

        first_date = (
            station_df["date"].min()
        )

        last_date = (
            station_df["date"].max()
        )

        # -------------------------------------------------
        # DAILY COVERAGE
        # -------------------------------------------------

        expected_dates = pd.date_range(
            start=first_date,
            end=last_date,
            freq="D",
        )

        actual_dates = pd.DatetimeIndex(
            station_df["date"]
            .dt.normalize()
            .drop_duplicates()
        )

        missing_dates = (
            expected_dates
            .difference(actual_dates)
        )

        expected_days = len(
            expected_dates
        )

        actual_days = len(
            actual_dates
        )

        coverage_percent = (
            actual_days / expected_days * 100
            if expected_days > 0
            else 0
        )

        # -------------------------------------------------
        # DATA QUALITY
        # -------------------------------------------------

        quality_counts = (
            station_df["quality"]
            .value_counts()
        )

        g_count = quality_counts.get(
            "G",
            0,
        )

        y_count = quality_counts.get(
            "Y",
            0,
        )

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

        # -------------------------------------------------
        # STATION NAME
        # -------------------------------------------------

        station_name = (
            station_df["station_name"]
            .iloc[0]
        )

        # -------------------------------------------------
        # RESULT
        # -------------------------------------------------

        results.append(
            {
                "station_id": station_id,
                "station_name": station_name,
                "first_date": first_date.date(),
                "last_date": last_date.date(),
                "observations": observations,
                "expected_days": expected_days,
                "actual_days": actual_days,
                "missing_days": len(
                    missing_dates
                ),
                "coverage_percent": coverage_percent,
                "G_count": g_count,
                "G_percent": g_percent,
                "Y_count": y_count,
                "Y_percent": y_percent,
            }
        )

    comparison = pd.DataFrame(
        results
    )

    comparison = comparison.sort_values(
        "station_id"
    ).reset_index(drop=True)

    return comparison


# ---------------------------------------------------------
# COMPARE OVERLAPPING STATIONS
# ---------------------------------------------------------

def compare_station_overlap(
    station_data,
):

    print()
    print("=" * 80)
    print("OVERLAPPING TEMPERATURE PERIODS")
    print("=" * 80)
    print()

    results = []

    station_ids = list(
        station_data.keys()
    )

    # combinations() creates every unique
    # station pair.
    #
    # Example:
    # 98210 + 98230
    # 98210 + 97200
    # etc.

    for station_a, station_b in combinations(
        station_ids,
        2,
    ):

        df_a = station_data[
            station_a
        ][
            [
                "date",
                "temperature_c",
            ]
        ].copy()

        df_b = station_data[
            station_b
        ][
            [
                "date",
                "temperature_c",
            ]
        ].copy()

        # Rename temperature columns so we know
        # which station each value belongs to.

        df_a = df_a.rename(
            columns={
                "temperature_c":
                    "temperature_a"
            }
        )

        df_b = df_b.rename(
            columns={
                "temperature_c":
                    "temperature_b"
            }
        )

        # -------------------------------------------------
        # INNER JOIN
        # -------------------------------------------------
        #
        # Only dates where BOTH stations have
        # a temperature measurement are kept.
        #

        overlap = pd.merge(
            df_a,
            df_b,
            on="date",
            how="inner",
        )

        if overlap.empty:

            print(
                f"{station_a} vs {station_b}: "
                "NO OVERLAP"
            )

            continue

        # -------------------------------------------------
        # TEMPERATURE DIFFERENCE
        # -------------------------------------------------

        overlap["difference_c"] = (
            overlap["temperature_a"]
            - overlap["temperature_b"]
        )

        overlap["absolute_difference_c"] = (
            overlap["difference_c"]
            .abs()
        )

        # -------------------------------------------------
        # STATISTICS
        # -------------------------------------------------

        mean_a = (
            overlap["temperature_a"]
            .mean()
        )

        mean_b = (
            overlap["temperature_b"]
            .mean()
        )

        mean_difference = (
            overlap["difference_c"]
            .mean()
        )

        mean_absolute_difference = (
            overlap["absolute_difference_c"]
            .mean()
        )

        correlation = (
            overlap[
                [
                    "temperature_a",
                    "temperature_b",
                ]
            ]
            .corr()
            .iloc[0, 1]
        )

        # -------------------------------------------------
        # RESULT
        # -------------------------------------------------

        results.append(
            {
                "station_a": station_a,
                "station_b": station_b,
                "overlap_start": (
                    overlap["date"].min().date()
                ),
                "overlap_end": (
                    overlap["date"].max().date()
                ),
                "overlap_days": len(overlap),
                "mean_temperature_a_c": mean_a,
                "mean_temperature_b_c": mean_b,
                "mean_difference_c": mean_difference,
                "mean_absolute_difference_c": (
                    mean_absolute_difference
                ),
                "correlation": correlation,
            }
        )

        print(
            f"{station_a} vs {station_b}: "
            f"{len(overlap):,} overlapping days"
        )

    comparison = pd.DataFrame(
        results
    )

    return comparison


# ---------------------------------------------------------
# PRINT STATION RESULTS
# ---------------------------------------------------------

def print_station_results(
    comparison,
):

    print()
    print("=" * 80)
    print("STATION OVERVIEW")
    print("-" * 80)

    print(
        comparison.to_string(
            index=False,
            formatters={
                "coverage_percent":
                    "{:.2f}%".format,
                "G_percent":
                    "{:.2f}%".format,
                "Y_percent":
                    "{:.2f}%".format,
            },
        )
    )

    print()


# ---------------------------------------------------------
# PRINT OVERLAP RESULTS
# ---------------------------------------------------------

def print_overlap_results(
    comparison,
):

    print()
    print("=" * 80)
    print("STATION OVERLAP COMPARISON")
    print("-" * 80)

    if comparison.empty:

        print(
            "No overlapping station periods found."
        )

        return

    print(
        comparison.to_string(
            index=False,
            formatters={
                "mean_temperature_a_c":
                    "{:.2f}".format,
                "mean_temperature_b_c":
                    "{:.2f}".format,
                "mean_difference_c":
                    "{:.2f}".format,
                "mean_absolute_difference_c":
                    "{:.2f}".format,
                "correlation":
                    "{:.4f}".format,
            },
        )
    )

    print()


# ---------------------------------------------------------
# SAVE RESULTS
# ---------------------------------------------------------

def save_results(
    station_comparison,
    overlap_comparison,
):

    STATION_OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    station_comparison.to_csv(
        STATION_OUTPUT_FILE,
        index=False,
    )

    overlap_comparison.to_csv(
        OVERLAP_OUTPUT_FILE,
        index=False,
    )

    print("=" * 80)
    print("COMPARISON COMPLETE")
    print("=" * 80)

    print()
    print(
        f"Station comparison saved to: "
        f"{STATION_OUTPUT_FILE}"
    )

    print(
        f"Overlap comparison saved to: "
        f"{OVERLAP_OUTPUT_FILE}"
    )


# ---------------------------------------------------------
# MAIN
# ---------------------------------------------------------

def main():

    station_data = load_station_data()

    station_comparison = (
        analyze_stations(
            station_data
        )
    )

    overlap_comparison = (
        compare_station_overlap(
            station_data
        )
    )

    print_station_results(
        station_comparison
    )

    print_overlap_results(
        overlap_comparison
    )

    save_results(
        station_comparison,
        overlap_comparison,
    )


if __name__ == "__main__":
    main()