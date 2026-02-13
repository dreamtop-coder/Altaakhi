from django.core.management.base import BaseCommand, CommandError
from django.apps import apps
from django.db import transaction
import csv


class Command(BaseCommand):
    help = 'Create Item records for existing Service records (name-match option). Produces a CSV mapping file. Use --commit to persist changes.'

    def add_arguments(self, parser):
        parser.add_argument('--commit', action='store_true', help='Persist created Item records (default: dry-run).')
        parser.add_argument('--out', type=str, default='service_to_item_map.csv', help='Output CSV filename for mappings.')
        parser.add_argument('--match-case', action='store_true', help='Match service names case-sensitively when searching for existing Items.')

    def handle(self, *args, **options):
        commit = options['commit']
        out_file = options['out']
        match_case = options['match_case']

        # Discover Service model
        try:
            Service = apps.get_model('services', 'Service')
        except LookupError:
            raise CommandError("Could not find model 'Service' in app 'services'. Adjust app/model name and re-run.")

        # Heuristic: find an Item-like model among installed apps
        candidate_models = []
        for app_config in apps.get_app_configs():
            for model in app_config.get_models():
                field_names = {f.name for f in model._meta.get_fields()}
                # item-like heuristics: has a `name` field and either `sale_price`/`price` or `quantity` or `is_service`
                if 'name' in field_names and (('sale_price' in field_names) or ('price' in field_names) or ('quantity' in field_names) or ('is_service' in field_names)):
                    candidate_models.append((app_config.label, model.__name__))

        if not candidate_models:
            raise CommandError('No candidate Item-like model found automatically. Inspect models and re-run with adjusted script.')

        # Prefer obvious app names
        preferred = None
        for app_label, model_name in candidate_models:
            if app_label in ('inventory', 'items', 'stock', 'products') or model_name.lower() in ('item', 'part', 'inventoryitem', 'product'):
                preferred = (app_label, model_name)
                break
        if not preferred:
            preferred = candidate_models[0]

        ItemApp, ItemModelName = preferred
        Item = apps.get_model(ItemApp, ItemModelName)

        self.stdout.write(self.style.NOTICE(f"Using Item-like model: {ItemApp}.{ItemModelName}"))
        self.stdout.write("Running in %s mode.\n" % ('COMMIT' if commit else 'DRY-RUN (no DB changes)'))

        mappings = []
        created_count = 0
        existing_count = 0

        services = Service.objects.all()
        if not services.exists():
            self.stdout.write('No Service records found; nothing to do.')
            return

        # Choose name lookup function
        def find_existing_item_by_name(sname):
            qs = Item.objects.all()
            if match_case:
                return qs.filter(name=sname).first()
            else:
                return qs.filter(name__iexact=sname).first()

        for s in services:
            s_name = getattr(s, 'name', None)
            if not s_name:
                self.stdout.write(self.style.WARNING(f"Skipping Service id={s.pk}: no name field."))
                continue

            existing = find_existing_item_by_name(s_name)
            if existing:
                existing_count += 1
                mappings.append({'service_id': s.pk, 'service_name': s_name, 'item_id': existing.pk, 'item_name': getattr(existing, 'name', '') , 'action': 'mapped_existing'})
                continue

            # Build new Item kwargs from Service fields if available
            new_kwargs = {}
            # Common candidate fields
            if hasattr(Item, '_meta'):
                item_field_names = {f.name for f in Item._meta.get_fields()}
            else:
                item_field_names = set()

            if 'name' in item_field_names:
                new_kwargs['name'] = s_name
            if 'description' in item_field_names and hasattr(s, 'description'):
                new_kwargs['description'] = getattr(s, 'description')
            # price heuristics
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

            # mark as service where possible
            if 'is_service' in item_field_names:
                new_kwargs['is_service'] = True
            if 'is_stock' in item_field_names and hasattr(s, 'is_service'):
                # if Item uses is_stock instead of is_service
                new_kwargs['is_stock'] = False

            # default quantity fields
            if 'quantity' in item_field_names:
                # services are not stock, set 0 if present
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

        # Write CSV output
        csv_fields = ['service_id', 'service_name', 'item_id', 'item_name', 'action']
        with open(out_file, 'w', newline='', encoding='utf-8') as fh:
            writer = csv.DictWriter(fh, fieldnames=csv_fields)
            writer.writeheader()
            for m in mappings:
                row = {k: m.get(k, '') for k in csv_fields}
                writer.writerow(row)

        self.stdout.write('\nSummary:')
        self.stdout.write(f'  Services scanned: {services.count()}')
        self.stdout.write(f'  Existing items matched: {existing_count}')
        self.stdout.write(f'  Items created: {created_count}')
        self.stdout.write(f'  CSV mapping written to: {out_file}')

        if not commit:
            self.stdout.write(self.style.WARNING('\nDRY-RUN: No database changes were made. Re-run with --commit to persist.'))
