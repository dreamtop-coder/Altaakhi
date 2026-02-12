Migration squashes and upgrade notes
=================================

Summary
-------
- `services` migrations squashed up to: `services/0001_squashed_0003_add_car_fk.py` (follow-up adds cross-app fields)
- `cars` migrations squashed up to: `cars/0001_squashed_0004_maintenancerecord_maintenance_date.py`
- `inventory` migrations squashed up to: `inventory/0001_squashed_0007_part_track_purchases_part_track_sales.py`

Important upgrade guidance
--------------------------

- Do NOT delete the original (pre-squash) migration files yet. Keep them in the repo until every running instance / environment has applied the migrations. Removing them prematurely will break upgrades for older deployments.

- Fresh installs

  - New installs will use the squashed migrations created above. Run the usual `python manage.py migrate` and migrations will apply in the correct order (the squashed migrations depend on the squashed `services` migration where needed).

- Existing deployments (upgrade path)

  1. Back up the database before applying schema changes.
 2. If the deployment has an existing migration history (older migrations applied), continue applying migrations normally — Django will skip operations already applied and use the old migrations that exist in the repository.
 3. Only remove the old migrations after you are certain every environment has the new squashed migrations applied (and you have coordinated with all deploys).

- Cross-app fields

  - The squashed migrations were generated to avoid circular dependencies on fresh installs. In some cases we moved cross-app FK/M2M additions into follow-up migrations (see `services/0002_add_parts_and_car.py`). If you maintain custom deployment scripts, ensure follow-up migrations are present and ordered correctly.

- Troubleshooting

  - If migrate fails because of an "InconsistentMigrationHistory" error, check the migration order on the target DB. This usually means a migration was applied on the DB that the new squashed migration expects to run later. Restoring from backup and applying migrations in order or applying the missing dependency migration first usually resolves it.
  - If you see model/field NOT NULL errors during tests or deploys, verify the default-handling logic in models (we added safe defaults for `Service.department` to avoid NOT NULL failures during test DB creation).

Recommendations
---------------

- Keep the squashed migration files committed. Wait at least one full release cycle and confirm all environments (staging, preprod, production) have applied them before deleting old migration files.
- Document the squash in your release notes and share the upgrade plan with the ops team.
- If you'd like, I can prepare a cleanup PR (delete old migrations) once you confirm all environments are upgraded.

Files created in this change
--------------------------
- `services/0001_squashed_0003_add_car_fk.py`
- `cars/0001_squashed_0004_maintenancerecord_maintenance_date.py`
- `inventory/0001_squashed_0007_part_track_purchases_part_track_sales.py`
