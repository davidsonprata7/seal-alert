import os
import json
import requests

BASE = "https://marie-sklodowska-curie-actions.ec.europa.eu"
AJAX_URL = BASE + "/views/ajax"
STATE_FILE = "state.json"

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"
}


def load_state():
    if not os.path.exists(STATE_FILE):
        return {"items": {}}
    with open(STATE_FILE, "r") as f:
        return json.load(f)


def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)


def fetch_items():
    payload = {
        "view_name": "news",
        "view_display_id": "page_1",
        "view_args": "",
        "view_path": "/funding/seal-of-excellence",
        "view_base_path": "news",
    }

    r = requests.post(AJAX_URL, headers=HEADERS, data=payload, timeout=30)

    print("STATUS:", r.status_code)

    if r.status_code != 200:
        print(r.text[:500])
        raise RuntimeError("Failed to fetch AJAX")

    return r.json()


def main():
    data = fetch_items()
    print("AJAX response length:", len(data))


if __name__ == "__main__":
    main()
