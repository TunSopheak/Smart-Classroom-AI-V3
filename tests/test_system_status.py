import unittest

from app.core.database import SessionLocal, init_db
from app.services.system_status_service import get_system_status


class SystemStatusTests(unittest.TestCase):
    def test_system_status_has_required_keys(self):
        init_db()
        db = SessionLocal()
        try:
            status = get_system_status(db)
            self.assertIn("database_ok", status)
            self.assertIn("students_count", status)
            self.assertIn("face_model_trained", status)
            self.assertIn("features", status)
        finally:
            db.close()


if __name__ == "__main__":
    unittest.main()
