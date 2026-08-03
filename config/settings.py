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


SHIFT_START_DATE = "2026-01-01" 

SHIFT_END_DATE = "2026-01-31"

STANDARD_SHIFT_HOURS = 8

WEEKDAY_SHIFT_START_HOURS = [
    8,
    9,
]

OPERATIONS_SHIFT_START_HOURS = [
    0,
    8,
    16,
]

SHIFT_GENERATION_PROBABILITY = {
    "Weekdays": 0.90,
    "24/7": 0.75,
}

ARRIVAL_MEAN_MINUTES = 2
ARRIVAL_STANDARD_DEVIATION_MINUTES = 6

DEPARTURE_MEAN_MINUTES = 3
DEPARTURE_STANDARD_DEVIATION_MINUTES = 12

MINIMUM_ARRIVAL_OFFSET_MINUTES = -30
MAXIMUM_ARRIVAL_OFFSET_MINUTES = 60

MINIMUM_DEPARTURE_OFFSET_MINUTES = -60
MAXIMUM_DEPARTURE_OFFSET_MINUTES = 180

MISSING_CLOCK_OUT_PROBABILITY = 0.02
DUPLICATE_PUNCH_PROBABILITY = 0.01
# Synthetic anomaly injection settings
ANOMALY_INJECTION_RATE = 0.03

ANOMALY_TYPE_WEIGHTS = {
    "extreme_overtime": 0.40,
    "extremely_early_clock_in": 0.35,
    "insufficient_rest": 0.25,
}

EXTREME_OVERTIME_MINIMUM_HOURS = 4
EXTREME_OVERTIME_MAXIMUM_HOURS = 10

EARLY_CLOCK_IN_MINIMUM_HOURS = 2
EARLY_CLOCK_IN_MAXIMUM_HOURS = 6

INSUFFICIENT_REST_MAXIMUM_HOURS = 4
