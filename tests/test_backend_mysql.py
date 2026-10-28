"""MySQL integration tests for Emergency Resource Management.

Run from the repository root after configuring .env and loading sample data:
PowerShell:
  $env:RUN_DB_TESTS="1"
  python -m unittest discover -s tests -p "test_backend_mysql.py" -v

These tests create a temporary incident and allocation records in the configured
development database. Do not point them at production data.
"""
import os
import unittest

from src.db import fetch_one, cursor, get_connection
from src.incident_manager import register_incident, get_incident_by_id
from src.resource_manager import allocate_resource, release_allocation


@unittest.skipUnless(
    os.getenv("RUN_DB_TESTS") == "1",
    "Set RUN_DB_TESTS=1 to enable MySQL integration tests."
)
class BackendMySQLTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Fail early with a useful message if DB settings or schema are missing.
        conn = get_connection()
        conn.close()

        cls.incident_id = register_incident(
            "Backend Test Incident",
            "Automated Test Location",
            "Low",
            "Temporary record created by test_backend_mysql.py",
            "Reported",
        )
        row = fetch_one(
            """SELECT resource_id, available_quantity
               FROM resources
               WHERE available_quantity > 0
               ORDER BY resource_id
               LIMIT 1"""
        )
        if row is None:
            # Remove the temporary incident before failing setup.
            with cursor() as (conn, cur):
                cur.execute("DELETE FROM incidents WHERE incident_id = %s",
                            (cls.incident_id,))
                conn.commit()
            raise RuntimeError(
                "Tests require at least one resource with available_quantity > 0."
            )
        cls.resource_id = row["resource_id"]

    @classmethod
    def tearDownClass(cls):
        # Delete test-created allocation rows before the test incident.
        with cursor() as (conn, cur):
            cur.execute(
                "DELETE FROM allocations WHERE incident_id = %s",
                (cls.incident_id,),
            )
            cur.execute("DELETE FROM incidents WHERE incident_id = %s",
                        (cls.incident_id,))
            conn.commit()

    def test_database_connection_and_sample_data(self):
        self.assertIsNotNone(fetch_one("SELECT DATABASE() AS db_name"))
        self.assertIsNotNone(fetch_one("SELECT incident_id FROM incidents LIMIT 1"))
        self.assertIsNotNone(fetch_one("SELECT resource_id FROM resources LIMIT 1"))

    def test_created_incident_can_be_retrieved(self):
        incident = get_incident_by_id(self.incident_id)
        self.assertIsNotNone(incident)
        self.assertEqual(incident["incident_id"], self.incident_id)

    def test_allocate_and_release_restores_quantity(self):
        before = fetch_one(
            "SELECT available_quantity FROM resources WHERE resource_id = %s",
            (self.resource_id,),
        )["available_quantity"]
        allocation_id = allocate_resource(self.incident_id, self.resource_id, 1)
        after_allocate = fetch_one(
            "SELECT available_quantity FROM resources WHERE resource_id = %s",
            (self.resource_id,),
        )["available_quantity"]
        self.assertEqual(after_allocate, before - 1)

        result = release_allocation(allocation_id)
        self.assertEqual(result["status"], "Released")
        after_release = fetch_one(
            "SELECT available_quantity FROM resources WHERE resource_id = %s",
            (self.resource_id,),
        )["available_quantity"]
        self.assertEqual(after_release, before)

    def test_overallocation_is_rejected_without_quantity_change(self):
        available = fetch_one(
            "SELECT available_quantity FROM resources WHERE resource_id = %s",
            (self.resource_id,),
        )["available_quantity"]
        with self.assertRaises(ValueError):
            allocate_resource(self.incident_id, self.resource_id, available + 1)
        after = fetch_one(
            "SELECT available_quantity FROM resources WHERE resource_id = %s",
            (self.resource_id,),
        )["available_quantity"]
        self.assertEqual(after, available)

    def test_invalid_ids_and_quantities_are_rejected(self):
        with self.assertRaises(ValueError):
            allocate_resource(-1, self.resource_id, 1)
        with self.assertRaises(ValueError):
            allocate_resource(self.incident_id, self.resource_id, 0)
        with self.assertRaises(ValueError):
            allocate_resource(self.incident_id, -1, 1)

    def test_releasing_same_allocation_twice_is_rejected(self):
        allocation_id = allocate_resource(self.incident_id, self.resource_id, 1)
        release_allocation(allocation_id)
        with self.assertRaises(ValueError):
            release_allocation(allocation_id)


if __name__ == "__main__":
    unittest.main()
