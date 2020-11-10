from django.shortcuts import render
from .models import Product


def all_products(request):
    """ shows all products, search bar and sorting """

    products = Product.objects.all()

    context = {
        'products': products,
    }

    return render(request, 'products/products.html', context)
