import requests
import os
from bs4 import BeautifulSoup

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

BASE_URL = "https://marie-sklodowska-curie-actions.ec.europa.eu"
URL = BASE_URL + "/funding/seal-of-excellence"

def send_message(text):
    telegram_url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": text[:4000]
    }
    requests.post(telegram_url, data=payload, timeout=30)

r = requests.get(URL, timeout=30)
soup = BeautifulSoup(r.text, "html.parser")

cards = soup.find_all("article")

if not cards:
    send_message("❌ Nenhum <article> encontrado.")
else:
    msg = "🔎 Articles encontrados:\n\n"
    for card in cards[:3]:
        link = card.find("a", href=True)
        if link:
            href = link["href"]
            full_link = href if href.startswith("http") else BASE_URL + href
            msg += full_link + "\n\n"
    send_message(msg)
