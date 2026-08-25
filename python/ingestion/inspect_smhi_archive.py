import requests
import json


STATION_ID = "98230"
PARAMETER_ID = "2"
PERIOD = "corrected-archive"

URL = (
    f"https://opendata-download-metobs.smhi.se/api/version/1.0/"
    f"parameter/{PARAMETER_ID}/station/{STATION_ID}/"
    f"period/{PERIOD}.json"
)


def main():

    print("Fetching SMHI archive metadata...")

    response = requests.get(
        URL,
        timeout=30
    )

    response.raise_for_status()

    data = response.json()

    print("\nTop-level keys:")
    print(data.keys())

    print("\nComplete archive metadata:")
    print(
        json.dumps(
            data,
            indent=4,
            ensure_ascii=False
        )
    )


if __name__ == "__main__":
    main()