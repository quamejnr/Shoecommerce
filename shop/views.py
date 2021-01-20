from django.shortcuts import render, get_object_or_404
from .models import Product, Order, OrderItem, BillingAddress, Payment
from django.views.generic import ListView, DetailView, View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.conf import settings
from django.http import JsonResponse
from django.contrib import messages
from django.shortcuts import redirect
from shop.forms import ShippingAddressForm
import json
import datetime
import stripe

stripe.api_key = settings.STRIPE_SECRET_KEY


class StoreListView(ListView):
    model = Product
    template_name = 'shop/store.html'


class ProductView(DetailView):
    model = Product
    template_name = 'shop/product.html'


class CartView(ListView):
    model = OrderItem
    template_name = 'shop/cart.html'

    def get_queryset(self):
        try:
            # Returning items in cart of a registered customer
            customer = self.request.user.customer
            order, created = Order.objects.get_or_create(customer=customer, complete=False)
            cart_items = order.orderitem_set.all()
            return cart_items
        except AttributeError:
            # Assigning cart items to an empty list if customer is not logged in.
            cart_items = []
            return cart_items

    def get_context_data(self, **kwargs):
        # Adding order to the context
        try:
            context = super().get_context_data(**kwargs)
            customer = self.request.user.customer
            order = get_object_or_404(Order, customer=customer, complete=False)
            context['order'] = order
            return context

        except AttributeError:
            # Data displayed when the user is not a registered customer.
            order = {
                'cart_items': 0,
                'cart_total': 0,
            }

            context['order'] = order
            return context


class CheckoutView(LoginRequiredMixin, View):

    def get(self, *args, **kwargs):
        form = ShippingAddressForm()

        customer = self.request.user.customer
        # Gets customer's order with items or creates one if none available
        order = get_object_or_404(Order, customer=customer, complete=False)
        items = order.orderitem_set.all()

        context = {
            'items': items,
            'order': order,
            'form': form,
        }

        return render(self.request, 'shop/checkout.html', context)

    def post(self, *args, **kwargs):
        # Checks if it is a POST request
        if self.request.method == 'POST':
            # Creates an instance of form with POST request
            form = ShippingAddressForm(self.request.POST)
            # print(self.request.POST)
            # Form is validated and saved
            try:

                payment_choices = {
                    'S': 'stripe',
                    'p': 'paypal',
                }

                order = Order.objects.get(customer=self.request.user.customer, complete=False)
                if form.is_valid():
                    # Using information from form provided by user to create a billing address object
                    street_address = form.cleaned_data.get('street_address')
                    apartment_address = form.cleaned_data.get('apartment_address')
                    city = form.cleaned_data.get('city')
                    country = form.cleaned_data.get('country')
                    payment_option = form.cleaned_data.get('payment_option')
                    billing_address = BillingAddress(
                        customer=self.request.user.customer,
                        country=country,
                        street_address=street_address,
                        city=city,
                        apartment_address=apartment_address,
                    )
                    billing_address.save()
                    order.billing_address = billing_address
                    order.save()
                    messages.success(self.request, "Form submitted")
                    return redirect('payment', payment_option=payment_choices[payment_option])
                messages.warning(self.request, 'Failed checkout. Make sure payment option has been chosen')
                return redirect('checkout')
            except ValueError:
                messages.warning(self.request, 'You do not have an active order')
                return redirect('checkout')


class PaymentView(LoginRequiredMixin, View):

    def get(self, *args, **kwargs):
        customer = self.request.user.customer
        order = get_object_or_404(Order, customer=customer, complete=False)
        items = order.orderitem_set.all()

        context = {
            'items': items,
            'order': order,
        }

        return render(self.request, 'shop/payment.html', context)

    def post(self, *args, **kwargs):
        order = Order.objects.get(customer=self.request.user.customer, complete=False)
        amount = int(order.cart_total() * 100)   # Multiply by 100 because stripe amount is in cents
        token = self.request.POST.get('stripeToken')
        order_items = order.orderitem_set.all()

        try:
            # Creates a stripe charge
            charge = stripe.Charge.create(
                amount=amount,
                currency="usd",
                source=token,
            )

            # Creating a payment
            payment = Payment()
            payment.charge_id = charge['id']
            payment.customer = self.request.user.customer
            payment.amount = order.cart_total()
            payment.save()

            # Creating a transaction id
            time = datetime.datetime.now()
            year = time.strftime('%Y')
            month = time.strftime('%m')
            transaction_id = f'{year}{month}{order.id}'

            # Changing the status of the order after completion
            order.payment = payment
            order.transaction_id = transaction_id
            order.complete = True
            order.save()

            # Changing product quantity after transaction
            for order_item in order_items:
                order_item.product.quantity -= order_item.quantity
                order_item.product.save()

            # Display message if payment is successful
            messages.info(self.request, 'Your payment was successful')
            return redirect('/')

        except stripe.error.CardError as e:
            # Since it's a decline, stripe.error.CardError will be caught
            messages.error(self.request, f'{e.user_message}')
            return redirect('/')

        except stripe.error.RateLimitError as e:
            # Too many requests made to the API too quickly
            messages.error(self.request, 'Rate Limit Error')
            return redirect('/')

        except stripe.error.InvalidRequestError as e:
            # Invalid parameters were supplied to Stripe's API
            messages.error(self.request, 'Invalid Parameters')
            return redirect('/')

        except stripe.error.AuthenticationError as e:
            # Authentication with Stripe's API failed
            # (maybe you changed API keys recently)
            messages.error(self.request, 'Not Authenticated')
            return redirect('/')

        except stripe.error.APIConnectionError as e:
            # Network communication with Stripe failed
            messages.error(self.request, 'Network Error')
            return redirect('/')

        except stripe.error.StripeError as e:
            # Display a very generic error to the user, and maybe send
            # yourself an email
            messages.error(self.request, 'Something went wrong, you were not charged. Please try again.')
            return redirect('/')

        except Exception as e:
            # Something else happened, completely unrelated to Stripe
            # Send an e-mail to myself.
            messages.error(self.request, 'An error occurred. We have ben notified')
            return redirect('/')


def update_item(request):
    # Loading and parsing the data received from UpdateItems Function in cart.js
    data = json.loads(request.body)
    product_id = data['productId']
    action = data["action"]

    customer = request.user.customer
    product = Product.objects.get(id=product_id)

    # Gets customer's order with items or creates one if none available
    order, created = Order.objects.get_or_create(customer=customer, complete=False)
    # Gets or creates an order item with order(if available) or create one
    item, created = OrderItem.objects.get_or_create(order=order, product=product)

    if action == "add":
        if item.quantity < product.quantity:
            item.quantity += 1
            messages.info(request, 'Item added to cart')
        else:
            messages.info(request, 'Out of stock')

    elif action == 'remove':
        item.quantity -= 1
        messages.info(request, 'Item removed from cart')

    elif action == 'clear':
        item.quantity = 0

    item.save()

    if item.quantity <= 0:
        item.delete()

    return JsonResponse("Updated cart", safe=False)



