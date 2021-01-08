from django import forms
from django_countries.fields import CountryField


PAYMENT_CHOICES = (
    ('S', 'Stripe'),
    ('P', 'Paypal'),

)


class ShippingAddressForm(forms.Form):
    street_address = forms.CharField(widget=forms.TextInput(attrs={
        'placeholder': '6 Neem Ln'
    }))
    apartment_address = forms.CharField(required=False, widget=forms.TextInput(attrs={
        'placeholder': 'Hse No 64/5'
    }))

    city = forms.CharField(widget=forms.TextInput(attrs={
        'placeholder': 'Accra'
    }))

    country = CountryField(blank_label='select country').formfield()
    same_billing_address = forms.BooleanField(widget=forms.CheckboxInput, required=False)
    save_info = forms.BooleanField(widget=forms.CheckboxInput, required=False)
    payment_option = forms.ChoiceField(widget=forms.RadioSelect, choices=PAYMENT_CHOICES)
