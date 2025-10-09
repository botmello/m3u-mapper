#!/usr/bin/env python3
import requests, zipfile, io, json
from pathlib import Path

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif"}
ZIP_URL = "https://github.com/tv-logo/tv-logos/archive/refs/heads/main.zip"

BASE_DIR = Path(__file__).resolve().parent
EXTRACT_DIR = BASE_DIR / "tv-logos-main"
COUNTRIES_DIR = EXTRACT_DIR / "countries"
OUTPUT_FILE = BASE_DIR / "logos.json"

def download_and_extract():
    print("📥 Downloading repo zip...")
    r = requests.get(ZIP_URL)
    r.raise_for_status()

    z = zipfile.ZipFile(io.BytesIO(r.content))
    z.extractall(BASE_DIR)
    print("✅ Extracted.")

def get_logos_by_region(country_path: Path, region: str, next_id: list):
    logos = {}
    for file_path in country_path.rglob("*"):
        if file_path.is_file() and file_path.suffix.lower().lstrip(".") in ALLOWED_EXTENSIONS:
            rel = file_path.relative_to(country_path).as_posix()
            logos[f"{region}/{rel}"] = next_id[0]
            next_id[0] += 1
    return logos

def generate_logos_json(countries_dir: Path):
    countries = [d for d in countries_dir.iterdir() if d.is_dir()]
    countries.sort(key=lambda p: p.name.lower())

    result = {}
    next_id = [1]
    for country_dir in countries:
        result[country_dir.name] = get_logos_by_region(country_dir, country_dir.name, next_id)
    return json.dumps(result, indent=4, ensure_ascii=False)

if __name__ == "__main__":
    download_and_extract()
    json_data = generate_logos_json(COUNTRIES_DIR)
    OUTPUT_FILE.write_text(json_data, encoding="utf-8")

    parsed = json.loads(json_data)
    total = sum(len(v) for v in parsed.values())
    print(f"✅ logos.json created in: {OUTPUT_FILE}")
    print(f"   Countries: {len(parsed)} | Total logos: {total}")
