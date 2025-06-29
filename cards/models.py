# cards/models.py
from django.db import models
from django.conf import settings
from decimal import Decimal # Import Decimal
from django.core.exceptions import ValidationError # Import ValidationError for clean method


class Currency(models.Model):
    code = models.CharField(max_length=3, unique=True)  # USD, GBP, EUR
    name = models.CharField(max_length=50)  # US Dollar, British Pound
    symbol = models.CharField(max_length=5)  # $, £, €
    
    def __str__(self):
        return f"{self.name} ({self.code})"


class Country(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=2)  # US, UK, DE
    currency = models.ForeignKey(Currency, on_delete=models.PROTECT)
    
    def __str__(self):
        return f"{self.name} ({self.code})"


class GiftCard(models.Model):
    name = models.CharField(max_length=100)
    logo = models.ImageField(upload_to='card_logos/')
    active = models.BooleanField(default=True)
    countries = models.ManyToManyField('Country', blank=True)
    
    def __str__(self):
        return self.name


class GiftCardRate(models.Model):
    CARD_TYPE_CHOICES = [
        ('physical', 'Physical Card'),
        ('ecode', 'E-code'),
    ]
    
    card = models.ForeignKey(GiftCard, on_delete=models.CASCADE, related_name='rates')
    country = models.ForeignKey(Country, on_delete=models.CASCADE)
    min_value = models.DecimalField(max_digits=10, decimal_places=2)
    max_value = models.DecimalField(max_digits=10, decimal_places=2)
    # UPDATED: Increased precision for rate_per_unit
    rate_per_unit = models.DecimalField(max_digits=10, decimal_places=4)  # Rate in Naira per 1 unit of foreign currency
    card_type = models.CharField(max_length=10, choices=CARD_TYPE_CHOICES, default='physical')
    
    class Meta:
        ordering = ['min_value']
        unique_together = ['card', 'country', 'min_value', 'max_value', 'card_type']
    
    def __str__(self):
        return f"{self.card.name} ({self.country.code} {self.get_card_type_display()}): {self.min_value}-{self.max_value}{self.country.currency.symbol} @ ₦{self.rate_per_unit}/{self.country.currency.code}"

    # NEW: Clean method for validation
    def clean(self):
        # Ensure min_value is less than max_value
        if self.min_value >= self.max_value:
            raise ValidationError("Min value must be less than max value.")
        # Optional: Add check for overlapping ranges if needed, but unique_together might cover some aspects.
        # This clean method will be called when ModelForm.is_valid() or Model.full_clean() is used.


class CardSubmission(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending Review'),
        ('approved', 'Approved - Pending Payment'),
        ('paid', 'Paid'),
        ('rejected', 'Rejected'),
    ]

    CARD_TYPE_CHOICES = [
        ('physical', 'Physical Card'),
        ('ecode', 'E-code'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    card = models.ForeignKey(GiftCard, on_delete=models.CASCADE)
    card_type = models.CharField(max_length=10, choices=CARD_TYPE_CHOICES)
    card_rate = models.ForeignKey(GiftCardRate, on_delete=models.SET_NULL, null=True, blank=True)
    card_value = models.DecimalField(max_digits=10, decimal_places=2)
    card_number = models.CharField(max_length=100)
    card_image = models.ImageField(upload_to='submissions/', blank=True, null=True)
    offer_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    date_submitted = models.DateTimeField(auto_now_add=True)
    date_processed = models.DateTimeField(null=True, blank=True)

    country = models.ForeignKey(Country, on_delete=models.PROTECT)
    currency = models.ForeignKey(Currency, on_delete=models.PROTECT, null=True, blank=True) # Added null=True, blank=True as it can be None if no rate found in save()

    # New field to link to the wallet transaction
    wallet_transaction = models.ForeignKey(
        'accounts.Transaction',  # Assuming your Transaction model is in the 'accounts' app
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    def save(self, *args, **kwargs):
        # Store original status to check for changes
        original_status = None
        if self.pk: # If object already exists
            original_status = CardSubmission.objects.get(pk=self.pk).status

        # Calculate offer amount if it's not already set
        if self.offer_amount is None: # Use `is None` for proper check
            rate = GiftCardRate.objects.filter(
                card=self.card,
                country=self.country,
                min_value__lte=self.card_value,
                max_value__gte=self.card_value,
                card_type=self.card_type
            ).first() # Use .first() to get one object or None
            
            if rate:
                self.card_rate = rate
                self.currency = rate.country.currency
                self.offer_amount = self.card_value * rate.rate_per_unit
            else:
                self.offer_amount = Decimal('0.00') # Set to Decimal 0.00
                self.currency = None # Set currency to None if no rate found
        
        super().save(*args, **kwargs)

        # Credit wallet when status changes to 'approved' and no transaction exists yet
        if self.status == 'approved' and original_status != 'approved' and not self.wallet_transaction:
            try:
                # IMPORTANT: You need to implement the 'credit_wallet' function in your 'accounts' app.
                # For example, in accounts/utils.py or accounts/services.py
                from accounts.utils import credit_wallet 

                transaction = credit_wallet(
                    user=self.user,
                    amount=self.offer_amount,
                    currency_code='NGN',  # Assuming payout is in Naira
                    transaction_type='card_sale',
                    description=f"{self.card.name} {self.get_card_type_display()} sale ({self.card_value} {self.currency.symbol if self.currency else 'N/A'})"
                )
                self.wallet_transaction = transaction
                self.save(update_fields=['wallet_transaction']) # Save again to update the wallet_transaction field
            except ImportError:
                print("Warning: 'credit_wallet' function not found. Wallet will not be credited.")
            except Exception as e:
                print(f"Error crediting wallet for card submission {self.pk}: {e}")

    def __str__(self):
        return f"{self.user.username}'s {self.card.name} {self.get_card_type_display()} ({self.card_value} {self.currency.code if self.currency else 'N/A'})"