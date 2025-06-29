# cards/middleware.py
from decimal import Decimal, InvalidOperation
from django.http import JsonResponse

class DecimalConversionMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Convert float strings to Decimal for specific views
        if request.path == '/api/calculate-offer/' and 'value' in request.GET:
            try:
                request.decimal_value = Decimal(str(request.GET['value']))
            except (ValueError, InvalidOperation):
                return JsonResponse({
                    'status': 'invalid_value',
                    'message': 'Invalid numeric value'
                }, status=400)
        return self.get_response(request)