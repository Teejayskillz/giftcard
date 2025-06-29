# cards/forms.py
from django import forms
from .models import GiftCard, CardSubmission, Country
from django.core.exceptions import ValidationError # Import ValidationError
from decimal import Decimal, InvalidOperation # Import Decimal and InvalidOperation

class CardSubmissionForm(forms.ModelForm):
    country = forms.ModelChoiceField(
        queryset=Country.objects.none(),
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'id_country'})
    )
    
    class Meta:
        model = CardSubmission
        fields = ['card', 'country', 'card_type', 'card_value', 'card_number', 'card_image']
        # Add widget attributes for better styling and placeholders
        widgets = {
            'card': forms.Select(attrs={'class': 'form-select'}),
            'card_type': forms.Select(attrs={'class': 'form-select'}),
            'card_value': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Enter card value (e.g., 100.00)'}),
            'card_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter card number (if applicable)'}),
            'card_image': forms.FileInput(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['card'].queryset = GiftCard.objects.filter(active=True)
        
        # Populate country dropdown based on card selection, either from POST data or instance
        if 'card' in self.data:
            try:
                card_id = int(self.data.get('card'))
                card = GiftCard.objects.get(id=card_id)
                self.fields['country'].queryset = card.countries.all()
            except (ValueError, GiftCard.DoesNotExist):
                # If card_id is invalid or card does not exist, keep queryset empty
                self.fields['country'].queryset = Country.objects.none() 
        elif self.instance.pk:
            # For existing instances, populate countries based on the instance's card
            if self.instance.card: # Check if instance.card exists
                self.fields['country'].queryset = self.instance.card.countries.all()
            else:
                self.fields['country'].queryset = Country.objects.none() # Fallback

        # You might want to initialize 'country' if it's already set on the instance
        if self.instance.pk and self.instance.country:
             self.fields['country'].initial = self.instance.country


    # NEW: Clean method for card_value
    def clean_card_value(self):
        card_value = self.cleaned_data.get('card_value') # This is already a DecimalField from the model
        
        # Ensure it's not None (should be handled by required=True by default for DecimalField)
        if card_value is None:
            raise ValidationError("This field is required.")

        try:
            # Convert to Decimal for validation if it somehow wasn't already (though ModelForm usually does this for DecimalFields)
            # The DecimalField on the model handles the initial conversion from string to Decimal.
            # This clean method primarily validates the *value* of the Decimal.
            decimal_value = card_value # card_value is already a Decimal here thanks to DecimalField
            
            if decimal_value <= Decimal('0'):
                raise ValidationError("Value must be greater than 0.")
            
            return decimal_value
        except InvalidOperation:
            # This might catch cases where the DecimalField conversion itself failed,
            # though Django's DecimalField usually handles this before clean_field is called.
            raise ValidationError("Enter a valid number.")