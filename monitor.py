import os
import json
import requests
from datetime import datetime
from bs4 import BeautifulSoup


URL = "COLE_AQUI_A_URL"
STATE_FILE = "state.json"


def get_env(name):
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Variável ausente: {name}")
    return value


def send_telegram(token, chat_id, text):
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    r = requests.post(url, data={"chat_id": chat_id, "text": text})
    if r.status_code != 200:
        raise RuntimeError(f"Erro Telegram: {r.text}")


def load_state():
    if not os.path.exists(STATE_FILE):
        return {"items": {}, "last_heartbeat": None}
    with open(STATE_FILE, "r") as f:
        return json.load(f)


def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)


def parse_page():
    r = requests.get(URL)
    soup = BeautifulSoup(r.text, "html.parser")

    items = []

    # ⚠️ ADAPTAR PARA SUA PÁGINA REAL
    for block in soup.select(".card"):
        title = block.select_one(".title").get_text(strip=True)
        end_date_text = block.select_one(".end-date").get_text(strip=True)

        end_date = datetime.strptime(end_date_text, "%d %B %Y")

        item_id = title

        items.append({
            "id": item_id,
            "title": title,
            "end_date": end_date.strftime("%Y-%m-%d")
        })

    return items


def main():
    token = get_env("BOT_TOKEN")
    chat_id = get_env("CHAT_ID")

    state = load_state()
    current_items = parse_page()

    today = datetime.utcnow().date()
    is_saturday = today.weekday() == 5

    open_count = 0

    for item in current_items:
        end_date = datetime.strptime(item["end_date"], "%Y-%m-%d").date()

        if end_date > today:
            open_count += 1

        # 🆕 Nova oportunidade
        if item["id"] not in state["items"]:
            send_telegram(
                token,
                chat_id,
                f"🆕 Nova oportunidade:\n{item['title']}\nEnd date: {item['end_date']}"
            )
            state["items"][item["id"]] = {
                "title": item["title"],
                "end_date": item["end_date"]
            }

        # 🔁 Reenvio sábado
        elif is_saturday and end_date > today:
            send_telegram(
                token,
                chat_id,
                f"🔁 Ainda aberta:\n{item['title']}\nEnd date: {item['end_date']}"
            )

    # 💓 Heartbeat diário
    if state["last_heartbeat"] != str(today):
        send_telegram(
            token,
            chat_id,
            f"💓 Monitor ativo.\nOportunidades abertas: {open_count}"
        )
        state["last_heartbeat"] = str(today)

    save_state(state)


if __name__ == "__main__":
    main()
