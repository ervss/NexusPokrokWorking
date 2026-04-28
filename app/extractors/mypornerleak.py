import re
import logging
import requests
from .base import VideoExtractor
from typing import Optional, Dict, Any

class MyPornerLeakExtractor(VideoExtractor):
    @property
    def name(self) -> str:
        return "MyPornerLeak"
    
    @property
    def domains(self):
        return ["mypornerleak.com"]
    
    def can_handle(self, url: str) -> bool:
        return any(domain in url for domain in self.domains)

    async def extract(self, url: str) -> Optional[Dict[str, Any]]:
        logging.info(f"Extracting metadata from MyPornerLeak: {url}")
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Referer': 'https://mypornerleak.com/'
        }
        
        try:
            resp = requests.get(url, headers=headers, timeout=10)
            if resp.status_code != 200:
                return None
            
            html = resp.text
            stream_url = None
            
            # common patterns for WP-based adult sites
            patterns = [
                r'["\']file["\']\s*:\s*["\'](https?://[^"\']+\.mp4[^"\']*)["\']',
                r'<source\s+src=["\'](https?://[^"\']+\.mp4[^"\']*)["\']',
                r'video_url\s*=\s*["\'](https?://[^"\']+\.mp4[^"\']*)["\']'
            ]
            
            for p in patterns:
                match = re.search(p, html, re.IGNORECASE)
                if match:
                    stream_url = match.group(1).replace('\\/', '/')
                    break

            if not stream_url:
                return None

            title = "MyPornerLeak Video"
            title_match = re.search(r'<h1[^>]*>(.*?)</h1>', html)
            if title_match:
                title = title_match.group(1).strip()
            
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
            logging.error(f"MyPornerLeak extraction failed: {e}")
            return None
