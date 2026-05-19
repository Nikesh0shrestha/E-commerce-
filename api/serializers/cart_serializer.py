# from rest_framework import serializers
# from carts.models import CartItem
# from store.models import Variation


# class VariationSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Variation
#         fields = ['variation_category', 'variation_value']


# class CartItemSerializer(serializers.ModelSerializer):

#     product_name = serializers.CharField(source='product.product_name')
#     product_price = serializers.DecimalField(
#         source='product.price',
#         max_digits=10,
#         decimal_places=2
#     )

#     variations = VariationSerializer(many=True)

#     subtotal = serializers.SerializerMethodField()

#     class Meta:
#         model = CartItem
#         fields = [
#             'id',
#             'product',
#             'product_name',
#             'product_price',
#             'quantity',
#             'variations',
#             'subtotal',
#         ]

#     def get_subtotal(self, obj):
#         return obj.product.price * obj.quantity   


from rest_framework import serializers
from carts.models import CartItem
from store.models import Variation


class VariationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Variation
        fields = ['variation_category', 'variation_value']


class CartItemSerializer(serializers.ModelSerializer):

    product_name = serializers.CharField(source='product.product_name')
    product_price = serializers.DecimalField(
        source='product.price',
        max_digits=10,
        decimal_places=2
    )

    variations = VariationSerializer(many=True, read_only=True)

    subtotal = serializers.SerializerMethodField()

    class Meta:
        model = CartItem
        fields = [
            'id',
            'product',
            'product_name',
            'product_price',
            'quantity',
            'variations',
            'subtotal',
        ]

    def get_subtotal(self, obj):
        return obj.sub_total()