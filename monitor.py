def extract_article(url):
    r = requests.get(url, timeout=30)
    soup = BeautifulSoup(r.text, "html.parser")

    # TITLE
    title_tag = soup.find("h1")
    title = title_tag.get_text(strip=True) if title_tag else "No title"

    # SUMMARY (primeiro parágrafo real do conteúdo principal)
    summary = ""
    main_content = soup.find("main")
    if main_content:
        first_p = main_content.find("p")
        if first_p:
            summary = first_p.get_text(strip=True).replace("\xa0", " ")

    # END DATE — abordagem estrutural completa
    end_date = "Not found"

    # Método 1 — dt/dd tradicional
    for dt in soup.find_all("dt"):
        if "End date" in dt.get_text(strip=True):
            dd = dt.find_next_sibling("dd")
            if dd:
                end_date = dd.get_text(strip=True)
                break

    # Método 2 — classes específicas ECL
    if end_date == "Not found":
        terms = soup.find_all(class_="ecl-description-list__term")
        for term in terms:
            if "End date" in term.get_text(strip=True):
                definition = term.find_next(class_="ecl-description-list__definition")
                if definition:
                    end_date = definition.get_text(strip=True)
                    break

    # IMAGE — sempre usar og:image (é a imagem oficial do artigo)
    image_url = None
    og = soup.find("meta", property="og:image")
    if og and og.get("content"):
        image_url = og["content"]

    return title, summary, end_date, image_url
