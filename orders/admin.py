# from django.contrib import admin
# from .models import Payment, Order, OrderProduct
# # Register your models here.


# class OrderProductInline(admin.TabularInline):
#     model = OrderProduct
#     readonly_fields = ('payment', 'user', 'product', 'quantity', 'product_price', 'ordered')
#     extra = 0

# class OrderAdmin(admin.ModelAdmin):
#     list_display = ['order_number', 'full_name', 'phone', 'email', 'city', 'order_total', 'tax', 'status', 'is_ordered', 'created_at']
#     list_filter = ['status', 'is_ordered']
#     search_fields = ['order_number', 'first_name', 'last_name', 'phone', 'email']
#     list_per_page = 20
#     inlines = [OrderProductInline]

# admin.site.register(Payment)
# admin.site.register(Order, OrderAdmin)
# admin.site.register(OrderProduct)


from django.contrib import admin
from .models import Order, OrderProduct, Payment


# 🔥 Inline: Order Items inside Order
class OrderProductInline(admin.TabularInline):
    model = OrderProduct
    extra = 0
    readonly_fields = ('product', 'quantity', 'product_price', 'ordered')


# 🔥 Payment Admin
@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('payment_id', 'user', 'payment_method', 'amount_paid', 'status', 'created_at')
    list_filter = ('payment_method', 'status', 'created_at')
    search_fields = ('payment_id', 'user__email')
    readonly_fields = ('payment_id', 'created_at')


# 🔥 Order Admin (MAIN DASHBOARD)
@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        'order_number',
        'full_name',
        'email',
        'order_total',
        'status',
        'is_ordered',
        'created_at'
    )

    list_filter = ('status', 'is_ordered', 'created_at')
    search_fields = ('order_number', 'first_name', 'last_name', 'email')

    readonly_fields = (
        'order_number',
        'payment',
        'user',
        'order_total',
        'tax',
        'created_at',
        'updated_at'
    )

    ordering = ('-created_at',)

    inlines = [OrderProductInline]

    fieldsets = (
        ('🧾 Order Info', {
            'fields': ('order_number', 'status', 'is_ordered')
        }),
        ('👤 Customer Info', {
            'fields': ('user', 'first_name', 'last_name', 'email', 'phone')
        }),
        ('📍 Address', {
            'fields': ('address_line_1', 'address_line_2', 'city', 'state', 'country')
        }),
        ('💰 Payment Info', {
            'fields': ('payment', 'order_total', 'tax')
        }),
        ('📅 Dates', {
            'fields': ('created_at', 'updated_at')
        }),
    )

    actions = ['mark_as_accepted', 'mark_as_completed', 'mark_as_cancelled']

    def mark_as_accepted(self, request, queryset):
        queryset.update(status='Accepted')
    mark_as_accepted.short_description = "Mark selected orders as Accepted"

    def mark_as_completed(self, request, queryset):
        queryset.update(status='Completed')
    mark_as_completed.short_description = "Mark selected orders as Completed"

    def mark_as_cancelled(self, request, queryset):
        queryset.update(status='Cancelled')
    mark_as_cancelled.short_description = "Mark selected orders as Cancelled"


# 🔥 Order Product Admin (Optional but useful)
@admin.register(OrderProduct)
class OrderProductAdmin(admin.ModelAdmin):
    list_display = ('order', 'product', 'quantity', 'product_price', 'ordered')
    list_filter = ('ordered', 'created_at')
    search_fields = ('product__product_name', 'order__order_number')