import unittest
from datetime import datetime, timedelta

from app.core.database import SessionLocal, init_db
from app.services import academic_service


class SessionSourceTests(unittest.TestCase):
    def test_generated_session_has_weekly_schedule_source(self):
        init_db()
        db = SessionLocal()

        try:
            academic_service.ensure_academic_schema(db)

            class_group = academic_service.save_class_group(
                db,
                department="CS",
                generation=77,
                year_level=3,
                section="SRC",
                building="B",
                room_number="177",
                shift="Morning",
            )

            subject = academic_service.save_subject(
                db,
                subject_name="Source Test Subject",
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
                room="B177",
            )

            session = academic_service.generate_session_from_schedule(db, schedule.id)

            self.assertIsNotNone(session)
            self.assertEqual(session.source, "weekly_schedule")
            self.assertEqual(session.schedule_id, schedule.id)
            self.assertIn(class_group.class_code, session.title)
        finally:
            db.close()


if __name__ == "__main__":
    unittest.main()
