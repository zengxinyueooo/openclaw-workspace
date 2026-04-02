#!/usr/bin/env python3
import json
import mimetypes
import sys
from pathlib import Path

from supabase import create_client


def load_env(env_path: Path) -> dict:
    data = {}
    if not env_path.exists():
        raise FileNotFoundError(f"Missing env file: {env_path}")
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        data[key.strip()] = value.strip()
    return data


def resolve_report_path() -> Path:
    root = Path(__file__).resolve().parents[3]
    return root / "shared/content-assets/face/pending/2026-03-05/batch_1139/review/report.json"


def main() -> int:
    env_path = Path(__file__).resolve().parents[3] / ".env.supabase"
    env = load_env(env_path)

    supabase_url = env.get("SUPABASE_URL")
    service_key = env.get("SUPABASE_SERVICE_KEY")
    if not supabase_url or not service_key:
        print("Missing SUPABASE_URL or SUPABASE_SERVICE_KEY in .env.supabase", file=sys.stderr)
        return 1

    report_path = resolve_report_path()
    if len(sys.argv) > 1:
        report_path = Path(sys.argv[1]).expanduser().resolve()

    if not report_path.exists():
        print(f"Report not found: {report_path}")
        return 1

    report = json.loads(report_path.read_text())
    passed_images = report.get("passed_images", [])

    batch_path = Path(report.get("batch", ""))
    batch_id = batch_path.name if batch_path.name else "batch_unknown"

    passed_dir = report_path.parent / "passed"

    supabase = create_client(supabase_url, service_key)
    storage = supabase.storage.from_("materials")

    uploaded = 0
    for item in passed_images:
        filename = item.get("name")
        if not filename:
            continue

        file_path = passed_dir / filename
        if not file_path.exists():
            fallback = Path(item.get("path", ""))
            file_path = fallback if fallback.exists() else file_path

        if not file_path.exists():
            print(f"Missing image file: {filename}")
            continue

        object_path = f"{batch_id}/{filename}"
        storage_path = f"materials/{object_path}"
        public_url = f"{supabase_url}/storage/v1/object/public/{storage_path}"

        mime_type, _ = mimetypes.guess_type(str(file_path))
        mime_type = mime_type or "image/jpeg"

        with open(file_path, "rb") as f:
            upload_result = storage.upload(
                object_path,
                f,
                {
                    "content-type": mime_type,
                    "upsert": "true",
                },
            )

        if isinstance(upload_result, dict) and upload_result.get("error"):
            print(f"Upload failed: {filename} -> {upload_result['error']}")
            continue

        material_data = {
            "image_url": public_url,
            "storage_path": storage_path,
            "status": "pending",
            "score": item.get("score", 0),
            "face_ratio": item.get("face_ratio"),
            "sharpness": item.get("sharpness"),
            "resolution": item.get("resolution"),
            "source_note_id": (filename.split("_")[0] if "_" in filename else None),
            "source_keyword": None,
            "batch_id": batch_id,
            "tags": [],
            "style": None,
            "mood": None,
        }

        existing = (
            supabase.table("materials")
            .select("id")
            .eq("storage_path", storage_path)
            .limit(1)
            .execute()
        )

        if existing.data:
            supabase.table("materials").update(material_data).eq(
                "storage_path", storage_path
            ).execute()
        else:
            supabase.table("materials").insert(material_data).execute()

        uploaded += 1
        print(f"Uploaded {uploaded}/{len(passed_images)}: {filename}")

    batch_data = {
        "id": batch_id,
        "keyword": None,
        "total_collected": report.get("total", 0),
        "total_passed": report.get("passed", 0),
        "total_uploaded": uploaded,
    }

    supabase.table("batches").upsert(batch_data, on_conflict="id").execute()

    print(f"Done. Uploaded {uploaded} images to batch {batch_id}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
