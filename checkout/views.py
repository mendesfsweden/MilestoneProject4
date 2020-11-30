from django.shortcuts import render, redirect, reverse, get_object_or_404, HttpResponse
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.conf import settings

from .forms import OrderForm
from .models import Order, OrderLineItem, Promo
from products.models import Product
from profiles.forms import UserProfileForm
from profiles.models import UserProfile
from cart.contexts import cart_contents
from premiumbody.settings import PROMO_CODE_TRESHOLD, PROMO_CODE_VALUE

import stripe
import json
import random
import string


@require_POST
def cache_checkout_data(request):
    try:
        pid = request.POST.get('client_secret').split('_secret')[0]
        stripe.api_key = settings.STRIPE_SECRET_KEY
        stripe.PaymentIntent.modify(pid, metadata={
            'cart': json.dumps(request.session.get('cart', {})),
            'save_info': request.POST.get('save_info'),
            'username': request.user,
        })
        return HttpResponse(status=200)
    except Exception as e:
        messages.error(request, 'Sorry, your payment cannot be \
            processed right now. Please try again later.')
        return HttpResponse(content=e, status=400)


def checkout(request):
    stripe_public_key = settings.STRIPE_PUBLIC_KEY
    stripe_secret_key = settings.STRIPE_SECRET_KEY

    profile = UserProfile.objects.get(user=request.user)
    params = request.GET if request.method == 'GET' else request.POST
    promo_code = params.get('promo-code')
    promo = None
    if promo_code:
        try:
            promo = Promo.objects.get(user_profile=profile,
                                      promo_code=promo_code,
                                      promo_used=False)
        except:
            pass

    if request.method == 'POST':
        cart = request.session.get('cart', {})

        form_data = {
            'full_name': request.POST['full_name'],
            'phone_number': request.POST['phone_number'],
            'country': request.POST['country'],
            'postcode': request.POST['postcode'],
            'city': request.POST['city'],
            'street_address1': request.POST['street_address1'],
            'street_address2': request.POST['street_address2'],
        }
        order_form = OrderForm(form_data)
        if order_form.is_valid():
            order = order_form.save(commit=False)
            pid = request.POST.get('client_secret').split('_secret')[0]
            order.stripe_pid = pid
            order.original_cart = json.dumps(cart)
            order.save()
            for item_id, item_data in cart.items():
                try:
                    product = Product.objects.get(id=item_id)
                    if isinstance(item_data, int):
                        order_line_item = OrderLineItem(
                            order=order,
                            product=product,
                            quantity=item_data,
                        )
                        order_line_item.save()
                except Product.DoesNotExist:
                    messages.error(request, (
                        "One of the products in your cart wasn't \
                         found in our database. "
                        "Please call us for assistance!")
                    )
                    order.delete()
                    return redirect(reverse('view_cart'))
            if promo and order.order_total > PROMO_CODE_VALUE:
                order.promo_code = promo.promo_code
                order.grand_total -= PROMO_CODE_VALUE
                promo.promo_used = True
                promo.save()
                order.save()
            request.session['save_info'] = 'save-info' in request.POST
            return redirect(reverse('checkout_success',
                                    args=[order.order_number]))
        else:
            messages.error(request, 'There was an error with your form. \
                Please double check your information.')

    else:
        cart = request.session.get('cart', {})
        if not cart:
            messages.error(request, "There's nothing in your \
                                     cart at the moment")
            return redirect(reverse('products'))

    current_cart = cart_contents(request)
    total = current_cart['grand_total']
    stripe_total = round(total * 100)
    stripe.api_key = stripe_secret_key
    intent = stripe.PaymentIntent.create(
        amount=stripe_total,
        currency=settings.STRIPE_CURRENCY,
    )

    order_form = OrderForm(initial={
        'full_name': profile.full_name,
        'phone_number': profile.default_phone_number,
        'country': profile.default_country,
        'postcode': profile.default_postcode,
        'city': profile.default_city,
        'street_address1': profile.default_street_address1,
        'street_address2': profile.default_street_address2,
    })

    if not stripe_public_key:
        messages.warning(request, 'Stripe public key is missing. \
            Did you forget to set it in your environment?')

    if promo and current_cart['total'] > PROMO_CODE_VALUE:
        current_cart['grand_total'] -= PROMO_CODE_VALUE

    template = 'checkout/checkout.html'
    context = {
        'order_form': order_form,
        'stripe_public_key': stripe_public_key,
        'client_secret': intent.client_secret,
        'PROMO_CODE_VALUE': PROMO_CODE_VALUE,
        'promo': promo,
        **current_cart
        }

    return render(request, template, context)


def checkout_success(request, order_number):
    """
    Handle successful checkouts
    """
    save_info = request.session.get('save_info')
    order = get_object_or_404(Order, order_number=order_number)

    profile = UserProfile.objects.get(user=request.user)
    # Attach the user's profile to the order
    order.user_profile = profile
    if order.promo_code == '':
        generate_promo_code(order.user_profile, order.grand_total)
    order.save()

    # Save the user's info
    if save_info:
        profile_data = {
            'full_name': order.full_name,
            'default_phone_number': order.phone_number,
            'default_country': order.country,
            'default_postcode': order.postcode,
            'default_city': order.city,
            'default_street_address1': order.street_address1,
            'default_street_address2': order.street_address2,
        }
        user_profile_form = UserProfileForm(profile_data, instance=profile)
        if user_profile_form.is_valid():
            user_profile_form.save()

    if 'cart' in request.session:
        del request.session['cart']

    template = 'checkout/checkout_success.html'
    context = {
        'order': order,
        'PROMO_CODE_VALUE': PROMO_CODE_VALUE,
    }

    return render(request, template, context)


def generate_promo_code(user, order_total):
    if order_total < PROMO_CODE_TRESHOLD:
        return None
    code = get_random_string()
    promo = Promo(user_profile=user, promo_code=code)
    promo.save()
    return code


def get_random_string():
    return ''.join(random.choice(string.ascii_uppercase) for i in range(8))
