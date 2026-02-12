import requests
import os
import json
import re
from datetime import datetime
from html import unescape

BOT_TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]

API_URL = "https://marie-sklodowska-curie-actions.ec.europa.eu/eac-api/content?filters[permanent|field_eac_topics][0]=290&language=en&page[limit]=10&sort=date_desc&story_type=pledge&type=story"

BASE_URL = "https://marie-sklodowska-curie-actions.ec.europa.eu"

STATE_FILE = "state.json"


# =========================
# TELEGRAM
# =========================

def send_photo(photo_url, caption, button_url):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"

    payload = {
        "chat_id": CHAT_ID,
        "photo": photo_url,
        "caption": caption,
        "parse_mode": "HTML",
        "reply_markup": json.dumps({
            "inline_keyboard": [
                [
                    {
                        "text": "Learn more",
                        "url": button_url
                    }
                ]
            ]
        })
    }

    requests.post(url, data=payload)


def send_message(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": text
    }
    requests.post(url, data=payload)


# =========================
# UTIL
# =========================

def clean_html(raw_html):
    text = re.sub('<.*?>', '', raw_html)
    text = unescape(text)
    text = text.replace("\xa0", " ")
    return text.strip()


def get_end_date(article_url):
    try:
        r = requests.get(article_url, timeout=10)
        html = r.text

        match = re.search(r'End date.*?(\d{1,2}\s\w+\s\d{4})', html, re.IGNORECASE)
        if match:
            return match.group(1)
        else:
            return "Not specified"

    except:
        return "Not specified"


def get_flag_from_title(title):
    flags = {
        "Estonia": "🇪🇪",
        "Poland": "🇵🇱",
        "Italy": "🇮🇹",
        "France": "🇫🇷",
        "Croatia": "🇭🇷",
        "Brittany": "🇫🇷"
    }

    for country in flags:
        if country.lower() in title.lower():
            return flags[country]

    return "🌍"


# =========================
# STATE
# =========================

def load_state():
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r") as f:
                state = json.load(f)
        except:
            state = {}
    else:
        state = {}

    if "seen_ids" not in state:
        state["seen_ids"] = []

    if "last_heartbeat" not in state:
        state["last_heartbeat"] = 0

    return state


def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f)


# =========================
# MAIN
# =========================

def main():
    state = load_state()
    seen_ids = state["seen_ids"]

    response = requests.get(API_URL)
    data = response.json()

    new_items = []

    for item in data["data"]:
        if item["nid"] not in seen_ids:
            new_items.append(item)

    if new_items:
        for item in reversed(new_items):

            title = item["title"]
            intro = clean_html(item["intro"])
            article_url = BASE_URL + item["url"]
            image = item["image"]

            flag = get_flag_from_title(title)
            end_date = get_end_date(article_url)

            caption = f"""🚩<b>{title}</b> {flag}

📍{intro}

⚠️ <b>End date:</b> ⚠️
✅ <b>{end_date}</b>
"""

            send_photo(image, caption, article_url)

            seen_ids.append(item["nid"])

        state["seen_ids"] = seen_ids
        save_state(state)

    # Heartbeat 3h
    now = int(datetime.now().timestamp())
    if now - state["last_heartbeat"] > 10800:
        send_message("✅ Bot ativo — nenhuma nova publicação encontrada.")
        state["last_heartbeat"] = now
        save_state(state)


if __name__ == "__main__":
    main()
