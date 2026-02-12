import requests
import os
import json
import re
from datetime import datetime
from html import unescape
import pycountry

BOT_TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]

API_URL = "https://marie-sklodowska-curie-actions.ec.europa.eu/eac-api/content?filters[permanent|field_eac_topics][0]=290&language=en&page[limit]=10&sort=date_desc&story_type=pledge&type=story"

BASE_URL = "https://marie-sklodowska-curie-actions.ec.europa.eu"
STATE_FILE = "state.json"


# ================= TELEGRAM =================

def send_message(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text}
    requests.post(url, data=payload)


def send_photo(photo_url, caption, button_url):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"

    payload = {
        "chat_id": CHAT_ID,
        "photo": photo_url,
        "caption": caption,
        "parse_mode": "HTML",
        "reply_markup": json.dumps({
            "inline_keyboard": [
                [{"text": "Learn more", "url": button_url}]
            ]
        })
    }

    requests.post(url, data=payload)


# ================= UTIL =================

def clean_html(raw_html):
    text = re.sub('<.*?>', '', raw_html)
    text = unescape(text)
    text = text.replace("\xa0", " ")
    return text.strip()


def shrink_image(image_url):
    return image_url.replace("eac_ratio_16_9_w_480", "eac_ratio_16_9_w_320")


# ================= 1️⃣ DETECÇÃO AUTOMÁTICA DE QUALQUER PAÍS =================

def get_flag_from_title(title):
    for country in pycountry.countries:
        if country.name.lower() in title.lower():
            code = country.alpha_2
            return ''.join(chr(127397 + ord(c)) for c in code)
    return "🌍"


# ================= DEADLINE =================

def get_end_date(article_url):
    try:
        r = requests.get(article_url, timeout=10)
        html = r.text

        match = re.search(
            r'(\d{1,2}\s(?:January|February|March|April|May|June|July|August|September|October|November|December)\s\d{4})',
            html
        )

        if match:
            return match.group(1)

        return None

    except:
        return None


def days_until(date_string):
    try:
        end_date = datetime.strptime(date_string, "%d %B %Y")
        delta = end_date - datetime.now()
        return delta.days
    except:
        return None


# ================= STATE =================

def load_state():
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r") as f:
                state = json.load(f)
        except:
            state = {}
    else:
        state = {}

    if "seen_ids" not in state:
        state["seen_ids"] = []

    return state


def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f)


# ================= MAIN =================

def main():

    state = load_state()
    seen_ids = state["seen_ids"]

    # ================= 2️⃣ ALERTA DE FALHA DA API =================

    try:
        response = requests.get(API_URL, timeout=10)

        if response.status_code != 200:
            send_message("🚨 ALERTA: API retornou status diferente de 200.")
            return

        data = response.json()

    except Exception:
        send_message("🚨 ALERTA: Falha ao acessar a API.")
        return

    # ================= 3️⃣ ALERTA DE ESTRUTURA ALTERADA =================

    if "data" not in data:
        send_message("🚨 ALERTA: Estrutura da API mudou (campo 'data' não encontrado).")
        return

    new_items = []

    for item in data["data"]:

        if not all(k in item for k in ["nid", "title", "url"]):
            send_message("🚨 ALERTA: Estrutura inesperada em item da API.")
            return

        if item["nid"] not in seen_ids:
            new_items.append(item)

    # ================= NOVOS ARTIGOS =================

    if new_items:

        for item in reversed(new_items):

            title = item["title"]
            intro = clean_html(item.get("intro", ""))
            article_url = BASE_URL + item["url"]
            image = shrink_image(item.get("image", ""))

            flag = get_flag_from_title(title)
            end_date = get_end_date(article_url)

            caption = f"""🚩<b>{title}</b> {flag}

📍{intro}
"""

            if end_date:

                caption += f"""
⚠️ <b>End date:</b>
✅ <b>{end_date}</b>
"""

                # ================= 4️⃣ ALERTA DE DEADLINE PRÓXIMO =================

                days_left = days_until(end_date)

                if days_left is not None:
                    if days_left <= 3:
                        caption += "\n🚨 <b>URGENTE: 3 dias ou menos restantes!</b>\n"
                    elif days_left <= 7:
                        caption += "\n⏳ <b>Deadline próximo (7 dias ou menos)</b>\n"

            else:
                caption += """
⚠️ <b>End date:</b>
❌ <b>Not specified</b>
"""

            send_photo(image, caption, article_url)

            seen_ids.append(item["nid"])

        state["seen_ids"] = seen_ids
        save_state(state)


if __name__ == "__main__":
    main()
