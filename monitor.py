import os
import json
import requests
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
    r = requests.get(url)
    soup = BeautifulSoup(r.text, "html.parser")

    title = soup.find("h1").get_text(strip=True)

    first_p = soup.find("p")
    summary = first_p.get_text(strip=True) if first_p else ""

    end_date = "Not found"
    for line in soup.get_text("\n").split("\n"):
        if "End date" in line:
            end_date = line.replace("End date:", "").strip()
            break

    img_tag = soup.find("img")
    image_url = None
    if img_tag and img_tag.get("src"):
        src = img_tag["src"]
        image_url = src if src.startswith("http") else BASE + src

    return title, summary, end_date, image_url


def send(token, chat_id, title, summary, end_date, url, image_url):
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

    if image_url:
        api = f"https://api.telegram.org/bot{token}/sendPhoto"
        requests.post(api, data={
            "chat_id": chat_id,
            "photo": image_url,
            "caption": caption,
            "reply_markup": json.dumps(keyboard)
        })
    else:
        api = f"https://api.telegram.org/bot{token}/sendMessage"
        requests.post(api, data={
            "chat_id": chat_id,
            "text": caption,
            "reply_markup": json.dumps(keyboard)
        })


def main():
    token = os.getenv("BOT_TOKEN")
    chat_id = os.getenv("CHAT_ID")

    state = load_state()
    links = get_links()

    print("Links encontrados:", len(links))

    for link in links:
        if link not in state["sent"]:
            title, summary, end_date, image_url = extract_article(link)
            send(token, chat_id, title, summary, end_date, link, image_url)
            state["sent"].append(link)

    save_state(state)


if __name__ == "__main__":
    main()
