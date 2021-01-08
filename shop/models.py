from django.db import models
from PIL import Image
from autoslug import AutoSlugField
from django.contrib.auth.models import User
from django.shortcuts import reverse
from django_countries.fields import CountryField


class Product(models.Model):
    name = models.CharField(max_length=200)
    brand = models.CharField(max_length=100, null=True, blank=True)
    price = models.FloatField()
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


class Customer(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    name = models.CharField(max_length=200, null=True)

    # image = CloudinaryField('image')

    def __str__(self):
        return self.name


class BillingAddress(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True, blank=True)
    country = CountryField(blank_label='select country', null=True, multiple=False)
    street_address = models.CharField(max_length=200, null=False)
    apartment_address = models.CharField(max_length=200, null=False, blank=True)
    city = models.CharField(max_length=200, null=False)
    date_added = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'({self.customer}, {self.country}, {self.street_address}'


class Order(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True, blank=True)
    date_ordered = models.DateTimeField(auto_now_add=True)
    complete = models.BooleanField(default=False, null=True, blank=False)
    transaction_id = models.CharField(max_length=200, null=True)
    billing_address = models.ForeignKey(BillingAddress, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return self.transaction_id

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
        return f'Order:{self.order} - {self.product.name} ({self.quantity})'

    def total(self):
        # Returns the total price of the quantity of products in cart
        try:
            total = self.product.discount_price * self.quantity
        except TypeError:
            total = self.product.price * self.quantity
        return total




