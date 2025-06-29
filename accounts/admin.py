# accounts/admin.py
from django.contrib import admin
from django.utils import timezone
from .models import Currency, Wallet, Transaction, WithdrawalRequest
from .utils import debit_wallet  # Make sure debit_wallet is defined in utils.py

@admin.register(Currency)
class CurrencyAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'symbol', 'exchange_rate']
    list_editable = ['exchange_rate']

@admin.register(Wallet)
class WalletAdmin(admin.ModelAdmin):
    list_display = ['user', 'currency', 'balance']
    list_filter = ['currency']
    search_fields = ['user__username']

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ['wallet', 'amount', 'transaction_type', 'status', 'created_at']
    list_filter = ['transaction_type', 'status']
    search_fields = ['reference', 'wallet__user__username']
    
    

@admin.register(WithdrawalRequest)
class WithdrawalRequestAdmin(admin.ModelAdmin):
    list_display = ['user', 'wallet', 'amount', 'method', 'is_verified', 'created_at']
    list_filter = ['method', 'is_verified']
    actions = ['process_withdrawals']

    def process_withdrawals(self, request, queryset):
        for withdrawal in queryset.filter(is_verified=True):
            # Mark as completed (actual bank transfer would be manual)
            withdrawal.completed_at = timezone.now()
            withdrawal.save()
            
            # Create debit transaction
            debit_wallet(
                withdrawal.user,
                withdrawal.amount,
                withdrawal.wallet.currency.code,
                transaction_type='withdrawal',
                description=f"{withdrawal.method} withdrawal"
            )
            
        self.message_user(request, f"Processed {queryset.count()} withdrawals")
    process_withdrawals.short_description = "Process selected withdrawals"    