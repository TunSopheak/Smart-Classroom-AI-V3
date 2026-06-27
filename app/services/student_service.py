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
    return (
        db.query(Student)
        .filter(Student.status == "active")
        .order_by(Student.student_code)
        .all()
    )


def get_by_code(db: Session, student_code: str):
    return db.query(Student).filter(Student.student_code == student_code).first()


def get_by_id(db: Session, student_id: int):
    return db.query(Student).filter(Student.id == student_id).first()


def generate_next_student_code(db: Session) -> str:
    max_number = 0

    for (code,) in db.query(Student.student_code).all():
        if not code:
            continue

        code = code.upper().strip()
        if not code.startswith("STU"):
            continue

        digits = "".join(ch for ch in code if ch.isdigit())
        if digits:
            max_number = max(max_number, int(digits))

    return f"STU{max_number + 1:04d}"


def create_student(
    db: Session,
    first_name: str,
    last_name: str,
    status: str = "active",
) -> Student:
    student = Student(
        student_code=generate_next_student_code(db),
        first_name=first_name.strip(),
        last_name=last_name.strip(),
        status=status.strip() or "active",
    )

    db.add(student)
    db.commit()
    db.refresh(student)
    return student


def update_student(
    db: Session,
    student_id: int,
    first_name: str,
    last_name: str,
    status: str = "active",
):
    student = get_by_id(db, student_id)

    if not student:
        return None

    student.first_name = first_name.strip()
    student.last_name = last_name.strip()
    student.status = status.strip() or "active"

    db.commit()
    db.refresh(student)
    return student


def set_student_status(db: Session, student_id: int, status: str):
    student = get_by_id(db, student_id)

    if not student:
        return None

    student.status = status
    db.commit()
    db.refresh(student)
    return student
