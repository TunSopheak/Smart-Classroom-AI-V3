import unittest
from types import SimpleNamespace

from app.services.training_service import dataset_folder_for_student


class TrainingServiceTests(unittest.TestCase):
    def test_dataset_folder_uses_student_code(self):
        student = SimpleNamespace(student_code="STU0001", first_name="Tun", last_name="Sopheak")
        folder = dataset_folder_for_student(student)
        self.assertIn("STU0001_TunSopheak", str(folder))


if __name__ == "__main__":
    unittest.main()
