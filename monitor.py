import requests
import time
from bs4 import BeautifulSoup

TOKEN = "COLOQUE_AQUI_SEU_TOKEN"
CHAT_ID = "COLOQUE_AQUI_SEU_CHAT_ID"
URL = "https://marie-sklodowska-curie-actions.ec.europa.eu/funding/seal-of-excellence"

def get_site_text():
    r = requests.get(URL)
    soup = BeautifulSoup(r.text, "html.parser")
    return soup.get_text()

def send_telegram(message):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message}
    requests.post(url, data=payload)

last_text = ""

while True:
    current_text = get_site_text()
    
    if last_text and current_text != last_text:
        send_telegram("🚨 Atualização detectada no site Seal of Excellence!\n" + URL)
    
    last_text = current_text
    time.sleep(3600)  # verifica a cada 1 hora
