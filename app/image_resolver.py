"""
Image URL resolver - simple version
"""
import re
from typing import Optional

async def resolve_image_url(url: str) -> Optional[str]:
    """
    Resolve image URLs. For most URLs, just pass through.
    Only try to fetch/transform for specific social media patterns.
    """
    if not url:
        return None
    
    url = url.strip()
    
    # Direct image URLs - pass through as-is
    if re.search(r'\.(jpg|jpeg|png|gif|webp|bmp|svg)(\?.*)?$', url, re.I):
        return url
    
    # Known working CDNs - pass through
    direct_domains = [
        'i.imgur.com',
        'cdn.discordapp.com',
        'media.discordapp.net',
        'pbs.twimg.com',
        'media.giphy.com',
        'preview.redd.it',
        'i.redd.it',
    ]
    
    for domain in direct_domains:
        if domain in url.lower():
            return url
    
    # Imgur page to direct image (non-CDN imgur links)
    imgur_match = re.match(r'https?://(?:www\.)?imgur\.com/(?!a/)(\w+)(?:\.\w+)?$', url)
    if imgur_match:
        return f"https://i.imgur.com/{imgur_match.group(1)}.jpg"
    
    # Giphy page to direct gif
    giphy_match = re.match(r'https?://giphy\.com/gifs/(?:.*-)?(\w+)', url)
    if giphy_match:
        return f"https://media.giphy.com/media/{giphy_match.group(1)}/giphy.gif"
    
    # For Instagram - try to extract og:image (optional, may fail)
    if 'instagram.com/p/' in url:
        try:
            import httpx
            async with httpx.AsyncClient(timeout=5.0, follow_redirects=True) as client:
                headers = {'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X)'}
                response = await client.get(url, headers=headers)
                if response.status_code == 200:
                    og_match = re.search(r'property="og:image"[^>]+content="([^"]+)"', response.text)
                    if og_match:
                        return og_match.group(1)
        except:
            pass
    
    # Fallback - return original URL
    return url
