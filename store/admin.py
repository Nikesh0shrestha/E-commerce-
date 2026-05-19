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
from django.http import JsonResponse, HttpResponse
from django.db.models import Count, Sum, Avg
from django.db.models.functions import TruncDate
from django.utils.html import format_html
from accounts.models import Account

import pandas as pd

# import pandas as pd
from reportlab.platypus import SimpleDocTemplate, Paragraph
from reportlab.lib.styles import getSampleStyleSheet

# MODELS
from .models import Product, Variation, ReviewRating, ProductGallery
from category.models import Category
from accounts.models import Account
from orders.models import Order


# ==============================
# 🔥 INLINE CLASSES
# ==============================

class ProductGalleryInline(admin.TabularInline):
    model = ProductGallery
    extra = 1


class VariationInline(admin.TabularInline):
    model = Variation
    extra = 1


# ==============================
# 🔥 PRODUCT ADMIN
# ==============================

class ProductAdmin(admin.ModelAdmin):
    list_display = (
        'id','product_name', 'price', 'stock', 'category',
        'is_available', 'supplier', 'image_preview', 'created_date'
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


# ==============================
# 🔥 OTHER ADMINS
# ==============================

class VariationAdmin(admin.ModelAdmin):
    list_display = ('product', 'variation_category', 'variation_value', 'is_active')
    list_filter = ('variation_category', 'is_active')
    search_fields = ('product__product_name', 'variation_value')


# class ReviewRatingAdmin(admin.ModelAdmin):
#     list_display = ('product', 'user', 'rating', 'status', 'created_at')
#     list_filter = ('rating', 'created_at')
#     search_fields = ('product__product_name', 'user__email')


class ProductGalleryAdmin(admin.ModelAdmin):
    list_display = ('product', 'image')


class CategoryAdmin(admin.ModelAdmin):
    list_display = ('category_name', 'slug')
    prepopulated_fields = {'slug': ('category_name',)}


class AccountAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'email', 'is_active', 'is_staff')
    list_filter = ('is_active', 'is_staff')
    search_fields = ('first_name', 'last_name', 'email')


class OrderAdmin(admin.ModelAdmin):
    list_display = ('order_number', 'order_total', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('order_number',)

class ReviewRatingAdmin(admin.ModelAdmin):
    list_display = ['product', 'user', 'rating', 'status', 'updated_at']
    list_filter = ['rating', 'status', 'updated_at']
    search_fields = ['product__product_name', 'user__email']

# ==============================
# 📊 EXPORT FUNCTIONS
# ==============================

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


# ==============================
# 📊 DASHBOARD DATA
# ==============================

def dashboard_data(request):

    start_date = request.GET.get('start')
    end_date = request.GET.get('end')

    orders = Order.objects.all()

    if start_date and end_date:
        orders = orders.filter(created_at__date__range=[start_date, end_date])

    total_orders = orders.count()
    total_revenue = orders.aggregate(total=Sum('order_total'))['total'] or 0
    # total_users = User.objects.count()
    total_users = Account.objects.count()

    category_data = Product.objects.values('category__category_name')\
        .annotate(count=Count('id'))

    order_data = orders.annotate(date=TruncDate('created_at'))\
        .values('date').annotate(count=Count('id'))

    revenue_data = orders.annotate(date=TruncDate('created_at'))\
        .values('date').annotate(total=Sum('order_total'))

    top_products = ReviewRating.objects.values('product__product_name')\
        .annotate(avg_rating=Avg('rating')).order_by('-avg_rating')[:5]

    recommended = ReviewRating.objects.values('product__product_name')\
        .annotate(total=Count('id')).order_by('-total')[:5]

    low_stock = Product.objects.filter(stock__lt=5)\
        .values('product_name', 'stock')

    return JsonResponse({
        "kpi": {
            "orders": total_orders,
            "revenue": float(total_revenue),
            "users": total_users,
        },
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
        "top_products": {
            "labels": [i['product__product_name'] for i in top_products],
            "ratings": [float(i['avg_rating']) for i in top_products],
        },
        "recommended": {
            "labels": [i['product__product_name'] for i in recommended],
            "counts": [i['total'] for i in recommended],
        },
        "low_stock": list(low_stock)
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


# ==============================
# ✅ REGISTER MODELS
# ==============================

admin_site = CustomAdminSite(name='custom_admin')

admin_site.register(Product, ProductAdmin)
admin_site.register(Variation, VariationAdmin)
admin_site.register(ReviewRating, ReviewRatingAdmin)
admin_site.register(ProductGallery, ProductGalleryAdmin)
admin_site.register(Category, CategoryAdmin)
admin_site.register(Account, AccountAdmin)
admin_site.register(Order, OrderAdmin)
