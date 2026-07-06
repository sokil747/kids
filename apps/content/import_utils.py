import csv
import io
import re
import requests


DEFAULT_SHEET_URL = (
    "https://docs.google.com/spreadsheets/d/"
    "1U52vYgYqOt4Zb15bkrTn1g15rSoAP9Qw/"
    "edit?gid=1170806001#gid=1170806001"
)

COLUMN_MAP = {
    "Назва мережі": "title",
    "Текст": "description",
    "Наші магазини": "online_store",
    "Facebook": "facebook",
    "Instagram": "instagram",
    "TikTok": "tiktok",
    "YouTube": "youtube",
    "Служба підтримки": "hotline",
}

URL_FIELDS = {"online_store", "facebook", "instagram", "tiktok", "youtube"}


def extract_spreadsheet_id(url):
    patterns = [
        r"/spreadsheets/d/([a-zA-Z0-9_-]+)",
        r"spreadsheets/d/([a-zA-Z0-9_-]+)",
    ]
    for p in patterns:
        m = re.search(p, url)
        if m:
            return m.group(1)
    return None


def extract_gid(url):
    m = re.search(r"[?&]gid=(\d+)", url)
    return m.group(1) if m else None


def fetch_sheet_csv(spreadsheet_id, gid=None):
    url = f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}/export?format=csv"
    if gid:
        url += f"&gid={gid}"
    resp = requests.get(url, allow_redirects=True, timeout=30)
    resp.raise_for_status()
    return resp.text


def parse_rows(csv_text):
    reader = csv.DictReader(io.StringIO(csv_text))
    rows = []
    for row in reader:
        data = {}
        for sheet_col, model_field in COLUMN_MAP.items():
            value = row.get(sheet_col, "").strip()
            if model_field in URL_FIELDS:
                if value.startswith("http://") or value.startswith("https://"):
                    data[model_field] = value
            else:
                data[model_field] = value
        photo = row.get("Фото", "").strip()
        if photo:
            data["photo_url"] = photo
        title = data.get("title", "").strip()
        if title:
            rows.append(data)
    return rows


def find_duplicates(rows):
    from .models import Business
    existing = Business.objects.filter(title__in=[r["title"] for r in rows])
    return {b.title.lower(): b for b in existing}
