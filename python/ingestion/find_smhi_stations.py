import requests


# SMHI API endpoint for daily mean temperature
URL = "https://opendata-download-metobs.smhi.se/api/version/latest/parameter/5.json"


def get_stockholm_stations():
    """Fetch temperature stations from SMHI and return stations located in Stockholm."""

    response = requests.get(URL, timeout=30)
    response.raise_for_status()

    data = response.json()

    stockholm_stations = []

    for station in data["station"]:
        name = station.get("name", "")
        county = station.get("county", "")

        # Search for stations connected to Stockholm
        if "Stockholm" in name or "Stockholm" in county:
            stockholm_stations.append(station)

    return stockholm_stations


def main():
    stations = get_stockholm_stations()

    print(f"\nFound {len(stations)} Stockholm stations:\n")

    for station in stations:
        print(
            f"ID: {station.get('id')} | "
            f"Name: {station.get('name')} | "
            f"Latitude: {station.get('latitude')} | "
            f"Longitude: {station.get('longitude')} | "
            f"Active: {station.get('active')}"
        )


if __name__ == "__main__":
    main()