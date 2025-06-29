# accounts/management/commands/process_scheduled_tasks.py
from django.core.management.base import BaseCommand
from django.conf import settings
import requests
from accounts.models import ExchangeRate, Currency

class Command(BaseCommand):
    help = 'Run scheduled tasks (exchange rates, etc.)'

    def handle(self, *args, **options):
        self.update_exchange_rates()
        # Add other scheduled tasks here

    def update_exchange_rates(self):
        try:
            response = requests.get(
                f"http://data.fixer.io/api/latest?access_key={settings.FIXER_API_KEY}&base=EUR"
            )
            data = response.json()
            
            if data['success']:
                eur = Currency.objects.get(code='EUR')
                for currency in Currency.objects.exclude(code='EUR'):
                    if currency.code in data['rates']:
                        ExchangeRate.objects.update_or_create(
                            from_currency=eur,
                            to_currency=currency,
                            defaults={'rate': data['rates'][currency.code]}
                        )
                self.stdout.write(self.style.SUCCESS('Exchange rates updated'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error updating rates: {e}'))