# shoppingList/filters.py
import django_filters
from django.db import models
from .models import ShoppingList, ShoppingListItem


class ShoppingListFilter(django_filters.FilterSet):
    status = django_filters.ChoiceFilter(choices=ShoppingList.STATUS_CHOICES)
    scheduled_date = django_filters.DateFilter()
    scheduled_date_after = django_filters.DateFilter(field_name='scheduled_date', lookup_expr='gte')
    scheduled_date_before = django_filters.DateFilter(field_name='scheduled_date', lookup_expr='lte')
    created_after = django_filters.DateTimeFilter(field_name='created_at', lookup_expr='gte')
    created_before = django_filters.DateTimeFilter(field_name='created_at', lookup_expr='lte')
    is_expired = django_filters.BooleanFilter(method='filter_is_expired')
    
    class Meta:
        model = ShoppingList
        fields = ['status', 'scheduled_date']
    
    def filter_is_expired(self, queryset, name, value):
        if value is True:
            # Show expired lists (past date and not completed)
            from datetime import date
            return queryset.filter(
                scheduled_date__lt=date.today(),
                status__in=['IN_PROGRESS', 'TRIAGED', 'PENDING', 'EXPIRED']
            )
        elif value is False:
            # Show non-expired lists
            from datetime import date
            return queryset.filter(
                models.Q(scheduled_date__gte=date.today()) |
                models.Q(status='COMPLETED')
            )
        return queryset


class ShoppingListItemFilter(django_filters.FilterSet):
    is_purchased = django_filters.BooleanFilter()
    product_category = django_filters.CharFilter(field_name='product__category', lookup_expr='icontains')
    product_name = django_filters.CharFilter(field_name='product__name', lookup_expr='icontains')
    predicted_price_min = django_filters.NumberFilter(field_name='predicted_price', lookup_expr='gte')
    predicted_price_max = django_filters.NumberFilter(field_name='predicted_price', lookup_expr='lte')
    
    class Meta:
        model = ShoppingListItem
        fields = ['is_purchased', 'product_category', 'product_name']