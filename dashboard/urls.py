from django.urls import path
from . import views

urlpatterns = [
    path('', views.analytics_dashboard, name='analytics_dashboard'),
    path('sales/', views.sales_chart, name='sales_chart'),
    path('recommend/<int:product_id>/', views.recommendations, name='recommendations'),
]