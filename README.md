# OpsPulse

OpsPulse is an end-to-end workforce analytics system that generates
synthetic timekeeping data, validates and transforms it through an ETL
pipeline, detects unusual workforce patterns, and surfaces records for
human review.

## Current Progress

### Milestone 1: Synthetic Data and ETL

- [x] Defined initial project architecture
- [x] Created department data model
- [x] Created employee data model
- [x] Added centralized configuration
- [x] Built deterministic department generator
- [x] Built deterministic employee generator
- [x] Added schema and referential-integrity validation
- [x] Added unit tests for department and employee generation
- [ ] Generate scheduled shifts
- [ ] Generate actual time punches
- [ ] Inject known anomalies
- [ ] Build ETL pipeline
- [ ] Add integration tests