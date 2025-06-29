# cards/views.py
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .forms import CardSubmissionForm
from .models import GiftCardRate, CardSubmission, GiftCard # Ensure GiftCard is imported
from django.http import JsonResponse
from django.core.exceptions import ObjectDoesNotExist
from django.contrib import messages
from decimal import Decimal, InvalidOperation # Import Decimal and InvalidOperation

# NEW IMPORTS for database expressions
from django.db.models import F, ExpressionWrapper, DecimalField


# Helper function to get the annotated rate table
# This function will be used in both GET and POST branches of submit_card
def get_annotated_rate_table():
    return GiftCardRate.objects.annotate(
        # Calculate example_offer for the table directly in the queryset
        example_offer=ExpressionWrapper(
            F('min_value') * F('rate_per_unit'),
            output_field=DecimalField(max_digits=10, decimal_places=2) # Ensure precision
        )
    ).all()


# --- View for submitting a gift card ---
@login_required
def submit_card(request):
    if request.method == 'POST':
        form = CardSubmissionForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                submission = form.save(commit=False)
                submission.user = request.user
                
                # NEW LOGIC: Calculate offer amount and currency here before saving
                rate = GiftCardRate.objects.get(
                    card=submission.card,
                    country=submission.country,
                    card_type=submission.card_type,
                    min_value__lte=submission.card_value,
                    max_value__gte=submission.card_value
                )
                submission.offer_amount = submission.card_value * rate.rate_per_unit
                submission.currency = rate.country.currency # Set the currency from the rate's country
                
                submission.save() # Now save the instance with calculated offer and currency
                messages.success(request, "Gift card submitted successfully! Awaiting review.")
                return redirect('cards:submission_success')
                
            except GiftCardRate.DoesNotExist:
                # Add a form error if no rate is found
                messages.error(request, "No specific rate found for this card, country, format, and value combination. Please check your inputs.")
                # Important: Re-render the form with errors and the annotated rate table
                return render(request, 'cards/submit.html', {
                    'form': form,
                    'rate_table': get_annotated_rate_table(), # Use the helper function
                })
            except Exception as e:
                # Catch any other unexpected errors during saving or calculation
                messages.error(request, f"An unexpected error occurred during submission: {str(e)}")
                # Re-render the form with errors and the annotated rate table
                return render(request, 'cards/submit.html', {
                    'form': form,
                    'rate_table': get_annotated_rate_table(), # Use the helper function
                })
        else:
            # Form is not valid (e.g., validation errors from forms.py or model's clean method)
            messages.error(request, "Please correct the errors below.")
            # Re-render the form with validation errors and the annotated rate table
            return render(request, 'cards/submit.html', {
                'form': form,
                'rate_table': get_annotated_rate_table(), # Use the helper function
            })
    else:
        # GET request: render empty form
        form = CardSubmissionForm()
    
    # Common context for GET and POST (if validation/submission fails)
    return render(request, 'cards/submit.html', {
        'form': form,
        'rate_table': get_annotated_rate_table(), # Use the helper function here too
    })
    
# --- API endpoint for fetching countries based on card type ---
def card_countries(request):
    card_id = request.GET.get('card_id')
    if not card_id:
        return JsonResponse({'error': 'card_id parameter is required'}, status=400)
    try:
        card = GiftCard.objects.get(id=card_id)
        countries = card.countries.all().values('id', 'name', 'code', 'currency__symbol')
        
        if not countries:
             return JsonResponse({'countries': []})
             
        return JsonResponse({'countries': list(countries)})
    except GiftCard.DoesNotExist:
        return JsonResponse({'error': 'Card not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': f'An unexpected error occurred: {str(e)}'}, status=500)


# --- API endpoint for calculating offer ---
def calculate_offer(request):
    try:
        card_id = request.GET.get('card')
        country_id = request.GET.get('country')
        card_type = request.GET.get('type')
        card_value_str = request.GET.get('value')
        
        if not all([card_id, country_id, card_type, card_value_str]):
            return JsonResponse({
                'status': 'missing_input',
                'message': 'Select card, country, format, and enter a valid value to get an offer.'
            })
            
        try:
            card_value = Decimal(card_value_str)
        except (ValueError, InvalidOperation):
            return JsonResponse({
                'status': 'invalid_value',
                'message': 'Please enter a valid numeric value for the card.'
            })
            
        if card_value <= Decimal('0'):
            return JsonResponse({
                'status': 'invalid_value',
                'message': 'Card value must be greater than 0.'
            })
            
        rate = GiftCardRate.objects.get(
            card_id=card_id,
            country_id=country_id,
            card_type=card_type,
            min_value__lte=card_value,
            max_value__gte=card_value
        )
        
        offer_amount = card_value * rate.rate_per_unit 
        
        return JsonResponse({
            'status': 'success',
            'offer': float(offer_amount),
            'rate': float(rate.rate_per_unit),
            'currency_code': rate.country.currency.code,
            'currency_symbol': rate.country.currency.symbol,
            'country_code': rate.country.code,
            'card_name': rate.card.name,
            'card_type': rate.get_card_type_display(),
            'card_value': float(card_value)
        })
            
    except ObjectDoesNotExist:
        return JsonResponse({
            'status': 'no_rate',
            'message': 'No specific rate found for this card, country, format, and value combination.'
        })
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': f'An unexpected server error occurred: {str(e)}'
        }, status=500)


# --- User Dashboard View ---
@login_required
def dashboard(request):
    submissions = CardSubmission.objects.filter(user=request.user).order_by('-date_submitted')
    balance = getattr(request.user, 'balance', Decimal('0.00')) 
    
    return render(request, 'cards/dashboard.html', {
        'submissions': submissions,
        'balance': balance,
    })

# --- Withdrawal Request View ---
@login_required
def withdraw_funds(request):
    if request.method == 'POST':
        try:
            amount_str = request.POST.get('amount', '0')
            amount = Decimal(amount_str)
        except (ValueError, InvalidOperation):
            messages.error(request, "Invalid withdrawal amount provided.")
            return render(request, 'cards/withdraw.html', {'error': 'Invalid withdrawal amount.'})
            
        user_balance = getattr(request.user, 'balance', Decimal('0.00')) 

        if Decimal('0') < amount <= user_balance:
            messages.info(request, "Withdrawal logic is a placeholder. Implement 'WithdrawalRequest' model and balance update.")
            return redirect('cards:dashboard')
        else:
            messages.error(request, "Invalid withdrawal amount or insufficient balance.")
            return render(request, 'cards/withdraw.html', {'error': 'Invalid amount or insufficient balance.'})
    
    return render(request, 'cards/withdraw.html')

@login_required 
def submission_success(request):
    latest_submission = CardSubmission.objects.filter(user=request.user).order_by('-date_submitted').first()
    
    return render(request, 'cards/submission_success.html', {
        'submission': latest_submission
    })