import unittest
from datetime import datetime, timedelta

from app.core.database import SessionLocal, init_db
from app.services import academic_service


class AcademicScheduleTests(unittest.TestCase):
    def test_schedule_can_generate_session(self):
        init_db()
        db = SessionLocal()

        try:
            academic_service.ensure_academic_schema(db)

            class_group = academic_service.save_class_group(
                db,
                department="CS",
                generation=99,
                year_level=3,
                section="T8",
                building="B",
                room_number="999",
                shift="Test",
            )

            subject = academic_service.save_subject(
                db,
                subject_name="Stage Eight Subject",
            )

            now = datetime.now()
            schedule = academic_service.save_weekly_schedule(
                db,
                class_group_id=class_group.id,
                subject_id=subject.id,
                day_of_week=now.weekday(),
                start_time=(now - timedelta(minutes=5)).time().replace(microsecond=0),
                late_time=(now + timedelta(minutes=10)).time().replace(microsecond=0),
                end_time=(now + timedelta(hours=1)).time().replace(microsecond=0),
                room="B999",
            )

            session = academic_service.generate_session_from_schedule(db, schedule.id)

            self.assertIsNotNone(session)
            self.assertTrue(session.is_active)
            self.assertEqual(session.class_name, class_group.class_code)
            self.assertEqual(session.subject, subject.subject_name)
            self.assertIn(class_group.class_code, session.title)
            self.assertIn(subject.subject_name, session.title)
        finally:
            db.close()


if __name__ == "__main__":
    unittest.main()
