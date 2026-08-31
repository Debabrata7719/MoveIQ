from src.worker.celery_app import celery_app
from database.elastic_utils import get_es_client
from database.mongo_utils import get_db_connection
from src.logger import get_logger
from elasticsearch import ConnectionError as ESConnectionError, ConnectionTimeout

logger = get_logger("delete_tasks")

@celery_app.task(
    queue="default",
    autoretry_for=(ESConnectionError, ConnectionTimeout),
    retry_backoff=True,
    max_retries=3
)
def delete_athlete_from_es(athlete_id: int):
    logger.info(f"Deleting athlete {athlete_id} from Elasticsearch...")
    es = get_es_client()
    if not es:
        return False
    try:
        es.delete(index="athletes", id=str(athlete_id), ignore=[404])
        logger.info(f"Successfully deleted athlete {athlete_id} from Elasticsearch.")
        return True
    except Exception as e:
        logger.error(f"Error deleting athlete {athlete_id} from Elasticsearch: {e}")
        return False



@celery_app.task(
    queue="default",
    autoretry_for=(ESConnectionError, ConnectionTimeout),
    retry_backoff=True,
    max_retries=3
)
def handle_session_deleted_es_sync(athlete_id: str):
    logger.info(f"Recalculating risk category for athlete {athlete_id} due to session deletion...")
    es = get_es_client()
    if not es:
        return False
    try:
        db = get_db_connection()
        # Find the new latest session for this athlete
        latest_session = db["sessions"].find_one(
            {"athlete_id": str(athlete_id)},
            sort=[("created_at", -1)]
        )
        
        risk_category = "Unknown"
        if latest_session:
            risk_score = db["risk_scores"].find_one({"session_id": latest_session["session_id"]})
            if risk_score:
                risk_data = risk_score.get("risk_data", {})
                risk_category = risk_data.get("risk_category", "Unknown")
        
        # Update the risk category in the Elasticsearch athletes document
        if es.exists(index="athletes", id=str(athlete_id)):
            es.update(
                index="athletes",
                id=str(athlete_id),
                body={"doc": {"risk_category": risk_category}}
            )
            logger.info(f"Updated athlete {athlete_id} risk_category to {risk_category} in Elasticsearch.")
        return True
    except Exception as e:
        logger.error(f"Error updating athlete {athlete_id} risk_category after deletion: {e}")
        return False
