"""
sql_utils.py — Unified Database Operations Layer (SQLAlchemy ORM)

All database operations for the relational store (MySQL or PostgreSQL)
are defined here using SQLAlchemy ORM. This replaces the old raw-SQL
mysql_utils.py and postgres_utils.py files.

Function signatures are intentionally kept identical to the old
raw-SQL implementations so that no API routers or Celery tasks need
to be changed.
"""
import os
import json
import random
import string
import urllib.parse
from typing import Any, Dict, List, Optional

from sqlalchemy import func, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from database.session import SessionLocal, USE_LOCAL_DB
from database.models import (
    CoachAthleteAssignment,
    Notification,
    Role,
    Team,
    TeamAthlete,
    User,
    UserRole,
    Webhook,
)
from src.logger import get_logger

logger = get_logger("sql_utils")


# ── Session helpers (kept for backward-compat with health check) ──────────────

def get_connection():
    """Returns a raw SQLAlchemy Session (named 'connection' for backward compat)."""
    return SessionLocal()


def release_connection(conn):
    """Closes a session returned by get_connection()."""
    try:
        if conn:
            conn.close()
    except Exception:
        pass


# ── Users ─────────────────────────────────────────────────────────────────────

def create_user(email: str, password_hash: str, full_name: str) -> Optional[int]:
    """Inserts a new user and returns their ID."""
    with SessionLocal() as db:
        try:
            safe_name = urllib.parse.quote(full_name or email.split("@")[0])
            profile_pic = f"https://ui-avatars.com/api/?name={safe_name}&background=004ccd&color=fff"

            user = User(
                email=email,
                password_hash=password_hash,
                full_name=full_name,
                profile_picture_url=profile_pic,
                is_active=True,
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            return user.id
        except IntegrityError:
            db.rollback()
            logger.warning(f"create_user: duplicate email {email}")
            return None
        except Exception as e:
            db.rollback()
            logger.error(f"create_user error: {e}")
            return None


def get_user_by_email(email: str) -> Optional[Dict[str, Any]]:
    """Fetches a user by their email address."""
    with SessionLocal() as db:
        try:
            user = db.query(User).filter(User.email == email).first()
            return user.to_dict() if user else None
        except Exception as e:
            logger.error(f"get_user_by_email error: {e}")
            return None


def get_user_by_id(user_id: int) -> Optional[Dict[str, Any]]:
    """Fetches a user by their ID. Auto-generates coach_code if missing."""
    with SessionLocal() as db:
        try:
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                return None

            # Auto-generate coach_code if user is a coach and doesn't have one
            is_coach = (
                db.query(UserRole)
                .join(Role, UserRole.role_id == Role.id)
                .filter(UserRole.user_id == user_id, Role.role_name == "coach")
                .first()
            )
            if is_coach and not user.coach_code:
                while True:
                    code = "".join(random.choices(string.ascii_uppercase + string.digits, k=6))
                    existing = db.query(User).filter(User.coach_code == code).first()
                    if not existing:
                        break
                user.coach_code = code
                db.commit()
                db.refresh(user)

            return user.to_dict()
        except Exception as e:
            logger.error(f"get_user_by_id error: {e}")
            return None


def update_user_account(user_id: int, full_name: str, email: str) -> bool:
    """Updates user's name and email."""
    with SessionLocal() as db:
        try:
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                return False
            user.full_name = full_name
            user.email = email
            db.commit()
            return True
        except Exception as e:
            db.rollback()
            logger.error(f"update_user_account error: {e}")
            return False


def update_user_profile_picture(user_id: int, profile_picture_url: str) -> bool:
    """Updates user's profile picture URL."""
    with SessionLocal() as db:
        try:
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                return False
            user.profile_picture_url = profile_picture_url
            db.commit()
            return True
        except Exception as e:
            db.rollback()
            logger.error(f"update_user_profile_picture error: {e}")
            return False


def update_user_password(user_id: int, new_password_hash: str) -> bool:
    """Updates user's password hash."""
    with SessionLocal() as db:
        try:
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                return False
            user.password_hash = new_password_hash
            db.commit()
            return True
        except Exception as e:
            db.rollback()
            logger.error(f"update_user_password error: {e}")
            return False


# ── Roles ─────────────────────────────────────────────────────────────────────

def _get_or_create_role(db: Session, role_name: str) -> Role:
    """Get an existing role or create it."""
    role = db.query(Role).filter(Role.role_name == role_name).first()
    if not role:
        role = Role(role_name=role_name)
        db.add(role)
        db.flush()
    return role


def assign_role(user_id: int, role_name: str) -> bool:
    """Assigns a role to a user (idempotent)."""
    with SessionLocal() as db:
        try:
            role = _get_or_create_role(db, role_name)
            # Skip if already assigned
            existing = (
                db.query(UserRole)
                .filter(UserRole.user_id == user_id, UserRole.role_id == role.id)
                .first()
            )
            if not existing:
                db.add(UserRole(user_id=user_id, role_id=role.id))
            db.commit()
            return True
        except Exception as e:
            db.rollback()
            logger.error(f"assign_role error: {e}")
            return False


def get_user_roles(user_id: int) -> List[str]:
    """Fetches all role names for a given user."""
    with SessionLocal() as db:
        try:
            rows = (
                db.query(Role.role_name)
                .join(UserRole, Role.id == UserRole.role_id)
                .filter(UserRole.user_id == user_id)
                .all()
            )
            return [r.role_name for r in rows]
        except Exception as e:
            logger.error(f"get_user_roles error: {e}")
            return []


def update_user_roles(user_id: int, roles: List[str]) -> bool:
    """Replaces the complete role set for a user."""
    with SessionLocal() as db:
        try:
            db.query(UserRole).filter(UserRole.user_id == user_id).delete()
            for role_name in roles:
                role = _get_or_create_role(db, role_name)
                db.add(UserRole(user_id=user_id, role_id=role.id))
            db.commit()
            return True
        except Exception as e:
            db.rollback()
            logger.error(f"update_user_roles error: {e}")
            return False


# ── Coach / Athlete Search ────────────────────────────────────────────────────

def search_coaches_by_name(query_str: str) -> List[Dict[str, Any]]:
    """Search for coaches by name, email or coach_code (using SQL only)."""
    with SessionLocal() as db:
        try:
            like = f"%{query_str}%"
            rows = (
                db.query(User.id, User.full_name, User.email, User.coach_code)
                .join(UserRole, User.id == UserRole.user_id)
                .join(Role, UserRole.role_id == Role.id)
                .filter(
                    Role.role_name == "coach",
                    (User.full_name.like(like)) | (User.email.like(like)) | (User.coach_code.like(like)),
                )
                .all()
            )
            return [{"id": r.id, "full_name": r.full_name, "email": r.email, "coach_code": r.coach_code} for r in rows]
        except Exception as e:
            logger.error(f"search_coaches_by_name SQL error: {e}")
            return []


def get_assigned_athletes(coach_id: int) -> List[Dict[str, Any]]:
    """Get all accepted athletes assigned to a coach."""
    with SessionLocal() as db:
        try:
            rows = (
                db.query(User.id, User.full_name, User.email, User.profile_picture_url)
                .join(CoachAthleteAssignment, User.id == CoachAthleteAssignment.athlete_id)
                .filter(
                    CoachAthleteAssignment.coach_id == coach_id,
                    CoachAthleteAssignment.status == "accepted",
                )
                .all()
            )
            return [{"id": r.id, "full_name": r.full_name, "email": r.email, "profile_picture_url": r.profile_picture_url} for r in rows]
        except Exception as e:
            logger.error(f"get_assigned_athletes error: {e}")
            return []


def create_athlete_by_coach(email: str, password_hash: str, full_name: str, coach_id: int) -> Optional[int]:
    """Manually registers an athlete and auto-assigns them to the coach."""
    with SessionLocal() as db:
        try:
            athlete = User(email=email, password_hash=password_hash, full_name=full_name, is_active=True)
            db.add(athlete)
            db.flush()

            role = _get_or_create_role(db, "athlete")
            db.add(UserRole(user_id=athlete.id, role_id=role.id))
            db.add(CoachAthleteAssignment(coach_id=coach_id, athlete_id=athlete.id, status="accepted"))
            db.commit()
            return athlete.id
        except Exception as e:
            db.rollback()
            logger.error(f"create_athlete_by_coach error: {e}")
            return None


def remove_athlete_from_coach(coach_id: int, athlete_id: int) -> bool:
    """Remove athlete connection from coach's roster and all coach's teams."""
    with SessionLocal() as db:
        try:
            db.query(CoachAthleteAssignment).filter(
                CoachAthleteAssignment.coach_id == coach_id,
                CoachAthleteAssignment.athlete_id == athlete_id,
            ).delete()

            # Remove from coach's teams
            team_ids = [t.id for t in db.query(Team.id).filter(Team.coach_id == coach_id).all()]
            if team_ids:
                db.query(TeamAthlete).filter(
                    TeamAthlete.team_id.in_(team_ids),
                    TeamAthlete.athlete_id == athlete_id,
                ).delete(synchronize_session=False)

            db.commit()
            return True
        except Exception as e:
            db.rollback()
            logger.error(f"remove_athlete_from_coach error: {e}")
            return False


def request_coach(athlete_id: int, coach_id: int) -> bool:
    """Send a connection invite from athlete to coach."""
    with SessionLocal() as db:
        try:
            existing = (
                db.query(CoachAthleteAssignment)
                .filter(
                    CoachAthleteAssignment.athlete_id == athlete_id,
                    CoachAthleteAssignment.coach_id == coach_id,
                )
                .first()
            )
            if existing:
                return False
            db.add(CoachAthleteAssignment(coach_id=coach_id, athlete_id=athlete_id, status="pending"))
            db.commit()
            return True
        except Exception as e:
            db.rollback()
            logger.error(f"request_coach error: {e}")
            return False


def get_athlete_coach(athlete_id: int) -> Optional[Dict[str, Any]]:
    """Retrieve the coach's details and pairing status for an athlete."""
    with SessionLocal() as db:
        try:
            row = (
                db.query(
                    CoachAthleteAssignment.status,
                    User.id,
                    User.full_name.label("coach_name"),
                    User.email.label("coach_email"),
                    User.profile_picture_url.label("coach_picture_url"),
                )
                .join(User, CoachAthleteAssignment.coach_id == User.id)
                .filter(CoachAthleteAssignment.athlete_id == athlete_id)
                .first()
            )
            if not row:
                return None
            return {
                "status": row.status,
                "id": row.id,
                "coach_name": row.coach_name,
                "coach_email": row.coach_email,
                "coach_picture_url": row.coach_picture_url,
            }
        except Exception as e:
            logger.error(f"get_athlete_coach error: {e}")
            return None


def get_coach_requests(coach_id: int) -> List[Dict[str, Any]]:
    """Retrieve all pending connection requests for a coach."""
    with SessionLocal() as db:
        try:
            rows = (
                db.query(
                    CoachAthleteAssignment.id,
                    CoachAthleteAssignment.athlete_id,
                    User.full_name.label("athlete_name"),
                    User.email.label("athlete_email"),
                    User.profile_picture_url.label("athlete_picture_url"),
                )
                .join(User, CoachAthleteAssignment.athlete_id == User.id)
                .filter(CoachAthleteAssignment.coach_id == coach_id, CoachAthleteAssignment.status == "pending")
                .all()
            )
            return [
                {
                    "id": r.id,
                    "athlete_id": r.athlete_id,
                    "athlete_name": r.athlete_name,
                    "athlete_email": r.athlete_email,
                    "athlete_picture_url": r.athlete_picture_url,
                }
                for r in rows
            ]
        except Exception as e:
            logger.error(f"get_coach_requests error: {e}")
            return []


def respond_coach_request(request_id: int, status: str) -> bool:
    """Accept or reject a pending coach connection request."""
    with SessionLocal() as db:
        try:
            assignment = db.query(CoachAthleteAssignment).filter(CoachAthleteAssignment.id == request_id).first()
            if not assignment:
                return False
            if status.lower() == "accepted":
                assignment.status = "accepted"
                db.commit()
            else:
                db.delete(assignment)
                db.commit()
            return True
        except Exception as e:
            db.rollback()
            logger.error(f"respond_coach_request error: {e}")
            return False


# ── Notifications ─────────────────────────────────────────────────────────────

def get_notifications(user_id: int) -> List[Dict[str, Any]]:
    """Retrieve all notifications for a user, newest first."""
    with SessionLocal() as db:
        try:
            rows = (
                db.query(Notification)
                .filter(Notification.user_id == user_id)
                .order_by(Notification.created_at.desc())
                .all()
            )
            return [
                {
                    "id": n.id,
                    "message": n.message,
                    "type": n.type,
                    "is_read": n.is_read,
                    "created_at": str(n.created_at),
                }
                for n in rows
            ]
        except Exception as e:
            logger.error(f"get_notifications error: {e}")
            return []


def create_notification(user_id: int, message: str, type_str: str = "info") -> bool:
    """Log a notification for a specific user."""
    with SessionLocal() as db:
        try:
            db.add(Notification(user_id=user_id, message=message, type=type_str, is_read=False))
            db.commit()
            return True
        except Exception as e:
            db.rollback()
            logger.error(f"create_notification error: {e}")
            return False


# ── Teams ─────────────────────────────────────────────────────────────────────

def create_team(coach_id: int, team_name: str) -> Optional[int]:
    """Create a new team under this coach."""
    with SessionLocal() as db:
        try:
            team = Team(coach_id=coach_id, name=team_name)
            db.add(team)
            db.commit()
            db.refresh(team)
            return team.id
        except Exception as e:
            db.rollback()
            logger.error(f"create_team error: {e}")
            return None


def add_athlete_to_team(team_id: int, athlete_id: int) -> bool:
    """Assign an athlete to a team (idempotent)."""
    with SessionLocal() as db:
        try:
            existing = (
                db.query(TeamAthlete)
                .filter(TeamAthlete.team_id == team_id, TeamAthlete.athlete_id == athlete_id)
                .first()
            )
            if existing:
                return True
            db.add(TeamAthlete(team_id=team_id, athlete_id=athlete_id))
            db.commit()
            return True
        except Exception as e:
            db.rollback()
            logger.error(f"add_athlete_to_team error: {e}")
            return False


def get_teams_with_athletes(coach_id: int) -> List[Dict[str, Any]]:
    """Retrieve all teams for a coach with their athletes."""
    with SessionLocal() as db:
        try:
            teams = db.query(Team).filter(Team.coach_id == coach_id).all()
            result = []
            for team in teams:
                athletes = (
                    db.query(User.id, User.full_name, User.email)
                    .join(TeamAthlete, User.id == TeamAthlete.athlete_id)
                    .filter(TeamAthlete.team_id == team.id)
                    .all()
                )
                result.append(
                    {
                        "id": team.id,
                        "name": team.name,
                        "athletes": [{"id": a.id, "full_name": a.full_name, "email": a.email} for a in athletes],
                    }
                )
            return result
        except Exception as e:
            logger.error(f"get_teams_with_athletes error: {e}")
            return []


def delete_team_by_id(coach_id: int, team_id: int) -> bool:
    """Delete a team (verifies ownership first)."""
    with SessionLocal() as db:
        try:
            team = db.query(Team).filter(Team.id == team_id, Team.coach_id == coach_id).first()
            if not team:
                return False
            db.delete(team)
            db.commit()
            return True
        except Exception as e:
            db.rollback()
            logger.error(f"delete_team_by_id error: {e}")
            return False


# ── Admin / Platform Operations ───────────────────────────────────────────────

def toggle_user_status(user_id: int, is_active: bool) -> bool:
    """Enable or disable a user account."""
    with SessionLocal() as db:
        try:
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                return False
            user.is_active = is_active
            db.commit()
            return True
        except Exception as e:
            db.rollback()
            logger.error(f"toggle_user_status error: {e}")
            return False


def get_all_users_paginated(page: int = 1, size: int = 20, search: str = "") -> Dict[str, Any]:
    """Paginated list of all non-admin users (using SQL)."""
    with SessionLocal() as db:
        try:
            # Subquery: users with admin role
            admin_ids = (
                db.query(UserRole.user_id)
                .join(Role, UserRole.role_id == Role.id)
                .filter(Role.role_name == "admin")
                .subquery()
            )
            base_q = db.query(User).filter(User.id.not_in(admin_ids))
            if search:
                like = f"%{search}%"
                base_q = base_q.filter((User.full_name.like(like)) | (User.email.like(like)))

            total = base_q.count()
            users_raw = base_q.order_by(User.created_at.desc()).offset((page - 1) * size).limit(size).all()

            users = []
            for u in users_raw:
                roles = (
                    db.query(Role.role_name)
                    .join(UserRole, Role.id == UserRole.role_id)
                    .filter(UserRole.user_id == u.id)
                    .all()
                )
                d = u.to_dict()
                d["roles"] = [r.role_name for r in roles]
                users.append(d)

            return {"total": total, "users": users}
        except Exception as e:
            logger.error(f"get_all_users_paginated SQL error: {e}")
            return {"total": 0, "users": []}


def get_platform_analytics() -> Dict[str, Any]:
    """Return high-level platform stats."""
    with SessionLocal() as db:
        try:
            total_users  = db.query(func.count(User.id)).scalar()
            active_users = db.query(func.count(User.id)).filter(User.is_active == True).scalar()

            roles_rows = (
                db.query(Role.role_name, func.count(UserRole.user_id).label("cnt"))
                .outerjoin(UserRole, Role.id == UserRole.role_id)
                .group_by(Role.role_name)
                .all()
            )
            roles_breakdown = {r.role_name: r.cnt for r in roles_rows}

            # Daily registrations last 30 days
            if USE_LOCAL_DB:
                day_expr = func.date(User.created_at)
            else:
                day_expr = func.date_trunc("day", User.created_at)

            daily_rows = (
                db.query(day_expr.label("day"), func.count(User.id).label("count"))
                .filter(User.created_at >= func.now() - text("interval '30 days'") if not USE_LOCAL_DB
                        else User.created_at >= func.date_sub(func.now(), text("interval 30 day")))
                .group_by("day")
                .order_by("day")
                .all()
            )
            daily_registrations = [{"date": str(r.day), "count": r.count} for r in daily_rows]

            total_sessions = 0
            try:
                from database.mongo_utils import get_db_connection as get_mongo
                mongo_db = get_mongo()
                total_sessions = mongo_db["sessions"].count_documents({})
            except Exception:
                pass

            return {
                "total_users": total_users,
                "active_users": active_users,
                "roles_breakdown": roles_breakdown,
                "daily_registrations": daily_registrations,
                "total_sessions": total_sessions,
            }
        except Exception as e:
            logger.error(f"get_platform_analytics error: {e}")
            return {}


def get_session_audit_log(page: int = 1, size: int = 20, status_filter: str = "") -> Dict[str, Any]:
    """Return session audit log from MongoDB, enriched with user emails from SQL."""
    try:
        from database.mongo_utils import get_db_connection as get_mongo
        mongo_db = get_mongo()
        query: dict = {}
        if status_filter:
            query["status"] = status_filter
        total = mongo_db["sessions"].count_documents(query)
        skip = (page - 1) * size
        cursor_m = (
            mongo_db["sessions"]
            .find(query, {"session_id": 1, "athlete_id": 1, "video_name": 1, "created_at": 1, "status": 1, "error_message": 1})
            .sort("created_at", -1)
            .skip(skip)
            .limit(size)
        )
        sessions = []
        with SessionLocal() as db:
            for doc in cursor_m:
                athlete_id = doc.get("athlete_id", "")
                user_email = ""
                try:
                    user = db.query(User.email).filter(User.id == int(athlete_id)).first()
                    if user:
                        user_email = user.email
                except Exception:
                    pass
                sessions.append({
                    "session_id": str(doc.get("session_id", "")),
                    "athlete_id": str(athlete_id),
                    "video_name": doc.get("video_name", ""),
                    "created_at": str(doc.get("created_at", "")),
                    "status": doc.get("status", "completed"),
                    "error_message": doc.get("error_message", ""),
                    "user_email": user_email,
                })
        return {"total": total, "sessions": sessions}
    except Exception as e:
        logger.error(f"get_session_audit_log error: {e}")
        return {"total": 0, "sessions": []}


# ── Webhooks ──────────────────────────────────────────────────────────────────

def create_webhook(user_id: int, url: str, events: list) -> Optional[Dict[str, Any]]:
    """Register a new webhook for a user."""
    with SessionLocal() as db:
        try:
            wh = Webhook(user_id=user_id, url=url, events=events, is_active=True)
            db.add(wh)
            db.commit()
            db.refresh(wh)
            return wh.to_dict()
        except Exception as e:
            db.rollback()
            logger.error(f"create_webhook error: {e}")
            return None


def get_webhooks_by_user(user_id: int) -> List[Dict[str, Any]]:
    """Get all webhooks registered by a specific user."""
    with SessionLocal() as db:
        try:
            webhooks = db.query(Webhook).filter(Webhook.user_id == user_id).all()
            return [wh.to_dict() for wh in webhooks]
        except Exception as e:
            logger.error(f"get_webhooks_by_user error: {e}")
            return []


def delete_webhook(webhook_id: int, user_id: int) -> bool:
    """Delete a webhook (must belong to user)."""
    with SessionLocal() as db:
        try:
            deleted = (
                db.query(Webhook)
                .filter(Webhook.id == webhook_id, Webhook.user_id == user_id)
                .delete()
            )
            db.commit()
            return deleted > 0
        except Exception as e:
            db.rollback()
            logger.error(f"delete_webhook error: {e}")
            return False


def get_webhooks_by_event(event_name: str, user_id: Optional[int] = None) -> List[Dict[str, Any]]:
    """Get all active webhooks subscribed to a specific event."""
    with SessionLocal() as db:
        try:
            # Use JSON_CONTAINS for MySQL, @> operator for PostgreSQL
            if USE_LOCAL_DB:
                # MySQL: JSON_CONTAINS(events, '"event_name"')
                condition = func.json_contains(Webhook.events, json.dumps(event_name))
            else:
                # PostgreSQL: events @> '["event_name"]'
                condition = Webhook.events.cast(db.bind.dialect.name == "postgresql" and text("jsonb") or text("json")).op("@>")(json.dumps([event_name]))

            q = db.query(Webhook).filter(Webhook.is_active == True, condition)
            if user_id:
                q = q.filter(Webhook.user_id == user_id)
            return [wh.to_dict() for wh in q.all()]
        except Exception as e:
            logger.error(f"get_webhooks_by_event error: {e}")
            return []
