import os
from src.worker.celery_app import celery_app
from src.main import run_pipeline

@celery_app.task(bind=True)
def process_video_task(self, file_path: str, athlete_id: str, video_name: str, session_id: str):
    """
    Celery task that runs the heavy AI pipeline in the background.
    """
    try:
        # Run the existing synchronous pipeline
        # The pipeline itself will publish progress to Redis for WebSockets
        result = run_pipeline(athlete_id=athlete_id, video_name=video_name, source_path=file_path, explicit_session_id=session_id)
        
        # Cleanup the temporary video file
        if os.path.exists(file_path):
            os.remove(file_path)
            
        return {"status": "success", "session_id": session_id}
        
    except Exception as e:
        # Ensure cleanup even on failure
        if os.path.exists(file_path):
            os.remove(file_path)
            
        # We can publish a failure message to the WebSocket channel
        try:
            import redis
            import json
            from api.utils.redis_utils import get_redis_url
            r = redis.from_url(get_redis_url())
            r.publish(f"session_progress_{session_id}", json.dumps({"step": "ERROR", "progress": 100, "error": str(e)}))
        except:
            pass
            
        self.update_state(state='FAILURE', meta={'error': str(e)})
        raise e
