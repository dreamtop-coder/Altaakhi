# Altaakhi Workshop — Quick README

This repository contains a Django-based workshop management system.

## Migration Squash & Upgrade Notes

We have recently squashed migrations for major apps:

- `services`: up to `0003`
- `cars`: up to `0004`
- `inventory`: up to `0007`

Please see [RELEASE_NOTES.md](RELEASE_NOTES.md) for detailed instructions on upgrading existing databases and fresh installs. Do not delete old migration files until all environments have applied the new squashed migrations.
