import os
import json
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta


RSS_URL = "https://marie-sklodowska-curie-actions.ec.europa.eu/funding/seal-of-excellence/rss.xml"
STATE_FILE = "state.json"

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}


def get_env(name):
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing env variable: {name}")
    return value


def load_state():
    if not os.path.exists(STATE_FILE):
        return {"items": {}}
    with open(STATE_FILE, "r") as f:
        return json.load(f)


def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)


def today_brt():
    return (datetime.utcnow() - timedelta(hours=3)).date()


def country_to_flag(country):
    try:
        import pycountry
        c = pycountry.countries.get(name=country)
        if not c:
            return ""
        return "".join(chr(127397 + ord(x)) for x in c.alpha_2)
    except:
        return ""


def send_telegram(token, chat_id, image_url, caption, link):

    api = f"https://api.telegram.org/bot{token}/sendPhoto"

    keyboard = {
        "inline_keyboard": [
            [{"text": "🔗 Open publication", "url": link}]
        ]
    }

    response = requests.post(
        api,
        data={
            "chat_id": chat_id,
            "caption": caption,
            "reply_markup": json.dumps(keyboard),
            "parse_mode": "HTML"
        },
        files={"photo": requests.get(image_url, headers=HEADERS).content},
        timeout=30
    )

    if response.status_code != 200:
        raise RuntimeError(response.text)


def extract_end_date_and_image(url):

    r = requests.get(url, headers=HEADERS, timeout=30)
    if r.status_code != 200:
        return None, None

    soup = BeautifulSoup(r.text, "html.parser")

    end_date = None

    for field in soup.find_all("div", class_="ecl-description-list__item"):
        label = field.find("dt")
        value = field.find("dd")

        if label and value and "End date" in label.get_text():
            try:
                end_date = datetime.strptime(
                    value.get_text(strip=True),
                    "%d %B %Y"
                ).date()
            except:
                pass

    img_tag = soup.find("img")
    image_url = None
    if img_tag and img_tag.get("src"):
        src = img_tag["src"]
        if src.startswith("http"):
            image_url = src
        else:
            image_url = "https://marie-sklodowska-curie-actions.ec.europa.eu" + src

    return end_date, image_url


def fetch_rss_items():

    r = requests.get(RSS_URL, headers=HEADERS, timeout=30)
    if r.status_code != 200:
        raise RuntimeError("Failed to load RSS")

    soup = BeautifulSoup(r.text, "xml")

    items = []

    for item in soup.find_all("item"):
        title = item.title.text
        link = item.link.text
        items.append({
            "title": title,
            "link": link
        })

    return items


def main():

    token = get_env("BOT_TOKEN")
    chat_id = get_env("CHAT_ID")

    state = load_state()
    today = today_brt()

    items = fetch_rss_items()

    for item in items:

        link = item["link"]
        title = item["title"]

        end_date, image_url = extract_end_date_and_image(link)

        if not end_date:
            continue

        if link not in state["items"]:

            caption = (
                f"🚩<b>{title}</b>\n\n"
                f"⚠️ <b>End date:</b>\n"
                f"✅ {end_date.strftime('%d %B %Y')}"
            )

            if image_url:
                send_telegram(token, chat_id, image_url, caption, link)

            state["items"][link] = {
                "end_date": str(end_date),
                "last_reminder": None
            }

        else:
            entry = state["items"][link]

            if today.weekday() == 5 and end_date > today:
                if entry["last_reminder"] != str(today):

                    caption = (
                        f"⏰ <b>Reminder</b>\n\n"
                        f"🚩<b>{title}</b>\n\n"
                        f"⚠️ <b>End date:</b>\n"
                        f"✅ {end_date.strftime('%d %B %Y')}"
                    )

                    if image_url:
                        send_telegram(token, chat_id, image_url, caption, link)

                    entry["last_reminder"] = str(today)

    save_state(state)


if __name__ == "__main__":
    main()
