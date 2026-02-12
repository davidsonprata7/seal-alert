import os
import requests

print("SCRIPT INICIOU")

BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

print("BOT_TOKEN existe?", BOT_TOKEN is not None)
print("CHAT_ID existe?", CHAT_ID is not None)

def send_message(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    r = requests.post(url, data={"chat_id": CHAT_ID, "text": text})
    print("Status Telegram:", r.status_code)
    print("Resposta Telegram:", r.text)

send_message("🚀 TESTE DIRETO DO GITHUB ACTIONS")
print("SCRIPT TERMINOU")
