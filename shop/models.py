from django.db import models
from PIL import Image
from autoslug import AutoSlugField
from django.contrib.auth.models import User
from django.shortcuts import reverse
from django_countries.fields import CountryField


ADDRESS_CHOICES = (
    ('B', 'Billing'),
    ('S', "Shipping"),
)


class Product(models.Model):
    name = models.CharField(max_length=200)
    brand = models.CharField(max_length=100, null=True, blank=True)
    price = models.FloatField()
    quantity = models.IntegerField(default=1)
    discount_price = models.FloatField(null=True, blank=True)
    digital = models.BooleanField(default=False)
    image = models.ImageField(null=True)
    description = models.TextField(max_length=200, null=True, blank=True)
    slug = AutoSlugField(populate_from='name', unique=True)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('product', kwargs={'slug': self.slug})

    def save(self, *args, **kwargs):
        # resizing images before saving
        super().save(*args, **kwargs)

        with Image.open(self.image.path) as img:
            if (img.height or img.width) > 1000:
                output_size = (800, 800)
                img.thumbnail(output_size)
                img.save(self.image.path)


class Coupon(models.Model):
    code = models.CharField(max_length=20)
    amount = models.FloatField()

    def __str__(self):
        return self.code


class Customer(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    coupons = models.ManyToManyField(Coupon, blank=True)

    def __str__(self):
        return self.user.username


class Address(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True, blank=True)
    country = CountryField(blank_label='select country', null=True, multiple=False)
    street_address = models.CharField(max_length=200, null=True)
    apartment_address = models.CharField(max_length=200, null=True, blank=True)
    city = models.CharField(max_length=200, null=True)
    zip_code = models.CharField(max_length=20, null=True, blank=True)
    address_type = models.CharField(max_length=1, choices=ADDRESS_CHOICES)
    default = models.BooleanField(default=False)
    date_added = models.DateTimeField(auto_now_add=True)

    @property
    def address(self):
        return f'{self.country}, {self.city}, {self.street_address}'

    def __str__(self):
        return self.address

    class Meta:
        verbose_name_plural = 'Addresses'


class Payment(models.Model):
    charge_id = models.CharField(max_length=50)
    customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, blank=True, null=True)
    amount = models.FloatField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Ghc{self.amount:.2f}'


class Order(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True, blank=True)
    date_ordered = models.DateTimeField(auto_now_add=True)
    complete = models.BooleanField(default=False, null=True, blank=False)
    transaction_id = models.CharField(max_length=200, null=True)
    billing_address = models.ForeignKey(Address, related_name='billing_address', on_delete=models.SET_NULL,
                                        null=True, blank=True)
    shipping_address = models.ForeignKey(Address, related_name='shipping_address', on_delete=models.SET_NULL,
                                         null=True, blank=True)
    payment = models.ForeignKey(Payment, on_delete=models.SET_NULL, null=True, blank=True)
    coupon = models.ForeignKey(Coupon, on_delete=models.SET_NULL, null=True, blank=True)
    order_sent = models.BooleanField(default=False, null=True, blank=False)
    order_received = models.BooleanField(default=False, null=True, blank=False)
    refund_requested = models.BooleanField(default=False, null=True, blank=False)
    refund_granted = models.BooleanField(default=False, null=True, blank=False)

    def __str__(self):
        if self.transaction_id:
            return self.transaction_id
        else:
            return "N/A"

    def shipping(self):
        # Returns a boolean as to whether a product is digital or not
        # and has to be shipped.
        items = self.orderitem_set.all()
        for i in items:
            if not i.product.digital:
                return True
        return False

    def cart_total(self):
        # Returns the total amount of products in cart.
        try:
            total = sum([item.total() for item in self.orderitem_set.all()])
            total -= self.coupon.amount
            if total < 0:
                return 0
            return total
        except AttributeError:
            total = sum([item.total() for item in self.orderitem_set.all()])
            return total

    def cart_items(self):
        # Returns the total quantity of products in cart.
        total = sum([item.quantity for item in self.orderitem_set.all()])
        return total


class OrderItem(models.Model):
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, blank=True)
    quantity = models.IntegerField(default=0, null=True, blank=True)
    order = models.ForeignKey(Order, on_delete=models.CASCADE, null=True)
    date_added = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.product.name

    def total(self):
        # Returns the total price of the quantity of products in cart
        try:
            total = self.product.discount_price * self.quantity
        except TypeError:
            total = self.product.price * self.quantity
        return total


class Refund(models.Model):
    order = models.ForeignKey(Order, on_delete=models.SET_NULL, null=True, blank=True)
    message = models.TextField()
    email = models.EmailField()
    refund_accepted = models.BooleanField(default=False)

    def __str__(self):
        return self.order.transaction_id
