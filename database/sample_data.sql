USE emergency_resource_db;

-- 1. Add fictional hospitals
INSERT INTO hospitals
    (hospital_name, location, contact_number)
VALUES
    ('City General Hospital', 'Shivajinagar, Pune', '020-40000001'),
    ('Community Medical Centre', 'Hadapsar, Pune', '020-40000002'),
    ('Emergency Care Hospital', 'Pimpri, Pune', '020-40000003');

-- 2. Add fictional emergency incidents
INSERT INTO incidents
    (incident_type, description, location, severity, status)
VALUES
    ('Road Accident', 'Multi-vehicle collision requiring medical assistance',
     'Shivajinagar, Pune', 'High', 'Reported'),

    ('Medical Emergency', 'Urgent medical assistance required',
     'Hadapsar, Pune', 'Critical', 'In Progress'),

    ('Fire Incident', 'Fire reported in a residential building',
     'Pimpri, Pune', 'High', 'Reported'),

    ('Road Accident', 'Minor traffic collision',
     'Kothrud, Pune', 'Medium', 'Resolved');

-- 3. Add fictional emergency resources
INSERT INTO resources
    (hospital_id, resource_name, resource_type,
     total_quantity, available_quantity, location)
VALUES
    (1, 'City Ambulances', 'Ambulance', 5, 5,
     'Shivajinagar, Pune'),

    (1, 'General Hospital Beds', 'Hospital Bed', 30, 25,
     'Shivajinagar, Pune'),

    (2, 'Medical Response Team', 'Personnel', 12, 10,
     'Hadapsar, Pune'),

    (2, 'First Aid Kits', 'Medical Supply', 50, 45,
     'Hadapsar, Pune'),

    (3, 'Rescue Vehicles', 'Rescue Equipment', 3, 3,
     'Pimpri, Pune');
