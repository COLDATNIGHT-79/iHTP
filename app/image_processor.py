"""
Extreme Image Compression - Reduces images to ~3KB blocky/pixelated style
Stores as base64 in database for minimal storage
"""
import io
import base64
from typing import Tuple, Optional
from PIL import Image

MAX_UPLOAD_SIZE = 2 * 1024 * 1024  # 2MB max upload
TARGET_SIZE = 3 * 1024  # 3KB target

def compress_to_blocky(file_content: bytes, content_type: str = None) -> Tuple[Optional[str], Optional[str]]:
    """
    Compress image to ~3KB with blocky/pixelated aesthetic.
    Returns (base64_data, error_message)
    """
    # Check upload size
    if len(file_content) > MAX_UPLOAD_SIZE:
        return None, f"File too large. Max size is 2MB, got {len(file_content) / 1024 / 1024:.1f}MB"
    
    try:
        # Open image
        img = Image.open(io.BytesIO(file_content))
        
        # Convert to RGB (needed for JPEG)
        if img.mode in ('RGBA', 'P', 'LA', 'L'):
            # Create white background for transparent images
            background = Image.new('RGB', img.size, (255, 255, 255))
            if img.mode in ('RGBA', 'LA', 'P'):
                if img.mode == 'P':
                    img = img.convert('RGBA')
                background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                img = background
            else:
                img = img.convert('RGB')
        elif img.mode != 'RGB':
            img = img.convert('RGB')
        
        # Strategy: Resize to very small (creates blocky effect when scaled up)
        # Then use lowest quality JPEG
        
        # Calculate tiny size while maintaining aspect ratio
        # We want ~3KB, which means roughly 32x32 to 48x48 pixels at low quality
        original_width, original_height = img.size
        aspect = original_width / original_height
        
        # Start with a small size
        target_pixels = 40  # Base size - will adjust if needed
        
        if aspect > 1:
            new_width = int(target_pixels * aspect)
            new_height = target_pixels
        else:
            new_width = target_pixels
            new_height = int(target_pixels / aspect)
        
        # Resize with NEAREST for maximum blockiness
        img_small = img.resize((new_width, new_height), Image.Resampling.NEAREST)
        
        # Try to get under 3KB by adjusting quality and size
        quality = 60
        result = io.BytesIO()
        
        while True:
            result.seek(0)
            result.truncate()
            img_small.save(result, format='JPEG', quality=quality, optimize=True)
            
            if result.tell() <= TARGET_SIZE:
                break
            
            # Reduce quality or size
            if quality > 10:
                quality -= 10
            else:
                # Reduce size further
                new_width = max(16, int(new_width * 0.8))
                new_height = max(16, int(new_height * 0.8))
                img_small = img.resize((new_width, new_height), Image.Resampling.NEAREST)
                quality = 50
                
            if new_width <= 16 and new_height <= 16 and quality <= 10:
                break  # Can't go smaller
        
        result.seek(0)
        encoded = base64.b64encode(result.read()).decode('utf-8')
        
        final_size = len(encoded) * 3 / 4 / 1024  # Approximate decoded size in KB
        print(f"Compressed to {new_width}x{new_height} at quality {quality} = ~{final_size:.1f}KB")
        
        return encoded, None
        
    except Exception as e:
        return None, f"Failed to process image: {str(e)}"


def get_data_url(base64_data: str) -> str:
    """Convert base64 data to data URL for img src"""
    return f"data:image/jpeg;base64,{base64_data}"
