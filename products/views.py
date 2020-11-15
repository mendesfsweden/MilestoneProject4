from django.shortcuts import render, get_object_or_404, reverse, redirect
from .models import Product, Category
from django.contrib import messages
from django.db.models import Q
from django.core.paginator import Paginator
from premiumbody.settings import PRODUCTS_PER_PAGE


def all_products(request):
    """ shows all products, search bar and sorting """

    products = Product.objects.all()
    query = None

    if request.GET:
        if 'category' in request.GET:
            categories = request.GET['category'].split(',')
            products = products.filter(category__name__in=categories)

        if 'q' in request.GET:
            query = request.GET['q']
            if not query:
                messages.error(request, "Please enter a word to search for!")
                return redirect(reverse('products'))

            queries = Q(name__icontains=query) | Q(description__icontains=query)
            products = products.filter(queries)

    paginator = Paginator(products, PRODUCTS_PER_PAGE)
    page_number = request.GET.get('page') or 1
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'search_term': query,

    }

    return render(request, 'products/products.html', context)


def detailed_product(request, product_id):
    """ shows individual product details """

    product = get_object_or_404(Product, pk=product_id)

    context = {
        'product': product,
    }

    return render(request, 'products/detailed_product.html', context)
