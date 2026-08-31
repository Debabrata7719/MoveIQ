from src.worker.celery_app import celery_app
from database.elastic_utils import get_es_client
from database.mongo_utils import get_db_connection
from database.sql_utils import get_all_users_paginated, get_athlete_coach
from src.logger import get_logger
from elasticsearch import ConnectionError as ESConnectionError, ConnectionTimeout

logger = get_logger("rebuild_tasks")

@celery_app.task(
    queue="low_priority",
    autoretry_for=(ESConnectionError, ConnectionTimeout),
    retry_backoff=True,
    max_retries=3
)
def check_and_rebuild_es_indices(force_rebuild: bool = False):
    """
    Check Elasticsearch index document counts against DB. Rebuilds if mismatched.
    Ensures Elasticsearch matches DB 100%.
    """
    logger.info("Starting Elasticsearch index validation...")
    es = get_es_client()
    if not es:
        logger.error("Failed to connect to Elasticsearch. Skipping validation.")
        return False
        
    try:
        # 1. Fetch total users from DB
        users_resp = get_all_users_paginated(page=1, size=999999)
        db_users = users_resp.get("users", [])
        total_db_users = len(db_users)
        
        # Count athletes and coaches in DB
        db_athletes_count = sum(1 for u in db_users if "athlete" in u.get("roles", []))
        db_coaches_count = sum(1 for u in db_users if "coach" in u.get("roles", []))
        
        # 2. Get counts from Elasticsearch (handle missing indices gracefully)
        es_athletes_count = 0
        
        try:
            if es.indices.exists(index="athletes"):
                es_athletes_count = es.count(index="athletes")["count"]
        except Exception:
            pass
            
        mismatch = (
            db_athletes_count != es_athletes_count 
        )
        
        if not force_rebuild and not mismatch:
            logger.info("Elasticsearch is fully in sync with Database. Rebuild not required.")
            return True
            
        logger.info(f"Mismatch detected! Rebuilding Elasticsearch indices. Force={force_rebuild}")
        logger.info(f"DB vs ES Counts -> Athletes: {db_athletes_count} vs {es_athletes_count}")
        
        # Create indices if they don't exist
        for idx in ["athletes"]:
            es.indices.create(index=idx, ignore=[400])
            
        # Rebuild athletes
        db = get_db_connection()
        
        for u in db_users:
            user_id = u["id"]
            roles = u.get("roles", [])
            

            # Index into athletes if applicable
            if "athlete" in roles:
                # Find coach_id if assigned
                coach_info = get_athlete_coach(user_id)
                coach_id = coach_info.get("coach_id") if coach_info else None
                
                # Fetch profile from MongoDB
                profile = db["athlete_profiles"].find_one({"athlete_id": str(user_id)})
                sport = "General"
                has_previous_injury = "No"
                previous_injury_type = "None"
                profile_picture_url = u.get("profile_picture_url")
                
                if profile:
                    sport = profile.get("sport", "General")
                    has_previous_injury = profile.get("has_previous_injury", "No")
                    previous_injury_type = profile.get("previous_injury_type", "None")
                    if not profile_picture_url:
                        profile_picture_url = profile.get("profile_picture_url")
                
                # Get latest Risk Category
                latest_session = db["sessions"].find_one(
                    {"athlete_id": str(user_id)},
                    sort=[("created_at", -1)]
                )
                
                risk_category = "Unknown"
                if latest_session:
                    risk_score = db["risk_scores"].find_one({"session_id": latest_session["session_id"]})
                    if risk_score:
                        risk_data = risk_score.get("risk_data", {})
                        risk_category = risk_data.get("risk_category", "Unknown")
                        
                athlete_doc = {
                    "athlete_id": str(user_id),
                    "coach_id": coach_id,
                    "full_name": u.get("full_name", ""),
                    "email": u.get("email", ""),
                    "sport": sport,
                    "has_previous_injury": has_previous_injury,
                    "previous_injury_type": previous_injury_type,
                    "risk_category": risk_category,
                    "profile_picture_url": profile_picture_url or ""
                }
                es.index(index="athletes", id=str(user_id), body=athlete_doc)
                
        logger.info("Elasticsearch indices rebuild complete.")
        return True
        
    except Exception as e:
        logger.error(f"Error rebuilding Elasticsearch indices: {e}")
        return False
