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


# Remaining Build Plan

Copy these files into the root of your existing `workforce-analytics-system` repository.

## Commit 1 — Extract stage

Add:

- `src/etl/extract.py`
- extraction tests from `tests/test_etl_pipeline.py` can wait until Commit 4

Run:

```bash
python -m pytest -v
git add src/etl/extract.py
git commit -m "Add raw data extraction layer"
```

## Commit 2 — Transform stage

Add:

- `src/etl/transform.py`

Run:

```bash
python -m pytest -v
git add src/etl/transform.py
git commit -m "Add workforce data cleaning and enrichment"
```

## Commit 3 — Load stage

Add:

- `src/etl/load.py`

Run:

```bash
python -m pytest -v
git add src/etl/load.py
git commit -m "Add idempotent processed data loading"
```

## Commit 4 — ETL orchestration and integration test

Add:

- `src/etl/pipeline.py`
- `tests/test_etl_pipeline.py`
- `pyarrow` dependency

Run:

```bash
python -m src.etl.pipeline
python -m pytest -v tests/test_etl_pipeline.py
git add src/etl/pipeline.py tests/test_etl_pipeline.py requirements.txt
git commit -m "Add end-to-end ETL pipeline"
```

Expected processed files:

```text
data/processed/departments.parquet
data/processed/employees.parquet
data/processed/shifts.parquet
data/processed/punches.parquet
data/processed/quarantine.parquet
data/processed/labels.parquet
```

## Commit 5 — Feature engineering

Add:

- `src/ml/__init__.py`
- `src/ml/features.py`

Run:

```bash
python -m pytest -v
git add src/ml
git commit -m "Add anomaly detection feature engineering"
```

## Commit 6 — Model training

Add:

- `src/ml/train.py`
- `tests/test_ml.py`
- scikit-learn and joblib dependencies

Run:

```bash
python -m src.ml.train
python -m pytest -v tests/test_ml.py
git add src/ml/train.py tests/test_ml.py requirements.txt
git commit -m "Add Isolation Forest anomaly model"
```

Expected outputs:

```text
artifacts/isolation_forest.joblib
data/processed/anomaly_scores.parquet
```

## Commit 7 — Model evaluation

Add:

- `src/ml/evaluate.py`

Run:

```bash
python -m src.ml.evaluate
cat artifacts/metrics.json
git add src/ml/evaluate.py
git commit -m "Add ground-truth anomaly evaluation"
```

Do not put the generated model, scores, or metrics under Git unless you intentionally want small demonstration artifacts.

## Commit 8 — FastAPI database layer

Add:

- `src/api/__init__.py`
- `src/api/database.py`
- `src/api/models.py`
- `src/api/schemas.py`

Run:

```bash
python -m pytest -v
git add src/api
git commit -m "Add API database models and schemas"
```

## Commit 9 — FastAPI endpoints

Add:

- `src/api/seed.py`
- `src/api/main.py`
- `tests/test_api.py`

Run:

```bash
uvicorn src.api.main:app --reload
```

In another terminal:

```bash
curl http://localhost:8000/health
curl -X POST http://localhost:8000/admin/seed
curl http://localhost:8000/anomalies
curl http://localhost:8000/metrics/summary
```

Then:

```bash
python -m pytest -v tests/test_api.py
git add src/api tests/test_api.py requirements.txt
git commit -m "Add anomaly review API"
```

## Commit 10 — React dashboard foundation

Add the entire `frontend/` directory except Dockerfile first.

Run:

```bash
cd frontend
npm install
npm run build
npm run dev
```

Create `frontend/.env`:

```text
VITE_API_URL=http://localhost:8000
```

Then:

```bash
git add frontend
git commit -m "Add React anomaly review dashboard"
```

## Commit 11 — Review workflow polish

Use the existing dropdown workflow, then add your own:

- reviewer notes input
- department filter
- review-status filter
- pagination
- loading skeleton
- empty state

Commit:

```bash
git commit -am "Add anomaly review workflow controls"
```

## Commit 12 — Docker

Add:

- `Dockerfile.api`
- `frontend/Dockerfile`
- `docker-compose.yml`

Run:

```bash
docker compose build
docker compose up
```

Open:

```text
Frontend: http://localhost:3000
API docs: http://localhost:8000/docs
```

Commit:

```bash
git add Dockerfile.api frontend/Dockerfile docker-compose.yml
git commit -m "Containerize API and frontend"
```

## Commit 13 — CI

Add:

- `.github/workflows/ci.yml`

Before committing, run:

```bash
cd frontend
npm install
```

Commit `package-lock.json`, because CI uses it for dependency caching.

Then:

```bash
git add .github/workflows/ci.yml frontend/package-lock.json
git commit -m "Add backend and frontend CI"
```

## Commit 14 — Developer commands and documentation

Add:

- `Makefile`
- update your main `README.md`
- architecture diagram
- screenshots
- model metrics
- limitations

Run:

```bash
make test
make all
```

Commit:

```bash
git add Makefile README.md
git commit -m "Document project architecture and workflow"
```

## Full local run

Use Python 3.11 for the remaining project.

```bash
deactivate
rm -rf .venv
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt

make generate
make etl
make train
make evaluate

uvicorn src.api.main:app --reload
```

In a second terminal:

```bash
source .venv/bin/activate
curl -X POST http://localhost:8000/admin/seed
```

In a third terminal:

```bash
cd frontend
npm install
npm run dev
```

## Add these lines to `.gitignore`

```gitignore
artifacts/
*.db
frontend/node_modules/
frontend/dist/
frontend/.env
data/raw/*
data/processed/*
!data/raw/.gitkeep
!data/processed/.gitkeep
```

## Final validation

```bash
python -m pytest -v
python -m src.etl.pipeline
python -m src.ml.train
python -m src.ml.evaluate
cd frontend && npm run build
docker compose build
```

## Final resume bullets after measuring real results

Replace brackets only with measured values:

```text
Built an end-to-end workforce analytics platform using Python, FastAPI,
SQLAlchemy, React, and Docker, processing [X]+ synthetic timekeeping
records through a validated, idempotent ETL pipeline.

Developed an Isolation Forest anomaly-detection workflow evaluated
against separately injected ground-truth labels, achieving [X] precision,
[Y] recall, and [Z] F1 while surfacing explainable alerts through a
human-review dashboard.

Implemented automated tests, GitHub Actions CI, containerized services,
data-quality quarantine handling, and REST endpoints for anomaly
filtering and review-state management.
```
