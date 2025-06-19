# shoppingList/permissions.py
from rest_framework.permissions import BasePermission


class IsOwnerOrReadOnly(BasePermission):
    """
    Custom permission to only allow owners of an object to edit it.
    """

    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed for authenticated users
        if request.method in ['GET', 'HEAD', 'OPTIONS']:
            return request.user.is_authenticated
        
        # Write permissions are only allowed to the owner of the shopping list
        return obj.user == request.user


class CanModifyShoppingList(BasePermission):
    """
    Permission to check if shopping list can be modified based on its status
    """
    
    def has_object_permission(self, request, view, obj):
        # Owner check first
        if obj.user != request.user:
            return False
        
        # For DELETE requests, check if list can be deleted
        if request.method == 'DELETE':
            return obj.can_be_deleted()
        
        # For other modifications, allow if not completed
        if request.method in ['PUT', 'PATCH']:
            return obj.status != 'COMPLETED'
        
        return True