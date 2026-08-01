import os
from dotenv import load_dotenv
import sys
import logging

# Ensure we can import from src
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.logger import get_logger
logger = get_logger("cloud_storage")

# Load environment variables BEFORE importing cloudinary
load_dotenv()

import cloudinary
import cloudinary.uploader
import cloudinary.api

# Explicitly configure using the URL if needed
cloudinary_url = os.getenv("CLOUDINARY_URL")
if cloudinary_url:
    cloudinary.config(
        cloud_url=cloudinary_url,
        secure=True
    )

def upload_image(file_path: str, public_id: str = None) -> str:
    """Uploads a lightweight image (like a key-moment JPEG) to Cloudinary."""
    if not os.getenv("CLOUDINARY_URL"):
        logger.warning("CLOUDINARY_URL not found. Upload skipped.")
        return None
        
    if not os.path.exists(file_path):
        return None

    try:
        upload_result = cloudinary.uploader.upload(
            file_path, 
            resource_type="image",
            public_id=public_id,
            folder="sports_injury_key_moments",
            transformation=[
                {"width": 800, "crop": "scale"} # Ensure max width to save bandwidth
            ]
        )
        return upload_result.get("secure_url")
    except Exception as e:
        logger.error(f"Failed to upload image to Cloudinary: {e}")
        return None
