import os
import json
import requests
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup

BASE = "https://marie-sklodowska-curie-actions.ec.europa.eu"
LIST_URL = BASE + "/funding/seal-of-excellence"
STATE_FILE = "state.json"


# =========================
# COUNTRY FLAGS (EXPANDIDO)
# =========================

COUNTRIES = {
    "France": "🇫🇷",
    "Croatia": "🇭🇷",
    "Estonia": "🇪🇪",
    "Germany": "🇩🇪",
    "Italy": "🇮🇹",
    "Spain": "🇪🇸",
    "Portugal": "🇵🇹",
    "Netherlands": "🇳🇱",
    "Belgium": "🇧🇪",
    "Poland": "🇵🇱",
    "Czech": "🇨🇿",
    "Austria": "🇦🇹",
    "Sweden": "🇸🇪",
    "Finland": "🇫🇮",
    "Ireland": "🇮🇪",
    "Bulgaria": "🇧🇬",
    "Romania": "🇷🇴",
    "Greece": "🇬🇷",
    "Hungary": "🇭🇺",
    "Slovenia": "🇸🇮",
    "Slovakia": "🇸🇰",
    "Lithuania": "🇱🇹",
    "Latvia": "🇱🇻",
    "Luxembourg": "🇱🇺"
}


def detect_flag(title):
    for country, flag in COUNTRIES.items():
        if country.lower() in title.lower():
            return flag
    return ""


# =========================
# STATE CONTROL
# =========================

def load_state():
    if not os.path.exists(STATE_FILE):
        return {"sent": []}
    with open(STATE_FILE, "r") as f:
        return json.load(f)


def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)


# =========================
# GET LINKS (Playwright)
# =========================

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


# =========================
# EXTRACT ARTICLE
# =========================

def extract_article(url):
    r = requests.get(url, timeout=30)
    soup = BeautifulSoup(r.text, "html.parser")

    # TITLE
    title_tag = soup.find("h1")
    title = title_tag.get_text(strip=True) if title_tag else "No title"

    # SUMMARY
    summary = ""
    main = soup.find("main")
    if main:
        paragraphs = main.find_all("p")
        for p in paragraphs:
            text = p.get_text(strip=True).replace("\xa0", " ")
            if len(text) > 80:
                summary = text
                break

    # END DATE (estrutura real MSCA)
    end_date = "Not found"
    items = soup.find_all("div", class_="ecl-description-list__item")
    for item in items:
        term = item.find(class_="ecl-description-list__term")
        definition = item.find(class_="ecl-description-list__definition")
        if term and definition:
            if "End date" in term.get_text(strip=True):
                end_date = definition.get_text(strip=True)
                break

    # IMAGE
    image_url = None
    media = soup.find("div", class_="ecl-media-container")
    if media:
        img = media.find("img")
        if img and img.get("src"):
            src = img["src"]
            image_url = src if src.startswith("http") else BASE + src

    return title, summary, end_date, image_url


# =========================
# TELEGRAM SEND
# =========================

def send_telegram(token, chat_id, title, summary, end_date, url, image_url):

    flag = detect_flag(title)

    caption = (
        f"🚩 {title} {flag}\n\n"
        f"📍 {summary}\n\n"
        f"⚠️ End date: ⚠️\n"
        f"✅ {end_date}"
    )

    keyboard = {
        "inline_keyboard": [
            [{"text": "🔗 Learn more", "url": url}]
        ]
    }

    api_photo = f"https://api.telegram.org/bot{token}/sendPhoto"
    api_text = f"https://api.telegram.org/bot{token}/sendMessage"

    # Try sending image
    if image_url:
        try:
            img_data = requests.get(image_url, timeout=30).content
            response = requests.post(
                api_photo,
                data={
                    "chat_id": chat_id,
                    "caption": caption,
                    "reply_markup": json.dumps(keyboard)
                },
                files={"photo": img_data}
            )
            if response.status_code == 200:
                return True
        except:
            pass

    # Fallback to text
    response = requests.post(
        api_text,
        data={
            "chat_id": chat_id,
            "text": caption,
            "reply_markup": json.dumps(keyboard)
        }
    )

    return response.status_code == 200


def send_no_updates(token, chat_id):
    api = f"https://api.telegram.org/bot{token}/sendMessage"
    requests.post(
        api,
        data={
            "chat_id": chat_id,
            "text": "ℹ️ No new Seal of Excellence updates today."
        }
    )


# =========================
# MAIN
# =========================

def main():
    token = os.getenv("BOT_TOKEN")
    chat_id = os.getenv("CHAT_ID")

    state = load_state()
    links = get_links()

    new_sent = 0

    for link in links:
        if link not in state["sent"]:
            title, summary, end_date, image_url = extract_article(link)

            success = send_telegram(
                token, chat_id, title, summary, end_date, link, image_url
            )

            if success:
                state["sent"].append(link)
                new_sent += 1

    if new_sent == 0:
        send_no_updates(token, chat_id)

    save_state(state)


if __name__ == "__main__":
    main()
