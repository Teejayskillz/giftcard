# cards/admin.py
from django.contrib import admin
from .models import Currency, Country, GiftCard, GiftCardRate, CardSubmission
from import_export import resources
from import_export.admin import ImportExportModelAdmin


# Resource for importing/exporting GiftCardRate data
class GiftCardRateResource(resources.ModelResource):
    class Meta:
        model = GiftCardRate
        skip_unchanged = True
        report_skipped = True
        # Fields to identify existing records during import to prevent duplicates
        import_id_fields = ('card', 'country', 'min_value', 'max_value', 'card_type')

# Admin configuration for GiftCardRate
@admin.register(GiftCardRate)
class GiftCardRateAdmin(ImportExportModelAdmin):
    resource_class = GiftCardRateResource
    # Display these fields in the list view
    list_display = ['card', 'country', 'card_type', 'min_value', 'max_value', 'rate_per_unit']
    # Add filters to the sidebar
    list_filter = ['card', 'country', 'card_type']

# Inline administration for GiftCardRate to be used within GiftCard admin
class GiftCardRateInline(admin.TabularInline):
    model = GiftCardRate
    extra = 1  # Number of empty forms to display

# Admin configuration for GiftCard
@admin.register(GiftCard)
class GiftCardAdmin(admin.ModelAdmin):
    # Display these fields in the list view
    list_display = ['name', 'active']
    # Include GiftCardRate inline forms
    inlines = [GiftCardRateInline]

# Admin configuration for CardSubmission
@admin.register(CardSubmission)
class CardSubmissionAdmin(admin.ModelAdmin):
    # Display these fields in the list view
    list_display = ['user', 'card', 'card_value', 'offer_amount', 'status']
    # Add filters to the sidebar
    list_filter = ['status', 'card']
    # Enable search functionality for these fields
    search_fields = ['user__username', 'card_number']

# Admin configuration for Currency
@admin.register(Currency)
class CurrencyAdmin(admin.ModelAdmin):
    # Display these fields in the list view
    list_display = ['code', 'name', 'symbol']

# Admin configuration for Country
@admin.register(Country)
class CountryAdmin(admin.ModelAdmin):
    # Display these fields in the list view
    list_display = ['name', 'code', 'currency']
    # Add filters to the sidebar
    list_filter = ['currency']