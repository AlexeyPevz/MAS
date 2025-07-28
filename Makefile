.PHONY: install lint test docker-build deploy run

install:
	pip install -r requirements.txt
	pip install flake8 mypy pytest

lint:
	flake8 .
	mypy agents config tools config_loader.py run.py --ignore-missing-imports || true

test:
	pytest -q

docker-build:
	docker build -t mas-app .

deploy:
	docker compose -f deploy/internal/compose.yml up -d

run:
	python run.py --goal "echo"
