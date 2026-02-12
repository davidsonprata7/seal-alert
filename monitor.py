import os
import json
import requests
from bs4 import BeautifulSoup

BASE = "https://marie-sklodowska-curie-actions.ec.europa.eu"
URL = f"{BASE}/funding/seal-of-excellence"
STATE_FILE = "state.json"

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}


def load_state():
    if not os.path.exists(STATE_FILE):
        return {"items": {}}
    with open(STATE_FILE, "r") as f:
        return json.load(f)


def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)


def send_message(token, chat_id, text, link):
    api = f"https://api.telegram.org/bot{token}/sendMessage"

    keyboard = {
        "inline_keyboard": [
            [{"text": "🔗 Open publication", "url": link}]
        ]
    }

    requests.post(
        api,
        data={
            "chat_id": chat_id,
            "text": text,
            "reply_markup": json.dumps(keyboard)
        },
        timeout=30
    )


def get_links():

    r = requests.get(URL, headers=HEADERS, timeout=30)
    soup = BeautifulSoup(r.text, "html.parser")

    links = []

    for a in soup.find_all("a", href=True):
        href = a["href"]

        if "/funding/seal-of-excellence/" in href and href.count("/") > 3:
            full = BASE + href if href.startswith("/") else href
            if full not in links:
                links.append(full)

    return links


def main():

    token = os.getenv("BOT_TOKEN")
    chat_id = os.getenv("CHAT_ID")

    state = load_state()

    links = get_links()

    print("Links encontrados:", len(links))

    for link in links:

        if link not in state["items"]:

            title = link.split("/")[-1].replace("-", " ").title()

            message = f"🚩 New publication detected:\n\n{title}"

            send_message(token, chat_id, message, link)

            state["items"][link] = True

    save_state(state)


if __name__ == "__main__":
    main()
