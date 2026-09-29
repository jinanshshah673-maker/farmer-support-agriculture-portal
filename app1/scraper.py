import json
from pathlib import Path

import requests
from bs4 import BeautifulSoup


URL = "https://dbtbharat.gov.in/central-scheme/list"

headers = {
    "User-Agent": "Mozilla/5.0"
}

response = requests.get(URL, headers=headers)

print("Status Code:", response.status_code)

soup = BeautifulSoup(response.text, "html.parser")

schemes = []

for a in soup.find_all("a"):
    text = a.get_text(strip=True)

    if len(text) > 5:
        schemes.append({
            "scheme_name": text,
            "category": "Central",
            "description": "",
            "benefits": "",
            "eligibility": "",
            "official_link": URL
        })

# Remove duplicate scheme names
unique = []
seen = set()

for scheme in schemes:
    if scheme["scheme_name"] not in seen:
        seen.add(scheme["scheme_name"])
        unique.append(scheme)

output_path = Path("app1/data/government_schemes.json")
output_path.parent.mkdir(parents=True, exist_ok=True)

with open(output_path, "w", encoding="utf-8") as f:
    json.dump(unique, f, indent=4, ensure_ascii=False)

print("Total Schemes:", len(unique))
print("Saved to:", output_path)