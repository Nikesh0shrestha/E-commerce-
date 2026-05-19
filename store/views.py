from django.shortcuts import render, get_object_or_404, redirect
from .models import  ReviewRating, ProductGallery
from category.models import Category
from carts.models import CartItem
from django.db.models import Q

from carts.views import _cart_id
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.http import HttpResponse
from .forms import ReviewForm
from django.contrib import messages
from orders.models import OrderProduct


from .models import Product, Variation
# Change line 13 to this:
from .recommendations import get_knn_recommendations

from django.db.models import Avg, Count, F, FloatField, ExpressionWrapper, Q


def store(request, category_slug=None):
    categories = None
    products = None

    if category_slug != None:
        categories = get_object_or_404(Category, slug=category_slug)
        products = Product.objects.filter(category=categories, is_available=True)
        paginator = Paginator(products, 1)
        page = request.GET.get('page')
        paged_products = paginator.get_page(page)
        product_count = products.count()
    else:
        products = Product.objects.all().filter(is_available=True).order_by('id')
        paginator = Paginator(products, 3)
        page = request.GET.get('page')
        paged_products = paginator.get_page(page)
        product_count = products.count()

    recommended = get_top_rated_products()[:4]


    context = {
        'products': paged_products,
        'product_count': product_count,
        'recommended': recommended,
    }
    return render(request, 'store/store.html', context)


# def product_detail(request, category_slug, product_slug):
#     try:
#         single_product = Product.objects.get(category__slug=category_slug, slug=product_slug)
#         in_cart = CartItem.objects.filter(cart__cart_id=_cart_id(request), product=single_product).exists()
#     except Exception as e:
#         raise e

#     if request.user.is_authenticated:
#         try:
#             orderproduct = OrderProduct.objects.filter(user=request.user, product_id=single_product.id).exists()
#         except OrderProduct.DoesNotExist:
#             orderproduct = None
#     else:
#         orderproduct = None

#     # Get the reviews
#     reviews = ReviewRating.objects.filter(product_id=single_product.id, status=True)

#     # Get the product gallery
#     product_gallery = ProductGallery.objects.filter(product_id=single_product.id)

#     # Content-based similar products (same category preferred for fallback)
#     similar_products = get_similar_products(single_product, max_results=6)
#     if not similar_products:
#         # Fallback: same category, exclude current
#         similar_products = list(
#             Product.objects.filter(category=single_product.category, is_available=True)
#             .exclude(pk=single_product.pk)[:6]
#         )
#     top_rated = get_top_rated_products().exclude(id=single_product.id)[:4]

#     context = {
#         'single_product': single_product,
#         'in_cart'       : in_cart,
#         'orderproduct': orderproduct,
#         'reviews': reviews,
#         'product_gallery': product_gallery,
#         'similar_products': similar_products,
#         'top_rated': top_rated,
#     }
#     return render(request, 'store/product_detail.html', context)


def product_detail(request, category_slug, product_slug):
    try:
        # Get the specific product
        single_product = Product.objects.get(
            category__slug=category_slug,
            slug=product_slug
        )

        # Check if product is already in cart
        in_cart = CartItem.objects.filter(
            cart__cart_id=_cart_id(request),
            product=single_product
        ).exists()

    except Exception as e:
        raise e

    # =========================
    # PRODUCT VARIATIONS
    # =========================

    color_variation = Variation.objects.filter(
        product=single_product,
        variation_category__iexact='color',
        is_active=True
    )

    size_variation = Variation.objects.filter(
        product=single_product,
        variation_category__iexact='size',
        is_active=True
    )

    # =========================
    # ORDER CHECK
    # =========================

    orderproduct = None

    if request.user.is_authenticated:
        orderproduct = OrderProduct.objects.filter(
            user=request.user,
            product_id=single_product.id
        ).exists()

    else:
        orderproduct = False

    # =========================
    # REVIEWS
    # =========================

    reviews = ReviewRating.objects.filter(
        product_id=single_product.id,
        status=True
    )

    # =========================
    # GALLERY
    # =========================

    product_gallery = ProductGallery.objects.filter(
        product_id=single_product.id
    )

    # =========================
    # RECOMMENDATIONS
    # =========================

    similar_products = get_knn_recommendations(
        single_product.id,
        k=6
    )

    if not similar_products:
        similar_products = Product.objects.filter(
            category=single_product.category,
            is_available=True
        ).exclude(id=single_product.id)[:6]

    top_rated = get_top_rated_products().exclude(
        id=single_product.id
    )[:4]

    # =========================
    # CONTEXT
    # =========================

    context = {
        'single_product': single_product,
        'in_cart': in_cart,
        'orderproduct': orderproduct,
        'reviews': reviews,
        'product_gallery': product_gallery,
        'similar_products': similar_products,
        'top_rated': top_rated,

        # IMPORTANT
        'color_variation': color_variation,
        'size_variation': size_variation,
    }

    return render(request, 'store/product_detail.html', context)
def search(request):
    if 'keyword' in request.GET:
        keyword = request.GET['keyword']
        if keyword:
            products = Product.objects.order_by('-created_date').filter(Q(description__icontains=keyword) | Q(product_name__icontains=keyword))
            product_count = products.count()
    context = {
        'products': products,
        'product_count': product_count,
    }
    return render(request, 'store/store.html', context)


def submit_review(request, product_id):
    url = request.META.get('HTTP_REFERER')
    if request.method == 'POST':
        try:
            reviews = ReviewRating.objects.get(user__id=request.user.id, product__id=product_id)
            form = ReviewForm(request.POST, instance=reviews)
            form.save()
            messages.success(request, 'Thank you! Your review has been updated.')
            return redirect(url)
        except ReviewRating.DoesNotExist:
            form = ReviewForm(request.POST)
            if form.is_valid():
                data = ReviewRating()
                data.subject = form.cleaned_data['subject']
                data.rating = form.cleaned_data['rating']
                data.review = form.cleaned_data['review']
                data.ip = request.META.get('REMOTE_ADDR')
                data.product_id = product_id
                data.user_id = request.user.id
                data.save()
                messages.success(request, 'Thank you! Your review has been submitted.')
                return redirect(url)


def get_top_rated_products():
    C = ReviewRating.objects.filter(status=True).aggregate(avg=Avg('rating'))['avg'] or 0
    m = 5  # minimum reviews threshold

    return Product.objects.filter(is_available=True).annotate(
        R=Avg('reviews__rating', filter=Q(reviews__status=True)),
        v=Count('reviews', filter=Q(reviews__status=True))
    ).annotate(
        score=ExpressionWrapper(
            (F('v')/(F('v')+m))*F('R') + (m/(F('v')+m))*C,
            output_field=FloatField()
        )
    ).order_by('-score')
