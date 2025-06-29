# accounts/models.py
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.conf import settings # Although settings is imported, it's not directly used in the User model definition here

class User(AbstractUser):
    # AbstractUser already provides:
    # username, first_name, last_name, email, is_staff, is_active, date_joined, last_login

    # Making email unique is highly recommended for user accounts,
    # as AbstractUser's email field is not unique by default.
    # You might also want to set blank=False and null=False if email is mandatory.
    email = models.EmailField(unique=True, blank=False, null=False, verbose_name='email address')

    # Your custom fields:
    # Changed max_length to 20 for more flexibility and added unique=True
    # Consider if blank=True or null=True is appropriate for your business logic.
    # If phone is required for registration, it should be blank=False, null=False.
    phone = models.CharField(max_length=20, unique=True, blank=True, null=True)
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    # You can add more custom fields here if needed

    def __str__(self):
        # Prefer to return a more descriptive unique identifier if possible
        return self.email if self.email else self.username

    class Meta:
        # You can add custom meta options here if needed for your User model
        pass

# The rest of your models remain unchanged and are good as they are:
class Currency(models.Model):
    code = models.CharField(max_length=3, unique=True)  # USD, NGN, GBP, EUR
    name = models.CharField(max_length=50)
    symbol = models.CharField(max_length=5)  # $, ₦, £, €
    exchange_rate = models.DecimalField(max_digits=10, decimal_places=4, default=1.0)  # Rate to base currency (NGN)

    def __str__(self):
        return f"{self.name} ({self.code})"

class ExchangeRate(models.Model):
    from_currency = models.ForeignKey(Currency, on_delete=models.CASCADE, related_name='from_rates')
    to_currency = models.ForeignKey(Currency, on_delete=models.CASCADE, related_name='to_rates')
    rate = models.DecimalField(max_digits=12, decimal_places=6)
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('from_currency', 'to_currency')

    def __str__(self):
        return f"1 {self.from_currency.code} = {self.rate} {self.to_currency.code}"

class Wallet(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='wallets')
    currency = models.ForeignKey(Currency, on_delete=models.PROTECT)
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'currency')  # One wallet per currency per user

    def __str__(self):
        return f"{self.user.username}'s {self.currency.code} Wallet"

class Transaction(models.Model):
    TRANSACTION_TYPES = [
        ('deposit', 'Deposit'),
        ('withdrawal', 'Withdrawal'),
        ('card_sale', 'Gift Card Sale'),
        ('conversion', 'Currency Conversion'),
        ('bonus', 'Bonus'),
    ]

    wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE, related_name='transactions')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    description = models.CharField(max_length=255, blank=True)
    reference = models.CharField(max_length=100, unique=True)
    status = models.CharField(max_length=20, default='pending')  # pending, completed, failed
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.wallet.user.username} - {self.get_transaction_type_display()}: {self.amount}{self.wallet.currency.symbol}"

class WithdrawalRequest(models.Model):
    WITHDRAWAL_METHODS = [
        ('bank', 'Bank Transfer'),
        ('crypto', 'Cryptocurrency'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    method = models.CharField(max_length=10, choices=WITHDRAWAL_METHODS)
    details = models.JSONField()  # Store bank/crypto details
    verification_code = models.CharField(max_length=6)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.user.username} - {self.amount}{self.wallet.currency.symbol}"

class AutoConversionRule(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    from_currency = models.ForeignKey(Currency, on_delete=models.CASCADE, related_name='auto_from_rules')
    to_currency = models.ForeignKey(Currency, on_delete=models.CASCADE, related_name='auto_to_rules')
    threshold = models.DecimalField(max_digits=12, decimal_places=2)
    rate_override = models.DecimalField(max_digits=12, decimal_places=6, null=True, blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.user.username}: {self.from_currency.code}→{self.to_currency.code} (>={self.threshold})"

class AdminNotification(models.Model):
    NOTIFICATION_TYPES = [
        ('large_withdrawal', 'Large Withdrawal'),
        ('suspicious_activity', 'Suspicious Activity'),
    ]

    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    withdrawal_request = models.ForeignKey(WithdrawalRequest, on_delete=models.CASCADE, null=True, blank=True)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.get_notification_type_display()} - {self.created_at}"