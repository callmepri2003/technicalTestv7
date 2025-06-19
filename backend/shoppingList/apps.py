# shoppingList/apps.py
from django.apps import AppConfig


class ShoppingListConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'shoppingList'
    verbose_name = 'Shopping Lists'
    
    def ready(self):
        # Import signals if you have any
        # import shoppingList.signals
        pass