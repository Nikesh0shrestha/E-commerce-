from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse
from carts.models import CartItem
from .forms import OrderForm
import datetime
from .models import Order, Payment, OrderProduct
import json
from store.models import Product
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from accounts.models import UserProfile



import base64
import json
import hmac
import hashlib
import datetime

def payments(request):
    # eSewa sends data in a URL parameter called 'data'
    encoded_data = request.GET.get('data')
    
    if encoded_data:
        # 1. Decode eSewa's response
        decoded_bytes = base64.b64decode(encoded_data)
        decoded_str = decoded_bytes.decode('utf-8')
        data = json.loads(decoded_str) # This contains status, signature, transaction_uuid, etc.

        if data['status'] == 'COMPLETE':
            order_number = data['transaction_uuid']
            transID = data['transaction_code']
            
            # 2. Get the order
            try:
                order = Order.objects.get(user=request.user, is_ordered=False, order_number=order_number)
            except Order.DoesNotExist:
                return redirect('home')

            # 3. Store transaction details in Payment model
            payment = Payment(
                user = request.user,
                payment_id = transID,
                payment_method = 'eSewa',
                amount_paid = order.order_total,
                status = 'Completed',
            )
            payment.save()

            # 4. Update Order table
            order.payment = payment
            order.is_ordered = True
            order.save()

            # 5. Move the cart items to Order Product table
            cart_items = CartItem.objects.filter(user=request.user)
            for item in cart_items:
                orderproduct = OrderProduct()
                orderproduct.order_id = order.id
                orderproduct.payment = payment
                orderproduct.user_id = request.user.id
                orderproduct.product_id = item.product_id
                orderproduct.quantity = item.quantity
                orderproduct.product_price = item.product.price
                orderproduct.ordered = True
                orderproduct.save()

                # Set variations
                cart_item = CartItem.objects.get(id=item.id)
                product_variation = cart_item.variations.all()
                orderproduct.variations.set(product_variation)
                orderproduct.save()

                # 6. Reduce the quantity of the sold products
                product = Product.objects.get(id=item.product_id)
                product.stock -= item.quantity
                product.save()

            # 7. Clear cart
            CartItem.objects.filter(user=request.user).delete()

            # 8. Send order received email
            mail_subject = 'Thank you for your order!'
            message = render_to_string('orders/order_recieved_email.html', {
                'user': request.user,
                'order': order,
            })
            to_email = request.user.email
            send_email = EmailMessage(mail_subject, message, to=[to_email])
            send_email.send()

            # 9. Redirect to the thank you page
            return redirect(f"/orders/order_complete/?order_number={order_number}&payment_id={transID}")

    # If payment fails or data is missing
    return redirect('checkout')

# def payments(request):
#     body = json.loads(request.body)
#     order = Order.objects.get(user=request.user, is_ordered=False, order_number=body['orderID'])

#     # Store transaction details inside Payment model
#     payment = Payment(
#         user = request.user,
#         payment_id = body['transID'],
#         payment_method = body['payment_method'],
#         amount_paid = order.order_total,
#         status = body['status'],
#     )
#     payment.save()

#     order.payment = payment
#     order.is_ordered = True
#     order.save()

#     # Move the cart items to Order Product table
#     cart_items = CartItem.objects.filter(user=request.user)

#     for item in cart_items:
#         orderproduct = OrderProduct()
#         orderproduct.order_id = order.id
#         orderproduct.payment = payment
#         orderproduct.user_id = request.user.id
#         orderproduct.product_id = item.product_id
#         orderproduct.quantity = item.quantity
#         orderproduct.product_price = item.product.price
#         orderproduct.ordered = True
#         orderproduct.save()

#         cart_item = CartItem.objects.get(id=item.id)
#         product_variation = cart_item.variations.all()
#         orderproduct = OrderProduct.objects.get(id=orderproduct.id)
#         orderproduct.variations.set(product_variation)
#         orderproduct.save()


#         # Reduce the quantity of the sold products
#         product = Product.objects.get(id=item.product_id)
#         product.stock -= item.quantity
#         product.save()

#     # Clear cart
#     CartItem.objects.filter(user=request.user).delete()

#     # Send order recieved email to customer
#     mail_subject = 'Thank you for your order!'
#     message = render_to_string('orders/order_recieved_email.html', {
#         'user': request.user,
#         'order': order,
#     })
#     to_email = request.user.email
#     send_email = EmailMessage(mail_subject, message, to=[to_email])
#     send_email.send()

#     # Send order number and transaction id back to sendData method via JsonResponse
#     data = {
#         'order_number': order.order_number,
#         'transID': payment.payment_id,
#     }
#     return JsonResponse(data)


def place_order(request, total=0, quantity=0):
    current_user = request.user
    cart_items = CartItem.objects.filter(user=current_user)
    cart_count = cart_items.count()

    if cart_count <= 0:
        return redirect('store')

    # Calculate Totals
    for cart_item in cart_items:
        total += (cart_item.product.price * cart_item.quantity)
        quantity += cart_item.quantity
    tax = (2 * total) / 100
    grand_total = total + tax



    # Pre-fill data for the Billing Form
    # initial_data = {
    #     'first_name': current_user.first_name,
    #     'last_name': current_user.last_name,
    #     'email': current_user.email,
    # }
    try:
        user_profile = UserProfile.objects.get(user=current_user)
        initial_data = {
            'first_name': current_user.first_name,
            'last_name': current_user.last_name,
            'email': current_user.email,
            'address_line_1': user_profile.address_line_1,
            'address_line_2': user_profile.address_line_2,
            'city': user_profile.city,
            'state': user_profile.state,
            'country': user_profile.country,
        }
    except UserProfile.DoesNotExist:
    # Fallback if no profile exists yet
        initial_data = {
            'first_name': current_user.first_name,
            'last_name': current_user.last_name,
            'email': current_user.email,
        }

    if request.method == 'POST':
        form = OrderForm(request.POST)
        if form.is_valid():
            # 1. Save Order Billing Info
            data = Order()
            data.user = current_user
            data.first_name = form.cleaned_data['first_name']
            data.last_name = form.cleaned_data['last_name']
            data.phone = form.cleaned_data['phone']
            data.email = form.cleaned_data['email']
            data.address_line_1 = form.cleaned_data['address_line_1']
            data.address_line_2 = form.cleaned_data['address_line_2']
            data.country = form.cleaned_data['country']
            data.state = form.cleaned_data['state']
            data.city = form.cleaned_data['city']
            data.order_note = form.cleaned_data['order_note']
            data.order_total = grand_total
            data.tax = tax
            data.ip = request.META.get('REMOTE_ADDR')
            data.save()

            # 2. Generate Unique Order Number
            current_date = datetime.date.today().strftime("%Y%m%d")
            order_number = current_date + str(data.id)
            data.order_number = order_number
            data.save()

            # 3. Generate eSewa Signature
            secret_key = "8gBm/:&EnhH.1/q"
            product_code = "EPAYTEST"
            display_total = "{:.1f}".format(grand_total) # Must match HTML exactly
            
            # The string used for hashing (No spaces!)
            message = f"total_amount={display_total},transaction_uuid={order_number},product_code={product_code}"
            
            hash_val = hmac.new(secret_key.encode(), message.encode(), hashlib.sha256).digest()
            signature = base64.b64encode(hash_val).decode()

            context = {
                'order': data,
                'cart_items': cart_items,
                'total': total,
                'tax': tax,
                'grand_total': display_total,
                'signature': signature,
            }
            return render(request, 'orders/payments.html', context)
        
        # If POST is invalid, fall through to re-render form with errors
    else:
        # GET request: Show pre-filled form
        form = OrderForm(initial=initial_data)

    context = {
        'form': form,
        'cart_items': cart_items,
        'total': total,
        'tax': tax,
        'grand_total': grand_total,
    }
    return render(request, 'store/checkout.html', context)


# def place_order(request, total=0, quantity=0,):
#     current_user = request.user

#     # If the cart count is less than or equal to 0, then redirect back to shop
#     cart_items = CartItem.objects.filter(user=current_user)
#     cart_count = cart_items.count()
#     if cart_count <= 0:
#         return redirect('store')

#     grand_total = 0
#     tax = 0
#     for cart_item in cart_items:
#         total += (cart_item.product.price * cart_item.quantity)
#         quantity += cart_item.quantity
#     tax = (2 * total)/100
#     grand_total = total + tax

#     # 1. Define initial_data at the top so it's always available
#     initial_data = {
#         'first_name': current_user.first_name,
#         'last_name': current_user.last_name,
#         'email': current_user.email,
#     }

#     if request.method == 'POST':
#         form = OrderForm(request.POST)
#         if form.is_valid():
#             # Store all the billing information inside Order table
#             data = Order()
#             data.user = current_user
#             data.first_name = form.cleaned_data['first_name']
#             data.last_name = form.cleaned_data['last_name']
#             data.phone = form.cleaned_data['phone']
#             data.email = form.cleaned_data['email']
#             data.address_line_1 = form.cleaned_data['address_line_1']
#             data.address_line_2 = form.cleaned_data['address_line_2']
#             data.country = form.cleaned_data['country']
#             data.state = form.cleaned_data['state']
#             data.city = form.cleaned_data['city']
#             data.order_note = form.cleaned_data['order_note']
#             data.order_total = grand_total
#             data.tax = tax
#             data.ip = request.META.get('REMOTE_ADDR')
#             data.save()
#             return render(request, 'orders/payments.html', context)
#         else:
#             form = OrderForm(initial=initial_data)
#         # PRE-FILL LOGIC: Pass initial data to the form
#             # initial_data = {
#             # 'first_name': current_user.first_name,
#             # 'last_name': current_user.last_name,
#             # 'email': current_user.email,
#             # If you have a UserProfile model for phone/address, fetch it here:
#             # 'phone': current_user.userprofile.phone_number,
#             # 'address_line_1': current_user.userprofile.address_line_1,
#         # }
#         # form = OrderForm(initial=initial_data)
#         context = {
#             'form': form,
#             'cart_items': cart_items,
#             'total': total,
#             'tax': tax,
#             'grand_total': grand_total,
#         }
#         return render(request, 'store/checkout.html', context)
#     data.save()
#             # Generate order number
#     yr = int(datetime.date.today().strftime('%Y'))
#     dt = int(datetime.date.today().strftime('%d'))
#     mt = int(datetime.date.today().strftime('%m'))
#     d = datetime.date(yr,mt,dt)
#     current_date = d.strftime("%Y%m%d") #20210305
#     order_number = current_date + str(data.id)
#     data.order_number = order_number
#     data.save()

#             # --- FIX: ESEWA SIGNATURE LOGIC ---
#     secret_key = "8gBm/:&EnhH.1/q" # Sandbox Secret
#     product_code = "EPAYTEST"      # Sandbox Product Code

#             # eSewa V2 requires the amount to be a string. 
#             # If total_amount is 100, string should be '100'. 
#             # We use format to ensure consistency with the HTML display.
#     display_total = "{:.1f}".format(grand_total)

#             # The message string must be exactly: total_amount,transaction_uuid,product_code
#     message = f"total_amount={display_total},transaction_uuid={order_number},product_code={product_code}"

#             # Generate HMAC-SHA256
#     hash_val = hmac.new(secret_key.encode(), message.encode(), hashlib.sha256).digest()
#     signature = base64.b64encode(hash_val).decode()

#     order = Order.objects.get(user=current_user, is_ordered=False, order_number=order_number)
#     context = {
#                 'order': data,
#                 'cart_items': cart_items,
#                 'total': total,
#                 'tax': tax,
#                 'grand_total': grand_total,
#                 'signature': signature,
#             }
#     return render(request, 'orders/payments.html', context)
#     else:
#     return redirect('checkout')
    
def cash_on_delivery(request, order_number):
        try:
            # 1. Retrieve the order
            order = Order.objects.get(user=request.user, is_ordered=False, order_number=order_number)
            
            # 2. Create Payment record for COD
            payment = Payment(
                user = request.user,
                payment_id = order_number, 
                payment_method = 'Cash on Delivery',
                amount_paid = order.order_total,
                status = 'Pending',
            )
            payment.save()

            # 3. Finalize Order
            order.payment = payment
            order.is_ordered = True
            order.save()

            # 4. Redirect to order completion page
            return redirect(f'/orders/order_complete/?order_number={order_number}&payment_id={order_number}')

        except Order.DoesNotExist:
            # If the order is not found, send them back to the store
            return redirect('store')
        except Exception as e:
            # Log any other error and redirect
            print(f"Error: {e}")
            return redirect('home')



def order_complete(request):
    order_number = request.GET.get('order_number')
    transID = request.GET.get('payment_id')

    try:
        order = Order.objects.get(order_number=order_number, is_ordered=True)
        ordered_products = OrderProduct.objects.filter(order_id=order.id)

        subtotal = 0
        for i in ordered_products:
            subtotal += i.product_price * i.quantity

        payment = Payment.objects.get(payment_id=transID)

        context = {
            'order': order,
            'ordered_products': ordered_products,
            'order_number': order.order_number,
            'transID': payment.payment_id,
            'payment': payment,
            'subtotal': subtotal,
        }
        return render(request, 'orders/order_complete.html', context)
    except (Payment.DoesNotExist, Order.DoesNotExist):
        return redirect('home')

