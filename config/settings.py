"""Central configuration for the OpsPulse project."""

RANDOM_SEED = 42

NUMBER_OF_EMPLOYEES = 100

DEPARTMENTS = [
    {
        "department_id": "D001",
        "department_name": "Operations",
        "operating_schedule": "24/7",
    },
    {
        "department_id": "D002",
        "department_name": "Finance",
        "operating_schedule": "Weekdays",
    },
    {
        "department_id": "D003",
        "department_name": "Technology",
        "operating_schedule": "Weekdays",
    },
]

OVERTIME_THRESHOLD_HOURS = 40

EMPLOYMENT_STATUSES = [
    "active",
    "on_leave",
    "terminated",
]