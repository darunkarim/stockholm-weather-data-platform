import requests
import pandas as pd


BASE_URL = "https://opendata-download-metobs.smhi.se/api/version/1.0"

# Temperature and precipitation station
STATION_ID = "98230"
STATION_NAME = "Stockholm-Observatoriekullen A"

# SMHI parameters
TEMPERATURE_PARAMETER = "1"
PRECIPITATION_PARAMETER = "5"
WIND_PARAMETER = "4"

# Wind station
WIND_STATION_ID = "97200"
WIND_STATION_NAME = "Stockholm-Bromma Flygplats"


def fetch_latest_observation(parameter_id, parameter_name, unit):
    """
    Fetch the latest available hourly observation
    from Stockholm-Observatoriekullen A.
    """

    url = (
        f"{BASE_URL}/parameter/{parameter_id}"
        f"/station/{STATION_ID}/period/latest-hour/data.json"
    )

    response = requests.get(url, timeout=30)
    response.raise_for_status()

    data = response.json()
    observations = data.get("value", [])

    if not observations:
        raise ValueError(
            f"No {parameter_name} observations returned from SMHI."
        )

    latest = observations[-1]

    return {
        "parameter": parameter_name,
        "parameter_id": parameter_id,
        "station_id": STATION_ID,
        "station_name": STATION_NAME,
        "value": float(latest["value"]),
        "unit": unit,
        "observation_time": pd.to_datetime(
            latest["date"],
            unit="ms",
            utc=True
        ),
        "reference_date": None,
        "quality": latest.get("quality", ""),
    }


def fetch_latest_temperature():
    """
    Fetch latest hourly temperature.
    """

    return fetch_latest_observation(
        TEMPERATURE_PARAMETER,
        "temperature",
        "°C"
    )


def fetch_latest_precipitation():
    """
    Fetch latest available daily precipitation observation
    from Stockholm-Observatoriekullen A.
    """

    url = (
        f"{BASE_URL}/parameter/{PRECIPITATION_PARAMETER}"
        f"/station/{STATION_ID}/period/latest-day/data.json"
    )

    response = requests.get(url, timeout=30)
    response.raise_for_status()

    data = response.json()
    observations = data.get("value", [])

    if not observations:
        raise ValueError(
            "No precipitation observations returned from SMHI."
        )

    latest = observations[-1]

    return {
        "parameter": "precipitation",
        "parameter_id": PRECIPITATION_PARAMETER,
        "station_id": STATION_ID,
        "station_name": STATION_NAME,
        "value": float(latest["value"]),
        "unit": "mm",
        "observation_time": pd.to_datetime(
            latest["to"],
            unit="ms",
            utc=True
        ),
        "reference_date": latest["ref"],
        "quality": latest.get("quality", ""),
    }


def fetch_latest_wind():
    """
    Fetch latest hourly wind speed observation
    from Stockholm-Bromma Flygplats.
    """

    url = (
        f"{BASE_URL}/parameter/{WIND_PARAMETER}"
        f"/station/{WIND_STATION_ID}/period/latest-hour/data.json"
    )

    response = requests.get(url, timeout=30)
    response.raise_for_status()

    data = response.json()
    observations = data.get("value", [])

    if not observations:
        raise ValueError(
            "No wind observations returned from SMHI."
        )

    latest = observations[-1]

    return {
        "parameter": "wind_speed",
        "parameter_id": WIND_PARAMETER,
        "station_id": WIND_STATION_ID,
        "station_name": WIND_STATION_NAME,
        "value": float(latest["value"]),
        "unit": "m/s",
        "observation_time": pd.to_datetime(
            latest["date"],
            unit="ms",
            utc=True
        ),
        "reference_date": None,
        "quality": latest.get("quality", ""),
    }


def fetch_latest_weather():
    """
    Fetch latest temperature, precipitation and wind
    and return all observations as a pandas DataFrame.
    """

    print("Fetching latest temperature...")
    temperature = fetch_latest_temperature()

    print("Fetching latest precipitation...")
    precipitation = fetch_latest_precipitation()

    print("Fetching latest wind...")
    wind = fetch_latest_wind()

    weather_data = [
        temperature,
        precipitation,
        wind
    ]

    df = pd.DataFrame(weather_data)

    return df


if __name__ == "__main__":

    print("=" * 70)
    print("STOCKHOLM LATEST WEATHER PIPELINE")
    print("=" * 70)

    df = fetch_latest_weather()

    print("\nLATEST WEATHER DATA")
    print("-" * 70)

    print(df.to_string(index=False))

    print("\n" + "=" * 70)
    print("LATEST WEATHER FETCH COMPLETED")
    print("=" * 70)