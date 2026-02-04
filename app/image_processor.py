"""
Image processing utilities for upload handling
- Validates file size (max 2MB)
- Compresses images to under 100KB
- Returns base64 encoded data for database storage
"""
from PIL import Image
import io
import base64
from typing import Optional, Tuple

MAX_UPLOAD_SIZE = 2 * 1024 * 1024  # 2MB
TARGET_SIZE = 100 * 1024  # 100KB

def process_uploaded_image(file_content: bytes, content_type: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Process an uploaded image file.
    
    Returns:
        Tuple of (base64_data, error_message)
        If successful, error_message is None
        If failed, base64_data is None
    """
    # Check initial file size
    if len(file_content) > MAX_UPLOAD_SIZE:
        return None, f"File too large. Maximum size is 2MB, got {len(file_content) / 1024 / 1024:.1f}MB"
    
    try:
        # Open image
        img = Image.open(io.BytesIO(file_content))
        
        # Convert to RGB if necessary (for JPEG output)
        if img.mode in ('RGBA', 'P'):
            img = img.convert('RGB')
        
        # If already under target size, just convert to JPEG
        if len(file_content) <= TARGET_SIZE:
            output = io.BytesIO()
            img.save(output, format='JPEG', quality=85)
            output.seek(0)
            return base64.b64encode(output.read()).decode('utf-8'), None
        
        # Compress to meet target size
        quality = 85
        max_dimension = 1200
        
        # First, resize if too large
        if max(img.size) > max_dimension:
            ratio = max_dimension / max(img.size)
            new_size = (int(img.size[0] * ratio), int(img.size[1] * ratio))
            img = img.resize(new_size, Image.Resampling.LANCZOS)
        
        # Binary search for right quality
        min_q, max_q = 10, 85
        result = None
        
        while min_q <= max_q:
            quality = (min_q + max_q) // 2
            output = io.BytesIO()
            img.save(output, format='JPEG', quality=quality, optimize=True)
            size = output.tell()
            
            if size <= TARGET_SIZE:
                result = output
                min_q = quality + 1  # Try higher quality
            else:
                max_q = quality - 1  # Need lower quality
        
        # If still too large after quality reduction, resize more aggressively
        if result is None:
            for scale in [0.8, 0.6, 0.5, 0.4, 0.3]:
                new_size = (int(img.size[0] * scale), int(img.size[1] * scale))
                scaled = img.resize(new_size, Image.Resampling.LANCZOS)
                output = io.BytesIO()
                scaled.save(output, format='JPEG', quality=50, optimize=True)
                if output.tell() <= TARGET_SIZE:
                    result = output
                    break
        
        if result is None:
            return None, "Unable to compress image to under 100KB"
        
        result.seek(0)
        return base64.b64encode(result.read()).decode('utf-8'), None
        
    except Exception as e:
        return None, f"Failed to process image: {str(e)}"


def get_image_data_url(base64_data: str) -> str:
    """Convert base64 data to a data URL for img src"""
    return f"data:image/jpeg;base64,{base64_data}"
