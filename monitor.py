import requests
import os
import json
import re
from datetime import datetime

BOT_TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]

API_URL = "https://marie-sklodowska-curie-actions.ec.europa.eu/eac-api/content?filters[permanent|field_eac_topics][0]=290&language=en&page[limit]=10&sort=date_desc&story_type=pledge&type=story"

STATE_FILE = "state.json"


def send_message(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": False
    }
    requests.post(url, data=payload)


def send_photo(photo_url, caption):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
    payload = {
        "chat_id": CHAT_ID,
        "photo": photo_url,
        "caption": caption,
        "parse_mode": "HTML"
    }
    requests.post(url, data=payload)


def clean_html(raw_html):
    clean = re.sub('<.*?>', '', raw_html)
    return clean.strip()


def load_state():
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r") as f:
                state = json.load(f)
        except:
            state = {"seen_ids": [], "last_heartbeat": 0}
    else:
        state = {"seen_ids": [], "last_heartbeat": 0}

    if "seen_ids" not in state:
        state["seen_ids"] = []

    if "last_heartbeat" not in state:
        state["last_heartbeat"] = 0

    return state


def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f)


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
            link = "https://marie-sklodowska-curie-actions.ec.europa.eu" + item["url"]
            image = item["image"]

            caption = f"""🚀 <b>New Seal of Excellence published</b>

<b>{title}</b>

{intro}

🔗 <a href="{link}">Learn more</a>
"""

            send_photo(image, caption)
            seen_ids.append(item["nid"])

        state["seen_ids"] = seen_ids
        save_state(state)

    # Heartbeat a cada 3 horas
    now = int(datetime.now().timestamp())
    if now - state["last_heartbeat"] > 10800:
        send_message("✅ Bot ativo — nenhuma nova publicação encontrada.")
        state["last_heartbeat"] = now
        save_state(state)


if __name__ == "__main__":
    main()
