# Person 2 Handover — Python Backend

This backend is designed for the existing `emergency_resource_db` schema. It does not create or modify SQL tables and does not include Streamlit UI or MongoDB logging.

## 1. Setup

1. Install Python 3.10+ and MySQL Server.
2. From the repository root, run the existing SQL scripts in order:
   - `database/schema.sql`
   - `database/sample_data.sql`
   - `database/advanced_queries.sql` (verification queries; not required for app startup)
3. Create and activate a virtual environment:
   - Windows PowerShell: `py -m venv .venv` then `.venv\Scripts\Activate.ps1`
   - macOS/Linux: `python3 -m venv .venv` then `source .venv/bin/activate`
4. Install dependencies: `python -m pip install -r requirements.txt`
5. Copy `.env.example` to `.env` and enter your own local MySQL credentials. The backend loads this local file automatically using `python-dotenv`.
6. Verify connection:
   `python -c "from src.db import fetch_one; print(fetch_one('SELECT DATABASE() AS db_name'))"`

## 2. Public functions for Person 3

All functions are imported from `src`. Database rows are returned as dictionaries; list-returning functions return a list of dictionaries. Database and unexpected SQL errors are raised to the caller; UI code should catch exceptions and show a user-friendly message.

### Incident management — `src.incident_manager`

- `register_incident(incident_type, location, severity="Medium", description=None, status="Reported") -> int`: inserts an incident and returns its new ID.
- `get_all_incidents() -> list[dict]`: returns all incidents, newest first.
- `get_incident_by_id(incident_id) -> dict | None`: returns one incident or `None`.
- `filter_incidents(severity=None, status=None) -> list[dict]`: either filter can be omitted.
- `update_incident_status(incident_id, new_status) -> dict`: updates and returns the incident. Raises `ValueError` for invalid input or unknown ID.

Allowed severity: `Low`, `Medium`, `High`, `Critical`.
Allowed status: `Reported`, `In Progress`, `Resolved`, `Cancelled`.

### Resource management — `src.resource_manager`

- `get_all_resources() -> list[dict]`: includes hospital name where available.
- `get_available_resources() -> list[dict]`: resources with available quantity greater than zero.
- `filter_resources(resource_type=None, location=None) -> list[dict]`: location is a substring match.
- `add_resource(resource_name, resource_type, total_quantity, location, hospital_id=None, available_quantity=None) -> int`: returns new resource ID. Available quantity defaults to total.
- `allocate_resource(incident_id, resource_id, quantity) -> int`: returns allocation ID; raises `ValueError` if IDs/quantity are invalid or quantity is unavailable. Uses a conditional update and transaction rollback.
- `release_allocation(allocation_id) -> dict`: releases an active allocation once and restores availability.
- `get_allocations(status=None, incident_id=None) -> list[dict]`: returns allocation records joined with incident/resource labels.

Allowed resource types: `Ambulance`, `Hospital Bed`, `Medical Supply`, `Personnel`, `Rescue Equipment`.

### Analytics — `src.analytics`

- `get_incident_summary() -> dict`: `total_incidents`, `active_incidents`, `high_critical_incidents`.
- `get_resource_summary() -> dict`: `total_resources`, `available_resources`, `allocated_resources` (quantities, not number of resource records).
- `get_resource_usage_by_type() -> list[dict]`: totals, available, and in-use quantity per type.
- `get_resources_by_hospital() -> list[dict]`: totals and available quantity per hospital.
- `get_resources_by_location() -> list[dict]`: totals and available quantities grouped by location and type.

## 3. Example calls

```python
from src.incident_manager import register_incident, get_all_incidents
from src.resource_manager import get_available_resources, allocate_resource, release_allocation
from src.analytics import get_incident_summary

incident_id = register_incident(
    incident_type="Road Accident",
    location="Kothrud, Pune",
    severity="High",
    description="Fictional demonstration incident"
)
print(get_all_incidents())
resources = get_available_resources()
print(resources)
# Choose a real resource_id from the returned rows and check its available_quantity first.
# allocation_id = allocate_resource(incident_id, resource_id, 1)
# release_allocation(allocation_id)
print(get_incident_summary())
```

## 4. Tests

Unit tests that do not require MySQL have not been added yet. Integration tests are opt-in because they create a temporary incident and change resource quantities during execution.

Run:
`RUN_DB_TESTS=1 python -m unittest discover -s tests -v`

Only run this against your local development database populated with the fictional sample data. Tests clean up their temporary incident and allocation records. Test results must be recorded only after running against a real local MySQL instance.

## 5. Design notes / limitations

- SQL values are passed using parameterized queries.
- Allocation uses an atomic conditional decrement; concurrent attempts cannot decrement below zero. The allocation row is inserted in the same transaction.
- Releasing an allocation locks the allocation row and only restores an allocation whose status is `Active`, preventing duplicate releases.
- MongoDB logging is intentionally not included. Person 4 should log events only after a successful MySQL operation, as agreed.
- The `.env` file is local-only. Never commit it or send the password in group chat.
- This is an academic prototype using fictional data, not a real emergency dispatch system.
