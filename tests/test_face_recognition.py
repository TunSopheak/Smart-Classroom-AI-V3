import unittest

from app.ai.face_recognition import confidence_from_distance


class FaceRecognitionTests(unittest.TestCase):
    def test_confidence_from_distance(self):
        self.assertEqual(confidence_from_distance(20), 80.0)
        self.assertEqual(confidence_from_distance(120), 0.0)
        self.assertEqual(confidence_from_distance(-10), 100.0)


if __name__ == "__main__":
    unittest.main()
