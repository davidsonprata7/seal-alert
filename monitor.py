import requests
import os
import json
import re
from datetime import datetime

BOT_TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]

API_URL = "https://marie-sklodowska-curie-actions.ec.europa.eu/eac-api/content?filters[permanent|field_eac_topics][0]=290&language=en&page[limit]=10&sort=date_desc&story_type=pledge&type=story"

BASE_URL = "https://marie-sklodowska-curie-actions.ec.europa.eu"

STATE_FILE = "state.json"


# ======== BANDEIRAS =========
FLAGS = {
    "Estonia": "🇪🇪",
    "Brittany": "🇫🇷",
    "France": "🇫🇷",
    "Germany": "🇩🇪",
    "Spain": "🇪🇸",
    "Italy": "🇮🇹",
    "Portugal": "🇵🇹",
    "Poland": "🇵🇱",
    "Netherlands": "🇳🇱",
    "Belgium": "🇧🇪",
    "Austria": "🇦🇹",
    "Sweden": "🇸🇪",
    "Finland": "🇫🇮",
    "Ireland": "🇮🇪",
}


def detect_flag(title):
    for country, flag in FLAGS.items():
        if country.lower() in title.lower():
            return flag
    return ""


def clean_html(raw_html):
    clean = re.sub('<.*?>', '', raw_html)
    return clean.strip()


def extract_end_date(url):
    try:
        page = requests.get(url)
        html = page.text

        match = re.search(r'End date.*?(\d{1,2}\s+\w+\s+\d{4})', html, re.DOTALL)
        if match:
            return match.group(1)
    except:
        pass

    return "Not found"


def load_state():
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r") as f:
                return json.load(f)
        except:
            pass
    return {"seen_ids": [], "last_heartbeat": 0}


def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f)


def send_photo_with_button(photo_url, caption, link):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"

    payload = {
        "chat_id": CHAT_ID,
        "photo": photo_url,
        "caption": caption,
        "parse_mode": "HTML",
        "reply_markup": json.dumps({
            "inline_keyboard": [
                [{"text": "Learn more", "url": link}]
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


def main():
    state = load_state()
    seen_ids = state["seen_ids"]

    response = requests.get(API_URL)
    data = response.json()

    new_items = []

    for item in data["data"]:
        nid = item["nid"]
        if nid not in seen_ids:
            new_items.append(item)

    if new_items:
        for item in reversed(new_items):
            title = item["title"]
            intro = clean_html(item["intro"])
            link = BASE_URL + item["url"]
            image = item["image"]

            flag = detect_flag(title)
            end_date = extract_end_date(link)

            caption = f"""🚩 <b>{title} {flag}</b>

📍 {intro}

⚠️ <b>End date:</b> ⚠️
✅ <b>{end_date}</b>
"""

            send_photo_with_button(image, caption, link)
            seen_ids.append(item["nid"])

        state["seen_ids"] = seen_ids
        save_state(state)

    # Heartbeat a cada 6h
    now = int(datetime.now().timestamp())
    if now - state.get("last_heartbeat", 0) > 21600:
        send_message("✅ Bot ativo — nenhuma nova publicação encontrada.")
        state["last_heartbeat"] = now
        save_state(state)


if __name__ == "__main__":
    main()
