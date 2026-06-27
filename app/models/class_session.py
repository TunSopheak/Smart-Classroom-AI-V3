from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Integer, String
from sqlalchemy.orm import relationship

from app.core.database import Base


class ClassSession(Base):
    __tablename__ = "class_sessions"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(160), nullable=False)
    class_name = Column(String(120), nullable=False)
    subject = Column(String(120), nullable=False)
    room = Column(String(80), default="Demo Room")

    start_time = Column(DateTime, nullable=False)
    late_time = Column(DateTime, nullable=False)
    close_time = Column(DateTime, nullable=False)

    is_active = Column(Boolean, default=True)

    # Stage 8: session should show where it came from
    # manual = Demo Reset / manual session
    # weekly_schedule = generated from Weekly Schedule
    source = Column(String(60), default="manual")
    schedule_id = Column(Integer, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    attendances = relationship("Attendance", back_populates="session")
