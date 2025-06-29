# cards/templatetags/cards_extras.py
from django import template
from decimal import Decimal

register = template.Library()

@register.filter
def mul(value, arg):
    """
    Multiplies the value by the argument.
    Usage: {{ value|mul:arg }}
    Ensures Decimal arithmetic for precision.
    """
    try:
        # Convert both to Decimal for precise multiplication
        return Decimal(str(value)) * Decimal(str(arg))
    except (TypeError, ValueError, Decimal.InvalidOperation):
        # Handle cases where conversion or multiplication fails
        return '' # Or return 0, None, or raise an error as appropriate for your needs