from django.db import models
from django.contrib.auth.models import User
from django.contrib.postgres.fields import ArrayField
from phonenumber_field.modelfields import PhoneNumberField
from django.utils import timezone
from django.urls import reverse
from django.utils.text import slugify
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator, MaxValueValidator
import re


def validate_gst(value):
    gst_pattern = r"^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[0-9A-Z]{1}[Z]{1}[0-9A-Z]{1}$"
    if not re.match(gst_pattern, value):
        raise ValidationError(
            _("Invalid GST number. Please enter a valid GST number."),
            code="invalid_gst",
        )


class Location(models.Model):
    latitude = models.CharField(max_length=200)
    longitude = models.CharField(max_length=200)

    def __str__(self):
        return f"{self.latitude}, {self.longitude}"


class Customer(User):
    pic = models.ImageField(upload_to="profile_pic/", null=True, blank=True)
    gstNo = models.CharField(
        max_length=200, null=True, blank=True, validators=[validate_gst], unique=True
    )
    phone = PhoneNumberField()
    gender_option = [
        ("Male", "male"),
        ("Female", "female"),
    ]
    gender = models.CharField(
        max_length=50, choices=gender_option, null=True, blank=True
    )

    def __str__(self):
        return self.username

    @property
    def getShippingAddress(self):
        return self.shippingaddress_set.all()

    @property
    def getGST(self):
        return self.gstNo

    @property
    def is_wholeSaleUser(self):
        return bool(self.gstNo)

    class Meta:
        verbose_name = "Customer"
        verbose_name_plural = "Customers"


class ShippingAddress(models.Model):
    user = models.ForeignKey(
        Customer,
        on_delete=models.CASCADE,
        help_text="User who is going to receive the product",
    )
    name = models.CharField(max_length=200)
    phone = PhoneNumberField()
    pincode = models.CharField(max_length=200)
    locality = models.CharField(max_length=200)
    address = models.TextField()
    city = models.CharField(max_length=200)
    state = models.CharField(max_length=200)
    landmark = models.CharField(max_length=200, null=True, blank=True)
    alternate_phone = PhoneNumberField(null=True, blank=True)
    location = models.ForeignKey(
        Location, on_delete=models.CASCADE, null=True, blank=True
    )

    def __str__(self):
        return f"{self.name} - {self.phone} - {self.city} - {self.state}"

    class Meta:
        verbose_name = "Shipping Address"
        verbose_name_plural = "Shipping Addresses"


class Address(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='addresses')
    street = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    country = models.CharField(max_length=100)
    zip_code = models.CharField(max_length=20)
    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username}'s address in {self.city}, {self.country}"

    class Meta:
        verbose_name_plural = "Addresses"


class Category(models.Model):
    name = models.CharField(max_length=100)
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE, related_name='subcategories')
    slug = models.SlugField(max_length=255, unique=True, db_index=True)
    image = models.ImageField(upload_to="category_pic/", null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    @property
    def total_products(self) -> int:
        if hasattr(self, 'products'):
            return self.products.count()
        return 0

    class Meta:
        verbose_name_plural = "Categories"
        indexes = [
            models.Index(fields=['slug']),
        ]


class Color(models.Model):
    color = models.CharField(max_length=50)
    hexcode = models.CharField(max_length=50)

    def __str__(self):
        return self.color

    @property
    def total_products(self) -> int:
        if hasattr(self, 'products'):
            return self.products.count()
        return 0

    class Meta:
        verbose_name = "Color"
        verbose_name_plural = "Colors"


class Size(models.Model):
    size_opt = [
        ("XS", "Extra Small"),
        ("S", "Small"),
        ("M", "Medium"),
        ("L", "Large"),
        ("XL", "Extra Large"),
        ("XXL", "Extra Extra Large"),
    ]
    size = models.CharField(max_length=50, choices=size_opt)
    
    # Upper body measurements
    bust = models.FloatField(null=True, blank=True)  # Bust circumference (for women)
    chest = models.FloatField(null=True, blank=True)  # Chest circumference
    shoulder = models.FloatField(null=True, blank=True)  # Shoulder width
    top_length = models.FloatField(null=True, blank=True)  # Length of top
    sleeve_length = models.FloatField(null=True, blank=True)  # Length of sleeves
    cuff_circumference = models.FloatField(null=True, blank=True)  # Sleeve cuff circumference
    bicep_circumference = models.FloatField(null=True, blank=True)  # Bicep circumference
    
    # Lower body measurements
    hip = models.FloatField(null=True, blank=True)  # Hip circumference
    rise = models.FloatField(null=True, blank=True)  # Distance from waist to crotch
    waist = models.FloatField(null=True, blank=True)  # Waist circumference
    thigh = models.FloatField(null=True, blank=True)  # Thigh circumference
    pant_length = models.FloatField(null=True, blank=True)  # Full length of pants
    inseam_length = models.FloatField(null=True, blank=True)  # Inner leg length
    knee_circumference = models.FloatField(null=True, blank=True)  # Knee circumference
    ankle_circumference = models.FloatField(null=True, blank=True)  # Ankle circumference
    
    # Dresses/Full body measurements
    dress_length = models.FloatField(null=True, blank=True)  # Full length of the dress
    shoulder_to_hip = models.FloatField(null=True, blank=True)  # Length from shoulder to hip
    shoulder_to_knee = models.FloatField(null=True, blank=True)  # Length from shoulder to knee
    shoulder_to_waist = models.FloatField(null=True, blank=True)  # Length from shoulder to waist
    shoulder_to_ankle = models.FloatField(null=True, blank=True)  # Length from shoulder to ankle
    neck_circumference = models.FloatField(null=True, blank=True)  # Neck circumference

    def __str__(self):
        return f"{self.get_size_display()}"

    @property
    def total_products(self) -> int:
        if hasattr(self, 'products'):
            return self.products.count()
        return 0

    class Meta:
        verbose_name = "Size"
        verbose_name_plural = "Sizes"


class Product(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products')
    slug = models.SlugField(max_length=255, unique=True, db_index=True)
    brand = models.CharField(max_length=100, blank=True)
    stock = models.PositiveIntegerField(default=0)
    color = models.ForeignKey(Color, on_delete=models.CASCADE, null=True, blank=True)
    size = models.ForeignKey(Size, on_delete=models.CASCADE, null=True, blank=True)
    avail_sizes = models.ManyToManyField(Size, blank=True, related_name="products_sizes")
    market_price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    selling_price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    
    # Additional attributes
    rating = models.FloatField(default=0)
    buy_count = models.PositiveIntegerField(default=0)
    tags = ArrayField(models.CharField(max_length=200), blank=True, null=True, default=list)
    fabric = ArrayField(models.CharField(max_length=200), blank=True, null=True, default=list)
    gsm = models.FloatField(null=True, blank=True, help_text="Thickness of the material")
    product_type = models.CharField(max_length=50, blank=True, null=True)
    sleeve = models.CharField(max_length=50, blank=True, null=True)
    fit = models.CharField(max_length=50, blank=True, null=True)
    ideal_for = models.CharField(max_length=50, blank=True, null=True)
    net_weight = models.FloatField(null=True, blank=True, help_text="Net weight in grams")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} ({self.stock} in stock)"

    def get_absolute_url(self):
        return reverse("product_detail", kwargs={"slug": self.slug})

    @property
    def SKU(self):
        fabric_initials = "".join([f[0].upper() for f in self.fabric]) if self.fabric else ""
        return (
            f"{self.id}"
            f"{self.size.size[:1].upper() if self.size else 'S'}"
            f"{self.color.color[:1].upper() if self.color else 'C'}"
            f"{self.stock:03d}"
            f"{int(self.gsm or 0):04d}"
            f"{fabric_initials}"
            f"{self.product_type[:1].upper() if self.product_type else 'T'}"
            f"{self.sleeve[:1].upper() if self.sleeve else 'L'}"
            f"{self.fit[:1].upper() if self.fit else 'F'}"
            f"{int(self.net_weight or 0):04d}"
            f"{self.ideal_for[:1].upper() if self.ideal_for else 'I'}"
        )

    class Meta:
        indexes = [
            models.Index(fields=['slug']),
        ]
        ordering = ["-created_at"]


class ProductVariant(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='variants')
    sku = models.CharField(max_length=100, unique=True, db_index=True)
    size = models.CharField(max_length=50, blank=True, null=True)
    color = models.CharField(max_length=50, blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    market_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, validators=[MinValueValidator(0)])
    stock = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.product.name} - {self.sku}"

    class Meta:
        indexes = [
            models.Index(fields=['sku']),
        ]


class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='product_images/')
    alt_text = models.CharField(max_length=255, blank=True)
    is_primary = models.BooleanField(default=False)

    def __str__(self):
        return f"Image for {self.product.name}"


class ProductGroup(models.Model):
    group_name = models.CharField(max_length=50, default="NA")
    product = models.ManyToManyField(Product, blank=True)

    def __str__(self):
        return self.group_name

    class Meta:
        verbose_name = "Product Group"
        verbose_name_plural = "Product Groups"


class Cart(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='cart')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Cart of {self.user.username}"


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items', null=True, blank=True)
    user = models.ForeignKey(Customer, on_delete=models.CASCADE, null=True, blank=True)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    variant = models.ForeignKey(ProductVariant, on_delete=models.CASCADE, related_name='cart_items', null=True, blank=True)
    quantity = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)])
    size = models.ForeignKey(Size, on_delete=models.CASCADE, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.product.name} (x{self.quantity})"

    @property
    def price(self):
        if self.variant:
            return self.variant.price * self.quantity
        return self.product.selling_price * self.quantity

    class Meta:
        unique_together = ('cart', 'variant')


class Order(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Processing', 'Processing'),
        ('Shipped', 'Shipped'),
        ('Delivered', 'Delivered'),
        ('Cancelled', 'Cancelled'),
        ('not_placed', 'Not Placed'),
        ('confirmed', 'Confirmed'),
        ('packed', 'Packed'),
        ('out_for_delivery', 'Out for delivery'),
    ]
    
    PAYMENT_CHOICES = [
        ('cod', 'Cash on delivery'), 
        ('online', 'Online payment'),
        ('Credit Card', 'Credit Card'),
        ('Debit Card', 'Debit Card'),
        ('Net Banking', 'Net Banking'),
        ('UPI', 'UPI'),
        ('Razorpay', 'Razorpay'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True, blank=True)
    shipping_address = models.ForeignKey(ShippingAddress, on_delete=models.SET_NULL, null=True, blank=True)
    billing_address = models.ForeignKey(Address, related_name='billing_orders', on_delete=models.SET_NULL, null=True)
    products = models.ManyToManyField(CartItem, blank=True)
    order_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='Pending')
    payment = models.CharField(max_length=200, choices=PAYMENT_CHOICES, default="cod")
    total_price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    tracking_number = models.CharField(max_length=100, blank=True, null=True)
    carrier = models.CharField(max_length=200, blank=True, null=True)
    expected_delivery_date = models.DateField(null=True, blank=True)
    
    # Shiprocket integration fields
    shiprocket_order_id = models.CharField(max_length=200, blank=True, null=True)
    shiprocket_shipment_id = models.CharField(max_length=200, blank=True, null=True)
    awb_code = models.CharField(max_length=200, blank=True, null=True)
    courier_company_id = models.CharField(max_length=200, blank=True, null=True)
    courier_name = models.CharField(max_length=200, blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Order #{self.id} by {self.user.username}"

    @property
    def cart_total(self):
        return sum(item.price for item in self.products.all())

    @property
    def is_delivered(self):
        return self.status == "delivered"

    @property
    def total_products(self):
        return self.products.aggregate(models.Sum("quantity"))["quantity__sum"] or 0

    class Meta:
        indexes = [
            models.Index(fields=['order_date', 'status']),
        ]


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    variant = models.ForeignKey(ProductVariant, on_delete=models.CASCADE, related_name='order_items')
    quantity = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])

    def __str__(self):
        return f"{self.quantity} x {self.variant.product.name}"


class Payment(models.Model):
    PAYMENT_METHOD_CHOICES = [
        ('Credit Card', 'Credit Card'),
        ('Debit Card', 'Debit Card'),
        ('Net Banking', 'Net Banking'),
        ('UPI', 'UPI'),
        ('Razorpay', 'Razorpay'),
        ('cod', 'Cash on delivery'),
        ('online', 'Online payment'),
    ]

    STATUS_CHOICES = [
        ('Paid', 'Paid'),
        ('Pending', 'Pending'),
        ('Failed', 'Failed'),
    ]

    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name='payments')
    payment_date = models.DateTimeField(auto_now_add=True)
    payment_method = models.CharField(max_length=50, choices=PAYMENT_METHOD_CHOICES)
    amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    transaction_id = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return f"Payment for Order {self.order.id}"


class Wishlist(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='wishlist')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Wishlist of {self.user.username}"


class WishlistItem(models.Model):
    wishlist = models.ForeignKey(Wishlist, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='wishlist_items')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.product.name} in wishlist"

    class Meta:
        unique_together = ('wishlist', 'product')


class Review(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews')
    rating = models.PositiveIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Review by {self.user.username} for {self.product.name}"

    class Meta:
        unique_together = ('product', 'user')
        indexes = [
            models.Index(fields=['product', 'created_at']),
        ]


class Subscription(models.Model):
    email = models.EmailField(unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.email
    
    class Meta:
        ordering = ['-created_at']