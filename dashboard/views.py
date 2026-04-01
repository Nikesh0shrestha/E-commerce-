from django.shortcuts import render
from orders.models import Order, OrderProduct
from store.models import Product
from django.db.models import Sum
from django.utils.timezone import now, timedelta


# 📊 Analytics Dashboard
def analytics_dashboard(request):
    total_orders = Order.objects.filter(status='Completed').count()

    total_revenue = Order.objects.filter(status='Completed')\
        .aggregate(Sum('order_total'))['order_total__sum'] or 0

    top_products = OrderProduct.objects.values(
        'product__product_name'
    ).annotate(total_qty=Sum('quantity')).order_by('-total_qty')[:5]

    low_stock = Product.objects.filter(stock__lte=5)

    context = {
        'total_orders': total_orders,
        'total_revenue': total_revenue,
        'top_products': top_products,
        'low_stock': low_stock,
    }

    return render(request, 'dashboard/analytics.html', context)


# 📈 Sales Chart (Last 30 days)
def sales_chart(request):
    today = now().date()
    last_30_days = today - timedelta(days=30)

    sales = (
        Order.objects.filter(status='Completed', created_at__gte=last_30_days)
        .extra({'day': "date(created_at)"})
        .values('day')
        .annotate(total=Sum('order_total'))
        .order_by('day')
    )

    context = {'sales': sales}
    return render(request, 'dashboard/sales.html', context)


# 🧠 Basic Recommendation (Same category)
def recommendations(request, product_id):
    product = Product.objects.get(id=product_id)
    recommended = Product.objects.filter(
        category=product.category
    ).exclude(id=product.id)[:5]

    return render(request, 'dashboard/recommendations.html', {
        'product': product,
        'recommended': recommended
    })