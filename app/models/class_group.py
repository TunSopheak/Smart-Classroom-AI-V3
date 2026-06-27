from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Integer, String

from app.core.database import Base


class ClassGroup(Base):
    __tablename__ = "class_groups"

    id = Column(Integer, primary_key=True, index=True)

    # Auto-generated example: CS-G27-Y3-M4
    class_code = Column(String(80), unique=True, index=True, nullable=False)

    # Human-readable display name
    class_name = Column(String(160), nullable=False)

    department = Column(String(30), default="CS")
    generation = Column(Integer, default=27)
    year_level = Column(Integer, default=3)
    section = Column(String(30), default="M4")

    building = Column(String(30), default="B")
    room_number = Column(String(30), default="108")
    shift = Column(String(50), default="Morning")
    room = Column(String(80), default="B108")

    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
