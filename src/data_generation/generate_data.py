import pandas as pd
import numpy as np
from faker import Faker
from datetime import datetime, timedelta
import random

fake = Faker()

NUM_EMPLOYEES = 200
DAYS = 60

def generate_employee_data():
    employees = []
    for i in range(NUM_EMPLOYEES):
        employees.append({
            "employee_id": i + 1,
            "name": fake.name(),
            "department": random.choice(["Operations", "Maintenance", "Finance", "HR"]),
        })
    return pd.DataFrame(employees)


def generate_timekeeping_data(employees):
    records = []

    start_date = datetime.today() - timedelta(days=DAYS)

    for _, emp in employees.iterrows():
        for day in range(DAYS):
            date = start_date + timedelta(days=day)

            # Base working hours
            hours = np.random.normal(8, 1.5)

            # Random absence
            absent = np.random.choice([0, 1], p=[0.9, 0.1])

            if absent:
                hours = 0

            # Overtime simulation
            overtime = max(0, hours - 8)

            records.append({
                "employee_id": emp["employee_id"],
                "date": date.strftime("%Y-%m-%d"),
                "hours_worked": round(hours, 2),
                "overtime_hours": round(overtime, 2),
                "absent": absent,
            })

    return pd.DataFrame(records)


def inject_anomalies(df):
    # Add abnormal overtime
    for _ in range(50):
        idx = random.randint(0, len(df) - 1)
        df.loc[idx, "overtime_hours"] += random.uniform(5, 10)

    # Add suspicious absence patterns
    for _ in range(30):
        idx = random.randint(0, len(df) - 1)
        df.loc[idx, "absent"] = 1
        df.loc[idx, "hours_worked"] = 0

    return df


def main():
    employees = generate_employee_data()
    data = generate_timekeeping_data(employees)
    data = inject_anomalies(data)

    employees.to_csv("employees.csv", index=False)
    data.to_csv("timekeeping_data.csv", index=False)

    print("Data generated successfully!")


if __name__ == "__main__":
    main()
