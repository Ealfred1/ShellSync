.PHONY: run migrate makemigrations shell createsuperuser test clean install help

# Variables
PYTHON = python
MANAGE = $(PYTHON) manage.py
PORT = 8000
HOST = 0.0.0.0

help:
	@echo "Available commands:"
	@echo "  make run              - Run development server"
	@echo "  make run port=<port>  - Run server on specific port"
	@echo "  make migrate          - Apply database migrations"
	@echo "  make makemigrations   - Create new migrations"
	@echo "  make shell            - Open Django shell"
	@echo "  make createsuperuser  - Create superuser"
	@echo "  make test             - Run tests"
	@echo "  make clean            - Remove Python compiled files"
	@echo "  make install          - Install dependencies"
	@echo "  make lint             - Run code linting"

run:
	$(MANAGE) runserver $(HOST):$(PORT)

migrate:
	$(MANAGE) migrate

makemigrations:
	$(MANAGE) makemigrations

shell:
	$(MANAGE) shell

createsuperuser:
	$(MANAGE) createsuperuser

test:
	$(MANAGE) test

clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type f -name ".coverage" -delete
	find . -type d -name "htmlcov" -exec rm -rf {} +

install:
	pip install -r requirements.txt

lint:
	pylint */*.py
	black .
	isort .

# Database related commands
dbshell:
	$(MANAGE) dbshell

flush:
	$(MANAGE) flush

# Static files
collectstatic:
	$(MANAGE) collectstatic --noinput

# Custom commands for our remote control app
list-processes:
	$(MANAGE) shell -c "from control_app.agent import get_running_processes; print(get_running_processes())"

system-info:
	$(MANAGE) shell -c "from control_app.agent import get_system_info; print(get_system_info())"

list-apps:
	$(MANAGE) shell -c "from control_app.agent import list_applications; print(list_applications())"

# Development utilities
dev-setup: install migrate

# Production commands
prod-setup: install migrate collectstatic

# Run with Gunicorn
gunicorn:
	gunicorn config.wsgi:application --bind $(HOST):$(PORT) --workers 3

# Create initial data
loaddata:
	$(MANAGE) loaddata initial_data.json

dumpdata:
	$(MANAGE) dumpdata --exclude auth.permission --exclude contenttypes > initial_data.json 