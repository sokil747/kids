import csv
import io
import re
import requests


DEFAULT_SHEET_URL = (
    "https://docs.google.com/spreadsheets/d/"
    "1U52vYgYqOt4Zb15bkrTn1g15rSoAP9Qw/"
    "edit?gid=1170806001#gid=1170806001"
)

BUSINESS_FIELDS = [
    ("title", "Назва мережі", True),
    ("description", "Опис", False),
    ("online_store", "Наші магазини", False),
    ("facebook", "Facebook", False),
    ("instagram", "Instagram", False),
    ("tiktok", "TikTok", False),
    ("youtube", "YouTube", False),
    ("hotline", "Телефон", False),
    ("photo_url", "Фото (logo)", False),
    ("country_name", "Країна", False),
    ("category_name", "Категорія", False),
]

URL_FIELDS = {"online_store", "facebook", "instagram", "tiktok", "youtube"}

COLUMN_MAP = {
    "Назва мережі": "title",
    "Текст": "description",
    "Фото": "photo_url",
    "Наші магазини": "online_store",
    "Facebook": "facebook",
    "Instagram": "instagram",
    "TikTok": "tiktok",
    "YouTube": "youtube",
    "Служба підтримки": "hotline",
    "Країна": "country_name",
    "Категорія": "category_name",
}


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
    return resp.content.decode("utf-8-sig")


def get_fieldnames(csv_text):
    reader = csv.DictReader(io.StringIO(csv_text))
    return reader.fieldnames


def parse_rows(csv_text, column_map=None):
    if column_map is None:
        column_map = COLUMN_MAP
    reader = csv.DictReader(io.StringIO(csv_text))
    rows = []
    for row in reader:
        data = {}
        for sheet_col, model_field in column_map.items():
            value = row.get(sheet_col, "").strip()
            if not value:
                continue
            if model_field == "photo_url":
                data[model_field] = value
            elif model_field in URL_FIELDS:
                if value.startswith("http://") or value.startswith("https://"):
                    data[model_field] = value
            else:
                data[model_field] = value
        title = data.get("title", "").strip()
        if title:
            rows.append(data)
    return rows


def find_duplicates(rows):
    from .models import Business

    row_titles_lower = {r["title"].lower() for r in rows}
    existing = Business.objects.all()
    dup_map = {}
    for b in existing:
        bl = b.title.lower()
        if bl in row_titles_lower:
            dup_map[bl] = b
    return dup_map
