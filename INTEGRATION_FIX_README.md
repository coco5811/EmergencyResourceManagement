# Integration fix patch

Copy these files into the existing repository, preserving existing files:
- `src/mongo_manager.py` -> repository `src/mongo_manager.py`
- `tests/test_backend_mysql.py` -> repository `tests/test_backend_mysql.py`
- `tests/test_mongo_manager.py` -> repository `tests/test_mongo_manager.py`
- `tests/__init__.py` -> repository `tests/__init__.py`
- `.env.example` -> repository root `.env.example` (merge if one already exists)

Add both `pymongo>=4.6,<5` and `python-dotenv>=1.0,<2` to the existing `requirements.txt` if they are not already listed; do not replace other dependencies.

## MySQL integration test
Install dependencies and configure local `.env`, load `database/schema.sql` and `database/sample_data.sql`, then run in PowerShell from repository root:
```powershell
$env:RUN_DB_TESTS="1"
python -m unittest discover -s tests -p "test_backend_mysql.py" -v
```
These tests create a temporary incident and allocate/release one resource. Run only on a development database with fictional sample data.

## MongoDB
Set `MONGO_URI`, `MONGO_DB_NAME`, and `MONGO_COLLECTION` in local `.env`. Start local MongoDB or use a MongoDB Atlas URI. The manager creates the `incident_events` collection on first insert; MongoDB does not need a separate SQL schema.

Run mocked MongoDB unit tests (no server needed):
```powershell
python -m unittest discover -s tests -p "test_mongo_manager.py" -v
```
These validate the event helper's document shape and query construction, not a live MongoDB connection.

## MongoDB usage examples
```python
from src.mongo_manager import (
    log_event, get_incident_history, get_recent_events,
    filter_events, aggregate_events_by_type, aggregate_events_by_incident
)

# Call only AFTER a MySQL operation has committed successfully:
result = log_event(
    incident_id=123,
    event_type="resource_allocated",
    description="Allocated one ambulance",
    resource_id=7,
    allocation_id=45,
)
if not result["ok"]:
    print("MySQL action succeeded, but event history was not saved:", result["error"])
```

The patch includes `src/operation_service.py` as the coordinated integration layer. For UI actions that must also write event history, use:
- `create_incident_with_event(...)`
- `update_incident_status_with_event(...)`
- `allocate_resource_with_event(...)`
- `release_allocation_with_event(...)`

These functions perform the MySQL operation first and only then attempt MongoDB logging. They return `log_status`; if MongoDB fails, the MySQL action remains committed and a RuntimeWarning is emitted. This is deliberate because the two databases do not share a transaction. Member 3 should use these wrappers for the corresponding UI actions if event history is required now. Do not report the whole application as fully verified until MySQL integration tests and a live MongoDB test have both run.
