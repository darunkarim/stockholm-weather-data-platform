import os
from io import StringIO

from dotenv import load_dotenv
from azure.storage.filedatalake import DataLakeServiceClient

# Hämtar och transformerar aktuell temperaturdata från SMHI
from src.weather_pipeline.ingestion.smhi_temperature import (
    fetch_weather_data,
    transform_to_dataframe,
)

# Kontrollerar att datan är korrekt innan uppladdning
from src.weather_pipeline.validation.weather_validation import (
    validate_weather_data,
)


# Läser in variabler från .env
load_dotenv()

# Hämtar Azure connection string från .env
connection_string = os.getenv(
    "AZURE_STORAGE_CONNECTION_STRING"
)

# Namnet på containern i Azure
CONTAINER_NAME = "weather"


# Stoppar programmet om connection string saknas
if not connection_string:
    raise ValueError(
        "AZURE_STORAGE_CONNECTION_STRING saknas i .env"
    )


def upload_to_adls(df):
    # Skapar anslutning till Azure Data Lake
    service_client = DataLakeServiceClient.from_connection_string(
        connection_string
    )

    # Hämtar containern som heter weather
    file_system_client = service_client.get_file_system_client(
        CONTAINER_NAME
    )

    # Hämtar datumet från den transformerade datan
    reference_date = df["reference_date"].iloc[0]

    # Skapar mappar baserat på år och månad
    year = reference_date.year
    month = f"{reference_date.month:02d}"

    # Sökvägen till Bronze-lagret
    directory_path = (
        f"bronze/temperature/stockholm/{year}/{month}"
    )

    # Filnamn baserat på observationsdatum
    file_name = (
        f"temperature_{reference_date}.csv"
    )

    # Fullständig sökväg i Azure Data Lake
    file_path = f"{directory_path}/{file_name}"

    # Gör om DataFrame till CSV-text
    csv_data = df.to_csv(index=False)

    # Skapar filklienten för filen i Azure
    file_client = file_system_client.get_file_client(
        file_path
    )

    # Laddar upp CSV-filen till Azure
    file_client.upload_data(
        csv_data,
        overwrite=True,
    )

    print("Upload successful!")
    print(f"Uploaded file: {file_path}")


if __name__ == "__main__":

    # Hämtar aktuell data från SMHI
    data = fetch_weather_data()

    # Gör om SMHI:s JSON till en DataFrame
    df = transform_to_dataframe(data)

    print("SMHI data fetched successfully!")
    print(f"Number of rows: {len(df)}")

    # Kör validation innan uppladdning
    is_valid, errors = validate_weather_data(df)

    if not is_valid:
        print("Validation failed!")

        for error in errors:
            print(f"- {error}")

        raise ValueError(
            "Weather data failed validation"
        )

    print("Validation passed!")

    # Laddar upp den validerade datan till Bronze
    upload_to_adls(df)