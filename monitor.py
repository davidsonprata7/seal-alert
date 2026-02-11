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

all_links = []

for a in soup.find_all("a", href=True):
    href = a["href"]

    # ignorar navegação e outras ações
    if "/funding/seal-of-excellence/" in href:
        if not href.endswith("/seal-of-excellence") and "postdoctoral" not in href:
            full_link = href if href.startswith("http") else BASE_URL + href
            all_links.append(full_link)

unique_links = list(set(all_links))

msg = "🔎 POSSÍVEIS LINKS DA LISTA:\n\n"
for link in unique_links[:10]:
    msg += link + "\n\n"

send_message(msg)
