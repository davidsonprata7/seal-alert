import os
import json
import requests
from datetime import datetime
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup

BASE = "https://marie-sklodowska-curie-actions.ec.europa.eu"
LIST_URL = BASE + "/funding/seal-of-excellence"
STATE_FILE = "state.json"


def load_state():
    if not os.path.exists(STATE_FILE):
        return {"sent": []}
    with open(STATE_FILE, "r") as f:
        return json.load(f)


def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)


def get_links():
    print("Carregando página principal...")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(LIST_URL, timeout=60000)
        page.wait_for_timeout(5000)
        html = page.content()
        browser.close()

    soup = BeautifulSoup(html, "html.parser")

    links = []
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if href.startswith("/funding/seal-of-excellence/") and href != "/funding/seal-of-excellence":
            full = BASE + href
            if full not in links:
                links.append(full)

    return links


def extract_article(url):
    print("Extraindo:", url)
    r = requests.get(url, timeout=30)
    soup = BeautifulSoup(r.text, "html.parser")

    # Title
    title_tag = soup.find("h1")
    title = title_tag.get_text(strip=True) if title_tag else "No title"

    # Summary
    summary = ""
    main_content = soup.find("main")
    if main_content:
        first_p = main_content.find("p")
        if first_p:
            summary = first_p.get_text(strip=True).replace("\xa0", " ")

    # End date
    end_date = "Not found"

    # método 1
    for dt in soup.find_all("dt"):
        if "End date" in dt.get_text(strip=True):
            dd = dt.find_next_sibling("dd")
            if dd:
                end_date = dd.get_text(strip=True)
                break

    # método 2 (classes ECL)
    if end_date == "Not found":
        terms = soup.find_all(class_="ecl-description-list__term")
        for term in terms:
            if "End date" in term.get_text(strip=True):
                definition = term.find_next(class_="ecl-description-list__definition")
                if definition:
                    end_date = definition.get_text(strip=True)
                    break

    # Image
    image_url = None
    og = soup.find("meta", property="og:image")
    if og and og.get("content"):
        image_url = og["content"]

    return title, summary, end_date, image_url


def send_telegram(token, chat_id, title, summary, end_date, url, image_url):

    caption = (
        f"🚩 {title}\n\n"
        f"📍 {summary}\n\n"
        f"⚠️ End date: ⚠️\n"
        f"✅ {end_date}"
    )

    keyboard = {
        "inline_keyboard": [
            [{"text": "🔗 Learn more", "url": url}]
        ]
    }

    api = f"https://api.telegram.org/bot{token}/sendMessage"

    response = requests.post(api, data={
        "chat_id": chat_id,
        "text": caption,
        "reply_markup": json.dumps(keyboard)
    })

    print("TELEGRAM STATUS:", response.status_code)
    print("TELEGRAM RESPONSE:", response.text)

    if response.status_code != 200:
        raise RuntimeError("Telegram send failed")


def main():
    print("Iniciando monitor...")
    token = os.getenv("BOT_TOKEN")
    chat_id = os.getenv("CHAT_ID")

    if not token or not chat_id:
        raise RuntimeError("BOT_TOKEN or CHAT_ID missing")

    state = load_state()
    links = get_links()

    print("Links encontrados:", len(links))

    for link in links:
        if link not in state["sent"]:
            print("Enviando:", link)

            title, summary, end_date, image_url = extract_article(link)

            send_telegram(token, chat_id, title, summary, end_date, link, image_url)

            state["sent"].append(link)

    save_state(state)
    print("Finalizado.")


if __name__ == "__main__":
    main()
