# accounts/utils.py
from django.shortcuts import get_object_or_404
from .models import Currency, Wallet, Transaction
import uuid

def get_user_wallet(user, currency_code):
    currency = get_object_or_404(Currency, code=currency_code.upper())
    wallet, created = Wallet.objects.get_or_create(
        user=user,
        currency=currency,
        defaults={'balance': 0.00}
    )
    return wallet

def credit_wallet(user, amount, currency_code, transaction_type='deposit', description=''):
    wallet = get_user_wallet(user, currency_code)
    wallet.balance += amount
    wallet.save()
    
    transaction = Transaction.objects.create(
        wallet=wallet,
        amount=amount,
        transaction_type=transaction_type,
        description=description,
        reference=f"CR-{uuid.uuid4().hex[:10]}",
        status='completed'
    )
    return transaction

def debit_wallet(user, amount, currency_code, transaction_type='withdrawal', description=''):
    wallet = get_user_wallet(user, currency_code)
    
    if wallet.balance < amount:
        raise ValueError("Insufficient balance")
    
    wallet.balance -= amount
    wallet.save()
    
    transaction = Transaction.objects.create(
        wallet=wallet,
        amount=-amount,  # Negative for debits
        transaction_type=transaction_type,
        description=description,
        reference=f"DR-{uuid.uuid4().hex[:10]}",
        status='completed'
    )
    return transaction

def convert_currency(user, from_currency_code, to_currency_code, amount):
    from_wallet = get_user_wallet(user, from_currency_code)
    to_wallet = get_user_wallet(user, to_currency_code)
    
    if from_wallet.balance < amount:
        raise ValueError("Insufficient balance")
    
    # Get exchange rate (simplified - in reality, fetch from API)
    from_currency = from_wallet.currency
    to_currency = to_wallet.currency
    converted_amount = amount * (to_currency.exchange_rate / from_currency.exchange_rate)
    
    # Perform transactions
    debit_wallet(
        user, amount, from_currency_code,
        transaction_type='conversion',
        description=f"Converted to {to_currency.code}"
    )
    
    credit_wallet(
        user, converted_amount, to_currency_code,
        transaction_type='conversion',
        description=f"Converted from {from_currency.code}"
    )
    
    return converted_amount
