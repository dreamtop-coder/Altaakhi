# Script Safety Guide

This document lists workspace scripts that can delete or reset data, with safe-run instructions.

IMPORTANT: Always back up `db.sqlite3` before running any destructive script.

Back up DB (PowerShell):

```powershell
Copy-Item db.sqlite3 db.sqlite3.bak.$((Get-Date).ToString('yyyyMMdd-HHmmss'))
```

Back up DB (POSIX):

```bash
cp db.sqlite3 db.sqlite3.bak.$(date +%Y%m%d-%H%M%S)
```

---

## Destructive scripts

- `clear_maintenance_and_invoices.py`
  - Action: Deletes ALL `MaintenanceRecord` and ALL `Invoice` rows.
  - Protection: Requires `--confirm` or `CONFIRM_CLEAR=1`.
  - Safe run examples:
    - `python clear_maintenance_and_invoices.py --confirm`
    - `CONFIRM_CLEAR=1 python clear_maintenance_and_invoices.py`

- `clear_clients_maintenance_payments.py`
  - Action: Deletes ALL `Client`, ALL `MaintenanceRecord`, ALL `Payment`.
  - Protection: Requires `--confirm` or `CONFIRM_CLEAR=1`.
  - Safe run examples:
    - `python clear_clients_maintenance_payments.py --confirm`
    - `CONFIRM_CLEAR=1 python clear_clients_maintenance_payments.py`

- `scripts/delete_placeholder_invoices.py`
  - Action: Deletes placeholder invoices (amount==0, no InvoiceItem, no Payment).
  - Protection: Interactive prompt. Type `DELETE` to confirm.
  - Safe run:
    - `python scripts/delete_placeholder_invoices.py` (review list, then confirm)

- `invoices/management/commands/list_placeholder_invoices.py`
  - Action: Lists placeholder invoices; supports deletion with flags.
  - Protection: Requires `--delete --yes` to delete.
  - Safe run:
    - List: `python manage.py list_placeholder_invoices`
    - Delete (after review + backup): `python manage.py list_placeholder_invoices --delete --yes`

- `reset_all_ids.py`
  - Action: Deletes records from key tables and resets SQLite sequences (wipes data).
  - Protection: now requires `--confirm` or `CONFIRM_CLEAR=1`.
  - Safe run:
    - `python reset_all_ids.py --confirm`
    - `CONFIRM_CLEAR=1 python reset_all_ids.py`

- `reset_car_delivery.py` (management command)
  - Action: Resets car status and marks invoices unpaid; deletes payments for the car.
  - Protection: None (operates on a specific plate); use with care.
  - Safe run:
    - `python manage.py reset_car_delivery PLATE_NUMBER --status waiting`

- `scripts/*` and other reset utilities
  - Action: Varies. Inspect before running; prefer `--confirm` support.

---

## Recommendations

1. Always back up `db.sqlite3` before running destructive scripts.
2. Prefer running scripts in a dev/test copy of the DB.
3. Use the `--confirm` flag or `CONFIRM_CLEAR=1` env var to allow destructive actions.
4. I can further patch any remaining scripts to require confirmation. Ask me to patch specific scripts if you want.

---

If you want, I can open a PR containing these safety changes and this document.
