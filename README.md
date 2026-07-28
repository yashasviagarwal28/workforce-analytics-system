# OpsPulse

OpsPulse is an end-to-end workforce analytics system that generates
synthetic timekeeping data, validates and transforms it through an ETL
pipeline, detects unusual workforce patterns, and surfaces records for
human review.

## Current Progress

### Milestone 1: Synthetic Data and ETL

- [x] Defined project purpose and architecture
- [x] Created department data model
- [x] Created employee data model
- [x] Added centralized configuration
- [x] Created deterministic department generator
- [x] Created deterministic employee generator
- [x] Added schema and referential-integrity validation
- [x] Added employee and department unit tests
- [x] Created deterministic scheduled-shift generator
- [x] Added weekday and 24/7 scheduling rules
- [x] Added overnight-shift handling
- [x] Added scheduled-shift validation and tests
- [x] Created deterministic actual time-punch generator
- [x] Added early-arrival and lateness variation
- [x] Added early-departure and overtime variation
- [x] Added controlled missing clock-outs
- [x] Added controlled duplicate records
- [x] Added raw punch validation and tests
- [ ] Inject labeled behavioral anomalies
- [ ] Build the ETL extract stage
- [ ] Build the ETL transform stage
- [ ] Build the ETL load stage
- [ ] Add end-to-end integration tests