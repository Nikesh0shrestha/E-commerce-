from django.shortcuts import get_object_or_404
from rest_framework.generics import ListAPIView, RetrieveAPIView
from store.models import Product
from api.serializers.product_serializers import ProductSerializer
from rest_framework.permissions import AllowAny
from rest_framework.filters import SearchFilter
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework import status

class ProductListView(ListAPIView):
    permission_classes = [AllowAny]

    # queryset = Product.objects.filter(is_available=True)
    serializer_class = ProductSerializer
    filter_backends = [SearchFilter]
    search_fields = ['product_name', ]
    pagination_class = PageNumberPagination

    def get_queryset(self):
        return Product.objects.filter(is_available=True)

class ProductDetailView(RetrieveAPIView):

    # queryset = Product.objects.filter(is_available=True)
    # serializer_class = ProductSerializer
    # lookup_field = 'slug'

    permission_classes = [AllowAny]

    def get(self, request, product_id):
        product = get_object_or_404(Product, id = product_id, is_available = True)
        serializer = ProductSerializer(product)
        return Response(serializer.data, status=status.HTTP_200_OK)