import unittest
from datetime import datetime, timedelta

from app.core.database import SessionLocal, init_db
from app.models.class_session import ClassSession
from app.models.video_record import VideoRecord
from app.services import video_record_service


class VideoRecordServiceTests(unittest.TestCase):
    def test_video_record_metadata_can_be_created(self):
        init_db()
        db = SessionLocal()

        session_id = None
        record_id = None

        try:
            now = datetime.now()
            session = ClassSession(
                title="Video Test Session",
                class_name="CS-G27-Y3-M4",
                subject="Internet of Things",
                room="B108",
                start_time=now,
                late_time=now + timedelta(minutes=10),
                close_time=now + timedelta(hours=2),
                is_active=True,
                source="weekly_schedule",
                schedule_id=999,
            )
            db.add(session)
            db.commit()
            db.refresh(session)
            session_id = session.id

            record = video_record_service.create_video_record(
                db=db,
                session_id=session.id,
                event_type="manual_clip",
                title="Video Evidence Test",
                note="Unit test record",
                video_path="/media/recordings/test.webm",
                file_name="test.webm",
                mime_type="video/webm",
                file_size_bytes=1234,
                duration_seconds=5.5,
            )
            record_id = record.id

            self.assertIsNotNone(record.id)
            self.assertEqual(record.session_id, session.id)
            self.assertEqual(record.event_type, "manual_clip")
            self.assertEqual(record.duration_seconds, 5.5)
        finally:
            if record_id:
                db.query(VideoRecord).filter(VideoRecord.id == record_id).delete(synchronize_session=False)
            if session_id:
                db.query(ClassSession).filter(ClassSession.id == session_id).delete(synchronize_session=False)
            db.commit()
            db.close()


if __name__ == "__main__":
    unittest.main()
