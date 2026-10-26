"""Resource management with transaction-safe allocation and release."""
from .db import cursor, fetch_all, fetch_one, execute_write
from .incident_manager import _validate_id

RESOURCE_TYPES = {"Ambulance", "Hospital Bed", "Medical Supply",
                  "Personnel", "Rescue Equipment"}


def get_all_resources():
    return fetch_all(
        """SELECT r.*, h.hospital_name
           FROM resources r LEFT JOIN hospitals h ON r.hospital_id = h.hospital_id
           ORDER BY r.resource_id"""
    )


def get_available_resources():
    return fetch_all(
        """SELECT r.*, h.hospital_name
           FROM resources r LEFT JOIN hospitals h ON r.hospital_id = h.hospital_id
           WHERE r.available_quantity > 0 ORDER BY r.resource_id"""
    )


def filter_resources(resource_type=None, location=None):
    if resource_type is not None and resource_type not in RESOURCE_TYPES:
        raise ValueError(f"Invalid resource type: {resource_type}")
    query = """SELECT r.*, h.hospital_name
               FROM resources r LEFT JOIN hospitals h ON r.hospital_id = h.hospital_id
               WHERE 1=1"""
    params = []
    if resource_type:
        query += " AND r.resource_type = %s"
        params.append(resource_type)
    if location:
        if not isinstance(location, str) or not location.strip():
            raise ValueError("Location filter must be non-empty text.")
        query += " AND r.location LIKE %s"
        params.append(f"%{location.strip()}%")
    query += " ORDER BY r.resource_id"
    return fetch_all(query, tuple(params))


def add_resource(resource_name, resource_type, total_quantity, location,
                 hospital_id=None, available_quantity=None):
    if not isinstance(resource_name, str) or not resource_name.strip() or len(resource_name.strip()) > 100:
        raise ValueError("Resource name is required and must be at most 100 characters.")
    if resource_type not in RESOURCE_TYPES:
        raise ValueError(f"Resource type must be one of: {', '.join(sorted(RESOURCE_TYPES))}.")
    if not isinstance(location, str) or not location.strip() or len(location.strip()) > 150:
        raise ValueError("Location is required and must be at most 150 characters.")
    _validate_quantity(total_quantity, "Total quantity", allow_zero=True)
    if available_quantity is None:
        available_quantity = total_quantity
    _validate_quantity(available_quantity, "Available quantity", allow_zero=True)
    if available_quantity > total_quantity:
        raise ValueError("Available quantity cannot exceed total quantity.")
    if hospital_id is not None:
        _validate_id(hospital_id, "Hospital ID")
        if not fetch_one("SELECT hospital_id FROM hospitals WHERE hospital_id = %s", (hospital_id,)):
            raise ValueError(f"Hospital {hospital_id} does not exist.")
    return execute_write(
        """INSERT INTO resources
           (hospital_id, resource_name, resource_type, total_quantity,
            available_quantity, location)
           VALUES (%s, %s, %s, %s, %s, %s)""",
        (hospital_id, resource_name.strip(), resource_type, total_quantity,
         available_quantity, location.strip())
    )


def allocate_resource(incident_id, resource_id, quantity):
    """Allocate quantity atomically; return new allocation ID.

    A conditional UPDATE prevents over-allocation even when requests race.
    The resource update and allocation insert commit or roll back together.
    """
    _validate_id(incident_id, "Incident ID")
    _validate_id(resource_id, "Resource ID")
    _validate_quantity(quantity, "Allocation quantity")
    with cursor() as (conn, cur):
        try:
            cur.execute("SELECT incident_id FROM incidents WHERE incident_id = %s FOR UPDATE",
                        (incident_id,))
            if cur.fetchone() is None:
                raise ValueError(f"Incident {incident_id} does not exist.")
            cur.execute(
                """UPDATE resources
                   SET available_quantity = available_quantity - %s
                   WHERE resource_id = %s AND available_quantity >= %s""",
                (quantity, resource_id, quantity)
            )
            if cur.rowcount != 1:
                cur.execute("SELECT resource_id FROM resources WHERE resource_id = %s",
                            (resource_id,))
                if cur.fetchone() is None:
                    raise ValueError(f"Resource {resource_id} does not exist.")
                raise ValueError("Insufficient available quantity for this allocation.")
            cur.execute(
                """INSERT INTO allocations (incident_id, resource_id, quantity, status)
                   VALUES (%s, %s, %s, 'Active')""",
                (incident_id, resource_id, quantity)
            )
            allocation_id = cur.lastrowid
            conn.commit()
            return allocation_id
        except Exception:
            conn.rollback()
            raise


def release_allocation(allocation_id):
    """Release an active allocation once and restore its quantity atomically."""
    _validate_id(allocation_id, "Allocation ID")
    with cursor() as (conn, cur):
        try:
            cur.execute(
                """SELECT allocation_id, resource_id, quantity, status
                   FROM allocations WHERE allocation_id = %s FOR UPDATE""",
                (allocation_id,)
            )
            allocation = cur.fetchone()
            if allocation is None:
                raise ValueError(f"Allocation {allocation_id} does not exist.")
            if allocation["status"] != "Active":
                raise ValueError(f"Allocation {allocation_id} has already been released.")
            cur.execute(
                """UPDATE resources
                   SET available_quantity = available_quantity + %s
                   WHERE resource_id = %s
                     AND available_quantity + %s <= total_quantity""",
                (allocation["quantity"], allocation["resource_id"], allocation["quantity"])
            )
            if cur.rowcount != 1:
                raise RuntimeError("Could not restore resource quantity; transaction cancelled.")
            cur.execute(
                "UPDATE allocations SET status = 'Released' WHERE allocation_id = %s AND status = 'Active'",
                (allocation_id,)
            )
            if cur.rowcount != 1:
                raise RuntimeError("Allocation state changed unexpectedly; transaction cancelled.")
            conn.commit()
            return {"allocation_id": allocation_id, "status": "Released",
                    "quantity_restored": allocation["quantity"]}
        except Exception:
            conn.rollback()
            raise


def get_allocations(status=None, incident_id=None):
    if status is not None and status not in {"Active", "Released"}:
        raise ValueError("Status must be Active or Released.")
    query = """SELECT a.*, i.incident_type, r.resource_name, r.resource_type
               FROM allocations a
               JOIN incidents i ON a.incident_id = i.incident_id
               JOIN resources r ON a.resource_id = r.resource_id
               WHERE 1=1"""
    params = []
    if status:
        query += " AND a.status = %s"
        params.append(status)
    if incident_id is not None:
        _validate_id(incident_id, "Incident ID")
        query += " AND a.incident_id = %s"
        params.append(incident_id)
    query += " ORDER BY a.allocated_at DESC, a.allocation_id DESC"
    return fetch_all(query, tuple(params))


def _validate_quantity(value, label, allow_zero=False):
    minimum = 0 if allow_zero else 1
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
        qualifier = "a non-negative" if allow_zero else "a positive"
        raise ValueError(f"{label} must be {qualifier} integer.")
