# Rol

You should acts as senior software engineer for this project which was constructed over django
You have a rol of an agent in this project. Your responsibilities include assisting with tasks, providing information, and supporting the team in achieving project goals. Please ensure to follow the guidelines and maintain effective communication with other team members.

# Environment

This projects runs over django framework, using django-Cookiecutter, which is a project template for Django that provides a structured and organized way to set up a new Django project. It includes best practices, pre-configured settings, and a directory structure that promotes maintainability and scalability.
use docker compose to run the project, and make sure to have the necessary environment variables set up in the .envs/.production/.postgresql file.

- local.yml: describes a development environment
- production.yml: describes a production environment
- manage.py should change from local to production depending on the environment being executed.
- All frontend code was created over admins py files (temporary admin interface) and the templates folder, which contains the HTML templates used to render the frontend of the application. The templates are organized in a way that allows for easy customization and extension of the frontend.
- All backend code is located under src folder, which contains the main application logic, models, views, and other backend components. The src folder is structured to promote modularity and maintainability of the codebase.

# Project details

README.md contains detailed information about the project, including necessary variables, internal configuration, and instructions for executing the system. It also provides guidance on creating a superuser and highlights the use of Django framework version 5.

# AGENTS.md — django-attendance-check (Sistema INPROMAR)

## Layout trap (read first)

- The repo root only contains `README.md`, `AGENTS.md`, and `src/`. The **real Django project root is `src/`** (cookiecutter-django layout). Run every command from `src/`, not the repo root.
- Inside `src/`, application code lives in `src/src/` (double `src`). App entrypoints are Django apps: `users` (custom `AUTH_USER_MODEL`), `clocking` (attendance/clocking logic), `employees`, `dining_room`, `reports`, `indentities`, `preloads`, `peladoydescabezado`, `settings` (an app named "settings" for client config — NOT Django settings).
- Django settings are in `src/config/settings/{base,local,production,test}.py` under the `config` package.
- General report of `dining_room ` is a synonym for reports generateds from `GhostService*`, therefore, when I say anything like "reporte general de cocina", "general report from dining_room", "reports of ghosts*" you shoud keep in mind that I refer to dining_room

## Commands (from `src/`)

```bash
# Dev environment (django on :8000, postgres, redis, mailpit :8025, celery worker+beat, flower :5555, pgadmin :9001)
docker compose -f local.yml up --build

# Production
docker compose -f production.yml up --build -d

# Django-ish tasks via docker
docker compose -f production.yml run --rm django python manage.py createsuperuser

# Tests (pytest-django): settings wired via addopts in pyproject.toml
docker compose -f local.yml run --rm django pytest
docker compose -f local.yml run --rm django pytest src/clocking/tests.py
```

- Toolchain: Python 3.11, Django **4.2** (pinned in `requirements/base.txt`; README claims Django 5 — stale, don't trust it). Docker images are built from `src/compose/{local,production}/django/Dockerfile`.
- One dev management command exists: `src/employees/management/commands/preload_employers.py` — loads employee data from the CSVs in `src/preloads/` (concepcion, destajos, fijos, nuevos_ingresos.csv).
- Frontend is the Django admin (extended via `django-unfold`; see `UNFOLD` in `config/settings/base.py`) plus `src/src/templates/` and `admin_filters/` — there is no separate JS frontend.

## Environment gotchas

- `manage.py` and `config/wsgi.py` default `DJANGO_SETTINGS_MODULE` to `config.settings.production`. When running anything outside Docker compose, the compose image sets the settings for you, but run raw commands carefully.
- Env files are checked in at `src/.envs/.local/.django` and `.envs/.local/.postgres` — local compose references these directly. Production expects `src/.envs/.production/.django` + `.postgres` (README calls the file `.postgresql` — stale; compose uses `.postgres`).
- Postgres data is stored in the named volume `src_local_postgres_data`; backup dir is hardcoded to `/home/.inpromar/postgres/backups` in `production.yml`.
- To run flat (no Docker): create a virtualenv, install `requirements/{production,local}.txt`, and export the env vars from the `.envs` files (settings read `DATABASE_URL`, `DJANGO_DEBUG`, etc. via django-environ). `base.py` only reads a `.env` file if `DJANGO_READ_DOT_ENV_FILE=true`.

## Conventions

- Line length 119 (black/isort/flake8 all configured; flake8 config is in `setup.cfg`, the rest in `src/pyproject.toml`).
- pytest is configured with `--ds=config.settings.test --reuse-db`, so tests use the `test` settings module automatically.
- Keep settings additions in `config/settings/*.py` per environment; `base.py` is shared by all.
