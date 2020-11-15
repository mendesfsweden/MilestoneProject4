from django.shortcuts import render
from products.models import Product
from premiumbody.settings import MAX_TOP_RATED


def index(request):
    """ returns index.html """

    products = Product.objects.order_by('-rating')[:MAX_TOP_RATED]

    context = {
        'top_rated_products': products,
    }

    return render(request, 'home/index.html', context)
