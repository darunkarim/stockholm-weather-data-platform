import requests


STATION_ID = "98230"
PARAMETER_ID = "2"

URL = (
    f"https://opendata-download-metobs.smhi.se/api/version/latest/"
    f"parameter/{PARAMETER_ID}/station/{STATION_ID}.json"
)


def main():
    print("Fetching available periods from SMHI...")

    response = requests.get(URL, timeout=30)
    response.raise_for_status()

    data = response.json()

    print("\nStation:")
    print(data.get("station"))

    print("\nParameter:")
    print(data.get("parameter"))

    print("\nAvailable periods:\n")

    for period in data.get("period", []):
        print(period)


if __name__ == "__main__":
    main()