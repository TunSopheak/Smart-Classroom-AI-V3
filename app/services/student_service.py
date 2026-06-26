from sqlalchemy.orm import Session

from app.models.student import Student

SAMPLE_STUDENTS = [
    ("STU0001", "Tun", "Sopheak"),
    ("STU0002", "Tit", "Sokhom"),
    ("STU0003", "Tep", "Makhon"),
    ("STU0004", "Thorn", "Sarey Rathana"),
    ("STU0005", "Theam", "Vantim"),
]


def seed_students(db: Session) -> None:
    if db.query(Student).count() > 0:
        return

    for code, first_name, last_name in SAMPLE_STUDENTS:
        db.add(Student(student_code=code, first_name=first_name, last_name=last_name))

    db.commit()


def get_students(db: Session):
    return db.query(Student).order_by(Student.student_code).all()


def get_active_students(db: Session):
    return db.query(Student).filter(Student.status == "active").order_by(Student.student_code).all()


def get_by_code(db: Session, student_code: str):
    return db.query(Student).filter(Student.student_code == student_code).first()
