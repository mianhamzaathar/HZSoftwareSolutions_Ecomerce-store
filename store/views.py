from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Product, Category

# Home and Product Views
def home(request):
    """Home page view"""
    products = Product.objects.filter(is_active=True)[:8]  # Get 8 featured products
    categories = Category.objects.filter(is_active=True)
    context = {
        'products': products,
        'categories': categories,
    }
    return render(request, 'store/home.html', context)

def product_list(request):
    """Product listing page"""
    products = Product.objects.filter(is_active=True)
    categories = Category.objects.filter(is_active=True)
    context = {
        'products': products,
        'categories': categories,
    }
    return render(request, 'store/product_list.html', context)

def product_detail(request, slug):
    """Product detail page"""
    product = get_object_or_404(Product, slug=slug, is_active=True)
    related_products = Product.objects.filter(category=product.category, is_active=True).exclude(id=product.id)[:4]
    context = {
        'product': product,
        'related_products': related_products,
    }
    return render(request, 'store/product_detail.html', context)

# Category Views
def category_products(request, category_slug):
    """Category products page"""
    category = get_object_or_404(Category, slug=category_slug, is_active=True)
    products = Product.objects.filter(category=category, is_active=True)
    context = {
        'category': category,
        'products': products,
    }
    return render(request, 'store/category_products.html', context)

def all_categories(request):
    """All categories page"""
    categories = Category.objects.filter(is_active=True)
    return render(request, 'store/categories.html', {'categories': categories})

# Cart Views
@login_required
def cart(request):
    """Shopping cart page"""
    cart, created = Cart.objects.get_or_create(user=request.user, is_active=True)
    context = {
        'cart': cart,
        'cart_items': cart.items.all(),
        'total': cart.get_total(),
    }
    return render(request, 'store/cart.html', context)

@login_required
def add_to_cart(request, product_id):
    """Add product to cart"""
    product = get_object_or_404(Product, id=product_id, is_active=True)
    cart, created = Cart.objects.get_or_create(user=request.user, is_active=True)
    
    cart_item, created = CartItem.objects.get_or_create(cart=cart, product=product)
    if not created:
        cart_item.quantity += 1
        cart_item.save()
    
    messages.success(request, f'{product.name} added to cart successfully!')
    return redirect('cart')

@login_required
def remove_from_cart(request, item_id):
    """Remove item from cart"""
    cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    product_name = cart_item.product.name
    cart_item.delete()
    
    messages.success(request, f'{product_name} removed from cart successfully!')
    return redirect('cart')

@login_required
def update_cart(request, item_id):
    """Update cart item quantity"""
    if request.method == 'POST':
        quantity = int(request.POST.get('quantity', 1))
        cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
        
        if quantity > 0:
            cart_item.quantity = quantity
            cart_item.save()
            messages.success(request, 'Cart updated successfully!')
        else:
            cart_item.delete()
            messages.success(request, 'Item removed from cart!')
    
    return redirect('cart')

# Checkout Views
@login_required
def checkout(request):
    """Checkout page"""
    cart = get_object_or_404(Cart, user=request.user, is_active=True)
    
    if request.method == 'POST':
        # Process order
        order = Order.objects.create(
            user=request.user,
            total_amount=cart.get_total(),
            shipping_address=request.POST.get('address'),
            payment_method=request.POST.get('payment_method')
        )
        
        # Transfer cart items to order
        for item in cart.items.all():
            order.items.create(
                product=item.product,
                quantity=item.quantity,
                price=item.product.price
            )
        
        # Deactivate cart
        cart.is_active = False
        cart.save()
        
        messages.success(request, 'Order placed successfully!')
        return redirect('checkout_success')
    
    context = {
        'cart': cart,
        'total': cart.get_total(),
    }
    return render(request, 'store/checkout.html', context)

@login_required
def checkout_success(request):
    """Checkout success page"""
    return render(request, 'store/checkout_success.html')

# User Account Views
@login_required
def profile(request):
    """User profile page"""
    return render(request, 'store/profile.html', {'user': request.user})

@login_required
def orders(request):
    """User orders page"""
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'store/orders.html', {'orders': orders})

@login_required
def order_detail(request, order_id):
    """Order detail page"""
    order = get_object_or_404(Order, id=order_id, user=request.user)
    return render(request, 'store/order_detail.html', {'order': order})

# Wishlist Views
@login_required
def wishlist(request):
    """User wishlist page"""
    wishlist, created = Wishlist.objects.get_or_create(user=request.user)
    return render(request, 'store/wishlist.html', {'wishlist': wishlist})

@login_required
def add_to_wishlist(request, product_id):
    """Add product to wishlist"""
    product = get_object_or_404(Product, id=product_id)
    wishlist, created = Wishlist.objects.get_or_create(user=request.user)
    wishlist.products.add(product)
    
    messages.success(request, f'{product.name} added to wishlist!')
    return redirect(request.META.get('HTTP_REFERER', 'product_list'))

@login_required
def remove_from_wishlist(request, product_id):
    """Remove product from wishlist"""
    product = get_object_or_404(Product, id=product_id)
    wishlist = get_object_or_404(Wishlist, user=request.user)
    wishlist.products.remove(product)
    
    messages.success(request, f'{product.name} removed from wishlist!')
    return redirect('wishlist')

# Search View
def search(request):
    """Search products"""
    query = request.GET.get('q', '')
    if query:
        products = Product.objects.filter(name__icontains=query, is_active=True)
    else:
        products = Product.objects.none()
    
    context = {
        'products': products,
        'query': query,
    }
    return render(request, 'store/search_results.html', context)

# Static Page Views
def about(request):
    """About page"""
    return render(request, 'store/about.html')

def contact(request):
    """Contact page"""
    if request.method == 'POST':
        # Process contact form
        name = request.POST.get('name')
        email = request.POST.get('email')
        message = request.POST.get('message')
        # Send email or save to database
        messages.success(request, 'Your message has been sent. We\'ll get back to you soon!')
        return redirect('contact')
    
    return render(request, 'store/contact.html')

def privacy_policy(request):
    """Privacy policy page"""
    return render(request, 'store/privacy_policy.html')

def terms_conditions(request):
    """Terms and conditions page"""
    return render(request, 'store/terms_conditions.html')