import unittest

from app.ai.behavior_detection import _estimate_person_box_from_face


class BehaviorDetectionTests(unittest.TestCase):
    def test_person_box_stays_inside_frame(self):
        box = _estimate_person_box_from_face((10, 10, 50, 50), frame_width=200, frame_height=200)
        self.assertGreaterEqual(box["x"], 0)
        self.assertGreaterEqual(box["y"], 0)
        self.assertLessEqual(box["x"] + box["w"], 200)
        self.assertLessEqual(box["y"] + box["h"], 200)


if __name__ == "__main__":
    unittest.main()
