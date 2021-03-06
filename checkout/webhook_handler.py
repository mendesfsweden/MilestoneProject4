from django.http import HttpResponse
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings

from .models import Order, OrderLineItem
from products.models import Product
from profiles.models import UserProfile
from .views import generate_promo_code

import json
import time


def _send_confirmation_email(order):
    """Send the user a confirmation email"""
    cust_email = order.user_profile.user.email
    subject = render_to_string(
        'checkout/confirmation_emails/confirmation_email_subject.txt',
        {'order': order})
    body = render_to_string(
        'checkout/confirmation_emails/confirmation_email_body.txt',
        {'order': order, 'contact_email': settings.DEFAULT_FROM_EMAIL})

    send_mail(
        subject,
        body,
        settings.DEFAULT_FROM_EMAIL,
        [cust_email]
    )


def handle_event(request, event):
    """
    Handle a generic/unknown/unexpected webhook event
    """
    event_type = event['type']
    event_handler = event_map.get(event_type)

    if event_handler:
        return event_handler(request, event)

    return HttpResponse(
        content=f'Unhandled webhook received: {event["type"]}',
        status=200)


def handle_payment_intent_succeeded(request, event):
    """
    Handle the payment_intent.succeeded webhook from Stripe
    """
    intent = event.data.object
    pid = intent.id
    cart = intent.metadata.cart
    save_info = intent.metadata.save_info

    billing_details = intent.charges.data[0].billing_details
    shipping_details = intent.shipping
    grand_total = round(intent.charges.data[0].amount / 100, 2)

    # Clean data in the shipping details
    for field, value in shipping_details.address.items():
        if value == "":
            shipping_details.address[field] = None

    # Update profile information if save_info was checked
        username = intent.metadata.username
        profile = UserProfile.objects.get(user__username=username)
        if save_info:
            profile.full_name = shipping_details.name
            profile.default_phone_number = shipping_details.phone
            profile.default_country = shipping_details.address.country
            profile.default_postcode = shipping_details.address.postal_code
            profile.default_city = shipping_details.address.city
            profile.default_street_address1 = shipping_details.address.line1
            profile.default_street_address2 = shipping_details.address.line2
            profile.save()

    order_exists = False
    attempt = 1
    while attempt < 5:
        try:
            order = Order.objects.get(
                full_name__iexact=shipping_details.name,
                email__iexact=billing_details.email,
                phone_number__iexact=shipping_details.phone,
                country__iexact=shipping_details.address.country,
                postcode__iexact=shipping_details.address.postal_code,
                city__iexact=shipping_details.address.city,
                street_address1__iexact=shipping_details.address.line1,
                street_address2__iexact=shipping_details.address.line2,
                grand_total=grand_total,
                original_cart=cart,
                stripe_pid=pid,
            )
            order_exists = True
            break
        except Order.DoesNotExist:
            attempt += 1
            time.sleep(1)
    if order_exists:
        generate_promo_code(order.user_profile, order.grand_total)
        _send_confirmation_email(order)
        return HttpResponse(
            content=f'Webhook received: {event["type"]} | SUCCESS: Verified order already in database',
            status=200)
    else:
        order = None
        try:
            order = Order.objects.create(
                full_name=shipping_details.name,
                user_profile=profile,
                email=billing_details.email,
                phone_number=shipping_details.phone,
                country=shipping_details.address.country,
                postcode=shipping_details.address.postal_code,
                city=shipping_details.address.city,
                street_address1=shipping_details.address.line1,
                street_address2=shipping_details.address.line2,
                original_cart=cart,
                stripe_pid=pid,
            )
            for item_id, item_data in json.loads(cart).items():
                product = Product.objects.get(id=item_id)
                if isinstance(item_data, int):
                    order_line_item = OrderLineItem(
                        order=order,
                        product=product,
                        quantity=item_data,
                    )
                    order_line_item.save()
        except Exception as e:
            if order:
                order.delete()
            return HttpResponse(
                content=f'Webhook received: {event["type"]} | ERROR: {e}',
                status=500)
    generate_promo_code(order.user_profile, order.grand_total)
    _send_confirmation_email(order)
    return HttpResponse(
        content=f'Webhook received: {event["type"]} | SUCCESS: Created order in webhook',
        status=200)


def handle_payment_intent_payment_failed(request, event):
    """
    Handle the payment_intent.payment_failed webhook from Stripe
    """
    return HttpResponse(
        content=f'Webhook received: {event["type"]}',
        status=200)


event_map = {
    'payment_intent.succeeded': handle_payment_intent_succeeded,
    'payment_intent.payment_failed': handle_payment_intent_payment_failed,
}
