from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from carts.models import CartItem
from orders.models import Order, OrderProduct


class CreateOrderView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        cart_items = CartItem.objects.filter(user=request.user)

        if not cart_items.exists():
            return Response({"error": "Cart is empty"})

        order = Order.objects.create(
            user=request.user,
            first_name=request.user.first_name,
            last_name=request.user.last_name,
            phone="",
            email=request.user.email,
            address_line_1="",
            country="",
            state="",
            city="",
            order_total=0,
            tax=0
        )

        total = 0

        for item in cart_items:
            total += item.product.price * item.quantity

            OrderProduct.objects.create(
                order=order,
                user=request.user,
                product=item.product,
                quantity=item.quantity,
                product_price=item.product.price
            )

        order.order_total = total
        order.save()

        cart_items.delete()

        return Response({"message": "Order created"})