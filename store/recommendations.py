# """
# Item-based collaborative filtering for product recommendations.

# This implementation uses historic purchase data to recommend products that are
# frequently bought together with a given product (co-occurrence based).
# """
# from typing import List

# from django.db.models import QuerySet, Count


# def get_similar_products(
#     product,
#     product_queryset: QuerySet = None,  # kept for backwards-compatibility, not used
#     max_results: int = 6,
# ) -> List:
#     """
#     Return products similar to the given product using item-based collaborative filtering.

#     The similarity is computed from order history:
#     - Find all users who purchased the current product.
#     - Among products those users also purchased, count how often each product
#       co-occurs with the current product.
#     - Rank by number of distinct users (and total occurrences) and return the top N.

#     Args:
#         product: The `Product` instance to find similar items for.
#         product_queryset: Unused, kept only to preserve the original signature.
#         max_results: Maximum number of similar products to return.

#     Returns:
#         List of `Product` instances, ordered by co-occurrence with the input product.
#         Excludes the input product. Returns [] if there is insufficient history.
#     """
#     from .models import Product
#     from orders.models import OrderProduct

#     # Users who bought this product
#     user_ids = (
#         OrderProduct.objects.filter(product=product, ordered=True)
#         .values_list("user_id", flat=True)
#         .distinct()
#     )

#     if not user_ids:
#         # No purchase history for this product; let the caller handle fallback.
#         return []

#     # Other products bought by those users, excluding the current product
#     co_occurrence = (
#         OrderProduct.objects.filter(user_id__in=user_ids, ordered=True)
#         .exclude(product=product)
#         .values("product")
#         .annotate(
#             user_count=Count("user", distinct=True),
#             occurrence_count=Count("id"),
#         )
#         .order_by("-user_count", "-occurrence_count")[:max_results]
#     )

#     product_ids = [entry["product"] for entry in co_occurrence]
#     if not product_ids:
#         return []

#     # Fetch product objects and preserve ranking order
#     products = list(
#         Product.objects.filter(id__in=product_ids, is_available=True).select_related("category")
#     )
#     products_by_id = {p.id: p for p in products}

#     ordered_products = [products_by_id[pid] for pid in product_ids if pid in products_by_id]
#     return ordered_products

# import pandas as pd
# from .models import ReviewRating, Product

# def get_knn_recommendations(user_id, k=4):
#     # Fetch ratings data
#     ratings_data = ReviewRating.objects.filter(status=True).values('user_id', 'product_id', 'rating')
#     df = pd.DataFrame(list(ratings_data))

#     if df.empty or user_id is None:
#         return []

#     # Create User-Item Matrix
#     user_item_matrix = df.pivot_table(index='user_id', columns='product_id', values='rating').fillna(0)

#     if user_id not in user_item_matrix.index:
#         return []

#     # Simple similarity logic (Using Pearson Correlation)
#     user_ratings = user_item_matrix.loc[user_id]
#     similarities = user_item_matrix.corrwith(user_ratings, axis=1)
    
#     # Calculate scores
#     recommendations = user_item_matrix.T.dot(similarities).sort_values(ascending=False)
    
#     # Filter out what they already bought/rated
#     already_rated = df[df['user_id'] == user_id]['product_id'].tolist()
#     recommended_ids = [idx for idx in recommendations.index if idx not in already_rated]

#     return recommended_ids[:k]


import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
from .models import ReviewRating, Product

def get_knn_recommendations(user_id, k=4):
    # 1. Fetch ratings data from PostgreSQL
    ratings_data = ReviewRating.objects.filter(status=True).values('user_id', 'product_id', 'rating')
    df = pd.DataFrame(list(ratings_data))

    if df.empty or user_id is None:
        return []
  
    # 2. Create User-Item Matrix
    user_item_matrix = df.pivot_table(index='user_id', columns='product_id', values='rating').fillna(0)

    if user_id not in user_item_matrix.index:
        return []

    # 3. Apply Cosine Similarity Formula
    # This calculates the similarity between ALL users based on the formula you shared
    user_sim_matrix = cosine_similarity(user_item_matrix)
    
    # Convert to a DataFrame for easier lookup
    user_sim_df = pd.DataFrame(user_sim_matrix, index=user_item_matrix.index, columns=user_item_matrix.index)

    # 4. Get the similarity scores for the logged-in user
    # This finds 'Neighbors' who have the most similar rating patterns
    user_similarities = user_sim_df[user_id]

    # 5. Generate Predictions
    # Multiply the similarity scores by the ratings of other users
    # This follows the weighted average principle of KNN
    recommendation_scores = user_item_matrix.T.dot(user_similarities).sort_values(ascending=False)

    # 6. Filter: Remove products the user has already rated
    already_rated = df[df['user_id'] == user_id]['product_id'].tolist()
    recommended_ids = [idx for idx in recommendation_scores.index if idx not in already_rated]

    # Return the top K product IDs
    return recommended_ids[:k]