"""Unit tests for MongoDB event helpers; no MongoDB server required."""
import unittest
from unittest.mock import MagicMock, patch

from src import mongo_manager


class MongoManagerTests(unittest.TestCase):
    @patch("src.mongo_manager._get_collection")
    def test_log_event_inserts_timestamped_event(self, get_collection):
        collection = get_collection.return_value
        collection.insert_one.return_value.inserted_id = "fake-id"
        result = mongo_manager.log_event(
            12, "incident_created", "Test incident created", new_status="Reported"
        )
        self.assertTrue(result["ok"])
        event = collection.insert_one.call_args.args[0]
        self.assertEqual(event["incident_id"], 12)
        self.assertEqual(event["event_type"], "incident_created")
        self.assertIn("timestamp", event)

    @patch("src.mongo_manager._get_collection")
    def test_history_queries_filter_by_incident(self, get_collection):
        collection = get_collection.return_value
        collection.find.return_value.sort.return_value.limit.return_value = [
            {"incident_id": 12, "event_type": "incident_created"}
        ]
        result = mongo_manager.get_incident_history(12)
        self.assertTrue(result["ok"])
        collection.find.assert_called_once_with({"incident_id": 12}, {"_id": 0})

    @patch("src.mongo_manager._get_collection")
    def test_aggregation_pipeline_is_submitted(self, get_collection):
        collection = get_collection.return_value
        collection.aggregate.return_value = [{"_id": "incident_created", "count": 2}]
        result = mongo_manager.aggregate_events_by_type()
        self.assertTrue(result["ok"])
        collection.aggregate.assert_called_once()

    def test_invalid_incident_id_is_rejected(self):
        with self.assertRaises(ValueError):
            mongo_manager.log_event(0, "incident_created", "Test")


if __name__ == "__main__":
    unittest.main()
