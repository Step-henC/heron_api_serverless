# example/urls.py
from django.urls import path

from glyco.views import index


urlpatterns = [
    path('', index),
]