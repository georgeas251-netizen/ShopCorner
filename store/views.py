from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required

from .models import Product, Order, OrderItem, Review, Wishlist
import razorpay
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings

def home(request):
    query = request.GET.get('q', '')
    if query:
        products = Product.objects.filter(name__icontains=query)
    else:
        products = Product.objects.all ()
    context = {
        'products': products,
        'query': query
    }
    return render(request, 'home.html', context)
def product_detail(request, pk):
    product = get_object_or_404 (Product, id=pk)
    context = {
        'product': product
    }
    return render(request, 'product_detail.html', context)

def add_to_cart(request, pk):
    cart = request.session.get('cart', {})
    cart[str(pk)] = cart.get(str(pk), 0) + 1
    request.session['cart'] = cart
    return redirect('cart')

def cart(request):
    cart = request.session.get('cart', {})
    cart_items = []
    total = 0
    for pk, quantity in cart.items():
        product = get_object_or_404(Product, id=pk)
        subtotal = product.price * quantity
        total += subtotal
        cart_items.append({
            'product': product,
            'quantity': quantity,
            'subtotal': subtotal
        })
    return render(request, 'cart.html', {'cart_items': cart_items, 'total': total})

def remove_from_cart(request, pk):
    cart = request.session.get('cart', {})
    cart.pop(str(pk), None)
    request.session['cart'] = cart
    return redirect('cart')

def checkout(request):
    cart = request.session.get('cart', {})
    cart_items = []
    total = 0

    for pk, quantity in cart.items():
        product = get_object_or_404(Product, id=pk)
        subtotal = product.price * quantity
        total += subtotal
        cart_items.append({
            'product': product,
            'quantity': quantity,
            'subtotal': subtotal
        })
    if request.method == 'POST':
        full_name = request.POST.get('full_name')
        address = request.POST.get('address')
        phone = request.POST.get('phone')

        #Create the order
        order = Order.objects.create(
            user=request.user,
            full_name=full_name,
            address=address,
            phone=phone,
            total_price=total
        )
#Save each item
        for item in cart_items:
            OrderItem.objects.create(
                order=order,
                product=item['product'],
                quantity=item['quantity'],
                price=item['product'].price
            )

        send_mail(
            subject=f'Order #{order.pk} Confirmed - ShopCorner',
            message=f'Hi {order.full_name}, your order #{order.pk} has been placed successfully! Total: ₹{order.total_price}',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[request.user.email],
            fail_silently=True,
        )

        # Clear the cart
        request.session['cart'] = {}
        return redirect('order_confirmation', order_id=order.pk)
    
    return render(request, 'checkout.html', {
        'cart_item': cart_items,
        'total':total
    })

def order_confirmation(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    return render(request, 'order_confirmation.html',{'order': order})

def order_history(request):
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'order_history.html',{'orders': orders})
    
def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('home')
        return render(request, 'register.html', {'form': form})
    form = UserCreationForm()
    return render(request, 'register.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('home')
        return render(request, 'login.html',{'form':form})
    form = AuthenticationForm()
    return render(request, 'login.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('home')

def profile(request):
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    total_orders = orders.count()
    return render(request, 'profile.html', {
        'orders': orders,
        'total_orders': total_orders,
    })

def add_review(request, pk):
    product = get_object_or_404(Product, id=pk)
    if request.method == 'POST':
        rating = request.POST.get('rating')
        comment = request.POST.get('comment')
        Review.objects.create(
            product=product,
            user=request.user,
            rating=rating,
            comment=comment
        )
    return redirect('product_detail', pk=pk)

def add_to_wishlist(request):
    product = get_object_or_404(Product, id=pk)
    Wishlist.objects.get_or_create(user=request.user, product=product)
    return redirect('wishlist')

def wishlist(request):
    items = Wishlist.objects.filter(user=request.user)
    return render(request, 'wishlist.html', {'items': items})

def remove_from_wishlist(request, pk):
    wishlist.objects.filter(user=request.user, product_id=pk).delete()
    return redirect('wishlist')

def payment(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

    razorpay_order = client.order.create({
        'amount': int(order.total_price * 100), #paise
        'currency': 'INR',
        'payment_capture': 1
    })

    return render(request, 'payment.html', {
        'order': order,
        'razorpay_key_id': settings.RAZORPAY_KEY_ID,
        'amount': int(order.total_price * 100),
    })

def payment_success(request):
    return render(request, 'payment_success.html')

