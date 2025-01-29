from django.urls import path
from hiv.views import transformHivData

urlpatterns = [
    path('', transformHivData),
]