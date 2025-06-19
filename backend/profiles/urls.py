from django.urls import path
from .views import UserProfileViewSet
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)
from rest_framework.authtoken.views import obtain_auth_token

urlpatterns = [
    # User Profile endpoints
    # Using .as_view() with {'get': 'retrieve', 'put': 'update', 'patch': 'partial_update'}
    # maps HTTP methods to viewset actions.
    path('', UserProfileViewSet.as_view({
        'get': 'retrieve',
        'put': 'update',
        'patch': 'partial_update'
    }), name='profile-detail'),
]