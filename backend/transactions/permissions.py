# transactions/permissions.py

from rest_framework import permissions

class IsOwnerPermission(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object to view or edit it.
    Assumes the model instance has a `user` attribute.
    """

    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any authenticated request,
        # so we'll always allow GET, HEAD, or OPTIONS requests.
        if request.method in permissions.SAFE_METHODS:
            return obj.user == request.user

        # Write permissions are only allowed to the owner of the snippet.
        return obj.user == request.user