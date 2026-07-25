# OpsPulse Data Model

## Department

A department represents an organizational group such as Operations,
Finance, or Technology.

Primary key: department_id

## Employee

An employee represents a worker in the organization.

Primary key: employee_id

Foreign key: department_id

Relationship: many employees may belong to one department.

## Shift

A shift represents the time an employee is scheduled to work.

Primary key: shift_id

Foreign key: employee_id

Relationship: one employee may have many shifts.

## Time Punch

A time punch contains the employee's actual clock-in and clock-out times.

Primary key: punch_id

Foreign keys: shift_id and employee_id

Relationship: time punches are connected to both an employee and a
scheduled shift.

## Referential Integrity

Every employee must reference a valid department.

Every shift must reference a valid employee.

Every time punch must reference a valid employee and shift.