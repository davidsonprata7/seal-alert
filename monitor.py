import requests
import os
import json
import re
import html
from datetime import datetime

BOT_TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]

API_URL = "https://marie-sklodowska-curie-actions.ec.europa.eu/eac-api/content?filters[permanent|field_eac_topics][0]=290&language=en&page[limit]=10&sort=date_desc&story_type=pledge&type=story"

STATE_FILE = "state.json"


# ---------------- TELEGRAM ---------------- #

def send_message(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": False
    }
    requests.post(url, data=payload)


# ---------------- HELPERS ---------------- #

def clean_html(raw_html):
    text = re.sub('<.*?>', '', raw_html)
    text = html.unescape(text)
    return text.strip()


def extract_end_date(url):
    try:
        r = requests.get(url)
        html_content = r.text

        match = re.search(r'End date:</strong>\s*([^<]+)', html_content)
        if match:
            return match.group(1).strip()
        else:
            return "Not specified"
    except:
        return "Not specified"


def get_flag(title):
    countries = {
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
        "Sweden": "🇸🇪",
        "Finland": "🇫🇮",
        "Ireland": "🇮🇪",
        "Austria": "🇦🇹",
        "Czech": "🇨🇿",
        "Hungary": "🇭🇺",
        "Romania": "🇷🇴",
        "Croatia": "🇭🇷",
        "Lithuania": "🇱🇹",
        "Latvia": "🇱🇻",
        "Slovenia": "🇸🇮",
        "Slovakia": "🇸🇰",
        "Bulgaria": "🇧🇬",
        "Greece": "🇬🇷",
        "Denmark": "🇩🇰"
    }

    for country, flag in countries.items():
        if country.lower() in title.lower():
            return flag

    return ""


# ---------------- STATE ---------------- #

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


# ---------------- MAIN ---------------- #

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

            flag = get_flag(title)
            end_date = extract_end_date(link)

            message = f"""
🚩 <b>{title} {flag}</b>

📍 {intro}

⚠️ <b>End date:</b> ⚠️
✅ {end_date}

🔗 <a href="{link}">Learn more</a>
"""

            send_message(message)

            seen_ids.append(item["nid"])

        state["seen_ids"] = seen_ids
        save_state(state)

    # Heartbeat a cada 3 horas
    now = int(datetime.now().timestamp())
    if now - state.get("last_heartbeat", 0) > 10800:
        send_message("✅ Bot ativo — nenhuma nova publicação encontrada.")
        state["last_heartbeat"] = now
        save_state(state)


if __name__ == "__main__":
    main()
