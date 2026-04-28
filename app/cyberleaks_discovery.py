"""
CyberLeaks Discovery Module
"""
import logging
import re
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

_BASE_URL = "https://cyberleaks.top/"
_UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"

def _extract_from_listing(card) -> Optional[Dict[str, Any]]:
    try:
        link = card.find("a", href=True)
        if not link:
            return None

        video_url = urljoin(_BASE_URL, link["href"])
        
        title_el = card.find("h3")
        title = title_el.get_text(strip=True) if title_el else ""
        
        img = card.find("img")
        thumbnail = img.get("src") if img else None
        if thumbnail and thumbnail.startswith("/"):
            thumbnail = urljoin(_BASE_URL, thumbnail)

        return {
            "title": title,
            "url": video_url,
            "thumbnail": thumbnail,
            "duration": 0,
            "quality": "HD",
            "resolution": 720,
            "upload_type": "leak",
            "views": 0,
            "stream_url": None,
            "source": "cyberleaks",
        }
    except Exception as exc:
        logger.warning("[CYBERLEAKS_DISCOVERY] Failed to parse listing card: %s", exc)
        return None

def scrape_cyberleaks_discovery(
    keyword: str = "",
    pages: int = 1,
    min_duration: int = 0,
    sort: str = "latest",
    tag: str = "tape"
) -> List[Dict[str, Any]]:
    """
    Discover videos from CyberLeaks listing pages.
    """
    pages = min(max(int(pages or 1), 1), 10)
    keyword_norm = (keyword or "").strip().lower()

    headers = {
        "User-Agent": _UA,
        "Referer": _BASE_URL,
    }

    results: List[Dict[str, Any]] = []
    seen_urls = set()

    # If tag is provided, use tag URL
    base_scrape_url = f"{_BASE_URL}tag/{tag}" if tag else _BASE_URL

    for page_num in range(1, pages + 1):
        try:
            if page_num == 1:
                page_url = base_scrape_url
            else:
                # CyberLeaks uses ?page=N or similar if it supports it, 
                # but based on Next.js it might be /page/N or just query.
                # Let's assume ?page=N for now or just skip pagination if unknown.
                page_url = f"{base_scrape_url}?page={page_num}"

            resp = requests.get(page_url, headers=headers, timeout=20)
            if resp.status_code != 200:
                logger.warning("[CYBERLEAKS_DISCOVERY] Page %s returned %s", page_num, resp.status_code)
                continue

            soup = BeautifulSoup(resp.text, "html.parser")
            # Cards are divs with specific classes
            cards = soup.find_all("div", class_=re.compile(r"rounded-lg overflow-hidden shadow-lg", re.I))
            logger.info("[CYBERLEAKS_DISCOVERY] Page %s yielded %s listing cards", page_num, len(cards))

            for card in cards:
                item = _extract_from_listing(card)
                if not item or not item.get("url"):
                    continue
                if item["url"] in seen_urls:
                    continue
                seen_urls.add(item["url"])

                if keyword_norm and keyword_norm not in (item.get("title") or "").lower():
                    continue

                results.append(item)
        except Exception as exc:
            logger.error("[CYBERLEAKS_DISCOVERY] Error on page %s: %s", page_num, exc)

    return results
