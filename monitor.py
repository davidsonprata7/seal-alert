import requests
import os
from bs4 import BeautifulSoup

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
URL = "https://marie-sklodowska-curie-actions.ec.europa.eu/funding/seal-of-excellence"

def get_site_text():
    r = requests.get(URL)
    soup = BeautifulSoup(r.text, "html.parser")
    return soup.get_text()

def send_telegram(message):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message}
    requests.post(url, data=payload)

# Executa uma vez e finaliza
current_text = get_site_text()

send_telegram("✅ Monitor rodou com sucesso.\n" + URL)
