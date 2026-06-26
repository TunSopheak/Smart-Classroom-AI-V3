from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Integer, String
from sqlalchemy.orm import relationship

from app.core.database import Base


class ClassSession(Base):
    __tablename__ = "class_sessions"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    class_name = Column(String, nullable=False)
    subject = Column(String, nullable=False)
    room = Column(String, nullable=False)
    start_time = Column(DateTime, nullable=False)
    late_time = Column(DateTime, nullable=False)
    close_time = Column(DateTime, nullable=False)
    is_active = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    attendances = relationship("Attendance", back_populates="session")
