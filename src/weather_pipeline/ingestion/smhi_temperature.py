import requests
import pandas as pd

# Importerar vår validation-funktion från validation-filen
from src.weather_pipeline.validation.weather_validation import validate_weather_data


# SMHI API för lufttemperatur (parameter 2)
# Station 98230 = Stockholm-Observatoriekullen A
URL = "https://opendata-download-metobs.smhi.se/api/version/1.0/parameter/2/station/98230/period/latest-day/data.json"


def fetch_weather_data():
    # Skickar en GET-request till SMHI
    response = requests.get(URL, timeout=30)

    # Stoppar programmet om API-anropet misslyckades
    response.raise_for_status()

    # Omvandlar SMHI:s JSON-svar till Python-data
    return response.json()


def transform_to_dataframe(data):
    # Hämtar observationslistan från SMHI:s JSON-svar
    observations = data["value"]

    # Gör om observationslistan till en Pandas DataFrame
    df = pd.DataFrame(observations)

    # Konverterar temperatur från text till numeriskt värde
    df["temperature_c"] = pd.to_numeric(
        df["value"],
        errors="coerce"
    )

    # Konverterar Unix-tid i millisekunder till UTC-datum
    df["from_utc"] = pd.to_datetime(
        df["from"],
        unit="ms",
        utc=True
    )

    df["to_utc"] = pd.to_datetime(
        df["to"],
        unit="ms",
        utc=True
    )

    # Konverterar observationsdatumet till datumformat
    df["reference_date"] = pd.to_datetime(
        df["ref"]
    ).dt.date

    # Behåller endast de kolumner vi behöver
    df = df[
        [
            "from_utc",
            "to_utc",
            "reference_date",
            "temperature_c",
            "quality",
        ]
    ]

    return df


if __name__ == "__main__":

    # Hämtar temperaturdata från SMHI
    data = fetch_weather_data()

    # Gör om JSON-datan till en DataFrame
    df = transform_to_dataframe(data)

    # Bekräftar att API-anropet fungerade
    print("SMHI API request successful!")

    # Visar antal rader
    print(f"Number of rows: {len(df)}")

    # Visar kolumnerna
    print("\nColumns:")
    print(df.columns.tolist())

    # Visar datan
    print("\nData:")
    print(df.head())

    # ---------------------------------------------------------
    # VALIDATION
    # ---------------------------------------------------------

    # Kör validation på den transformerade datan
    is_valid, errors = validate_weather_data(df)

    # Skriver ut resultatet från validationen
    print("\nValidation:")

    if is_valid:
        print("Weather data validation passed!")

    else:
        print("Weather data validation failed!")

        # Skriver ut alla validation-fel
        for error in errors:
            print(f"- {error}")