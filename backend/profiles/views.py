from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from .models import UserProfile
from .serializers import UserProfileSerializer, UserProfileUpdateSerializer

class UserProfileViewSet(viewsets.ViewSet):
    """
    ViewSet for handling user profile operations.
    Supports retrieval (GET) and update (PUT/PATCH) of the authenticated user's profile.
    """
    permission_classes = [IsAuthenticated]

    def get_object(self):
        """
        Custom get_object to ensure the user can only access their own profile.
        Also creates a profile if one doesn't exist for the current user.
        """
        user = self.request.user
        # get_or_create is useful here to handle cases where a profile might not exist yet
        profile, created = UserProfile.objects.get_or_create(user=user)
        return profile

    def retrieve(self, request):
        """
        GET /profile/
        Retrieve current user's profile and preferences.
        """
        instance = self.get_object()
        serializer = UserProfileSerializer(instance)
        return Response({
            'success': True,
            'message': 'Profile retrieved successfully',
            'data': serializer.data
        }, status=status.HTTP_200_OK)

    def update(self, request, pk=None):
        """
        PUT /profile/
        Update user's shopping preferences.
        """
        instance = self.get_object()
        partial = request.method == 'PATCH' # Allow partial updates with PATCH

        serializer = UserProfileUpdateSerializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        # Re-serialize with the full profile serializer for the response format
        response_serializer = UserProfileSerializer(instance)

        return Response({
            'success': True,
            'message': 'Profile updated successfully',
            'data': response_serializer.data
        }, status=status.HTTP_200_OK)

    def partial_update(self, request, pk=None):
        """
        PATCH /profile/
        Partially update user's shopping preferences.
        """
        return self.update(request, partial=True)