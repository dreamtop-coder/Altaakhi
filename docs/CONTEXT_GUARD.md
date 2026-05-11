ContextGuard — Quick Reference

Purpose
- Small service to detect/enforce page context (e.g. `car_id` on maintenance/add).
- Supports shadow mode (resolve + logging) and controlled enforcement (POST override).

Files
- `services/context_guard.py` — ContextGuard.resolve / enforce_request_post helpers
- `cars/views_add_maintenance.py` — ContextGuard used in shadow mode and optional enforcement
- `debug_context_guard.log` — runtime log produced next to project root when resolve/enforce run

Feature Toggle
- Enable enforcement only when you want a controlled rollout.
- Two supported settings (either works):
  - `CONTEXT_GUARD_ENFORCE = True`
  - `ENABLE_CONTEXT_GUARD_POST_OVERRIDE = True`

Current Scope
- Currently used only in:
   - `maintenance/add`
- Not applied to (by design):
   - `bills/add` (standalone purchases — no vehicle context)
   - `payments/add`

Expected Behavior
- When `car_id` exists in the request (URL or POST):
   - context becomes locked
   - `selected_client_id` and `selected_client_car` are authoritative and will be enforced
   - tampering hidden inputs should be overridden or the request rejected by server logic
- When `car_id` is absent:
   - page remains fully editable and no enforcement is applied
   - ContextGuard will resolve to `locked: False`

How to enable locally (Windows PowerShell)
1. Set environment variable (session):
   ```powershell
   setx CONTEXT_GUARD_ENFORCE "1"
   # Restart your terminal or sign-out/in so new env is visible to new processes
   ```
2. Restart the Django dev server:
   ```powershell
   python manage.py runserver
   ```

How to test tamper resistance (recommended)
1. Open in browser:
   `http://127.0.0.1:8000/maintenance/add/?car_id=<CAR_ID>`
2. In DevTools, modify the hidden `selected_client_id` input to another client id (tamper).
3. Submit the form.
4. Inspect logs:
   - `debug_context_guard.log` — should show `ENFORCE_APPLIED` when enforcement ran.
   - `debug_post_dump.log` — inspect the POST keys the server actually processed; enforced values should appear.

Quick rollback
- To disable enforcement immediately, unset the env var and restart server:
  ```powershell
  setx CONTEXT_GUARD_ENFORCE ""
  # restart server
  ```

Notes
- We intentionally keep the old fallback logic in `cars/views_add_maintenance.py` while we run this controlled rollout.
- `ContextGuard` is intentionally small and explicit (service-style) rather than a global middleware to avoid unintended side effects.
- Once logs and tests are clean, we can progressively remove the fallback and adopt `ContextGuard` as the single source-of-truth.

Status: Shadow mode + logging enabled; controlled enforcement available behind toggle.
