.PHONY: test generate etl train evaluate api frontend all

test:
	python -m pytest -v

generate:
	python -m src.generation.generate_departments
	python -m src.generation.generate_employees
	python -m src.generation.generate_shifts
	python -m src.generation.generate_time_punches
	python -m src.generation.inject_anomalies

etl:
	python -m src.etl.pipeline

train:
	python -m src.ml.train

evaluate:
	python -m src.ml.evaluate

api:
	uvicorn src.api.main:app --reload

frontend:
	cd frontend && npm run dev

all: generate etl train evaluate
