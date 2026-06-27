import unittest
from datetime import datetime, timedelta

from app.core.database import SessionLocal, init_db
from app.services import academic_service


class AcademicCrudTests(unittest.TestCase):
    def test_class_subject_schedule_can_update_and_disable(self):
        init_db()
        db = SessionLocal()

        unique_suffix = datetime.now().strftime("%H%M%S%f")[-8:]
        section = f"C{unique_suffix}"
        subject_name = f"Crud Subject {unique_suffix}"
        updated_subject_name = f"Updated Crud Subject {unique_suffix}"

        try:
            academic_service.ensure_academic_schema(db)

            class_group = academic_service.save_class_group(
                db,
                department="CS",
                generation=88,
                year_level=3,
                section=section,
                building="B",
                room_number="188",
                shift="Morning",
            )

            updated_class = academic_service.update_class_group(
                db,
                class_group_id=class_group.id,
                department="CS",
                generation=88,
                year_level=4,
                section=section,
                building="C",
                room_number="288",
                shift="Afternoon",
            )

            expected_code = f"CS-G88-Y4-{section}"
            self.assertEqual(updated_class.class_code, expected_code)
            self.assertEqual(updated_class.room, "C288")
            self.assertEqual(updated_class.shift, "Afternoon")

            subject = academic_service.save_subject(db, subject_name=subject_name)
            updated_subject = academic_service.update_subject(
                db,
                subject_id=subject.id,
                subject_name=updated_subject_name,
            )

            self.assertIn("Updated", updated_subject.subject_name)

            now = datetime.now()
            schedule = academic_service.save_weekly_schedule(
                db,
                class_group_id=updated_class.id,
                subject_id=updated_subject.id,
                day_of_week=now.weekday(),
                start_time=(now - timedelta(minutes=5)).time().replace(microsecond=0),
                late_time=(now + timedelta(minutes=10)).time().replace(microsecond=0),
                end_time=(now + timedelta(hours=1)).time().replace(microsecond=0),
                room="C288",
            )

            changed_schedule = academic_service.update_weekly_schedule(
                db,
                schedule_id=schedule.id,
                class_group_id=updated_class.id,
                subject_id=updated_subject.id,
                day_of_week=now.weekday(),
                start_time=(now - timedelta(minutes=10)).time().replace(microsecond=0),
                late_time=(now + timedelta(minutes=5)).time().replace(microsecond=0),
                end_time=(now + timedelta(hours=2)).time().replace(microsecond=0),
                room="C288",
            )

            self.assertEqual(changed_schedule.room, "C288")

            academic_service.set_schedule_active(db, changed_schedule.id, False)
            disabled_schedule = academic_service.get_schedule_by_id(db, changed_schedule.id)
            self.assertFalse(disabled_schedule.is_active)
        finally:
            db.close()


if __name__ == "__main__":
    unittest.main()
