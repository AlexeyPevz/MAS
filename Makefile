.PHONY: install lint test run

install:
	pip install -r requirements.txt
	pip install pytest flake8

lint:
	flake8 . --ignore=E501

test:
	pytest -q

run:
	python run.py --goal "echo"
