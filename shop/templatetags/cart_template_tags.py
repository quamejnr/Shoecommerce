from django import template
from shop.models import Order

register = template.Library()


@register.filter
def cart_quantity(user):
    # Returns the total quantity of products in cart.
    if user.is_authenticated:
        order = Order.objects.get(customer=user.customer)
        total = sum([item.quantity for item in order.orderitem_set.all()])
        return total
    return 0
