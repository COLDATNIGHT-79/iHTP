"""
Image Proxy - Server-side image fetching to bypass CORS/hotlink restrictions
"""
import httpx
import re
import os
from typing import Optional, Tuple

# Use /tmp for cache on serverless platforms like Render
CACHE_DIR = "/tmp/image_cache"
os.makedirs(CACHE_DIR, exist_ok=True)

async def resolve_image_url(url: str) -> str:
    """Resolve a URL to a direct image URL."""
    if not url:
        return ""
    
    url = url.strip()
    
    # Already a direct image
    if re.search(r'\.(jpg|jpeg|png|gif|webp)(\?.*)?$', url, re.I):
        return url
    
    # Known CDNs - pass through
    direct_domains = [
        'i.imgur.com', 'cdn.discordapp.com', 'media.discordapp.net',
        'pbs.twimg.com', 'media.giphy.com', 'i.redd.it'
    ]
    for domain in direct_domains:
        if domain in url.lower():
            return url
    
    # Imgur page -> direct
    imgur_match = re.match(r'https?://(?:www\.)?imgur\.com/(\w+)$', url)
    if imgur_match:
        return f"https://i.imgur.com/{imgur_match.group(1)}.jpg"
    
    # Giphy page -> direct
    giphy_match = re.search(r'giphy\.com/gifs/(?:.*-)?(\w+)', url)
    if giphy_match:
        return f"https://media.giphy.com/media/{giphy_match.group(1)}/giphy.gif"
    
    # Instagram - extract og:image
    if 'instagram.com/p/' in url:
        try:
            async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                }
                response = await client.get(url, headers=headers)
                if response.status_code == 200:
                    patterns = [
                        r'property="og:image"\s+content="([^"]+)"',
                        r'content="([^"]+)"\s+property="og:image"',
                    ]
                    for pattern in patterns:
                        match = re.search(pattern, response.text)
                        if match:
                            return match.group(1).replace('\\u0026', '&')
        except:
            pass
    
    return url


async def fetch_image(url: str) -> Tuple[Optional[bytes], str]:
    """Fetch image bytes from URL."""
    try:
        resolved = await resolve_image_url(url)
        
        async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'image/*,*/*',
            }
            response = await client.get(resolved, headers=headers)
            
            if response.status_code == 200:
                content_type = response.headers.get('content-type', 'image/jpeg')
                return response.content, content_type
        
        return None, "Failed to fetch"
    except Exception as e:
        return None, str(e)


async def get_cached_or_fetch(url: str) -> Tuple[Optional[bytes], str]:
    """Get image from cache or fetch it."""
    import hashlib
    
    url_hash = hashlib.md5(url.encode()).hexdigest()
    cache_path = f"{CACHE_DIR}/{url_hash}.jpg"
    
    # Check cache
    if os.path.exists(cache_path):
        with open(cache_path, 'rb') as f:
            return f.read(), 'image/jpeg'
    
    # Fetch and cache
    data, content_type = await fetch_image(url)
    if data:
        try:
            with open(cache_path, 'wb') as f:
                f.write(data)
        except:
            pass
    
    return data, content_type
