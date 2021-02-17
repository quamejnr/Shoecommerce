from django.contrib import admin
from .models import Customer, Product, OrderItem, Order, Address, Payment, Coupon, Refund


def refund_accepted(request, modeladmin, queryset):
    queryset.update(refund_requested=False, refund_granted=True)


refund_accepted.short_description = 'Update orders to refund granted'


def update_order_sent(request, modeladmin, queryset):
    queryset.update(order_sent=True)


update_order_sent.short_description = 'Update orders to order sent'


class OrderAdmin(admin.ModelAdmin):
    list_display = ['customer', 'transaction_id', 'complete', 'order_sent', 'order_received',
                    'refund_requested', 'refund_granted']
    list_filter = ['complete', 'order_sent', 'order_received', 'refund_requested', 'refund_granted']
    list_display_links = ['customer', 'transaction_id']
    search_fields = ['customer__name', 'transaction_id']
    actions = [refund_accepted, update_order_sent]


class AddressAdmin(admin.ModelAdmin):
    list_display = ['customer', 'country', 'city', 'street_address', 'apartment_address', 'address_type', 'default']
    list_filter = ['city', 'street_address', 'address_type']
    search_fields = ['city', 'street_address', 'address_type', 'zip_code']


class PaymentAdmin(admin.ModelAdmin):
    list_display = ['customer', 'amount', 'charge_id']


class OrderItemAdmin(admin.ModelAdmin):
    list_display = ['product', 'quantity', 'order']


class RefundAdmin(admin.ModelAdmin):
    list_display = ['order', 'refund_accepted']


admin.site.register(Customer)
admin.site.register(Product)
admin.site.register(OrderItem, OrderItemAdmin)
admin.site.register(Order, OrderAdmin)
admin.site.register(Address, AddressAdmin)
admin.site.register(Payment, PaymentAdmin)
admin.site.register(Coupon)
admin.site.register(Refund, RefundAdmin)
