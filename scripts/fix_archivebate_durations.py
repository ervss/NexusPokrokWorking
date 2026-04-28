#!/usr/bin/env python3
"""
One-off repair tool for Archivebate durations in DB.

Strategy:
1) Prefer duration already present on sibling rows with same media key
   (same /v2/<id>.mp4 or /e/<id>), because these typically come from extension
   imports and are the most trustworthy.
2) If no sibling duration exists, try extractor metadata from source_url.

Default mode is dry-run. Use --apply to persist changes.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Dict, Optional

# Add repo root for local imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import SessionLocal, Video  # noqa: E402
from app.extractors.archivebate import ArchivebateExtractor  # noqa: E402


def media_key(url: str) -> str:
    u = (url or "").lower()
    m = re.search(r"/v2/([a-z0-9_-]+)\.mp4", u, re.I)
    if m:
        return f"v2:{m.group(1).lower()}"
    m = re.search(r"/e/([a-z0-9_-]+)", u, re.I)
    if m:
        return f"e:{m.group(1).lower()}"
    return ""


def is_archivebate_row(v: Video) -> bool:
    src = (v.source_url or "").lower()
    url = (v.url or "").lower()
    return "archivebate.com/watch/" in src or "archivebate.com" in src or "mxcontent.net" in url


def build_known_duration_map(videos: list[Video]) -> Dict[str, float]:
    by_key: Dict[str, float] = {}
    for v in videos:
        dur = float(v.duration or 0)
        if dur <= 0:
            continue
        key = media_key(v.url or "")
        if not key:
            continue
        # Keep larger non-zero duration if multiple variants exist.
        by_key[key] = max(by_key.get(key, 0.0), dur)
    return by_key


def extractor_duration(extractor: ArchivebateExtractor, source_url: str) -> float:
    if not source_url:
        return 0.0
    try:
        import asyncio

        res = asyncio.run(extractor.extract(source_url))
        return float((res or {}).get("duration") or 0)
    except Exception:
        return 0.0


def browser_duration(source_url: str, timeout_ms: int = 30000) -> float:
    if not source_url:
        return 0.0
    try:
        import asyncio
        from playwright.async_api import async_playwright

        async def _run() -> float:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                context = await browser.new_context(
                    user_agent=(
                        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
                    )
                )
                page = await context.new_page()
                await page.goto(source_url, wait_until="domcontentloaded", timeout=timeout_ms)

                async def _duration_in_frame(frame) -> float:
                    try:
                        d = await frame.evaluate(
                            "() => { const v = document.querySelector('video'); return v ? Number(v.duration || 0) : 0; }"
                        )
                        return float(d or 0)
                    except Exception:
                        return 0.0

                d = await _duration_in_frame(page.main_frame)
                if d > 0 and d < 86400:
                    await browser.close()
                    return d

                deadline = asyncio.get_event_loop().time() + (timeout_ms / 1000.0)
                while asyncio.get_event_loop().time() < deadline:
                    for fr in page.frames:
                        try:
                            await fr.evaluate(
                                "() => { const b = document.querySelector('.vjs-big-play-button, .jw-icon-playback'); if (b) b.click(); }"
                            )
                        except Exception:
                            pass

                    await page.wait_for_timeout(1200)

                    for fr in page.frames:
                        d = await _duration_in_frame(fr)
                        if d > 0 and d < 86400:
                            await browser.close()
                            return d

                await browser.close()
                return 0.0

        return float(asyncio.run(_run()) or 0.0)
    except Exception:
        return 0.0


def main() -> int:
    parser = argparse.ArgumentParser(description="Repair Archivebate durations in videos table.")
    parser.add_argument("--apply", action="store_true", help="Persist updates to DB.")
    parser.add_argument("--limit", type=int, default=0, help="Process at most N candidate rows (0 = all).")
    parser.add_argument(
        "--mode",
        choices=["missing_only", "all"],
        default="missing_only",
        help="missing_only = only rows with duration<=0, all = check every Archivebate row",
    )
    parser.add_argument(
        "--use-browser",
        action="store_true",
        help="Enable heavy Playwright fallback to read duration from embedded player.",
    )
    parser.add_argument(
        "--browser-timeout-ms",
        type=int,
        default=20000,
        help="Per-row browser fallback timeout in milliseconds (used with --use-browser).",
    )
    args = parser.parse_args()

    db = SessionLocal()
    try:
        all_rows = db.query(Video).all()
        archive_rows = [v for v in all_rows if is_archivebate_row(v)]
        known_map = build_known_duration_map(archive_rows)
        extractor = ArchivebateExtractor()

        candidates = []
        for v in archive_rows:
            dur = float(v.duration or 0)
            if args.mode == "missing_only" and dur > 0:
                continue
            candidates.append(v)

        if args.limit and args.limit > 0:
            candidates = candidates[: args.limit]

        scanned = 0
        fixed = 0
        from_sibling = 0
        from_extractor = 0
        from_browser = 0

        for v in candidates:
            scanned += 1
            old_dur = float(v.duration or 0)

            new_dur: float = 0.0
            key = media_key(v.url or "")
            if key and known_map.get(key, 0) > 0:
                new_dur = float(known_map[key])
                source = "sibling"
            else:
                new_dur = extractor_duration(extractor, v.source_url or "")
                source = "extractor"
                if new_dur <= 0 and args.use_browser:
                    new_dur = browser_duration(v.source_url or "", timeout_ms=args.browser_timeout_ms)
                    if new_dur > 0:
                        source = "browser"

            if new_dur <= 0:
                continue

            # In all mode avoid downgrades; in missing_only old duration is typically 0.
            if args.mode == "all" and old_dur > 0 and new_dur <= old_dur:
                continue

            if abs(new_dur - old_dur) < 0.5:
                continue

            print(
                f"[FIX] id={v.id} duration {old_dur:.1f}s -> {new_dur:.1f}s "
                f"({source}) title={repr((v.title or '')[:80])}"
            )
            if args.apply:
                v.duration = new_dur
            fixed += 1
            if source == "sibling":
                from_sibling += 1
            elif source == "browser":
                from_browser += 1
            else:
                from_extractor += 1

        if args.apply and fixed > 0:
            db.commit()
        elif args.apply:
            db.rollback()

        mode_txt = "APPLY" if args.apply else "DRY-RUN"
        print(
            f"\n[{mode_txt}] scanned={scanned} fixed={fixed} "
            f"(sibling={from_sibling}, extractor={from_extractor}, browser={from_browser})"
        )
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())
