from django.core.management.base import BaseCommand
from services.models import Service
from inventory.models import Part
import csv
import sys
import re


def normalize(s):
    return re.sub(r"\s+", " ", (s or "").strip()).lower()


def tokens(s):
    return set(normalize(s).split()) if s else set()


class Command(BaseCommand):
    help = "Map Services to inventory Parts and emit CSV dry-run report"

    def add_arguments(self, parser):
        parser.add_argument(
            "--output",
            "-o",
            help="CSV output file path (default stdout)",
            default=None,
        )
        parser.add_argument(
            "--no-dry-run",
            action="store_true",
            help="Disable dry-run and allow creating placeholder Parts when used with --create-placeholders",
        )
        parser.add_argument(
            "--create-placeholders",
            action="store_true",
            help="Create placeholder Part records for unmatched Services (only when --no-dry-run is passed)",
        )

    def handle(self, *args, **options):
        out_path = options.get("output")
        dry_run = not options.get("no_dry_run")
        create_placeholders = options.get("create_placeholders")

        if create_placeholders and dry_run:
            self.stdout.write(self.style.WARNING("--create-placeholders requested but running in dry-run mode. Use --no-dry-run to apply changes."))

        if out_path:
            out_file = open(out_path, "w", newline="", encoding="utf-8")
        else:
            out_file = sys.stdout

        writer = csv.DictWriter(
            out_file,
            fieldnames=[
                "service_id",
                "service_name",
                "matched_part_id",
                "matched_part_name",
                "match_type",
                "confidence",
                "note",
            ],
        )
        writer.writeheader()

        parts = list(Part.objects.all())
        parts_by_name = {normalize(p.name): p for p in parts}

        for svc in Service.objects.all():
            svc_name = svc.name or ""
            svc_norm = normalize(svc_name)
            matched = None
            match_type = ""
            confidence = 0.0
            note = ""

            # exact match
            p = parts_by_name.get(svc_norm)
            if p:
                matched = p
                match_type = "exact"
                confidence = 1.0
            else:
                # startswith
                for p in parts:
                    if normalize(p.name).startswith(svc_norm) and svc_norm:
                        matched = p
                        match_type = "startswith"
                        confidence = 0.8
                        break
            if not matched:
                # contains
                for p in parts:
                    if svc_norm and svc_norm in normalize(p.name):
                        matched = p
                        match_type = "contains"
                        confidence = 0.6
                        break
            if not matched:
                # token intersection
                svc_tokens = tokens(svc_name)
                best = None
                best_score = 0
                for p in parts:
                    p_tokens = tokens(p.name)
                    if not svc_tokens or not p_tokens:
                        continue
                    common = svc_tokens.intersection(p_tokens)
                    score = len(common)
                    if score > best_score:
                        best_score = score
                        best = p
                if best and best_score > 0:
                    matched = best
                    match_type = "token_overlap"
                    # confidence scaled by proportion of matched tokens
                    confidence = round(best_score / max(1, len(tokens(svc_name))), 2)

            if matched:
                writer.writerow(
                    {
                        "service_id": svc.id,
                        "service_name": svc_name,
                        "matched_part_id": getattr(matched, "id", ""),
                        "matched_part_name": getattr(matched, "name", ""),
                        "match_type": match_type,
                        "confidence": confidence,
                        "note": "",
                    }
                )
            else:
                # No match found
                writer.writerow(
                    {
                        "service_id": svc.id,
                        "service_name": svc_name,
                        "matched_part_id": "",
                        "matched_part_name": "",
                        "match_type": "none",
                        "confidence": 0,
                        "note": "no-match",
                    }
                )
                if create_placeholders and not dry_run:
                    # create a basic placeholder part
                    try:
                        dept = getattr(svc, "department", None)
                        part = Part.objects.create(
                            name=svc_name,
                            quantity=0,
                            low_stock_alert=5,
                            department=dept if dept else None,
                        )
                        writer.writerow(
                            {
                                "service_id": svc.id,
                                "service_name": svc_name,
                                "matched_part_id": part.id,
                                "matched_part_name": part.name,
                                "match_type": "created_placeholder",
                                "confidence": 0,
                                "note": "created placeholder",
                            }
                        )
                    except Exception as e:
                        self.stderr.write(f"Failed to create placeholder for Service {svc.id}: {e}")

        if out_path:
            out_file.close()
        self.stdout.write(self.style.SUCCESS("Mapping complete."))
