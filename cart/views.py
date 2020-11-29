from django.shortcuts import render, redirect


def view_cart(request):
    """ renders the cart contents page """
    return render(request, 'cart/cart.html')


def add_to_cart(request, item_id):
    """ Add a quantity of the specified product to the shopping cart """

    quantity = int(request.POST.get('quantity', '1'))
    redirect_url = request.headers.get('referer')
    cart = request.session.get('cart', {})

    if item_id in list(cart.keys()):
        cart[item_id] += quantity
    else:
        cart[item_id] = quantity

    request.session['cart'] = cart
    return redirect(redirect_url)


def remove_from_cart(request, item_id):
    """ remove item from shopping cart """

    redirect_url = request.headers.get('referer')
    cart = request.session.get('cart', {})
    cart.pop(item_id, None)

    request.session['cart'] = cart
    return redirect(redirect_url)


def decrement_cart_itm(request, item_id):
    """ decrement a specific product qty from shopping cart """

    redirect_url = request.headers.get('referer')
    cart = request.session.get('cart', {})
    product = cart.get(item_id)

    if product:
        cart[item_id] -= 1
        request.session['cart'] = cart

    return redirect(redirect_url)
