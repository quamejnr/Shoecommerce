from django import template
from shop.models import Order

register = template.Library()


@register.filter
def cart_quantity(user):
    # Returns the total quantity of products in cart.
    if user.is_authenticated:
        order_qs = Order.objects.filter(customer=user.customer, complete=False)
        if order_qs.exists():
            order = order_qs[0]
            return sum([item.quantity for item in order.orderitem_set.all()])
    return 0
