# from rest_framework.views import APIView
# from rest_framework.response import Response
# from rest_framework import status, permissions

# from django.shortcuts import get_object_or_404

# from carts.models import CartItem
# from store.models import Product, Variation

# from api.serializers.cart_serializer import CartItemSerializer


# # =========================
# # ADD TO CART
# # =========================
# class AddToCartAPIView(APIView):

#     permission_classes = [permissions.IsAuthenticated]

#     def post(self, request, product_id):

#         user = request.user

#         # Role restriction
#         if user.role in ['admin', 'supplier']:
#             return Response({
#                 "error": "Admins and suppliers cannot shop"
#             }, status=status.HTTP_403_FORBIDDEN)

#         product = get_object_or_404(Product, id=product_id)

#         # Get variations
#         product_variation = []

#         for key, value in request.data.items():

#             try:
#                 variation = Variation.objects.get(
#                     product=product,
#                     variation_category__iexact=key,
#                     variation_value__iexact=value
#                 )

#                 product_variation.append(variation)

#             except Variation.DoesNotExist:
#                 pass

#         # Check existing cart item
#         cart_items = CartItem.objects.filter(
#             product=product,
#             user=user
#         )

#         exists = False

#         for item in cart_items:

#             existing_variations = list(item.variations.all())

#             if existing_variations == product_variation:
#                 item.quantity += 1
#                 item.save()

#                 serializer = CartItemSerializer(item)

#                 return Response(serializer.data)

#         # Create new cart item
#         cart_item = CartItem.objects.create(
#             product=product,
#             quantity=1,
#             user=user
#         )

#         if product_variation:
#             cart_item.variations.add(*product_variation)

#         serializer = CartItemSerializer(cart_item)

#         return Response(serializer.data, status=status.HTTP_201_CREATED)


# class CartAPIView(APIView):

#     permission_classes = [permissions.IsAuthenticated]

#     def get(self, request):

#         cart_items = CartItem.objects.filter(
#             user=request.user,
#             is_active=True
#         )

#         serializer = CartItemSerializer(
#             cart_items,
#             many=True
#         )

#         total = 0
#         quantity = 0

#         for item in cart_items:
#             total += item.product.price * item.quantity
#             quantity += item.quantity

#         tax = (2 * total) / 100
#         grand_total = total + tax

#         return Response({
#             "cart_items": serializer.data,
#             "total": total,
#             "quantity": quantity,
#             "tax": tax,
#             "grand_total": grand_total
#         })


# class RemoveCartAPIView(APIView):

#     permission_classes = [permissions.IsAuthenticated]

#     def delete(self, request, cart_item_id):

#         try:
#             cart_item = CartItem.objects.get(
#                 id=cart_item_id,
#                 user=request.user
#             )

#             if cart_item.quantity > 1:
#                 cart_item.quantity -= 1
#                 cart_item.save()

#             else:
#                 cart_item.delete()

#             return Response({
#                 "message": "Cart updated"
#             })

#         except CartItem.DoesNotExist:
#             return Response({
#                 "error": "Cart item not found"
#             }, status=status.HTTP_404_NOT_FOUND)
# class RemoveCartItemAPIView(APIView):

#     permission_classes = [permissions.IsAuthenticated]

#     def delete(self, request, cart_item_id):

#         try:
#             cart_item = CartItem.objects.get(
#                 id=cart_item_id,
#                 user=request.user
#             )

#             cart_item.delete()

#             return Response({
#                 "message": "Item removed from cart"
#             })

#         except CartItem.DoesNotExist:
#             return Response({
#                 "error": "Cart item not found"
#             }, status=status.HTTP_404_NOT_FOUND)

# class CheckoutAPIView(APIView):

#     permission_classes = [permissions.IsAuthenticated]

#     def get(self, request):

#         cart_items = CartItem.objects.filter(
#             user=request.user,
#             is_active=True
#         )

#         serializer = CartItemSerializer(
#             cart_items,
#             many=True
#         )

#         total = 0
#         quantity = 0

#         for item in cart_items:
#             total += item.product.price * item.quantity
#             quantity += item.quantity

#         tax = (2 * total) / 100
#         grand_total = total + tax

#         return Response({
#             "checkout_items": serializer.data,
#             "total": total,
#             "quantity": quantity,
#             "tax": tax,
#             "grand_total": grand_total
#         })



from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions

from django.shortcuts import get_object_or_404

from carts.models import *
from store.models import Product, Variation
from api.serializers.cart_serializer import CartItemSerializer


# =========================
# ADD TO CART
# =========================
class AddToCartAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, product_id):
        user = request.user

        # restrict roles
        if user.role in ['admin', 'supplier']:
            return Response(
                {"error": "Admins and suppliers cannot shop"},
                status=status.HTTP_403_FORBIDDEN
            )

        if not request.data:
            return Response(
                {"error": "Request body cannot be empty"},
                status=status.HTTP_400_BAD_REQUEST
            )

        product = get_object_or_404(Product, id=product_id)

        # create or get cart
        cart, _ = Cart.objects.get_or_create(cart_id=str(user.id))

        # get variations
        product_variation = []
        for key, value in request.data.items():
            if key in ["quantity"]:  
                continue
            try:
                variation = Variation.objects.get(
                    product=product,
                    variation_category__iexact=key,
                    variation_value__iexact=value,
                )
                product_variation.append(variation)
            except Variation.DoesNotExist:
                pass

        # get requested quantity (default to 1 if not provided)
        quantity = int(request.data.get("quantity", 1))


        if quantity < 1:
            return Response(
                {"error": "Quantity must be at least 1"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # check existing cart items
        cart_items = CartItem.objects.filter(
            product=product,
            user=user,
            is_active=True
        )

        for item in cart_items:
            existing_variations = list(item.variations.all())
            if set(existing_variations) == set(product_variation):
                # increment by requested quantity
                item.quantity += quantity
                item.save()
                serializer = CartItemSerializer(item)
                return Response(serializer.data)

        # create new cart item with requested quantity
        cart_item = CartItem.objects.create(
            product=product,
            user=user,
            cart=cart,
            quantity=quantity
        )

        if product_variation:
            cart_item.variations.add(*product_variation)

        cart_item = CartItem.objects.prefetch_related('variations').get(id=cart_item.id)
        serializer = CartItemSerializer(cart_item)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


# =========================
# CART LIST + TOTAL
# =========================
class CartAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):

        cart_items = CartItem.objects.filter(
            user=request.user,
            is_active=True
        )

        serializer = CartItemSerializer(cart_items, many=True)

        total = 0
        quantity = 0

        for item in cart_items:
            total += item.sub_total()
            quantity += item.quantity

        tax = (2 * total) / 100
        grand_total = total + tax

        return Response({
            "cart_items": serializer.data,
            "total": total,
            "quantity": quantity,
            "tax": tax,
            "grand_total": grand_total
        })


# =========================
# DECREASE QUANTITY
# =========================
class RemoveCartAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, cart_item_id):
        cart_item = get_object_or_404(
            CartItem,
            id=cart_item_id,
            user=request.user
        )
        serializer = CartItemSerializer(cart_item)
        return Response(serializer.data)

    def delete(self, request, cart_item_id):

        cart_item = get_object_or_404(
            CartItem,
            id=cart_item_id,
            user=request.user
        )

        if cart_item.quantity > 1:
            cart_item.quantity -= 1
            cart_item.save()
        else:
            cart_item.delete()

        return Response({"message": "Cart updated"})


# =========================
# DELETE ITEM COMPLETELY
# =========================
# class RemoveCartItemAPIView(APIView):
#     permission_classes = [permissions.IsAuthenticated]

#     def delete(self, request, cart_item_id):

#         cart_item = get_object_or_404(
#             CartItem,
#             id=cart_item_id,
#             user=request.user
#         )

#         cart_item.delete()

#         return Response({"message": "Item removed from cart"})


# =========================
# CHECKOUT
# =========================
class CheckoutAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):

        cart_items = CartItem.objects.filter(
            user=request.user,
            is_active=True
        )

        serializer = CartItemSerializer(cart_items, many=True)

        total = sum(item.sub_total() for item in cart_items)
        quantity = sum(item.quantity for item in cart_items)

        tax = (2 * total) / 100
        grand_total = total + tax

        return Response({
            "checkout_items": serializer.data,
            "total": total,
            "quantity": quantity,
            "tax": tax,
            "grand_total": grand_total
        })