import os
import uuid
import sys
from datetime import datetime
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
import dns.resolver
from src.logger import get_logger

logger = get_logger("mongo_utils")

# Force Google DNS to bypass local ISP timeout issues with SRV records
dns.resolver.default_resolver = dns.resolver.Resolver(configure=False)
dns.resolver.default_resolver.nameservers = ['8.8.8.8']

# Ensure we can import from src.config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
try:
    from src.config import MONGO_URI, MONGO_DB_NAME
except ImportError:
    # Fallback if config is not accessible
    from dotenv import load_dotenv
    load_dotenv()
    MONGO_URI = os.getenv("MONGO_URI")
    MONGO_DB_NAME = os.getenv("MONGO_DB_NAME")
    
    if not MONGO_URI or not MONGO_DB_NAME:
        raise ValueError("Missing MONGO_URI or MONGO_DB_NAME in your .env file!")

USE_LOCAL_DB = os.getenv("USE_LOCAL_DB", "false").lower() == "true"

# Global connection objects for connection pooling
_mongo_client = None
_db_instance = None

def get_db_connection():
    """Establishes and returns a connection to the MongoDB database.
    Tries localhost first if USE_LOCAL_DB=true, otherwise uses Atlas.
    Reuses a global MongoClient instance for connection pooling."""
    global _mongo_client, _db_instance
    
    if _db_instance is not None:
        return _db_instance
        
    if USE_LOCAL_DB:
        local_uri = "mongodb://localhost:27017/"
        local_db_name = "sports_injury_db"
        
        try:
            # Try local first with a short timeout
            _mongo_client = MongoClient(local_uri, serverSelectionTimeoutMS=2000, maxPoolSize=50)
            _mongo_client.admin.command('ping')
            logger.info(f"Successfully connected to Local MongoDB -> {local_db_name}")
            _db_instance = _mongo_client[local_db_name]
            return _db_instance
        except Exception:
            logger.warning(f"Local MongoDB not found at {local_uri}. Falling back to MongoDB Atlas...")
    
    try:
        # Connect to Atlas with connection pooling parameters
        _mongo_client = MongoClient(
            MONGO_URI, 
            serverSelectionTimeoutMS=5000,
            maxPoolSize=50,
            minPoolSize=5,
            maxIdleTimeMS=60000
        )
        _mongo_client.admin.command('ping')
        logger.info(f"Successfully connected to MongoDB Atlas -> {MONGO_DB_NAME}")
        _db_instance = _mongo_client[MONGO_DB_NAME]
        return _db_instance
    except Exception as e:
        logger.error(f"Could not connect to MongoDB Atlas at {MONGO_URI}. Reason: {e}")
        sys.exit(1)


def generate_session_id() -> str:
    """Generates a unique session ID."""
    return str(uuid.uuid4())


# =========================================================================
# DB READ/WRITE FUNCTIONS
# =========================================================================

def get_athlete_profile(athlete_id: str) -> dict:
    db = get_db_connection()
    collection = db["athlete_profiles"]
    
    profile = collection.find_one({"athlete_id": athlete_id})
    if not profile:
        logger.warning(f"Athlete profile '{athlete_id}' not found in database. Using default fallback values. Please add the profile to MongoDB.")
        return {
            "athlete_id": athlete_id,
            "has_previous_injury": "No",
            "injury_recency": "None",
            "previous_injury_type": "None",
            "training_intensity": "Medium",
            "weekly_training_sessions": 3,
            "is_default": True
        }
    return profile


def save_session(session_id: str, athlete_id: str, video_name: str, status: str):
    db = get_db_connection()
    collection = db["sessions"]
    
    document = {
        "session_id": session_id,
        "athlete_id": athlete_id,
        "video_name": video_name,
        "status": status,
        "created_at": datetime.utcnow()
    }
    collection.insert_one(document)


def update_session_video_url(session_id: str, video_url: str):
    """Update an existing session with the uploaded video URL."""
    db = get_db_connection()
    try:
        sessions_collection = db["sessions"]
        sessions_collection.update_one(
            {"session_id": session_id},
            {"$set": {"video_url": video_url}}
        )
        logger.info(f"Added video URL to session {session_id}")
    except Exception as e:
        logger.error(f"MongoDB error updating video URL: {e}")


def update_session_key_moments(session_id: str, key_moments: list):
    """Update an existing session with the Base64 key moment images."""
    db = get_db_connection()
    try:
        sessions_collection = db["sessions"]
        sessions_collection.update_one(
            {"session_id": session_id},
            {"$set": {"key_moments": key_moments}}
        )
    except Exception as e:
        logger.error(f"MongoDB error updating key moments: {e}")


def save_biomechanics_data(session_id: str, frames_data: list, summary_data: dict):
    db = get_db_connection()
    collection = db["biomechanics_data"]
    
    document = {
        "session_id": session_id,
        "frames": frames_data,
        "summary": summary_data,
        "created_at": datetime.utcnow()
    }
    collection.insert_one(document)


def save_risk_score(session_id: str, athlete_id: str, risk_score_dict: dict):
    db = get_db_connection()
    collection = db["risk_scores"]
    
    document = {
        "session_id": session_id,
        "athlete_id": athlete_id,
        "risk_data": risk_score_dict,
        "created_at": datetime.utcnow()
    }
    collection.insert_one(document)


def save_recommendations(session_id: str, recommendations_dict: dict):
    db = get_db_connection()
    collection = db["recommendations"]
    
    document = {
        "session_id": session_id,
        "recommendations": recommendations_dict,
        "created_at": datetime.utcnow()
    }
    collection.insert_one(document)


def save_full_report(session_id: str, report_text: str):
    db = get_db_connection()
    collection = db["full_recommendation_reports"]
    
    document = {
        "session_id": session_id,
        "raw_text_report": report_text,
        "created_at": datetime.utcnow()
    }
    collection.insert_one(document)


def get_biomechanics_data(session_id: str) -> dict:
    db = get_db_connection()
    collection = db["biomechanics_data"]
    
    data = collection.find_one({"session_id": session_id})
    if not data:
        raise ValueError(f"No biomechanics data found for session {session_id}")
    return data


def get_risk_score(session_id: str) -> dict:
    db = get_db_connection()
    collection = db["risk_scores"]
    
    data = collection.find_one({"session_id": session_id})
    if not data:
        raise ValueError(f"No risk score found for session {session_id}")
    return data


def get_full_report(session_id: str) -> dict:
    db = get_db_connection()
    collection = db["full_recommendation_reports"]
    
    data = collection.find_one({"session_id": session_id})
    return data

def update_session_key_moments(session_id: str, key_moments_b64: list):
    """Saves base64 encoded images to the session document in MongoDB."""
    db = get_db_connection()
    db["sessions"].update_one(
        {"session_id": session_id},
        {"$set": {"key_moments": key_moments_b64}}
    )

def insert_notification(recipient_id: int, notif_type: str, idempotency_key: str, title: str, message: str, action_link: str = None) -> bool:
    """Inserts a notification using idempotency_key to prevent duplicates."""
    db = get_db_connection()
    collection = db["notifications"]
    
    # Ensure unique index exists
    collection.create_index("idempotency_key", unique=True)
    
    document = {
        "recipient_id": recipient_id,
        "type": notif_type,
        "idempotency_key": idempotency_key,
        "title": title,
        "message": message,
        "action_link": action_link,
        "is_read": False,
        "created_at": datetime.utcnow()
    }
    
    try:
        from pymongo.errors import DuplicateKeyError
        result = collection.insert_one(document)
        
        # Publish to WebSockets via Redis
        document["_id"] = str(result.inserted_id)
        if "created_at" in document:
            document["created_at"] = document["created_at"].isoformat()
            
        from api.utils.redis_utils import publish_notification_event
        publish_notification_event(recipient_id, document)
        
        return True
    except DuplicateKeyError:
        logger.info(f"Notification {idempotency_key} already exists. Skipping duplicate.")
        return False
    except Exception as e:
        logger.error(f"Failed to insert notification: {e}")
        return False

def get_user_notifications(user_id, limit: int = 50) -> list:
    """Retrieves recent notifications for a user."""
    db = get_db_connection()
    collection = db["notifications"]
    
    # Check for both int and str to be safe
    try:
        user_id_int = int(user_id)
    except ValueError:
        user_id_int = user_id
        
    notifs = list(collection.find(
        {"recipient_id": {"$in": [user_id, user_id_int, str(user_id)]}},
        {"_id": 1, "type": 1, "title": 1, "message": 1, "is_read": 1, "action_link": 1, "created_at": 1}
    ).sort("created_at", -1).limit(limit))
    
    # Convert ObjectIds to strings
    for n in notifs:
        n["_id"] = str(n["_id"])
    return notifs

def mark_notification_read(notif_id: str, user_id) -> bool:
    """Marks a notification as read."""
    from bson.objectid import ObjectId
    db = get_db_connection()
    collection = db["notifications"]
    
    try:
        user_id_int = int(user_id)
    except ValueError:
        user_id_int = user_id
        
    result = collection.update_one(
        {"_id": ObjectId(notif_id), "recipient_id": {"$in": [user_id, user_id_int, str(user_id)]}},
        {"$set": {"is_read": True}}
    )
    return result.modified_count > 0
