import os
import json
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta


BASE = "https://marie-sklodowska-curie-actions.ec.europa.eu"
LIST_URL = f"{BASE}/funding/seal-of-excellence"
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


def send_telegram(token, chat_id, text, image_url, link):

    url = f"https://api.telegram.org/bot{token}/sendPhoto"

    keyboard = {
        "inline_keyboard": [
            [{"text": "🔗 Open publication", "url": link}]
        ]
    }

    response = requests.post(
        url,
        data={
            "chat_id": chat_id,
            "caption": text,
            "reply_markup": json.dumps(keyboard),
            "parse_mode": "HTML"
        },
        files={"photo": requests.get(image_url, headers=HEADERS).content},
        timeout=30
    )

    if response.status_code != 200:
        raise RuntimeError(response.text)


def get_article_links():

    r = requests.get(LIST_URL, headers=HEADERS, timeout=30)
    if r.status_code != 200:
        raise RuntimeError("Failed to load listing page")

    soup = BeautifulSoup(r.text, "html.parser")

    links = []

    for a in soup.find_all("a", href=True):
        href = a["href"]

        if "/funding/seal-of-excellence/" in href and href.count("/") > 3:
            full = BASE + href if href.startswith("/") else href
            if full not in links:
                links.append(full)

    return links


def parse_article(url):

    r = requests.get(url, headers=HEADERS, timeout=30)
    if r.status_code != 200:
        return None

    soup = BeautifulSoup(r.text, "html.parser")

    title_tag = soup.find("h1")
    if not title_tag:
        return None

    title = title_tag.get_text(strip=True)

    end_date = None

    rows = soup.find_all("div", class_="ecl-description-list__item")

    for row in rows:
        dt = row.find("dt")
        dd = row.find("dd")

        if dt and dd and "End date" in dt.get_text():
            try:
                end_date = datetime.strptime(
                    dd.get_text(strip=True),
                    "%d %B %Y"
                ).date()
            except:
                pass

    if not end_date:
        return None

    img = soup.find("img")
    image_url = None

    if img and img.get("src"):
        src = img["src"]
        if src.startswith("http"):
            image_url = src
        else:
            image_url = BASE + src

    return {
        "title": title,
        "end_date": end_date,
        "image": image_url
    }


def main():

    token = get_env("BOT_TOKEN")
    chat_id = get_env("CHAT_ID")

    state = load_state()
    today = today_brt()

    links = get_article_links()

    for link in links:

        article = parse_article(link)
        if not article:
            continue

        if link not in state["items"]:

            caption = (
                f"🚩 <b>{article['title']}</b>\n\n"
                f"⚠️ <b>End date:</b>\n"
                f"✅ {article['end_date'].strftime('%d %B %Y')}"
            )

            if article["image"]:
                send_telegram(token, chat_id, caption, article["image"], link)

            state["items"][link] = {
                "end_date": str(article["end_date"]),
                "last_reminder": None
            }

        else:
            entry = state["items"][link]

            if today.weekday() == 5 and article["end_date"] > today:
                if entry["last_reminder"] != str(today):

                    caption = (
                        f"⏰ <b>Reminder</b>\n\n"
                        f"🚩 <b>{article['title']}</b>\n\n"
                        f"⚠️ <b>End date:</b>\n"
                        f"✅ {article['end_date'].strftime('%d %B %Y')}"
                    )

                    if article["image"]:
                        send_telegram(token, chat_id, caption, article["image"], link)

                    entry["last_reminder"] = str(today)

    save_state(state)


if __name__ == "__main__":
    main()
