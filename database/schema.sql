CREATE DATABASE IF NOT EXISTS emergency_resource_db;
USE emergency_resource_db;

CREATE TABLE IF NOT EXISTS hospitals (
    hospital_id INT AUTO_INCREMENT PRIMARY KEY,
    hospital_name VARCHAR(100) NOT NULL,
    location VARCHAR(150) NOT NULL,
    contact_number VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS incidents (
    incident_id INT AUTO_INCREMENT PRIMARY KEY,
    incident_type VARCHAR(50) NOT NULL,
    description TEXT,
    location VARCHAR(150) NOT NULL,
    severity ENUM('Low', 'Medium', 'High', 'Critical')
        NOT NULL DEFAULT 'Medium',
    status ENUM('Reported', 'In Progress', 'Resolved', 'Cancelled')
        NOT NULL DEFAULT 'Reported',
    reported_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS resources (
    resource_id INT AUTO_INCREMENT PRIMARY KEY,
    hospital_id INT NULL,
    resource_name VARCHAR(100) NOT NULL,
    resource_type ENUM(
        'Ambulance',
        'Hospital Bed',
        'Medical Supply',
        'Personnel',
        'Rescue Equipment'
    ) NOT NULL,
    total_quantity INT NOT NULL,
    available_quantity INT NOT NULL,
    location VARCHAR(150) NOT NULL,

    CONSTRAINT fk_resources_hospital
        FOREIGN KEY (hospital_id)
        REFERENCES hospitals(hospital_id),

    CONSTRAINT chk_resources_total
        CHECK (total_quantity >= 0),

    CONSTRAINT chk_resources_available
        CHECK (available_quantity >= 0),

    CONSTRAINT chk_resources_quantity
        CHECK (available_quantity <= total_quantity)
);

CREATE TABLE IF NOT EXISTS allocations (
    allocation_id INT AUTO_INCREMENT PRIMARY KEY,
    incident_id INT NOT NULL,
    resource_id INT NOT NULL,
    quantity INT NOT NULL,
    allocated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status ENUM('Active', 'Released') NOT NULL DEFAULT 'Active',

    CONSTRAINT fk_allocations_incident
        FOREIGN KEY (incident_id)
        REFERENCES incidents(incident_id),

    CONSTRAINT fk_allocations_resource
        FOREIGN KEY (resource_id)
        REFERENCES resources(resource_id),

    CONSTRAINT chk_allocation_quantity
        CHECK (quantity > 0)
);
