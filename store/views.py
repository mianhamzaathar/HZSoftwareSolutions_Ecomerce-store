import json

from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_POST
from .models import Product, Category
from .models import ProductReview
from cart.models import Cart, CartItem
from orders.models import Order

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
    Product.objects.filter(id=product.id).update(view_count=product.view_count + 1)
    product.refresh_from_db(fields=['view_count'])
    related_products = Product.objects.filter(category=product.category, is_active=True).exclude(id=product.id)[:4]
    context = {
        'product': product,
        'related_products': related_products,
        'reviews': product.approved_reviews,
        'variations': product.variations.filter(is_active=True),
    }
    return render(request, 'store/product_detail.html', context)


def quick_view(request, slug):
    """Return quick-view HTML snippet for a product modal."""
    product = get_object_or_404(Product, slug=slug, is_active=True)
    return render(request, 'store/partials/quick_view.html', {'product': product})


@login_required
def add_review(request, product_id):
    """Handle product review submission."""
    product = get_object_or_404(Product, id=product_id, is_active=True)

    if request.method == 'POST':
        rating = max(1, min(5, int(request.POST.get('rating', 5) or 5)))
        ProductReview.objects.update_or_create(
            product=product,
            user=request.user,
            defaults={
                'rating': rating,
                'comment': request.POST.get('comment', '').strip(),
                'is_approved': True,
            },
        )
        messages.success(request, 'Review submitted successfully.')

    return redirect('store:product_detail', slug=product.slug)

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
    return redirect('/checkout/')

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
def update_profile(request):
    """Update basic profile information."""
    if request.method == 'POST':
        request.user.first_name = request.POST.get('first_name', '').strip()
        request.user.last_name = request.POST.get('last_name', '').strip()
        request.user.email = request.POST.get('email', '').strip()
        request.user.save(update_fields=['first_name', 'last_name', 'email'])
        messages.success(request, 'Profile updated successfully.')
    return redirect('profile')


@login_required
def change_password(request):
    """Change account password."""
    if request.method == 'POST':
        current_password = request.POST.get('current_password', '')
        new_password1 = request.POST.get('new_password1', '')
        new_password2 = request.POST.get('new_password2', '')

        if not request.user.check_password(current_password):
            messages.error(request, 'Current password is incorrect.')
            return redirect('profile')

        if not new_password1 or new_password1 != new_password2:
            messages.error(request, 'New passwords do not match.')
            return redirect('profile')

        request.user.set_password(new_password1)
        request.user.save()
        update_session_auth_hash(request, request.user)
        messages.success(request, 'Password updated successfully.')
    return redirect('profile')


@login_required
def add_address(request):
    """Placeholder handler for profile address form."""
    if request.method == 'POST':
        messages.success(request, 'Address saved successfully.')
    return redirect('profile')


@login_required
def delete_account(request):
    """Delete current user account."""
    if request.method == 'POST':
        user = request.user
        logout(request)
        user.delete()
        messages.success(request, 'Your account has been deleted.')
        return redirect('landing')
    return redirect('profile')

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
    ids = request.session.get('wishlist_product_ids', [])
    products = Product.objects.filter(id__in=ids, is_active=True)
    return render(request, 'store/wishlist.html', {'wishlist_products': products})

@login_required
def add_to_wishlist(request, product_id):
    """Add product to wishlist"""
    product = get_object_or_404(Product, id=product_id)
    ids = request.session.get('wishlist_product_ids', [])
    if product.id not in ids:
        ids.append(product.id)
        request.session['wishlist_product_ids'] = ids
    messages.success(request, f'{product.name} added to wishlist!')
    return redirect(request.META.get('HTTP_REFERER', 'product_list'))

@login_required
def remove_from_wishlist(request, product_id):
    """Remove product from wishlist"""
    product = get_object_or_404(Product, id=product_id)
    ids = request.session.get('wishlist_product_ids', [])
    if product.id in ids:
        ids.remove(product.id)
        request.session['wishlist_product_ids'] = ids
    messages.success(request, f'{product.name} removed from wishlist!')
    return redirect('wishlist')


@login_required
def clear_wishlist(request):
    """Remove all products from wishlist."""
    request.session['wishlist_product_ids'] = []
    messages.success(request, 'Wishlist cleared successfully.')
    return redirect('wishlist')


@login_required
@require_POST
def api_add_to_wishlist(request):
    data = json.loads(request.body or '{}')
    product_id = data.get('product_id')
    product = get_object_or_404(Product, id=product_id, is_active=True)

    ids = request.session.get('wishlist_product_ids', [])
    if product.id not in ids:
        ids.append(product.id)
        request.session['wishlist_product_ids'] = ids

    return JsonResponse({'success': True, 'message': 'Added to wishlist.'})


@login_required
@require_POST
def api_remove_from_wishlist(request):
    data = json.loads(request.body or '{}')
    product_id = data.get('product_id')
    ids = request.session.get('wishlist_product_ids', [])
    if product_id in ids:
        ids.remove(product_id)
        request.session['wishlist_product_ids'] = ids

    return JsonResponse({'success': True, 'message': 'Removed from wishlist.'})

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
