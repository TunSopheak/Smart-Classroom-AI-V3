from datetime import datetime

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String

from app.core.database import Base


class BehaviorEvent(Base):
    __tablename__ = "behavior_events"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("class_sessions.id"), nullable=True)
    event_type = Column(String, nullable=False)
    severity = Column(String, default="info", nullable=False)
    message = Column(String, nullable=False)
    confidence = Column(Float, nullable=True)
    snapshot_path = Column(String, nullable=True)
    detected_at = Column(DateTime, default=datetime.utcnow)
