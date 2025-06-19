from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/', include('authentication.urls')),
    path('api/shopping-list/', include('shoppingList.urls')),
    path('api/profile', include('profiles.urls')),
    path('api/transactions', include('transactions.urls'))
]