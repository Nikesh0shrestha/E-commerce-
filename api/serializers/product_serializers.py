from rest_framework import serializers
from store.models import Product, Variation, ReviewRating, ProductGallery


class VariationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Variation
        fields = ['id', 'variation_category', 'variation_value']


class ReviewSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField()

    class Meta:
        model = ReviewRating
        fields = ['id', 'user', 'subject', 'review', 'rating']


class ProductGallerySerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductGallery
        fields = ['id', 'image']


class ProductSerializer(serializers.ModelSerializer):

    variations = VariationSerializer(many=True, read_only=True)
    reviews = ReviewSerializer(many=True, read_only=True)
    gallery = ProductGallerySerializer(many=True, read_only=True)

    average_rating = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            'id',
            'product_name',
            'slug',
            'description',
            'price',
            'images',
            'stock',
            'is_available',
            'category',
            'average_rating',
            'variations',
            'reviews',
            'gallery',
        ]

    def get_average_rating(self, obj):
        return obj.averageReview()