from datetime import datetime

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import relationship

from app.core.database import Base


class Attendance(Base):
    __tablename__ = "attendances"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    session_id = Column(Integer, ForeignKey("class_sessions.id"), nullable=False)
    first_seen_time = Column(DateTime, nullable=True)
    status = Column(String, nullable=False)  # present / late / absent / permission
    method = Column(String, nullable=False)  # face / qr / manual
    confidence = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    student = relationship("Student", back_populates="attendances")
    session = relationship("ClassSession", back_populates="attendances")

    __table_args__ = (
        UniqueConstraint("student_id", "session_id", name="uq_student_session_attendance"),
    )
