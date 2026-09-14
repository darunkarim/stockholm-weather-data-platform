import os

import pandas as pd

from dotenv import load_dotenv
from azure.storage.filedatalake import DataLakeServiceClient


# ---------------------------------------------------------
# CONFIGURATION
# ---------------------------------------------------------

# Load environment variables from .env
load_dotenv()

# Get Azure connection string
connection_string = os.getenv(
    "AZURE_STORAGE_CONNECTION_STRING"
)

# Azure container name
CONTAINER_NAME = "weather"

# Local complete dataset
INPUT_FILE = (
    "data/raw/stockholm_temperature_complete.csv"
)

# Azure Bronze destination
OUTPUT_PATH = (
    "bronze/temperature/stockholm/"
    "complete/stockholm_temperature_complete.csv"
)


# ---------------------------------------------------------
# VALIDATE CONFIGURATION
# ---------------------------------------------------------

if not connection_string:
    raise ValueError(
        "AZURE_STORAGE_CONNECTION_STRING saknas i .env"
    )


# ---------------------------------------------------------
# LOAD DATA
# ---------------------------------------------------------

def load_data():

    print("=" * 60)
    print("LOADING COMPLETE TEMPERATURE DATA")
    print("=" * 60)

    df = pd.read_csv(
        INPUT_FILE
    )

    print(f"Rows loaded: {len(df):,}")

    return df


# ---------------------------------------------------------
# UPLOAD TO ADLS
# ---------------------------------------------------------

def upload_to_adls(df):

    print()
    print("=" * 60)
    print("UPLOADING TO AZURE DATA LAKE")
    print("=" * 60)

    # Create connection to Azure Data Lake
    service_client = (
        DataLakeServiceClient.from_connection_string(
            connection_string
        )
    )

    # Get the weather container
    file_system_client = (
        service_client.get_file_system_client(
            CONTAINER_NAME
        )
    )

    # Convert DataFrame to CSV
    csv_data = df.to_csv(
        index=False
    )

    # Create file client for the destination
    file_client = (
        file_system_client.get_file_client(
            OUTPUT_PATH
        )
    )

    # Upload CSV to Azure
    file_client.upload_data(
        csv_data,
        overwrite=True,
    )

    print()
    print("Upload successful!")
    print(f"Uploaded file: {OUTPUT_PATH}")


# ---------------------------------------------------------
# MAIN
# ---------------------------------------------------------

def main():

    df = load_data()

    upload_to_adls(df)


if __name__ == "__main__":
    main()