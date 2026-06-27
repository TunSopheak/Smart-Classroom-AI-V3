from datetime import datetime

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.core.database import Base


class VideoRecord(Base):
    __tablename__ = "video_records"

    id = Column(Integer, primary_key=True, index=True)

    session_id = Column(Integer, ForeignKey("class_sessions.id"), nullable=False)

    event_type = Column(String(80), default="manual_clip", nullable=False)
    title = Column(String(180), nullable=False)
    note = Column(Text, nullable=True)

    video_path = Column(String(260), nullable=False)
    file_name = Column(String(180), nullable=False)
    mime_type = Column(String(80), default="video/webm")
    file_size_bytes = Column(Integer, default=0)
    duration_seconds = Column(Float, default=0)

    recorded_at = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)

    session = relationship("ClassSession")
