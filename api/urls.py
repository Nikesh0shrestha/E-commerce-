from django.urls import path

from api.views.product_views import (
    ProductListView,
    ProductDetailView,
)

from api.views.account_views import (
    LoginAPIView,
    RegisterView,
    UserProfileView,
    FullProfileView,
)

from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

from api.views.cart_views import (
    AddToCartAPIView,
    CartAPIView,
    RemoveCartAPIView,
    CheckoutAPIView,
)

urlpatterns = [

    # =========================
    # PRODUCT APIs
    # =========================

    path('products/',ProductListView.as_view(),name='product_list'),

    path('products/<int:product_id>/',ProductDetailView.as_view(),name='product_detail'),

    # =========================
    # ACCOUNT APIs
    # =========================

    # Register API
    path('accounts/register/',RegisterView.as_view(),name='api_register'),

    # Login API
    path('accounts/login/',LoginAPIView.as_view(),name='api_login'),

    # Refresh JWT Token
    path('accounts/token/refresh/',TokenRefreshView.as_view(),name='token_refresh'),

    # User Profile API
    path('accounts/profile/',UserProfileView.as_view(),name='profile'),

    # Full Profile API
    path('accounts/full-profile/',FullProfileView.as_view(),name='full_profile'),


    # =========================
    # CART APIs
    # =========================

    path('products/cart/list/', CartAPIView.as_view(), name='cart'),

    path('products/cart/add/<int:product_id>/', AddToCartAPIView.as_view(), name='add-to-cart'),

    path('products/cart/list/remove/<int:cart_item_id>/', RemoveCartAPIView.as_view(), name='remove-cart-item'),

    # path('products/cart/delete/<int:cart_item_id>/', RemoveCartItemAPIView.as_view(), name='delete-cart-item'),

    path('products/checkout/', CheckoutAPIView.as_view(), name='checkout'),

]