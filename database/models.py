"""
SQLAlchemy ORM Models — MoveIQ
Mirrors the existing MySQL schema exactly (reverse-engineered from init.sql).
"""
from datetime import datetime
from typing import List, Optional
from sqlalchemy import (
    BigInteger, Boolean, Column, DateTime, ForeignKey,
    Integer, String, Text, UniqueConstraint, JSON, func
)
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    pass


# ── Users ─────────────────────────────────────────────────────────────────────
class User(Base):
    __tablename__ = "users"

    id                  = Column(Integer, primary_key=True, autoincrement=True)
    email               = Column(String(255), nullable=False, unique=True)
    password_hash       = Column(String(255), nullable=False)
    full_name           = Column(String(255), nullable=True)
    is_active           = Column(Boolean, default=True)
    profile_picture_url = Column(String(1024), nullable=True)
    coach_code          = Column(String(12), nullable=True, unique=True)
    created_at          = Column(DateTime, server_default=func.now())
    updated_at          = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationships
    roles                    = relationship("UserRole", back_populates="user", cascade="all, delete-orphan")
    coach_assignments        = relationship("CoachAthleteAssignment", foreign_keys="CoachAthleteAssignment.coach_id",
                                            back_populates="coach", cascade="all, delete-orphan")
    athlete_assignments      = relationship("CoachAthleteAssignment", foreign_keys="CoachAthleteAssignment.athlete_id",
                                             back_populates="athlete", cascade="all, delete-orphan")
    notifications            = relationship("Notification", back_populates="user", cascade="all, delete-orphan")
    teams                    = relationship("Team", back_populates="coach", cascade="all, delete-orphan")
    team_memberships         = relationship("TeamAthlete", back_populates="athlete", cascade="all, delete-orphan")
    webhooks                 = relationship("Webhook", back_populates="user", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "email": self.email,
            "password_hash": self.password_hash,
            "full_name": self.full_name,
            "is_active": self.is_active,
            "profile_picture_url": self.profile_picture_url,
            "coach_code": self.coach_code,
            "created_at": str(self.created_at) if self.created_at else None,
            "updated_at": str(self.updated_at) if self.updated_at else None,
        }


# ── Roles ─────────────────────────────────────────────────────────────────────
class Role(Base):
    __tablename__ = "roles"

    id        = Column(Integer, primary_key=True, autoincrement=True)
    role_name = Column(String(50), nullable=False, unique=True)

    user_roles = relationship("UserRole", back_populates="role", cascade="all, delete-orphan")


# ── User ↔ Role join table ────────────────────────────────────────────────────
class UserRole(Base):
    __tablename__ = "user_roles"
    __table_args__ = (UniqueConstraint("user_id", "role_id"),)

    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    role_id = Column(Integer, ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True)

    user = relationship("User", back_populates="roles")
    role = relationship("Role", back_populates="user_roles")


# ── Coach ↔ Athlete Assignments ───────────────────────────────────────────────
class CoachAthleteAssignment(Base):
    __tablename__ = "coach_athlete_assignments"
    __table_args__ = (UniqueConstraint("coach_id", "athlete_id"),)

    id         = Column(Integer, primary_key=True, autoincrement=True)
    coach_id   = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    athlete_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    status     = Column(String(50), default="pending")
    created_at = Column(DateTime, server_default=func.now())

    coach   = relationship("User", foreign_keys=[coach_id],   back_populates="coach_assignments")
    athlete = relationship("User", foreign_keys=[athlete_id], back_populates="athlete_assignments")


# ── Notifications ─────────────────────────────────────────────────────────────
class Notification(Base):
    __tablename__ = "notifications"

    id         = Column(Integer, primary_key=True, autoincrement=True)
    user_id    = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    message    = Column(Text, nullable=False)
    type       = Column(String(50), nullable=False)
    is_read    = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now())

    user = relationship("User", back_populates="notifications")


# ── Teams ─────────────────────────────────────────────────────────────────────
class Team(Base):
    __tablename__ = "teams"

    id         = Column(Integer, primary_key=True, autoincrement=True)
    coach_id   = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name       = Column(String(255), nullable=False)
    created_at = Column(DateTime, server_default=func.now())

    coach    = relationship("User", back_populates="teams")
    athletes = relationship("TeamAthlete", back_populates="team", cascade="all, delete-orphan")


# ── Team ↔ Athlete join table ─────────────────────────────────────────────────
class TeamAthlete(Base):
    __tablename__ = "team_athletes"
    __table_args__ = (UniqueConstraint("team_id", "athlete_id"),)

    id         = Column(Integer, primary_key=True, autoincrement=True)
    team_id    = Column(Integer, ForeignKey("teams.id", ondelete="CASCADE"), nullable=False)
    athlete_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime, server_default=func.now())

    team    = relationship("Team", back_populates="athletes")
    athlete = relationship("User", back_populates="team_memberships")


# ── Webhooks ──────────────────────────────────────────────────────────────────
class Webhook(Base):
    __tablename__ = "webhooks"

    id         = Column(Integer, primary_key=True, autoincrement=True)
    user_id    = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    url        = Column(String(2048), nullable=False)
    events     = Column(JSON, nullable=False)
    is_active  = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    user = relationship("User", back_populates="webhooks")

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "url": self.url,
            "events": self.events if isinstance(self.events, list) else [],
            "is_active": self.is_active,
            "created_at": str(self.created_at) if self.created_at else None,
            "updated_at": str(self.updated_at) if self.updated_at else None,
        }
