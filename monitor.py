import os
import json
import requests
import xml.etree.ElementTree as ET

RSS_URL = "https://marie-sklodowska-curie-actions.ec.europa.eu/news/rss.xml"
STATE_FILE = "state.json"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
}


def load_state():
    if not os.path.exists(STATE_FILE):
        return {"items": {}}
    with open(STATE_FILE, "r") as f:
        return json.load(f)


def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)


def fetch_rss():
    r = requests.get(RSS_URL, headers=HEADERS, timeout=30)

    print("STATUS CODE:", r.status_code)

    if r.status_code != 200:
        print("RESPONSE TEXT:", r.text[:500])
        raise RuntimeError("Failed to load RSS")

    return r.content


def main():
    rss = fetch_rss()
    root = ET.fromstring(rss)

    items = root.findall(".//item")
    print("RSS items encontrados:", len(items))


if __name__ == "__main__":
    main()
