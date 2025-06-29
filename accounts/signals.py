# accounts/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Transaction, AutoConversionRule, WithdrawalRequest, AdminNotification
from .utils import convert_currency  # Make sure convert_currency is defined in utils.py
from django.conf import settings

@receiver(post_save, sender=Transaction)
def auto_convert_currencies(sender, instance, created, **kwargs):
    if created and instance.transaction_type == 'card_sale':
        wallet = instance.wallet
        rules = AutoConversionRule.objects.filter(
            from_currency=wallet.currency,
            is_active=True,
            user=wallet.user
        )
        
        for rule in rules:
            if wallet.balance >= rule.threshold:
                convert_currency(
                    user=wallet.user,
                    from_currency_code=rule.from_currency.code,
                    to_currency_code=rule.to_currency.code,
                    amount=wallet.balance,
                    rate_override=rule.rate_override
                )


@receiver(post_save, sender=WithdrawalRequest)
def check_large_withdrawal(sender, instance, created, **kwargs):
    if created:
        large_withdrawal_threshold = getattr(settings, 'LARGE_WITHDRAWAL_THRESHOLD', 500000)  # 500,000 NGN default
        
        if instance.amount >= large_withdrawal_threshold:
            AdminNotification.objects.create(
                notification_type='large_withdrawal',
                withdrawal_request=instance,
                message=f"Large withdrawal request of {instance.amount}{instance.wallet.currency.symbol} by {instance.user.username}"
            )                