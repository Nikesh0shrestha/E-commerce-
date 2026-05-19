"""greatkart URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from . import views
from django.conf.urls.static import static
from django.conf import settings
from store.admin import admin_site 

from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

schema_view = get_schema_view(
    openapi.Info(
        title="ShopSphere API",
        default_version='v1',
        description="E-commerce API Documentation",
    ),
    public=True,
    permission_classes=[permissions.AllowAny],
)

urlpatterns = [
     # Fake admin (honeypot)
    path('admin/', include('admin_honeypot.urls', namespace='admin_honeypot')),

    # Real admin (secured)
    path('securelogin/', admin.site.urls),

    # Frontend
    path('', views.home, name='home'),

    # Apps
    path('store/', include('store.urls')),
    path('cart/', include('carts.urls')),   # KEEP ONLY ONE CART PATH
    path('accounts/', include('accounts.urls')),
    path('dashboard/', include('dashboard.urls')),
    path('orders/', include('orders.urls')),

    # API
    path('api/', include('api.urls')),  # KEEP ONLY ONE
    # path('api/cart/', include('carts.api_urls')),

    # JWT Auth
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # Swagger / ReDoc
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='swagger'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='redoc'),


] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

