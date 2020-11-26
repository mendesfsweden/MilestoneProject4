from django.shortcuts import render, redirect, reverse
from products.models import Product
from premiumbody.settings import MAX_TOP_RATED, MAX_REVIEWS
from .models import Review
from profiles.models import UserProfile


def index(request):
    """ returns index.html """

    products = Product.objects.order_by('-rating')[:MAX_TOP_RATED]
    reviews = Review.objects.order_by('?')[:MAX_REVIEWS]

    context = {
        'top_rated_products': products,
        'reviews': reviews,
    }

    return render(request, 'home/index.html', context)


def add_review(request):
    """ add a review """

    if not request.user.is_authenticated:
        return redirect(reverse('home'))
    print('ola')
    profile = UserProfile.objects.get(user=request.user)
    review = Review(user_profile=profile, text=request.POST["text"])
    review.save()
    return redirect(reverse('home'))
