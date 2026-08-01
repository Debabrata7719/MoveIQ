from celery.utils.log import get_task_logger
from src.worker.celery_app import celery_app
from database.mongo_utils import get_db_connection, insert_notification
from api.auth import get_connection
from datetime import datetime, timedelta, timezone
import uuid

logger = get_task_logger(__name__)

@celery_app.task(
    name="src.worker.scheduled_tasks.reassessment_reminder_task",
    queue="low_priority"
)
def reassessment_reminder_task():
    """
    Checks for athletes who haven't uploaded an assessment in over 30 days, 
    and inserts an in-app reminder notification.
    """
    logger.info("Starting 30-day reassessment reminder sweep...")
    try:
        db = get_db_connection()
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=30)
        
        conn = get_connection()
        if not conn:
            return "Failed to connect to MySQL"
            
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT u.id, u.full_name
            FROM users u
            JOIN user_roles ur ON u.id = ur.user_id
            JOIN roles r ON ur.role_id = r.id
            WHERE r.role_name = 'athlete' AND u.is_active = 1
        """)
        athletes = cursor.fetchall()
        
        notified_count = 0
        current_month = datetime.now().strftime('%Y%m')
        
        for ath in athletes:
            latest = db["sessions"].find_one(
                {"athlete_id": str(ath["id"])},
                sort=[("created_at", -1)]
            )
            needs_reminder = False
            
            if latest:
                created_at = latest.get("created_at")
                # Ensure timezone aware comparison
                if created_at:
                    if created_at.tzinfo is None:
                        created_at = created_at.replace(tzinfo=timezone.utc)
                    if created_at < cutoff_date:
                        needs_reminder = True
            else:
                needs_reminder = True
                
            if needs_reminder:
                # Use idempotency key based on current month so they only get 1 reminder per month
                insert_notification(
                    recipient_id=ath["id"],
                    notif_type="REASSESSMENT_REMINDER",
                    idempotency_key=f"reassess_{ath['id']}_{current_month}",
                    title="Time for a Reassessment!",
                    message=f"Hi {ath['full_name']}, it's been over 30 days since your last assessment. Upload a new video to track your progress!",
                    action_link="/dashboard"
                )
                notified_count += 1
                
        cursor.close()
        conn.close()
        logger.info(f"Reminded {notified_count} athletes.")
        return f"Reminded {notified_count} athletes."
        
    except Exception as e:
        logger.error(f"Error in reassessment reminder task: {e}")
        raise

@celery_app.task(
    name="src.worker.scheduled_tasks.weekly_progress_report_task",
    queue="low_priority"
)
def weekly_progress_report_task():
    """
    Generates a weekly summary notification for athletes who trained this week.
    """
    logger.info("Starting weekly progress report sweep...")
    try:
        db = get_db_connection()
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=7)
        
        conn = get_connection()
        if not conn:
            return "Failed to connect to MySQL"
            
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT u.id, u.full_name
            FROM users u
            JOIN user_roles ur ON u.id = ur.user_id
            JOIN roles r ON ur.role_id = r.id
            WHERE r.role_name = 'athlete' AND u.is_active = 1
        """)
        athletes = cursor.fetchall()
        
        notified_count = 0
        current_week = datetime.now().strftime('%Y%V')
        
        # cutoff_date as naive datetime since pymongo usually returns naive UTC datetimes
        naive_cutoff = cutoff_date.replace(tzinfo=None)
        
        for ath in athletes:
            # Check if they had ANY sessions in the last 7 days
            recent_sessions = list(db["sessions"].find({
                "athlete_id": str(ath["id"]),
                "created_at": {"$gte": naive_cutoff}
            }))
            
            if recent_sessions:
                insert_notification(
                    recipient_id=ath["id"],
                    notif_type="WEEKLY_PROGRESS_REPORT",
                    idempotency_key=f"weekly_{ath['id']}_{current_week}",
                    title="Your Weekly Progress Report is Ready!",
                    message=f"Great job! You completed {len(recent_sessions)} assessment(s) this week. Click here to review your progress.",
                    action_link="/dashboard"
                )
                notified_count += 1
                
        cursor.close()
        conn.close()
        logger.info(f"Sent weekly report to {notified_count} athletes.")
        return f"Sent weekly report to {notified_count} athletes."
        
    except Exception as e:
        logger.error(f"Error in weekly progress report task: {e}")
        raise
