from dataclasses import dataclass


@dataclass()
class GA4:
    measurement_id: str
    api_secret: str


def get_ga4(config: dict):
    ga4 = config["ga4"]
    measurement_id = ga4.get("measurement_id") or ""
    api_secret = ga4.get("api_secret") or ""

    if config["bot"]["analytics"] and not (api_secret and measurement_id):
        raise ValueError("No measurement_id or api_secret")
    return GA4(measurement_id=measurement_id, api_secret=api_secret)
