"""MongoDB event history for Emergency Resource Management.

MySQL remains authoritative for incidents, resources and allocations.
Call logging functions only after the corresponding MySQL operation succeeds.
MongoDB failures are returned as a status result; they do not undo a committed
MySQL operation.
"""
import os
from datetime import datetime, timezone

from dotenv import load_dotenv
from pymongo import MongoClient, DESCENDING
from pymongo.errors import PyMongoError

load_dotenv()

_client = None


def _get_collection():
    """Create/reuse a Mongo client and return the incident_events collection."""
    global _client
    uri = os.getenv("MONGO_URI", "mongodb://127.0.0.1:27017")
    database_name = os.getenv("MONGO_DB_NAME", "emergency_resource_logs")
    collection_name = os.getenv("MONGO_COLLECTION", "incident_events")
    if _client is None:
        _client = MongoClient(uri, serverSelectionTimeoutMS=3000)
    return _client[database_name][collection_name]


def close_mongo_connection():
    """Close the cached MongoDB client, if it has been created."""
    global _client
    if _client is not None:
        _client.close()
        _client = None


def log_event(incident_id, event_type, description, *, previous_status=None,
              new_status=None, resource_id=None, allocation_id=None,
              extra=None):
    """Insert an event document; return {'ok': bool, ...} instead of raising.

    Call only after the matching MySQL operation has committed successfully.
    """
    if isinstance(incident_id, bool) or not isinstance(incident_id, int) or incident_id <= 0:
        raise ValueError("incident_id must be a positive integer.")
    if not isinstance(event_type, str) or not event_type.strip():
        raise ValueError("event_type is required.")
    if not isinstance(description, str) or not description.strip():
        raise ValueError("description is required.")

    event = {
        "incident_id": incident_id,
        "event_type": event_type.strip(),
        "description": description.strip(),
        "timestamp": datetime.now(timezone.utc),
    }
    if previous_status is not None:
        event["previous_status"] = previous_status
    if new_status is not None:
        event["new_status"] = new_status
    if resource_id is not None:
        event["resource_id"] = resource_id
    if allocation_id is not None:
        event["allocation_id"] = allocation_id
    if extra:
        event["extra"] = extra

    try:
        result = _get_collection().insert_one(event)
        return {"ok": True, "event_id": str(result.inserted_id)}
    except PyMongoError as exc:
        return {"ok": False, "error": str(exc)}


def get_incident_history(incident_id, limit=100):
    """Return one incident's events in chronological order."""
    _validate_positive_int(incident_id, "incident_id")
    _validate_positive_int(limit, "limit")
    try:
        docs = list(_get_collection().find(
            {"incident_id": incident_id}, {"_id": 0}
        ).sort("timestamp", 1).limit(limit))
        return {"ok": True, "events": docs}
    except PyMongoError as exc:
        return {"ok": False, "error": str(exc), "events": []}


def get_recent_events(limit=50):
    """Return most recent events first."""
    _validate_positive_int(limit, "limit")
    try:
        docs = list(_get_collection().find({}, {"_id": 0}).sort(
            "timestamp", DESCENDING
        ).limit(limit))
        return {"ok": True, "events": docs}
    except PyMongoError as exc:
        return {"ok": False, "error": str(exc), "events": []}


def filter_events(event_type=None, incident_id=None, limit=100):
    """Filter events by event type and/or incident ID."""
    _validate_positive_int(limit, "limit")
    query = {}
    if event_type is not None:
        if not isinstance(event_type, str) or not event_type.strip():
            raise ValueError("event_type must be non-empty text.")
        query["event_type"] = event_type.strip()
    if incident_id is not None:
        _validate_positive_int(incident_id, "incident_id")
        query["incident_id"] = incident_id
    try:
        docs = list(_get_collection().find(query, {"_id": 0}).sort(
            "timestamp", DESCENDING
        ).limit(limit))
        return {"ok": True, "events": docs}
    except PyMongoError as exc:
        return {"ok": False, "error": str(exc), "events": []}


def aggregate_events_by_type():
    """MongoDB aggregation: count event documents by event_type."""
    pipeline = [
        {"$group": {"_id": "$event_type", "count": {"$sum": 1}}},
        {"$sort": {"count": -1, "_id": 1}},
    ]
    try:
        return {"ok": True, "results": list(_get_collection().aggregate(pipeline))}
    except PyMongoError as exc:
        return {"ok": False, "error": str(exc), "results": []}


def aggregate_events_by_incident():
    """MongoDB aggregation: count events and status changes per incident."""
    pipeline = [
        {"$group": {
            "_id": "$incident_id",
            "event_count": {"$sum": 1},
            "status_change_count": {
                "$sum": {"$cond": [
                    {"$eq": ["$event_type", "incident_status_changed"]}, 1, 0
                ]}
            },
            "latest_event": {"$max": "$timestamp"},
        }},
        {"$sort": {"latest_event": -1}},
    ]
    try:
        return {"ok": True, "results": list(_get_collection().aggregate(pipeline))}
    except PyMongoError as exc:
        return {"ok": False, "error": str(exc), "results": []}


def _validate_positive_int(value, label):
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ValueError(f"{label} must be a positive integer.")
