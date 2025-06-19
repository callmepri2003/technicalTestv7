# transactions/urls.py

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import TransactionViewSet

router = DefaultRouter()
router.register(r'transactions', TransactionViewSet, basename='transaction')

urlpatterns = [
    path('', include(router.urls)),
    # Custom action 'estimate-missed' is automatically routed by DefaultRouter
    # to /transactions/estimate-missed/
]