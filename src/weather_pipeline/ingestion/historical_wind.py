import sys
from pathlib import Path
from io import StringIO

import pandas as pd
import requests


PARAMETER_ID = "4"

STATIONS = {
    "98210": "Stockholm-Observatoriekullen",
    "97200": "Stockholm-Bromma Flygplats",
    "97400": "Stockholm-Arlanda Flygplats",
}


def fetch_wind_data(station_id):
    """
    Hämtar historisk vinddata från SMHI:s corrected archive.

    Vindfilen har ett annat format än temperaturfilen:
    - Datum
    - Tid (UTC)
    - Vindhastighet
    - Kvalitet

    Därför skapar vi själva en timestamp från Datum + Tid.
    """

    station_name = STATIONS[station_id]

    url = (
        f"https://opendata-download-metobs.smhi.se/"
        f"api/version/1.0/parameter/{PARAMETER_ID}/"
        f"station/{station_id}/period/corrected-archive/data.csv"
    )

    print("=" * 70)
    print("SMHI HISTORICAL WIND DATA")
    print("=" * 70)
    print(f"Station: {station_id} - {station_name}")
    print(f"Parameter: {PARAMETER_ID} - Vindhastighet")
    print()
    print("Fetching data from:")
    print(url)
    print()

    response = requests.get(url, timeout=60)
    response.raise_for_status()

    # SMHI använder UTF-8 med BOM i dessa filer.
    text = response.content.decode("utf-8-sig")

    lines = text.splitlines()

    # Hitta raden där själva mätdata börjar.
    header_index = None

    for i, line in enumerate(lines):
        if "Vindhastighet" in line and "Kvalitet" in line:
            header_index = i
            break

    if header_index is None:
        print("Could not find measurement header.")
        print()
        print("First 30 lines from SMHI:")
        for line in lines[:30]:
            print(line)

        raise ValueError(
            "Could not find the measurement header in the SMHI file."
        )

    # Läs CSV:n från den riktiga header-raden.
    data_text = "\n".join(lines[header_index:])

    df = pd.read_csv(
        StringIO(data_text),
        sep=";",
    )

    print("SMHI columns found:")
    for column in df.columns:
        print(f"  {column}")

    print()

    # Kontrollera att de kolumner vi behöver finns.
    required_columns = [
        "Datum",
        "Tid (UTC)",
        "Vindhastighet",
        "Kvalitet",
    ]

    missing_columns = [
        column for column in required_columns
        if column not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            f"Missing required SMHI columns: {missing_columns}"
        )

    print("Detected columns:")
    print("  Date:        Datum")
    print("  Time:        Tid (UTC)")
    print("  Wind:        Vindhastighet")
    print("  Quality:     Kvalitet")
    print()

    # Skapa en UTC-timestamp från Datum + Tid.
    df["datetime_utc"] = pd.to_datetime(
        df["Datum"].astype(str) + " " + df["Tid (UTC)"].astype(str),
        errors="coerce",
        utc=True,
    )

    # Vindhastighet till numeriskt format.
    df["wind_speed_ms"] = pd.to_numeric(
        df["Vindhastighet"],
        errors="coerce",
    )

    # Kvalitet behålls som den kommer från SMHI.
    df["quality"] = df["Kvalitet"]

    # Skapa standardiserad struktur för vårt projekt.
    result = pd.DataFrame(
        {
            "station_id": station_id,
            "station_name": station_name,
            "parameter_id": PARAMETER_ID,
            "from_utc": df["datetime_utc"],
            "to_utc": df["datetime_utc"],
            "reference_date": df["datetime_utc"].dt.date,
            "wind_speed_ms": df["wind_speed_ms"],
            "quality": df["quality"],
        }
    )

    # Ta bort rader där datum/tid eller vindhastighet saknas.
    result = result.dropna(
        subset=["from_utc", "wind_speed_ms"]
    ).copy()

    # Gör reference_date till datetime.
    result["reference_date"] = pd.to_datetime(
        result["reference_date"]
    )

    # Sortera kronologiskt.
    result = result.sort_values(
        "from_utc"
    ).reset_index(drop=True)

    print("=" * 70)
    print("VALIDATION")
    print("=" * 70)

    print(f"Rows:          {len(result):,}")

    if len(result) > 0:
        print(
            f"Start datetime: {result['from_utc'].min()}"
        )
        print(
            f"End datetime:   {result['from_utc'].max()}"
        )

    print(
        f"Missing wind:   {result['wind_speed_ms'].isna().sum():,}"
    )

    print(
        f"Missing dates:  {result['reference_date'].isna().sum():,}"
    )

    print(
        f"Duplicate rows: {result.duplicated().sum():,}"
    )

    print()
    print("Quality:")
    print(result["quality"].value_counts(dropna=False))
    print()

    # Kontrollera att vi inte har negativa vindhastigheter.
    negative_wind = (
        result["wind_speed_ms"] < 0
    ).sum()

    print(
        f"Negative wind values: {negative_wind:,}"
    )

    if negative_wind > 0:
        raise ValueError(
            "Validation failed: negative wind speeds found."
        )

    print()

    # Sökväg till outputfilen.
    output_path = Path(
        f"data/raw/stockholm_wind_{station_id}_historical.csv"
    )

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    result.to_csv(
        output_path,
        index=False,
    )

    print("=" * 70)
    print("SUCCESS")
    print("=" * 70)
    print(f"Saved to: {output_path}")
    print(f"Rows saved: {len(result):,}")
    print()

    return result


def main():

    if len(sys.argv) != 2:
        print("Usage:")
        print(
            "python src/weather_pipeline/ingestion/"
            "historical_wind.py <station_id>"
        )
        print()
        print("Available stations:")

        for station_id, station_name in STATIONS.items():
            print(
                f"  {station_id} - {station_name}"
            )

        sys.exit(1)

    station_id = sys.argv[1]

    if station_id not in STATIONS:
        print(f"Unknown station: {station_id}")
        print()
        print("Available stations:")

        for station_id, station_name in STATIONS.items():
            print(
                f"  {station_id} - {station_name}"
            )

        sys.exit(1)

    fetch_wind_data(station_id)


if __name__ == "__main__":
    main()