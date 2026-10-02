from datetime import datetime, timezone

from src.weather_pipeline.ingestion.latest_weather import (
    fetch_latest_weather,
)

from src.weather_pipeline.load.load_latest_weather_to_sql import (
    load_latest_weather,
)


def validate_latest_weather(df):
    """
    Validate the latest weather dataset before loading it to Azure SQL.
    """

    print("\nValidating latest weather data...")

    required_parameters = {
        "temperature",
        "precipitation",
        "wind_speed",
    }

    actual_parameters = set(df["parameter"])

    missing_parameters = required_parameters - actual_parameters

    if missing_parameters:
        raise ValueError(
            f"Missing weather parameters: {missing_parameters}"
        )

    if len(df) != 3:
        raise ValueError(
            f"Expected 3 weather observations, received {len(df)}."
        )

    if df["value"].isna().any():
        raise ValueError(
            "One or more weather observations contain missing values."
        )

    if df["observation_time"].isna().any():
        raise ValueError(
            "One or more observations are missing observation_time."
        )

    print("Validation passed.")
    print("Temperature:   available")
    print("Precipitation: available")
    print("Wind speed:    available")


def run_pipeline():
    """
    Run the complete latest weather pipeline:

    SMHI API
        ->
    Pandas DataFrame
        ->
    Validation
        ->
    Azure SQL
    """

    pipeline_start = datetime.now(timezone.utc)

    print("=" * 70)
    print("STOCKHOLM LATEST WEATHER PIPELINE")
    print("=" * 70)

    print(
        f"\nPipeline started: "
        f"{pipeline_start.strftime('%Y-%m-%d %H:%M:%S')} UTC"
    )

    try:

        # ====================================================
        # 1. INGEST
        # ====================================================

        print("\n[1/3] INGESTION")
        print("-" * 70)

        weather_df = fetch_latest_weather()

        print(f"\nObservations fetched: {len(weather_df)}")

        print("\nLatest weather:")
        print(weather_df.to_string(index=False))

        # ====================================================
        # 2. VALIDATE
        # ====================================================

        print("\n[2/3] VALIDATION")
        print("-" * 70)

        validate_latest_weather(weather_df)

        # ====================================================
        # 3. LOAD
        # ====================================================

        print("\n[3/3] AZURE SQL LOAD")
        print("-" * 70)

        rows_loaded = load_latest_weather(weather_df)

        # ====================================================
        # COMPLETE
        # ====================================================

        pipeline_end = datetime.now(timezone.utc)

        duration = (
            pipeline_end - pipeline_start
        ).total_seconds()

        print("\n" + "=" * 70)
        print("PIPELINE COMPLETED SUCCESSFULLY")
        print("=" * 70)

        print(f"\nRows loaded: {rows_loaded}")

        print(
            f"Completed: "
            f"{pipeline_end.strftime('%Y-%m-%d %H:%M:%S')} UTC"
        )

        print(
            f"Duration: {duration:.2f} seconds"
        )

        return True

    except Exception as error:

        pipeline_end = datetime.now(timezone.utc)

        duration = (
            pipeline_end - pipeline_start
        ).total_seconds()

        print("\n" + "=" * 70)
        print("PIPELINE FAILED")
        print("=" * 70)

        print(f"\nError: {error}")
        print(f"Duration: {duration:.2f} seconds")

        raise


if __name__ == "__main__":
    run_pipeline()