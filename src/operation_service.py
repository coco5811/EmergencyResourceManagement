"""Application service functions that coordinate MySQL actions and MongoDB logs.

Use these from the UI when you want each successful MySQL operation to create
an event-history record. MySQL remains authoritative: a Mongo failure does not
undo an already committed MySQL operation and is returned as log_status.
"""
import warnings

from . import incident_manager, resource_manager
from . import mongo_manager


def _log_after_commit(**event):
    result = mongo_manager.log_event(**event)
    if not result.get("ok"):
        warnings.warn(
            "MySQL operation succeeded, but MongoDB event logging failed: "
            + result.get("error", "unknown MongoDB error"),
            RuntimeWarning,
            stacklevel=2,
        )
    return result


def create_incident_with_event(incident_type, location, severity="Medium",
                               description=None, status="Reported"):
    incident_id = incident_manager.register_incident(
        incident_type, location, severity, description, status
    )
    log_status = _log_after_commit(
        incident_id=incident_id,
        event_type="incident_created",
        description=f"Incident created: {incident_type}",
        new_status=status,
    )
    return {"incident_id": incident_id, "log_status": log_status}


def update_incident_status_with_event(incident_id, new_status):
    previous = incident_manager.get_incident_by_id(incident_id)
    if previous is None:
        raise ValueError(f"Incident {incident_id} does not exist.")
    updated = incident_manager.update_incident_status(incident_id, new_status)
    log_status = _log_after_commit(
        incident_id=incident_id,
        event_type="incident_status_changed",
        description=f"Incident status changed from {previous['status']} to {new_status}",
        previous_status=previous["status"],
        new_status=new_status,
    )
    return {"incident": updated, "log_status": log_status}


def allocate_resource_with_event(incident_id, resource_id, quantity):
    allocation_id = resource_manager.allocate_resource(
        incident_id, resource_id, quantity
    )
    # Do not perform another MySQL read after commit just to build the event.
    # If that read failed, the allocation would already be committed but the
    # wrapper could misleadingly raise before attempting MongoDB logging.
    log_status = _log_after_commit(
        incident_id=incident_id,
        event_type="resource_allocated",
        description=f"Allocated quantity {quantity} of resource {resource_id}",
        resource_id=resource_id,
        allocation_id=allocation_id,
        extra={"quantity": quantity},
    )
    return {"allocation_id": allocation_id, "log_status": log_status}


def release_allocation_with_event(allocation_id):
    # Read the allocation details before release, then perform the authoritative
    # MySQL transaction. Only write an event if release succeeds.
    active = next(
        (a for a in resource_manager.get_allocations(status="Active")
         if a["allocation_id"] == allocation_id),
        None,
    )
    if active is None:
        raise ValueError(f"Active allocation {allocation_id} does not exist.")
    result = resource_manager.release_allocation(allocation_id)
    log_status = _log_after_commit(
        incident_id=active["incident_id"],
        event_type="resource_released",
        description=f"Released allocation {allocation_id}",
        resource_id=active["resource_id"],
        allocation_id=allocation_id,
        extra={"quantity": active["quantity"]},
    )
    return {**result, "log_status": log_status}
