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


def get_flag(country_name):
    try:
        import pycountry
        country = pycountry.countries.get(name=country_name)
        if not country:
            return ""
        code = country.alpha_2
        return "".join(chr(127397 + ord(c)) for c in code)
    except:
        return ""


def send_telegram(token, chat_id, title, description, end_date, url, image_url, flag):

    caption = (
        f"🚩{title} {flag}\n\n"
        f"📍{description}\n\n"
        f"⚠️ End date:\n"
        f"✅ {end_date}"
    )

    telegram_url = f"https://api.telegram.org/bot{token}/sendPhoto"

    requests.post(
        telegram_url,
        data={
            "chat_id": chat_id,
            "caption": caption,
            "parse_mode": "HTML",
            "reply_markup": json.dumps({
                "inline_keyboard":_
