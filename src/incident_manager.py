"""Incident CRUD and validation functions."""
from .db import cursor, fetch_all, fetch_one

SEVERITIES = {"Low", "Medium", "High", "Critical"}
STATUSES = {"Reported", "In Progress", "Resolved", "Cancelled"}


def _validate_text(value, label, max_length=None, required=True):
    if value is None:
        if required:
            raise ValueError(f"{label} is required.")
        return
    if not isinstance(value, str):
        raise ValueError(f"{label} must be text.")
    if required and not value.strip():
        raise ValueError(f"{label} is required.")
    if max_length and len(value.strip()) > max_length:
        raise ValueError(f"{label} must be at most {max_length} characters.")


def register_incident(incident_type, location, severity="Medium",
                      description=None, status="Reported"):
    _validate_text(incident_type, "Incident type", 50)
    _validate_text(location, "Location", 150)
    _validate_text(description, "Description", required=False)
    if severity not in SEVERITIES:
        raise ValueError(f"Severity must be one of: {', '.join(sorted(SEVERITIES))}.")
    if status not in STATUSES:
        raise ValueError(f"Status must be one of: {', '.join(sorted(STATUSES))}.")
    from .db import execute_write
    incident_id = execute_write(
        """INSERT INTO incidents
           (incident_type, description, location, severity, status)
           VALUES (%s, %s, %s, %s, %s)""",
        (incident_type.strip(), description.strip() if description else None,
         location.strip(), severity, status)
    )
    return incident_id


def get_all_incidents():
    return fetch_all(
        """SELECT incident_id, incident_type, description, location, severity,
                  status, reported_at
           FROM incidents ORDER BY reported_at DESC, incident_id DESC"""
    )


def get_incident_by_id(incident_id):
    _validate_id(incident_id, "Incident ID")
    return fetch_one("SELECT * FROM incidents WHERE incident_id = %s", (incident_id,))


def filter_incidents(severity=None, status=None):
    if severity is not None and severity not in SEVERITIES:
        raise ValueError(f"Invalid severity: {severity}")
    if status is not None and status not in STATUSES:
        raise ValueError(f"Invalid status: {status}")
    query = "SELECT * FROM incidents WHERE 1=1"
    params = []
    if severity is not None:
        query += " AND severity = %s"
        params.append(severity)
    if status is not None:
        query += " AND status = %s"
        params.append(status)
    query += " ORDER BY reported_at DESC, incident_id DESC"
    return fetch_all(query, tuple(params))


def update_incident_status(incident_id, new_status):
    _validate_id(incident_id, "Incident ID")
    if new_status not in STATUSES:
        raise ValueError(f"Status must be one of: {', '.join(sorted(STATUSES))}.")
    with cursor() as (conn, cur):
        cur.execute("UPDATE incidents SET status = %s WHERE incident_id = %s",
                    (new_status, incident_id))
        if cur.rowcount == 0:
            conn.rollback()
            raise ValueError(f"Incident {incident_id} does not exist.")
        conn.commit()
    return get_incident_by_id(incident_id)


def _validate_id(value, label):
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ValueError(f"{label} must be a positive integer.")
