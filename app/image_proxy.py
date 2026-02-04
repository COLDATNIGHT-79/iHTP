"""
Image Proxy - Server-side image fetching to bypass CORS/hotlink restrictions

This module provides:
1. URL resolution (Instagram og:image extraction, Imgur transforms, etc.)
2. Image fetching and caching
3. A proxy endpoint for serving images
"""
import httpx
import re
import hashlib
from typing import Optional, Tuple
from pathlib import Path

# Simple file-based cache for resolved URLs
CACHE_DIR = Path(__file__).parent.parent / "image_cache"
CACHE_DIR.mkdir(exist_ok=True)

async def resolve_image_url(url: str) -> str:
    """
    Resolve a URL to a direct image URL.
    Handles Instagram, Imgur, Twitter, etc.
    """
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
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
                }
                response = await client.get(url, headers=headers)
                if response.status_code == 200:
                    # Try multiple og:image patterns
                    patterns = [
                        r'property="og:image"\s+content="([^"]+)"',
                        r'content="([^"]+)"\s+property="og:image"',
                        r'"display_url":"([^"]+)"',
                        r'"src":"(https://[^"]+\.jpg[^"]*)"'
                    ]
                    for pattern in patterns:
                        match = re.search(pattern, response.text)
                        if match:
                            img_url = match.group(1).replace('\\u0026', '&')
                            return img_url
        except Exception as e:
            print(f"Instagram resolution failed: {e}")
    
    # Twitter/X - extract og:image
    if 'twitter.com' in url or 'x.com' in url:
        try:
            async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
                headers = {'User-Agent': 'Twitterbot/1.0'}
                response = await client.get(url, headers=headers)
                if response.status_code == 200:
                    match = re.search(r'property="og:image"\s+content="([^"]+)"', response.text)
                    if match:
                        return match.group(1)
        except:
            pass
    
    # Fallback - return original
    return url


async def fetch_image(url: str) -> Tuple[Optional[bytes], str]:
    """
    Fetch image bytes from URL.
    Returns (bytes, content_type) or (None, error_message)
    """
    try:
        resolved = await resolve_image_url(url)
        
        async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'image/*,*/*',
                'Referer': 'https://www.google.com/'
            }
            response = await client.get(resolved, headers=headers)
            
            if response.status_code == 200:
                content_type = response.headers.get('content-type', 'image/jpeg')
                if 'image' in content_type or len(response.content) > 1000:
                    return response.content, content_type
        
        return None, "Failed to fetch image"
    except Exception as e:
        return None, str(e)


def get_cache_path(url: str) -> Path:
    """Get cache file path for a URL"""
    url_hash = hashlib.md5(url.encode()).hexdigest()
    return CACHE_DIR / f"{url_hash}.jpg"


async def get_cached_or_fetch(url: str) -> Tuple[Optional[bytes], str]:
    """Get image from cache or fetch it"""
    cache_path = get_cache_path(url)
    
    # Check cache first
    if cache_path.exists():
        return cache_path.read_bytes(), 'image/jpeg'
    
    # Fetch and cache
    data, content_type = await fetch_image(url)
    if data:
        try:
            cache_path.write_bytes(data)
        except:
            pass  # Cache write failed, that's ok
    
    return data, content_type
