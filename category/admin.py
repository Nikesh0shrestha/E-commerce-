# from django.contrib import admin
# from .models import Category

# # Register your models here.

# class CategoryAdmin(admin.ModelAdmin):
#     prepopulated_fields = {'slug': ('category_name',)}
#     list_display = ('category_name', 'slug')

# admin.site.register(Category, CategoryAdmin)


from django.contrib import admin
from .models import Category
from django.utils.html import format_html


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('category_name', 'image_preview', 'slug')
    search_fields = ('category_name', 'description')
    prepopulated_fields = {'slug': ('category_name',)}
    ordering = ('category_name',)

    readonly_fields = ('image_preview',)

    fieldsets = (
        ('📂 Category Info', {
            'fields': ('category_name', 'slug', 'description')
        }),
        ('🖼️ Image', {
            'fields': ('cat_image', 'image_preview')
        }),
    )

    def image_preview(self, obj):
        if obj.cat_image:
            return format_html('<img src="{}" width="60" />', obj.cat_image.url)
        return "No Image"

    image_preview.short_description = "Preview"