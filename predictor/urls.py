# predictor/urls.py
from django.urls import path
from .views import predict_view

app_name = 'predictor'

urlpatterns = [
    path('', predict_view, name='predict'),]