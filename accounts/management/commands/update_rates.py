# accounts/management/commands/update_rates.py
from django.core.management.base import BaseCommand
from accounts.models import Currency, ExchangeRate
import requests
from django.conf import settings

class Command(BaseCommand):
    help = 'Updates currency exchange rates from Fixer API'

    def handle(self, *args, **options):
        API_KEY = settings.FIXER_API_KEY
        response = requests.get(
            f"http://data.fixer.io/api/latest?access_key={API_KEY}&base=EUR"
        )
        data = response.json()
        
        if data['success']:
            eur = Currency.objects.get(code='EUR')
            for currency in Currency.objects.exclude(code='EUR'):
                rate = data['rates'].get(currency.code)
                if rate:
                    ExchangeRate.objects.update_or_create(
                        from_currency=eur,
                        to_currency=currency,
                        defaults={'rate': rate}
                    )
            self.stdout.write(self.style.SUCCESS('Successfully updated rates'))
        else:
            self.stdout.write(self.style.ERROR('Failed to update rates'))