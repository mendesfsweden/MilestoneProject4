from django.shortcuts import render, get_object_or_404
from .models import Product


def all_products(request):
    """ shows all products, search bar and sorting """

    products = Product.objects.all()

    context = {
        'products': products,
    }

    return render(request, 'products/products.html', context)


def detailed_product(request, product_id):
    """ shows individual product details """

    product = get_object_or_404(Product, pk=product_id)

    context = {
        'product': product,
    }

    return render(request, 'products/detailed_products.html', context)
