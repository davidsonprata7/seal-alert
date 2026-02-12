import os
import json
import requests
from datetime import datetime, timedelta
from bs4 import BeautifulSoup


BASE_URL = "https://marie-sklodowska-curie-actions.ec.europa.eu"
URL = "https://marie-sklodowska-curie-actions.ec.europa.eu/funding/seal-of-excellence"
STATE_FILE = "state.json"


# ==============================
# UTIL
# ==============================

def get_env(name):
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Variável ausente: {name}")
    return value


def send
