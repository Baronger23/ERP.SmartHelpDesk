import unittest
from smart_helpdesk.sla import deadline, validate_policy


class CalendarTests(unittest.TestCase):
    def setUp(self):
        self.policy = {"timezone": "Asia/Ho_Chi_Minh", "anchor": "reported_at", "pause_policy": "No pause",
            "calendar": "Business hours", "weekly_windows": {str(d): [["08:00", "12:00"], ["13:00", "17:00"]] for d in range(5)},
            "holidays": ["2026-10-19"], "response_minutes": 30, "restoration_minutes": 120}

    def test_weekend_and_holiday(self):
        due = deadline("2026-10-16 16:45:00", 30, self.policy)
        self.assertEqual("2026-10-20T08:15:00+07:00", due.isoformat())

    def test_lunch_break(self):
        self.assertEqual("2026-10-15T13:15:00+07:00", deadline("2026-10-15 11:45:00", 30, self.policy).isoformat())

    def test_utc_anchor(self):
        self.assertEqual("2026-10-15T08:30:00+07:00", deadline("2026-10-15T01:00:00+00:00", 30, self.policy).isoformat())

    def test_missing_or_invalid_policy_rejected(self):
        with self.assertRaises(ValueError):
            validate_policy({**self.policy, "pause_policy": "Pause all waiting"})
        with self.assertRaises(ValueError):
            deadline("2026-10-15", 0, self.policy)

    def test_overlapping_windows_rejected(self):
        policy = {**self.policy, "weekly_windows": {"3": [["08:00", "12:00"], ["11:00", "17:00"]]}}
        with self.assertRaises(ValueError):
            deadline("2026-10-15 08:00:00", 600, policy)
