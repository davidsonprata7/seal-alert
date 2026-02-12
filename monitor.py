import requests

URL = "https://marie-sklodowska-curie-actions.ec.europa.eu/funding/seal-of-excellence"

headers = {
    "User-Agent": "Mozilla/5.0"
}

r = requests.get(URL, headers=headers, timeout=30)

print("STATUS:", r.status_code)
print("TAMANHO HTML:", len(r.text))

print("\nPRIMEIROS 1000 CARACTERES:\n")
print(r.text[:1000])
