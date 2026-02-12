import os
import json
import requests
from datetime import datetime

BASE = "https://marie-sklodowska-curie-actions.ec.europa.eu"
API = f"{BASE}/jsonapi/node/seal_of_excellence"
STATE_FILE = "state.json"


def load_state():
    if not os.path.exists(STATE_FILE):
        return {"items": {}}
    with open(STATE_FILE, "r") as f:
        return json.load(f)


def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)


def fetch_items():
    r = requests.get(API, timeout=30)
    if r.status_code != 200:
        raise RuntimeError("Failed to fetch JSON API")

    data = r.json()
    return data.get("data", [])


def send_message(token, chat_id, title, link, end_date):
    api = f"https://api.telegram.org/bot{token}/sendPhoto"

    caption = (
        f"🚩 {title} 🇫🇷\n\n"
        f"⚠️ End date:\n"
        f"✅ {end_date}"
    )

    keyboard = {
        "inline_keyboard": [
            [{"text": "🔗 Open publication", "url": link}]
        ]
    }

    requests.post(
        api,
        data={
            "chat_id": chat_id,
            "photo": f"{BASE}/sites/default/files/styles/oe_theme_medium/public/default_images/news-default.jpg",
            "caption": caption,
            "reply_markup": json.dumps(keyboard)
        },
        timeout=30
    )


def main():
    token = os.getenv("BOT_TOKEN")
    chat_id = os.getenv("CHAT_ID")

    state = load_state()
    items = fetch_items()

    print("Items encontrados:", len(items))

    for item in items:
        title = item["attributes"]["title"]
        created = item["attributes"]["created"]

        slug = item["attributes"]["drupal_internal__nid"]
        link = f"{BASE}/node/{slug}"

        if slug not in state["items"]:

            date_obj = datetime.fromisoformat(created.replace("Z", "+00:00"))
            formatted_date = date_obj.strftime("%d %B %Y")

            send_message(token, chat_id, title, link, formatted_date)

            state["items"][slug] = True

    save_state(state)


if __name__ == "__main__":
    main()
