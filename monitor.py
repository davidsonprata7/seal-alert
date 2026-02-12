import os
import json
import hashlib
import requests
from bs4 import BeautifulSoup

URL = "https://marie-sklodowska-curie-actions.ec.europa.eu/funding/seal-of-excellence"
STATE_FILE = "state.json"

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}


def load_state():
    if not os.path.exists(STATE_FILE):
        return {"hash": ""}
    with open(STATE_FILE, "r") as f:
        return json.load(f)


def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)


def get_page():
    r = requests.get(URL, headers=HEADERS, timeout=30)
    print("STATUS:", r.status_code)
    return r.text


def get_hash(content):
    return hashlib.sha256(content.encode()).hexdigest()


def extract_content(html):
    soup = BeautifulSoup(html, "html.parser")

    # Título
    title_tag = soup.find("h1")
    title = title_tag.get_text(strip=True) if title_tag else "Update detected"

    # Primeiro parágrafo
    p_tag = soup.find("p")
    summary = p_tag.get_text(strip=True) if p_tag else ""

    # End date (busca texto contendo "End date")
    end_date = "Not found"
    text_blocks = soup.find_all(text=True)

    for t in text_blocks:
        if "End date" in t:
            parent = t.parent.get_text(strip=True)
            end_date = parent.replace("End date:", "").strip()
            break

    return title, summary, end_date


def send_message(token, chat_id, title, summary, end_date):
    api = f"https://api.telegram.org/bot{token}/sendMessage"

    message = (
        f"🚩 {title}\n\n"
        f"📍 {summary}\n\n"
        f"⚠️ End date: ⚠️\n"
        f"✅ {end_date}"
    )

    requests.post(api, data={
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "HTML"
    })


def main():
    token = os.getenv("BOT_TOKEN")
    chat_id = os.getenv("CHAT_ID")

    state = load_state()
    html = get_page()
    current_hash = get_hash(html)

    print("Current hash:", current_hash)

    if state["hash"] != current_hash:
        print("Change detected!")

        title, summary, end_date = extract_content(html)

        send_message(token, chat_id, title, summary, end_date)

        state["hash"] = current_hash
        save_state(state)

    else:
        print("No changes.")


if __name__ == "__main__":
    main()
