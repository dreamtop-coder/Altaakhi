from django.apps import AppConfig


class InvoicesConfig(AppConfig):
    name = 'invoices'

    def ready(self):
        import invoices.signals
