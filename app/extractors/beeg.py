"""
Beeg extractor.

Extension-first support still means backend should be able to:
- refresh metadata from a Beeg detail page
- prefer master playlists / highest quality variants over the first captured stream
- fall back gracefully when only partial page metadata is available
"""
from __future__ import annotations

import logging
import re
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class BeegExtractor:
    USER_AGENT = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )

    @property
    def name(self) -> str:
        return "Beeg"

    @property
    def domains(self):
        return ["beeg.com", "www.beeg.com", "video.beeg.com"]

    def can_handle(self, url: str) -> bool:
        low = (url or "").lower()
        return any(domain in low for domain in self.domains)

    def is_playable_stream(self, url: str) -> bool:
        low = (url or "").strip().lower()
        if not low.startswith(("http://", "https://")):
            return False
        if self._is_watch_page(low) or self._is_transport_segment(low):
            return False
        if ".m3u8" in low or ".mp4" in low:
            return True
        return False

    async def extract(self, url: str) -> Optional[Dict[str, Any]]:
        try:
            page_url = self._normalize_url(url)
            if not page_url:
                return None

            html, final_url = self._fetch_text(page_url, referer="https://beeg.com/")
            if not html:
                logger.warning("Beeg: empty HTML for %s", page_url)
                return self._fallback_result(page_url)

            soup = BeautifulSoup(html, "html.parser")
            title = self._extract_title(soup, html, final_url)
            thumbnail = self._extract_thumbnail(soup, html, final_url)
            duration = self._extract_duration(soup, html)
            uploader = self._extract_uploader(soup)
            views = self._extract_views(soup, html)

            candidates = self._collect_media_candidates(soup, html, final_url)
            best_stream, width, height, is_hls = self._resolve_best_stream(candidates, referer=final_url)
            size_bytes = self._head_size(best_stream, referer=final_url) if best_stream else 0

            return {
                "id": self._extract_id(final_url) or None,
                "title": title or "Beeg Video",
                "description": "",
                "thumbnail": thumbnail,
                "duration": duration,
                "stream_url": best_stream or "",
                "width": width,
                "height": height,
                "tags": [],
                "views": views,
                "uploader": uploader,
                "is_hls": is_hls,
                "quality": self._quality_label(height),
                "size_bytes": size_bytes,
                "source_url": final_url,
            }
        except Exception as exc:
            logger.error("Beeg extraction failed for %s: %s", url, exc, exc_info=True)
            return self._fallback_result(url)

    def _fallback_result(self, url: str) -> Dict[str, Any]:
        return {
            "id": self._extract_id(url) or None,
            "title": self._title_from_url(url) or "Beeg Video",
            "description": "",
            "thumbnail": "",
            "duration": 0,
            "stream_url": "",
            "width": 0,
            "height": 0,
            "tags": [],
            "views": 0,
            "uploader": "",
            "is_hls": False,
            "quality": "SD",
            "size_bytes": 0,
            "source_url": self._normalize_url(url),
        }

    def _fetch_text(self, url: str, referer: str = "") -> Tuple[str, str]:
        headers = {
            "User-Agent": self.USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        }
        if referer:
            headers["Referer"] = referer
        resp = requests.get(url, headers=headers, timeout=20, allow_redirects=True)
        if resp.status_code >= 400:
            return "", url
        return resp.text or "", resp.url or url

    def _normalize_url(self, value: str) -> str:
        raw = str(value or "").strip()
        if not raw:
            return ""
        if raw.startswith("//"):
            return f"https:{raw}"
        if raw.startswith("http://") or raw.startswith("https://"):
            return raw
        return ""

    def _extract_id(self, url: str) -> str:
        m = re.search(r"/-(\d+)", str(url or ""))
        return m.group(1) if m else ""

    def _title_from_url(self, url: str) -> str:
        raw = str(url or "").split("/")[-1]
        raw = re.sub(r"^-\d+", "", raw).strip("-_ ")
        return raw.replace("-", " ").replace("_", " ").strip().title()

    def _extract_title(self, soup: BeautifulSoup, html: str, base_url: str) -> str:
        for value in (
            soup.select_one('meta[property="og:title"]'),
            soup.select_one('meta[name="twitter:title"]'),
        ):
            content = (value.get("content") or "").strip() if value else ""
            if content:
                return re.sub(r"\s*\|\s*Beeg.*$", "", content, flags=re.I).strip()

        h1 = soup.find("h1")
        if h1:
            text = h1.get_text(" ", strip=True)
            if text:
                return text

        json_title = re.search(r'"title"\s*:\s*"([^"]{3,300})"', html)
        if json_title:
            return json_title.group(1).strip()

        title_tag = soup.find("title")
        if title_tag:
            text = title_tag.get_text(" ", strip=True)
            if text:
                return re.sub(r"\s*\|\s*Beeg.*$", "", text, flags=re.I).strip()

        return self._title_from_url(base_url)

    def _extract_thumbnail(self, soup: BeautifulSoup, html: str, base_url: str) -> str:
        candidates: List[str] = []
        for node in soup.select('meta[property="og:image"], meta[name="twitter:image"], video[poster], img[src], img[data-src]'):
            raw = (
                node.get("content")
                or node.get("poster")
                or node.get("data-src")
                or node.get("src")
                or ""
            )
            if raw:
                candidates.append(raw)

        regex_matches = re.findall(r'https?://[^"\']+\.(?:jpg|jpeg|png|webp)(?:\?[^"\']*)?', html, re.I)
        candidates.extend(regex_matches)

        for raw in candidates:
            absolute = self._abs(raw, base_url)
            if not absolute:
                continue
            if re.search(r"avatar|logo|icon|sprite|pixel|blank", absolute, re.I):
                continue
            return absolute
        return ""

    def _extract_duration(self, soup: BeautifulSoup, html: str) -> int:
        meta_duration = soup.select_one('meta[property="og:video:duration"]')
        if meta_duration:
            try:
                value = int(float(meta_duration.get("content") or "0"))
                if value > 0:
                    return value
            except Exception:
                pass

        for text in (
            soup.get_text(" ", strip=True),
            html,
        ):
            match = re.search(r"\b(\d{1,2}):(\d{2})(?::(\d{2}))?\b", text or "")
            if not match:
                continue
            if match.group(3):
                return int(match.group(1)) * 3600 + int(match.group(2)) * 60 + int(match.group(3))
            return int(match.group(1)) * 60 + int(match.group(2))
        return 0

    def _extract_uploader(self, soup: BeautifulSoup) -> str:
        for selector in (
            '[data-testid="unit-avatar"] img[alt]',
            '[data-testid="unit-avatar"]',
            '[itemprop="author"]',
        ):
            node = soup.select_one(selector)
            if not node:
                continue
            value = (node.get("alt") or node.get_text(" ", strip=True) or "").strip()
            if value:
                return value
        return ""

    def _extract_views(self, soup: BeautifulSoup, html: str) -> int:
        text = f"{soup.get_text(' ', strip=True)} {html}"
        m = re.search(r"([\d,.]+)\s*(K|M|B)?\s+likes", text, re.I)
        if not m:
            m = re.search(r"([\d,.]+)\s*(K|M|B)?\s+views", text, re.I)
        if not m:
            return 0
        try:
            num = float(m.group(1).replace(",", ""))
            scale = {"K": 1_000, "M": 1_000_000, "B": 1_000_000_000}.get((m.group(2) or "").upper(), 1)
            return int(num * scale)
        except Exception:
            return 0

    def _collect_media_candidates(self, soup: BeautifulSoup, html: str, base_url: str) -> List[str]:
        candidates: List[str] = []
        for node in soup.select(
            'video[src], video source[src], source[src], meta[property="og:video"], '
            'meta[property="og:video:url"], meta[property="og:video:secure_url"], '
            'meta[itemprop="contentUrl"], meta[name="twitter:player:stream"]'
        ):
            raw = node.get("src") or node.get("content") or ""
            if raw:
                candidates.append(self._abs(raw, base_url))

        regexes = [
            r'https?://[^"\']+video\.beeg\.com[^"\']+',
            r'https?://[^"\']+\.(?:m3u8|mp4)(?:\?[^"\']*)?',
            r'(?:https?:)?//[^"\']+\.(?:m3u8|mp4)(?:\?[^"\']*)?',
        ]
        for pattern in regexes:
            candidates.extend([self._abs(m, base_url) for m in re.findall(pattern, html, re.I)])

        # JSON style `"url":"https:\/\/video.beeg.com\/..."`
        for match in re.findall(r'"url"\s*:\s*"(https?:\\?/\\?/[^"]+)"', html, re.I):
            candidates.append(self._abs(match.replace("\\/", "/"), base_url))

        deduped: List[str] = []
        seen = set()
        for candidate in candidates:
            if not candidate or candidate in seen:
                continue
            seen.add(candidate)
            deduped.append(candidate)
        return deduped

    def _resolve_best_stream(self, candidates: List[str], referer: str = "") -> Tuple[str, int, int, bool]:
        best_url = ""
        best_score = -1
        best_width = 0
        best_height = 0
        best_is_hls = False

        for candidate in candidates or []:
            candidate = self._normalize_url(candidate)
            if not candidate:
                continue
            if self._is_transport_segment(candidate) or self._is_watch_page(candidate):
                continue

            resolved_url = candidate
            width = 0
            height = self._infer_height(candidate)
            is_hls = ".m3u8" in candidate.lower() or "multi=" in candidate.lower()

            if is_hls:
                parsed = self._resolve_master_playlist(candidate, referer=referer)
                if parsed:
                    resolved_url, width, height = parsed
                    is_hls = True
                elif height == 0:
                    height = 240

            score = height * 100 + (1 if is_hls else 0)
            if "video.beeg.com" in candidate.lower():
                score += 5
            if "vp.externulls.com" in candidate.lower():
                score -= 10
            if score > best_score:
                best_score = score
                best_url = resolved_url
                best_width = width or self._width_for_height(height)
                best_height = height
                best_is_hls = is_hls

        return best_url, best_width, best_height, best_is_hls

    def _resolve_master_playlist(self, playlist_url: str, referer: str = "") -> Optional[Tuple[str, int, int]]:
        headers = {"User-Agent": self.USER_AGENT, "Accept": "*/*"}
        if referer:
            headers["Referer"] = referer
        try:
            resp = requests.get(playlist_url, headers=headers, timeout=15, allow_redirects=True)
            if resp.status_code >= 400:
                return None
            text = resp.text or ""
            lines = [line.strip() for line in text.splitlines() if line.strip()]
            best = None
            for idx, line in enumerate(lines):
                if not line.startswith("#EXT-X-STREAM-INF"):
                    continue
                if idx + 1 >= len(lines):
                    continue
                stream_line = lines[idx + 1]
                bw_match = re.search(r"BANDWIDTH=(\d+)", line)
                res_match = re.search(r"RESOLUTION=(\d+)x(\d+)", line)
                height = int(res_match.group(2)) if res_match else self._infer_height(stream_line)
                width = int(res_match.group(1)) if res_match else self._width_for_height(height)
                bandwidth = int(bw_match.group(1)) if bw_match else 0
                score = (height * 10_000) + bandwidth
                abs_url = self._abs(stream_line, resp.url or playlist_url)
                if not abs_url:
                    continue
                if not best or score > best[0]:
                    best = (score, abs_url, width, height)
            if best:
                return best[1], best[2], best[3]
        except Exception as exc:
            logger.debug("Beeg master playlist parse failed for %s: %s", playlist_url, exc)
        return None

    def _head_size(self, url: str, referer: str = "") -> int:
        candidate = self._normalize_url(url)
        if not candidate:
            return 0
        headers = {"User-Agent": self.USER_AGENT, "Accept": "*/*"}
        if referer:
            headers["Referer"] = referer
        try:
            resp = requests.head(candidate, headers=headers, timeout=10, allow_redirects=True)
            content_length = resp.headers.get("Content-Length")
            if content_length and str(content_length).isdigit():
                return int(content_length)
        except Exception:
            pass
        return 0

    def _infer_height(self, value: str) -> int:
        match = re.search(r"(2160|1440|1080|720|480|360|240)(?:p)?(?:[^\d]|$)", str(value or ""), re.I)
        return int(match.group(1)) if match else 0

    def _width_for_height(self, height: int) -> int:
        return {
            2160: 3840,
            1440: 2560,
            1080: 1920,
            720: 1280,
            480: 854,
            360: 640,
            240: 426,
        }.get(int(height or 0), 0)

    def _quality_label(self, height: int) -> str:
        h = int(height or 0)
        if h >= 2160:
            return "4K"
        if h >= 1440:
            return "1440p"
        if h >= 1080:
            return "1080p"
        if h >= 720:
            return "720p"
        if h >= 480:
            return "480p"
        if h >= 360:
            return "360p"
        if h >= 240:
            return "240p"
        return "SD"

    def _is_watch_page(self, raw: str) -> bool:
        low = (raw or "").lower()
        return bool(re.search(r"^https?://(?:www\.)?beeg\.com/-\d+", low))

    def _is_transport_segment(self, raw: str) -> bool:
        low = (raw or "").lower()
        return bool(
            low.endswith(".ts")
            or ".ts?" in low
            or "/seg-" in low
        )

    def _abs(self, raw: str, base_url: str) -> str:
        value = str(raw or "").strip()
        if not value:
            return ""
        value = value.replace("\\/", "/")
        if value.startswith("//"):
            return f"https:{value}"
        if value.startswith("http://") or value.startswith("https://"):
            return value
        try:
            return urljoin(base_url, value)
        except Exception:
            return ""
