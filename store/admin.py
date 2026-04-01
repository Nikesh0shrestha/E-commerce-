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
from .models import Product, Variation, ReviewRating, ProductGallery
from django.utils.html import format_html


# 🔥 Inline for Product Gallery (multiple images)
class ProductGalleryInline(admin.TabularInline):
    model = ProductGallery
    extra = 1


# 🔥 Inline for Variations (color, size)
class VariationInline(admin.TabularInline):
    model = Variation
    extra = 1


# 🔥 Product Admin (Main Highlight)
@admin.register(Product)
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
@admin.register(Variation)
class VariationAdmin(admin.ModelAdmin):
    list_display = ('product', 'variation_category', 'variation_value', 'is_active')
    list_filter = ('variation_category', 'is_active')
    search_fields = ('product__product_name', 'variation_value')


# 🔥 Review Admin
@admin.register(ReviewRating)
class ReviewRatingAdmin(admin.ModelAdmin):
    list_display = ('product', 'user', 'rating', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('product__product_name', 'user__email')
    readonly_fields = ('created_at', 'updated_at')


# 🔥 Product Gallery Admin
@admin.register(ProductGallery)
class ProductGalleryAdmin(admin.ModelAdmin):
    list_display = ('product', 'image')