from django import forms
from shop.models import ShippingAddress


class ShippingAddressForm(forms.ModelForm):

    class Meta:
        model = ShippingAddress
        fields = ['country', 'city', 'street_address']
