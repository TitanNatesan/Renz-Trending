import random
from icecream import ic
from . import models, serializers, filters
from django.contrib.auth.models import User
from django.contrib.auth.models import Group
from django.contrib.auth import authenticate
from django.utils import timezone
from datetime import timedelta
from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAdminUser
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter
from rest_framework.authtoken.models import Token
from django.core.exceptions import ValidationError
from django.contrib.auth.password_validation import validate_password

# ic.disable()

@api_view(["POST"])
@permission_classes([AllowAny])
def register(request):
    if request.method == "POST":
        try:
            serializer = serializers.UserSerializer(data=request.data)
            if not request.data.get("email"):
                return Response(
                    {"email": "Please Provide your Mail Address"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            if serializer.is_valid():
                if User.objects.filter(email=request.data["email"]).exists():
                    return Response(
                        {"message": ["Email Already Exists"]},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
                if models.Customer.objects.filter(phone=request.data["phone"]).exists():
                    return Response(
                        {"message": ["Phone Number Already Exists"]},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
                user = serializer.save()
                token, created = Token.objects.get_or_create(user=user)
                group = Group.objects.get_or_create(name="Customer")[0]
                user.groups.add(group)
                cont = serializer.data
                cont["token"] = token.key
                cont["groups"] = [group.name]
                cont["message"] = "User Created Successfully"
                return Response(cont, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            ic(e)
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class CustomAuthToken(APIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        try:
            username = request.data.get("username")
            password = request.data.get("password")
            if username is None or password is None:
                raise Exception
        except:
            return Response(
                {"error": "Please Provide Username and Password"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = authenticate(request, username=username, password=password)

        if user is not None:
            token, created = Token.objects.get_or_create(user=user)
            return Response(
                {"token": token.key, "username": user.username, "email": user.email},
                status=status.HTTP_200_OK,
            )
        else:
            return Response(
                {"error": "Invalid Credentials"}, status=status.HTTP_400_BAD_REQUEST
            )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def logout(request):
    try:
        request.user.auth_token.delete()
        cont = {"user": request.user.username, "message": "Logout Successfully"}
        return Response(cont)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def checkAuth(request):
    return Response({"message": "Authenticated", "username": request.user.username})


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def resetPassword(req):
    if req.method == "POST":
        try:
            user_obj = models.Customer.objects.get(username=req.user.username)
            old_pass = req.data.get("old_password")
            new_pass = req.data.get("new_password")
            confirm_pass = req.data.get("confirm_password")

            user = authenticate(username=user_obj.username, password=old_pass)
            if not user:
                return Response(
                    {"error": "Old password Invalid"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            if not new_pass or not confirm_pass:
                return Response(
                    {"error": "New or confirm password missing"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            if new_pass != confirm_pass:
                return Response(
                    {"error": "Passwords do not match"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            try:
                validate_password(new_pass, user)
            except ValidationError as e:
                return Response(
                    {"error": e.messages}, status=status.HTTP_400_BAD_REQUEST
                )

            user_obj.set_password(new_pass)
            user_obj.save()
            return Response(
                {"message": "Password has been reset"}, status=status.HTTP_200_OK
            )
        except models.Customer.DoesNotExist:
            return Response(
                {"error": "User not found"}, status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


@api_view(["GET"])
@permission_classes([AllowAny])
def getCategories(request):
    categories = models.Category.objects.all()
    serializer = serializers.CategorySerializer(categories, many=True)
    cont = {
        "message": "Success",
        "data": serializer.data,
    }
    return Response(cont)


class ProductListView(generics.ListAPIView):
    queryset = models.Product.objects.all()
    serializer_class = serializers.ProductSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_class = filters.ProductFilter
    permission_classes = [AllowAny]

    def get_queryset(self):
        queryset = super().get_queryset()
        query = self.request.query_params.get("search", None)
        if query:
            queryset = queryset.filter(name__icontains=query)
        return queryset

    def format_product(self, product):
        images = models.ProductImages.objects.filter(product=product)
        discount_percentage = (
            1 - (float(product.selling_price) / float(product.market_price))
        ) * 100
        badge = (
            "Hot"
            if product.buy_count > 100
            else f"-{int(discount_percentage)}%" if discount_percentage > 0 else None
        )
        return {
            "id": product.id,
            "slug": product.slug,
            "img1": str(images[0].image.url) if len(images) > 0 else None,
            "img2": str(images[1].image.url) if len(images) > 1 else None,
            "rating": random.randint(1, 5),
            "oldPrice": product.market_price,
            "newPrice": product.selling_price,
            "badge": badge,
            "category": (
                product.categories[0].name if product.categories else "Uncategorized"
            ),
            "name": product.name,
        }

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        formatted_products = [self.format_product(product) for product in queryset]
        return Response({"products": formatted_products})


@api_view(["POST"])
@permission_classes([AllowAny])
def makeSubscription(request):
    if request.method == "POST":
        serializer = serializers.SubscriptionSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Subscribed Successfully"})
        return Response(serializer.errors)


@api_view(["GET"])
@permission_classes([AllowAny])
def getProduct(request, slug):
    if request.method == "GET":
        cont = {}
        try:
            product = models.Product.objects.get(slug=slug)
            cont["product"] = serializers.ProductSerializer(product).data
            product_variants = models.ProductGroup.objects.filter(product=product).first()
            cont["variants"] = serializers.ProductGroupSerial(product_variants).data
            return Response(cont)
        except models.Product.DoesNotExist: return Response({"error": "Product not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e: return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["GET"])
@permission_classes([AllowAny])
def getRelatedProducts(request, slug):
    """Get related products - simplified version that always works"""
    try:
        # Get the current product
        current_product = models.Product.objects.get(slug=slug)
        
        # Get 8 random products excluding the current one
        related_products = models.Product.objects.exclude(id=current_product.id).order_by('?')[:8]
        
        # Format products
        formatted_products = []
        for product in related_products:
            try:
                # Get product images
                product_images = list(product.product_images.all())
                
                # Calculate discount
                discount_percentage = 0
                if product.market_price > 0:
                    discount_percentage = ((product.market_price - product.selling_price) / product.market_price) * 100
                
                # Determine badge
                badge = None
                if product.buy_count > 100:
                    badge = "Hot"
                elif discount_percentage > 5:
                    badge = f"-{int(discount_percentage)}%"
                
                # Get category name
                category_name = "Fashion"
                try:
                    categories = product.categories
                    if categories:
                        category_name = categories[0].name
                except:
                    pass
                
                formatted_product = {
                    "id": product.id,
                    "slug": product.slug,
                    "img1": product_images[0].image.url if len(product_images) > 0 else None,
                    "img2": product_images[1].image.url if len(product_images) > 1 else None,
                    "rating": int(product.rating) if product.rating else 4,
                    "oldPrice": float(product.market_price),
                    "newPrice": float(product.selling_price),
                    "badge": badge,
                    "category": category_name,
                    "name": product.name,
                    "stock": product.stock,
                }
                formatted_products.append(formatted_product)
            except Exception as e:
                # Skip products that can't be formatted
                continue
        
        return Response({
            "success": True,
            "related_products": formatted_products,
            "count": len(formatted_products)
        })
        
    except models.Product.DoesNotExist:
        return Response({"error": "Product not found"}, status=404)
    except Exception as e:
        return Response({"error": str(e)}, status=500)
        


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def addCartItem(request):
    if request.method == "POST":
        ciSerial = serializers.CartItemSerializer(data=request.data)
        user = models.Customer.objects.get(user=request.user)
        product = models.Product.objects.get(id=request.data["product"])
        size = request.data["size"]
        if user.cart.filter(product=product, size=size).exists():
            ciid = user.cart.get(product=product, size=size).id
            cartItem = models.CartItem.objects.get(id=ciid)
            cartItem.quantity += 1
            cartItem.save()
            return Response({"message": "Success"})
        elif ciSerial.is_valid():
            ciSerial.save()
            user.cart.add(ciSerial.instance)
            user.save()
            return Response({"message": "Success"})
        return Response(ciSerial.errors)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def updateCartItem(request):
    if request.method == "POST":
        user = models.Customer.objects.get(user=request.user)
        cartItem = models.CartItem.objects.get(id=request.data["id"])
        quantity = request.data["quantity"]
        cd = request.data["cd"]
        if cd or quantity == 0:
            user.cart.remove(cartItem)
            cartItem.delete()
            cart = user.cart.all()
            cartSerial = serializers.SendCartItemSerializer(cart, many=True)
            cont = {
                "message": "Deleted",
                "cartItems": cartSerial.data,
            }
            return Response(cont)
        elif quantity > 0:
            cartItem.quantity = quantity
            cartItem.save()
            cart = user.cart.all()
            cartSerial = serializers.SendCartItemSerializer(cart, many=True)
            cont = {
                "message": "Updated",
                "cartItems": cartSerial.data,
            }
            return Response(cont)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_cart(requset):
    if requset.method == "GET":
        user = models.Customer.objects.get(user=requset.user)
        cart = user.cart.all()
        serializer = serializers.SendCartItemSerializer(cart, many=True)
        return Response(serializer.data)


@api_view(["GET", "POST", "PUT"])
@permission_classes([IsAuthenticated])
def order(request):
    if request.method == "POST" and request.data["type"] == "single-product":
        try:
            user = models.Customer.objects.get(username=request.user.username)
            product = models.Product.objects.get(id=request.data["product"])
            size = models.Size.objects.get(id=request.data["size"])
            qty = int(request.data["quantity"])

            if qty <= 0:
                return Response(
                    {"error": "Quantity must be greater than zero"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            cartitem, created = models.CartItem.objects.get_or_create(
                user=user,
                product=product,
                size=size,
            )

            makeorder, created = models.Order.objects.get_or_create(
                customer=user,
                status="pending",
                tracking_number="123",
                carrier="naane dhan",
            )

            if created:
                cartitem.quantity = qty
                cartitem.save()
            else:
                if qty > cartitem.quantity:
                    cartitem.quantity = qty
                    cartitem.save()

            makeorder.products.add(cartitem)
            makeorder.save()

            return Response(
                {"message": "Order placed successfully", "order_id": makeorder.id},
                status=status.HTTP_201_CREATED,
            )

        except models.Customer.DoesNotExist:
            return Response(
                {"error": "Customer not found"},
                status=status.HTTP_404_NOT_FOUND,
            )
        except models.Product.DoesNotExist:
            return Response(
                {"error": "Product not found"},
                status=status.HTTP_404_NOT_FOUND,
            )
        except models.Size.DoesNotExist:
            return Response(
                {"error": "Size not found"},
                status=status.HTTP_404_NOT_FOUND,
            )
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    if request.method == "PUT" and request.data['change']=="address":
        try:
            order = models.Order.objects.get(id=request.data["order_id"])
            address = models.ShippingAddress.objects.get(id=request.data["address_id"])
            order.shipping_address = address
            order.save()
            return Response({"message": "Address Updated Successfully"})
        except models.Order.DoesNotExist:
            return Response(
                {"error": "Order not found"},
                status=status.HTTP_404_NOT_FOUND,
            )
        except models.ShippingAddress.DoesNotExist:
            return Response(
                {"error": "Shipping address not found"},
                status=status.HTTP_404_NOT_FOUND,
            )
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def getorder(request, oid):
    if request.method == "GET":
        try:
            order = models.Order.objects.get(id=oid)
            serializer = serializers.OrderSerializer(order)
            return Response(serializer.data)
        except models.Order.DoesNotExist:
            return Response(
                {"error": "Order not found"},
                status=status.HTTP_404_NOT_FOUND,
            )
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def isWholeSaleUser(request):
    if request.method == "GET":
        user = models.Customer.objects.get(user=request.user)
        return Response({"is_wholeSaleUser": user.is_wholeSaleUser})


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def getWholeSaleProducts(request):
    if request.method == "GET":
        products = models.BulkProducts.objects.all()
        serializer = serializers.BulkProductSerializer(products, many=True)
        return Response(serializer.data)


@api_view(["GET"])
@permission_classes([AllowAny])
def Home(request):
    cont = {}
    cont["login"] = request.user.username if request.user.is_authenticated else None

    # Categories data
    categories = models.Category.objects.all()
    serializer = serializers.CategorySerializer(categories, many=True)
    cont["categories"] = serializer.data

    def get_random_products(queryset, num_items):
        queryset_list = list(queryset)
        random.shuffle(queryset_list)
        return queryset_list[:num_items]

    # Get products for each category
    newly_added_products = get_random_products(
        models.Product.objects.order_by("-created_at")[:6], 3
    )
    popular_products = get_random_products(
        models.Product.objects.order_by("buy_count")[:6], 3
    )
    featured_products = get_random_products(
        models.Product.objects.order_by("-selling_price")[:6], 3
    )
    newly_added_productss = get_random_products(
        models.Product.objects.order_by("-created_at")[:6], 6
    )

    # Helper function to format product data
    def format_product(product, category_type):
        images = models.ProductImages.objects.filter(product=product)
        # Calculate discount badge if applicable
        discount_percentage = (
            1 - (float(product.selling_price) / float(product.market_price))
        ) * 100
        badge = (
            "Hot"
            if product.buy_count > 100
            else f"-{int(discount_percentage)}%" if discount_percentage > 0 else None
        )
        return {
            "id": product.pk,
            "slug": product.slug,
            "img1": str(images[0].image.url) if len(images) > 0 else None,
            "img2": str(images[1].image.url) if len(images) > 1 else None,
            "rating": random.randint(
                1, 5
            ),  # Assigning a random rating for demonstration
            "oldPrice": product.market_price,
            "newPrice": product.selling_price,
            "badge": badge,
            "category": (
                product.categories[0].name if product.categories else "Uncategorized"
            ),
            "name": product.name,
            "type": category_type,
        }

    # Serialize each category separately
    cont["newly_added"] = [
        format_product(p, "Newly Added") for p in newly_added_productss
    ]
    cont["hot_release"] = [
        format_product(p, "Newly Added") for p in newly_added_products
    ]
    cont["trendy"] = [format_product(p, "Popular") for p in popular_products]
    cont["best_deal"] = [format_product(p, "Featured") for p in featured_products]

    # Combine all products with their respective types
    cont["products"] = (
        [format_product(p, "Newly Added") for p in newly_added_products]
        + [format_product(p, "Popular") for p in popular_products]
        + [format_product(p, "Featured") for p in featured_products]
    )

    return Response(cont)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def Review(req):
    if req.method == "POST":
        ic(req.data)
        serializer = serializers.PostReviewSerial(data=req.data)
        if serializer.is_valid():
            review_data = {
                "user": models.Customer.objects.get(username=req.user.username),
                "product": models.Product.objects.get(slug=req.data["product"]),
                "rating": str(req.data["rating"]).strip(),
                "review": req.data["review"],
            }
            review = models.Review.objects.create(**review_data)
            review.save()
            return Response({"message": "Success"})
        return Response(serializer.errors)


@api_view(["GET"])
@permission_classes([AllowAny])
def GetReview(req, pid):
    if req.method == "GET":
        cont = {}
        reviews = models.Review.objects.filter(product=pid)
        cont["reviews"] = serializers.PutReviewSerial(reviews, many=True).data
        return Response(cont)


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def Cart(req):
    user = models.Customer.objects.get(username=req.user.username)
    if req.method == "GET":
        cont = {}
        cartitem = models.CartItem.objects.filter(user=user)
        cont["cart"] = serializers.SendCartItemSerializer(cartitem, many=True).data
        return Response(cont)

    if req.method == "POST":
        cont = {}
        cart = models.CartItem.objects.get(pk=req.data["cartID"])
        if req.data["action"] == "r":
            cont["message"] = "One Item Reduced"
            if cart.quantity == 1:
                cont["message"] = "Item Deleted"
                cart.delete()
            cart.quantity -= 1
            cart.save()
        elif req.data["action"] == "a":
            cont["message"] = "One Item Added"
            cart.quantity += 1
            cart.save()
        elif req.data["action"] == "d":
            cont["message"] = "Item Deleted"
            cart.delete()
        cont["cart"] = serializers.SendCartItemSerializer(
            models.CartItem.objects.filter(user=user),
            many=True,
        ).data
        return Response(cont)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def AddToCart(req):
    if req.method == "POST":
        ic(req.data)
        try:
            product = models.Product.objects.get(pk=req.data["product"])
            user = models.Customer.objects.get(username=req.user.username)
            qty = int(req.data["quantity"])
            size = models.Size.objects.get(pk=req.data["size"])

            if qty <= 0: return Response({"error": "Quantity must be greater than zero"},status=status.HTTP_400_BAD_REQUEST,)

            cartItem, created = models.CartItem.objects.get_or_create(user=user, product=product, size=size)

            if created:
                if qty > 20: return Response({"error": "Quantity cannot exceed 20"},status=status.HTTP_400_BAD_REQUEST,)
                cartItem.quantity = qty
                cartItem.color = (product.product_color)  # ithu irukardhala error varala, working good
                cartItem.save()
            else:
                if cartItem.quantity + qty > 20: return Response({"error": "Total quantity cannot exceed 20"},status=status.HTTP_400_BAD_REQUEST,)
                cartItem.quantity += qty
                cartItem.save()

            return Response({"message": "Item added to cart successfully"},status=status.HTTP_200_OK,)

        except models.Product.DoesNotExist: return Response({"error": "Product not found"}, status=status.HTTP_404_NOT_FOUND)
        except models.Size.DoesNotExist: return Response({"error": "Size not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e: return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def BuyNow(req):
    ic(req.data)
    if req.method == "POST" and req.data.get("type") == "PP": # PP - Product Page
        try:
            customer = models.Customer.objects.get(username=req.user.username)
            product = models.Product.objects.get(pk=req.data.get("pid"))
            size = models.Size.objects.get(pk=req.data.get("sid"))

            item, created = models.CartItem.objects.get_or_create(user=customer, product=product, size=size)
            if created: item.save()
            order = models.Order.objects.create(customer=customer, status="Not Placed")
            order.products.add(item)
            order.save()

            return Response({"message": "Order Created Successfully", "order_id": order.id},status=status.HTTP_201_CREATED)
        except models.Customer.DoesNotExist:return Response({"error": "Customer not found"}, status=status.HTTP_404_NOT_FOUND)
        except models.Product.DoesNotExist:return Response({"error": "Product not found"}, status=status.HTTP_404_NOT_FOUND)
        except models.Size.DoesNotExist:return Response({"error": "Size not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    if req.method == "POST" and req.data.get("type") == "MP": # MP - Main Page
        cont = {}
        try:
            customer = models.Customer.objects.get(username=req.user.username)
        except models.Customer.DoesNotExist:
            return Response({"error": "Customer not found"}, status=status.HTTP_404_NOT_FOUND)
        
        pass
    
    return Response({"error": "Invalid request type"}, status=status.HTTP_400_BAD_REQUEST)


@api_view(["GET", "POST", "PUT", "DELETE"])
@permission_classes([IsAuthenticated])
def profile(request):
    ic(request.data)
    if request.method == "GET":
        user = models.Customer.objects.get(username=request.user.username)
        piserializer = serializers.ProfileInfoSerial(user)
        shippingAddresses = models.ShippingAddress.objects.filter(user=user)
        saserial = serializers.ShippingAddressSerializer(shippingAddresses, many=True)
        cont = {
            "ProfileInfo": piserializer.data,
            "ShippingAddresses": saserial.data,
        }
        return Response(cont)

    if request.method == "PUT" and request.data["type"] == "profileinfo":
        user = models.Customer.objects.get(username=request.user.username)
        serializer = serializers.ProfileInfoSerial(user, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Profile Updated Successfully"})
        return Response(serializer.errors)

    if request.method == "PUT" and request.data["type"] == "addressUpdate":
        try:
            address_id = request.data.get("id")
            user = models.Customer.objects.get(username=request.user.username)
            address = models.ShippingAddress.objects.get(user=user, id=address_id)
            ic(address)
            serial = serializers.ShippingAddressSerializer(address, data=request.data)
            if serial.is_valid():
                ic("saved")
                serial.save()
                return Response(
                    {"message": "Updated Successfully"}, status=status.HTTP_200_OK
                )
            return Response(serial.errors, status=status.HTTP_400_BAD_REQUEST)
        except models.ShippingAddress.DoesNotExist:
            return Response(
                {"error": "Address not found"}, status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            ic(f"Error: {str(e)}")
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    if request.method == "POST" and request.data["type"] == "addressUpdate":
        try:
            user = models.Customer.objects.get(username=request.user.username)
            request.data["user"] = user.id
            serial = serializers.ShippingAddressSerializer(data=request.data)
            if serial.is_valid():
                ic("saved")
                serial.save(user=user)
                return Response(
                    {"message": "Created Successfully"}, status=status.HTTP_201_CREATED
                )
            return Response(serial.errors, status=status.HTTP_400_BAD_REQUEST)
        except models.ShippingAddress.DoesNotExist:
            return Response(
                {"error": "Address not found"}, status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            ic(f"Error: {str(e)}")
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    if request.method == "DELETE":
        address_id = request.data.get("id")
        try:
            address = models.ShippingAddress.objects.get(
                id=address_id, user=request.user
            )
            address.delete()
            return Response({"message": "Address Deleted Successfully"})
        except models.ShippingAddress.DoesNotExist:
            return Response(
                {"error": "Address not found"}, status=status.HTTP_404_NOT_FOUND
            )


from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import razorpay
from django.conf import settings
import json


@csrf_exempt
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def verify_payment(request):
    if request.method == "POST":
        try:
            razorpay_payment_id = request.data.get("razorpay_payment_id")
            razorpay_order_id = request.data.get("razorpay_order_id")
            razorpay_signature = request.data.get("razorpay_signature")            # Initialize Razorpay client with your secret key
            client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

            # Verify the payment signature
            params_dict = {
                "razorpay_order_id": razorpay_order_id,
                "razorpay_payment_id": razorpay_payment_id,
                "razorpay_signature": razorpay_signature,
            }

            client.utility.verify_payment_signature(params_dict)

            # Get customer and create order from cart items
            customer = models.Customer.objects.get(username=request.user.username)
            cart_items = models.CartItem.objects.filter(user=customer)
            
            if cart_items.exists():
                # Create order
                order = models.Order.objects.create(
                    customer=customer,
                    status="confirmed",
                    payment="online",
                    tracking_number=f"AG{razorpay_payment_id[-8:]}"
                )
                
                # Add cart items to order
                for item in cart_items:
                    order.products.add(item)
                
                order.save()
                
                # Clear cart
                cart_items.delete()

            # If the signature is verified, handle payment success logic here
            return JsonResponse(
                {"success": True, "message": "Payment verified successfully", "order_id": order.id if 'order' in locals() else None}
            )

        except razorpay.errors.SignatureVerificationError:
            return JsonResponse(
                {"success": False, "message": "Payment verification failed"}, status=400
            )
        except Exception as e:
            return JsonResponse({"success": False, "message": str(e)}, status=400)

    # return JsonResponse({"success": False, "message": "Invalid request method"}, status=400)


@permission_classes([IsAuthenticated])
@csrf_exempt
def create_razorpay_order(request):
    if request.method == "POST":
        client = razorpay.Client(
            auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
        )
        try:
            data = json.loads(request.body)
            amount = data.get("amount")
            if not amount or not isinstance(amount, (int, float)):
                return JsonResponse({"error": "Valid amount is required"}, status=400)

            amount_in_paise = int(amount * 100)
            order = client.order.create(
                {
                    "amount": amount_in_paise,
                    "currency": "INR",
                    "payment_capture": "1",
                }
            )

            ic(order)
            return JsonResponse(
                {
                    "order_id": order["id"],
                    "key": settings.RAZORPAY_KEY_ID,
                    "amount": order["amount"],
                    "currency": order["currency"],
                }
            )

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
    return JsonResponse({"error": "Invalid method"}, status=405)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def create_cod_order(request):
    if request.method == "POST":
        try:
            customer = models.Customer.objects.get(username=request.user.username)
            cart_items = models.CartItem.objects.filter(user=customer)
            
            if not cart_items.exists():
                return JsonResponse({"success": False, "message": "Cart is empty"}, status=400)
            
            # Create order
            order = models.Order.objects.create(
                customer=customer,
                status="pending",
                payment="cod",
                tracking_number=f"AG{random.randint(10000000, 99999999)}"
            )
            
            # Add cart items to order
            for item in cart_items:
                order.products.add(item)
            
            order.save()
            
            # Clear cart
            cart_items.delete()

            return JsonResponse({
                "success": True, 
                "message": "Order placed successfully", 
                "order_id": order.id
            })

        except models.Customer.DoesNotExist:
            return JsonResponse({"success": False, "message": "Customer not found"}, status=404)
        except Exception as e:
            return JsonResponse({"success": False, "message": str(e)}, status=500)
    
    return JsonResponse({"success": False, "message": "Invalid method"}, status=405)

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def user_orders(request):
    """Get all orders for the authenticated user"""
    if request.method == "GET":
        try:
            customer = models.Customer.objects.get(username=request.user.username)
            orders = models.Order.objects.filter(customer=customer).exclude(status="not_placed").order_by('-created_at')
            serializer = serializers.OrderSerializer(orders, many=True)
            return Response(serializer.data)
        except models.Customer.DoesNotExist:
            return Response({"error": "Customer not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["POST"])
@permission_classes([IsAdminUser])
def update_order_tracking(request):
    """Admin endpoint to update order tracking information"""
    try:
        order_id = request.data.get("order_id")
        tracking_number = request.data.get("tracking_number")
        carrier = request.data.get("carrier")
        
        if not order_id:
            return Response({"error": "Order ID is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        order = models.Order.objects.get(id=order_id)
        
        if tracking_number:
            order.tracking_number = tracking_number
        if carrier:
            order.carrier = carrier
            
        order.save()
        
        return Response({
            "success": True,
            "message": "Order tracking updated successfully",
            "order_id": order.id,
            "tracking_number": order.tracking_number,
            "carrier": order.carrier
        })
        
    except models.Order.DoesNotExist:
        return Response({"error": "Order not found"}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ====================== WISHLIST VIEWS ======================

@api_view(["GET", "POST", "DELETE"])
@permission_classes([IsAuthenticated])
def wishlist(request):
    """
    GET: Get user's wishlist
    POST: Add product to wishlist
    DELETE: Remove product from wishlist
    """
    user = models.Customer.objects.get(username=request.user.username)
    
    if request.method == "GET":
        try:
            wishlist_items = models.Wishlist.objects.filter(user=user).order_by('-created_at')
            serializer = serializers.WishlistSerializer(wishlist_items, many=True)
            return Response({
                "success": True,
                "wishlist": serializer.data,
                "count": len(serializer.data)
            })
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    elif request.method == "POST":
        try:
            product_id = request.data.get('product_id')
            if not product_id:
                return Response({"error": "Product ID is required"}, status=status.HTTP_400_BAD_REQUEST)
            
            product = models.Product.objects.get(id=product_id)
            
            # Check if already in wishlist
            if models.Wishlist.objects.filter(user=user, product=product).exists():
                return Response({"message": "Product already in wishlist"}, status=status.HTTP_200_OK)
            
            # Add to wishlist
            wishlist_item = models.Wishlist.objects.create(user=user, product=product)
            serializer = serializers.WishlistSerializer(wishlist_item)
            return Response({
                "success": True,
                "message": "Product added to wishlist",
                "wishlist_item": serializer.data
            }, status=status.HTTP_201_CREATED)
            
        except models.Product.DoesNotExist:
            return Response({"error": "Product not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    elif request.method == "DELETE":
        try:
            product_id = request.data.get('product_id')
            if not product_id:
                return Response({"error": "Product ID is required"}, status=status.HTTP_400_BAD_REQUEST)
            
            product = models.Product.objects.get(id=product_id)
            wishlist_item = models.Wishlist.objects.get(user=user, product=product)
            wishlist_item.delete()
            
            return Response({
                "success": True,
                "message": "Product removed from wishlist"
            })
            
        except models.Product.DoesNotExist:
            return Response({"error": "Product not found"}, status=status.HTTP_404_NOT_FOUND)
        except models.Wishlist.DoesNotExist:
            return Response({"error": "Product not in wishlist"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def add_to_wishlist(request):
    """Add a product to user's wishlist"""
    try:
        user = models.Customer.objects.get(username=request.user.username)
        product_id = request.data.get('product_id')
        
        if not product_id:
            return Response({"error": "Product ID is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        product = models.Product.objects.get(id=product_id)
        
        # Check if already in wishlist
        if models.Wishlist.objects.filter(user=user, product=product).exists():
            return Response({"message": "Product already in wishlist"})
        
        # Add to wishlist
        wishlist_item = models.Wishlist.objects.create(user=user, product=product)
        return Response({
            "success": True,
            "message": "Product added to wishlist successfully"
        }, status=status.HTTP_201_CREATED)
        
    except models.Product.DoesNotExist:
        return Response({"error": "Product not found"}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def remove_from_wishlist(request, product_id):
    """Remove a product from user's wishlist"""
    try:
        user = models.Customer.objects.get(username=request.user.username)
        product = models.Product.objects.get(id=product_id)
        
        wishlist_item = models.Wishlist.objects.get(user=user, product=product)
        wishlist_item.delete()
        
        return Response({
            "success": True,
            "message": "Product removed from wishlist successfully"
        })
        
    except models.Product.DoesNotExist:
        return Response({"error": "Product not found"}, status=status.HTTP_404_NOT_FOUND)
    except models.Wishlist.DoesNotExist:
        return Response({"error": "Product not in wishlist"}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def check_wishlist_status(request, product_id):
    """Check if a product is in user's wishlist"""
    try:
        user = models.Customer.objects.get(username=request.user.username)
        product = models.Product.objects.get(id=product_id)
        
        is_in_wishlist = models.Wishlist.objects.filter(user=user, product=product).exists()
        
        return Response({
            "success": True,
            "is_in_wishlist": is_in_wishlist
        })
        
    except models.Product.DoesNotExist:
        return Response({"error": "Product not found"}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ====================== NEWSLETTER SUBSCRIPTION ======================

@api_view(["POST"])
@permission_classes([AllowAny])
def newsletter_subscription(request):
    """Subscribe to newsletter"""
    try:
        email = request.data.get('email')
        if not email:
            return Response({'error': 'Email is required'}, status=400)
        
        # Check if email already exists
        if models.Subscription.objects.filter(email=email).exists():
            return Response({'error': 'Email already subscribed'}, status=400)
        
        # Create subscription
        subscription = models.Subscription.objects.create(email=email)
        
        # Send confirmation email (optional)
        try:
            from django.core.mail import send_mail
            send_mail(
                'Newsletter Subscription Confirmed',
                f'Thank you for subscribing to our newsletter! You will now receive updates about our latest products and offers.',
                settings.EMAIL_HOST_USER,
                [email],
                fail_silently=False,
            )
        except Exception as e:
            print(f"Email sending failed: {e}")
        
        return Response({'success': True, 'message': 'Successfully subscribed to newsletter'})
    except Exception as e:
        return Response({'error': str(e)}, status=500)

@api_view(["DELETE"])
@permission_classes([AllowAny])
def newsletter_unsubscribe(request):
    """Unsubscribe from newsletter"""
    try:
        email = request.data.get('email')
        if not email:
            return Response({'error': 'Email is required'}, status=400)
        
        subscription = models.Subscription.objects.filter(email=email).first()
        if not subscription:
            return Response({'error': 'Email not found in subscription list'}, status=404)
        
        subscription.delete()
        return Response({'success': True, 'message': 'Successfully unsubscribed from newsletter'})
    except Exception as e:
        return Response({'error': str(e)}, status=500)

# ====================== AUTOMATED EMAIL NOTIFICATIONS ======================

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def send_order_update_email(request):
    """Send order update email to customer"""
    try:
        order_id = request.data.get('order_id')
        if not order_id:
            return Response({'error': 'Order ID is required'}, status=400)
        
        order = models.Order.objects.get(id=order_id)
        
        # Get the first item for email template
        first_item = order.products.first()
        product_name = first_item.product.name if first_item else "Your order"
        
        # Send email notification
        from .needs import send_email
        from django.utils import timezone
        send_email(
            to_email=order.customer.email,
            subject=f"Order Update - {order.status.replace('_', ' ').title()}",
            username=order.customer.first_name or order.customer.username,
            product_name=product_name,
            quantity=order.total_products,
            price=f"₹{first_item.price}" if first_item else "N/A",
            total=f"₹{order.cart_total}",
            address=f"{order.shipping_address.address}, {order.shipping_address.city}" if order.shipping_address else "N/A",
            phone=order.shipping_address.phone if order.shipping_address else "N/A",
            landmark=order.shipping_address.landmark if hasattr(order.shipping_address, 'landmark') and order.shipping_address.landmark else "N/A",
            order_date=order.created_at
        )
        
        return Response({'success': True, 'message': 'Email sent successfully'})
    except models.Order.DoesNotExist:
        return Response({'error': 'Order not found'}, status=404)
    except Exception as e:
        return Response({'error': str(e)}, status=500)

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_order_analytics(request):
    """Get order analytics for admin dashboard"""
    try:
        from django.db.models import Count, Sum, Q
        from datetime import datetime, timedelta
        from django.utils import timezone
        
        # Get date range (last 30 days)
        end_date = timezone.now()
        start_date = end_date - timedelta(days=30)
        
        # Order statistics
        total_orders = models.Order.objects.count()
        recent_orders = models.Order.objects.filter(created_at__gte=start_date).count()
        
        # Revenue statistics
        total_revenue = models.Order.objects.aggregate(
            total=Sum('cart_total')
        )['total'] or 0
        
        recent_revenue = models.Order.objects.filter(
            created_at__gte=start_date
        ).aggregate(
            total=Sum('cart_total')
        )['total'] or 0
        
        # Status breakdown
        status_breakdown = models.Order.objects.values('status').annotate(
            count=Count('id')
        ).order_by('status')
        
        # Top products
        top_products = models.CartItem.objects.values(
            'product__name'
        ).annotate(
            total_quantity=Sum('quantity'),
            total_orders=Count('order', distinct=True)
        ).order_by('-total_quantity')[:5]
        
        return Response({
            'success': True,
            'analytics': {
                'total_orders': total_orders,
                'recent_orders': recent_orders,
                'total_revenue': float(total_revenue),
                'recent_revenue': float(recent_revenue),
                'status_breakdown': list(status_breakdown),
                'top_products': list(top_products)
            }
        })
    except Exception as e:
        return Response({'error': str(e)}, status=500)

# ====================== INVENTORY MANAGEMENT ======================

@api_view(["GET", "POST"])
@permission_classes([IsAdminUser])
def inventory_management(request):
    """Manage product inventory"""
    if request.method == "GET":
        try:
            # Get products with low stock (less than 10)
            low_stock_products = models.Product.objects.filter(stock__lt=10).values(
                'id', 'name', 'stock', 'SKU'
            )
            
            # Get out of stock products
            out_of_stock_products = models.Product.objects.filter(stock=0).values(
                'id', 'name', 'stock', 'SKU'
            )
            
            # Get recent stock movements (if you have a stock movement model)
            recent_orders = models.CartItem.objects.select_related(
                'product', 'order'
            ).filter(
                order__created_at__gte=timezone.now() - timedelta(days=7)
            ).values(
                'product__name', 'quantity', 'order__created_at', 'order__status'
            ).order_by('-order__created_at')[:20]
            
            return Response({
                'success': True,
                'inventory': {
                    'low_stock_products': list(low_stock_products),
                    'out_of_stock_products': list(out_of_stock_products),
                    'recent_orders': list(recent_orders)
                }
            })
        except Exception as e:
            return Response({'error': str(e)}, status=500)
    
    elif request.method == "POST":
        try:
            # Update product stock
            product_id = request.data.get('product_id')
            new_stock = request.data.get('stock')
            
            if not product_id or new_stock is None:
                return Response({'error': 'Product ID and stock are required'}, status=400)
            
            product = models.Product.objects.get(id=product_id)
            old_stock = product.stock
            product.stock = new_stock
            product.save()
            
            return Response({
                'success': True,
                'message': f'Stock updated for {product.name} from {old_stock} to {new_stock}'
            })
        except models.Product.DoesNotExist:
            return Response({'error': 'Product not found'}, status=404)
        except Exception as e:
            return Response({'error': str(e)}, status=500)

@api_view(["POST"])
@permission_classes([IsAdminUser])
def bulk_inventory_update(request):
    """Bulk update inventory for multiple products"""
    try:
        updates = request.data.get('updates', [])
        
        if not updates:
            return Response({'error': 'No updates provided'}, status=400)
        
        updated_count = 0
        for update in updates:
            try:
                product = models.Product.objects.get(id=update['product_id'])
                product.stock = update['stock']
                product.save()
                updated_count += 1
            except (models.Product.DoesNotExist, KeyError):
                continue
        
        return Response({
            'success': True,
            'message': f'Successfully updated {updated_count} products'
        })
    except Exception as e:
        return Response({'error': str(e)}, status=500)
