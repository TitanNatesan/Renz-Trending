from django import forms
from django.contrib import admin
from django.utils.html import mark_safe, format_html
from . import models
from django.core.mail import send_mail
from django.utils import timezone
from django.utils.text import slugify
from django.db.models import Count
from rest_framework.authtoken.admin import TokenAdmin
from django.contrib.auth.admin import UserAdmin
from django.contrib.admin import SimpleListFilter
from django.utils.translation import gettext_lazy as _
import csv
from django.http import HttpResponse
import base64
from django.urls import reverse
from matplotlib.figure import Figure
import io


TokenAdmin.raw_id_fields = ["user"]
admin.site.site_header = "AG Admin"
admin.site.site_title = "Admin site"
admin.site.index_title = "AG Admin"


@admin.register(models.Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ('latitude', 'longitude', 'id')
    search_fields = ('latitude', 'longitude')

@admin.register(models.Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ('user', 'street', 'city', 'state', 'country', 'is_default')
    list_filter = ('state', 'country', 'is_default')
    search_fields = ('user__username', 'city', 'state', 'street')

class ProductAdminForm(forms.ModelForm):
    """
    Custom form for the Product admin.
    """
    tags = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            "placeholder": "Enter tags separated by commas"
        }),
        help_text="Tags should be separated by commas, e.g., 'tag1, tag2'."
    )
    fabric = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            "placeholder": "Enter fabrics separated by commas"
        }),
        help_text="Fabrics should be separated by commas, e.g., 'cotton, silk'."
    )

    class Meta:
        model = models.Product
        fields = "__all__"
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.initial["tags"] = ", ".join(self.instance.tags or [])
            self.initial["fabric"] = ", ".join(self.instance.fabric or [])

    def clean_tags(self):
        """
        Convert the comma-separated string of tags into a list.
        """
        tags = self.cleaned_data.get("tags", "")
        return [tag.strip() for tag in tags.split(",") if tag.strip()]

    def clean_fabric(self):
        """
        Convert the comma-separated string of fabric types into a list.
        """
        fabric = self.cleaned_data.get("fabric", "")
        return [item.strip() for item in fabric.split(",") if item.strip()]


class ProductImageInline(admin.TabularInline):
    """
    Inline configuration for managing multiple product images.
    """
    model = models.ProductImage
    extra = 1
    fields = ("image", "preview", "is_primary")
    readonly_fields = ("preview",)

    def preview(self, obj):
        """
        Generate a preview thumbnail for the image.
        """
        if obj.image:
            return format_html('<img src="{}" style="width: 75px; height: auto;" />', obj.image.url)
        return "No image available"

    preview.short_description = "Preview"

@admin.register(models.Product)
class ProductAdmin(admin.ModelAdmin):
    """
    Admin configuration for the Product model.
    """
    form = ProductAdminForm
    inlines = [ProductImageInline]
    list_display = ("main_image_tag","name", "stock", "market_price", "selling_price", "rating", "buy_count", "size", "color", "product_type", "created_at", "id")
    list_filter = ("product_type", "color", "rating", "created_at", "stock", "category")
    search_fields = ("name", "tags", "fabric", "slug")
    ordering = ("-created_at",)
    readonly_fields = ("created_at", "updated_at", "main_image_tag")
    prepopulated_fields = {"slug": ("name",)}

    fieldsets = (
        ("General Information", {
            "fields": ("name", "description", "slug", "tags", "fabric", "category", "brand")
        }),
        ("Pricing and Stock", {
            "fields": ("market_price", "selling_price", "stock", "buy_count")
        }),
        ("Product Attributes", {
            "fields": ("color", "size", "avail_sizes", "gsm", "product_type", "sleeve", "fit", "ideal_for", "net_weight")
        }),
        
    )

    def main_image_tag(self, obj):
        """
        Display the first image associated with the product as a thumbnail.
        """
        first_image = obj.images.first()
        if first_image and first_image.image:
            return format_html('<img src="{}" width="100" height="100" style="object-fit: cover;" />', first_image.image.url)
        return "No Image"

    main_image_tag.short_description = "Main Image"


    def save_model(self, request, obj, form, change):
        """
        Save the Product model first, then update its images from ProductImage.
        """
        obj.tags = form.cleaned_data.get("tags", [])
        obj.fabric = form.cleaned_data.get("fabric", [])
        if not obj.slug:
            obj.slug = slugify(obj.name)
        super().save_model(request, obj, form, change)

@admin.register(models.ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    """
    Admin configuration for the ProductImage model.
    """
    list_display = ("product", "image_tag", "is_primary")
    list_filter = ("product", "is_primary")
    search_fields = ("product__name",)
    ordering = ("product",)

    def image_tag(self, obj):
        """
        Display the image as a thumbnail in the admin list view.
        """
        return mark_safe(f'<img src="{obj.image.url}" width="100" height="100" style="object-fit: cover;" />')

    image_tag.short_description = "Image Preview"
    
    def get_readonly_fields(self, _request, obj=None):
        if obj:
            return ["product"]
        return []

@admin.register(models.ProductVariant)
class ProductVariantAdmin(admin.ModelAdmin):
    list_display = ('product', 'sku', 'size', 'color', 'price', 'stock')
    list_filter = ('product', 'size', 'color')
    search_fields = ('sku', 'product__name')

@admin.register(models.ProductGroup)
class ProductGroupAdmin(admin.ModelAdmin):
    list_display = ["group_name", "display_products", "total_products", "product_images", "id"]
    list_filter = ["group_name"]
    search_fields = ["group_name", "product__name"]
    filter_horizontal = ('product',)

    def display_products(self, obj):
        products = obj.product.all()
        return " | ".join(
            [
                f"{product.name} - {str(product.color).capitalize()} (₹{product.selling_price})"
                for product in products
            ]
        ) if products else "No Products"
    display_products.short_description = "Products"

    def total_products(self, obj):
        return obj.product.count()
    total_products.short_description = "Total Products"

    def product_images(self, obj):
        products = obj.product.all()
        images = [
            format_html(f'<img src="{image.image.url}" alt="{product.name}" style="width: 50px; height: 50px;" />',)
            for product in products
            for image in product.images.all()
        ]
        return format_html(" ".join(images)) if images else "No Images"
    product_images.short_description = "Product Images"

    fieldsets = (
        (None, {
            "fields": ["group_name", "product"],
        }),
    )

@admin.register(models.Customer)
class CustomerAdmin(UserAdmin):
    """
    Admin class for the Customer model.
    Inherits from UserAdmin to handle default User fields like username and email.
    """
    model = models.Customer
    list_display = (
        "username",
        "email",
        "first_name",
        "last_name",
        "gender",
        "gstNo",
        "is_wholeSaleUser",
        "profile_pic_preview",
        "phone",
    )
    list_filter = ("is_staff", "is_superuser", "is_active", "date_joined", "gender")
    search_fields = ("username", "email", "gstNo", "first_name", "last_name")
    ordering = ("-date_joined",)
    readonly_fields = ("date_joined", "last_login", "profile_pic_preview")

    fieldsets = (
        ("Personal Information", {
            "fields": ("username", "email", "first_name", "last_name","gender", "pic", "profile_pic_preview", "gstNo", "phone")
        }),
        ("Permissions", {
            "fields": ("is_staff", "is_active", "is_superuser", "groups", "user_permissions"),
        }),
        ("Important Dates", {
            "fields": ("last_login", "date_joined"),
        }),
    )

    add_fieldsets = UserAdmin.add_fieldsets + (
        (None, {
            "classes": ("wide",),
            "fields": ("pic", "gstNo", "phone", "gender"),
        }),
    )

    def profile_pic_preview(self, obj):
        """
        Display a small preview of the profile picture in the admin panel.
        """
        if obj.pic:
            return mark_safe(f'<img src="{obj.pic.url}" width="50" height="50" style="object-fit:cover;border-radius:50%;"/>')
        return "No Profile Picture"
    
    profile_pic_preview.short_description = "Profile Picture Preview"

@admin.register(models.ShippingAddress)
class ShippingAddressAdmin(admin.ModelAdmin):
    """
    Admin configuration for the ShippingAddress model.
    """
    list_display = (
        "name",
        "phone",
        "user",
        "city",
        "state",
        "pincode",
        "location_display",
    )
    list_filter = ("state", "city")
    search_fields = ("name", "phone", "city", "state", "pincode", "user__username")
    ordering = ("state", "city")
    list_per_page = 20

    fields = (
        "user",
        "name",
        "phone",
        "pincode",
        "locality",
        "address",
        "city",
        "state",
        "landmark",
        "alternate_phone",
        "location",
    )
    readonly_fields = ("location_display",)

    def location_display(self, obj):
        if obj.location:
            return str(obj.location)
        return "No Location Set"

    location_display.short_description = "Location"

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("user", "location")

class OrderStatusFilter(SimpleListFilter):
    title = _('Order Status')
    parameter_name = 'status'

    def lookups(self, _request, _model_admin):
        return models.Order.STATUS_CHOICES

    def queryset(self, _request, queryset):
        if self.value():
            return queryset.filter(status=self.value())
        return queryset

class OrderItemInline(admin.TabularInline):
    model = models.OrderItem
    extra = 0
    readonly_fields = ('variant', 'quantity', 'price')

@admin.register(models.Order)
class OrderAdmin(admin.ModelAdmin):
    inlines = [OrderItemInline] 
    list_display = [
        "id",
        "customer_name",
        "shipping_info",
        "status_badge",
        "payment_badge",
        "get_cart_total",
        "total_products",
        "shiprocket_info",
        "created_at",
    ]
    
    list_filter = [
        "status", 
        "payment", 
        "created_at",
        "carrier",
        OrderStatusFilter,
    ]
    
    search_fields = [
        "customer__first_name", 
        "customer__last_name", 
        "customer__username",
        "tracking_number", 
        "shiprocket_order_id",
        "awb_code"
    ]
    
    ordering = ["-created_at"]
    actions = [
        "mark_as_pending",
        "mark_as_confirmed",
        "mark_as_packed",
        "mark_as_shipped",
        "mark_as_out_for_delivery",
        "mark_as_delivered",
        "mark_as_cancelled",
        "export_order_csv",
    ]
    
    list_per_page = 25
    
    fieldsets = (
        ('Order Information', {
            'fields': ('customer', 'status', 'payment', 'total_price', 'tracking_number'),
            'classes': ('wide',)
        }),
        ('Shipping Details', {
            'fields': ('shipping_address', 'billing_address', 'carrier', 'expected_delivery_date'),
            'classes': ('collapse',)
        }),
        ('Shiprocket Integration', {
            'fields': ('shiprocket_order_id', 'shiprocket_shipment_id', 'awb_code', 'courier_company_id', 'courier_name'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ('created_at', 'updated_at', 'total_price')    
    
    def get_cart_total(self, obj):
        return format_html(
            '<span style="font-weight: bold; color: #2e7d32;">₹{:.2f}</span>', 
            obj.cart_total
        )
    get_cart_total.short_description = "Cart Total"
    
    def status_badge(self, obj):
        status_colors = {
            'Pending': '#ff9800',
            'Processing': '#2196f3',
            'confirmed': '#2196f3',
            'packed': '#9c27b0',
            'shipped': '#3f51b5',
            'out_for_delivery': '#ff5722',
            'Delivered': '#4caf50',
            'Cancelled': '#f44336',
        }
        color = status_colors.get(obj.status, '#757575')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 12px; font-size: 11px; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = "Status"
    status_badge.admin_order_field = "status"
    
    def payment_badge(self, obj):
        color = '#4caf50' if 'online' in obj.payment.lower() else '#ff9800'
        icon = '💳' if 'online' in obj.payment.lower() else '💵'
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 12px; font-size: 11px; font-weight: bold;">{} {}</span>',
            color,
            icon,
            obj.get_payment_display()
        )
    payment_badge.short_description = "Payment"
    payment_badge.admin_order_field = "payment"
    
    def shiprocket_info(self, obj):
        if obj.shiprocket_order_id:
            return format_html(
                '<div style="font-size: 11px;">'
                '<div><strong>Order:</strong> {}</div>'
                '<div><strong>AWB:</strong> {}</div>'
                '<div><strong>Courier:</strong> {}</div>'
                '</div>',
                obj.shiprocket_order_id[:10] + '...' if len(obj.shiprocket_order_id) > 10 else obj.shiprocket_order_id,
                obj.awb_code or 'N/A',
                obj.courier_name or 'N/A'
            )
        return format_html('<span style="color: #999;">Not integrated</span>')
    shiprocket_info.short_description = "Shiprocket"
    
    def total_products(self, obj):
        count = obj.total_products
        return format_html(
            '<span style="background-color: #e3f2fd; color: #1976d2; padding: 2px 6px; border-radius: 8px; font-size: 11px; font-weight: bold;">{} items</span>',
            count
        )
    total_products.short_description = "Items"
    
    def customer_name(self, obj):
        customer = obj.customer or obj.user
        return format_html(
            '<div style="font-size: 12px;">'
            '<div><strong>{} {}</strong></div>'
            '<div style="color: #666;">{}</div>'
            '</div>',
            customer.first_name or '',
            customer.last_name or '',
            customer.username
        )
    customer_name.short_description = "Customer"
    
    def shipping_info(self, obj):
        if obj.shipping_address:
            addr = obj.shipping_address
            return format_html(
                '<div style="font-size: 11px;">'
                '<div><strong>{}</strong></div>'
                '<div>{}, {}</div>'
                '<div>{}</div>'
                '</div>',
                addr.name,
                addr.city,
                addr.state,
                addr.phone
            )
        return format_html('<span style="color: #999;">No address</span>')
    shipping_info.short_description = "Shipping Address"    
    
    def mark_as_pending(self, request, queryset):
        updated = queryset.update(status="Pending")
        self.message_user(request, f"Successfully marked {updated} orders as Pending.")
    mark_as_pending.short_description = "Mark selected orders as Pending"

    def mark_as_confirmed(self, request, queryset):
        updated = queryset.update(status="confirmed")
        self.message_user(request, f"Successfully confirmed {updated} orders.")
    mark_as_confirmed.short_description = "Mark selected orders as Confirmed"
    
    def mark_as_packed(self, request, queryset):
        updated = queryset.update(status="packed")
        self.message_user(request, f"Successfully marked {updated} orders as Packed.")
    mark_as_packed.short_description = "Mark selected orders as Packed"
    
    def mark_as_shipped(self, request, queryset):
        updated = queryset.update(status="Shipped")
        self.message_user(request, f"Successfully marked {updated} orders as Shipped.")
    mark_as_shipped.short_description = "Mark selected orders as Shipped"

    def mark_as_cancelled(self, request, queryset):
        updated = queryset.update(status="Cancelled")
        self.message_user(request, f"Successfully cancelled {updated} orders.")
    mark_as_cancelled.short_description = "Mark selected orders as Cancelled"

    def mark_as_out_for_delivery(self, request, queryset):
        updated = queryset.update(status="out_for_delivery")
        self.message_user(request, f"Successfully marked {updated} orders as Out for Delivery.")
    mark_as_out_for_delivery.short_description = "Mark selected orders as Out for Delivery"

    def mark_as_delivered(self, request, queryset):
        updated = queryset.update(status="Delivered")
        self.message_user(request, f"Successfully marked {updated} orders as Delivered.")
    mark_as_delivered.short_description = "Mark selected orders as Delivered"
    
    def export_order_csv(self, _request, queryset):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="orders.csv"'
        
        writer = csv.writer(response)
        writer.writerow([
            'Order ID', 'Customer', 'Status', 'Payment', 'Total Amount', 
            'Items Count', 'Tracking Number', 'Created Date'
        ])
        
        for order in queryset:
            writer.writerow([
                order.id,
                f"{order.customer.first_name} {order.customer.last_name}".strip() or order.customer.username,
                order.status,
                order.payment,
                order.cart_total,
                order.total_products,
                order.tracking_number or '',
                order.created_at.strftime('%Y-%m-%d %H:%M:%S')
            ])
        
        return response
    export_order_csv.short_description = "Export selected orders to CSV"

@admin.register(models.OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('order', 'variant', 'quantity', 'price')
    search_fields = ('order__id', 'variant__sku', 'variant__product__name')

@admin.register(models.Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('order', 'payment_method', 'amount', 'status', 'payment_date', 'transaction_id')
    list_filter = ('status', 'payment_method')
    search_fields = ('order__id', 'transaction_id')

@admin.register(models.Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = [
        "user_name",
        "product_name",
        "rating_display",
        "comment",
        "created_at",
        "view_product_link"
    ]
    list_filter = ["rating", "created_at"]
    search_fields = ["user__username", "product__name", "comment"]
    ordering = ["-created_at"]

    def user_name(self, obj):
        return f"{obj.user.first_name} {obj.user.last_name}"
    user_name.short_description = "User"

    def product_name(self, obj):
        return obj.product.name
    product_name.short_description = "Product"

    def rating_display(self, obj):
        return f"{obj.rating}/5"
    rating_display.short_description = "Rating"

    def view_product_link(self, obj):
        url = reverse("admin:Main_product_change", args=[obj.product.id])
        return format_html('<a href="{}">View Product</a>', url)
    view_product_link.short_description = "Product Link"

@admin.register(models.Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ["name", "parent", "product_count", "image_tag", "view_products_link"]
    list_filter = ["parent"]
    search_fields = ["name", "slug"]
    readonly_fields = ("image_tag",)
    prepopulated_fields = {"slug": ("name",)}
    
    def product_count(self, obj):
        return obj.products.count()
    product_count.short_description = "Number of Products"

    def image_tag(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="100" height="100" style="object-fit: cover;" />', obj.image.url)
        return "No Image"
    image_tag.short_description = "Image Preview"

    def view_products_link(self, obj):
        url = reverse("admin:Main_product_changelist") + f"?category__id__exact={obj.id}"
        return format_html('<a href="{}">View Products</a>', url)
    view_products_link.short_description = "Products Link"

    actions = ["export_as_csv"]

    def export_as_csv(self, _request, queryset):
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="categories.csv"'
        writer = csv.writer(response)
        writer.writerow(["Name", "Parent", "Total Products", "Image URL"])
        for category in queryset:
            writer.writerow([category.name, category.parent.name if category.parent else "", category.products.count(), category.image.url if category.image else "N/A"])
        return response
    export_as_csv.short_description = "Export Selected Categories to CSV"

    fieldsets = (
        (None, {
            "fields": ("name", "slug", "parent", "image", "image_tag")
        }),
    )

@admin.register(models.Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ["email", "created_at", "is_active", "send_confirmation_email"]
    search_fields = ["email"]
    list_filter = ["is_active", "created_at"]
    ordering = ["-created_at"]
    actions = ["send_bulk_confirmation_email"]

    def send_bulk_confirmation_email(self, request, queryset):
        for subscription in queryset:
            send_mail(
                'Subscription Confirmation',
                'Thank you for subscribing to our newsletter!',
                'from@example.com',
                [subscription.email],
                fail_silently=False,
            )
        self.message_user(request, "Confirmation emails sent successfully.")
    send_bulk_confirmation_email.short_description = "Send Confirmation Email to Selected"
    
    def send_confirmation_email(self, obj):
        return mark_safe(f'<a href="mailto:{obj.email}">Send Email</a>')
    send_confirmation_email.short_description = "Send Email"

@admin.register(models.Color)
class ColorAdmin(admin.ModelAdmin):
    list_display = ["color", "id", "hexcode", "color_tag", "total_products"]
    search_fields = ["color", "hexcode"]

    def color_tag(self, obj):
        return (
            mark_safe(
                f'<div style="background-color:{obj.hexcode}; width: 50px; height: 50px; border: 1px solid #ccc;"></div>'
            )
            if obj.hexcode
            else ("NA")
        )
    color_tag.short_description = "Color Preview"

    def total_products(self, obj):
        return obj.product_set.count()
    total_products.short_description = "Total Products"

    fieldsets = (
        (None, {
            'fields': ('color', 'hexcode'),
        }),
    )

@admin.register(models.Size)
class SizeAdmin(admin.ModelAdmin):
    list_display = [
        "size", 
        "total_products", 
        "measurements_summary",
        "id"
    ]
    search_fields = ["size"]
    
    fieldsets = (
        (None, {
            "fields": ("size",)
        }),
        ("Upper Body Measurements (cm)", {
            "fields": ("bust", "chest", "shoulder", "top_length", "sleeve_length", "cuff_circumference", "bicep_circumference"),
        }),
        ("Lower Body Measurements (cm)", {
            "fields": ("hip", "rise", "waist", "thigh", "pant_length", "inseam_length", "knee_circumference", "ankle_circumference"),
        }),
        ("Full Body/Dress Measurements (cm)", {
            "fields": ("dress_length", "shoulder_to_hip", "shoulder_to_knee", "shoulder_to_waist", "shoulder_to_ankle", "neck_circumference"),
        }),
    )

    @admin.display(description="Body Measurements Summary")
    def measurements_summary(self, obj):
        measurements = []
        if obj.bust: measurements.append(f"Bust: {obj.bust} cm")
        if obj.chest: measurements.append(f"Chest: {obj.chest} cm")
        if obj.waist: measurements.append(f"Waist: {obj.waist} cm")
        if obj.hip: measurements.append(f"Hip: {obj.hip} cm")
        return mark_safe("<br>".join(measurements)) if measurements else "No data available"

    @admin.display(description="Total Products")
    def total_products(self, obj):
        return obj.product_set.count() + obj.products_sizes.count()

@admin.register(models.Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ('user', 'created_at', 'updated_at')

@admin.register(models.CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ["product", "quantity", "price_display", "size", "image_display", "user", "created_at", "id"]
    list_display_links = ["product"]
    search_fields = ["product__name", "size__size", "user__email"]
    list_filter = ["product", "size", "user", "created_at"]
    ordering = ["-created_at"]
    readonly_fields = ('created_at',)

    def get_readonly_fields(self, _request, obj=None):
        if obj:
            return ["product", "user", "created_at", "cart", "variant"]
        return ["created_at"]

    def price_display(self, obj):
        return f"₹ {obj.price:.2f}"
    price_display.short_description = "Total Price"

    def image_display(self, obj):
        if obj.product and obj.product.images.exists():
            return mark_safe(f'<img src="{obj.product.images.first().image.url}" width="50" height="50" />')
        return "No Image"
    image_display.short_description = "Product Image"

class WishlistItemInline(admin.TabularInline):
    model = models.WishlistItem
    extra = 1
    readonly_fields = ('product_image',)
    fields = ('product', 'product_image')
    autocomplete_fields = ['product']

    def product_image(self, obj):
        if obj.product and obj.product.images.exists():
            return format_html('<img src="{}" style="width: 50px; height: auto;" />', obj.product.images.first().image.url)
        return "No Image"
    product_image.short_description = "Image"

@admin.register(models.Wishlist)
class WishlistAdmin(admin.ModelAdmin):
    list_display = ('user', 'created_at', 'item_count')
    search_fields = ('user__username',)
    inlines = [WishlistItemInline]

    def item_count(self, obj):
        return obj.items.count()
    item_count.short_description = "Number of Items"

@admin.register(models.WishlistItem)
class WishlistItemAdmin(admin.ModelAdmin):
    list_display = ('wishlist', 'product', 'created_at')
    search_fields = ('wishlist__user__username', 'product__name')
    autocomplete_fields = ['wishlist', 'product']
