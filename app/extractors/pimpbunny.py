import re
import logging
import requests
from .base import VideoExtractor
from typing import Optional, Dict, Any

class PimpBunnyExtractor(VideoExtractor):
    @property
    def name(self) -> str:
        return "PimpBunny"
    
    @property
    def domains(self):
        return ["pimpbunny.com"]
    
    def can_handle(self, url: str) -> bool:
        return any(domain in url for domain in self.domains)

    async def extract(self, url: str) -> Optional[Dict[str, Any]]:
        logging.info(f"Extracting metadata from PimpBunny: {url}")
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Referer': 'https://pimpbunny.com/'
        }
        
        try:
            resp = requests.get(url, headers=headers, timeout=10)
            if resp.status_code != 200:
                return None
            
            html = resp.text
            stream_url = None
            
            # PimpBunny often uses standard <video> tags or JS variables
            match = re.search(r'["\']?file["\']?\s*:\s*["\'](https?://[^"\']+\.mp4[^"\']*)["\']', html)
            if not match:
                match = re.search(r'<source\s+src=["\'](https?://[^"\']+\.mp4[^"\']*)["\']', html)
            
            if match:
                stream_url = match.group(1).replace('\\/', '/')

            if not stream_url:
                return None

            title = "PimpBunny Video"
            title_match = re.search(r'<title>(.*?)</title>', html)
            if title_match:
                title = title_match.group(1).split('|')[0].strip()
            
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
            logging.error(f"PimpBunny extraction failed: {e}")
            return None
