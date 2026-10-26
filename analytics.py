"""Dashboard-ready analytics. Functions return dictionaries or lists of dictionaries."""
from .db import fetch_all, fetch_one


def get_incident_summary():
    return fetch_one(
        """SELECT COUNT(*) AS total_incidents,
                  COALESCE(SUM(status IN ('Reported', 'In Progress')), 0) AS active_incidents,
                  COALESCE(SUM(severity IN ('High', 'Critical')), 0) AS high_critical_incidents
           FROM incidents"""
    )


def get_resource_summary():
    return fetch_one(
        """SELECT COALESCE(SUM(total_quantity), 0) AS total_resources,
                  COALESCE(SUM(available_quantity), 0) AS available_resources,
                  COALESCE(SUM(total_quantity - available_quantity), 0) AS allocated_resources
           FROM resources"""
    )


def get_resource_usage_by_type():
    return fetch_all(
        """SELECT resource_type,
                  SUM(total_quantity) AS total_quantity,
                  SUM(available_quantity) AS available_quantity,
                  SUM(total_quantity - available_quantity) AS in_use_quantity
           FROM resources GROUP BY resource_type ORDER BY resource_type"""
    )


def get_resources_by_hospital():
    return fetch_all(
        """SELECT h.hospital_id, h.hospital_name, h.location AS hospital_location,
                  COALESCE(SUM(r.total_quantity), 0) AS total_quantity,
                  COALESCE(SUM(r.available_quantity), 0) AS available_quantity
           FROM hospitals h
           LEFT JOIN resources r ON h.hospital_id = r.hospital_id
           GROUP BY h.hospital_id, h.hospital_name, h.location
           ORDER BY h.hospital_name"""
    )


def get_resources_by_location():
    return fetch_all(
        """SELECT location, resource_type, SUM(total_quantity) AS total_quantity,
                  SUM(available_quantity) AS available_quantity
           FROM resources GROUP BY location, resource_type ORDER BY location, resource_type"""
    )
