#!/usr/bin/env python
import os
import sys
import argparse
import csv
from django.apps import apps
from django.db import transaction

# Ensure project root is on sys.path so `workshop` settings package is importable
from pathlib import Path
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Setup Django environment (uses same settings as manage.py)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'workshop.settings')
import django
django.setup()


def main():
    parser = argparse.ArgumentParser(description='Create Item records for existing Service records (name-match option). Produces a CSV mapping file. Use --commit to persist changes.')
    parser.add_argument('--commit', action='store_true', help='Persist created Item records (default: dry-run).')
    parser.add_argument('--out', type=str, default='service_to_item_map.csv', help='Output CSV filename for mappings.')
    parser.add_argument('--match-case', action='store_true', help='Match service names case-sensitively when searching for existing Items.')
    args = parser.parse_args()

    commit = args.commit
    out_file = args.out
    match_case = args.match_case

    try:
        Service = apps.get_model('services', 'Service')
    except LookupError:
        print("Could not find model 'Service' in app 'services'. Adjust app/model name and re-run.")
        sys.exit(2)

    # Heuristic: find an Item-like model among installed apps
    candidate_models = []
    for app_config in apps.get_app_configs():
        for model in app_config.get_models():
            field_names = {f.name for f in model._meta.get_fields()}
            if 'name' in field_names and (('sale_price' in field_names) or ('price' in field_names) or ('quantity' in field_names) or ('is_service' in field_names)):
                candidate_models.append((app_config.label, model.__name__))

    if not candidate_models:
        print('No candidate Item-like model found automatically. Inspect models and re-run with adjusted script.')
        sys.exit(2)

    preferred = None
    for app_label, model_name in candidate_models:
        if app_label in ('inventory', 'items', 'stock', 'products') or model_name.lower() in ('item', 'part', 'inventoryitem', 'product'):
            preferred = (app_label, model_name)
            break
    if not preferred:
        preferred = candidate_models[0]

    ItemApp, ItemModelName = preferred
    Item = apps.get_model(ItemApp, ItemModelName)

    print(f"Using Item-like model: {ItemApp}.{ItemModelName}")
    print("Running in %s mode.\n" % ('COMMIT' if commit else 'DRY-RUN (no DB changes)'))

    mappings = []
    created_count = 0
    existing_count = 0

    services = Service.objects.all()
    if not services.exists():
        print('No Service records found; nothing to do.')
        return

    def find_existing_item_by_name(sname):
        qs = Item.objects.all()
        if match_case:
            return qs.filter(name=sname).first()
        else:
            return qs.filter(name__iexact=sname).first()

    for s in services:
        s_name = getattr(s, 'name', None)
        if not s_name:
            print(f"Skipping Service id={s.pk}: no name field.")
            continue

        existing = find_existing_item_by_name(s_name)
        if existing:
            existing_count += 1
            mappings.append({'service_id': s.pk, 'service_name': s_name, 'item_id': existing.pk, 'item_name': getattr(existing, 'name', '') , 'action': 'mapped_existing'})
            continue

        new_kwargs = {}
        item_field_names = {f.name for f in Item._meta.get_fields()} if hasattr(Item, '_meta') else set()

        if 'name' in item_field_names:
            new_kwargs['name'] = s_name
        if 'description' in item_field_names and hasattr(s, 'description'):
            new_kwargs['description'] = getattr(s, 'description')

        price_val = None
        for fld in ('sale_price', 'price', 'default_price', 'unit_price'):
            if hasattr(s, fld):
                price_val = getattr(s, fld)
                break
        if price_val is None and 'sale_price' in item_field_names and hasattr(s, 'price'):
            price_val = getattr(s, 'price')

        if price_val is not None and ('sale_price' in item_field_names):
            new_kwargs['sale_price'] = price_val
        elif price_val is not None and ('price' in item_field_names):
            new_kwargs['price'] = price_val

        if 'is_service' in item_field_names:
            new_kwargs['is_service'] = True
        if 'is_stock' in item_field_names and hasattr(s, 'is_service'):
            new_kwargs['is_stock'] = False

        if 'quantity' in item_field_names:
            new_kwargs['quantity'] = 0

        mappings.append({'service_id': s.pk, 'service_name': s_name, 'item_id': None, 'item_name': None, 'action': 'will_create', 'create_kwargs': new_kwargs})

        if commit:
            try:
                with transaction.atomic():
                    created = Item.objects.create(**new_kwargs)
                    created_count += 1
                    mappings[-1].update({'item_id': created.pk, 'item_name': getattr(created, 'name', ''), 'action': 'created'})
            except Exception as e:
                mappings[-1].update({'action': 'error', 'error': str(e)})

    csv_fields = ['service_id', 'service_name', 'item_id', 'item_name', 'action']
    with open(out_file, 'w', newline='', encoding='utf-8') as fh:
        writer = csv.DictWriter(fh, fieldnames=csv_fields)
        writer.writeheader()
        for m in mappings:
            row = {k: m.get(k, '') for k in csv_fields}
            writer.writerow(row)

    print('\nSummary:')
    print(f'  Services scanned: {services.count()}')
    print(f'  Existing items matched: {existing_count}')
    print(f'  Items created: {created_count}')
    print(f'  CSV mapping written to: {out_file}')

    if not commit:
        print('\nDRY-RUN: No database changes were made. Re-run with --commit to persist.')


if __name__ == '__main__':
    main()
