import argparse
import asyncio
import re
import sys
from pathlib import Path
from typing import Optional

# Allow running as: python scripts/fix_bunkr_stream_urls.py
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.database import SessionLocal, Video
from app.extractors.bunkr import BunkrExtractor


def is_bunkr_page_url(url: Optional[str]) -> bool:
    u = (url or "").lower()
    if "bunkr." not in u:
        return False
    return bool(re.search(r"/(f|v)/", u))


def is_direct_stream_url(url: Optional[str]) -> bool:
    u = (url or "").lower()
    return u.startswith(("http://", "https://")) and (
        bool(re.search(r"\.(mp4|mkv|webm|m4v|mov)(\?|$)", u))
        or "scdn.st" in u
        or "media-files" in u
        or "stream-files" in u
    )


def pick_candidates(db, limit: int):
    q = (
        db.query(Video)
        .filter(Video.source_url.isnot(None))
        .filter(Video.source_url.ilike("%bunkr.%"))
        .order_by(Video.id.desc())
    )
    out = []
    for v in q.all():
        if is_bunkr_page_url(v.source_url) or is_bunkr_page_url(v.url):
            out.append(v)
        if len(out) >= limit:
            break
    return out


def main():
    parser = argparse.ArgumentParser(description="Resolve Bunkr page URLs to direct stream URLs")
    parser.add_argument("--limit", type=int, default=100, help="Max records to scan")
    parser.add_argument("--apply", action="store_true", help="Persist fixes")
    args = parser.parse_args()

    db = SessionLocal()
    extractor = BunkrExtractor()
    scanned = 0
    fixed = 0
    unresolved = 0

    try:
        videos = pick_candidates(db, args.limit)
        for v in videos:
            scanned += 1
            source = v.source_url or v.url or ""
            try:
                res = asyncio.run(extractor.extract(source))
            except Exception:
                res = None
            new_url = (res or {}).get("stream_url") if res else None
            if is_direct_stream_url(new_url):
                if new_url != v.url:
                    fixed += 1
                    print(f"[FIX] id={v.id} -> {new_url[:120]}")
                    if args.apply:
                        v.url = new_url
                else:
                    print(f"[OK] id={v.id} already direct")
            else:
                unresolved += 1
                print(f"[MISS] id={v.id} source={source[:120]}")

        if args.apply and fixed > 0:
            db.commit()

        mode = "APPLY" if args.apply else "DRY-RUN"
        print(f"[{mode}] scanned={scanned} fixed={fixed} unresolved={unresolved}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
