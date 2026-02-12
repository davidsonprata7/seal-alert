import os
import json
import requests
from datetime import datetime, timedelta


API_URL = "https://marie-sklodowska-curie-actions.ec.europa.eu/api/content/funding/seal-of-excellence"
STATE_FILE = "state.json"


def get_env(name):
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Variável ausente: {name}")
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


def country_to_flag(country_name):
    try:
        import pycountry
        country = pycountry.countries.get(name=country_name)
        if not country:
            return ""
        code = country.alpha_2
        return "".join(chr(127397 + ord(c)) for c in code)
    except Exception:
        return ""


def send_telegram_photo(token, chat_id, image_url, caption, url_button):

    telegram_url = f"https://api.telegram.org/bot{token}/sendPhoto"

    keyboard = {
        "inline_keyboard": [
            [{"text": "🔗 Abrir publicação", "url": url_button}]
        ]
    }

    response = requests.post(
        telegram_url,
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


def main():

    token = get_env("BOT_TOKEN")
    chat_id = get_env("CHAT_ID")

    state = load_state()
    today = today_brt()

    response = requests.get(API_URL, timeout=30)
    data = response.json()

    for item in data.get("items", []):

        url = item.get("url")
        title = item.get("title")
        description = item.get("summary", "")
        country = item.get("country", "")
        image_url = item.get("image")
        end_date_raw = item.get("end_date")

        if not url or not end_date_raw:
            continue

        end_date_obj = datetime.strptime(end_date_raw, "%Y-%m-%d").date()

        if url not in state["items"]:

            flag = country_to_flag(country)

            caption = (
                f"🚩{title} {flag}\n\n"
                f"📍{description}\n\n"
                f"⚠️ End date:⚠️\n"
                f"✅ {end_date_obj.strftime('%d %B %Y')}"
            )

            if image_url:
                send_telegram_photo(token, chat_id, image_url, caption, url)

            state["items"][url] = {
                "end_date": end_date_raw,
                "last_reminder": None
            }

        else:
            entry = state["items"][url]

            if today.weekday() == 5 and end_date_obj > today:
                if entry.get("last_reminder") != str(today):

                    flag = country_to_flag(country)

                    caption = (
                        f"⏰ Reminder\n\n"
                        f"🚩{title} {flag}\n\n"
                        f"📍{description}\n\n"
                        f"⚠️ End date:⚠️\n"
                        f"✅ {end_date_obj.strftime('%d %B %Y')}"
                    )

                    if image_url:
                        send_telegram_photo(token, chat_id, image_url, caption, url)

                    entry["last_reminder"] = str(today)

    save_state(state)


if __name__ == "__main__":
    main()
