import requests
import os
import json
import re
from datetime import datetime, timedelta
from html import unescape
import pycountry

BOT_TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]
DEBUG = os.environ.get("DEBUG", "false").lower() == "true"

API_URL = "https://marie-sklodowska-curie-actions.ec.europa.eu/eac-api/content?filters[permanent|field_eac_topics][0]=290&language=en&page[limit]=10&sort=date_desc&story_type=pledge&type=story"

BASE_URL = "https://marie-sklodowska-curie-actions.ec.europa.eu"
STATE_FILE = "state.json"

# ================= TELEGRAM =================

def send_message(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    r = requests.post(url, data={"chat_id": CHAT_ID, "text": text})
    if r.status_code != 200:
        print("Erro Telegram:", r.text)

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

    r = requests.post(url, data=payload)

    if r.status_code != 200:
        print("Erro envio imagem, enviando só texto")
        send_message(caption + f"\n\n{button_url}")

# ================= UTIL =================

def clean_html(text):
    text = re.sub('<.*?>', '', text)
    text = unescape(text)
    return text.strip()

def shrink_image(url):
    if url:
        return url.replace("eac_ratio_16_9_w_480", "eac_ratio_16_9_w_320")
    return None

# ================= PAÍS =================

def flag_from_code(code):
    return ''.join(chr(127397 + ord(c)) for c in code)

def detect_country_flag(text):
    for country in pycountry.countries:
        if country.name.lower() in text.lower():
            return flag_from_code(country.alpha_2)
    return "🌍"

# ================= DEADLINE =================

def extract_end_date(article_url):
    try:
        r = requests.get(article_url, timeout=10)
        match = re.search(
            r'(\d{1,2}\s(?:January|February|March|April|May|June|July|August|September|October|November|December)\s\d{4})',
            r.text
        )
        if match:
            return match.group(1)
        return None
    except:
        return None

# ================= STATE =================

def load_state():
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r") as f:
                return json.load(f)
        except:
            pass

    return {
        "seen_ids": [],
        "last_new": None,
        "last_heartbeat": None
    }

def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f)

# ================= MAIN =================

def main():
    if DEBUG:
        
        send_message("🐞 DEBUG ATIVO")
    
    now = datetime.utcnow()
    state = load_state()
    seen_ids = state.get("seen_ids", [])

    try:
        response = requests.get(API_URL, timeout=10)

        if response.status_code != 200:
            send_message("🚨 ALERTA: API retornou status diferente de 200.")
            return

        data = response.json()

    except:
        send_message("🚨 ALERTA: Falha ao acessar API MSCA.")
        return

    if "data" not in data:
        send_message("🚨 ALERTA: Estrutura da API foi alterada.")
        return

    new_items = []

    for item in data["data"]:
        if not all(k in item for k in ["nid", "title", "url"]):
            send_message("🚨 ALERTA: Estrutura inesperada da API.")
            return

        if item["nid"] not in seen_ids:
            new_items.append(item)

    # ================= NOVOS ITENS =================

    if new_items:

        for item in reversed(new_items):

            title = item["title"]
            intro = clean_html(item.get("intro", ""))
            article_url = BASE_URL + item["url"]
            image = shrink_image(item.get("image", ""))

            flag = detect_country_flag(title)

            caption = f"""🚩 <b>{title}</b> {flag}

📍 {intro}
"""

            if image:
                send_photo(image, caption, article_url)
            else:
                send_message(caption + f"\n{article_url}")

            seen_ids.append(item["nid"])

        state["last_new"] = now.isoformat()

    else:
        if DEBUG:
            send_message("🐞 DEBUG: Script executado. Nenhuma novidade encontrada.")

    # ================= ALERTA 24H SEM NOVIDADE =================

    if state.get("last_new"):
        last_new = datetime.fromisoformat(state["last_new"])
        if now - last_new > timedelta(hours=24):
            send_message("⚠️ Nenhuma nova oportunidade nas últimas 24h.")

    # ================= HEARTBEAT DIÁRIO =================

    if state.get("last_heartbeat"):
        last_heartbeat = datetime.fromisoformat(state["last_heartbeat"])
    else:
        last_heartbeat = None

    if not last_heartbeat or now - last_heartbeat > timedelta(hours=24):
        send_message("💓 Monitor MSCA ativo e funcionando.")
        state["last_heartbeat"] = now.isoformat()

    state["seen_ids"] = seen_ids
    save_state(state)


if __name__ == "__main__":
    main()
