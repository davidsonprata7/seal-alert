import os
import json
import hashlib
import requests

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


def get_page_hash():
    r = requests.get(URL, headers=HEADERS, timeout=30)
    print("STATUS:", r.status_code)
    content = r.text
    return hashlib.sha256(content.encode()).hexdigest()


def send_message(token, chat_id):
    api = f"https://api.telegram.org/bot{token}/sendMessage"

    text = (
        "🚩 Update detected on Seal of Excellence page!\n\n"
        f"{URL}"
    )

    requests.post(api, data={
        "chat_id": chat_id,
        "text": text
    })


def main():
    token = os.getenv("BOT_TOKEN")
    chat_id = os.getenv("CHAT_ID")

    state = load_state()
    current_hash = get_page_hash()

    print("Current hash:", current_hash)

    if state["hash"] != current_hash:
        print("Change detected!")
        send_message(token, chat_id)
        state["hash"] = current_hash
        save_state(state)
    else:
        print("No changes.")


if __name__ == "__main__":
    main()
