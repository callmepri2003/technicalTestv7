# shoppingList/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.ShoppingListListCreateView.as_view(), name='shopping-list-list'),
    path('<int:pk>/', views.ShoppingListDetailView.as_view(), name='shopping-list-detail'),
    path('generate/', views.generate_shopping_lists, name='shopping-list-generate'),
    path('<int:pk>/complete/', views.complete_shopping_list, name='shopping-list-complete'),
    path('<int:pk>/convert-to-transaction/', views.convert_to_transaction, name='shopping-list-convert-to-transaction'),
    path('simulate/', views.simulate_shopping_behavior, name='shopping-list-simulate'),
]