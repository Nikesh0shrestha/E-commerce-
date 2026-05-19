from django.shortcuts import render, redirect, get_object_or_404
from .forms import RegistrationForm, UserForm, UserProfileForm
from .models import Account, UserProfile
from orders.models import Order, OrderProduct
from django.contrib import messages, auth
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import HttpResponse
from store.models import Product

# Verification email
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import EmailMessage

from carts.views import _cart_id
from carts.models import Cart, CartItem
from urllib.parse import urlparse

from store.forms import ProductForm

from django.forms import inlineformset_factory
from store.models import Product, Variation
from store.forms import ProductForm, VariationForm



def register(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            first_name = form.cleaned_data['first_name']
            last_name = form.cleaned_data['last_name']
            phone_number = form.cleaned_data['phone_number']
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            role = form.cleaned_data['role'] # <--- Get the role

            username = email.split("@")[0]
            user = Account.objects.create_user(first_name=first_name, last_name=last_name, email=email, username=username, password=password)
            user.phone_number = phone_number
            user.role = role
            user.save()

            # Create a user profile
            profile = UserProfile()
            profile.user_id = user.id
            profile.profile_picture = 'default/default-user.png'
            profile.save()

            # USER ACTIVATION
            current_site = get_current_site(request)
            mail_subject = 'Please activate your account'
            message = render_to_string('accounts/account_verification_email.html', {
                'user': user,
                'domain': current_site,
                'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                'token': default_token_generator.make_token(user),
            })
            to_email = email
            send_email = EmailMessage(mail_subject, message, to=[to_email])
            send_email.send()
            # messages.success(request, 'Thank you for registering with us. We have sent you a verification email to {email}. Please verify it.')
            return redirect('/accounts/login/?command=verification&email='+email)
    else:
        form = RegistrationForm()
    context = {
        'form': form,
    }
    return render(request, 'accounts/register.html', context)


def login(request):
    if request.method == 'POST':
        email = request.POST['email']
        password = request.POST['password']
        selected_role = request.POST.get('role') # Get role from dropdown

        user = auth.authenticate(email=email, password=password)

        if user is not None:
            # This ensures a Supplier can't login by selecting "Customer"
            if user.role != selected_role:
                messages.error(request, f'This account is not registered as a {selected_role}.')
                return redirect('login')
            try:
                cart = Cart.objects.get(cart_id=_cart_id(request))
                is_cart_item_exists = CartItem.objects.filter(cart=cart).exists()
                if is_cart_item_exists:
                    cart_item = CartItem.objects.filter(cart=cart)

                    # Getting the product variations by cart id
                    product_variation = []
                    for item in cart_item:
                        variation = item.variations.all()
                        product_variation.append(list(variation))

                    # Get the cart items from the user to access his product variations
                    cart_item = CartItem.objects.filter(user=user)
                    ex_var_list = []
                    id = []
                    for item in cart_item:
                        existing_variation = item.variations.all()
                        ex_var_list.append(list(existing_variation))
                        id.append(item.id)

                    # product_variation = [1, 2, 3, 4, 6]
                    # ex_var_list = [4, 6, 3, 5]

                    for pr in product_variation:
                        if pr in ex_var_list:
                            index = ex_var_list.index(pr)
                            item_id = id[index]
                            item = CartItem.objects.get(id=item_id)
                            item.quantity += 1
                            item.user = user
                            item.save()
                        else:
                            cart_item = CartItem.objects.filter(cart=cart)
                            for item in cart_item:
                                item.user = user
                                item.save()
            
            except:
                pass
            auth.login(request, user)
            messages.success(request, 'You are now logged in.')
            url = request.META.get('HTTP_REFERER')
            try:
                query = urlparse(url).query
                # next=/cart/checkout/
                params = dict(x.split('=') for x in query.split('&'))
                if 'next' in params:
                    # nextPage = params['next']
                    # return redirect(nextPage)
                    return redirect(params['next'])
            except:
                #  return redirect('dashboard')
                # change in code (ROLE BASED REDIRECTION)
                pass
            if user.is_admin:
                return redirect('admin:index')
            elif user.role == 'supplier':
                return redirect('supplier_dashboard')
            elif user.role == 'delivery':
                return redirect('delivery_dashboard')
            else:
                return redirect ('dashboard') # upto here 
        else:
            messages.error(request, 'Invalid login credentials')
            return redirect('login')
    return render(request, 'accounts/login.html')


@login_required(login_url = 'login')
def logout(request):
    auth.logout(request)
    messages.success(request, 'You are logged out.')
    return redirect('login')


# This is checking user based login -----
# 1. Access Control: This function returns True only if the user is an admin
def is_admin_check(user):
    return user.is_admin

# 2. Admin Dashboard View
@login_required(login_url='login')
@user_passes_test(is_admin_check, login_url='login') # Redirects to login if not an admin
def admin_dashboard(request):
    return render(request, 'accounts/admin_dashboard.html')

# 3. Customer Dashboard View
@login_required(login_url='login')
def customer_dashboard(request):
    return render(request, 'accounts/dashboard.html')


def activate(request, uidb64, token):
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = Account._default_manager.get(pk=uid)
    except(TypeError, ValueError, OverflowError, Account.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        user.is_active = True
        user.save()
        messages.success(request, 'Congratulations! Your account is activated.')
        return redirect('login')
    else:
        messages.error(request, 'Invalid activation link')
        return redirect('register')


# @login_required(login_url = 'login')
# def dashboard(request):
#     orders = Order.objects.order_by('-created_at').filter(user_id=request.user.id, is_ordered=True)
#     orders_count = orders.count()

#     userprofile = UserProfile.objects.get(user_id=request.user.id)
#     context = {
#         'orders_count': orders_count,
#         'userprofile': userprofile,
#     }
#     return render(request, 'accounts/dashboard.html', context)

# change here 
@login_required(login_url='login')
def dashboard(request):
    # 1. The Role Check: This separates the two dashboards
    if request.user.role == 'supplier':
        return redirect('supplier_dashboard')
    
    # 2. Customer Logic: This only runs if the user is NOT a supplier
    try:
        orders = Order.objects.order_by('-created_at').filter(user_id=request.user.id, is_ordered=True)
        orders_count = orders.count()
        userprofile = UserProfile.objects.get(user_id=request.user.id)
        
        context = {
            'orders_count': orders_count,
            'userprofile': userprofile,
        }
        # This renders the standard customer dashboard
        return render(request, 'accounts/dashboard.html', context)
        
    except UserProfile.DoesNotExist:
        return redirect('edit_profile')


def forgotPassword(request):
    if request.method == 'POST':
        email = request.POST['email']
        if Account.objects.filter(email=email).exists():
            user = Account.objects.get(email__exact=email)

            # Reset password email
            current_site = get_current_site(request)
            mail_subject = 'Reset Your Password'
            message = render_to_string('accounts/reset_password_email.html', {
                'user': user,
                'domain': current_site,
                'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                'token': default_token_generator.make_token(user),
            })
            to_email = email
            send_email = EmailMessage(mail_subject, message, to=[to_email])
            send_email.send()

            messages.success(request, 'Password reset email has been sent to your email address.')
            return redirect('login')
        else:
            messages.error(request, 'Account does not exist!')
            return redirect('forgotPassword')
    return render(request, 'accounts/forgotPassword.html')


def resetpassword_validate(request, uidb64, token):
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = Account._default_manager.get(pk=uid)
    except(TypeError, ValueError, OverflowError, Account.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        request.session['uid'] = uid
        messages.success(request, 'Please reset your password')
        return redirect('resetPassword')
    else:
        messages.error(request, 'This link has been expired!')
        return redirect('login')


def resetPassword(request):
    if request.method == 'POST':
        password = request.POST['password']
        confirm_password = request.POST['confirm_password']

        if password == confirm_password:
            uid = request.session.get('uid')
            user = Account.objects.get(pk=uid)
            user.set_password(password)
            user.save()
            messages.success(request, 'Password reset successful')
            return redirect('login')
        else:
            messages.error(request, 'Password do not match!')
            return redirect('resetPassword')
    else:
        return render(request, 'accounts/resetPassword.html')


@login_required(login_url='login')
def my_orders(request):
    orders = Order.objects.filter(user=request.user, is_ordered=True).order_by('-created_at')
    context = {
        'orders': orders,
    }
    return render(request, 'accounts/my_orders.html', context)


@login_required(login_url='login')
def edit_profile(request):
    userprofile = get_object_or_404(UserProfile, user=request.user)
    if request.method == 'POST':
        user_form = UserForm(request.POST, instance=request.user)
        profile_form = UserProfileForm(request.POST, request.FILES, instance=userprofile)
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, 'Your profile has been updated.')
            return redirect('edit_profile')
    else:
        user_form = UserForm(instance=request.user)
        profile_form = UserProfileForm(instance=userprofile)
    context = {
        'user_form': user_form,
        'profile_form': profile_form,
        'userprofile': userprofile,
    }
    return render(request, 'accounts/edit_profile.html', context)


@login_required(login_url='login')
def change_password(request):
    if request.method == 'POST':
        current_password = request.POST['current_password']
        new_password = request.POST['new_password']
        confirm_password = request.POST['confirm_password']

        user = Account.objects.get(username__exact=request.user.username)

        if new_password == confirm_password:
            success = user.check_password(current_password)
            if success:
                user.set_password(new_password)
                user.save()
                # auth.logout(request)
                messages.success(request, 'Password updated successfully.')
                return redirect('change_password')
            else:
                messages.error(request, 'Please enter valid current password')
                return redirect('change_password')
        else:
            messages.error(request, 'Password does not match!')
            return redirect('change_password')
    return render(request, 'accounts/change_password.html')


@login_required(login_url='login')
def order_detail(request, order_id):
    order_detail = OrderProduct.objects.filter(order__order_number=order_id)
    order = Order.objects.get(order_number=order_id)
    subtotal = 0
    for i in order_detail:
        subtotal += i.product_price * i.quantity

    context = {
        'order_detail': order_detail,
        'order': order,
        'subtotal': subtotal,
    }
    return render(request, 'accounts/order_detail.html', context)


@login_required(login_url='login')
def supplier_dashboard(request):
    # Security check to ensure customers can't type this URL
    if request.user.role != 'supplier':
        return redirect('dashboard')
    return render(request, 'accounts/supplier_dashboard.html')

@login_required(login_url='login')
def supplier_products(request):
    if request.user.role != 'supplier':
        return redirect('dashboard')
        
    products = Product.objects.filter(supplier=request.user).order_by('-created_date')
    
    context = {
        'products': products,
    }
    return render(request, 'accounts/supplier_products.html', context)



# CRUD by supplier 
# @login_required(login_url='login')
# def add_product(request):
#     if request.user.role != 'supplier':
#         return redirect('dashboard')

#     if request.method == 'POST':
#         form = ProductForm(request.POST, request.FILES) # request.FILES is required for images!
#         if form.is_valid():
#             product = form.save(commit=False)
#             product.supplier = request.user # Automatically set the owner
#             product.save()
#             messages.success(request, 'Product added successfully!')
#             return redirect('supplier_products')
#     else:
#         form = ProductForm()
    
#     context = {'form': form}
#     return render(request, 'accounts/add_product.html', context)



@login_required(login_url='login')
def add_product(request):
    if request.user.role != 'supplier':
        return redirect('dashboard')
    
    # Add 'form=VariationForm' here
    VariationFormSet = inlineformset_factory(
        Product, 
        Variation, 
        form=VariationForm, # This tells Django which fields to use
        extra=2, 
        can_delete=False
    )

    # This creates a set of variation forms linked to one product
    VariationFormSet = inlineformset_factory(
        Product, Variation, form=VariationForm, extra=2, can_delete=False
    )

    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        formset = VariationFormSet(request.POST, instance=None) # instance=None because it's a new product
        
        if form.is_valid() and formset.is_valid():
            product = form.save(commit=False)
            product.supplier = request.user
            product.save() # We MUST save the product first to get a Product ID
            
            # Now save the variations linked to the new product
            variations = formset.save(commit=False)
            for var in variations:
                var.product = product
                var.save()
                
            messages.success(request, 'Product and Variations added successfully!')
            return redirect('supplier_products')
    else:
        form = ProductForm()
        formset = VariationFormSet()

    context = {
        'form': form,
        'formset': formset,
    }
    return render(request, 'accounts/add_product.html', context)



@login_required(login_url='login')
def edit_product(request, product_id):
    product = get_object_or_404(Product, id=product_id, supplier=request.user)
    
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            form.save()
            messages.success(request, 'Product updated successfully!')
            return redirect('supplier_products')
    else:
        form = ProductForm(instance=product)
    
    context = {'form': form, 'product': product}
    return render(request, 'accounts/edit_product.html', context)

@login_required(login_url='login')
def delete_product(request, product_id):
    product = get_object_or_404(Product, id=product_id, supplier=request.user)
    product.delete()
    messages.success(request, 'Product deleted successfully.')
    return redirect('supplier_products')

# def dashboard(request):
#     if request.user.is_authenticated:
#         # Check for supplier status
#         if hasattr(request.user, 'is_supplier') and request.user.is_supplier:
#             return redirect('supplier_dashboard') 
#         else:
#             # This will now find the path we named 'customer_dashboard' in urls.py
#             return redirect('customer_dashboard')
#     else:
#         return redirect('login')

def dashboard_switch(request):
    if not request.user.is_authenticated:
        return redirect('login')

    # Priority 1: Check if Supplier
    # Adjust 'is_supplier' to match your exact field name in models.py
    if hasattr(request.user, 'is_supplier') and request.user.is_supplier:
        return redirect('supplier_dashboard')
    
    # Priority 2: Default to Customer
    return redirect('customer_dashboard')

# These functions render the actual HTML pages
def customer_dashboard(request):
    return render(request, 'accounts/customer_dashboard.html')

def supplier_dashboard(request):
    return render(request, 'accounts/supplier_dashboard.html')


def delivery_dashboard(request):
    return render(request, 'acccounts/delivery_dashboard.html')