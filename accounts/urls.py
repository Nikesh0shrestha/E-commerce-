from django.urls import path
from . import views


urlpatterns = [
    path('register/', views.register, name='register'),
    path('login/', views.login, name='login'),
    path('logout/', views.logout, name='logout'),

    #Custommer Dashboard 
    path('dashboard/', views.dashboard, name='dashboard'),

    # Admin Dashboard (New)
    path('admin_dashboard/', views.admin_dashboard, name='admin_dashboard'),

    #Suppliers Dashboard 
    path('customer-dashboard/', views.customer_dashboard, name='customer_dashboard'),
    path('supplier_dashboard/', views.supplier_dashboard, name='supplier_dashboard'),

    path('', views.dashboard, name='dashboard'),
    path('supplier_products/', views.supplier_products, name='supplier_products'),

    path('activate/<uidb64>/<token>/', views.activate, name='activate'),
    path('forgotPassword/', views.forgotPassword, name='forgotPassword'),
    path('resetpassword_validate/<uidb64>/<token>/', views.resetpassword_validate, name='resetpassword_validate'),
    path('resetPassword/', views.resetPassword, name='resetPassword'),

    path('my_orders/', views.my_orders, name='my_orders'), # change 

    path('edit_profile/', views.edit_profile, name='edit_profile'),
    path('change_password/', views.change_password, name='change_password'),
    path('order_detail/<int:order_id>/', views.order_detail, name='order_detail'),

    path('add_product/', views.add_product, name='add_product'),
    path('edit_product/<int:product_id>/', views.edit_product, name='edit_product'),
    path('delete_product/<int:product_id>/', views.delete_product, name='delete_product'),

    # path('cash_on_delivery/<str:order_number>/', views.cash_on_delivery, name='cash_on_delivery'),


]
