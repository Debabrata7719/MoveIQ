import os
from elasticsearch import Elasticsearch
from dotenv import load_dotenv
from src.logger import get_logger

logger = get_logger("elastic_utils")

load_dotenv()

# Global Elasticsearch client
_es_client = None

def get_es_client():
    global _es_client
    if _es_client is not None:
        return _es_client

    use_local = os.getenv("USE_LOCAL_DB", "true").lower() == "true"
    es_urls = []
    if use_local:
        es_urls.append(os.getenv("LOCAL_ELASTICSEARCH_URL", "http://localhost:9200"))
    
    # Always include cloud URL as a fallback
    cloud_url = os.getenv("CLOUD_ELASTICSEARCH_URL", "https://elasticsearch-production-c98b.up.railway.app")
    if cloud_url:
        es_urls.append(cloud_url)

    for es_url in es_urls:
        try:
            _es_client = Elasticsearch([es_url])
            # Verify connection
            if _es_client.ping():
                logger.info(f"Connected to Elasticsearch at {es_url}")
                return _es_client
            else:
                logger.warning(f"Could not connect/ping Elasticsearch at {es_url}")
        except Exception as e:
            logger.error(f"Error initializing Elasticsearch client at {es_url}: {e}")
            _es_client = None

    logger.critical("All configured Elasticsearch connection endpoints failed.")
    _es_client = None
    return _es_client

def initialize_indices():
    """Create necessary indices and mappings if they don't exist."""
    es = get_es_client()
    if not es:
        return

    athlete_mapping = {
        "mappings": {
            "properties": {
                "athlete_id": {"type": "keyword"},
                "coach_id": {"type": "integer"},
                "full_name": {
                    "type": "text",
                    "fields": {
                        "keyword": {"type": "keyword", "ignore_above": 256}
                    }
                },
                "email": {"type": "text"},
                "sport": {"type": "keyword"},
                "has_previous_injury": {"type": "keyword"},
                "previous_injury_type": {"type": "text"},
                "risk_category": {"type": "keyword"},
                "profile_picture_url": {"type": "keyword", "index": False}
            }
        }
    }

    index_name = "athletes"
    try:
        if not es.indices.exists(index=index_name):
            es.indices.create(index=index_name, body=athlete_mapping)
            logger.info(f"Created index: {index_name}")
        else:
            logger.info(f"Index {index_name} already exists.")
    except Exception as e:
        logger.error(f"Failed to create index {index_name}: {e}")

