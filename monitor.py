import requests
import os
from bs4 import BeautifulSoup

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

BASE_URL = "https://marie-sklodowska-curie-actions.ec.europa.eu"
URL = BASE_URL + "/funding/seal-of-excellence"

def send_photo_with_caption(photo_url, caption):
    telegram_url = f"https://api.telegram.org/bot{TOKEN}/sendPhoto"
    payload = {
        "chat_id": CHAT_ID,
        "photo": photo_url,
        "caption": caption[:1024],  # limite do Telegram para legenda
        "parse_mode": "Markdown"
    }
    requests.post(telegram_url, data=payload, timeout=30)

def get_latest_news():
    r = requests.get(URL, timeout=30)
    soup = BeautifulSoup(r.text, "html.parser")

    # pega todos os links internos da seção
    links = []
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if "/funding/seal-of-excellence/" in href and href != "/funding/seal-of-excellence":
            full_link = href if href.startswith("http") else BASE_URL + href
            links.append(full_link)

    if not links:
        return None

    latest_link = links[0]  # assume que o primeiro é o mais recente

    # agora entra na página da notícia
    r2 = requests.get(latest_link, timeout=30)
    soup2 = BeautifulSoup(r2.text, "html.parser")

    # título
    title = soup2.find("h1")
    title_text = title.get_text(strip=True) if title else "Novo item publicado"

    # resumo (primeiro parágrafo significativo)
    paragraphs = soup2.find_all("p")
    summary = ""
    for p in paragraphs:
        text = p.get_text(strip=True)
        if len(text) > 100:
            summary = text
            break

    # imagem principal
    image = soup2.find("img")
    image_url = ""
    if image and image.get("src"):
        src = image["src"]
        image_url = src if src.startswith("http") else BASE_URL + src

    return title_text, summary, image_url, latest_link

news = get_latest_news()

if news:
    title, summary, image_url, link = news

    caption = f"📢 *Novo item publicado!*\n\n"
    caption += f"*{title}*\n\n"
    caption += f"{summary}\n\n"
    caption += f"[🔎 Learn more]({link})"

    if image_url:
        send_photo_with_caption(image_url, caption)
    else:
        send_photo_with_caption("", caption)
