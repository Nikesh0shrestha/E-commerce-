# from django.contrib import admin
# from .models import Product, Variation, ReviewRating, ProductGallery
# import admin_thumbnails
# from accounts.models import Account

# @admin_thumbnails.thumbnail('image')
# class ProductGalleryInline(admin.TabularInline):
#     model = ProductGallery
#     extra = 1

# class ProductAdmin(admin.ModelAdmin):
#     list_display = ('product_name', 'price', 'stock', 'category', 'modified_date', 'is_available')
#     prepopulated_fields = {'slug': ('product_name',)}
#     inlines = [ProductGalleryInline]

#     # This filters the dropdown in the Admin Panel
#     def formfield_for_foreignkey(self, db_field, request, **kwargs):
#         if db_field.name == "supplier":
#             # Only show users whose role is 'supplier'
#             kwargs["queryset"] = Account.objects.filter(role='supplier')
#         return super().formfield_for_foreignkey(db_field, request, **kwargs)

# class VariationAdmin(admin.ModelAdmin):
#     list_display = ('product', 'variation_category', 'variation_value', 'is_active')
#     list_editable = ('is_active',)
#     list_filter = ('product', 'variation_category', 'variation_value')

# admin.site.register(Product, ProductAdmin)
# admin.site.register(Variation, VariationAdmin)
# admin.site.register(ReviewRating)
# admin.site.register(ProductGallery)


from django.contrib import admin
from django.contrib.admin import AdminSite
from django.urls import path
from django.http import JsonResponse
from django.db.models import Count, Sum
from django.db.models.functions import TruncDate
from django.utils.html import format_html

from .models import Product, Variation, ReviewRating, ProductGallery
from orders.models import Order

from django.db.models import Count, Sum, Avg
from django.contrib.auth.models import User

import pandas as pd
from django.http import HttpResponse
from reportlab.platypus import SimpleDocTemplate, Paragraph

# 🔥 Inline for Product Gallery
class ProductGalleryInline(admin.TabularInline):
    model = ProductGallery
    extra = 1


# 🔥 Inline for Variations
class VariationInline(admin.TabularInline):
    model = Variation
    extra = 1


# 🔥 Product Admin
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        'product_name',
        'price',
        'stock',
        'category',
        'is_available',
        'supplier',
        'image_preview',
        'created_date'
    )

    list_filter = ('is_available', 'category', 'created_date', 'supplier')
    search_fields = ('product_name', 'description')
    prepopulated_fields = {'slug': ('product_name',)}
    ordering = ('-created_date',)

    readonly_fields = ('created_date', 'modified_date', 'image_preview')

    inlines = [ProductGalleryInline, VariationInline]

    fieldsets = (
        ('📦 Product Info', {
            'fields': ('product_name', 'slug', 'description', 'category')
        }),
        ('💰 Pricing & Stock', {
            'fields': ('price', 'stock', 'is_available')
        }),
        ('🖼️ Images', {
            'fields': ('images', 'image_preview')
        }),
        ('👤 Supplier Info', {
            'fields': ('supplier',)
        }),
        ('📅 Dates', {
            'fields': ('created_date', 'modified_date')
        }),
    )

    def image_preview(self, obj):
        if obj.images:
            return format_html('<img src="{}" width="60" />', obj.images.url)
        return "No Image"

    image_preview.short_description = "Preview"


# 🔥 Variation Admin
class VariationAdmin(admin.ModelAdmin):
    list_display = ('product', 'variation_category', 'variation_value', 'is_active')
    list_filter = ('variation_category', 'is_active')
    search_fields = ('product__product_name', 'variation_value')


# 🔥 Review Admin
class ReviewRatingAdmin(admin.ModelAdmin):
    list_display = ('product', 'user', 'rating', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('product__product_name', 'user__email')
    readonly_fields = ('created_at', 'updated_at')


# 🔥 Product Gallery Admin
class ProductGalleryAdmin(admin.ModelAdmin):
    list_display = ('product', 'image')


# ==============================
# 📊 DASHBOARD ANALYTICS API
# ==============================

# def dashboard_data(request):

#     # 1. Products per category
#     category_data = Product.objects.values('category__category_name')\
#         .annotate(count=Count('id'))

#     # 2. Stock status (FIXED)
#     available = Product.objects.filter(is_available=True).count()
#     out_of_stock = Product.objects.filter(is_available=False).count()

#     # 3. Orders per day
#     order_data = Order.objects.annotate(date=TruncDate('created_at'))\
#         .values('date').annotate(count=Count('id'))

#     # 4. Revenue per day
#     revenue_data = Order.objects.annotate(date=TruncDate('created_at'))\
#         .values('date').annotate(total=Sum('order_total'))

#     return JsonResponse({
#         "category": {
#             "labels": [i['category__category_name'] for i in category_data],
#             "counts": [i['count'] for i in category_data],
#         },
#         "stock": {
#             "labels": ["Available", "Out of Stock"],
#             "counts": [available, out_of_stock],
#         },
#         "orders": {
#             "labels": [str(i['date']) for i in order_data],
#             "counts": [i['count'] for i in order_data],
#         },
#         "revenue": {
#             "labels": [str(i['date']) for i in revenue_data],
#             "amounts": [float(i['total'] or 0) for i in revenue_data],
#         }
#     })
def export_excel(request):
    data = Order.objects.all().values()
    df = pd.DataFrame(data)

    response = HttpResponse(content_type='application/vnd.ms-excel')
    response['Content-Disposition'] = 'attachment; filename=report.xlsx'

    df.to_excel(response, index=False)
    return response

def export_pdf(request):
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename=report.pdf'

    doc = SimpleDocTemplate(response)
    elements = []

    orders = Order.objects.all()[:10]

    for order in orders:
        elements.append(Paragraph(f"Order {order.id} - Rs {order.order_total}", None))

    doc.build(elements)
    return response

def dashboard_data(request):

    # 📅 Date filter
    start_date = request.GET.get('start')
    end_date = request.GET.get('end')

    orders = Order.objects.all()

    if start_date and end_date:
        orders = orders.filter(created_at__date__range=[start_date, end_date])

    # =========================
    # 📊 KPI CARDS
    # =========================
    total_orders = orders.count()
    total_revenue = orders.aggregate(total=Sum('order_total'))['total'] or 0
    total_users = User.objects.count()

    # =========================
    # 📦 CATEGORY CHART
    # =========================
    category_data = Product.objects.values('category__category_name')\
        .annotate(count=Count('id'))

    # =========================
    # 📈 ORDERS CHART
    # =========================
    order_data = orders.annotate(date=TruncDate('created_at'))\
        .values('date').annotate(count=Count('id'))

    # =========================
    # 💰 REVENUE CHART
    # =========================
    revenue_data = orders.annotate(date=TruncDate('created_at'))\
        .values('date').annotate(total=Sum('order_total'))

    # =========================
    # ⭐ TOP RATED PRODUCTS
    # =========================
    top_products = ReviewRating.objects.values('product__product_name')\
        .annotate(avg_rating=Avg('rating'))\
        .order_by('-avg_rating')[:5]

    # =========================
    # 🤖 RECOMMENDATION ANALYTICS
    # =========================
    recommended = ReviewRating.objects.values('product__product_name')\
        .annotate(total=Count('id'))\
        .order_by('-total')[:5]

    # =========================
    # 📦 LOW STOCK ALERT
    # =========================
    low_stock_products = Product.objects.filter(stock__lt=5)\
        .values('product_name', 'stock')

    # =========================
    # 🔄 RESPONSE
    # =========================
    return JsonResponse({

        # KPI
        "kpi": {
            "orders": total_orders,
            "revenue": float(total_revenue),
            "users": total_users,
        },

        # Charts
        "category": {
            "labels": [i['category__category_name'] for i in category_data],
            "counts": [i['count'] for i in category_data],
        },

        "orders_chart": {
            "labels": [str(i['date']) for i in order_data],
            "counts": [i['count'] for i in order_data],
        },

        "revenue_chart": {
            "labels": [str(i['date']) for i in revenue_data],
            "amounts": [float(i['total'] or 0) for i in revenue_data],
        },

        # ⭐ Top Rated
        "top_products": {
            "labels": [i['product__product_name'] for i in top_products],
            "ratings": [float(i['avg_rating']) for i in top_products],
        },

        # 🤖 Recommended
        "recommended": {
            "labels": [i['product__product_name'] for i in recommended],
            "counts": [i['total'] for i in recommended],
        },

        # 📦 Low Stock
        "low_stock": [
            {
                "name": i['product_name'],
                "stock": i['stock']
            }
            for i in low_stock_products
        ]

    })


# ==============================
# 🔧 CUSTOM ADMIN SITE
# ==============================

class CustomAdminSite(AdminSite):
    site_header = "ShopSphere Admin"
    site_title = "ShopSphere Dashboard"
    index_title = "Analytics Dashboard"

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('dashboard-data/', self.admin_view(dashboard_data)),
            path('export-excel/', self.admin_view(export_excel)),
            path('export-pdf/', self.admin_view(export_pdf)),
        ]
        return custom_urls + urls


# 🔥 Create admin instance
admin_site = CustomAdminSite(name='custom_admin')


# ==============================
# ✅ REGISTER MODELS HERE
# ==============================

admin_site.register(Product, ProductAdmin)
admin_site.register(Variation, VariationAdmin)
admin_site.register(ReviewRating, ReviewRatingAdmin)
admin_site.register(ProductGallery, ProductGalleryAdmin)