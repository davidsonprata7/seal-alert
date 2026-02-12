import os
import json
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta


URL = "https://marie-sklodowska-curie-actions.ec.europa.eu/funding/seal-of-excellence"
STATE_FILE = "state.json"


def get_env(name):
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing env variable: {name}")
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


def country_to_flag(country):
    try:
        import pycountry
        country_obj = pycountry.countries.get(name=country)
        if not country_obj:
            return ""
        return "".join(chr(127397 + ord(c)) for c in country_obj.alpha_2)
    except:
        return ""


def send_telegram(token, chat_id, image_url, caption, link):

    api = f"https://api.telegram.org/bot{token}/sendPhoto"

    keyboard = {
        "inline_keyboard": [
            [{"text": "🔗 Open publication", "url": link}]
        ]
    }

    response = requests.post(
        api,
        data={
            "chat_id": chat_id,
            "caption": caption,
            "reply_markup": json.dumps(keyboard)
        },
        files={"photo": requests.get(image_url).content},
        timeout=30
    )

    if response.status_code != 200:
        raise RuntimeError(response.text)


def parse_page():

    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    response = requests.get(URL, headers=headers, timeout=30)

    if response.status_code != 200:
        raise RuntimeError("Failed to load page")

    soup = BeautifulSoup(response.text, "html.parser")

    cards = soup.select(".ecl-content-block")

    results = []

    for card in cards:

        title_tag = card.select_one("h2 a")
        if not title_tag:
            continue

        title = title_tag.get_text(strip=True)
        link = "https://marie-sklodowska-curie-actions.ec.europa.eu" + title_tag["href"]

        description_tag = card.select_one(".ecl-content-block__description")
        description = description_tag.get_text(strip=True) if description_tag else ""

        img_tag = card.select_one("img")
        image = "https://marie-sklodowska-curie-actions.ec.europa.eu" + img_tag["src"] if img_tag else None

        country = ""
        if " in " in title:
            country = title.split(" in ")[-1]

        end_date = None
        if "End date:" in description:
            try:
                end_str = description.split("End date:")[-1].strip()
                end
