import logging
import re
import asyncio
from typing import Optional, Dict, Any, List
from bs4 import BeautifulSoup
import aiohttp
from .base import VideoExtractor

logger = logging.getLogger(__name__)

class CyberLeaksExtractor(VideoExtractor):
    @property
    def name(self) -> str:
        return "CyberLeaks"

    def can_handle(self, url: str) -> bool:
        return "cyberleaks.top" in url.lower()

    async def extract(self, url: str) -> Optional[Dict[str, Any]]:
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Referer': 'https://cyberleaks.top/'
            }
            async with aiohttp.ClientSession(headers=headers) as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                    if resp.status != 200:
                        return None
                    html = await resp.text()

            soup = BeautifulSoup(html, 'lxml')

            # Title
            title_el = soup.find('h3', class_=re.compile(r'text-2xl font-semibold', re.I))
            title = title_el.get_text(strip=True) if title_el else ""
            if not title:
                title = (soup.find('meta', property='og:title') or {}).get('content', '')
            if not title:
                title = soup.title.get_text(strip=True) if soup.title else "CyberLeaks Video"
            title = title.replace(' _ CyberLeaks', '').strip()

            # Thumbnail
            thumbnail = (soup.find('meta', property='og:image') or {}).get('content', '')

            # Video Iframe
            iframe = soup.find('iframe', title='player')
            stream_url = iframe.get('src') if iframe else None

            # Fallback to searching in scripts (Next.js data)
            if not stream_url:
                match = re.search(r'src\\":\\"(https?://[^"]+)\\"', html)
                if match:
                    stream_url = match.group(1).replace('\\/', '/')

            # Tags
            tags = []
            tag_container = soup.find('div', class_=re.compile(r'flex flex-wrap gap-2', re.I))
            if tag_container:
                tags = [a.get_text(strip=True) for a in tag_container.find_all('a')]

            if not stream_url:
                stream_url = url

            return {
                "id": url.rstrip('/').split('/')[-1],
                "title": title,
                "description": title,
                "thumbnail": thumbnail,
                "duration": 0.0,
                "stream_url": stream_url,
                "width": 0,
                "height": 720,
                "tags": tags,
                "uploader": "CyberLeaks",
                "is_hls": '.m3u8' in (stream_url or '').lower(),
            }
        except Exception as e:
            logger.error(f"CyberLeaks extraction failed for {url}: {e}")
            return None
