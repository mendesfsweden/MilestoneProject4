from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name="home"),
    path('reviews/', views.add_review, name="add_review"),
]
