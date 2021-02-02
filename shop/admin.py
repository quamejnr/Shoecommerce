from django.contrib import admin
from .models import Customer, Product, OrderItem, Order, BillingAddress, Payment, Coupon, Refund


class OrderAdmin(admin.ModelAdmin):
    list_display = ['customer', 'complete', 'order_sent', 'order_received',
                    'refund_requested', 'refund_granted']
    list_filter = ['complete', 'order_sent', 'order_received', 'refund_requested', 'refund_granted']
    search_fields = ['customer__name', 'transaction_id']


class BillingAddressAdmin(admin.ModelAdmin):
    list_display = ['customer', 'address', 'payment_option']


class PaymentAdmin(admin.ModelAdmin):
    list_display = ['customer', 'amount', 'charge_id']


class OrderItemAdmin(admin.ModelAdmin):
    list_display = ['product', 'quantity', 'order']


admin.site.register(Customer)
admin.site.register(Product)
admin.site.register(OrderItem, OrderItemAdmin)
admin.site.register(Order, OrderAdmin)
admin.site.register(BillingAddress, BillingAddressAdmin)
admin.site.register(Payment, PaymentAdmin)
admin.site.register(Coupon)
admin.site.register(Refund)
