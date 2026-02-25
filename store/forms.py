# store/forms.py
from django import forms
from .models import ReviewRating, Product, Variation

class ReviewForm(forms.ModelForm):
    class Meta:
        model = ReviewRating
        fields = ['subject', 'review', 'rating']

class VariationForm(forms.ModelForm):
    class Meta:
        model = Variation
        fields = ['variation_category', 'variation_value', 'is_active']
        
    def __init__(self, *args, **kwargs):
        super(VariationForm, self).__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs['class'] = 'form-control'

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['product_name', 'slug', 'description', 'price', 'images', 'stock', 'category', 'is_available']
    
    def __init__(self, *args, **kwargs):
        # FIXED: Changed VariationForm to ProductForm here
        super(ProductForm, self).__init__(*args, **kwargs) 
        for field in self.fields:
            self.fields[field].widget.attrs['class'] = 'form-control'