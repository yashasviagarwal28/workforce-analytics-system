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


JOB_TITLES_BY_DEPARTMENT = {
    "D001": [
        "Operations Coordinator",
        "Shift Supervisor",
        "Field Technician",
        "Operations Analyst",
    ],
    "D002": [
        "Financial Analyst",
        "Payroll Specialist",
        "Accountant",
        "Finance Manager",
    ],
    "D003": [
        "Software Engineer",
        "Data Engineer",
        "Systems Analyst",
        "Technical Support Specialist",
    ],
}

HOURLY_RATE_RANGES = {
    "D001": {
        "minimum": 22,
        "maximum": 42,
    },
    "D002": {
        "minimum": 25,
        "maximum": 48,
    },
    "D003": {
        "minimum": 30,
        "maximum": 60,
    },
}

EARLIEST_HIRE_DATE = "2015-01-01"
LATEST_HIRE_DATE = "2025-12-31"