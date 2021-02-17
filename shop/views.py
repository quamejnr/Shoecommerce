from django.shortcuts import render, get_object_or_404
from .models import Product, Order, OrderItem, Address, Payment, Coupon, Refund
from django.views.generic import ListView, DetailView, View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.http import JsonResponse
from django.contrib import messages
from django.shortcuts import redirect
from shop.forms import AddressForm, CouponForm, RefundForm
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
        # TODO: Rewrite code so order is only created when an item is added to cart

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


def is_valid_form(values):
    valid = True
    for field in values:
        if field == '':
            valid = False
    return valid


class CheckoutView(LoginRequiredMixin, View):

    def get(self, *args, **kwargs):
        form = AddressForm()
        coupon_form = CouponForm()
        customer = self.request.user.customer

        # Gets customer's order with items or creates one if none available
        order = get_object_or_404(Order, customer=customer, complete=False)
        items = order.orderitem_set.all()

        context = {
            'items': items,
            'order': order,
            'form': form,
            'c_form': coupon_form,
        }

        shipping_address = Address.objects.filter(
            customer=customer,
            address_type='S',
            default=True,
        )
        if shipping_address.exists():
            context.update({'default_shipping_address': shipping_address[0]})

        billing_address = Address.objects.filter(
            customer=customer,
            address_type='B',
            default=True,
        )
        if billing_address.exists():
            context.update({'default_billing_address': billing_address[0]})

        return render(self.request, 'shop/checkout.html', context)

    def post(self, *args, **kwargs):
        # Creates an instance of form with POST request
        form = AddressForm(self.request.POST or None)

        try:

            payment_choices = {
                'S': 'stripe',
                'p': 'paypal',
            }

            order = Order.objects.get(customer=self.request.user.customer, complete=False)
            if form.is_valid():

                # SHIPPING ADDRESS VIEW
                # Using default shipping address if available
                use_default_shipping = form.cleaned_data.get('use_default_shipping')

                if use_default_shipping:
                    print('Using default shipping address')
                    address_qs = Address.objects.filter(
                        customer=self.request.user.customer,
                        address_type='S',
                        default=True,
                    )
                    shipping_address = address_qs[0]
                    order.shipping_address = shipping_address
                    order.save()

                else:
                    # Using information from form provided by user to create a billing address object
                    shipping_address1 = form.cleaned_data.get('shipping_address1')
                    shipping_address2 = form.cleaned_data.get('shipping_address2')
                    shipping_city = form.cleaned_data.get('shipping_city')
                    shipping_zip = form.cleaned_data.get('shipping_zip')
                    shipping_country = form.cleaned_data.get('shipping_country')

                    if is_valid_form([shipping_address1, shipping_city, shipping_country]):
                        shipping_address = Address(
                            customer=self.request.user.customer,
                            country=shipping_country,
                            street_address=shipping_address1,
                            city=shipping_city,
                            zip_code=shipping_zip,
                            apartment_address=shipping_address2,
                            address_type='S',
                        )
                        shipping_address.save()

                        # Making current shipping address the default if chosen to be default
                        set_default_shipping = form.cleaned_data.get('set_default_shipping')
                        if set_default_shipping:
                            shipping_address.default = True
                            shipping_address.save()

                    else:
                        messages.info(self.request, 'Please fill in the required fields in the Shipping Address')

                # BILLING ADDRESS VIEW
                # Using default billing address if available
                same_billing_address = form.cleaned_data.get('same_billing_address')
                use_default_billing = form.cleaned_data.get('use_default_billing')

                if same_billing_address:
                    billing_address = shipping_address
                    billing_address.pk = None
                    billing_address.address_type = 'B'
                    billing_address.save()
                    order.billing_address = billing_address
                    order.save()

                elif use_default_billing:
                    address_qs = Address.objects.filter(
                        customer=self.request.user.customer,
                        address_type='B',
                        default=True,
                    )
                    billing_address = address_qs[0]
                    order.billing_address = billing_address
                    order.save()

                else:
                    # Using information from form provided by user to create a billing address object
                    billing_address1 = form.cleaned_data.get('billing_address1')
                    billing_address2 = form.cleaned_data.get('billing_address2')
                    billing_city = form.cleaned_data.get('billing_city')
                    billing_zip = form.cleaned_data.get('billing_zip')
                    billing_country = form.cleaned_data.get('billing_country')

                    if is_valid_form([billing_address1, billing_city, billing_country]):
                        billing_address = Address(
                            customer=self.request.user.customer,
                            country=billing_country,
                            street_address=billing_address1,
                            city=billing_city,
                            zip_code=billing_zip,
                            apartment_address=billing_address2,
                            address_type='B',
                        )
                        billing_address.save()

                        # Making current billing address the default if chosen to be default
                        set_default_billing = form.cleaned_data.get('set_default_billing')
                        if set_default_billing:
                            billing_address.default = True
                            billing_address.save()

                    else:
                        messages.info(self.request, 'Please fill in the required fields in Billing Address')
                        return redirect('checkout')

                payment_option = form.cleaned_data.get('payment_option')
                messages.success(self.request, "Form submitted")
                return redirect('payment', payment_option=payment_choices[payment_option])
            messages.warning(self.request, 'Failed checkout. Make sure payment option has been chosen')
            return redirect('checkout')
        except ValueError:
            messages.warning(self.request, 'You do not have an active order')
            return redirect('checkout')


class AddCouponView(View):

    def post(self, *args, **kwargs):
        form = CouponForm(self.request.POST)
        if form.is_valid():
            try:
                order = Order.objects.get(customer=self.request.user.customer, complete=False)
            except ObjectDoesNotExist:
                messages.info(self.request, "You do not have an active order")
                return redirect('checkout')
            try:
                code = form.cleaned_data.get('code')
                coupon = Coupon.objects.get(code=code)

                # check if user has already used coupon before
                # then add to order if the customer hasn't
                customer = self.request.user.customer
                user_coupons = customer.coupons.all()
                if coupon in user_coupons:
                    messages.warning(self.request, "This coupon has already been used")
                    return redirect('checkout')
                else:
                    order.coupon = coupon
                    order.save()
                    messages.success(self.request, 'Successfully added coupon')
                    return redirect('checkout')
            except ObjectDoesNotExist:
                messages.warning(self.request, 'This coupon does not exist')
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

            # Associating coupon with customer so it can't be used by same customer again
            customer = self.request.user.customer
            customer.coupons.add(order.coupon)
            customer.save()

            # Changing product quantity after transaction
            for order_item in order_items:
                order_item.product.quantity -= order_item.quantity
                order_item.product.save()

            # Display message if payment is successful
            messages.info(self.request, 'Your payment was successful')
            return redirect('checkout')

        except stripe.error.CardError as e:
            # Since it's a decline, stripe.error.CardError will be caught
            messages.error(self.request, f'{e.user_message}')
            return redirect('checkout')

        except stripe.error.RateLimitError as e:
            # Too many requests made to the API too quickly
            messages.warning(self.request, 'Rate Limit Error')
            return redirect('checkout')

        except stripe.error.InvalidRequestError as e:
            # Invalid parameters were supplied to Stripe's API
            messages.warning(self.request, 'Invalid Parameters')
            return redirect('checkout')

        except stripe.error.AuthenticationError as e:
            # Authentication with Stripe's API failed
            # (maybe you changed API keys recently)
            messages.warning(self.request, 'Not Authenticated')
            return redirect('checkout')

        except stripe.error.APIConnectionError as e:
            # Network communication with Stripe failed
            messages.warning(self.request, 'Network Error')
            return redirect('checkout')

        except stripe.error.StripeError as e:
            # Display a very generic error to the user, and maybe send
            # yourself an email
            messages.warning(self.request, 'Something went wrong, you were not charged. Please try again.')
            return redirect('checkout')

        except Exception as e:
            # Something else happened, completely unrelated to Stripe
            # Send an e-mail to myself.
            messages.warning(self.request, 'An error occurred. We have ben notified')
            return redirect('checkout')


class RefundView(View):
    def get(self, *args, **kwargs):
        form = RefundForm()
        context = {
            'form': form
        }

        return render(self.request, 'shop/refund_request.html', context)

    def post(self, *args, **kwargs):
        form = RefundForm(self.request.POST)
        if form.is_valid():
            order_id = form.cleaned_data.get('order_id')
            message = form.cleaned_data.get('message')
            email = form.cleaned_data.get('email')
            try:
                # Checks if order exists
                order = Order.objects.get(transaction_id=order_id, complete=True)

                # Edit the order
                order.refund_requested = True
                order.save()

                # Save refund
                refund = Refund()
                refund.order = order
                refund.message = message
                refund.email = email
                refund.save()
                messages.success(self.request, 'Your request has been sent')
                return redirect('refund-request')
            except ObjectDoesNotExist:
                messages.warning(self.request, "This order does not exist")
                return redirect('refund-request')


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
            messages.warning(request, 'Out of stock')

    elif action == 'remove':
        item.quantity -= 1
        messages.info(request, 'Item removed from cart')

    elif action == 'clear':
        item.quantity = 0

    item.save()

    if item.quantity <= 0:
        item.delete()

    return JsonResponse("Updated cart", safe=False)





