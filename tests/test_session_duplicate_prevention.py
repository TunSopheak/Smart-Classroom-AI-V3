import unittest
from datetime import datetime, timedelta

from app.core.database import SessionLocal, init_db
from app.models.class_session import ClassSession
from app.services import academic_service


class SessionDuplicatePreventionTests(unittest.TestCase):
    def test_generate_session_reuses_today_schedule_session(self):
        init_db()
        db = SessionLocal()

        unique_suffix = datetime.now().strftime("%H%M%S%f")[-8:]
        section = f"D{unique_suffix}"
        subject_name = f"Duplicate Prevention Subject {unique_suffix}"

        try:
            academic_service.ensure_academic_schema(db)

            class_group = academic_service.save_class_group(
                db,
                department="CS",
                generation=66,
                year_level=3,
                section=section,
                building="B",
                room_number="166",
                shift="Morning",
            )

            subject = academic_service.save_subject(db, subject_name=subject_name)

            now = datetime.now()
            schedule = academic_service.save_weekly_schedule(
                db,
                class_group_id=class_group.id,
                subject_id=subject.id,
                day_of_week=now.weekday(),
                start_time=(now - timedelta(minutes=5)).time().replace(microsecond=0),
                late_time=(now + timedelta(minutes=10)).time().replace(microsecond=0),
                end_time=(now + timedelta(hours=1)).time().replace(microsecond=0),
                room="B166",
            )

            session_one = academic_service.generate_session_from_schedule(db, schedule.id)
            session_two = academic_service.generate_session_from_schedule(db, schedule.id)

            self.assertEqual(session_one.id, session_two.id)
            self.assertTrue(session_two.is_active)
            self.assertEqual(session_two.source, "weekly_schedule")
            self.assertEqual(session_two.schedule_id, schedule.id)

            today = datetime.now().date()
            today_start = datetime.combine(today, datetime.min.time())
            tomorrow_start = today_start + timedelta(days=1)

            count = (
                db.query(ClassSession)
                .filter(
                    ClassSession.schedule_id == schedule.id,
                    ClassSession.start_time >= today_start,
                    ClassSession.start_time < tomorrow_start,
                )
                .count()
            )

            self.assertEqual(count, 1)
        finally:
            db.close()


if __name__ == "__main__":
    unittest.main()
