# Changelog

## Unreleased

### Added
- Enforced model-based deletion permissions for clients, invoices, and payments.
- Logged denied delete attempts to `AuditLog` with action `DELETE_ATTEMPT_DENIED`.
- Added tests covering allowed and denied delete operations for clients, invoices, and payments.

### Security
- Prevent unauthorized deletions by returning `403 Forbidden` and logging attempts.

---

(See PR `feature/security-hardening-v1` for details)
