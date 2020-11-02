from django.shortcuts import render


def index(request):
    """ returns index.html """
    return render(request, 'home/index.html')