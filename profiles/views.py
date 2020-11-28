from django.shortcuts import render, get_object_or_404
from .models import UserProfile
from .forms import UserProfileForm
from checkout.models import Order, Promo


def profile(request):
    """ Display the user's profile. """
    profile = get_object_or_404(UserProfile, user=request.user)

    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()

    form = UserProfileForm(instance=profile)
    orders = profile.orders.all()
    promo_codes = Promo.objects.filter(user_profile=profile)

    template = 'profiles/profile.html'
    context = {
        'form': form,
        'orders': orders,
        'promo_codes': promo_codes,
    }

    return render(request, template, context)


def order_history(request, order_number):
    order = get_object_or_404(Order, order_number=order_number)

    template = 'checkout/checkout_success.html'
    context = {
        'order': order,
        'from_profile': True,
    }

    return render(request, template, context)
