# Emergency Resource Management System

## Project Overview

The Emergency Resource Management System is a course project designed to organize emergency incidents, hospitals, available resources, and resource allocations in one system.

The project aims to support the tracking of emergency incidents and the management of resources such as ambulances, hospital beds, medical supplies, personnel, and rescue equipment.

**Project status:** Under development.

## Technology Stack

- **Python:** Backend logic
- **MySQL:** Relational database for hospitals, incidents, resources, and allocations
- **Streamlit:** Planned user interface
- **MongoDB:** Planned event history and activity logging

## Current Implementation

The initial MySQL database foundation has been created and tested.

The database includes the following tables:

- `hospitals` — hospital details and locations
- `incidents` — reported emergencies, severity, and status
- `resources` — resource quantities and availability
- `allocations` — records linking resources to incidents

The database schema uses primary keys, foreign keys, enumerated values, and check constraints. Fictional sample data is provided for testing and demonstration.

## Repository Structure

```text
EmergencyResourceManagement/
├── database/
│   ├── schema.sql
│   ├── sample_data.sql
│   └── advanced_queries.sql
├── .gitignore
└── README.md
```

Additional application components will be added as development progresses.

## Database Setup

1. Install MySQL Server and ensure the MySQL service is running.
2. Open a MySQL client.
3. Execute `database/schema.sql` to create the database and tables.
4. Execute `database/sample_data.sql` to insert the fictional sample records.
5. Execute `database/advanced_queries.sql` to run the example analysis queries.

The SQL scripts are intended for a local MySQL development environment. Review the scripts before executing them.

## Team Development Plan

The project is being developed in stages:

1. **Person 1:** MySQL database schema, sample data, and analytical queries.
2. **Person 2:** Python backend and database operations.
3. **Person 3:** Streamlit user interface.
4. **Person 4:** MongoDB event history, aggregation, and integration testing.

## Data and Scope

The sample records are fictional and intended for academic demonstration. This project is not a real emergency dispatch system and should not be used to make operational emergency-response decisions.

## License

No open-source license has been selected yet.