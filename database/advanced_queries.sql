USE emergency_resource_db;

-- Query 1: Display high and critical severity incidents
SELECT incident_id, incident_type, location, severity, status
FROM incidents
WHERE severity IN ('High', 'Critical')
ORDER BY
    CASE severity
        WHEN 'Critical' THEN 1
        WHEN 'High' THEN 2
        ELSE 3
    END;

-- Query 2: Count incidents by severity
SELECT severity, COUNT(*) AS total_incidents
FROM incidents
GROUP BY severity
ORDER BY total_incidents DESC;

-- Query 3: Display resources with their hospital names
SELECT
    h.hospital_name,
    r.resource_name,
    r.resource_type,
    r.total_quantity,
    r.available_quantity
FROM hospitals h
INNER JOIN resources r
    ON h.hospital_id = r.hospital_id
ORDER BY h.hospital_name;

-- Query 4: Calculate resource quantities by type
SELECT
    resource_type,
    SUM(total_quantity) AS total_resources,
    SUM(available_quantity) AS available_resources,
    SUM(total_quantity - available_quantity) AS resources_in_use
FROM resources
GROUP BY resource_type
ORDER BY total_resources DESC;

-- Query 5: Find resources with less than 80% availability
SELECT
    resource_name,
    resource_type,
    total_quantity,
    available_quantity,
    ROUND(available_quantity * 100.0 /
          NULLIF(total_quantity, 0), 2) AS availability_percentage
FROM resources
WHERE total_quantity > 0
  AND available_quantity * 100.0 / total_quantity < 80;

-- Query 6: Find incidents that are not resolved or cancelled
SELECT incident_id, incident_type, location, severity, status
FROM incidents
WHERE status NOT IN ('Resolved', 'Cancelled')
ORDER BY reported_at DESC;

-- Query 7: Find hospitals that have at least one resource
SELECT hospital_name, location
FROM hospitals h
WHERE EXISTS (
    SELECT 1
    FROM resources r
    WHERE r.hospital_id = h.hospital_id
);

-- Query 8: Count unresolved incidents
SELECT COUNT(*) AS unresolved_incidents
FROM incidents
WHERE status IN ('Reported', 'In Progress');
