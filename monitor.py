import os
import json
import requests
from datetime import datetime, timedelta


API_URL = "https://marie-sklodowska-curie-actions.ec.europa.eu/api/content/funding/seal-of-excellence"
STATE_FILE = "state.json"


def get_env(name):
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Variável ausente: {name}")
    return value


def load_state():
    if not os.path.exists(STATE_FILE):
        return {"items": {}}
    with open(STATE_FILE, "r") as f:
        return json.load(f)


def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)


def today_brt():
    return (datetime.utcnow() - timedelta(hours=3)).date()


def country_to_flag(country_name):
    try:
        import pycountry
        country = pycountry.countries.get(name=country_name)
        if not
