"""
PornHat Video Extractor
Handles direct video page imports from PornHat.
"""
import logging
import re
from typing import Any, Dict, Optional

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class PornHatExtractor:
    @property
    def name(self) -> str:
        return "PornHat"

    @property
    def domains(self):
        return ["pornhat.com", "www.pornhat.com"]

    def can_handle(self, url: str) -> bool:
        low = (url or "").lower()
        return any(domain in low for domain in self.domains)

    async def extract(self, url: str) -> Optional[Dict[str, Any]]:
        try:
            headers = {
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/124.0.0.0 Safari/537.36"
                ),
                "Referer": "https://www.pornhat.com/",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            }

            resp = requests.get(url, headers=headers, timeout=15)
            if resp.status_code != 200:
                logger.warning("PornHat: HTTP %s for %s", resp.status_code, url)
                return None

            html = resp.text
            soup = BeautifulSoup(html, "html.parser")

            def _clean_url(value: str) -> str:
                value = (value or "").strip()
                if value.startswith("//"):
                    return f"https:{value}"
                return value

            title = ""
            og_title = soup.find("meta", property="og:title")
            if og_title:
                title = (og_title.get("content") or "").strip()
            if not title:
                title_tag = soup.find("title")
                if title_tag:
                    title = re.sub(r"\s*[-|]\s*PornHat.*$", "", title_tag.get_text(" ", strip=True), flags=re.I).strip()

            thumbnail = ""
            og_image = soup.find("meta", property="og:image")
            if og_image:
                thumbnail = _clean_url(og_image.get("content") or "")
            if not thumbnail:
                video_tag = soup.find("video")
                if video_tag:
                    thumbnail = _clean_url(video_tag.get("poster") or "")

            stream_url = ""
            width = 0
            height = 0
            best_score = -1
            video_tag = soup.find("video")
            if video_tag:
                for source in video_tag.find_all("source"):
                    src = _clean_url(source.get("src") or "")
                    if not src:
                        continue
                    label = ((source.get("label") or source.get("title") or "")).lower()
                    match = re.search(r"(\d{3,4})p", label)
                    source_height = int(match.group(1)) if match else 0
                    score = source_height
                    if "auto" in label and source_height == 0:
                        score = 1
                    if score > best_score:
                        best_score = score
                        stream_url = src
                        height = source_height

            if not stream_url:
                mp4_matches = re.findall(r'https?://[^"\']+\.mp4[^"\']*', html, re.I)
                for candidate in mp4_matches:
                    if "/get_file/" in candidate:
                        stream_url = candidate
                        q = re.search(r"_(\d{3,4})p\.mp4", candidate, re.I)
                        height = int(q.group(1)) if q else 0
                        break

            if not stream_url:
                logger.warning("PornHat: no stream URL found for %s", url)
                return None

            if height:
                width = int(height * 16 / 9)

            duration = 0
            duration_sources = []
            duration_sources.extend(el.get_text(" ", strip=True) for el in soup.select(".duration"))
            duration_sources.extend(el.get_text(" ", strip=True) for el in soup.select(".thumb-bl-info li"))
            duration_sources.extend(el.get_text(" ", strip=True) for el in soup.select(".video-meta li"))
            for text in duration_sources:
                match = re.search(r"\b(\d{1,2}:\d{2}(?::\d{2})?)\b", text)
                if not match:
                    continue
                parts = [int(p) for p in match.group(1).split(":")]
                duration = parts[0] * 60 + parts[1] if len(parts) == 2 else parts[0] * 3600 + parts[1] * 60 + parts[2]
                if duration:
                    break

            tags = []
            seen = set()
            for anchor in soup.select('a[href*="/tags/"], a[href*="/categories/"], .tags a'):
                tag = anchor.get_text(" ", strip=True)
                tag_low = tag.lower()
                if not tag or tag_low == "tags" or tag_low in seen:
                    continue
                seen.add(tag_low)
                tags.append(tag)

            description = ""
            desc_meta = soup.find("meta", attrs={"name": "description"})
            if desc_meta:
                description = (desc_meta.get("content") or "").strip()

            upload_date = None
            full_text = soup.get_text(" ", strip=True)
            date_match = re.search(r"\b(\d{2}\.\d{2}\.\d{4})\b", full_text)
            if date_match:
                upload_date = date_match.group(1)

            views = 0
            views_match = re.search(r"\b([\d.,]+)\s+views\b", full_text, re.I)
            if views_match:
                try:
                    views = int(views_match.group(1).replace(",", "").replace(".", ""))
                except Exception:
                    views = 0

            video_id = ""
            id_match = re.search(r"/video/([^/?#]+)/?", resp.url)
            if id_match:
                video_id = id_match.group(1)

            return {
                "id": video_id or None,
                "title": title or "PornHat Video",
                "description": description,
                "thumbnail": thumbnail,
                "duration": duration,
                "stream_url": stream_url,
                "width": width,
                "height": height,
                "tags": tags,
                "views": views,
                "upload_date": upload_date,
                "uploader": "",
                "is_hls": False,
                "quality": f"{height}p" if height else None,
            }
        except Exception as exc:
            logger.error("PornHat extraction failed for %s: %s", url, exc, exc_info=True)
            return None
