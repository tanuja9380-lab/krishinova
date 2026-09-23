import requests


GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
WEATHER_URL = "https://api.open-meteo.com/v1/forecast"


def get_coordinates(location: str):
    """
    Convert a city/location name into latitude and longitude.
    """

    response = requests.get(
        GEOCODING_URL,
        params={
            "name": location,
            "count": 1,
            "language": "en",
            "format": "json"
        },
        timeout=10
    )

    response.raise_for_status()

    data = response.json()

    results = data.get("results", [])

    if not results:
        raise ValueError(
            f"Location '{location}' could not be found."
        )

    result = results[0]

    return {
        "name": result.get("name"),
        "country": result.get("country"),
        "latitude": result["latitude"],
        "longitude": result["longitude"]
    }


def get_weather(location: str):
    """
    Get current weather and short-term rainfall information
    for a given location.
    """

    coordinates = get_coordinates(location)

    response = requests.get(
        WEATHER_URL,
        params={
            "latitude": coordinates["latitude"],
            "longitude": coordinates["longitude"],

            "current": (
                "temperature_2m,"
                "relative_humidity_2m,"
                "precipitation,"
                "rain"
            ),

            "daily": "precipitation_probability_max",

            "forecast_days": 3,

            "timezone": "auto"
        },
        timeout=10
    )

    response.raise_for_status()

    data = response.json()

    current = data.get("current", {})
    daily = data.get("daily", {})

    precipitation_probability = daily.get(
        "precipitation_probability_max",
        []
    )

    rain_probability = (
        max(precipitation_probability)
        if precipitation_probability
        else 0
    )

    current_rain = current.get("rain", 0) or 0

    rainfall_expected = (
        current_rain > 0
        or rain_probability >= 40
    )

    return {
        "location": coordinates["name"],
        "country": coordinates["country"],
        "latitude": coordinates["latitude"],
        "longitude": coordinates["longitude"],

        "temperature_c": current.get(
            "temperature_2m"
        ),

        "humidity_percent": current.get(
            "relative_humidity_2m"
        ),

        "precipitation_mm": current.get(
            "precipitation"
        ),

        "rain_mm": current_rain,

        "rain_probability_percent": rain_probability,

        "rainfall_expected": rainfall_expected
    }