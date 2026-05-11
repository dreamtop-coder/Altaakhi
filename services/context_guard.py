"""
Simple Context Guard service.

Purpose: provide an explicit, reusable small service to resolve whether a
request is opened with a fixed context (e.g. `car_id` for maintenance) and
offer helpers to enforce that context on `request.POST` when needed.

Keep this intentionally small and explicit so callers control when to use it.
"""
from typing import Dict, Any


class ContextGuard:
    @staticmethod
    def resolve(request, model: str = None) -> Dict[str, Any]:
        """Return a small context dict for the given model.

        Returns:
            { 'locked': bool, 'car': Car|None, 'customer': Client|None }

        Caller should import models lazily to avoid circular imports.
        """
        ctx = {'locked': False, 'car': None, 'customer': None}
        try:
            if model == 'maintenance':
                car_id = request.GET.get('car_id') or request.POST.get('car_id')
                if car_id:
                    try:
                        from cars.models import Car

                        car = Car.objects.select_related('client').filter(id=car_id).first()
                        if car:
                            ctx['locked'] = True
                            ctx['car'] = car
                            ctx['customer'] = getattr(car, 'client', None)
                    except Exception:
                        # best-effort: if model import or DB lookup fails, treat as unlocked
                        pass
            # future models can be added here (e.g. bookings, orders)
        except Exception:
            pass
        return ctx

    @staticmethod
    def enforce_request_post(request, ctx: Dict[str, Any]) -> None:
        """If ctx indicates locked context, override relevant POST keys.

        This mutates `request.POST` by replacing it with a copy that contains
        enforced values. Callers should do this early in POST handling when
        they want server-side source-of-truth behavior.
        """
        if not ctx or not ctx.get('locked'):
            return
        try:
            p = request.POST.copy()
            cust = ctx.get('customer')
            car = ctx.get('car')
            if cust and getattr(cust, 'id', None):
                p['selected_client_id'] = str(cust.id)
            if car and getattr(car, 'id', None):
                p['selected_client_car'] = str(car.id)
                p['plate_number'] = getattr(car, 'plate_number', '') or ''
            request.POST = p
        except Exception:
            pass

    @staticmethod
    def resolve_and_enforce(request, model: str = None) -> Dict[str, Any]:
        """Convenience: resolve context and enforce POST in one call."""
        ctx = ContextGuard.resolve(request, model=model)
        ContextGuard.enforce_request_post(request, ctx)
        return ctx
