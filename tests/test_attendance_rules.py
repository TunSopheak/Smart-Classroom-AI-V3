import unittest
from datetime import datetime, timedelta
from types import SimpleNamespace

from app.services.attendance_service import status_for_time


class AttendanceRuleTests(unittest.TestCase):
    def test_present_before_late_time(self):
        now = datetime.now()
        session = SimpleNamespace(late_time=now + timedelta(minutes=10), close_time=now + timedelta(hours=1))
        self.assertEqual(status_for_time(now, session), "present")

    def test_late_after_late_time(self):
        now = datetime.now()
        session = SimpleNamespace(late_time=now - timedelta(minutes=1), close_time=now + timedelta(hours=1))
        self.assertEqual(status_for_time(now, session), "late")


if __name__ == "__main__":
    unittest.main()
