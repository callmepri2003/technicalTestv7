# authentication/serializers.py

from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import UserProfile

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    """
    Serializer for the nested User object within UserProfile.
    """
    class Meta:
        model = User
        fields = ['id', 'username', 'email']
        read_only_fields = ['id', 'username', 'email']

class UserProfileSerializer(serializers.ModelSerializer):
    """
    Serializer for retrieving UserProfile details.
    Matches OpenAPI schema 'UserProfile'.
    """
    user = UserSerializer(read_only=True) # Nested serializer for user details

    class Meta:
        model = UserProfile
        fields = ['id', 'user', 'preferred_shopping_day', 'preferred_shopping_frequency', 'created_at', 'updated_at']
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']

    def validate_preferred_shopping_day(self, value):
        if value is not None and not (0 <= value <= 6):
            raise serializers.ValidationError("Preferred shopping day must be an integer between 0 (Monday) and 6 (Sunday).")
        return value

class UserProfileUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating UserProfile details.
    Matches OpenAPI schema 'UserProfileUpdate'.
    """
    class Meta:
        model = UserProfile
        fields = ['preferred_shopping_day', 'preferred_shopping_frequency']
        # No read_only_fields here as these are the fields allowed for update.

    def validate_preferred_shopping_day(self, value):
        if value is not None and not (0 <= value <= 6):
            raise serializers.ValidationError("Preferred shopping day must be an integer between 0 (Monday) and 6 (Sunday).")
        return value