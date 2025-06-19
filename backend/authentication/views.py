# authentication/views.py

from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.authtoken.models import Token
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth import authenticate, login, logout # Import Django's built-in logout
from .serializers import AuthResponseSerializer # Your custom serializer

class CustomObtainAuthToken(ObtainAuthToken):
    """
    Custom Login View to return response in the specified OpenAPI format.
    Handles /auth/login/
    """
    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data,
                                           context={'request': request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        token, created = Token.objects.get_or_create(user=user)

        # Log the user in using Django's built-in login function (optional but good practice)
        login(request, user)

        # Prepare data for AuthResponseSerializer
        response_data = {
            'token': token, # Pass the token object
            'user': user    # Pass the user object
        }
        custom_serializer = AuthResponseSerializer(response_data)

        return Response(custom_serializer.data, status=status.HTTP_200_OK)

class LogoutView(APIView):
    """
    User Logout View.
    Handles /auth/logout/
    """
    permission_classes = [IsAuthenticated] # Only authenticated users can log out

    def post(self, request, *args, **kwargs):
        try:
            # Delete the user's token
            request.user.auth_token.delete()
            # Log the user out from Django session (if using SessionAuthentication)
            logout(request)
            return Response(
                {"success": True, "message": "Logout successful", "errors": None},
                status=status.HTTP_200_OK
            )
        except Exception as e:
            # Handle cases where token might already be deleted or other errors
            return Response(
                {"success": False, "message": f"Logout failed: {str(e)}", "errors": {"detail": str(e)}},
                status=status.HTTP_400_BAD_REQUEST # Or 500 depending on the specific error
            )