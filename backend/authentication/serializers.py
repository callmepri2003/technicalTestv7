# authentication/serializers.py

from rest_framework import serializers
from django.contrib.auth import get_user_model

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    """
    Serializer for the User model, used in authentication responses.
    Matches the 'user' object in AuthResponse schema.
    """
    class Meta:
        model = User
        fields = ('id', 'username', 'email')
        read_only_fields = ('id', 'username', 'email') # These are read-only from auth response perspective

class AuthResponseSerializer(serializers.Serializer):
    """
    Serializer for the full authentication response.
    Matches the AuthResponse schema defined in OpenAPI.
    """
    success = serializers.BooleanField(default=True)
    message = serializers.CharField(default="Login successful")
    errors = serializers.ReadOnlyField(default=None) # As per spec, 'null' on success
    data = serializers.SerializerMethodField()

    def get_data(self, obj):
        # 'obj' here will be the token instance and user instance from the view
        token = obj.get('token')
        user = obj.get('user')
        if token and user:
            return {
                'token': token.key,
                'user': UserSerializer(user).data
            }
        return None # Should not happen if view passes correct data