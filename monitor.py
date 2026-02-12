import os
import json
import requests
from datetime import datetime, timedelta
from bs4 import BeautifulSoup


BASE_URL = "https://marie-sklodowska-curie-actions.ec.europa.eu"
URL = "https://marie-sklodowska-curie-actions.ec.europa.eu/funding/seal-of-excellence"
STATE_FILE = "state.json"


# ==============================
# UTIL
# ==============================

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


def today_brt():
    # Brasília UTC-3
    return (datetime.utcnow() - timedelta(hours=3)).date()


# ==============================
# SCRAPING LISTA PRINCIPAL
# ==============================

def parse_list_page():
    r = requests.get(URL, timeout=30)
    soup = BeautifulSoup(r.text, "html.parser")

    items = []

    # Estrutura real do site MSCA
    for card in soup.select("div.ecl-card"):
        link = card.select_one("a")

        if not link:
            continue

        title = link.get_text(strip=True)
        href = link.get("href")

        if not href or not title:
            continue

        full_url = href if href.startswith("http") else BASE_URL + href

        items.append({
            "id": full_url,
            "title": title,
            "url": full_url
        })

    # Remove duplicados
    unique = {item["id"]: item for item in items}
    return list(unique.values())


# ==============================
# EXTRAÇÃO END DATE
# ==============================

def extract_end_date(detail_url):
    r = requests.get(detail_url, timeout=30)
    soup = BeautifulSoup(r.text, "html.parser")

    for strong in soup.find_all("strong"):
        if "End date" in strong.get_text():
            full_text = strong.parent.get_text(" ", strip=True)
            date_part = full_text.replace("End date:", "").strip()

            try:
                parsed = datetime.strptime(date_part, "%d %B %Y")
                return parsed.strftime("%Y-%m-%d")
            except Exception:
                return None

    return None


# ==============================
# MAIN
# ==============================

def main():
    token = get_env("BOT_TOKEN")
    chat_id = get_env("CHAT_ID")

    state = load_state()
    current_items = parse_list_page()

    today = today_brt()
    is_saturday = today.weekday() == 5

    open_count = 0

    for item in current_items:

        # NOVO ITEM
        if item["id"] not in state["items"]:

            end_date = extract_end_date(item["url"])
            if not end_date:
                continue

            end_date_date = datetime.strptime(end_date, "%Y-%m-%d").date()

            if end_date_date > today:
                open_count += 1

            send_telegram(
                token,
                chat_id,
                f"🆕 Nova publicação MSCA\n\n"
                f"{item['title']}\n"
                f"End date: {end_date}\n"
                f"{item['url']}"
            )

            state["items"][item["id"]] = {
                "title": item["title"],
                "end_date": end_date,
                "last_reminder": None
            }

        # ITEM EXISTENTE
        else:
            entry = state["items"][item["id"]]
            end_date = entry["end_date"]
            end_date_date = datetime.strptime(end_date, "%Y-%m-%d").date()

            if end_date_date > today:
                open_count += 1

                # Reminder semanal sábado
                if is_saturday:
                    last = entry.get("last_reminder")

                    if last != str(today):

                        days_left = (end_date_date - today).days

                        send_telegram(
                            token,
                            chat_id,
                            f"⏰ Reminder semanal\n\n"
                            f"{entry['title']}\n"
                            f"End date: {end_date}\n"
                            f"Dias restantes: {days_left}\n"
                            f"{item['url']}"
                        )

                        entry["last_reminder"] = str(today)

    # Heartbeat diário
    if state["last_heartbeat"] != str(today):
        send_telegram(
            token,
            chat_id,
            f"💓 Monitor ativo\nOportunidades abertas: {open_count}"
        )
        state["last_heartbeat"] = str(today)

    save_state(state)


if __name__ == "__main__":
    main()
