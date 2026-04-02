# Supabase Materials Setup

This task adds a Supabase DB setup script, an uploader for approved images, and a mobile-first review page.

## Prerequisites
- Python 3.9+
- `supabase` Python package already installed
- `psycopg2-binary` if you want to run DB setup locally

## 1) Create Tables

```bash
python scripts/setup_db.py
```

If `psycopg2` is missing:

```bash
pip install psycopg2-binary
```

## 2) Upload Images + Insert Rows

```bash
python scripts/upload_images.py
```

Optional: pass a custom report path:

```bash
python scripts/upload_images.py /path/to/report.json
```

This script:
- Uploads approved images to bucket `materials`
- Uses storage path `materials/{batch_id}/{filename}` in the DB
- Inserts (or updates) rows in `materials`
- Upserts a `batches` record

## 3) Review Page

Open `review/index.html` in a browser or run:

```bash
python -m http.server 8000
```

Then visit `http://localhost:8000/review/`.

On first load, enter your Supabase URL + anon key and press **Connect**. The page will load all `pending` images. Swipe right to approve, left to reject, or use buttons. Tap the image to view a larger preview.

## Notes
- Credentials are read from `../../.env.supabase` by the Python scripts.
- The review page stores credentials in `localStorage` for convenience.
