# Maintenance Scripts

This folder contains maintenance and data-fix helper scripts.

## fix_maintenance_prices.py
Fix `MaintenanceRecord.price` from linked `Invoice` amount.

Run (PowerShell):

Get-Content scripts/fix_maintenance_prices.py | python manage.py shell

Or use the new Django management command (recommended):

```bash
python manage.py fix_maintenance_prices --dry-run
python manage.py fix_maintenance_prices
```

## fix_mr_legacy.py
LEGACY script retained for historical purposes. Do not use; replaced by `fix_maintenance_prices.py`.
