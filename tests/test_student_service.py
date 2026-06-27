import unittest

from app.core.database import SessionLocal, init_db
from app.services import student_service


class StudentServiceTests(unittest.TestCase):
    def test_student_code_is_generated_automatically(self):
        init_db()
        db = SessionLocal()

        try:
            before_code = student_service.generate_next_student_code(db)

            student = student_service.create_student(
                db,
                first_name="Auto",
                last_name="Code",
                status="active",
            )

            self.assertEqual(student.student_code, before_code)
            self.assertTrue(student.student_code.startswith("STU"))
            self.assertEqual(student.status, "active")
        finally:
            db.close()


if __name__ == "__main__":
    unittest.main()
