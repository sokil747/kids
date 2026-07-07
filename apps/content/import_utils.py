import csv
import io
import logging
import re

import requests

logger = logging.getLogger(__name__)


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
    "Country": "country_name",
    "Страна": "country_name",
    "Категорія": "category_name",
    "Category": "category_name",
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


def download_drive_image(file_id):
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
    })

    # Helper to check if response is an image
    def _is_image(r):
        return r.status_code == 200 and r.headers.get('content-type', '').startswith('image/')

    strategies = [
        f"https://drive.google.com/thumbnail?id={file_id}&sz=w1000",
        f"https://drive.google.com/thumbnail?id={file_id}&sz=s1000",
        f"https://drive.google.com/uc?id={file_id}&export=view",
        f"https://docs.google.com/uc?export=download&id={file_id}&confirm=t",
        f"https://drive.usercontent.google.com/download?id={file_id}&export=download&authuser=0",
        f"https://drive.usercontent.google.com/download?id={file_id}&export=download&authuser=0&confirm=t",
    ]

    for url in strategies:
        try:
            r = session.get(url, allow_redirects=True, timeout=15)
            if _is_image(r):
                return r.content
        except Exception:
            continue

    # Try docs.google.com/uc with confirm token parsing
    try:
        url = f"https://docs.google.com/uc?export=download&id={file_id}"
        r = session.get(url, allow_redirects=True, timeout=15)
        if _is_image(r):
            return r.content
        # Look for confirm token in form action or download link
        confirm = None
        m = re.search(r'confirm=([a-zA-Z0-9_-]+)', r.text)
        if m:
            confirm = m.group(1)
        else:
            m = re.search(r'action="[^"]*confirm=([a-zA-Z0-9_-]+)', r.text)
            if m:
                confirm = m.group(1)
        if confirm:
            url2 = f"https://docs.google.com/uc?export=download&confirm={confirm}&id={file_id}"
            r2 = session.get(url2, allow_redirects=True, timeout=15)
            if _is_image(r2):
                return r2.content
    except Exception:
        pass

    # Last resort: gdown
    data = download_drive_image_gdown(file_id)
    if data:
        return data

    return None


def download_drive_image_gdown(file_id):
    """Fallback using gdown library which handles Google Drive's virus scan page internally."""
    try:
        import gdown
        url = f"https://drive.google.com/uc?id={file_id}"
        output = gdown.download(url, output=None, quiet=True, fuzzy=False)
        if output:
            with open(output, 'rb') as f:
                data = f.read()
            import os
            os.remove(output)
            return data
    except Exception as e:
        logger.warning("gdown failed for %s: %s", file_id, e)
    return None


def download_image(url):
    """Try to download an image from any HTTP/HTTPS URL.
    Supports Google Drive URLs and direct image URLs.
    Returns (content_bytes, suggested_filename) or (None, None)."""
    from urllib.parse import urlparse, unquote
    import hashlib
    from pathlib import Path

    if not url:
        return None, None

    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36',
        'Accept': 'image/webp,image/*,*/*;q=0.8',
    })

    # Google Drive URL
    m = re.search(r'/d/([a-zA-Z0-9_-]+)', url)
    if m:
        data = download_drive_image(m.group(1))
        if data:
            return data, f"{m.group(1)}.jpg"

    # Direct image URL
    try:
        r = session.get(url, allow_redirects=True, timeout=15, stream=True)
        if r.status_code == 200:
            ct = r.headers.get('content-type', '')
            if ct.startswith('image/'):
                data = r.content
                ext = ct.split('/')[-1].split(';')[0]
                if ext not in ('jpeg', 'png', 'gif', 'webp'):
                    ext = 'jpg'
                if ext == 'jpeg':
                    ext = 'jpg'
                path = unquote(urlparse(url).path)
                basename = Path(path).stem or hashlib.md5(url.encode()).hexdigest()[:12]
                return data, f"{basename}.{ext}"
    except Exception:
        pass

    return None, None


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
