# Emergency Resource Management System

## Overview
An academic prototype for recording emergency incidents, maintaining resource inventory, tracking resource allocations, and reviewing operational summaries.

The Streamlit application has two demonstration views:
- **User View:** submit an incident report and track its status using the incident ID.
- **Dispatcher View:** review dashboard summaries, manage incidents and resources, allocate/release resources, view analytics, and inspect event history.

This is a classroom prototype using fictional/sample data, not a production emergency dispatch service. The view selector is not secure authentication.

## Technology stack
- Python for backend logic
- MySQL for structured operational records
- MongoDB for event-history documents
- Streamlit for the interface
- Pandas and Plotly Express for tables and charts

## Repository structure
```text
.
├── .streamlit/config.toml
├── app.py
├── database/
│   ├── schema.sql
│   ├── sample_data.sql
│   └── advanced_queries.sql
├── src/
│   ├── db.py
│   ├── incident_manager.py
│   ├── resource_manager.py
│   ├── analytics.py
│   ├── mongo_manager.py
│   └── operation_service.py
├── tests/
│   ├── test_backend_mysql.py
│   └── test_mongo_manager.py
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md
```

## Setup (Windows PowerShell)
1. Install Python 3.10+ and run MySQL locally.
2. Create and activate a virtual environment:
   ```powershell
   py -m venv .venv
   .venv\Scripts\Activate.ps1
   ```
3. Install dependencies:
   ```powershell
   python -m pip install -r requirements.txt
   ```
4. Copy `.env.example` to `.env`, then enter your local database credentials. Never commit `.env`.
5. In a MySQL client, run `database/schema.sql` followed by `database/sample_data.sql` against your development database.
6. Start MongoDB locally or configure a MongoDB Atlas URI in `.env`.
7. Start the app from the repository root:
   ```powershell
   streamlit run app.py
   ```

## Database roles
MySQL is authoritative for current incidents, resources and allocations. The operation service performs a MySQL operation first and then attempts to log the action in MongoDB. If MongoDB logging fails after the MySQL operation commits, the operational change is not rolled back; the UI should warn that event history may be incomplete.

## Tests
Mocked MongoDB tests do not require a running MongoDB server:
```powershell
python -m unittest discover -s tests -p "test_mongo_manager.py" -v
```

MySQL integration tests require a running development MySQL server, the schema and sample data, and valid `.env` settings. They create temporary incident/allocation records, so do not run them against production or valuable data:
```powershell
$env:RUN_DB_TESTS="1"
python -m unittest discover -s tests -p "test_backend_mysql.py" -v
```

The existence of test files does not mean tests have passed. Record results only after running them in your environment.

## SQL files
- `schema.sql` creates the database and tables.
- `sample_data.sql` inserts fictional records.
- `advanced_queries.sql` contains demonstration analytical queries.

## Scope and limitations
- User/Dispatcher selection is for demonstration and does not provide authentication or authorization.
- MySQL and MongoDB do not share a distributed transaction. Event logging may fail after a successful MySQL write.
- The project is not production-validated and must not be used for real emergency decisions.
