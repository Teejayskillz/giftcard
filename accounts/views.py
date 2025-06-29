# accounts/views.py
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from .models import Transaction, Wallet, WithdrawalRequest, AutoConversionRule, Currency
from .forms import AutoConversionRuleForm, CustomUserCreationForm
from django.contrib import messages
from .utils import convert_currency
from cards.models import GiftCard 
 # accounts/views.py
from django.core.mail import send_mail
import random


def home(request):
    popular_cards = GiftCard.objects.filter(active=True).order_by('-id')[:8]
    return render(request, 'home.html', {'popular_cards': popular_cards})

# accounts/views.py

from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import CustomUserCreationForm
# from .models import User # Ensure User is imported if you use it directly in views

def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Optional: Log the user in immediately after registration
            # from django.contrib.auth import login # Import here or at the top
            # login(request, user)

            messages.success(request, "Account created successfully! You can now log in.")
            return redirect('login') # Redirect to the login page
        else:
            # Form is not valid, display errors
            messages.error(request, "Please correct the errors below.")
            
            # --- START: DEBUGGING PRINTS ADDED HERE ---
            print("\n--- FORM ERRORS (from accounts/views.py) ---")
            print("Field errors:", form.errors) # This will show errors per field
            print("Non-field errors:", form.non_field_errors) # This will show general errors (e.g., passwords don't match)
            print("-------------------------------------------\n")
            # --- END: DEBUGGING PRINTS ADDED HERE ---

            # The invalid form (with errors) is passed back to the template
            # so the errors can be rendered next to the fields.
            return render(request, 'registration/register.html', {'form': form})
    else:
        # This is a GET request, so we create an empty form to display
        form = CustomUserCreationForm()

    return render(request, 'registration/register.html', {'form': form})
@login_required
def request_withdrawal(request):
    if request.method == 'POST':
        wallet_id = request.POST.get('wallet')
        amount = float(request.POST.get('amount'))
        method = request.POST.get('method')
        details = {
            'bank_name': request.POST.get('bank_name'),
            'account_number': request.POST.get('account_number'),
            # ... other details
        }
        
        wallet = get_object_or_404(Wallet, id=wallet_id, user=request.user)
        
        if wallet.balance < amount:
            messages.error(request, "Insufficient balance")
            return redirect('wallet_dashboard')
        
        # Generate verification code
        code = ''.join(random.choices('0123456789', k=6))
        
        withdrawal = WithdrawalRequest.objects.create(
            user=request.user,
            wallet=wallet,
            amount=amount,
            method=method,
            details=details,
            verification_code=code
        )
        
        # Send verification email
        send_mail(
            'Withdrawal Verification Code',
            f'Your verification code is: {code}',
            'noreply@yourdomain.com',
            [request.user.email],
            fail_silently=False,
        )
        
        messages.success(request, "Verification code sent to your email")
        return redirect('verify_withdrawal', withdrawal.id)
    
    wallets = request.user.wallets.filter(balance__gt=0)
    return render(request, 'accounts/request_withdrawal.html', {'wallets': wallets})

@login_required
def verify_withdrawal(request, withdrawal_id):
    withdrawal = get_object_or_404(WithdrawalRequest, id=withdrawal_id, user=request.user)
    
    if request.method == 'POST':
        code = request.POST.get('code')
        
        if code == withdrawal.verification_code:
            withdrawal.is_verified = True
            withdrawal.save()
            
            # Process withdrawal (you'll manually complete this in admin)
            messages.success(request, "Withdrawal verified and pending processing")
            return redirect('wallet_dashboard')
        else:
            messages.error(request, "Invalid verification code")
    
    return render(request, 'accounts/verify_withdrawal.html', {'withdrawal': withdrawal})

@login_required
def convert_currency_view(request):
    if request.method == 'POST':
        try:
            from_currency = request.POST.get('from_currency')
            to_currency = request.POST.get('to_currency')
            amount = float(request.POST.get('amount'))
            
            converted_amount = convert_currency(
                request.user,
                from_currency,
                to_currency,
                amount
            )
            
            messages.success(
                request,
                f"Converted {amount}{from_currency} to {converted_amount:.2f}{to_currency}"
            )
        except Exception as e:
            messages.error(request, str(e))
        
        return redirect('wallet_dashboard')
    
    wallets = request.user.wallets.filter(balance__gt=0)
    return render(request, 'accounts/convert_currency.html', {'wallets': wallets})


@login_required
def wallet_dashboard(request):
    """
    Displays the user's wallet dashboard, including wallet balances
    and recent transactions. Requires the user to be logged in.
    """
    # Get all wallets belonging to the current user,
    # and prefetch related currency for efficiency.
    wallets = request.user.wallets.select_related('currency').all()

    # Get recent transactions for the user's wallets, ordered by creation date,
    # and limit to the last 10.
    recent_transactions = Transaction.objects.filter(
        wallet__user=request.user
    ).order_by('-created_at')[:10]

    # Add converted balance to each wallet
    for wallet in wallets:
        # Check if the currency code is not 'NGN' (Nigerian Naira, assuming this is your base currency)
        # If it's different, calculate a converted balance based on the exchange rate.
        if wallet.currency.code != 'NGN':
            wallet.converted_balance = wallet.balance * wallet.currency.exchange_rate
        else:
            # If it's NGN, the converted balance is just the balance itself
            wallet.converted_balance = wallet.balance

    # Add the absolute amount to each transaction object
    # This prepares the data for display in the template where you needed 'abs'.
    for tx in recent_transactions:
        tx.abs_amount = abs(tx.amount)

    context = {
        'wallets': wallets,
        'recent_transactions': recent_transactions
    }
    return render(request, 'accounts/dashboard.html', context)

@login_required
def transaction_history(request):
    # Filter transactions for the current logged-in user, ordered by creation date
    transactions = Transaction.objects.filter(
        wallet__user=request.user
    ).order_by('-created_at')

    # Add the absolute amount to each transaction object
    # This loop iterates through the queryset and adds a new attribute 'abs_amount'
    # to each transaction object before it's passed to the template.
    for tx in transactions:
        tx.abs_amount = abs(tx.amount)

    context = {
        'transactions': transactions,
        # You can add other context variables here if needed, e.g., 'page_title': 'Transaction History'
    }
    return render(request, 'accounts/transactions.html', context)

@login_required
def conversion_rules(request):
    rules = AutoConversionRule.objects.filter(user=request.user)
    currencies = Currency.objects.all()
    return render(request, 'accounts/conversion_rules.html', {
        'rules': rules,
        'currencies': currencies
    })

@login_required
def create_conversion_rule(request):
    if request.method == 'POST':
        form = AutoConversionRuleForm(request.POST, user=request.user)
        if form.is_valid():
            rule = form.save(commit=False)
            rule.user = request.user
            rule.save()
            messages.success(request, 'Auto-conversion rule created successfully')
            return redirect('conversion_rules')
        messages.error(request, 'Error creating rule')
    return redirect('accounts:conversion_rules')

@login_required
def delete_conversion_rule(request, pk):
    rule = get_object_or_404(AutoConversionRule, pk=pk, user=request.user)
    if request.method == 'POST':
        rule.delete()
        messages.success(request, 'Rule deleted successfully')
    return redirect('conversion_rules')

@login_required
def profile(request):
    if request.method == 'POST':
        # Handle profile updates
        pass
    
    return render(request, 'accounts/profile.html')
    