.PHONY: install flake8 mypy lint test docker-build deploy run

install:
	pip install -r requirements.txt
	pip install pytest flake8 mypy

flake8:
	flake8 . --config=.flake8

mypy:
	mypy --ignore-missing-imports --explicit-package-bases .

lint: flake8 mypy

test:
	pytest -q

docker-build:
	docker build -t mas-app .

deploy:
	docker compose -f compose.yml up -d

run:
	python run.py --goal "echo"
