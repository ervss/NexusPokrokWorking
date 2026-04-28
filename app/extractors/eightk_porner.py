import re
import logging
import requests
from .base import VideoExtractor
from typing import Optional, Dict, Any

class EightKPornerExtractor(VideoExtractor):
    @property
    def name(self) -> str:
        return "8KPorner"
    
    @property
    def domains(self):
        return ["8kporner.com"]
    
    def can_handle(self, url: str) -> bool:
        return any(domain in url for domain in self.domains)

    async def extract(self, url: str) -> Optional[Dict[str, Any]]:
        logging.info(f"Extracting metadata from 8KPorner: {url}")
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Referer': 'https://8kporner.com/'
        }
        
        try:
            resp = requests.get(url, headers=headers, timeout=10)
            if resp.status_code != 200:
                return None
            
            html = resp.text
            stream_url = None
            
            # Look for source tags or script variables
            # Pattern 1: <source src="..."
            source_match = re.search(r'<source\s+src=["\'](https?://[^"\']+\.mp4[^"\']*)["\']', html, re.IGNORECASE)
            if source_match:
                stream_url = source_match.group(1)
            
            # Pattern 2: "file": "..." (common in JWPlayer/VideoJS configs)
            if not stream_url:
                file_match = re.search(r'["\']file["\']\s*:\s*["\'](https?://[^"\']+\.mp4[^"\']*)["\']', html)
                if file_match:
                    stream_url = file_match.group(1)

            if not stream_url:
                return None

            # Metadata
            title = "8KPorner Video"
            title_match = re.search(r'<title>(.*?)</title>', html)
            if title_match:
                title = title_match.group(1).split('|')[0].split('-')[0].strip()
            
            thumb_url = None
            thumb_match = re.search(r'<meta\s+property="og:image"\s+content="([^"]+)"', html)
            if thumb_match:
                thumb_url = thumb_match.group(1)
            
            return {
                "id": None,
                "title": title,
                "description": "",
                "thumbnail": thumb_url,
                "duration": 0,
                "stream_url": stream_url,
                "width": 0,
                "height": 0,
                "tags": [],
                "views": 0,
                "upload_date": None,
                "uploader": "",
                "is_hls": ".m3u8" in stream_url
            }
        except Exception as e:
            logging.error(f"8KPorner extraction failed: {e}")
            return None
