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

def upload_video(file_path: str, public_id: str = None) -> str:
    """Uploads a large video file to Cloudinary."""
    if not os.getenv("CLOUDINARY_URL"):
        logger.warning("CLOUDINARY_URL not found. Video upload skipped.")
        return None
        
    if not os.path.exists(file_path):
        return None

    try:
        upload_result = cloudinary.uploader.upload_large(
            file_path, 
            resource_type="video",
            public_id=public_id,
            folder="sports_injury_raw_videos"
        )
        return upload_result.get("secure_url")
    except Exception as e:
        logger.error(f"Failed to upload video to Cloudinary: {e}")
        return None

def delete_all_raw_videos() -> int:
    """Deletes all videos in the sports_injury_raw_videos folder."""
    if not os.getenv("CLOUDINARY_URL"):
        return 0
        
    try:
        # We can delete by prefix (folder name)
        result = cloudinary.api.delete_resources_by_prefix(
            "sports_injury_raw_videos/", 
            resource_type="video"
        )
        deleted_count = len(result.get('deleted', {}))
        logger.info(f"Deleted {deleted_count} raw videos from Cloudinary.")
        return deleted_count
    except Exception as e:
        logger.error(f"Failed to delete raw videos from Cloudinary: {e}")
        return 0
