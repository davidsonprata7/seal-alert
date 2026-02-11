import requests
import os
import hashlib
import json
from bs4 import BeautifulSoup

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
URL = "https://marie-sklodowska-curie-actions.ec.europa.eu/funding/seal-of-excellence"

STATE_FILE = "state.json"

def get_section_hash():
    r = requests.get(URL, timeout=30)
    soup = BeautifulSoup(r.text, "html.parser")

    full_text = soup.get_text(separator="\n")
    
    marker = "List of Seal of Excellence"

    if marker not in full_text:
        return None

    # Pega apenas o texto a partir da seção desejada
    section_text = full_text.split(marker, 1)[1]

    return hashlib.sha256(section_text.encode()).hexdigest()

def send_telegram(message):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message}
    requests.post(url, data=payload, timeout=30)

def load_state():
    try:
        with open(STATE_FILE, "r") as f:
            return json.load(f)
    except:
        return {"last_hash": "", "no_change_count": 0}

def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f)

current_hash = get_section_hash()
state = load_state()

if current_hash is None:
    send_telegram("⚠️ Não foi possível encontrar a seção 'List of Seal of Excellence' no site.")
else:

    if state["last_hash"] == "":
        state["last_hash"] = current_hash
        send_telegram("🤖 Monitor da seção 'List of Seal of Excellence' iniciado com sucesso.")

    elif current_hash != state["last_hash"]:
        send_telegram("🚨 Nova informação detectada na seção 'List of Seal of Excellence'!\n" + URL)
        state["last_hash"] = current_hash
        state["no_change_count"] = 0

    else:
        state["no_change_count"] += 1

        if state["no_change_count"] >= 3:
            send_telegram("✅ BOT funcionando normalmente.\nNenhuma mudança na seção 'List of Seal of Excellence' nas últimas 3 horas.")
            state["no_change_count"] = 0

save_state(state)
