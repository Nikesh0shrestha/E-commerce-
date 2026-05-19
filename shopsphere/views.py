from django.shortcuts import render
from store.models import Product, ReviewRating
from django.db.models import Avg

# def home(request):
#     products = Product.objects.all().filter(is_available=True).order_by('created_date')

#     # Get the reviews
#     reviews = None
#     for product in products:
#         reviews = ReviewRating.objects.filter(product_id=product.id, status=True)

#     # Logic for Top Rated Products:
#     # We annotate each product with its average rating and order by highest first
#     top_rated_products = Product.objects.filter(is_available=True).annotate(
#         avg_rating=Avg('reviewrating__rating')
#     ).order_by('-avg_rating')[:4] # Limits to top 4 products
#     context = {
#         'products': products,
#         'reviews': reviews,
#         'top_rated_products': top_rated_products,
#     }
#     return render(request, 'home.html', context)


from django.shortcuts import render
from store.models import Product, ReviewRating
from django.db.models import Avg
from store  .recommendations import get_knn_recommendations # Import your KNN function

def home(request):
    # 1. Fetch all available products (ordered by newest)
    products = Product.objects.filter(is_available=True).order_by('-created_date')

    # 2. Logic for Top Rated Products (Global Favorites)
    # We use annotate to calculate the average on the fly
    top_rated_products = Product.objects.filter(is_available=True).annotate(
        avg_rating=Avg('reviews__rating')
    ).filter(avg_rating__isnull=False).order_by('-avg_rating')[:4]

    # 3. Logic for Personalized Recommendations (KNN)
    recommended_products = None
    if request.user.is_authenticated:
        # Get the list of recommended product IDs from your recommendations.py
        recommended_ids = get_knn_recommendations(request.user.id, k=4)
        
        # Fetch the actual product objects for those IDs
        if recommended_ids:
            recommended_products = Product.objects.filter(id__in=recommended_ids)

    context = {
        'products': products,
        'top_rated_products': top_rated_products,
        'recommended_products': recommended_products,
    }
    return render(request, 'home.html', context)