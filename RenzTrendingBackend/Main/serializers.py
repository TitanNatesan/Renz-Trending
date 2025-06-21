from rest_framework import serializers
from . import models
from django.contrib.auth.models import User


class LocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Location
        fields = "__all__"


class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    phone = serializers.CharField(required=False)
    pic = serializers.ImageField(required=False)
    gender = serializers.CharField(required=False)
    gstNo = serializers.CharField(required=False, validators=[models.validate_gst])

    class Meta:
        model = models.Customer
        fields = ["username", "email", "password", "phone", "pic", "gender", "gstNo"]

    def create(self, validated_data):
        user = models.Customer(
            email=validated_data["email"], 
            username=validated_data["username"],
            phone=validated_data.get("phone", "")
        )
        if "pic" in validated_data:
            user.pic = validated_data["pic"]
        if "gender" in validated_data:
            user.gender = validated_data["gender"]
        if "gstNo" in validated_data:
            user.gstNo = validated_data["gstNo"]
        user.set_password(validated_data["password"])
        user.save()
        return user

    def update(self, instance, validated_data):
        instance.email = validated_data.get("email", instance.email)
        instance.username = validated_data.get("username", instance.username)
        instance.phone = validated_data.get("phone", instance.phone)
        instance.gender = validated_data.get("gender", instance.gender)
        instance.gstNo = validated_data.get("gstNo", instance.gstNo)
        if "pic" in validated_data:
            instance.pic = validated_data["pic"]
        if "password" in validated_data:
            instance.set_password(validated_data["password"])        
        instance.save()
        return instance


class GetUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["username", "email"]


class ColorSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Color
        fields = "__all__"


class SizeSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Size
        fields = "__all__"


class CategorySerializer(serializers.ModelSerializer):
    parent = serializers.PrimaryKeyRelatedField(queryset=models.Category.objects.all(), required=False, allow_null=True)
    
    class Meta:
        model = models.Category
        fields = ["id", "name", "parent", "slug", "image", "total_products", "created_at", "updated_at"]


class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.ProductImage
        fields = ["id", "image", "alt_text", "is_primary"]


class ProductVariantSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.ProductVariant
        fields = "__all__"


class ProductSerializer(serializers.ModelSerializer):
    images = ProductImageSerializer(many=True, read_only=True)
    category = CategorySerializer(read_only=True)
    color = ColorSerializer(read_only=True)
    size = SizeSerializer(read_only=True)
    avail_sizes = SizeSerializer(many=True, read_only=True, source='avail_sizes')
    variants = ProductVariantSerializer(many=True, read_only=True)
    SKU = serializers.CharField(read_only=True)

    class Meta:
        model = models.Product
        fields = "__all__"


class HomeProductSerializer(serializers.ModelSerializer):
    images = ProductImageSerializer(many=True, read_only=True)
    
    class Meta:
        model = models.Product
        fields = ["id", "name", "description", "selling_price", "market_price", "images", "rating", "buy_count", "slug"]


class ProductGroupSerializer(serializers.ModelSerializer):
    product = ProductSerializer(many=True, read_only=True)

    class Meta:
        model = models.ProductGroup
        fields = "__all__"


class AddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Address
        fields = "__all__"
        extra_kwargs = {
            "user": {"read_only": True}
        }


class ShippingAddressSerializer(serializers.ModelSerializer):
    location = LocationSerializer(required=False)
    
    class Meta:
        model = models.ShippingAddress
        fields = "__all__"
        extra_kwargs = {
            "user": {"read_only": True}
        }
    
    def create(self, validated_data):
        location_data = validated_data.pop('location', None)
        if location_data:
            location = models.Location.objects.create(**location_data)
            shipping_address = models.ShippingAddress.objects.create(location=location, **validated_data)
        else:
            shipping_address = models.ShippingAddress.objects.create(**validated_data)
        return shipping_address


class CartItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.CartItem
        fields = ["product", "variant", "quantity", "size"]


class CartItemDetailSerializer(serializers.ModelSerializer):
    product = ProductSerializer()
    variant = ProductVariantSerializer()
    size = SizeSerializer()

    class Meta:
        model = models.CartItem
        fields = ["id", "product", "variant", "quantity", "size", "price"]


class CartSerializer(serializers.ModelSerializer):
    items = CartItemDetailSerializer(many=True, read_only=True)
    
    class Meta:
        model = models.Cart
        fields = ["id", "user", "items", "created_at", "updated_at"]


class OrderItemSerializer(serializers.ModelSerializer):
    variant = ProductVariantSerializer(read_only=True)
    
    class Meta:
        model = models.OrderItem
        fields = ["id", "variant", "quantity", "price"]


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    shipping_address = ShippingAddressSerializer(read_only=True)
    billing_address = AddressSerializer(read_only=True)
    
    class Meta:
        model = models.Order
        fields = "__all__"


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Payment
        fields = "__all__"


class WishlistItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)
    
    class Meta:
        model = models.WishlistItem
        fields = ["id", "product", "created_at"]


class WishlistSerializer(serializers.ModelSerializer):
    items = WishlistItemSerializer(many=True, read_only=True)
    
    class Meta:
        model = models.Wishlist
        fields = ["id", "user", "items", "created_at", "updated_at"]


class WishlistCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.WishlistItem
        fields = ["product"]


class ReviewUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Customer
        fields = ["pic", "username"]


class ReviewSerializer(serializers.ModelSerializer):
    user = ReviewUserSerializer(read_only=True)
    
    class Meta:
        model = models.Review
        fields = ["id", "product", "user", "rating", "comment", "created_at", "updated_at"]


class ReviewCreateSerializer(serializers.ModelSerializer):
    product = serializers.PrimaryKeyRelatedField(queryset=models.Product.objects.all())
    
    class Meta:
        model = models.Review
        fields = ["product", "rating", "comment"]


class SubscriptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Subscription
        fields = "__all__"


class ProfileInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Customer
        fields = ["username", "first_name", "last_name", "email", "phone", "gender", "pic", "gstNo"]
        extra_kwargs = {
            "pic": {"read_only": True}
        }
        
    def validate_email(self, value):
        user_id = self.instance.id if self.instance else None
        if models.Customer.objects.filter(email=value).exclude(id=user_id).exists():
            raise serializers.ValidationError("This email is already in use.")
        return value
