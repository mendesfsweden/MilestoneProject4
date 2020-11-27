from django.shortcuts import render, get_object_or_404, reverse, redirect
from .models import Product
from django.contrib import messages
from django.db.models import Q
from django.core.paginator import Paginator
from premiumbody.settings import PRODUCTS_PER_PAGE, DEFAULT_ORDER_BY, ORDERS


def all_products(request):
    """ shows all products, search bar, sorting and pagination """

    products = Product.objects.all()
    query = None
    category = None

    if request.GET:
        if 'category' in request.GET:
            category = request.GET['category']
            products = products.filter(category__name__in=[category])

        if 'q' in request.GET:
            query = request.GET['q']
            if not query:
                messages.error(request, "Please enter a word to search for!")
                return redirect(reverse('products'))

            queries = Q(name__icontains=query) | Q(description__icontains=query)
            products = products.filter(queries)

    order_param = request.GET.get('order_by')
    order = ORDERS.get(order_param, DEFAULT_ORDER_BY)
    products = products.order_by(order)
    paginator = Paginator(products, PRODUCTS_PER_PAGE)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'search_term': query,
        'order': order,
        'category': category,
    }

    return render(request, 'products/products.html', context)


def detailed_product(request, product_id):
    """ shows individual product details """

    product = get_object_or_404(Product, pk=product_id)

    context = {
        'product': product,
    }

    return render(request, 'products/detailed_product.html', context)
