.PHONY: help
help:
	@echo "Available targets:"
	@echo "  django.sh            - Run python interactive shell"
	@echo "  django.bash          - Run bash shell in django container"
	@echo "  django.test          - Run django tests"
	@echo "  django.superuser     - Create django superuser"
	@echo "  db.migration.migrate - Create django migrations and migrate to database"
	@echo "  db.migration.clean   - Remove all django migrations (Dangerous!)"
	@echo "  db.volume.delete     - Delete database volume"
	@echo "  code.format          - Format code using black, isort and flake8"
	@echo "  git.prune.deleted    - Delete local branches that have been deleted on remote"


.PHONY: db.migration.migrate
db.migration.migrate:
	@echo "Running django migrate..."
	docker compose run --rm django python manage.py makemigrations
	docker compose run --rm django python manage.py migrate


.PHONY: django.sh
django.sh:
	docker compose run --rm django python manage.py shell


.PHONY: django.bash
django.bash:
	docker compose run --rm django /bin/bash


.PHONY: db.volume.delete
db.volume.delete:
	docker compose down
	docker volume rm flowback-backend_postgres_data | true


.PHONY: code.format
code.format:
	@echo "Running code linters and formatters..."
	docker compose run --rm django sh -c "black . && isort . && flake8 ."


.PHONY: django.test
django.test:
	docker compose run --rm django python manage.py test $(app)

.PHONY: django.superuser
django.superuser:
	docker compose run --rm django python manage.py createsuperuser

.PHONY: django.migrations.clean
django.migrations.clean:
	@echo "Are you sure you want to delete all migrations? [y/n] " && read ans && [ $${ans:-n} = y ]; \
	if [ $$? -eq 0 ]; then \
		echo "Removing migration files..." ; \
		find . -path "*/migrations/*.py" -not -name "__init__.py" -delete ; \
	else \
		echo "Aborted"; \
	fi

.PHONY: git.prune.deleted
git.prune.deleted:
	@echo "Pruning deleted branches..."
	git fetch -p && git branch -vv | awk '/: gone]/{print $1}' | xargs git branch -D

.PHONY: start-celery
start-celery:
	@echo "Starting celery..."
	./scripts/start-celery.sh
	