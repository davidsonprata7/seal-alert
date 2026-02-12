import os
import json
import requests
import xml.etree.ElementTree as ET

RSS_URL = "https://marie-sklodowska-curie-actions.ec.europa.eu/news/rss.xml"
STATE_FILE = "state.json"


def load_state():
    if not os.path.exists(STATE_FILE):
        return {"items": {}}
    with open(STATE_FILE, "r") as f:
        return json.load(f)


def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)


def fetch_rss():
    r = requests.get(RSS_URL, timeout=30)
    if r.status_code != 200:
        raise RuntimeError("Failed to load RSS")
    return r.content


def send_message(token, chat_id, title, link, pub_date):
    api = f"https://api.telegram.org/bot{token}/sendPhoto"

    caption = (
        f"🚩 {title}\n\n"
        f"⚠️ Publication date:\n"
        f"✅ {pub_date}"
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
            "photo": "https://marie-sklodowska-curie-actions.ec.europa.eu/sites/default/files/styles/oe_theme_medium/public/default_images/news-default.jpg",
            "caption": caption,
            "reply_markup": json.dumps(keyboard)
        },
        timeout=30
    )


def main():
    token = os.getenv("BOT_TOKEN")
    chat_id = os.getenv("CHAT_ID")

    state = load_state()

    rss_content = fetch_rss()
    root = ET.fromstring(rss_content)

    items = root.findall(".//item")

    print("Total RSS items:", len(items))

    for item in items:
        title = item.find("title").text
        link = item.find("link").text
        pub_date = item.find("pubDate").text

        if "/funding/seal-of-excellence" in link:

            if link not in state["items"]:

                send_message(token, chat_id, title, link, pub_date)
                state["items"][link] = True

    save_state(state)


if __name__ == "__main__":
    main()
