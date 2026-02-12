import os
import json
import requests
from datetime import datetime, timedelta


BASE = "https://marie-sklodowska-curie-actions.ec.europa.eu"
API = f"{BASE}/jsonapi/node/article"
STATE_FILE = "state.json"


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
            "caption": caption,
            "reply_markup": json.dumps(keyboard)
        },
        files={"photo": requests.get(image_url).content},
        timeout=30
    )

    if response.status_code != 200:
        raise RuntimeError(response.text)


def fetch_articles():

    params = {
        "filter[field_tags.name]": "Seal of Excellence",
        "sort": "-created",
        "page[limit]": 20
    }

    headers = {"User-Agent": "Mozilla/5.0"}

    r = requests.get(API, params=params, headers=headers, timeout=30)

    if r.status_code != 200:
        raise RuntimeError("Failed to fetch articles")

    return r.json().get("data", [])


def main():

    token = get_env("BOT_TOKEN")
    chat_id = get_env("CHAT_ID")

    state = load_state()
    today = today_brt()

    articles = fetch_articles()

    for article in articles:

        attr = article["attributes"]

        title = attr.get("title")
        path = attr.get("path", {}).get("alias")

        if not path:
            continue

        link = BASE + path

        body = attr.get("body", {}).get("value", "")

        if "End date" not in body:
            continue

        # extrair End date do HTML
        try:
            import re
            match = re.search(r"End date:\s*([0-9]{1,2}\s+[A-Za-z]+\s+[0-9]{4})", body)
            if not match:
                continue
            end_date_obj = datetime.strptime(match.group(1), "%d %B %Y").date()
        except:
            continue

        image_url = None
        if "relationships" in article and "field_image" in article["relationships"]:
            img_rel = article["relationships"]["field_image"]["data"]
            if img_rel:
                file_id = img_rel["id"]
                file_url = f"{BASE}/jsonapi/file/file/{file_id}"
                img_response = requests.get(file_url, timeout=30)
                if img_response.status_code == 200:
                    img_data = img_response.json()["data"]["attributes"]
                    image_url = BASE + img_data["uri"]["url"]

        if link not in state["items"]:

            caption = (
                f"🚩{title}\n\n"
                f"⚠️ End date:⚠️\n"
                f"✅ {end_date_obj.strftime('%d %B %Y')}"
            )

            if image_url:
                send_telegram(token, chat_id, image_url, caption, link)

            state["items"][link] = {
                "end_date": str(end_date_obj),
                "last_reminder": None
            }

        else:
            entry = state["items"][link]

            if today.weekday() == 5 and end_date_obj > today:
                if entry["last_reminder"] != str(today):

                    caption = (
                        f"⏰ Reminder\n\n"
                        f"🚩{title}\n\n"
                        f"⚠️ End date:⚠️\n"
                        f"✅ {end_date_obj.strftime('%d %B %Y')}"
                    )

                    if image_url:
                        send_telegram(token, chat_id, image_url, caption, link)

                    entry["last_reminder"] = str(today)

    save_state(state)


if __name__ == "__main__":
    main()
