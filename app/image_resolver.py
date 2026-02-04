"""
Universal Image URL Resolver - Handles all major platforms
"""
import re
import httpx
from typing import Optional
from urllib.parse import urlparse, parse_qs

async def resolve_image_url(url: str) -> Optional[str]:
    """
    Resolve any URL to a direct image URL.
    Supports: Instagram, Twitter/X, Reddit, Imgur, Giphy, TikTok, YouTube, Pinterest, and more.
    """
    if not url:
        return None
    
    url = url.strip()
    
    # Already a direct image URL
    if re.search(r'\.(jpg|jpeg|png|gif|webp|bmp|svg)(\?.*)?$', url, re.I):
        return url
    
    # Known working CDNs - pass through
    direct_domains = [
        'i.imgur.com', 'cdn.discordapp.com', 'media.discordapp.net',
        'pbs.twimg.com', 'media.giphy.com', 'preview.redd.it', 'i.redd.it',
        'media.tenor.com', 'c.tenor.com', 'i.ytimg.com'
    ]
    for domain in direct_domains:
        if domain in url.lower():
            return url
    
    # ============ IMGUR ============
    # imgur.com/abc123 -> i.imgur.com/abc123.jpg
    imgur_match = re.match(r'https?://(?:www\.)?imgur\.com/(?!a/|gallery/)(\w+)(?:\.\w+)?$', url)
    if imgur_match:
        return f"https://i.imgur.com/{imgur_match.group(1)}.jpg"
    
    # Imgur album/gallery - get first image
    imgur_album = re.match(r'https?://(?:www\.)?imgur\.com/(?:a/|gallery/)(\w+)', url)
    if imgur_album:
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url)
                if response.status_code == 200:
                    # Find first image in album
                    match = re.search(r'https://i\.imgur\.com/(\w+)\.(jpg|png|gif)', response.text)
                    if match:
                        return f"https://i.imgur.com/{match.group(1)}.{match.group(2)}"
        except:
            pass
    
    # ============ GIPHY ============
    giphy_match = re.search(r'giphy\.com/gifs/(?:.*-)?(\w+)', url)
    if giphy_match:
        return f"https://media.giphy.com/media/{giphy_match.group(1)}/giphy.gif"
    
    # ============ TENOR ============
    if 'tenor.com' in url:
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url)
                if response.status_code == 200:
                    # Find the gif URL
                    match = re.search(r'"url":"(https://media\.tenor\.com/[^"]+\.gif)"', response.text)
                    if match:
                        return match.group(1).replace('\\/', '/')
        except:
            pass
    
    # ============ REDDIT ============
    if 'reddit.com' in url or 'redd.it' in url:
        try:
            async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
                headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
                response = await client.get(url, headers=headers)
                if response.status_code == 200:
                    # Try multiple patterns
                    patterns = [
                        r'"url":"(https://preview\.redd\.it/[^"]+)"',
                        r'"url":"(https://i\.redd\.it/[^"]+)"',
                        r'<meta property="og:image" content="([^"]+)"',
                    ]
                    for pattern in patterns:
                        match = re.search(pattern, response.text)
                        if match:
                            img_url = match.group(1).replace('\\/', '/').replace('&amp;', '&')
                            return img_url
        except:
            pass
    
    # ============ TWITTER/X ============
    if 'twitter.com' in url or 'x.com' in url:
        try:
            async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                }
                response = await client.get(url, headers=headers)
                if response.status_code == 200:
                    # Look for og:image or tweet image
                    patterns = [
                        r'<meta property="og:image" content="([^"]+)"',
                        r'<meta name="twitter:image" content="([^"]+)"',
                        r'"media_url_https":"([^"]+)"',
                    ]
                    for pattern in patterns:
                        match = re.search(pattern, response.text)
                        if match:
                            img_url = match.group(1).replace('\\/', '/')
                            # Get larger version if it's a Twitter image
                            if 'pbs.twimg.com' in img_url:
                                img_url = re.sub(r'_\w+(\.[^.]+)$', r'\1', img_url)  # Remove size suffix
                                img_url = img_url.replace('?format=', '?format=jpg&name=large')
                            return img_url
        except:
            pass
    
    # ============ INSTAGRAM ============
    if 'instagram.com/p/' in url or 'instagram.com/reel/' in url:
        try:
            async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.5',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'DNT': '1',
                    'Connection': 'keep-alive',
                    'Upgrade-Insecure-Requests': '1',
                    'Sec-Fetch-Dest': 'document',
                    'Sec-Fetch-Mode': 'navigate',
                    'Sec-Fetch-Site': 'none',
                }
                response = await client.get(url, headers=headers)
                if response.status_code == 200:
                    text = response.text
                    patterns = [
                        r'<meta property="og:image" content="([^"]+)"',
                        r'<meta content="([^"]+)" property="og:image"',
                        r'"display_url":"([^"]+)"',
                        r'"thumbnail_src":"([^"]+)"',
                    ]
                    for pattern in patterns:
                        match = re.search(pattern, text)
                        if match:
                            img_url = match.group(1).replace('\\u0026', '&').replace('\\/', '/')
                            return img_url
        except Exception as e:
            print(f"Instagram fetch failed: {e}")
    
    # ============ TIKTOK ============
    if 'tiktok.com' in url:
        try:
            async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
                headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
                response = await client.get(url, headers=headers)
                if response.status_code == 200:
                    match = re.search(r'<meta property="og:image" content="([^"]+)"', response.text)
                    if match:
                        return match.group(1)
        except:
            pass
    
    # ============ PINTEREST ============
    if 'pinterest.com' in url or 'pin.it' in url:
        try:
            async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
                headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
                response = await client.get(url, headers=headers)
                if response.status_code == 200:
                    patterns = [
                        r'<meta property="og:image" content="([^"]+)"',
                        r'"image_large_url":"([^"]+)"',
                    ]
                    for pattern in patterns:
                        match = re.search(pattern, response.text)
                        if match:
                            return match.group(1).replace('\\/', '/')
        except:
            pass
    
    # ============ YOUTUBE ============
    if 'youtube.com/watch' in url or 'youtu.be/' in url:
        # Extract video ID
        video_id = None
        if 'youtu.be/' in url:
            video_id = url.split('youtu.be/')[-1].split('?')[0].split('&')[0]
        else:
            parsed = urlparse(url)
            query = parse_qs(parsed.query)
            video_id = query.get('v', [None])[0]
        
        if video_id:
            # Try different thumbnail qualities
            for quality in ['maxresdefault', 'sddefault', 'hqdefault', '0']:
                return f"https://i.ytimg.com/vi/{video_id}/{quality}.jpg"
    
    # ============ GENERIC FALLBACK - Try to extract og:image ============
    try:
        async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            }
            response = await client.get(url, headers=headers)
            if response.status_code == 200:
                # Try og:image as last resort
                match = re.search(r'<meta\s+(?:property|name)="og:image"\s+content="([^"]+)"', response.text)
                if not match:
                    match = re.search(r'<meta\s+content="([^"]+)"\s+(?:property|name)="og:image"', response.text)
                if match:
                    return match.group(1)
    except:
        pass
    
    # Return original URL as final fallback
    return url