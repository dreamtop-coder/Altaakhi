# Copilot Instructions for Altaakhi Workshop

## Project Overview
- **Django-based multi-app monolith**: The project is structured as a Django workspace with apps for cars, clients, inventory, invoices, reports, services, settings, users, and workshop.
- **Data storage**: Uses a local SQLite database (`db.sqlite3`).
- **App boundaries**: Each app (e.g., `cars`, `clients`, `invoices`) has its own models, views, forms, and admin logic. Cross-app communication is via Django ORM and imports.

## Key Workflows
- **Run the server**: `python manage.py runserver`
- **Migrations**: `python manage.py makemigrations` and `python manage.py migrate`
- **Create demo data**: `python create_demo_data.py`
- **Reset/test data**: Use scripts like `reset_all_ids.py`, `reset_car_delivery.py`, `clear_maintenance_and_invoices.py`
- **Debugging**: Use `debug_data_overview.py` for data inspection.

## Project Conventions
- **App structure**: Each app contains `models.py`, `views.py`, `forms.py`, and may have specialized files (e.g., `brand_models.py`, `forms_maintenance.py` in `cars`).
- **Templates**: Shared in `/templates/`, not per-app. Template names match view purposes (e.g., `add_client.html`, `edit_invoice.html`).
- **No REST API**: All logic is server-rendered via Django views and templates.
- **Custom scripts**: Top-level Python scripts are used for data manipulation and maintenance outside the Django management command system.
- **No explicit test runner**: Tests exist in each app but are not run by default; use `python manage.py test <app>`.

## Patterns & Integration
- **Cross-app imports**: Import models and utilities directly between apps as needed.
- **Forms**: Custom forms are used for most data entry and editing, often split into multiple files for complex domains (see `cars/forms_*.py`).
- **No API endpoints**: All user interaction is via HTML forms and server-rendered pages.
- **Static files**: Located in `/static/`.

## Examples
- To add a new car brand: update `cars/brand_models.py`, `cars/brand_forms.py`, and corresponding templates.
- To add a new invoice type: update `invoices/models.py`, `invoices/forms.py`, and `invoices/views.py`.

## Key Files/Directories
- `manage.py`: Django entry point
- `cars/`, `clients/`, `invoices/`, etc.: Main Django apps
- `templates/`: All HTML templates
- Top-level scripts: Data and maintenance utilities

---
For more details, inspect the relevant app directory and top-level scripts. Follow the structure and naming conventions already present in the codebase.