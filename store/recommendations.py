"""
Item-based collaborative filtering for product recommendations.

This implementation uses historic purchase data to recommend products that are
frequently bought together with a given product (co-occurrence based).
"""
from typing import List

from django.db.models import QuerySet, Count


def get_similar_products(
    product,
    product_queryset: QuerySet = None,  # kept for backwards-compatibility, not used
    max_results: int = 6,
) -> List:
    """
    Return products similar to the given product using item-based collaborative filtering.

    The similarity is computed from order history:
    - Find all users who purchased the current product.
    - Among products those users also purchased, count how often each product
      co-occurs with the current product.
    - Rank by number of distinct users (and total occurrences) and return the top N.

    Args:
        product: The `Product` instance to find similar items for.
        product_queryset: Unused, kept only to preserve the original signature.
        max_results: Maximum number of similar products to return.

    Returns:
        List of `Product` instances, ordered by co-occurrence with the input product.
        Excludes the input product. Returns [] if there is insufficient history.
    """
    from .models import Product
    from orders.models import OrderProduct

    # Users who bought this product
    user_ids = (
        OrderProduct.objects.filter(product=product, ordered=True)
        .values_list("user_id", flat=True)
        .distinct()
    )

    if not user_ids:
        # No purchase history for this product; let the caller handle fallback.
        return []

    # Other products bought by those users, excluding the current product
    co_occurrence = (
        OrderProduct.objects.filter(user_id__in=user_ids, ordered=True)
        .exclude(product=product)
        .values("product")
        .annotate(
            user_count=Count("user", distinct=True),
            occurrence_count=Count("id"),
        )
        .order_by("-user_count", "-occurrence_count")[:max_results]
    )

    product_ids = [entry["product"] for entry in co_occurrence]
    if not product_ids:
        return []

    # Fetch product objects and preserve ranking order
    products = list(
        Product.objects.filter(id__in=product_ids, is_available=True).select_related("category")
    )
    products_by_id = {p.id: p for p in products}

    ordered_products = [products_by_id[pid] for pid in product_ids if pid in products_by_id]
    return ordered_products
