"""Opt-in integration tests. These modify the configured local database temporarily.

Run with: RUN_DB_TESTS=1 python -m unittest discover -s tests -v
Use only a development database with the provided fictional sample data.
"""
import os
import unittest

from src.db import fetch_one, cursor
from src.incident_manager import (
    register_incident, get_incident_by_id, get_all_incidents
)
from src.resource_manager import (
    allocate_resource, release_allocation, get_all_resources
)


@unittest.skipUnless(os.getenv("RUN_DB_TESTS") == "1",
                     "Set RUN_DB_TESTS=1 to run MySQL integration tests.")
class BackendMySQLTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Check the connection and confirm the seeded records are accessible first.
        if fetch_one("SELECT DATABASE() AS db_name")["db_name"] != "emergency_resource_db":
            raise RuntimeError("DB_NAME must be emergency_resource_db.")
        if not get_all_incidents():
            raise RuntimeError("Load database/sample_data.sql before running integration tests.")
        row = fetch_one(
            "SELECT resource_id, available_quantity FROM resources "
            "WHERE available_quantity > 0 ORDER BY resource_id LIMIT 1"
        )
        if row is None:
            raise RuntimeError("Integration tests need at least one available resource.")
        cls.resource_id = row["resource_id"]
        cls.original_available = row["available_quantity"]
        cls.incident_id = register_incident(
            "Backend Test Incident", "Test Location", "Low",
            "Temporary integration-test record", "Reported"
        )

    @classmethod
    def tearDownClass(cls):
        with cursor() as (conn, cur):
            cur.execute("DELETE FROM allocations WHERE incident_id = %s", (cls.incident_id,))
            cur.execute("DELETE FROM incidents WHERE incident_id = %s", (cls.incident_id,))
            conn.commit()

    def test_sample_records_and_new_incident_retrieval(self):
        self.assertGreaterEqual(len(get_all_incidents()), 4)
        self.assertGreaterEqual(len(get_all_resources()), 5)
        self.assertEqual(get_incident_by_id(self.incident_id)["incident_id"], self.incident_id)

    def test_allocate_release_and_restore(self):
        allocation_id = allocate_resource(self.incident_id, self.resource_id, 1)
        after_allocate = fetch_one("SELECT available_quantity FROM resources WHERE resource_id=%s",
                                   (self.resource_id,))["available_quantity"]
        self.assertEqual(after_allocate, self.original_available - 1)
        release_allocation(allocation_id)
        after_release = fetch_one("SELECT available_quantity FROM resources WHERE resource_id=%s",
                                  (self.resource_id,))["available_quantity"]
        self.assertEqual(after_release, self.original_available)

    def test_overallocation_rejected_without_partial_update(self):
        current = fetch_one("SELECT available_quantity FROM resources WHERE resource_id=%s",
                            (self.resource_id,))["available_quantity"]
        with self.assertRaises(ValueError):
            allocate_resource(self.incident_id, self.resource_id, current + 1)
        after = fetch_one("SELECT available_quantity FROM resources WHERE resource_id=%s",
                          (self.resource_id,))["available_quantity"]
        self.assertEqual(after, current)

    def test_invalid_values_and_unknown_ids(self):
        with self.assertRaises(ValueError):
            allocate_resource(self.incident_id, self.resource_id, 0)
        with self.assertRaises(ValueError):
            allocate_resource(-1, self.resource_id, 1)
        with self.assertRaises(ValueError):
            allocate_resource(2147483647, self.resource_id, 1)
        with self.assertRaises(ValueError):
            allocate_resource(self.incident_id, 2147483647, 1)

    def test_duplicate_release_is_rejected(self):
        allocation_id = allocate_resource(self.incident_id, self.resource_id, 1)
        release_allocation(allocation_id)
        with self.assertRaises(ValueError):
            release_allocation(allocation_id)


if __name__ == "__main__":
    unittest.main()
