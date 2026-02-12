import os
import json
import requests
from bs4 import BeautifulSoup

BASE = "https://marie-sklodowska-curie-actions.ec.europa.eu"
LIST_URL = BASE + "/funding/seal-of-excellence"
STATE_FILE = "state.json"

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}


def load_state():
    if not os.path.exists(STATE_FILE):
        return {"sent": []}
    with open(STATE_FILE, "r") as f:
        return json.load(f)


def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)


def get_listing_links():
    r = requests.get(LIST_URL, headers=HEADERS, timeout=30)
    soup = BeautifulSoup(r.text, "html.parser")

    links = []

    for a in soup.find_all("a", href=True):
        href = a["href"]

        if href.startswith("/funding/seal-of-excellence/") and href != "/funding/seal-of-excellence":
            full = BASE + href
            if full not in links:
                links.append(full)

    return links


def extract_article_data(url):
    r = requests.get(url, headers=HEADERS, timeout=30)
    soup = BeautifulSoup(r.text, "html.parser")

    # Title
    title_tag = soup.find("h1")
    title = title_tag.get_text(strip=True) if title_tag else "No title"

    # First paragraph
    p_tag = soup.find("p")
    summary = p_tag.get_text(strip=True) if p_tag else ""

    # End date
    end_date = "Not found"
    all_text = soup.get_text(separator="\n")

    for line in all_text.split("\n"):
        if "End date" in line:
            end_date = line.replace("End date:", "").strip()
            break

    # Image
    img_tag = soup.find("img")
    image_url = None
    if img_tag and img_tag.get("src"):
        src = img_tag["src"]
        image_url = src if src.startswith("http") else BASE + src

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
    links = get_listing_links()

    print("Links encontrados:", len(links))

    for link in links:

        if link not in state["sent"]:

            title, summary, end_date, image_url = extract_article_data(link)

            send_telegram(token, chat_id, title, summary, end_date, link, image_url)

            state["sent"].append(link)

    save_state(state)


if __name__ == "__main__":
    main()
